#!/usr/bin/env python3
"""
Deep scrape and re-classify ALL remaining NOT_RELEVANT companies.
Uses direct HTTP scraping (no Jina API) for reliability.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

def direct_scrape(url, timeout=20):
    """Scrape directly without external API"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        if not url.startswith('http'):
            url = 'https://' + url
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return text[:8000]
    except Exception as e:
        pass
    return ""

def classify_company(name, website, industry, content):
    """Classify based on actual website content"""
    prompt = f"""Based on this company's website content, what products/services do they offer?

COMPANY: {name}
INDUSTRY: {industry}
WEBSITE: {website}
CONTENT: {content[:6000]}

RAPIDISE PRODUCTS (ODM manufacturer can supply):
1. Cameras: IP cameras, CCTV, dashcams, body cameras, surveillance
2. IoT devices: beacons, trackers, GPS, sensors, asset tracking
3. Automotive: ADAS, DMS, infotainment, instrument clusters, connected car
4. Telematics: fleet tracking, vehicle monitoring, dashcam systems
5. Access control: video intercom, smart locks, biometrics, door automation
6. Security hardware: body worn cameras, security cameras

CLASSIFY AS RELEVANT IF:
- They MAKE or SELL any of the above products
- They are potential BUYERS (automotive OEMs, fleet companies, security guards, logistics with fleets)
- They have warehouses/fleets needing cameras, beacons, or telematics

CLASSIFY AS NOT_RELEVANT IF:
- Pure software with no hardware needs
- Audio/speakers/headphones only
- Lighting/LEDs only
- EV charging infrastructure only
- Generic components (springs, fasteners, tires)
- Consulting/research only

What products does this company sell? Is it RELEVANT or NOT_RELEVANT for Rapidise?

JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "products": "brief list of what they sell/do"}}
"""
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False, "format": "json"
        }, timeout=60)
        if resp.status_code == 200:
            return json.loads(resp.json().get("response", "{}"))
    except:
        pass
    return {"classification": "UNKNOWN", "products": "Error"}

def main():
    # Load current classification
    df = pd.read_csv('data/Companies/sep_nov_rag_classified_v3.csv')
    
    # Get ALL NOT_RELEVANT companies (excluding electrical already done)
    not_relevant = df[df['Classification'] == 'NOT_RELEVANT'].copy()
    
    # Exclude electrical (already processed)
    not_relevant = not_relevant[~not_relevant['Industry'].str.lower().str.contains('electrical', na=False)]
    
    print(f"Total NOT_RELEVANT to process: {len(not_relevant)}")
    print("\nBy industry:")
    print(not_relevant['Industry'].value_counts().head(15))
    print("=" * 60)
    
    results = []
    changed_count = 0
    
    for idx, (_, row) in enumerate(not_relevant.iterrows()):
        name = row['Company Name']
        website = row['Website']
        industry = row['Industry']
        
        print(f"[{idx+1}/{len(not_relevant)}] {name[:40]}")
        
        # Direct scrape
        content = direct_scrape(website)
        if len(content) < 200:
            print(f"    SKIP - no content")
            results.append({
                'Company Name': name,
                'Website': website,
                'Industry': industry,
                'New_Classification': 'UNKNOWN',
                'Products_Found': 'Scraping failed'
            })
            continue
        
        # Classify
        result = classify_company(name, website, industry, content)
        new_class = result.get('classification', 'UNKNOWN')
        products = result.get('products', '')
        
        if new_class == 'RELEVANT':
            changed_count += 1
            print(f"    → RELEVANT: {products[:50]}")
        else:
            print(f"    → NOT_RELEVANT: {products[:40]}")
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'New_Classification': new_class,
            'Products_Found': products
        })
        
        time.sleep(0.5)
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('data/Companies/all_industries_deep_scrape.csv', index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Changed to RELEVANT: {changed_count}")
    print(f"\nBy classification:")
    print(results_df['New_Classification'].value_counts())
    print(f"\nSaved to: data/Companies/all_industries_deep_scrape.csv")
    
    # Show RELEVANT finds
    relevant = results_df[results_df['New_Classification'] == 'RELEVANT']
    if len(relevant) > 0:
        print(f"\n{len(relevant)} companies should be RELEVANT:")
        for _, row in relevant.iterrows():
            print(f"  - {row['Company Name']}: {row['Products_Found'][:50]}")

if __name__ == "__main__":
    main()
