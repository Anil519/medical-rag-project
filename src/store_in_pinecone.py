from pinecone import Pinecone, ServerlessSpec
import json
import numpy as np
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "medical-rag-index"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)

# Batch upload helper
def batch_upsert(vectors, batch_size=100):
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
            logging.info(f"✅ Successfully upserted batch {i} to {i + len(batch)}.")
        except Exception as e:
            logging.error(f"❌ Error upserting batch {i}-{i + len(batch)}: {str(e)}")

# Main upsert logic
def upsert_to_pinecone():
    try:
        with open("full_data_chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)

        embeddings = np.load("./embeddings/embeddings.npy")

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)})")

        vectors = [
            (str(i), embeddings[i].tolist(), {"text": chunks[i]})
            for i in range(len(chunks))
        ]

        logging.info(f"📦 Total vectors to upsert: {len(vectors)}")
        batch_upsert(vectors, batch_size=100)

    except Exception as e:
        logging.error(f"❌ Failed in upsert_to_pinecone: {str(e)}")

if __name__ == "__main__":
    upsert_to_pinecone()
 