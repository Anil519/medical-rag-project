import asyncio
import pubchempy as pcp
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

def fetch_compound(cid):
    try:
        details = pcp.Compound.from_cid(cid)
        return {
            "name": details.iupac_name,
            "description": details.synonyms,
            "molecular_formula": details.molecular_formula
        }
    except Exception:
        return None

async def fetch_pubchem_data(query, max_results=50, batch_size=10):
    compounds = pcp.get_compounds(query, 'name', listkey_count=max_results)
    data = []
    
    logging.info(f"Found {len(compounds)} PubChem compounds for query: {query}")
    
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        tasks = []
        for compound in compounds:
            tasks.append(loop.run_in_executor(executor, fetch_compound, compound.cid))
        results = await asyncio.gather(*tasks)
        data = [res for res in results if res]
    
    with open("pubchem_data.json", "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Fetched and saved {len(data)} PubChem compounds.")

asyncio.run(fetch_pubchem_data("aspirin", max_results=20))