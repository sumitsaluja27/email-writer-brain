import os
import sys
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# --- Configuration ---
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")

AUTOMOTIVE_CHROMA_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "automotive_chroma")
SS_CHROMA_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "s_s_chroma")

EMBEDDING_MODEL_NAME = "mxbai-embed-large"
LLM_MODEL_NAME = "llama3.1"

def get_domain_from_query(query):
    query_lower = query.lower()
    automotive_keywords = ["automotive", "car", "vehicle", "auto", "driving", "ADAS", "mobility"]
    ss_keywords = ["security", "surveillance", "camera", "monitor", "safety", "detection", "alarm"]

    if any(keyword in query_lower for keyword in automotive_keywords):
        return "automotive"
    elif any(keyword in query_lower for keyword in ss_keywords):
        return "s&s"
    else:
        return "general" # Or ask for clarification

def main(query):
    print("\n--- Initializing RAG Query Agent ---")
    print(f"Using Embedding Model: {EMBEDDING_MODEL_NAME}")
    print(f"Using LLM Model: {LLM_MODEL_NAME}")

    # Initialize embeddings
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

    # Load Chroma DBs
    try:
        automotive_db = Chroma(persist_directory=AUTOMOTIVE_CHROMA_PATH, embedding_function=embeddings)
        automotive_retriever = automotive_db.as_retriever()
        print(f"Loaded Automotive RAG from {AUTOMOTIVE_CHROMA_PATH}")
    except Exception as e:
        print(f"Error loading Automotive RAG: {e}")
        automotive_db = None

    try:
        ss_db = Chroma(persist_directory=SS_CHROMA_PATH, embedding_function=embeddings)
        ss_retriever = ss_db.as_retriever()
        print(f"Loaded S&S RAG from {SS_CHROMA_PATH}")
    except Exception as e:
        print(f"Error loading S&S RAG: {e}")
        ss_db = None

    if not automotive_db and not ss_db:
        print("No RAG databases could be loaded. Exiting.")
        sys.exit(1)

    # Initialize LLM
    llm = Ollama(model=LLM_MODEL_NAME)

    # Define a custom prompt template
    template = """Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Keep the answer as concise as possible.
    {context}
    Question: {question}
    Concise Answer:"""
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    print("\n--- RAG Query Agent Ready ---")
    
    domain = get_domain_from_query(query)
    print(f"Detected domain: {domain.upper()}")

    selected_retriever = None
    if domain == "automotive" and automotive_db:
        selected_retriever = automotive_retriever
    elif domain == "s&s" and ss_db:
        selected_retriever = ss_retriever
    else:
        print("Could not determine specific domain or RAG not loaded. Skipping query.")
        return

    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=selected_retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    try:
        result = qa_chain.invoke({"query": query})
        print("\n--- Answer ---")
        print(result["result"])
        print("--------------")
    except Exception as e:
        print(f"An error occurred during query processing: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_rag.py \"Your query here\"")
        sys.exit(1)
    query_text = sys.argv[1]
    main(query_text)