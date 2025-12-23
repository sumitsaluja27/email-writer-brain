"""
Build ChromaDB RAG from scraped sample company data.
Each document includes:
- Company name
- Product category (Beacon, IP Camera, Dashcam, Bodycam)
- Industry
- Assessment (why they're a customer)
- Website content (their language, problems they solve)
"""

import pandas as pd
import chromadb
from chromadb.config import Settings
import requests
from datetime import datetime

def get_embedding(text, model="mxbai-embed-large:latest"):
    """Get embedding from Ollama."""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["embedding"]
    except Exception as e:
        print(f"  Embedding error: {e}")
    return None

class OllamaEmbedding:
    """ChromaDB compatible embedding function."""
    def __init__(self, model="mxbai-embed-large:latest"):
        self.model = model
        self.api_url = "http://localhost:11434/api/embeddings"
    
    def name(self):
        return "ollama_mxbai"
    
    def __call__(self, input):
        embeddings = []
        for text in input:
            try:
                response = requests.post(
                    self.api_url,
                    json={"model": self.model, "prompt": text},
                    timeout=60
                )
                if response.status_code == 200:
                    embeddings.append(response.json()["embedding"])
                else:
                    embeddings.append([0.0] * 1024)
            except:
                embeddings.append([0.0] * 1024)
        return embeddings

def main():
    print("=" * 60)
    print("BUILDING RAG FROM SAMPLE COMPANIES")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load scraped data
    df = pd.read_csv('data/RAG/sample_companies_scraped.csv')
    print(f"Total companies: {len(df)}")
    
    # Filter out failed scrapes
    df = df[df['content_length'] > 0]
    print(f"With content: {len(df)}")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="data/chroma_db_v2")
    
    # Delete existing collection if exists
    try:
        client.delete_collection(name="customer_knowledge")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name="customer_knowledge",
        embedding_function=OllamaEmbedding()
    )
    
    # Add documents
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        company = str(row['company_name'])
        product = str(row['product_category'])
        industry = str(row['industry'])
        assessment = str(row['assessment'])
        content = str(row['website_content'])[:3000]  # Limit size
        
        # Create document with structured format
        doc = f"""PRODUCT CATEGORY: {product}

COMPANY: {company}
INDUSTRY: {industry}

WHY THEY ARE A CUSTOMER:
{assessment}

THEIR WEBSITE LANGUAGE:
{content[:2000]}
"""
        
        documents.append(doc)
        metadatas.append({
            "company_name": company,
            "product_category": product,
            "industry": industry,
            "assessment": assessment
        })
        ids.append(f"customer_{idx}")
        
        print(f"Adding: {company[:30]} ({product})")
    
    # Add to collection
    print(f"\nAdding {len(documents)} documents to ChromaDB...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Collection size: {collection.count()} documents")
    
    # Summary by category
    print("\n" + "=" * 60)
    print("RAG SUMMARY")
    print("=" * 60)
    print(df['product_category'].value_counts())
    print(f"\nSaved to: data/chroma_db_v2")
    print("Collection name: customer_knowledge")

if __name__ == "__main__":
    main()
