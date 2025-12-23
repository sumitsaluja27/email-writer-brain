"""
Improved Company Classification Pipeline
- Scrapes website for actual content
- LLM extracts structured company info
- RAG matches against Rapidise product profiles
- Final classification with confidence

Test on last 200 companies from complete_list.csv
"""

import pandas as pd
import requests
import json
import os
from datetime import datetime

# Config
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_EMBED_URL = 'http://localhost:11434/api/embeddings'
MODEL = 'deepseek-llm:7b'
EMBED_MODEL = 'mxbai-embed-large:latest'
JINA_API = 'https://r.jina.ai/'

# Read customer profiles for RAG
CUSTOMER_PROFILES = {}
PROFILE_DIR = 'docs/product_definitions'

def load_customer_profiles():
    """Load all customer profile documents for RAG."""
    profiles = {}
    for filename in os.listdir(PROFILE_DIR):
        if filename.endswith('_customer_profile.md'):
            category = filename.replace('_customer_profile.md', '')
            with open(os.path.join(PROFILE_DIR, filename), 'r') as f:
                profiles[category] = f.read()
    return profiles

def get_embedding(text):
    """Get embedding from Ollama."""
    try:
        response = requests.post(OLLAMA_EMBED_URL, json={
            'model': EMBED_MODEL,
            'prompt': text[:2000]  # Limit text length
        }, timeout=60)
        if response.status_code == 200:
            return response.json().get('embedding', [])
    except:
        pass
    return []

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def scrape_website(url):
    """Scrape website using Jina Reader API."""
    if not url or url == 'nan':
        return ""
    
    try:
        # Clean URL
        if not url.startswith('http'):
            url = 'https://' + url
        
        jina_url = JINA_API + url
        response = requests.get(jina_url, timeout=30, headers={
            'Accept': 'text/plain'
        })
        
        if response.status_code == 200:
            text = response.text[:5000]  # Limit to 5000 chars
            return text
    except Exception as e:
        pass
    
    return ""

def extract_company_info(company_name, website_content):
    """Use LLM to extract structured company info."""
    
    prompt = f"""Analyze this company's website content and extract key information.

COMPANY: {company_name}

WEBSITE CONTENT:
{website_content[:3000]}

Extract and respond ONLY with this JSON:
{{
  "company_type": "manufacturer|service_provider|software|platform|retailer|other",
  "products_sold": ["list", "of", "products"],
  "is_camera_related": true/false,
  "is_security_related": true/false,
  "is_fleet_transport": true/false,
  "target_customers": "consumers|businesses|government|law_enforcement",
  "one_line_summary": "What this company does in one sentence"
}}

If content is unclear, make best guess. Always respond with valid JSON.
"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=120)
        
        if response.status_code == 200:
            result = response.json()['response']
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
    except:
        pass
    
    return {"company_type": "unknown", "products_sold": [], "one_line_summary": "Unknown"}

def rag_match(company_info, profile_embeddings):
    """Match company info against customer profiles using embeddings."""
    
    # Create company description for matching
    company_text = f"""
    Company type: {company_info.get('company_type', 'unknown')}
    Products: {', '.join(company_info.get('products_sold', []))}
    Summary: {company_info.get('one_line_summary', '')}
    Camera related: {company_info.get('is_camera_related', False)}
    Security related: {company_info.get('is_security_related', False)}
    Fleet/transport: {company_info.get('is_fleet_transport', False)}
    """
    
    company_embedding = get_embedding(company_text)
    
    if not company_embedding:
        return {"best_match": "not_relevant", "scores": {}}
    
    # Compare with each profile
    scores = {}
    for category, profile_emb in profile_embeddings.items():
        sim = cosine_similarity(company_embedding, profile_emb)
        scores[category] = sim
    
    # Get best match
    if scores:
        best = max(scores, key=scores.get)
        return {"best_match": best, "scores": scores}
    
    return {"best_match": "not_relevant", "scores": {}}

def final_classification(company_name, company_info, rag_result):
    """Final LLM classification combining company info and RAG match."""
    
    scores_str = "\n".join([f"  {k}: {v:.3f}" for k,v in sorted(rag_result.get('scores', {}).items(), key=lambda x: -x[1])[:3]])
    
    prompt = f"""You are classifying companies for Rapidise, an ODM manufacturer of cameras and tracking devices.

COMPANY: {company_name}

EXTRACTED INFO:
- Type: {company_info.get('company_type')}
- Products: {company_info.get('products_sold')}
- Camera related: {company_info.get('is_camera_related')}
- Security related: {company_info.get('is_security_related')}
- Fleet/Transport: {company_info.get('is_fleet_transport')}
- Summary: {company_info.get('one_line_summary')}

RAG SIMILARITY SCORES (higher = more similar to customer profile):
{scores_str}

RAG suggested: {rag_result.get('best_match')}

CATEGORIES:
- dashcam: Sells dashcams/fleet cameras (Geotab, Lytx, Nexar)
- ip_camera: Sells security cameras (Verkada, SimpliSafe)
- bodycam: Sells body cameras (Axon, Reveal Media)
- in_cabin: Sells driver monitoring (Smart Eye)
- access_control: Sells access control devices (Acre Security)
- beacon: Uses beacons for cold storage/logistics
- bodycam_enduser: Police/security that BUYS bodycams
- not_relevant: Not a camera/security products company

IMPORTANT: Most random companies are NOT relevant. Only classify as relevant if they clearly sell cameras/security devices.

Respond with JSON:
{{"category": "not_relevant", "confidence": "high", "reason": "Software company, no hardware products"}}
"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=120)
        
        if response.status_code == 200:
            result = response.json()['response']
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
    except:
        pass
    
    return {"category": "error", "confidence": "low", "reason": "Parse error"}

def process_companies(input_file, output_file, num_companies=200):
    """Process companies through the full pipeline."""
    
    print("="*60)
    print("IMPROVED CLASSIFICATION PIPELINE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Load customer profiles
    print("\n[1] Loading customer profiles...")
    profiles = load_customer_profiles()
    print(f"    Loaded {len(profiles)} profiles: {list(profiles.keys())}")
    
    # Create profile embeddings
    print("\n[2] Creating profile embeddings...")
    profile_embeddings = {}
    for category, text in profiles.items():
        emb = get_embedding(text[:2000])
        if emb:
            profile_embeddings[category] = emb
            print(f"    ✓ {category}")
    print(f"    Created {len(profile_embeddings)} embeddings")
    
    # Load companies
    print(f"\n[3] Loading last {num_companies} companies from {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8', on_bad_lines='skip')
    unique = df.drop_duplicates(subset=['Company Name'], keep='last').tail(num_companies)
    print(f"    Selected {len(unique)} companies")
    
    # Process each company
    print(f"\n[4] Processing companies...")
    results = []
    
    for idx, row in unique.iterrows():
        company_name = str(row.get('Company Name', ''))
        website = str(row.get('Website', ''))
        industry = str(row.get('Industry', ''))
        
        if company_name == 'nan' or company_name == '':
            continue
        
        print(f"\n[{len(results)+1}/{len(unique)}] {company_name[:40]}")
        
        # Step 1: Scrape
        print("    Scraping...", end=" ")
        content = scrape_website(website)
        print(f"✓ ({len(content)} chars)" if content else "✗ (no content)")
        
        # Step 2: Extract info
        print("    Extracting...", end=" ")
        if content:
            company_info = extract_company_info(company_name, content)
        else:
            company_info = {"company_type": "unknown", "products_sold": [], 
                          "one_line_summary": f"{industry} company"}
        print(f"✓ ({company_info.get('company_type')})")
        
        # Step 3: RAG match
        print("    RAG matching...", end=" ")
        rag_result = rag_match(company_info, profile_embeddings)
        print(f"✓ ({rag_result.get('best_match')})")
        
        # Step 4: Final classification
        print("    Classifying...", end=" ")
        classification = final_classification(company_name, company_info, rag_result)
        cat = classification.get('category', 'error')
        print(f"→ {cat}")
        
        results.append({
            'Company Name': company_name,
            'Website': website,
            'Industry': industry,
            'Scraped': 'Yes' if content else 'No',
            'Company Type': company_info.get('company_type', ''),
            'Products': ', '.join(company_info.get('products_sold', []))[:100],
            'Summary': company_info.get('one_line_summary', '')[:100],
            'RAG Match': rag_result.get('best_match', ''),
            'Category': cat,
            'Confidence': classification.get('confidence', ''),
            'Reason': classification.get('reason', '')
        })
        
        # Save progress
        if len(results) % 10 == 0:
            pd.DataFrame(results).to_csv(output_file, index=False)
            print(f"    [Saved: {len(results)} companies]")
    
    # Final save
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_file, index=False)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(result_df['Category'].value_counts())
    print(f"\nSaved to: {output_file}")

def main():
    process_companies(
        input_file='data/Companies/complete_list.csv',
        output_file='data/Companies/improved_classification_test.csv',
        num_companies=200
    )

if __name__ == "__main__":
    main()
