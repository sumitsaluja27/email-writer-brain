"""
Create structured company profiles from scraped website content.
Uses LLM to extract specific sections following buyer journey logic.

Output format: One txt file per company with structured sections:
[HOMEPAGE], [PRODUCT], [USE CASE], [TRUST SIGNALS], [ABOUT US]
"""

import pandas as pd
import requests
import json
import os
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1:8b'

# Companies that are ODM Customers (we sell TO them)
ODM_KEYWORDS = [
    'good customer', 'odm customer', 'potential customer', 
    'sells cameras', 'sells dashcams', 'sells body cams',
    'need manufacturing', 'need odm', 'white-label',
    'video telematics', 'brand'
]

# Companies that are End Users (they BUY cameras, not from ODM)
END_USER_KEYWORDS = [
    'end user', 'uses cameras', 'uses beacons', 
    'buys body cameras', 'police department',
    'warehouse', 'cold storage'
]


def classify_company_type(assessment):
    """Determine if company is ODM customer or end user based on assessment."""
    assessment_lower = str(assessment).lower()
    
    for kw in END_USER_KEYWORDS:
        if kw in assessment_lower:
            return 'end_user'
    
    for kw in ODM_KEYWORDS:
        if kw in assessment_lower:
            return 'odm_customer'
    
    # Default: If unclear, consider potential customer
    return 'odm_customer'


def extract_structured_profile(company_name, industry, assessment, raw_content, product_category):
    """Use LLM to extract structured sections from raw website content."""
    
    prompt = f"""Extract structured information from this company's website content.

COMPANY: {company_name}
INDUSTRY: {industry}
PRODUCT CATEGORY: {product_category}
YOUR NOTES: {assessment}

RAW WEBSITE CONTENT:
{raw_content[:4000]}

Extract the following sections. If information is not available, write "Not found".

[HOMEPAGE]
Hero Headline: (main headline/tagline)
Sub-headline: (supporting statement)
Value Paragraph: (what value they offer)
Who It's For: (target customers/industries)

[PRODUCT / SOLUTION]
Problem Framed As: (what problem do they solve)
What It Does: (core functionality)
Key Outcomes: (benefits, results)
Who Uses It: (user types)

[USE CASE / INDUSTRY]
Industries Served: (list industries)
Problem Description: (problems they address)
Solution Angle: (how they position solution)

[TRUST SIGNALS]
Certifications: (any certifications mentioned)
Deployment Mentions: (scale, number of users, customers)
Reliability Language: (trust/quality claims)

[ABOUT US]
Self Description: (how they describe themselves)
What They Emphasise: (engineering, innovation, service, etc.)
How They Differentiate: (unique selling points)

Return ONLY the structured sections above, nothing else.
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=180)
        
        if response.status_code == 200:
            return response.json()['response']
    except Exception as e:
        print(f"  LLM error: {e}")
    
    return None


def main():
    print("=" * 60)
    print("CREATING STRUCTURED COMPANY PROFILES")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load scraped data
    df = pd.read_csv('data/RAG/sample_companies_scraped.csv')
    print(f"Total companies: {len(df)}")
    
    # Create output directories
    os.makedirs('data/company_profiles/odm_customers', exist_ok=True)
    os.makedirs('data/company_profiles/end_users', exist_ok=True)
    
    odm_count = 0
    end_user_count = 0
    
    for idx, row in df.iterrows():
        company = str(row['company_name']).strip()
        industry = str(row.get('industry', ''))
        assessment = str(row.get('assessment', ''))
        content = str(row.get('website_content', ''))
        product = str(row.get('product_category', ''))
        
        # Skip if no content
        if len(content) < 100:
            print(f"[{idx+1}/{len(df)}] {company[:30]} - SKIPPED (no content)")
            continue
        
        # Classify company type
        company_type = classify_company_type(assessment)
        
        print(f"[{idx+1}/{len(df)}] {company[:30]} ({company_type})...", end=" ", flush=True)
        
        # Extract structured profile using LLM
        profile = extract_structured_profile(company, industry, assessment, content, product)
        
        if profile:
            # Create safe filename
            safe_name = company.lower().replace(' ', '_').replace('/', '_').replace(',', '')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')[:50]
            
            # Determine output path
            if company_type == 'end_user':
                output_path = f"data/company_profiles/end_users/{safe_name}.txt"
                end_user_count += 1
            else:
                output_path = f"data/company_profiles/odm_customers/{safe_name}.txt"
                odm_count += 1
            
            # Add header info
            full_profile = f"""COMPANY: {company}
INDUSTRY: {industry}
PRODUCT CATEGORY: {product}
CUSTOMER TYPE: {company_type.upper().replace('_', ' ')}
ASSESSMENT: {assessment}

{'='*60}

{profile}
"""
            
            # Save to file
            with open(output_path, 'w') as f:
                f.write(full_profile)
            
            print("✓ saved")
        else:
            print("✗ failed")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"ODM Customers: {odm_count} profiles")
    print(f"End Users: {end_user_count} profiles")
    print(f"\nSaved to:")
    print(f"  - data/company_profiles/odm_customers/")
    print(f"  - data/company_profiles/end_users/")


if __name__ == "__main__":
    main()
