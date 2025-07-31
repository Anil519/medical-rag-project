# modules/vectorstore.py

import uuid
import chromadb
from chromadb.config import Settings
from config.config import CHROMA_COLLECTION_NAME

# Set the persistent directory
CHROMA_DIR = "memory/chroma"
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Load or create the Chroma collection
try:
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
except:
    collection = client.create_collection(name=CHROMA_COLLECTION_NAME)

def upsert_chunks(chunks, embeddings):
    assert len(chunks) == len(embeddings), "Mismatch between chunks and embeddings"

    ids = [str(uuid.uuid4()) for _ in chunks]
    batch_size = 5000  # ChromaDB safe batch size

    for i in range(0, len(chunks), batch_size):
        collection.add(
            documents=chunks[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            ids=ids[i:i + batch_size]
        )

def query_similar_chunks(question_embedding, top_k=5):
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    return results["documents"][0] if results["documents"] else []
