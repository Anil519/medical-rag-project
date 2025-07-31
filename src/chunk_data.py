import json
import os
import logging
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)

def clean_text(text):
    """Remove newline chars and extra spaces"""
    return ' '.join(text.strip().replace('\n', ' ').split())

def load_and_chunk(data_dir="./data"):
    chunks = []
    seen = set()

    # Get all JSON files in ./data
    all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".json")]
    logging.info(f"🔍 Found {len(all_files)} JSON files in {data_dir}")

    for file in all_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"❌ Failed to load {file}: {e}")
            continue

        count_before = len(chunks)

        for item in data:
            name = item.get("name", "").strip()
            desc = item.get("description") or ""

            if not name or not desc:
                continue

            # Clean and combine
            name = clean_text(name)
            desc = clean_text(desc)

            chunk = f"Drug Name: {name}. Description: {desc}."
            chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()

            if chunk_hash not in seen:
                seen.add(chunk_hash)
                chunks.append(chunk)

        logging.info(f"📦 Processed {file} — added {len(chunks) - count_before} unique chunks.")

    # Save
    with open("full_data_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    logging.info(f"✅ Finished: Created and saved {len(chunks)} unique drug chunks.")

if __name__ == "__main__":
    load_and_chunk()
 