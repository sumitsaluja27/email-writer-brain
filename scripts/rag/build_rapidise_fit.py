"""
Build Rapidise Fit Knowledge Base from PDFs.

Extracts text from Rapidise product PDFs and creates embeddings for:
1. Products Rapidise can manufacture
2. Problems Rapidise solves  
3. Capabilities and services
"""

import os
import chromadb
import requests
from datetime import datetime

# Try to import PDF reader
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("pdfplumber not installed. Installing...")
    import subprocess
    subprocess.run(['pip', 'install', 'pdfplumber'], check=True)
    import pdfplumber
    PDF_AVAILABLE = True

OLLAMA_URL = 'http://localhost:11434/api/embeddings'
EMBED_MODEL = 'mxbai-embed-large:latest'

PDF_DIR = "data/rapidise_capabilities_deck/rapidise_capabilities_deck_&_products/All pdfs for rapidise"


class OllamaEmbed:
    """ChromaDB compatible embedding function for Ollama."""
    def __init__(self):
        self.api_url = OLLAMA_URL
        self.model = EMBED_MODEL
    
    def name(self):
        return 'ollama_mxbai'
    
    def __call__(self, input):
        return self._get_embeddings(input)
    
    def embed_query(self, input):
        return self._get_embeddings(input)
    
    def embed_documents(self, input):
        return self._get_embeddings(input)
    
    def _get_embeddings(self, texts):
        embeddings = []
        for text in texts:
            try:
                resp = requests.post(
                    self.api_url, 
                    json={'model': self.model, 'prompt': str(text)}, 
                    timeout=60
                )
                if resp.status_code == 200:
                    embeddings.append(resp.json()['embedding'])
                else:
                    embeddings.append([0.0]*1024)
            except:
                embeddings.append([0.0]*1024)
        return embeddings


def extract_pdf_text(pdf_path, max_chars=8000):
    """Extract text from a PDF file."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:20]:  # Limit to first 20 pages
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text[:max_chars]
    except Exception as e:
        print(f"  Error reading PDF: {e}")
        return ""


def main():
    print("=" * 60)
    print("BUILDING RAPIDISE FIT KNOWLEDGE BASE")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # List PDFs
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDFs")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="data/rapidise_fit_db")
    embed_fn = OllamaEmbed()
    
    # Delete existing collection if exists
    try:
        client.delete_collection(name="rapidise_fit")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name="rapidise_fit",
        embedding_function=embed_fn
    )
    
    documents = []
    metadatas = []
    ids = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        product_name = pdf_file.replace('.pdf', '').strip()
        
        print(f"\nProcessing: {pdf_file}")
        
        # Extract text
        text = extract_pdf_text(pdf_path)
        if not text:
            print(f"  No text extracted, skipping")
            continue
        
        print(f"  Extracted {len(text)} chars")
        
        # Create document for full PDF
        doc = f"""RAPIDISE PRODUCT: {product_name}

CAPABILITIES:
{text[:6000]}
"""
        documents.append(doc)
        metadatas.append({
            'product': product_name,
            'source': pdf_file,
            'type': 'product_capability'
        })
        ids.append(f"rapidise_{len(ids)}")
        
        # Also chunk text for more granular matching
        chunk_size = 1500
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for i, chunk in enumerate(chunks[:5]):  # Max 5 chunks per PDF
            if len(chunk.strip()) > 200:
                documents.append(f"RAPIDISE {product_name}: {chunk}")
                metadatas.append({
                    'product': product_name,
                    'source': pdf_file,
                    'type': 'product_chunk',
                    'chunk': i
                })
                ids.append(f"rapidise_{len(ids)}")
        
        print(f"  Added {1 + min(len(chunks), 5)} documents")
    
    # Add to collection
    print(f"\nAdding {len(documents)} documents to ChromaDB...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Collection size: {collection.count()} documents")
    
    print("\n" + "=" * 60)
    print("RAPIDISE FIT KB COMPLETE")
    print("=" * 60)
    print(f"Location: data/rapidise_fit_db")
    print(f"Collection: rapidise_fit")
    print(f"Total documents: {collection.count()}")


if __name__ == "__main__":
    main()
