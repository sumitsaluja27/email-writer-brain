#!/usr/bin/env python3
"""
Deep scrape and re-classify electrical/electronic companies.
Scrapes multiple pages (homepage, about, products) for better classification.
"""

import pandas as pd
import requests
import json
import time
import re
from urllib.parse import urljoin

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
JINA_API = "https://r.jina.ai/"

def scrape_page(url, timeout=30):
    """Scrape a single page using Jina Reader"""
    try:
        resp = requests.get(f"{JINA_API}{url}", timeout=timeout, headers={
            'Accept': 'text/plain'
        })
        if resp.status_code == 200:
            return resp.text[:5000]  # First 5000 chars
    except Exception as e:
        print(f"    Error scraping {url}: {e}")
    return ""

def deep_scrape_website(base_url):
    """Scrape multiple pages from a website"""
    content_parts = []
    
    # Clean URL
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    base_url = base_url.rstrip('/')
    
    # Pages to try
    pages_to_scrape = [
        ('homepage', base_url),
        ('about', f"{base_url}/about"),
        ('about-us', f"{base_url}/about-us"),
        ('products', f"{base_url}/products"),
        ('solutions', f"{base_url}/solutions"),
        ('services', f"{base_url}/services"),
    ]
    
    for page_name, url in pages_to_scrape:
        content = scrape_page(url)
        if content and len(content) > 200:
            content_parts.append(f"=== {page_name.upper()} ===\n{content}")
            time.sleep(0.5)  # Rate limit
    
    return "\n\n".join(content_parts)

def classify_company(name, website, industry, content):
    """Classify company based on scraped content"""
    
    prompt = f"""Analyze this company's website content and determine if they are relevant for Rapidise.

RAPIDISE PRODUCTS (ODM manufacturer):
1. Cameras: IP cameras, CCTV, dashcams, body cameras
2. IoT devices: beacons, trackers, sensors
3. Automotive: ADAS, DMS, infotainment, instrument clusters
4. Access control: video intercom, smart locks

COMPANY: {name}
Industry: {industry}
Website: {website}

WEBSITE CONTENT:
{content[:8000]}

CLASSIFICATION RULES:
- RELEVANT if they MAKE or SELL: cameras, video devices, dashcams, body cams, security cameras, IoT devices, automotive electronics, ADAS, infotainment, telematics
- RELEVANT if they are potential BUYERS: automotive OEMs, fleet companies, security companies
- NOT_RELEVANT if they ONLY make: audio speakers, headphones, music equipment, phone cases, chargers, mounts, cables, lighting, furniture

Based on the actual website content, what does this company sell/make?

Respond JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "products_found": "list what they actually sell", "reasoning": "brief explanation"}}
"""
    
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=60)
        
        if resp.status_code == 200:
            result = json.loads(resp.json().get("response", "{}"))
            return result
    except Exception as e:
        print(f"    LLM Error: {e}")
    
    return {"classification": "UNKNOWN", "products_found": "Error", "reasoning": "API error"}

def main():
    # Load data
    df = pd.read_csv('data/Companies/sep_nov_rag_classified_v3.csv')
    
    # Get electrical/electronic NOT_RELEVANT companies
    mask = (df['Classification'] == 'NOT_RELEVANT') & \
           (df['Industry'].str.lower().str.contains('electrical', na=False))
    
    electrical = df[mask].copy()
    print(f"Found {len(electrical)} electrical/electronic companies to deep-scrape")
    print("=" * 60)
    
    results = []
    
    for idx, (_, row) in enumerate(electrical.iterrows()):
        name = row['Company Name']
        website = row['Website']
        industry = row['Industry']
        
        print(f"[{idx+1}/{len(electrical)}] {name}")
        print(f"    Scraping: {website}")
        
        # Deep scrape
        content = deep_scrape_website(website)
        print(f"    Scraped {len(content)} chars")
        
        if len(content) < 300:
            print(f"    SKIP - insufficient content")
            results.append({
                'Company Name': name,
                'Website': website,
                'Industry': industry,
                'New_Classification': 'UNKNOWN',
                'Products_Found': 'Scraping failed',
                'Reasoning': 'Could not scrape website'
            })
            continue
        
        # Classify
        result = classify_company(name, website, industry, content)
        
        new_class = result.get('classification', 'UNKNOWN')
        products = result.get('products_found', '')
        reasoning = result.get('reasoning', '')
        
        if new_class == 'RELEVANT':
            print(f"    → CHANGED to RELEVANT: {products[:50]}")
        else:
            print(f"    → stays NOT_RELEVANT: {products[:50]}")
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'New_Classification': new_class,
            'Products_Found': products,
            'Reasoning': reasoning
        })
        
        time.sleep(1)  # Rate limit
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('data/Companies/electrical_deep_scrape_results.csv', index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(results_df['New_Classification'].value_counts())
    print(f"\nSaved to: data/Companies/electrical_deep_scrape_results.csv")
    
    # Show which companies changed
    changed = results_df[results_df['New_Classification'] == 'RELEVANT']
    if len(changed) > 0:
        print(f"\n{len(changed)} companies should be RELEVANT:")
        for _, row in changed.iterrows():
            print(f"  - {row['Company Name']}: {row['Products_Found'][:60]}")

if __name__ == "__main__":
    main()
