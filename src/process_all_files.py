# src/process_all_files.py

import os
import sys
import json
import xml.etree.ElementTree as ET
import pandas as pd

# Fix import path so config and modules can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.chunk_embed import chunk_text, get_embeddings
from modules import vectorstore

SUPPORTED_EXTENSIONS = [".txt", ".pdf", ".docx", ".doc", ".csv", ".xlsx", ".json", ".xml"]

def read_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()

    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".pdf":
            import fitz
            doc = fitz.open(file_path)
            return "\n".join([page.get_text() for page in doc])

        elif ext in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])

        elif ext in [".csv", ".xlsx"]:
            df = pd.read_excel(file_path) if ext == ".xlsx" else pd.read_csv(file_path)
            return df.to_string(index=False)

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.dumps(json.load(f), indent=2)

        elif ext == ".xml":
            tree = ET.parse(file_path)
            return ET.tostring(tree.getroot(), encoding="unicode")

    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def process_and_store(file_path):
    print(f"\n📂 Processing: {file_path}")
    text = read_file(file_path)
    if not text or text.strip() == "":
        print(f"⚠️ No text extracted from: {file_path}")
        return

    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)
    vectorstore.upsert_chunks(chunks, embeddings)
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB: {file_path}")

def process_all_files(folder_path="./data/"):
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return

    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        if os.path.isfile(fpath) and os.path.splitext(fpath)[-1].lower() in SUPPORTED_EXTENSIONS:
            process_and_store(fpath)
        else:
            print(f"⛔ Skipping unsupported or non-file: {fname}")

if __name__ == "__main__":
    process_all_files()
