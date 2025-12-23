"""
Build Customer DNA Knowledge Base for RAG classification.

Creates ChromaDB collection with embeddings from:
1. Problems customers talk about (exact phrases)
2. Outcomes customers promise (exact phrases)
3. Products customers sell
4. Buyer personas

Source: company_analysis_v02.csv
"""

import pandas as pd
import chromadb
import requests
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/embeddings'
EMBED_MODEL = 'mxbai-embed-large:latest'


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


def main():
    print("=" * 60)
    print("BUILDING CUSTOMER DNA KNOWLEDGE BASE")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load analysis CSV
    df = pd.read_csv('data/company_analysis_v02.csv')
    print(f"Loaded: {len(df)} companies")
    
    # Filter only OEM/ODM customers (not end users)
    odm_df = df[df['Company Type'] == 'OEM/ODM']
    print(f"ODM Customers: {len(odm_df)}")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="data/customer_dna_db")
    embed_fn = OllamaEmbed()
    
    # Delete existing collection if exists
    try:
        client.delete_collection(name="customer_dna")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name="customer_dna",
        embedding_function=embed_fn
    )
    
    # Build documents from each company
    documents = []
    metadatas = []
    ids = []
    
    print("\nProcessing companies...")
    
    for idx, row in odm_df.iterrows():
        company = str(row['Company Name'])
        product_cat = str(row.get('Product Category', ''))
        
        # Extract key fields
        problems = str(row.get('Problems Explicit', ''))
        outcomes = str(row.get('Outcomes Promised', ''))
        products = str(row.get('Products Mentioned', ''))
        personas = str(row.get('Buyer Persona', ''))
        keywords = str(row.get('Top Keywords', ''))
        language = str(row.get('Language Style', ''))
        
        # Create rich document for embedding
        doc = f"""CUSTOMER PROFILE: {company}

PRODUCT CATEGORY: {product_cat}

PROBLEMS THEY SOLVE:
{problems}

OUTCOMES THEY PROMISE:
{outcomes}

PRODUCTS THEY SELL:
{products}

WHO THEY SELL TO:
{personas}

KEY LANGUAGE:
{keywords}
"""
        
        documents.append(doc)
        metadatas.append({
            'company_name': company,
            'product_category': product_cat,
            'language_style': language,
            'type': 'customer_profile'
        })
        ids.append(f"customer_{idx}")
        
        print(f"  Added: {company[:40]}")
    
    # Also add individual problem/outcome statements for granular matching
    print("\nAdding granular problem statements...")
    stmt_idx = 0
    
    for idx, row in odm_df.iterrows():
        company = str(row['Company Name'])
        product_cat = str(row.get('Product Category', ''))
        
        # Split problems into individual statements
        problems = str(row.get('Problems Explicit', ''))
        if problems and len(problems) > 10:
            for problem in problems.split(','):
                problem = problem.strip()
                if len(problem) > 10:
                    documents.append(f"CUSTOMER PROBLEM: {problem}")
                    metadatas.append({
                        'company_name': company,
                        'product_category': product_cat,
                        'type': 'problem_statement'
                    })
                    ids.append(f"problem_{stmt_idx}")
                    stmt_idx += 1
        
        # Split outcomes into individual statements
        outcomes = str(row.get('Outcomes Promised', ''))
        if outcomes and len(outcomes) > 10:
            for outcome in outcomes.split(','):
                outcome = outcome.strip()
                if len(outcome) > 10:
                    documents.append(f"CUSTOMER OUTCOME: {outcome}")
                    metadatas.append({
                        'company_name': company,
                        'product_category': product_cat,
                        'type': 'outcome_statement'
                    })
                    ids.append(f"outcome_{stmt_idx}")
                    stmt_idx += 1
    
    print(f"Total statements added: {stmt_idx}")
    
    # Add to collection
    print(f"\nAdding {len(documents)} documents to ChromaDB...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Collection size: {collection.count()} documents")
    
    # Save summary
    print("\n" + "=" * 60)
    print("CUSTOMER DNA KB COMPLETE")
    print("=" * 60)
    print(f"Location: data/customer_dna_db")
    print(f"Collection: customer_dna")
    print(f"Total documents: {collection.count()}")


if __name__ == "__main__":
    main()
