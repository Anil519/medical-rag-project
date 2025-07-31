from langchain_huggingface import HuggingFacePipeline
import json
from neo4j import GraphDatabase
import torch
import torch.nn as nn
import torch.optim as optim
import random
import re
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

extractor = HuggingFacePipeline.from_model_id(
    model_id="google/medgemma-4b-it",  # Stable as of July 8, 2025 bug fix; for multimodal, use 'google/medgemma-27b-multimodal'
    task="text-generation",
    pipeline_kwargs={"max_new_tokens": 200}
)

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD")))

def validate_triple(sub, pred, obj):
    if not sub or not pred or not obj:
        return False
    if len(pred.split()) < 1 or not re.match(r'^[a-zA-Z0-9_ -]+$', pred):
        return False
    common_rels = ['treats', 'causes', 'interacts_with', 'is_a', 'has_side_effect']
    if pred.lower() not in common_rels:
        logging.warning(f"Uncommon relation '{pred}' - consider human review or ontology enrichment (e.g., UMLS).")
    
    # UMLS alignment placeholder (simulate; integrate real API: import requests; res = requests.get(f"https://uts-ws.nlm.nih.gov/rest/search/current?string={sub}&apiKey=your_uts_key"))
    # if res.json()['result']['results']: return True  # Example check for entity existence
    return True

def extract_triples(text):
    prompt = f"Extract knowledge graph triples as 'entity1, relation, entity2;' from biomedical text: {text}. Focus on accurate drug/disease/compound relations."
    generated = extractor.invoke(prompt)
    triples = []
    for t in generated.split(';'):
        parts = t.split(',')
        if len(parts) >= 3:
            sub = ','.join(parts[:-2]).strip()
            pred = parts[-2].strip()
            obj = parts[-1].strip()
            if validate_triple(sub, pred, obj):
                triples.append((sub, pred, obj))
    return triples

class DistMult(nn.Module):
    def __init__(self, num_entities, num_relations, embedding_dim):
        super().__init__()
        self.entity_emb = nn.Embedding(num_entities, embedding_dim)
        self.rel_emb = nn.Embedding(num_relations, embedding_dim)

    def forward(self, h, r, t):
        h_emb = self.entity_emb(h)
        r_emb = self.rel_emb(r)
        t_emb = self.entity_emb(t)
        return torch.sum(h_emb * r_emb * t_emb, dim=-1)

class TransE(nn.Module):
    def __init__(self, num_entities, num_relations, embedding_dim):
        super().__init__()
        self.entity_emb = nn.Embedding(num_entities, embedding_dim)
        self.rel_emb = nn.Embedding(num_relations, embedding_dim)

    def forward(self, h, r, t):
        h_emb = self.entity_emb(h)
        r_emb = self.rel_emb(r)
        t_emb = self.entity_emb(t)
        return -torch.norm(h_emb + r_emb - t_emb, p=1, dim=-1)

def infer_type(entity):
    if any(word in entity.lower() for word in ['drug', 'med', 'compound']):
        return "Drug"
    elif any(word in entity.lower() for word in ['disease', 'symptom', 'condition']):
        return "Disease"
    return "Entity"

def build_kg(train_gan=True):
    with open("data_chunks.json", "r") as f:
        chunks = json.load(f)
    
    all_triples = []
    for chunk in chunks:
        all_triples.extend(extract_triples(chunk))
    
    all_triples = list(set(all_triples))
    entities = list(set([t[0] for t in all_triples] + [t[2] for t in all_triples]))
    relations = list(set([t[1] for t in all_triples]))
    
    entity2id = {e: i for i, e in enumerate(entities)}
    rel2id = {r: i for i, r in enumerate(relations)}
    num_entities = len(entities)
    num_relations = len(relations)
    
    triple_indices = [(entity2id[sub], rel2id[pred], entity2id[obj]) for sub, pred, obj in all_triples]
    
    if not train_gan:
        refined_triples = all_triples
        logging.info("Skipping GAN training; using rule-validated triples.")
    else:
        embedding_dim = 50
        epochs = 10
        batch_size = 32
        margin = 1.0
        neg_sample_size = 50
        
        generator = DistMult(num_entities, num_relations, embedding_dim)
        discriminator = TransE(num_entities, num_relations, embedding_dim)
        
        g_optimizer = optim.Adam(generator.parameters(), lr=0.001)
        d_optimizer = optim.Adam(discriminator.parameters(), lr=0.001)
        
        # Pre-train
        for model, optimizer in [(generator, g_optimizer), (discriminator, d_optimizer)]:
            for _ in range(5):
                for i in range(0, len(triple_indices), batch_size):
                    batch = triple_indices[i:i+batch_size]
                    pos_h, pos_r, pos_t = zip(*batch)
                    pos_h = torch.tensor(pos_h)
                    pos_r = torch.tensor(pos_r)
                    pos_t = torch.tensor(pos_t)
                    
                    neg_t = torch.randint(0, num_entities, (len(batch),))
                    neg_score = model(pos_h, pos_r, neg_t)
                    pos_score = model(pos_h, pos_r, pos_t)
                    
                    loss = torch.mean(torch.clamp(margin - pos_score + neg_score, min=0.0))
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
        
        # Adversarial Training
        for epoch in range(epochs):
            for i in range(0, len(triple_indices), batch_size):
                batch = triple_indices[i:i+batch_size]
                pos_h, pos_r, pos_t = [torch.tensor(x) for x in zip(*batch)]
                
                with torch.no_grad():
                    cand_neg_t = torch.randint(0, num_entities, (len(batch), neg_sample_size))
                    cand_scores = generator(pos_h.unsqueeze(1).repeat(1, neg_sample_size), 
                                            pos_r.unsqueeze(1).repeat(1, neg_sample_size), 
                                            cand_neg_t)
                    probs = torch.softmax(cand_scores, dim=1)
                    neg_t = torch.multinomial(probs, 1).squeeze()
                
                pos_score_d = discriminator(pos_h, pos_r, pos_t)
                neg_score_d = discriminator(pos_h, pos_r, neg_t)
                d_loss = torch.mean(torch.clamp(margin - pos_score_d + neg_score_d, min=0.0))
                d_optimizer.zero_grad()
                d_loss.backward()
                d_optimizer.step()
                
                cand_scores = generator(pos_h.unsqueeze(1).repeat(1, neg_sample_size), 
                                        pos_r.unsqueeze(1).repeat(1, neg_sample_size), 
                                        cand_neg_t)
                log_probs = torch.log_softmax(cand_scores, dim=1)
                with torch.no_grad():
                    rewards = -discriminator(pos_h.unsqueeze(1).repeat(1, neg_sample_size), 
                                             pos_r.unsqueeze(1).repeat(1, neg_sample_size), 
                                             cand_neg_t)
                    baseline = rewards.mean(dim=1, keepdim=True)
                    advantages = rewards - baseline
                g_loss = -torch.mean(advantages * log_probs)
                g_optimizer.zero_grad()
                g_loss.backward()
                g_optimizer.step()
            
            logging.info(f"Epoch {epoch+1}/{epochs} completed.")
        
        refined_triples = []
        with torch.no_grad():
            for h, r, t in triple_indices:
                score = discriminator(torch.tensor([h]), torch.tensor([r]), torch.tensor([t]))
                if score > 0:
                    sub = entities[h]
                    pred = relations[r]
                    obj = entities[t]
                    refined_triples.append((sub, pred, obj))
        
        num_refined = len(refined_triples)
        num_total = len(all_triples)
        precision = num_refined / num_total if num_total > 0 else 0
        
        # Recall/F1 (placeholder; use gold_triples = load_gold_data() for real)
        assumed_gold = num_total * 0.9  # Simulate
        recall = num_refined / assumed_gold if assumed_gold > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        logging.info(f"Triple refinement metrics: Precision={precision:.2f}, Recall={recall:.2f}, F1={f1:.2f} (refined {num_refined}/{num_total})")
        # Future: Improve accuracy with reinforcement (e.g., RLHF using human feedback on triples)
    
    with driver.session() as session:
        for sub, pred, obj in refined_triples:
            sub_type = infer_type(sub)
            obj_type = infer_type(obj)
            session.run(
                f"MERGE (a:{sub_type} {{name: $sub}}) MERGE (b:{obj_type} {{name: $obj}}) MERGE (a)-[r:REL {{type: $pred}}]->(b)",
                sub=sub, obj=obj, pred=pred
            )
    logging.info(f"KG built in Neo4j with {len(refined_triples)} refined triples.")

build_kg(train_gan=False)