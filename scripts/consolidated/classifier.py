"""
Rapidise Company Classification Pipeline - Classifier
======================================================

Consolidated company classification functionality.
Combines: rag_classifier.py, classify_companies.py, crag_classify.py,
          classify_sep_nov.py, complete_list_classify.py, and other classify scripts

Core classification logic using:
1. RAG similarity matching
2. LLM-based reasoning
3. Product-specific rules
"""

import requests
import json
from datetime import datetime

try:
    from .config import (
        OLLAMA_URL, LLM_MODEL, LLM_TIMEOUT,
        PRODUCTS, SERVICES, CLASSIFICATION
    )
    from .scraper import smart_scrape
    from .rag_builder import query_customer_dna, query_rapidise_fit
except ImportError:
    OLLAMA_URL = 'http://localhost:11434/api/generate'
    LLM_MODEL = 'llama3.1:8b'
    LLM_TIMEOUT = 120


# =============================================================================
# LLM CLASSIFICATION
# =============================================================================

def call_llm(prompt, temperature=0.1, format_json=True):
    """Call Ollama LLM with prompt."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': LLM_MODEL,
                'prompt': prompt,
                'stream': False,
                'format': 'json' if format_json else None,
                'options': {'temperature': temperature}
            },
            timeout=LLM_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()['response']
            if format_json:
                return json.loads(result)
            return result
    except Exception as e:
        print(f"LLM error: {e}")
    
    return None


# =============================================================================
# RAG-BASED CLASSIFICATION
# =============================================================================

def classify_with_rag(name, website, industry, content=None, verbose=True):
    """
    Classify a company using RAG + LLM.
    
    Returns:
        dict with: classification, confidence, reasoning, products, similar_customers
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"CLASSIFYING: {name}")
        print(f"{'='*60}")
    
    # Get website content if not provided
    if not content:
        if verbose:
            print("Step 1: Scraping website...")
        try:
            content, method = smart_scrape(website)
            if verbose:
                print(f"  Got {len(content)} chars via {method}")
        except:
            content = ""
    
    if len(content) < 100:
        return {
            'classification': 'UNKNOWN',
            'confidence': 0.3,
            'reasoning': 'Could not access website content',
            'products': [],
            'similar_customers': []
        }
    
    # Query RAG databases
    if verbose:
        print("Step 2: Querying RAG databases...")
    
    query = f"{name} {industry} {content[:2000]}"
    
    try:
        customer_results = query_customer_dna(query)
        product_results = query_rapidise_fit(query)
    except:
        customer_results = {'metadatas': [[]], 'distances': [[]]}
        product_results = {'metadatas': [[]], 'distances': [[]]}
    
    # Extract similar customers
    similar_customers = []
    if customer_results['metadatas'] and customer_results['metadatas'][0]:
        for meta, dist in zip(customer_results['metadatas'][0], customer_results['distances'][0]):
            similar_customers.append({
                'company': meta.get('company_name', 'Unknown'),
                'product_category': meta.get('product_category', ''),
                'distance': round(dist, 3)
            })
    
    # Extract matching products
    matching_products = []
    if product_results['metadatas'] and product_results['metadatas'][0]:
        for meta, dist in zip(product_results['metadatas'][0], product_results['distances'][0]):
            if dist < 1.0:  # Only include close matches
                matching_products.append({
                    'product': meta.get('product_name', ''),
                    'distance': round(dist, 3)
                })
    
    if verbose:
        print(f"  Found {len(similar_customers)} similar customers")
        print(f"  Found {len(matching_products)} matching products")
    
    # LLM Classification
    if verbose:
        print("Step 3: LLM Classification...")
    
    avg_distance = sum(c['distance'] for c in similar_customers) / max(len(similar_customers), 1)
    
    similar_info = "\n".join([
        f"- {c['company']} ({c['product_category']}, distance: {c['distance']})"
        for c in similar_customers[:5]
    ])
    
    product_info = "\n".join([
        f"- {p['product']} (distance: {p['distance']})"
        for p in matching_products[:3]
    ])
    
    prompt = f"""You are classifying if a company is RELEVANT for Rapidise, an ODM manufacturer.

RAPIDISE SERVICES:
- ODM: Design + manufacture complete products
- PES: Product engineering services
- EMS: Electronics manufacturing services

RAPIDISE PRODUCTS:
- Dashcams, In-cabin/DMS, Body cameras, IP cameras, Access control, Beacons

COMPANY TO CLASSIFY:
Name: {name}
Industry: {industry}

WEBSITE CONTENT:
{content[:3000]}

SIMILAR EXISTING CUSTOMERS:
{similar_info}

MATCHING PRODUCTS:
{product_info}

CLASSIFICATION RULES:
1. RELEVANT if they MAKE or NEED products similar to Rapidise offerings
2. RELEVANT if they could use ODM/PES/EMS services
3. NOT_RELEVANT if pure software with no hardware need
4. NOT_RELEVANT if end-user only (hospitals, schools, etc.)

Respond in JSON:
{{
  "classification": "RELEVANT" or "NOT_RELEVANT",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation",
  "best_service": "ODM" or "PES" or "EMS" or "none",
  "best_products": ["dashcam", "bodycam", etc.]
}}"""

    result = call_llm(prompt)
    
    if result:
        return {
            'classification': result.get('classification', 'UNKNOWN'),
            'confidence': result.get('confidence', 0.5),
            'reasoning': result.get('reasoning', ''),
            'best_service': result.get('best_service', ''),
            'products': result.get('best_products', matching_products),
            'similar_customers': similar_customers,
            'avg_distance': avg_distance
        }
    
    return {
        'classification': 'UNKNOWN',
        'confidence': 0.3,
        'reasoning': 'Classification failed',
        'products': [],
        'similar_customers': similar_customers
    }


# =============================================================================
# KEYWORD-BASED CLASSIFICATION (Fast, no LLM)
# =============================================================================

def classify_by_keywords(name, industry, content=""):
    """
    Fast keyword-based classification.
    Good for initial filtering before LLM.
    """
    text = f"{name} {industry} {content}".lower()
    
    # Check for each product
    matched_products = []
    
    product_keywords = {
        'dashcam': ['dashcam', 'dash cam', 'fleet camera', 'vehicle recorder', 'dvr', 'telematics'],
        'bodycam': ['body camera', 'bodycam', 'body-worn', 'bwv', 'police camera'],
        'ip_camera': ['ip camera', 'security camera', 'cctv', 'surveillance', 'nvr'],
        'in_cabin': ['driver monitoring', 'dms', 'in-cabin', 'fatigue detection', 'adas'],
        'access_control': ['access control', 'door controller', 'biometric', 'card reader'],
        'beacon': ['beacon', 'ble', 'asset tracker', 'cold chain', 'temperature monitor']
    }
    
    for product, keywords in product_keywords.items():
        for keyword in keywords:
            if keyword in text:
                matched_products.append(product)
                break
    
    # Check for relevant company types
    relevant_signals = [
        'manufacturer', 'oem', 'odm', 'supplier', 'hardware', 'electronics',
        'fleet', 'security', 'automotive', 'telematics', 'camera'
    ]
    
    not_relevant_signals = [
        'hospital', 'school', 'university', 'restaurant', 'hotel', 
        'bank', 'insurance', 'law firm', 'accounting'
    ]
    
    relevant_score = sum(1 for s in relevant_signals if s in text)
    not_relevant_score = sum(1 for s in not_relevant_signals if s in text)
    
    if matched_products and relevant_score > not_relevant_score:
        return {
            'classification': 'LIKELY_RELEVANT',
            'products': matched_products,
            'confidence': min(0.3 + (relevant_score * 0.1), 0.7)
        }
    elif not_relevant_score > relevant_score:
        return {
            'classification': 'LIKELY_NOT_RELEVANT',
            'products': [],
            'confidence': min(0.3 + (not_relevant_score * 0.1), 0.7)
        }
    
    return {
        'classification': 'UNKNOWN',
        'products': matched_products,
        'confidence': 0.3
    }


# =============================================================================
# BATCH CLASSIFICATION
# =============================================================================

def classify_companies_batch(companies, use_rag=True, verbose=False):
    """
    Classify multiple companies.
    
    Args:
        companies: List of dicts with 'name', 'website', 'industry'
        use_rag: Whether to use RAG+LLM (slower but more accurate)
    """
    results = []
    
    for i, company in enumerate(companies):
        name = company.get('name', company.get('Company Name', f'Company_{i}'))
        website = company.get('website', company.get('Website', ''))
        industry = company.get('industry', company.get('Industry', ''))
        
        print(f"\n[{i+1}/{len(companies)}] {name}")
        
        if use_rag:
            result = classify_with_rag(name, website, industry, verbose=verbose)
        else:
            # Quick keyword classification first
            result = classify_by_keywords(name, industry)
            
            # Use RAG only for uncertain cases
            if result['classification'] == 'UNKNOWN':
                result = classify_with_rag(name, website, industry, verbose=verbose)
        
        result['company_name'] = name
        result['website'] = website
        result['industry'] = industry
        results.append(result)
        
        print(f"  → {result['classification']} ({result['confidence']:.2f})")
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify companies")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--website", help="Company website")
    parser.add_argument("--industry", help="Company industry", default="")
    parser.add_argument("--keywords-only", action="store_true", help="Use keyword classification only")
    
    args = parser.parse_args()
    
    if args.company:
        if args.keywords_only:
            result = classify_by_keywords(args.company, args.industry)
        else:
            result = classify_with_rag(args.company, args.website or "", args.industry)
        
        print(f"\nResult: {json.dumps(result, indent=2)}")
    else:
        # Test with sample
        print("Testing classifier...")
        result = classify_by_keywords("Samsara", "Fleet Telematics", "dashcam fleet camera vehicle")
        print(f"Keyword result: {result}")
