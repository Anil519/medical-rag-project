import xml.etree.ElementTree as ET
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

def parse_drugbank_xml(xml_file):
    data = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for drug in root.findall("drug"):
        try:
            name = drug.find("name").text
            description = drug.find("description").text
            data.append({"name": name, "description": description})
        except AttributeError:
            continue
    
    with open("drugbank_data.json", "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Parsed and saved {len(data)} DrugBank entries.")

parse_drugbank_xml("full database.xml")