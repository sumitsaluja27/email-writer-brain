"""
Company Enrichment Script using Playwright

This script enriches company data by scraping their websites and LinkedIn pages.
Uses Playwright directly for robust scraping compatible with Python 3.9+.

Input: CES_2026_CATEGORIZED.csv
Output: CES_2026_ENRICHED.csv with scraped summaries
"""

import os
import sys
import pandas as pd
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import time
from typing import Optional, Dict
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Configuration
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
INPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES_2026_CATEGORIZED.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES_2026_ENRICHED.csv")

# Crawling configuration
CRAWL_DELAY = 2  # Seconds between requests
MAX_RETRIES = 1
TIMEOUT = 30000  # Milliseconds (30 seconds)

# Validation Configuration
JUNK_DOMAINS = [
    "wikipedia.org", "linkedin.com", "facebook.com", "twitter.com", "youtube.com",
    "instagram.com", "pinterest.com", "zhihu.com", "yahoo.com", "zoom.us", 
    "ces.tech", "restaurantguru.com", "wongnai.com", "puzzle", "forum", 
    "directory", "blog", "news", "telegram", "bing.com", "amazon", "ebay", 
    "alibaba", "devex", "ceatec", "archive", "koreashop", "yellowpages", 
    "crunchbase", "reddit", "quora", "medium", "prnewswire", "businesswire",
    "glassdoor", "bloomberg", "forbes"
]

def validate_website_content(url: str, content: str, company_name: str) -> dict:
    """Validate if the website content matches the company."""
    if not url or not content:
        return {'verified': False, 'reason': 'No content/URL'}
        
    # 1. Check for junk domain
    try:
        domain = urlparse(url).netloc.lower()
        if any(junk in domain for junk in JUNK_DOMAINS):
            return {'verified': False, 'reason': 'Junk domain'}
    except:
        pass

    # 2. Check for company name in content (fuzzy match)
    if not isinstance(company_name, str):
        company_name = str(company_name) if company_name is not None else ""
        
    name_parts = [part.lower() for part in re.split(r'\W+', company_name) if len(part) >= 3]
    
    if not name_parts:
        return {'verified': True, 'reason': 'Name too short for strict check', 'warning': 'Manual review needed'}
        
    content_lower = content.lower()[:5000]
    match_found = any(part in content_lower for part in name_parts)
    
    if match_found:
        return {'verified': True, 'reason': 'Name match found'}
    else:
        return {'verified': False, 'reason': 'Company name not found in content'}

async def scrape_url(url: str, browser) -> Optional[Dict]:
    """Scrape a URL using Playwright."""
    if not url or pd.isna(url):
        return None
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    page = await browser.new_page()
    try:
        # Block resources to speed up
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font"] 
            else route.continue_())
            
        response = await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
        
        if not response or response.status >= 400:
            await page.close()
            return {
                'url': url,
                'content': None,
                'success': False,
                'error': f"HTTP {response.status if response else 'Unknown'}"
            }
            
        # Get text content
        content = await page.content()
        
        # Clean with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Basic cleanup
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        await page.close()
        return {
            'url': url,
            'content': text[:10000],  # Limit content size
            'success': True,
            'error': None
        }
        
    except Exception as e:
        await page.close()
        return {
            'url': url,
            'content': None,
            'success': False,
            'error': str(e)
        }

async def enrich_company(row: pd.Series, browser) -> Dict:
    """Enrich a single company's data."""
    company_name = row.get('Company Name') or row.get('Exhibitor', 'Unknown')
    tier = row.get('Data_Tier', 'UNKNOWN')
    
    enrichment = {
        'company_name': company_name,
        'tier': tier,
        'website_content': None,
        'linkedin_content': None,
        'enriched_summary': None,
        'scrape_status': 'pending',
        'errors': [],
        'website_verified': None,
        'validation_reason': None
    }
    
    # Scrape website
    website = row.get('Website') or row.get('Website_Found_By_Search')
    if website and not pd.isna(website):
        print(f"  📄 Scraping: {website}")
        web_result = await scrape_url(website, browser)
        
        if web_result and web_result['success']:
            enrichment['website_content'] = web_result['content']
            
            # Validate
            validation = validate_website_content(website, web_result['content'], company_name)
            enrichment['website_verified'] = validation['verified']
            enrichment['validation_reason'] = validation['reason']
            
            status_icon = "✅" if validation['verified'] else "⚠️"
            print(f"    {status_icon} Verified: {validation['verified']} ({validation['reason']})")
        else:
            error_msg = web_result['error'] if web_result else "Unknown error"
            enrichment['errors'].append(f"Website scrape failed: {error_msg}")
            enrichment['website_verified'] = False
            enrichment['validation_reason'] = "Scrape failed"
            print(f"    ❌ Failed: {error_msg}")
    
    # Create summary
    summary_parts = []
    if row.get('Full_Summary') and not pd.isna(row.get('Full_Summary')):
        summary_parts.append(f"Original Summary: {row.get('Full_Summary')}")
    if enrichment['website_content']:
        summary_parts.append(f"Website Content: {enrichment['website_content']}")
        
    if summary_parts:
        enrichment['enriched_summary'] = '\n\n'.join(summary_parts)
        enrichment['scrape_status'] = 'success'
    else:
        enrichment['enriched_summary'] = row.get('Full_Summary')
        enrichment['scrape_status'] = 'no_new_data'
    
    return enrichment

async def process_batch(df: pd.DataFrame, start_idx: int, batch_size: int, browser) -> list:
    """Process a batch of companies."""
    tasks = []
    end_idx = min(start_idx + batch_size, len(df))
    
    for idx in range(start_idx, end_idx):
        row = df.iloc[idx]
        tasks.append(enrich_company(row, browser))
        
    results = await asyncio.gather(*tasks)
    return results

async def main_async():
    print("=" * 80)
    print("COMPANY ENRICHMENT SCRIPT (Playwright)")
    print("=" * 80)
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} companies")
    
    # Priority sort
    tier_priority = ["GOLD", "SILVER", "BRONZE_WEB", "BRONZE_LI", "COPPER"]
    df['_tier_priority'] = df['Data_Tier'].apply(
        lambda x: tier_priority.index(x) if x in tier_priority else 999
    )
    df = df.sort_values('_tier_priority').reset_index(drop=True)
    
    # Initialize columns
    for col in ['Scraped_Summary', 'Scrape_Status', 'Scrape_Errors', 'Website_Verified', 'Validation_Reason']:
        df[col] = None
        
    BATCH_SIZE = 5
    total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"🚀 Starting enrichment of {len(df)} companies...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(df))
            
            print(f"\n📦 Batch {batch_num + 1}/{total_batches} ({start_idx}-{end_idx})")
            
            results = await process_batch(df, start_idx, BATCH_SIZE, browser)
            
            for i, result in enumerate(results):
                idx = start_idx + i
                df.at[idx, 'Scraped_Summary'] = result['enriched_summary']
                df.at[idx, 'Scrape_Status'] = result['scrape_status']
                df.at[idx, 'Scrape_Errors'] = ', '.join(result['errors']) if result['errors'] else None
                df.at[idx, 'Website_Verified'] = result.get('website_verified')
                df.at[idx, 'Validation_Reason'] = result.get('validation_reason')
            
            df.to_csv(OUTPUT_CSV, index=False)
            print(f"💾 Saved progress")
            
            if batch_num < total_batches - 1:
                await asyncio.sleep(CRAWL_DELAY)
                
        await browser.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
