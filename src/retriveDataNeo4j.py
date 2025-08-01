from neo4j import GraphDatabase
import json

# ===== Neo4j Aura Cloud Connection =====
uri = "neo4j+s://a3c30e36.databases.neo4j.io"  # Replace with Aura URI
username = "neo4j"  # Default for Aura
password = "WpfI9Gu3epdkqaMxUZkm3ZbETLH1fHtecXqEiPqpk_I"  # Replace with Aura password

driver = GraphDatabase.driver(uri, auth=(username, password))

# ===== Search Function =====
def search_disease_or_symptom(tx, user_input):
    query = """
    // Check if input is a disease
    MATCH (d:Disease)
    WHERE toLower(d.name) CONTAINS toLower($input)
    OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
    OPTIONAL MATCH (d)-[:HAS_CAUSE]->(c:Cause)
    OPTIONAL MATCH (d)-[:HAS_PRECAUTION]->(p:Precaution)
    OPTIONAL MATCH (d)-[:TREATED_BY]->(dr:Drug)
    OPTIONAL MATCH (dr)-[:HAS_DESCRIPTION]->(desc:Description)
    RETURN DISTINCT d.name AS disease,
           collect(DISTINCT s.name) AS symptoms,
           collect(DISTINCT c.name) AS causes,
           collect(DISTINCT p.name) AS precautions,
           collect(DISTINCT dr.name) AS drugs,
           collect(DISTINCT desc.text) AS drug_descriptions

    UNION

    // Check if input is a symptom
    MATCH (s:Symptom)
    WHERE toLower(s.name) CONTAINS toLower($input)
    MATCH (d:Disease)-[:HAS_SYMPTOM]->(s)
    OPTIONAL MATCH (d)-[:HAS_CAUSE]->(c:Cause)
    OPTIONAL MATCH (d)-[:HAS_PRECAUTION]->(p:Precaution)
    OPTIONAL MATCH (d)-[:TREATED_BY]->(dr:Drug)
    OPTIONAL MATCH (dr)-[:HAS_DESCRIPTION]->(desc:Description)
    RETURN DISTINCT d.name AS disease,
           collect(DISTINCT s.name) AS symptoms,
           collect(DISTINCT c.name) AS causes,
           collect(DISTINCT p.name) AS precautions,
           collect(DISTINCT dr.name) AS drugs,
           collect(DISTINCT desc.text) AS drug_descriptions
    """
    result = tx.run(query, input=user_input)
    records = []
    for record in result:
        records.append({
            "disease": record["disease"],
            "symptoms": [s for s in record["symptoms"] if s],
            "causes": [c for c in record["causes"] if c],
            "precautions": [p for p in record["precautions"] if p],
            "drugs": [d for d in record["drugs"] if d],
            "drug_descriptions": [desc for desc in record["drug_descriptions"] if desc]
        })
    return records

# ===== Run Search =====
user_input = input("Enter disease name or symptom: ")

with driver.session() as session:
    results = session.execute_read(search_disease_or_symptom, user_input)

if results:
    print(json.dumps(results, indent=2, ensure_ascii=False))
else:
    print("❌ No data found for:", user_input)

driver.close()
