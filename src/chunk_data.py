from langchain_text_splitters import TokenTextSplitter
import json
from transformers import AutoTokenizer
import logging
from dotenv import load_dotenv
import hashlib

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

tokenizer = AutoTokenizer.from_pretrained('dmis-lab/biobert-base-cased-v1.1')

def load_and_chunk(files):
    all_text = ""
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
            for item in data:
                text = f"{item.get('title', '')} {item.get('name', '')} {item.get('abstract', '')} {item.get('description', '')}"
                all_text += text + "\n\n"
    
    splitter = TokenTextSplitter.from_huggingface_tokenizer(
        tokenizer=tokenizer,
        chunk_size=512,
        chunk_overlap=50
    )
    chunks = splitter.split_text(all_text)
    
    # Deduplicate chunks (using SHA-256 hash)
    seen = set()
    unique_chunks = []
    for chunk in chunks:
        chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()
        if chunk_hash not in seen:
            seen.add(chunk_hash)
            unique_chunks.append(chunk)
    
    with open("data_chunks.json", "w") as f:
        json.dump(unique_chunks, f, indent=4)
    logging.info(f"Created and saved {len(unique_chunks)} unique chunks (after deduplication).")

load_and_chunk(["pubmed_data.json", "pubchem_data.json", "drugbank_data.json"])