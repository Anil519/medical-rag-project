import asyncio
from Bio import Entrez
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os

load_dotenv()
Entrez.email = os.getenv("ENTREZ_EMAIL")
Entrez.api_key = os.getenv("ENTREZ_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

def fetch_batch(ids):
    handle = Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml")
    records = Entrez.read(handle)
    handle.close()
    data = []
    for article in records['PubmedArticle']:
        try:
            title = article['MedlineCitation']['Article']['ArticleTitle']
            abstract = article['MedlineCitation']['Article'].get('Abstract', {}).get('AbstractText', ['No abstract'])[0]
            data.append({"title": title, "abstract": abstract})
        except KeyError:
            continue
    return data

async def fetch_pubmed_data(query, max_results=100, batch_size=20):
    data = []
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    id_list = record["IdList"]
    handle.close()
    
    logging.info(f"Found {len(id_list)} PubMed IDs for query: {query}")
    
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        tasks = []
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i+batch_size]
            tasks.append(loop.run_in_executor(executor, fetch_batch, batch_ids))
        batch_results = await asyncio.gather(*tasks)
        for batch in batch_results:
            data.extend(batch)
    os.makedirs("./data", exist_ok=True)
    with open("./data/pubmed_data.json", "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Fetched and saved {len(data)} PubMed articles.")

asyncio.run(fetch_pubmed_data("antibiotics", max_results=50))