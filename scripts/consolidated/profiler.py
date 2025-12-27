"""
Rapidise Company Classification Pipeline - Profiler
====================================================

Consolidated company profiling functionality.
Combines: create_profiles.py, extract_company_analysis.py

Handles:
- Creating structured company profiles
- Extracting key information with LLM
- Saving profiles to JSON format
"""

import json
import os
import pandas as pd
from datetime import datetime

try:
    from .config import OLLAMA_URL, LLM_MODEL, LLM_TIMEOUT, PROFILES_DIR, PRODUCTS
    from .scraper import scrape_company_deep
except ImportError:
    OLLAMA_URL = 'http://localhost:11434/api/generate'
    LLM_MODEL = 'llama3.1:8b'
    LLM_TIMEOUT = 120
    PROFILES_DIR = 'data/company_profiles_v2'

import requests


# =============================================================================
# LLM PROFILE EXTRACTION
# =============================================================================

def extract_profile_with_llm(company_name, content, customer_type="unknown"):
    """
    Use LLM to extract structured profile from scraped content.
    """
    prompt = f"""Analyze this company and extract a structured profile.

COMPANY: {company_name}
CUSTOMER TYPE: {customer_type}

WEBSITE CONTENT:
{content[:6000]}

Extract the following information in JSON format:
{{
    "what_they_do": "Brief 1-2 sentence description of the company",
    "business_model": "ODM, OEM, Software, Integrator, End User, etc.",
    "products_they_make": ["list of products they manufacture"],
    "products_they_sell": ["list of products they sell/offer"],
    "services_they_offer": ["list of services"],
    "who_they_sell_to": ["target customer types"],
    "industries_served": ["list of industries"],
    "technology_focus": ["key technologies mentioned"],
    "partnerships": ["key partners or integrations"],
    "key_differentiators": ["what makes them unique"]
}}

Be concise and factual. Only include information found in the content."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': LLM_MODEL,
                'prompt': prompt,
                'stream': False,
                'format': 'json',
                'options': {'temperature': 0.1}
            },
            timeout=LLM_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()['response']
            return json.loads(result)
    except Exception as e:
        print(f"  LLM error: {e}")
    
    return {
        "what_they_do": "",
        "business_model": "unknown",
        "products_they_make": [],
        "products_they_sell": [],
        "services_they_offer": [],
        "who_they_sell_to": [],
        "industries_served": [],
        "technology_focus": [],
        "partnerships": [],
        "key_differentiators": []
    }


# =============================================================================
# PROFILE CREATION
# =============================================================================

def create_company_profile(name, website, customer_type="odm_customer", 
                          product_category="", existing_assessment="",
                          output_dir=None):
    """
    Create a complete company profile with scraping and LLM extraction.
    """
    output_dir = output_dir or str(PROFILES_DIR)
    
    print(f"\n{'='*60}")
    print(f"CREATING PROFILE: {name}")
    print(f"{'='*60}")
    
    # Step 1: Deep scrape
    print("Step 1: Deep scraping website...")
    scrape_result = scrape_company_deep(name, website)
    
    if scrape_result['total_chars'] < 100:
        print("  ✗ Insufficient content scraped")
        return None
    
    # Combine all content
    all_content = "\n\n".join([
        f"=== {page.upper()} ===\n{content}"
        for page, content in scrape_result['pages'].items()
    ])
    
    # Step 2: LLM extraction
    print("Step 2: Extracting structured profile...")
    profile = extract_profile_with_llm(name, all_content, customer_type)
    
    # Add metadata
    profile['_metadata'] = {
        'company_name': name,
        'website': website,
        'customer_type': customer_type,
        'product_category': product_category,
        'existing_assessment': existing_assessment,
        'scraped_at': datetime.now().isoformat(),
        'pages_scraped': list(scrape_result['pages'].keys()),
        'total_content_chars': scrape_result['total_chars']
    }
    
    # Step 3: Save profile
    print("Step 3: Saving profile...")
    company_dir = os.path.join(output_dir, customer_type, 
                               name.lower().replace(' ', '_').replace(',', ''))
    os.makedirs(company_dir, exist_ok=True)
    os.makedirs(os.path.join(company_dir, 'raw'), exist_ok=True)
    
    # Save profile.json
    profile_path = os.path.join(company_dir, 'profile.json')
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2)
    
    # Save raw content
    for page, content in scrape_result['pages'].items():
        raw_path = os.path.join(company_dir, 'raw', f'{page}.txt')
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Save summary
    summary_path = os.path.join(company_dir, 'summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"Company: {name}\n")
        f.write(f"Website: {website}\n")
        f.write(f"Type: {customer_type}\n")
        f.write(f"Category: {product_category}\n\n")
        f.write(f"What they do:\n{profile.get('what_they_do', '')}\n\n")
        f.write(f"Business model: {profile.get('business_model', '')}\n\n")
        f.write(f"Products: {', '.join(profile.get('products_they_make', []))}\n")
        f.write(f"Target: {', '.join(profile.get('who_they_sell_to', []))}\n")
    
    print(f"  ✓ Profile saved to {company_dir}")
    
    return profile


# =============================================================================
# BATCH PROFILING
# =============================================================================

def create_profiles_from_csv(csv_path, output_dir=None):
    """
    Create profiles for all companies in a CSV file.
    
    Expected columns:
    - Company Name / name
    - Website / website
    - Customer Type (optional)
    - Product Category (optional)
    - My Assessment (optional)
    """
    output_dir = output_dir or str(PROFILES_DIR)
    
    print("=" * 60)
    print("BATCH PROFILE CREATION")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded: {len(df)} companies from {csv_path}")
    
    results = []
    
    for idx, row in df.iterrows():
        # Get company info
        name = row.get('Company Name', row.get('name', f'Company_{idx}'))
        website = row.get('Website', row.get('website', ''))
        customer_type = row.get('Customer Type', 'odm_customer')
        product_category = row.get('Product Category', row.get('Product relevance', ''))
        assessment = row.get('My Assessment', '')
        
        # Normalize customer type
        if customer_type in ['End User', 'end_user', 'END_USER']:
            customer_type = 'end_user'
        else:
            customer_type = 'odm_customer'
        
        # Create profile
        profile = create_company_profile(
            name=name,
            website=website,
            customer_type=customer_type,
            product_category=product_category,
            existing_assessment=assessment,
            output_dir=output_dir
        )
        
        results.append({
            'company': name,
            'success': profile is not None,
            'pages': profile['_metadata']['pages_scraped'] if profile else [],
            'chars': profile['_metadata']['total_content_chars'] if profile else 0
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("PROFILE CREATION COMPLETE")
    print("=" * 60)
    
    success = sum(1 for r in results if r['success'])
    total_chars = sum(r['chars'] for r in results)
    
    print(f"Successful: {success}/{len(results)}")
    print(f"Total content: {total_chars:,} chars")
    print(f"Output: {output_dir}")
    
    return results


# =============================================================================
# PROFILE LOADING
# =============================================================================

def load_profile(company_name, customer_type="odm_customer", profiles_dir=None):
    """Load a company profile from disk."""
    profiles_dir = profiles_dir or str(PROFILES_DIR)
    
    folder_name = company_name.lower().replace(' ', '_').replace(',', '')
    profile_path = os.path.join(profiles_dir, customer_type, folder_name, 'profile.json')
    
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            return json.load(f)
    
    return None


def list_profiles(profiles_dir=None):
    """List all available profiles."""
    profiles_dir = profiles_dir or str(PROFILES_DIR)
    
    profiles = []
    
    for customer_type in ['odm_customer', 'end_user']:
        type_dir = os.path.join(profiles_dir, customer_type)
        if os.path.exists(type_dir):
            for company_folder in os.listdir(type_dir):
                company_dir = os.path.join(type_dir, company_folder)
                if os.path.isdir(company_dir):
                    profile_path = os.path.join(company_dir, 'profile.json')
                    if os.path.exists(profile_path):
                        profiles.append({
                            'folder': company_folder,
                            'type': customer_type,
                            'path': profile_path
                        })
    
    return profiles


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create company profiles")
    parser.add_argument("--company", help="Single company name")
    parser.add_argument("--website", help="Company website")
    parser.add_argument("--csv", help="CSV file with companies")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--list", action="store_true", help="List existing profiles")
    
    args = parser.parse_args()
    
    if args.list:
        profiles = list_profiles(args.output)
        print(f"Found {len(profiles)} profiles:")
        for p in profiles:
            print(f"  - {p['folder']} ({p['type']})")
    
    elif args.company and args.website:
        create_company_profile(args.company, args.website, output_dir=args.output)
    
    elif args.csv:
        create_profiles_from_csv(args.csv, args.output)
    
    else:
        parser.print_help()
