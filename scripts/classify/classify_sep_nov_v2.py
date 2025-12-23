"""
RAG Classifier with industry-based classification and location extraction.
Uses requests for scraping with retries, extracts city/state from website.
"""

import pandas as pd
import chromadb
import requests
import json
import re
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
    """Scrape website with retries."""
    if not url or pd.isna(url) or url == 'nan':
        return ""
    
    url = str(url).strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    for attempt in range(2):
        try:
            response = requests.get(
                JINA_API + url, 
                timeout=30 + (attempt * 10),
                headers={'Accept': 'text/plain'}
            )
            if response.status_code == 200:
                content = response.text[:max_chars]
                if len(content) > 100:
                    return content
        except:
            time.sleep(1)
    
    return ""


def extract_location(content, name):
    """Extract city/state from website content using LLM."""
    if len(content) < 50:
        return ""
    
    prompt = f"""Extract the company's headquarters location (city, state/country) from this website content.
If you can find the location, return it in format: "City, State" or "City, Country"
If not found, return "Unknown"

COMPANY: {name}
WEBSITE CONTENT:
{content[:2000]}

Response (location only, nothing else):"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=60)
        
        if response.status_code == 200:
            location = response.json()['response'].strip()
            # Clean up response
            location = location.replace('\n', ' ').strip()
            if len(location) < 50 and 'Unknown' not in location:
                return location
    except:
        pass
    
    return ""


def classify_company(name, website, industry, cust_collection, rap_collection):
    """Classify using KB similarity + LLM."""
    
    # Try to scrape
    content = scrape_website(website)
    
    # Extract location if we have content
    location = extract_location(content, name) if len(content) > 100 else ""
    
    # Query KBs
    query = f"{name} {industry} {content[:1000]}" if content else f"{name} {industry}"
    
    cust_results = cust_collection.query(query_texts=[query], n_results=3, include=['metadatas', 'distances'])
    similar = []
    if cust_results['metadatas'] and cust_results['metadatas'][0]:
        for meta, dist in zip(cust_results['metadatas'][0], cust_results['distances'][0]):
            similar.append(f"{meta.get('company_name', '')} ({dist:.0f})")
    
    rap_results = rap_collection.query(query_texts=[query], n_results=2, include=['metadatas', 'distances'])
    products = []
    if rap_results['metadatas'] and rap_results['metadatas'][0]:
        for meta, dist in zip(rap_results['metadatas'][0], rap_results['distances'][0]):
            products.append(f"{meta.get('product', '')} ({dist:.0f})")
    
    avg_dist = sum(d for d in cust_results['distances'][0]) / max(len(cust_results['distances'][0]), 1)
    
    # LLM Classification
    website_info = f"Website: {content[:1200]}" if content else "(website not accessible)"
    
    prompt = f"""Classify if this company is RELEVANT for Rapidise, an ODM manufacturer that makes cameras and IoT devices.

COMPANY: {name}
Industry: {industry}
{website_info}

SIMILAR CUSTOMERS: {', '.join(similar)}
RAPIDISE PRODUCTS: {', '.join(products)}

RULES:
- RELEVANT = SELL cameras, dashcams, bodycams, security devices, telematics, or NEED custom device manufacturing
- NOT_RELEVANT = software-only, consulting, unrelated industry, or just USE cameras (end user)

JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "confidence": 0.0-1.0, "reasoning": "brief"}}"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL, 'prompt': prompt, 'stream': False, 'format': 'json',
            'options': {'temperature': 0.1}
        }, timeout=90)
        
        if response.status_code == 200:
            parsed = json.loads(response.json()['response'])
            return {
                'classification': parsed.get('classification', 'NOT_RELEVANT'),
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', '')[:100],
                'similar_customers': ', '.join(similar),
                'rapidise_products': ', '.join(products),
                'location': location
            }
    except:
        pass
    
    return {
        'classification': 'NOT_RELEVANT',
        'confidence': 0.3,
        'reasoning': 'LLM error',
        'similar_customers': ', '.join(similar),
        'rapidise_products': ', '.join(products),
        'location': location
    }


def main():
    print("=" * 60)
    print("RAG CLASSIFICATION - SEP_NOV COMPANIES")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load from previous or fresh
    try:
        prev_df = pd.read_csv('data/Companies/sep_nov_rag_classified.csv')
        unknown_df = prev_df[prev_df['Classification'] == 'UNKNOWN'].copy()
        known_df = prev_df[prev_df['Classification'] != 'UNKNOWN'].copy()
        print(f"Previously classified: {len(known_df)}")
        print(f"Need to retry: {len(unknown_df)}")
        use_previous = True
    except:
        unknown_df = pd.read_csv('data/Companies/sep_nov.csv')
        known_df = pd.DataFrame()
        use_previous = False
        print(f"Fresh run: {len(unknown_df)} companies")
    
    orig_df = pd.read_csv('data/Companies/sep_nov.csv')
    
    # Load KBs
    client1 = chromadb.PersistentClient(path='data/customer_dna_db')
    cust_col = client1.get_collection(name='customer_dna', embedding_function=OllamaEmbed())
    
    client2 = chromadb.PersistentClient(path='data/rapidise_fit_db')
    rap_col = client2.get_collection(name='rapidise_fit', embedding_function=OllamaEmbed())
    
    results = []
    
    for idx, row in unknown_df.iterrows():
        name = str(row['Company Name']).strip()
        
        if use_previous:
            orig_row = orig_df[orig_df['Company Name'].str.strip() == name]
            website = str(orig_row['Website'].values[0]) if len(orig_row) > 0 else ''
            industry = str(row.get('Industry', '')).strip()
        else:
            website = str(row.get('Website', '')).strip()
            industry = str(row.get('Industry', '')).strip()
        
        print(f"[{len(results)+1}/{len(unknown_df)}] {name[:35]}...", end=" ", flush=True)
        
        result = classify_company(name, website, industry, cust_col, rap_col)
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'Classification': result['classification'],
            'Confidence': result['confidence'],
            'Reasoning': result['reasoning'],
            'Similar Customers': result['similar_customers'],
            'Rapidise Products': result['rapidise_products'],
            'City_State': result['location']
        })
        
        print(f"{result['classification']} ({result['confidence']:.1f})")
        
        time.sleep(0.3)
    
    # Combine
    retry_df = pd.DataFrame(results)
    final_df = pd.concat([known_df, retry_df], ignore_index=True)
    
    output_path = 'data/Companies/sep_nov_rag_classified_v2.csv'
    final_df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(final_df['Classification'].value_counts())
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
