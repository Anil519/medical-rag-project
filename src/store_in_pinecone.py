from pinecone import Pinecone, ServerlessSpec
import json
import numpy as np
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

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

def upsert_to_pinecone():
    with open("data_chunks.json", "r") as f:
        chunks = json.load(f)
    embeddings = np.load("embeddings.npy")
    
    try:
        vectors = [(str(i), embeddings[i].tolist(), {"text": chunks[i]}) for i in range(len(chunks))]
        index.upsert(vectors=vectors)
        logging.info("Successfully upserted to Pinecone.")
    except Exception as e:
        logging.error(f"Error upserting: {str(e)}")

upsert_to_pinecone()