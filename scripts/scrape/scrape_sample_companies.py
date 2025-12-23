"""
Scrape ALL sample company websites and build RAG training data.
Groups content by product category (Beacon, IP Camera, Dashcam, Bodycam, etc.)
"""

import pandas as pd
import requests
import json
from datetime import datetime
import time

JINA_API = 'https://r.jina.ai/'

def scrape_website(url, max_chars=5000):
    """Scrape website content using Jina API."""
    if not url or url == 'nan' or pd.isna(url):
        return ""
    try:
        if not str(url).startswith('http'):
            url = 'https://' + str(url)
        
        # Get main page
        response = requests.get(JINA_API + url, timeout=45, headers={'Accept': 'text/plain'})
        content = response.text[:max_chars] if response.status_code == 200 else ""
        
        # Try to get about/products page for more context
        for subpage in ['/about', '/about-us', '/products', '/solutions']:
            try:
                sub_url = url.rstrip('/') + subpage
                resp = requests.get(JINA_API + sub_url, timeout=30, headers={'Accept': 'text/plain'})
                if resp.status_code == 200 and len(resp.text) > 500:
                    content += f"\n\n=== {subpage.upper()} PAGE ===\n" + resp.text[:2000]
                    break
            except:
                pass
        
        return content[:max_chars]
    except Exception as e:
        print(f"    Error: {e}")
        return ""

def main():
    print("=" * 60)
    print("SCRAPING SAMPLE COMPANIES FOR RAG TRAINING")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load sample companies
    df = pd.read_csv('data/Companies/sample_companies_for_review.csv')
    print(f"Total: {len(df)} companies")
    print(f"Product categories: {df['Product relevance'].unique().tolist()}")
    print()
    
    results = []
    
    for idx, row in df.iterrows():
        name = str(row['Company Name']).strip()
        website = str(row['Website'])
        product = str(row['Product relevance'])
        assessment = str(row['My Assessment'])
        industry = str(row.get('Industry', ''))
        
        print(f"[{idx+1}/{len(df)}] {name[:30]}... ({product})", end=" ", flush=True)
        
        # Scrape website
        content = scrape_website(website)
        
        if content:
            print(f"✓ {len(content)} chars")
        else:
            print("✗ Failed")
        
        results.append({
            'company_name': name,
            'website': website,
            'product_category': product,
            'industry': industry,
            'assessment': assessment,
            'website_content': content,
            'content_length': len(content)
        })
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_csv('data/RAG/sample_companies_scraped.csv', index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total scraped: {len(result_df)}")
    print(f"Successful: {len(result_df[result_df['content_length'] > 0])}")
    print()
    print("By product category:")
    for product in result_df['product_category'].unique():
        subset = result_df[result_df['product_category'] == product]
        success = len(subset[subset['content_length'] > 0])
        print(f"  {product}: {success}/{len(subset)} scraped")
    
    print(f"\nSaved to: data/RAG/sample_companies_scraped.csv")

if __name__ == "__main__":
    main()
