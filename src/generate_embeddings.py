import json
import numpy as np
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import os

# Load .env
load_dotenv()

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Load embedding model
MODEL_NAME = 'pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb'
logging.info(f"🔗 Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

# File paths
CHUNK_FILE = "full_data_chunks.json"
EMBED_FILE = "embeddings/embeddings.npy"
os.makedirs("embeddings", exist_ok=True)

def embed_chunks():
    if not os.path.exists(CHUNK_FILE):
        logging.error(f"❌ Chunk file not found: {CHUNK_FILE}")
        return

    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logging.info(f"🧠 Encoding {len(chunks)} medical chunks...")
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)

    np.save(EMBED_FILE, embeddings)
    logging.info(f"✅ Saved embeddings to: {EMBED_FILE}")
    logging.info(f"📐 Shape: {embeddings.shape}")

if __name__ == "__main__":
    embed_chunks()
 