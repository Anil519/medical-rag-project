from sentence_transformers import SentenceTransformer
import json
import numpy as np
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

model = SentenceTransformer('dmis-lab/biobert-base-cased-v1.1')

def embed_chunks():
    with open("data_chunks.json", "r") as f:
        chunks = json.load(f)
    
    embeddings = model.encode(chunks, convert_to_numpy=True)
    np.save("embeddings.npy", embeddings)
    logging.info(f"Generated and saved {len(embeddings)} embeddings (dim=768).")

embed_chunks()