import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

client = chromadb.Client()
collection = client.get_or_create_collection(
    name="document_chunks",
    embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
)

def upsert_chunks(chunks, embeddings):
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        collection.upsert(
            ids=[f"chunk_{i}"],
            documents=[chunk],
            embeddings=[emb.tolist()],
        )
