import requests
import json
import re
from xml.etree import ElementTree as ET
import time

def clean_html(raw_html):
    """Remove HTML tags from text."""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"

def fetch_diseases(term="disease", max_pages=500):
    all_diseases = []
    page = 1

    while True:
        params = {
            "db": "healthTopics",
            "term": term,
            "retmax": 100,  # try to get more per request
            "retstart": (page - 1) * 100
        }

        print(f"📡 Fetching page {page} ...")
        response = requests.get(BASE_URL, params=params)

        if response.status_code != 200:
            print(f"❌ Error fetching page {page}: {response.status_code}")
            break

        root = ET.fromstring(response.text)
        documents = root.findall(".//document")
        if not documents:
            print("✅ No more results.")
            break

        for document in documents:
            raw_name = document.findtext(".//content[@name='title']")
            name = clean_html(raw_name) if raw_name else None

            raw_desc = document.findtext(".//content[@name='FullSummary']")
            desc = clean_html(raw_desc) if raw_desc else None

            if name and desc:
                all_diseases.append({"name": name, "description": desc})

        page += 1
        if page > max_pages:
            print("⚠️ Reached max page limit.")
            break

        time.sleep(0.5)  # be kind to the server

    return all_diseases


if __name__ == "__main__":
    diseases = fetch_diseases(term="disease", max_pages=500)

    with open("diseases.json", "w", encoding="utf-8") as f:
        json.dump(diseases, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved {len(diseases)} diseases to diseases.json")
