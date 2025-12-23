"""
Build ChromaDB Vector Database for Rapidise RAG

This script:
1. Loads Rapidise product PDFs from data/Rapidise_capabilities_deck/
2. Loads customer profile documents from docs/product_definitions/
3. Creates embeddings using mxbai-embed-large
4. Stores in ChromaDB for persistent RAG
"""

import os
import chromadb
from chromadb.utils import embedding_functions
import requests

# Paths
PDF_DIR = "data/Rapidise_capabilities_deck"
PROFILES_DIR = "docs/product_definitions"
CHROMA_DIR = "data/chroma_db"

# Ollama embedding through custom function
class OllamaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_name="mxbai-embed-large:latest"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/embeddings"
    
    def __call__(self, input_texts):
        embeddings = []
        for text in input_texts:
            try:
                response = requests.post(self.api_url, json={
                    'model': self.model_name,
                    'prompt': text[:2000]  # Limit text length
                }, timeout=60)
                if response.status_code == 200:
                    emb = response.json().get('embedding', [])
                    embeddings.append(emb)
                else:
                    embeddings.append([0.0] * 1024)  # Placeholder
            except Exception as e:
                print(f"  Embedding error: {e}")
                embeddings.append([0.0] * 1024)
        return embeddings

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber or fallback."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:10]:  # First 10 pages max
                text += page.extract_text() or ""
            return text[:5000]  # Limit to 5000 chars
    except ImportError:
        print("  pdfplumber not installed, using filename only")
        return os.path.basename(pdf_path)
    except Exception as e:
        print(f"  PDF error: {e}")
        return os.path.basename(pdf_path)

def load_customer_profiles():
    """Load customer profile markdown files."""
    profiles = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith('_customer_profile.md'):
            filepath = os.path.join(PROFILES_DIR, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            category = filename.replace('_customer_profile.md', '')
            profiles.append({
                'id': f"profile_{category}",
                'content': content[:3000],  # Limit size
                'metadata': {'type': 'customer_profile', 'category': category}
            })
    return profiles

def load_product_pdfs():
    """Load PDFs from each product category."""
    documents = []
    for category in os.listdir(PDF_DIR):
        category_path = os.path.join(PDF_DIR, category)
        if not os.path.isdir(category_path):
            continue
        
        pdf_folder = os.path.join(category_path, 'pdfs')
        if not os.path.exists(pdf_folder):
            continue
        
        for filename in os.listdir(pdf_folder):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(pdf_folder, filename)
                print(f"  Loading: {category}/{filename}")
                text = extract_text_from_pdf(pdf_path)
                if text:
                    documents.append({
                        'id': f"pdf_{category}_{filename}",
                        'content': text,
                        'metadata': {'type': 'product_pdf', 'category': category, 'filename': filename}
                    })
    return documents

def build_chromadb():
    """Build the ChromaDB vector database."""
    print("="*60)
    print("BUILDING CHROMADB FOR RAPIDISE RAG")
    print("="*60)
    
    # Initialize ChromaDB
    print("\n[1] Initializing ChromaDB...")
    if os.path.exists(CHROMA_DIR):
        import shutil
        shutil.rmtree(CHROMA_DIR)
    
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Create embedding function
    embed_fn = OllamaEmbeddingFunction()
    
    # Create collection
    collection = client.create_collection(
        name="rapidise_knowledge",
        embedding_function=embed_fn
    )
    print(f"  Created collection: rapidise_knowledge")
    
    # Load customer profiles
    print("\n[2] Loading customer profiles...")
    profiles = load_customer_profiles()
    print(f"  Loaded {len(profiles)} profiles")
    
    # Add profiles to collection
    print("\n[3] Adding customer profiles to ChromaDB...")
    for profile in profiles:
        print(f"  Adding: {profile['metadata']['category']}")
        collection.add(
            ids=[profile['id']],
            documents=[profile['content']],
            metadatas=[profile['metadata']]
        )
    
    # Load PDFs
    print("\n[4] Loading product PDFs...")
    pdfs = load_product_pdfs()
    print(f"  Loaded {len(pdfs)} PDFs")
    
    # Add PDFs to collection
    print("\n[5] Adding PDFs to ChromaDB...")
    for doc in pdfs:
        print(f"  Adding: {doc['metadata']['category']}/{doc['metadata']['filename']}")
        try:
            collection.add(
                ids=[doc['id']],
                documents=[doc['content']],
                metadatas=[doc['metadata']]
            )
        except Exception as e:
            print(f"    Error: {e}")
    
    # Verify
    print("\n[6] Verifying...")
    count = collection.count()
    print(f"  Total documents in ChromaDB: {count}")
    
    print("\n" + "="*60)
    print("CHROMADB BUILT SUCCESSFULLY")
    print(f"Location: {CHROMA_DIR}")
    print("="*60)
    
    return collection

if __name__ == "__main__":
    build_chromadb()
