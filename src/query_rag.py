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
    """
    Detects the domain (automotive vs security) from query keywords.
    Returns: 'automotive', 's&s', or 'general'
    """
    query_lower = query.lower()
    
    # Expanded automotive keywords - add more as needed
    automotive_keywords = [
        "automotive", "car", "vehicle", "auto", "driving", "adas", 
        "mobility", "telematics", "dashcam", "fleet", "dms", 
        "driver monitoring", "collision", "parking", "infotainment",
        "connected car", "v2x", "autonomous"
    ]
    
    # Expanded security keywords - add more as needed
    ss_keywords = [
        "security", "surveillance", "camera", "monitor", "safety", 
        "detection", "alarm", "cctv", "access control", "perimeter",
        "intrusion", "facial recognition", "nvr", "dvr", "ptz"
    ]
    
    # Check automotive first
    if any(keyword in query_lower for keyword in automotive_keywords):
        return "automotive"
    # Then check security
    elif any(keyword in query_lower for keyword in ss_keywords):
        return "s&s"
    # Default to general if no match
    else:
        return "general"

def main(query):
    """
    Main function to query the RAG system.
    """
    print("\n" + "="*60)
    print("🚀 RAG QUERY AGENT - INITIALIZING")
    print("="*60)
    print(f"📊 Embedding Model: {EMBEDDING_MODEL_NAME}")
    print(f"🤖 LLM Model: {LLM_MODEL_NAME}")
    print(f"💬 Query: \"{query}\"")
    print("="*60)
    
    # Initialize embeddings
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
        print("✅ Embeddings initialized")
    except Exception as e:
        print(f"❌ Error initializing embeddings: {e}")
        sys.exit(1)
    
    # Load Automotive RAG
    automotive_db = None
    try:
        automotive_db = Chroma(
            persist_directory=AUTOMOTIVE_CHROMA_PATH, 
            embedding_function=embeddings
        )
        automotive_retriever = automotive_db.as_retriever(search_kwargs={"k": 8})
        print(f"✅ Automotive RAG loaded ({AUTOMOTIVE_CHROMA_PATH})")
    except Exception as e:
        print(f"❌ Error loading Automotive RAG: {e}")
    
    # Load Security & Surveillance RAG
    ss_db = None
    try:
        ss_db = Chroma(
            persist_directory=SS_CHROMA_PATH, 
            embedding_function=embeddings
        )
        ss_retriever = ss_db.as_retriever(search_kwargs={"k": 8})
        print(f"✅ Security & Surveillance RAG loaded ({SS_CHROMA_PATH})")
    except Exception as e:
        print(f"❌ Error loading S&S RAG: {e}")
    
    # Check if at least one RAG loaded
    if not automotive_db and not ss_db:
        print("\n❌ FATAL: No RAG databases could be loaded. Exiting.")
        sys.exit(1)
    
    # Initialize LLM
    try:
        llm = Ollama(model=LLM_MODEL_NAME)
        print("✅ LLM initialized")
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        sys.exit(1)
    
    # Define prompt template
    template = """You are an expert on Rapidise's capabilities. Use the following context to answer the question.

If the context doesn't contain enough information, say so clearly. Do not make up information.
Provide specific details like metrics, certifications, or product names when available.

Context:
{context}

Question: {question}

Detailed Answer:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    
    print("\n" + "="*60)
    print("🔍 DOMAIN DETECTION")
    print("="*60)
    
    # Detect domain from query
    domain = get_domain_from_query(query)
    print(f"📌 Detected Domain: {domain.upper()}")
    
    # Select appropriate retriever
    selected_retriever = None
    if domain == "automotive" and automotive_db:
        selected_retriever = automotive_retriever
        print("📂 Using: Automotive RAG")
    elif domain == "s&s" and ss_db:
        selected_retriever = ss_retriever
        print("📂 Using: Security & Surveillance RAG")
    else:
        print("\n⚠️  WARNING: Could not determine domain or RAG not available")
        print("💡 TIP: Try using keywords like 'automotive', 'dashcam', 'security', or 'surveillance'")
        return
    
    # Create QA chain
    print("\n" + "="*60)
    print("⚙️  PROCESSING QUERY")
    print("="*60)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=selected_retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    
    # Execute query
    try:
        print("🔄 Searching knowledge base...")
        result = qa_chain.invoke({"query": query})
        
        print("\n" + "="*60)
        print("📝 ANSWER")
        print("="*60)
        print(result["result"])
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during query processing: {e}")
        print("💡 TIP: Make sure Ollama is running with the required models")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n" + "="*60)
        print("📖 USAGE")
        print("="*60)
        print('python3 src/query_rag.py "Your question here"')
        print("\nExamples:")
        print('  python3 src/query_rag.py "What automotive capabilities does Rapidise have?"')
        print('  python3 src/query_rag.py "Tell me about Rapidise\'s security solutions"')
        print("="*60 + "\n")
        sys.exit(1)
    
    query_text = sys.argv[1]
    main(query_text)