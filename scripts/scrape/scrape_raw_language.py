"""
Scrape EXACT TEXT from company websites - no LLM summarization.
Extracts raw language from: Homepage, About Us, Products pages.
Preserves exact wording for language analysis.
"""

import pandas as pd
import requests
import os
from datetime import datetime
import time
import re

JINA_API = 'https://r.jina.ai/'

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
    """Determine if company is ODM customer or end user."""
    assessment_lower = str(assessment).lower()
    
    for kw in END_USER_KEYWORDS:
        if kw in assessment_lower:
            return 'end_user'
    
    for kw in ODM_KEYWORDS:
        if kw in assessment_lower:
            return 'odm_customer'
    
    return 'odm_customer'


def scrape_page(url, max_chars=8000):
    """Scrape a single page and return raw text."""
    if not url:
        return ""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        response = requests.get(JINA_API + url, timeout=45, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            return response.text[:max_chars]
    except Exception as e:
        print(f"    Error: {e}")
    return ""


def clean_text(text):
    """Clean text while preserving language."""
    if not text:
        return ""
    # Remove excessive whitespace but keep structure
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove URL artifacts from Jina
    text = re.sub(r'URL Source:.*?\n', '', text)
    text = re.sub(r'Markdown Content:.*?\n', '', text)
    return text.strip()


def scrape_company(website):
    """Scrape all relevant pages from a company website."""
    base_url = website.rstrip('/')
    
    pages = {}
    
    # 1. Homepage
    print("    Homepage...", end="", flush=True)
    homepage = scrape_page(base_url)
    if homepage:
        pages['homepage'] = clean_text(homepage)
        print("✓", end="", flush=True)
    else:
        print("✗", end="", flush=True)
    
    time.sleep(0.5)
    
    # 2. About Us (try multiple paths)
    print(" About...", end="", flush=True)
    about_paths = ['/about', '/about-us', '/about-us/', '/company', '/who-we-are']
    about = ""
    for path in about_paths:
        about = scrape_page(base_url + path)
        if about and len(about) > 500:
            pages['about'] = clean_text(about)
            print("✓", end="", flush=True)
            break
    if not about:
        print("✗", end="", flush=True)
    
    time.sleep(0.5)
    
    # 3. Products/Solutions (try multiple paths)
    print(" Products...", end="", flush=True)
    product_paths = ['/products', '/solutions', '/services', '/our-products', '/platform']
    products = ""
    for path in product_paths:
        products = scrape_page(base_url + path)
        if products and len(products) > 500:
            pages['products'] = clean_text(products)
            print("✓", end="", flush=True)
            break
    if not products:
        print("✗", end="", flush=True)
    
    return pages


def save_profile(company, industry, product_cat, assessment, company_type, pages, output_dir):
    """Save company profile as txt file with exact text."""
    
    # Create safe filename
    safe_name = company.lower().replace(' ', '_').replace('/', '_').replace(',', '')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')[:50]
    
    output_path = os.path.join(output_dir, f"{safe_name}.txt")
    
    content = f"""================================================================================
COMPANY: {company}
================================================================================
INDUSTRY: {industry}
PRODUCT CATEGORY: {product_cat}
CUSTOMER TYPE: {company_type.upper().replace('_', ' ')}
YOUR ASSESSMENT: {assessment}
================================================================================

"""
    
    # Add homepage content (exact text)
    if 'homepage' in pages and pages['homepage']:
        content += """
================================================================================
[HOMEPAGE - EXACT TEXT]
================================================================================

"""
        content += pages['homepage'][:6000]
    
    # Add about us content (exact text)
    if 'about' in pages and pages['about']:
        content += """


================================================================================
[ABOUT US - EXACT TEXT]
================================================================================

"""
        content += pages['about'][:6000]
    
    # Add products content (exact text)
    if 'products' in pages and pages['products']:
        content += """


================================================================================
[PRODUCTS/SOLUTIONS - EXACT TEXT]
================================================================================

"""
        content += pages['products'][:6000]
    
    # Save file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path


def main():
    print("=" * 60)
    print("SCRAPING RAW WEBSITE LANGUAGE")
    print("(Exact text, no LLM summarization)")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load sample companies
    df = pd.read_csv('data/Companies/sample_companies_for_review.csv')
    print(f"Total companies: {len(df)}")
    
    # Create output directories
    os.makedirs('data/company_profiles_raw/odm_customers', exist_ok=True)
    os.makedirs('data/company_profiles_raw/end_users', exist_ok=True)
    
    odm_count = 0
    end_user_count = 0
    
    for idx, row in df.iterrows():
        company = str(row['Company Name']).strip()
        website = str(row['Website']).strip()
        industry = str(row.get('Industry', ''))
        assessment = str(row.get('My Assessment', ''))
        product_cat = str(row.get('Product relevance', ''))
        
        if not website or website == 'nan':
            print(f"[{idx+1}/{len(df)}] {company[:30]} - SKIPPED (no website)")
            continue
        
        # Classify company type
        company_type = classify_company_type(assessment)
        output_dir = f"data/company_profiles_raw/{company_type}s"
        
        print(f"[{idx+1}/{len(df)}] {company[:30]} ({company_type})")
        
        # Scrape website pages
        pages = scrape_company(website)
        
        if pages:
            # Save profile
            path = save_profile(company, industry, product_cat, assessment, company_type, pages, output_dir)
            print(f" → saved")
            
            if company_type == 'end_user':
                end_user_count += 1
            else:
                odm_count += 1
        else:
            print(f" → failed")
        
        time.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"ODM Customers: {odm_count} profiles")
    print(f"End Users: {end_user_count} profiles")
    print(f"\nSaved to:")
    print(f"  - data/company_profiles_raw/odm_customers/")
    print(f"  - data/company_profiles_raw/end_users/")


if __name__ == "__main__":
    main()
