

import os
import sys
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# --- Configuration ---
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
PDF_BASE_PATH = os.path.join(BASE_DIR, "data", "Rapidise_capabilities_deck")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")

EMBEDDING_MODEL_NAME = "mxbai-embed-large"

# Define the structure for each database
DB_CONFIGS = {
    "beacon_capabilities": {
        "product_name": "beacon",
        "sources": [
            os.path.join(PDF_BASE_PATH, "beacon", "faqs"),
            os.path.join(PDF_BASE_PATH, "beacon", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "body_cam_capabilities": {
        "product_name": "body_cam",
        "sources": [
            os.path.join(PDF_BASE_PATH, "body_cam", "faqs"),
            os.path.join(PDF_BASE_PATH, "body_cam", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "dashcam_capabilities": {
        "product_name": "dashcam",
        "sources": [
            os.path.join(PDF_BASE_PATH, "dashcam", "faqs"),
            os.path.join(PDF_BASE_PATH, "dashcam", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "in_cabin_capabilities": {
        "product_name": "in_cabin",
        "sources": [
            os.path.join(PDF_BASE_PATH, "in_cabin", "faqs"),
            os.path.join(PDF_BASE_PATH, "in_cabin", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "ip_camera_capabilities": {
        "product_name": "ip_camera",
        "sources": [
            os.path.join(PDF_BASE_PATH, "ip_camera", "faqs"),
            os.path.join(PDF_BASE_PATH, "ip_camera", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "access_control_capabilities": {
        "product_name": "access_control",
        "sources": [
            os.path.join(PDF_BASE_PATH, "access_control", "faqs"),
            os.path.join(PDF_BASE_PATH, "access_control", "pdfs"),
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
    "rapidise_core_capabilities": {
        "product_name": "rapidise_core",
        "sources": [
            os.path.join(PDF_BASE_PATH, "common_pdfs"),
        ],
    },
}

def load_and_process_pdfs(pdf_dirs: List[str], product_name: str) -> List[Document]:
    """
    Loads PDFs from specified directories, applies conditional chunking,
    and adds custom metadata.
    """
    all_processed_documents = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    for pdf_dir in pdf_dirs:
        if not os.path.exists(pdf_dir):
            print(f"  Warning: Directory not found: {pdf_dir}. Skipping.")
            continue

        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(pdf_dir, filename)
                print(f"    Loading file: {filename}")
                
                try:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load() # docs is a list of Document objects, one per page

                    if not docs:
                        print(f"      No content found in {filename}. Skipping.")
                        continue

                    content_type = "faq" if "faq" in filename.lower() else "capability_pdf"
                    
                    if content_type == "faq":
                        # For FAQs, treat the entire document as a single chunk
                        full_content = "\n".join([doc.page_content for doc in docs])
                        metadata = {
                            "source": filename,
                            "product": product_name,
                            "content_type": content_type,
                            "page": "all" # Indicate it's the whole document
                        }
                        all_processed_documents.append(Document(page_content=full_content, metadata=metadata))
                        print(f"      Processed {filename} as single FAQ document.")
                    else:
                        # For other PDFs, chunk them and add metadata
                        chunks = text_splitter.split_documents(docs)
                        for chunk in chunks:
                            # Ensure page number is extracted correctly from original metadata
                            page_num = chunk.metadata.get('page', 'N/A')
                            chunk.metadata.update({
                                "source": filename,
                                "product": product_name,
                                "content_type": content_type,
                                "page": page_num
                            })
                            all_processed_documents.append(chunk)
                        print(f"      Chunked {filename} into {len(chunks)} parts.")

                except Exception as e:
                    print(f"    Error processing {filename}: {e}. Skipping.")
    return all_processed_documents

def main():
    # Ensure knowledge_base directory exists
    os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)

    print(f"Initializing Ollama embeddings with model: {EMBEDDING_MODEL_NAME}")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

    for db_name, config in DB_CONFIGS.items():
        product_name = config["product_name"]
        source_dirs = config["sources"]
        chroma_persist_path = os.path.join(KNOWLEDGE_BASE_PATH, db_name)

        print(f"\n--- Creating RAG for {db_name} (Product: {product_name}) ---")
        print(f"  ChromaDB will be persisted at: {chroma_persist_path}")
        os.makedirs(chroma_persist_path, exist_ok=True) # Ensure specific DB path exists

        processed_docs = load_and_process_pdfs(source_dirs, product_name)

        if not processed_docs:
            print(f"  No documents processed for {db_name}. Skipping ChromaDB creation.")
            continue

        print(f"  Total processed documents/chunks for {db_name}: {len(processed_docs)}")
        
        try:
            # Create Chroma DB
            db = Chroma.from_documents(
                documents=processed_docs,
                embedding=embeddings,
                persist_directory=chroma_persist_path
            )
            # db.persist() # persist() is deprecated in newer Chroma versions
            print(f"  ChromaDB for {db_name} created successfully.")
        except Exception as e:
            print(f"  Error creating ChromaDB for {db_name}: {e}")

    print("\n--- All RAG Creation Processes Complete ---")

if __name__ == "__main__":
    main()
