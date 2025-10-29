
import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# --- Configuration ---
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
PDF_BASE_PATH = os.path.join(BASE_DIR, "data", "Rapidise capabilities deck")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")

AUTOMOTIVE_PDF_PATH = os.path.join(PDF_BASE_PATH, "automotive")
SS_PDF_PATH = os.path.join(PDF_BASE_PATH, "s&s")

AUTOMOTIVE_CHROMA_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "automotive_chroma")
SS_CHROMA_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "s_s_chroma")

EMBEDDING_MODEL_NAME = "mxbai-embed-large"

def create_rag_for_domain(pdf_dir, chroma_path, domain_name):
    print(f"\n--- Creating RAG for {domain_name} domain ---")
    print(f"Loading documents from: {pdf_dir}")

    documents = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"  Loaded {filename}")
            except Exception as e:
                print(f"  Error loading {filename}: {e}")

    if not documents:
        print(f"No PDF documents found in {pdf_dir}. Skipping RAG creation for {domain_name}.")
        return

    print(f"Total documents loaded for {domain_name}: {len(documents)}")

    # --- Chunking ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Total chunks created for {domain_name}: {len(chunks)}")

    # --- Embeddings ---
    print(f"Initializing Ollama embeddings with model: {EMBEDDING_MODEL_NAME}")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

    # --- Chroma DB Creation ---
    print(f"Creating Chroma DB at: {chroma_path}")
    try:
        # Ensure the directory exists
        os.makedirs(chroma_path, exist_ok=True)
        db = Chroma.from_documents(chunks, embeddings, persist_directory=chroma_path)
        db.persist()
        print(f"Chroma DB for {domain_name} created successfully.")
    except Exception as e:
        print(f"Error creating Chroma DB for {domain_name}: {e}")

def main():
    # Create RAG for Automotive
    create_rag_for_domain(AUTOMOTIVE_PDF_PATH, AUTOMOTIVE_CHROMA_PATH, "Automotive")

    # Create RAG for Security & Surveillance
    create_rag_for_domain(SS_PDF_PATH, SS_CHROMA_PATH, "Security & Surveillance")

    print("\n--- RAG Creation Process Complete ---")

if __name__ == "__main__":
    main()
