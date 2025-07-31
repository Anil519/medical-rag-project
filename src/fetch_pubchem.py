import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ====== Ensure data folder exists ======
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "pubchem_scraped_with_description.json")

# ====== Get Description from Compound Page ======
def get_description_from_page(driver, cid):
    try:
        detail_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        driver.get(detail_url)

        # Wait for "Description" heading
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Description')]"))
        )

        # Get the description container (the sibling div after heading)
        description_container = driver.find_element(
            By.XPATH, "//div[contains(text(),'Description')]/following-sibling::div"
        )
        description_text = description_container.text.strip()

        return description_text if description_text else None
    except Exception as e:
        print(f"❌ Error fetching description for CID {cid}: {e}")
        return None

# ====== Selenium Setup ======
base_url = (
    "https://pubchem.ncbi.nlm.nih.gov/#query="
    "xYJirgzqaVZefGtl6R0iQ5gm9kbrFwD-etsbsmHKCbNh0zU"
    "&alias=PubChem%20Compound%20TOC%3A%20Drug%20and%20Medication%20Information&page="
)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ====== Scraping Loop ======
all_data = []
max_pages = 10  # Change to 400 for full scrape

for page_num in range(1, max_pages + 1):
    url = base_url + str(page_num)
    print(f"📄 Scraping page {page_num} → {url}")
    driver.get(url)
    time.sleep(5)  # Wait for JS to load

    soup = BeautifulSoup(driver.page_source, "html.parser")

    for item in soup.select("li.p-md-bottom"):
        # Compound Name
        name_tag = item.select_one(".f-1125 a span span")
        name = name_tag.get_text(strip=True) if name_tag else None

        # CID extraction (more reliable)
        cid_link = item.select_one('a[href^="https://pubchem.ncbi.nlm.nih.gov/compound/"]')
        if cid_link and "/compound/" in cid_link["href"]:
            try:
                cid = cid_link["href"].split("/compound/")[1].split("?")[0].strip()
            except:
                cid = None
        else:
            cid = None

        # Molecular Formula (MF)
        mf_tag = item.find("span", string="MF:")
        mf = mf_tag.find_next("span").get_text(strip=True) if mf_tag else None

        # Molecular Weight (MW)
        mw_tag = item.find("span", string="MW:")
        mw = mw_tag.find_next("span").get_text(strip=True) if mw_tag else None

        # IUPAC Name
        iupac_tag = item.find("span", string="IUPAC Name:")
        iupac_name = iupac_tag.find_next("span").get_text(strip=True) if iupac_tag else None

        # Fetch Description from the compound detail page
        description = get_description_from_page(driver, cid) if cid else None

        all_data.append({
            "name": name,
            "cid": cid,
            "description": description
        })

# ====== Close Browser ======
driver.quit()

# ====== Save JSON ======
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(f"✅ Extracted {len(all_data)} compounds from {max_pages} pages")
print(f"📂 Data saved at: {OUTPUT_FILE}")
