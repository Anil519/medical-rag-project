import requests
import json

BASE_URL = "https://api.fda.gov/drug/label.json"
LIMIT = 100
TOTAL_RECORDS = 500  # Adjust to fetch more or fewer records

def fetch_drugs(skip: int = 0):
    params = {
        "limit": LIMIT,
        "skip": skip
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"Error fetching drugs: {e}")
        return []

def extract_drug_info(entry):
    openfda = entry.get("openfda", {})

    # Try brand_name or generic_name first
    name_list = openfda.get("brand_name") or openfda.get("generic_name")

    # Fallback to package label
    if not name_list:
        name_list = entry.get("package_label_principal_display_panel")

    # Fallback to SPL product data
    if not name_list:
        name_list = entry.get("spl_product_data_elements")

    # Final fallback
    name = name_list[0] if name_list else "Unknown"

    # Extract description
    description_list = entry.get("indications_and_usage", ["No description available."])
    description = description_list[0].strip()

    return {
        "name": name.strip(),
        "description": description
    }

def main():
    all_drugs = []
    for skip in range(0, TOTAL_RECORDS, LIMIT):
        print(f"Fetching records {skip + 1} to {min(skip + LIMIT, TOTAL_RECORDS)}")
        results = fetch_drugs(skip)
        for entry in results:
            drug_info = extract_drug_info(entry)
            all_drugs.append(drug_info)

    print(f"\nTotal drugs collected: {len(all_drugs)}")

    # Save to JSON
    with open("openfda_drugs.json", "w", encoding="utf-8") as f:
        json.dump(all_drugs, f, ensure_ascii=False, indent=2)

    print("Saved to 'openfda_drugs.json' successfully.\n")

    # Preview top 10 entries
    print("Sample entries:\n")
    for drug in all_drugs[:10]:
        print(f"Name: {drug['name']}")
        print(f"Description: {drug['description']}\n")

if __name__ == "__main__":
    main()
