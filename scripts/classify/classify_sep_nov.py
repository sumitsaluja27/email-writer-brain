"""
Run RAG Classifier on sep_nov.csv companies.
Uses Customer DNA KB + Rapidise Fit KB for classification.
"""

import pandas as pd
import chromadb
import requests
import json
from datetime import datetime
import time

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_EMBED_URL = 'http://localhost:11434/api/embeddings'
MODEL = 'llama3.1:8b'
EMBED_MODEL = 'mxbai-embed-large:latest'
JINA_API = 'https://r.jina.ai/'


class OllamaEmbed:
    def __init__(self):
        self.api_url = OLLAMA_EMBED_URL
        self.model = EMBED_MODEL
    def name(self):
        return 'ollama_mxbai'
    def __call__(self, input):
        return self._get_embeddings(input)
    def embed_query(self, input):
        return self._get_embeddings(input)
    def _get_embeddings(self, texts):
        embeddings = []
        for text in texts:
            try:
                resp = requests.post(self.api_url, json={'model': self.model, 'prompt': str(text)}, timeout=60)
                if resp.status_code == 200:
                    embeddings.append(resp.json()['embedding'])
                else:
                    embeddings.append([0.0]*1024)
            except:
                embeddings.append([0.0]*1024)
        return embeddings


def scrape_website(url, max_chars=3000):
    """Scrape website content using Jina API."""
    if not url or pd.isna(url):
        return ""
    try:
        url = str(url).strip()
        if not url.startswith('http'):
            url = 'https://' + url
        response = requests.get(JINA_API + url, timeout=30, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            return response.text[:max_chars]
    except:
        pass
    return ""


def classify_company(name, website, industry, cust_collection, rap_collection):
    """Classify a company using both KBs."""
    
    # Scrape website
    content = scrape_website(website)
    if len(content) < 50:
        return {
            'classification': 'UNKNOWN',
            'confidence': 0.0,
            'reasoning': 'Could not scrape website',
            'similar_customers': '',
            'rapidise_products': ''
        }
    
    # Query both KBs
    query = f"{name} {industry} {content[:1000]}"
    
    # Customer DNA matches
    cust_results = cust_collection.query(query_texts=[query], n_results=3, include=['metadatas', 'distances'])
    similar = []
    if cust_results['metadatas'] and cust_results['metadatas'][0]:
        for meta, dist in zip(cust_results['metadatas'][0], cust_results['distances'][0]):
            similar.append(f"{meta.get('company_name', '')} ({dist:.0f})")
    
    # Rapidise Fit matches
    rap_results = rap_collection.query(query_texts=[query], n_results=2, include=['metadatas', 'distances'])
    products = []
    if rap_results['metadatas'] and rap_results['metadatas'][0]:
        for meta, dist in zip(rap_results['metadatas'][0], rap_results['distances'][0]):
            products.append(f"{meta.get('product', '')} ({dist:.0f})")
    
    avg_cust_dist = sum(d for d in cust_results['distances'][0]) / max(len(cust_results['distances'][0]), 1)
    avg_rap_dist = sum(d for d in rap_results['distances'][0]) / max(len(rap_results['distances'][0]), 1)
    
    # LLM Classification
    prompt = f"""Classify if this company is RELEVANT for an ODM manufacturer (Rapidise) that makes cameras and IoT devices.

COMPANY:
Name: {name}
Industry: {industry}
Website excerpt: {content[:1500]}

SIMILAR CUSTOMERS (from our existing customer database):
{', '.join(similar)}
Average distance: {avg_cust_dist:.0f} (lower = more similar)

RAPIDISE PRODUCTS THAT MIGHT FIT:
{', '.join(products)}

RULES:
- RELEVANT if they SELL cameras, dashcams, bodycams, security devices, telematics
- RELEVANT if they NEED custom camera/device manufacturing
- NOT_RELEVANT if software-only, consulting, unrelated industry
- NOT_RELEVANT if they just USE cameras (end user)

JSON response only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "confidence": 0.0-1.0, "reasoning": "brief reason"}}"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0.1}
        }, timeout=90)
        
        if response.status_code == 200:
            result = response.json()['response']
            parsed = json.loads(result)
            return {
                'classification': parsed.get('classification', 'UNKNOWN'),
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', '')[:100],
                'similar_customers': ', '.join(similar),
                'rapidise_products': ', '.join(products)
            }
    except Exception as e:
        pass
    
    return {
        'classification': 'UNKNOWN',
        'confidence': 0.0,
        'reasoning': 'LLM error',
        'similar_customers': ', '.join(similar),
        'rapidise_products': ', '.join(products)
    }


def main():
    print("=" * 60)
    print("RAG CLASSIFICATION - SEP_NOV COMPANIES")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load companies
    df = pd.read_csv('data/Companies/sep_nov.csv')
    print(f"Total companies: {len(df)}")
    
    # Load KBs
    client1 = chromadb.PersistentClient(path='data/customer_dna_db')
    cust_col = client1.get_collection(name='customer_dna', embedding_function=OllamaEmbed())
    print(f"Customer DNA KB: {cust_col.count()} documents")
    
    client2 = chromadb.PersistentClient(path='data/rapidise_fit_db')
    rap_col = client2.get_collection(name='rapidise_fit', embedding_function=OllamaEmbed())
    print(f"Rapidise Fit KB: {rap_col.count()} documents")
    
    results = []
    
    for idx, row in df.iterrows():
        name = str(row['Company Name']).strip()
        website = str(row.get('Website', '')).strip()
        industry = str(row.get('Industry', '')).strip()
        
        print(f"[{idx+1}/{len(df)}] {name[:35]}...", end=" ", flush=True)
        
        result = classify_company(name, website, industry, cust_col, rap_col)
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'Classification': result['classification'],
            'Confidence': result['confidence'],
            'Reasoning': result['reasoning'],
            'Similar Customers': result['similar_customers'],
            'Rapidise Products': result['rapidise_products']
        })
        
        print(f"{result['classification']} ({result['confidence']:.1f})")
        
        time.sleep(0.5)  # Rate limiting
    
    # Save results
    result_df = pd.DataFrame(results)
    output_path = 'data/Companies/sep_nov_rag_classified.csv'
    result_df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(result_df['Classification'].value_counts())
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
