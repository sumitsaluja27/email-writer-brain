"""
RAG Classifier using crawl4ai for website scraping.
Re-processes UNKNOWN companies from previous run.
"""

import pandas as pd
import chromadb
import requests
import json
from datetime import datetime
import time
import asyncio
from crawl4ai import AsyncWebCrawler

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_EMBED_URL = 'http://localhost:11434/api/embeddings'
MODEL = 'llama3.1:8b'
EMBED_MODEL = 'mxbai-embed-large:latest'


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


async def scrape_website_crawl4ai(url, max_chars=3000):
    """Scrape website using crawl4ai."""
    if not url or pd.isna(url) or url == 'nan':
        return ""
    
    url = str(url).strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, bypass_cache=True)
            if result.success and result.markdown:
                return result.markdown[:max_chars]
    except Exception as e:
        pass
    
    return ""


def classify_with_industry_fallback(name, industry, cust_collection, rap_collection):
    """Classify using industry alone if website fails."""
    
    query = f"{name} {industry}"
    
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
    
    avg_cust_dist = sum(d for d in cust_results['distances'][0]) / max(len(cust_results['distances'][0]), 1)
    
    prompt = f"""Classify if this company is RELEVANT for an ODM manufacturer (Rapidise) that makes cameras and IoT devices.

COMPANY: {name}
Industry: {industry}

SIMILAR CUSTOMERS: {', '.join(similar)}
Distance: {avg_cust_dist:.0f}

RAPIDISE PRODUCTS: {', '.join(products)}

RULES:
- RELEVANT if industry suggests cameras, dashcams, bodycams, security, telematics, fleet
- NOT_RELEVANT if software-only, consulting, unrelated (food, healthcare, real estate)

JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "confidence": 0.0-1.0, "reasoning": "brief reason"}}"""

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
                'reasoning': parsed.get('reasoning', 'Industry-based')[:100],
                'similar_customers': ', '.join(similar),
                'rapidise_products': ', '.join(products)
            }
    except:
        pass
    
    return {
        'classification': 'NOT_RELEVANT',
        'confidence': 0.3,
        'reasoning': 'Classification failed',
        'similar_customers': ', '.join(similar),
        'rapidise_products': ', '.join(products)
    }


async def classify_company(name, website, industry, cust_collection, rap_collection):
    """Classify a company using crawl4ai for scraping."""
    
    content = await scrape_website_crawl4ai(website)
    
    if len(content) < 100:
        return classify_with_industry_fallback(name, industry, cust_collection, rap_collection)
    
    query = f"{name} {industry} {content[:1000]}"
    
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
    
    prompt = f"""Classify if this company is RELEVANT for an ODM manufacturer (Rapidise) that makes cameras and IoT devices.

COMPANY: {name}
Industry: {industry}
Website: {content[:1500]}

SIMILAR CUSTOMERS: {', '.join(similar)}
Distance: {avg_dist:.0f}

RAPIDISE PRODUCTS: {', '.join(products)}

RULES:
- RELEVANT if they SELL cameras, dashcams, bodycams, security devices, telematics
- RELEVANT if they NEED custom camera/device manufacturing
- NOT_RELEVANT if software-only, consulting, unrelated
- NOT_RELEVANT if just USE cameras (end user)

JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "confidence": 0.0-1.0, "reasoning": "brief reason"}}"""

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
                'rapidise_products': ', '.join(products)
            }
    except:
        pass
    
    return classify_with_industry_fallback(name, industry, cust_collection, rap_collection)


async def main():
    print("=" * 60)
    print("RAG CLASSIFICATION with CRAWL4AI")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load previous results
    prev_df = pd.read_csv('data/Companies/sep_nov_rag_classified.csv')
    unknown_df = prev_df[prev_df['Classification'] == 'UNKNOWN'].copy()
    known_df = prev_df[prev_df['Classification'] != 'UNKNOWN'].copy()
    
    print(f"Previously classified: {len(known_df)}")
    print(f"Need to retry: {len(unknown_df)}")
    
    orig_df = pd.read_csv('data/Companies/sep_nov.csv')
    
    # Load KBs
    client1 = chromadb.PersistentClient(path='data/customer_dna_db')
    cust_col = client1.get_collection(name='customer_dna', embedding_function=OllamaEmbed())
    
    client2 = chromadb.PersistentClient(path='data/rapidise_fit_db')
    rap_col = client2.get_collection(name='rapidise_fit', embedding_function=OllamaEmbed())
    
    results = []
    
    for idx, row in unknown_df.iterrows():
        name = str(row['Company Name']).strip()
        
        orig_row = orig_df[orig_df['Company Name'].str.strip() == name]
        website = str(orig_row['Website'].values[0]) if len(orig_row) > 0 else ''
        industry = str(row.get('Industry', '')).strip()
        
        print(f"[{len(results)+1}/{len(unknown_df)}] {name[:35]}...", end=" ", flush=True)
        
        result = await classify_company(name, website, industry, cust_col, rap_col)
        
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
        
        time.sleep(0.5)
    
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
    asyncio.run(main())
