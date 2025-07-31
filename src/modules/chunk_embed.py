from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Initialize the embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

def get_embeddings(chunks):
    return embedding_model.encode(chunks, show_progress_bar=True)
