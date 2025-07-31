from langchain_huggingface import HuggingFacePipeline
from langchain_pinecone import PineconeVectorStore
from langchain_community.graphs import Neo4jGraph
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain import PromptTemplate
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import os
import logging
from dotenv import load_dotenv
from neo4j.exceptions import SyntaxError

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")

llm = HuggingFacePipeline.from_model_id(
    model_id="google/medgemma-4b-it",
    task="text-generation",
    pipeline_kwargs={"max_new_tokens": 200}
)

embedder = SentenceTransformer('dmis-lab/biobert-base-cased-v1.1')

vectorstore = PineconeVectorStore(index_name="medical-rag-index", embedding=embedder)

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password=os.getenv("NEO4J_PASSWORD"))

def retrieve_from_vector(query):
    try:
        results = vectorstore.similarity_search(query, k=3)
        if not results or results[0].metadata.get('score', 0) < 0.7:
            logging.warning("No relevant vector data found; falling back.")
            return "No relevant data found in DB."
        return "\n".join([res.page_content for res in results])
    except Exception as e:
        logging.error(f"Vector DB error: {str(e)}")
        return f"Vector DB error: {str(e)}. Falling back to reasoning."

def query_kg(query):
    try:
        cypher = llm.invoke(f"Convert to Cypher query: {query}")[0]['generated_text']
        # Basic Cypher validation (e.g., check for common keywords; extend with cypher-syntax parser if needed)
        if not all(keyword in cypher.upper() for keyword in ['MATCH', 'RETURN']):
            raise ValueError("Invalid Cypher syntax generated.")
        return graph.query(cypher)
    except (SyntaxError, ValueError) as e:
        logging.error(f"Invalid Cypher query: {str(e)}")
        return f"KG query error: Invalid Cypher syntax. Falling back to reasoning."
    except Exception as e:
        logging.error(f"KG query error: {str(e)}")
        return f"KG query error: {str(e)}. Falling back to reasoning."

tools = [
    Tool(name="VectorRetriever", func=retrieve_from_vector, description="Retrieve chunks from vector DB"),
    Tool(name="KGQuery", func=query_kg, description="Query knowledge graph for entities/relations")
]

prompt = PromptTemplate.from_template(
    "You are a medical AI. For query: {query}\n"
    "Use tools to retrieve if needed. If no data in DB, reason based on your knowledge.\n"
    "Tools: {tools}\nOutput response."
)

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def rag_query(query):
    try:
        response = executor.invoke({"query": query, "tools": ", ".join([t.name for t in tools])})
        logging.info(f"Processed query: {query}")
        return response['output']
    except Exception as e:
        logging.error(f"Agent error: {str(e)}")
        return llm.invoke(f"Reason directly on query '{query}' due to error: {str(e)}")['generated_text']

# Test
logging.info(rag_query("What is aspirin used for?"))