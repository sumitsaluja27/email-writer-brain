"""
Hybrid Company Scraper
- Uses Jina Reader API first (fast, 1000/day free)
- Falls back to Playwright if Jina fails or rate-limited
- Updates unique_companies_list.csv IN-PLACE
- Resumable (saves progress after each company)
"""

import pandas as pd
import requests
import time
import re
import os

# Config
INPUT_FILE = 'data/Companies/unique_companies_list.csv'
JINA_BASE = 'https://r.jina.ai/'
JINA_DAILY_LIMIT = 1000
REQUEST_DELAY = 1  # seconds between requests

# Playwright fallback (imported only if needed)
playwright_available = False

def scrape_with_jina(url):
    """Scrape using Jina Reader API."""
    if not url or pd.isna(url) or url.strip() == '':
        return None, None
    
    try:
        jina_url = JINA_BASE + url.strip()
        response = requests.get(jina_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CompanyScraper/1.0)'
        })
        
        if response.status_code == 200:
            content = response.text[:5000]  # Limit to first 5000 chars
            description = extract_description(content)
            country = extract_country(content)
            return description, country
        elif response.status_code == 429:
            print("   ⚠️  Jina rate limit hit")
            return "RATE_LIMITED", None
        else:
            return None, None
    except Exception as e:
        return None, None

def scrape_with_playwright(url):
    """Fallback: Scrape using Playwright."""
    global playwright_available
    
    if not playwright_available:
        try:
            from playwright.sync_api import sync_playwright
            playwright_available = True
        except ImportError:
            print("   ⚠️  Playwright not available")
            return None, None
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            content = page.content()[:5000]
            browser.close()
            
            description = extract_description(content)
            country = extract_country(content)
            return description, country
    except Exception as e:
        return None, None

def extract_description(content):
    """Extract a clean company description from scraped content."""
    if not content:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Take first 500 chars as description
    if len(text) > 500:
        text = text[:500] + "..."
    return text

def extract_country(content):
    """Try to extract country from content."""
    if not content:
        return ""
    
    # Common country patterns
    countries = [
        'United States', 'USA', 'UK', 'United Kingdom', 'Germany', 'France',
        'Canada', 'Australia', 'India', 'Japan', 'China', 'South Korea',
        'Netherlands', 'Sweden', 'Switzerland', 'Israel', 'Singapore'
    ]
    
    content_lower = content.lower()
    for country in countries:
        if country.lower() in content_lower:
            return country
    return ""

def main():
    print("=" * 60)
    print("HYBRID COMPANY SCRAPER")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(INPUT_FILE)
    total = len(df)
    
    # Add columns if not exist
    if 'Description' not in df.columns:
        df['Description'] = ''
    if 'Country' not in df.columns:
        df['Country'] = ''
    
    jina_count = 0
    success_count = 0
    
    for idx, row in df.iterrows():
        company = row['Company Name']
        website = row['Website']
        
        # Skip if already scraped
        if pd.notna(row['Description']) and row['Description'] != '':
            continue
        
        print(f"[{idx+1}/{total}] {company}")
        
        # Try Jina first
        if jina_count < JINA_DAILY_LIMIT:
            description, country = scrape_with_jina(website)
            jina_count += 1
            
            if description == "RATE_LIMITED":
                print("   Switching to Playwright...")
                description, country = scrape_with_playwright(website)
        else:
            # Use Playwright after Jina limit
            description, country = scrape_with_playwright(website)
        
        # Update dataframe
        if description:
            df.at[idx, 'Description'] = description
            success_count += 1
            print(f"   ✅ Got description")
        else:
            df.at[idx, 'Description'] = 'No description found'
            print(f"   ❌ No description")
        
        if country:
            df.at[idx, 'Country'] = country
        
        # Save progress every 10 companies
        if (idx + 1) % 10 == 0:
            df.to_csv(INPUT_FILE, index=False)
            print(f"   💾 Progress saved ({success_count} successful)")
        
        time.sleep(REQUEST_DELAY)
    
    # Final save
    df.to_csv(INPUT_FILE, index=False)
    
    print("=" * 60)
    print(f"DONE: {success_count}/{total} companies scraped")
    print(f"Jina requests used: {jina_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
