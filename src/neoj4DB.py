from neo4j import GraphDatabase

# ====== Neo4j Aura Cloud Connection ======
uri = "neo4j+s://a3c30e36.databases.neo4j.io"  # from Aura
username = "neo4j"  # default
password = "WpfI9Gu3epdkqaMxUZkm3ZbETLH1fHtecXqEiPqpk_I"  # from Aura

driver = GraphDatabase.driver(uri, auth=(username, password))

# ====== Your Data ======
data = [
    {
        "name": "Influenza",
        "symptoms": "Fever, Cough, Sore throat, Muscle aches, Fatigue, Headache, Runny nose",
        "cause": "Influenza virus (types A, B, C, or D)",
        "precautions": "Annual vaccination, Wash hands regularly, Avoid contact with sick individuals, Wear masks in crowded places",
        "drugs": "Oseltamivir, Zanamivir",
        "drug_descriptions": {
            "Oseltamivir": "An antiviral medication that inhibits influenza virus neuraminidase, reducing viral spread.",
            "Zanamivir": "An inhaled antiviral that prevents influenza virus release from infected cells."
        },
        "description": "A contagious respiratory illness..."
    },
    {
        "name": "Tuberculosis",
        "symptoms": "Persistent cough, Chest pain, Weight loss, Night sweats, Fever, Fatigue",
        "cause": "Mycobacterium tuberculosis (bacterial infection)",
        "precautions": "BCG vaccination, Avoid close contact with infected individuals, Ensure good ventilation, Wear masks in high-risk settings",
        "drugs": "Isoniazid, Rifampin",
        "drug_descriptions": {
            "Isoniazid": "A bactericidal antibiotic that inhibits mycobacterial cell wall synthesis.",
            "Rifampin": "A bactericidal antibiotic that inhibits bacterial RNA polymerase."
        },
        "description": "A serious infectious disease primarily affecting the lungs..."
    }
]

# ====== Function to Insert Triples ======
def insert_triples(tx, disease):
    # Disease node
    tx.run("MERGE (d:Disease {name: $name}) SET d.description = $description",
           name=disease["name"], description=disease["description"])

    # Symptoms
    for symptom in disease["symptoms"].split(","):
        symptom = symptom.strip()
        tx.run("""
        MERGE (s:Symptom {name: $symptom})
        MERGE (d:Disease {name: $name})
        MERGE (d)-[:HAS_SYMPTOM]->(s)
        """, name=disease["name"], symptom=symptom)

    # Cause
    tx.run("""
    MERGE (c:Cause {name: $cause})
    MERGE (d:Disease {name: $name})
    MERGE (d)-[:HAS_CAUSE]->(c)
    """, name=disease["name"], cause=disease["cause"])

    # Precautions
    for precaution in disease["precautions"].split(","):
        precaution = precaution.strip()
        tx.run("""
        MERGE (p:Precaution {name: $precaution})
        MERGE (d:Disease {name: $name})
        MERGE (d)-[:HAS_PRECAUTION]->(p)
        """, name=disease["name"], precaution=precaution)

    # Drugs & descriptions
    for drug, desc in disease["drug_descriptions"].items():
        tx.run("""
        MERGE (dr:Drug {name: $drug})
        MERGE (d:Disease {name: $name})
        MERGE (d)-[:TREATED_BY]->(dr)
        """, name=disease["name"], drug=drug)
        tx.run("""
        MERGE (desc:Description {text: $desc})
        MERGE (dr:Drug {name: $drug})
        MERGE (dr)-[:HAS_DESCRIPTION]->(desc)
        """, drug=drug, desc=desc)

# ====== Insert All Data ======
with driver.session() as session:
    for item in data:
        session.execute_write(insert_triples, item)

driver.close()
print("✅ Data inserted successfully into Neo4j Aura Cloud")
