"""
Rapidise Company Classification Pipeline - RAG Builder
=======================================================

Consolidated RAG database building functionality.
Combines: build_customer_dna.py, build_customer_rag.py, build_rapidise_fit.py, test_rag.py

Creates ChromaDB collections for:
1. Customer DNA - profiles of existing customers
2. Rapidise Fit - product matching database
"""

import requests
import json
import os
from datetime import datetime

try:
    import chromadb
    import pandas as pd
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb or pandas not installed")

try:
    from .config import (
        OLLAMA_EMBED_URL, EMBED_MODEL, CUSTOMER_DNA_DB, 
        RAPIDISE_FIT_DB, PRODUCTS, DATA_DIR
    )
except ImportError:
    OLLAMA_EMBED_URL = 'http://localhost:11434/api/embeddings'
    EMBED_MODEL = 'mxbai-embed-large:latest'
    CUSTOMER_DNA_DB = 'data/customer_dna_db'
    RAPIDISE_FIT_DB = 'data/rapidise_fit_db'


# =============================================================================
# OLLAMA EMBEDDING CLASS
# =============================================================================

class OllamaEmbed:
    """ChromaDB compatible embedding function using Ollama."""
    
    def __init__(self, model=EMBED_MODEL):
        self.api_url = OLLAMA_EMBED_URL
        self.model = model
    
    def name(self):
        return 'ollama_mxbai'
    
    def __call__(self, input):
        return self._get_embeddings(input)
    
    def embed_query(self, input):
        if isinstance(input, str):
            return self._get_embeddings([input])[0]
        return self._get_embeddings(input)
    
    def embed_documents(self, documents):
        return self._get_embeddings(documents)
    
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
                    embeddings.append([0.0] * 1024)
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0] * 1024)
        return embeddings


# =============================================================================
# CUSTOMER DNA DATABASE
# =============================================================================

def build_customer_dna_db(csv_path='data/company_analysis_v02.csv', db_path=None):
    """
    Build Customer DNA knowledge base from company analysis CSV.
    
    This creates embeddings from:
    - Problems customers talk about
    - Outcomes customers promise
    - Products customers sell
    - Buyer personas
    """
    if not CHROMADB_AVAILABLE:
        print("Error: chromadb not available")
        return False
    
    db_path = db_path or str(CUSTOMER_DNA_DB)
    
    print("=" * 60)
    print("BUILDING CUSTOMER DNA KNOWLEDGE BASE")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded: {len(df)} companies from {csv_path}")
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        return False
    
    # Filter ODM customers
    if 'Company Type' in df.columns:
        odm_df = df[df['Company Type'] == 'OEM/ODM']
    else:
        odm_df = df
    print(f"ODM Customers: {len(odm_df)}")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=db_path)
    embed_fn = OllamaEmbed()
    
    # Delete existing collection
    try:
        client.delete_collection(name="customer_dna")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name="customer_dna",
        embedding_function=embed_fn
    )
    
    # Build documents
    documents = []
    metadatas = []
    ids = []
    
    print("\nProcessing companies...")
    
    for idx, row in odm_df.iterrows():
        company = str(row.get('Company Name', f'Company_{idx}'))
        product_cat = str(row.get('Product Category', ''))
        
        # Build rich document
        doc = f"""CUSTOMER PROFILE: {company}
PRODUCT CATEGORY: {product_cat}
PROBLEMS: {row.get('Problems Explicit', '')}
OUTCOMES: {row.get('Outcomes Promised', '')}
PRODUCTS: {row.get('Products Mentioned', '')}
PERSONAS: {row.get('Buyer Persona', '')}
KEYWORDS: {row.get('Top Keywords', '')}"""
        
        documents.append(doc)
        metadatas.append({
            'company_name': company,
            'product_category': product_cat,
            'type': 'customer_profile'
        })
        ids.append(f"customer_{idx}")
        
        print(f"  Added: {company[:40]}")
    
    # Add to collection
    if documents:
        print(f"\nAdding {len(documents)} documents to ChromaDB...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    print(f"\n{'='*60}")
    print(f"CUSTOMER DNA DB COMPLETE")
    print(f"Location: {db_path}")
    print(f"Documents: {collection.count()}")
    print("=" * 60)
    
    return True


# =============================================================================
# RAPIDISE FIT DATABASE
# =============================================================================

def build_rapidise_fit_db(db_path=None, products=None):
    """
    Build Rapidise product fit database.
    
    Creates embeddings for each product category to match against companies.
    """
    if not CHROMADB_AVAILABLE:
        print("Error: chromadb not available")
        return False
    
    db_path = db_path or str(RAPIDISE_FIT_DB)
    
    # Use default products if not provided
    if products is None:
        try:
            from .config import PRODUCTS
        except:
            PRODUCTS = {
                "dashcam": {
                    "name": "Dashcam",
                    "description": "Fleet and consumer dashcams",
                    "keywords": ["dashcam", "fleet camera", "DVR"],
                    "customer_types": ["fleet operators", "telematics providers"]
                },
                "bodycam": {
                    "name": "Body Camera",
                    "description": "Body-worn cameras",
                    "keywords": ["body camera", "bodycam", "BWV"],
                    "customer_types": ["law enforcement", "security"]
                },
                "ip_camera": {
                    "name": "IP Camera",
                    "description": "Network security cameras",
                    "keywords": ["IP camera", "CCTV", "surveillance"],
                    "customer_types": ["security integrators", "enterprise"]
                },
                "in_cabin": {
                    "name": "In-Cabin / DMS",
                    "description": "Driver monitoring systems",
                    "keywords": ["DMS", "driver monitoring", "fatigue"],
                    "customer_types": ["automotive OEMs", "fleet management"]
                },
                "access_control": {
                    "name": "Access Control",
                    "description": "Access control devices",
                    "keywords": ["access control", "door controller"],
                    "customer_types": ["security integrators"]
                },
                "beacon": {
                    "name": "Beacon / IoT",
                    "description": "BLE beacons, asset trackers",
                    "keywords": ["beacon", "BLE", "tracker"],
                    "customer_types": ["logistics", "cold chain"]
                }
            }
        products = PRODUCTS
    
    print("=" * 60)
    print("BUILDING RAPIDISE FIT DATABASE")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=db_path)
    embed_fn = OllamaEmbed()
    
    # Delete existing
    try:
        client.delete_collection(name="rapidise_fit")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name="rapidise_fit",
        embedding_function=embed_fn
    )
    
    # Build documents for each product
    documents = []
    metadatas = []
    ids = []
    
    for product_id, product in products.items():
        # Create rich document for product
        doc = f"""RAPIDISE PRODUCT: {product['name']}
DESCRIPTION: {product['description']}
KEYWORDS: {', '.join(product['keywords'])}
IDEAL CUSTOMERS: {', '.join(product['customer_types'])}"""
        
        documents.append(doc)
        metadatas.append({
            'product_id': product_id,
            'product_name': product['name'],
            'type': 'product_definition'
        })
        ids.append(f"product_{product_id}")
        
        print(f"  Added: {product['name']}")
    
    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"\n{'='*60}")
    print(f"RAPIDISE FIT DB COMPLETE")
    print(f"Location: {db_path}")
    print(f"Products: {collection.count()}")
    print("=" * 60)
    
    return True


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def query_customer_dna(query_text, n_results=5, db_path=None):
    """Query the Customer DNA database."""
    db_path = db_path or str(CUSTOMER_DNA_DB)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(
        name="customer_dna",
        embedding_function=OllamaEmbed()
    )
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )
    
    return results


def query_rapidise_fit(query_text, n_results=3, db_path=None):
    """Query the Rapidise Fit database."""
    db_path = db_path or str(RAPIDISE_FIT_DB)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(
        name="rapidise_fit",
        embedding_function=OllamaEmbed()
    )
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build RAG databases")
    parser.add_argument("--customer-dna", action="store_true", help="Build Customer DNA DB")
    parser.add_argument("--rapidise-fit", action="store_true", help="Build Rapidise Fit DB")
    parser.add_argument("--all", action="store_true", help="Build all databases")
    parser.add_argument("--test", help="Test query against databases")
    
    args = parser.parse_args()
    
    if args.all or args.customer_dna:
        build_customer_dna_db()
    
    if args.all or args.rapidise_fit:
        build_rapidise_fit_db()
    
    if args.test:
        print("\nTesting Customer DNA query...")
        results = query_customer_dna(args.test)
        if results['metadatas']:
            for meta, dist in zip(results['metadatas'][0], results['distances'][0]):
                print(f"  {meta['company_name']}: {dist:.3f}")
