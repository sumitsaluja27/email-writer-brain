#!/usr/bin/env python3
"""
Scrape websites to get one-line company summaries for filtered companies.
Updates COMPLETE_LIST_INDUSTRY_FILTERED.csv in-place.
"""
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def get_company_summary(url):
    """Scrape website and extract a brief company summary"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try to find company description/summary
            summary = None
            
            # Method 1: Look for meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                summary = meta_desc['content'].strip()
            
            # Method 2: Look for common about/description text
            if not summary:
                # Look for h1 + first paragraph
                h1 = soup.find('h1')
                if h1:
                    next_p = h1.find_next('p')
                    if next_p:
                        summary = next_p.get_text().strip()
            
            # Method 3: First substantial paragraph
            if not summary:
                paragraphs = soup.find_all('p')
                for p in paragraphs[:10]:  # Check first 10 paragraphs
                    text = p.get_text().strip()
                    if len(text) > 50 and len(text) < 500:  # Reasonable length
                        summary = text
                        break
            
            await browser.close()
            
            # Clean up summary
            if summary:
                summary = re.sub(r'\s+', ' ', summary)  # Normalize whitespace
                summary = summary[:300]  # Limit length
            
            return summary or "No summary found"
    
    except Exception as e:
        return f"Error: {str(e)[:50]}"

async def process_companies():
    """Process all companies and add summaries"""
    csv_file = 'data/Companies/COMPLETE_LIST_INDUSTRY_FILTERED.csv'
    
    print("="*80)
    print("SCRAPING COMPANY SUMMARIES")
    print("="*80)
    
    df = pd.read_csv(csv_file)
    print(f"\nTotal companies: {len(df)}")
    
    # Add summary column if it doesn't exist
    if 'Company_Summary' not in df.columns:
        df['Company_Summary'] = None
    
    # Count companies with/without websites
    has_website = df['Website'].notna() & (df['Website'] != '')
    print(f"Companies with websites: {has_website.sum()}")
    
    # Process companies
    processed = 0
    
    for idx, row in df.iterrows():
        # Skip if already has summary
        if pd.notna(row.get('Company_Summary')) and row['Company_Summary'] != '':
            continue
        
        company_name = row['Company Name']
        website = row.get('Website')
        
        if pd.isna(website) or not website:
            df.at[idx, 'Company_Summary'] = "No website available"
            continue
        
        processed += 1
        print(f"[{processed}/{has_website.sum()}] {company_name}")
        print(f"  URL: {website}")
        
        summary = await get_company_summary(website)
        df.at[idx, 'Company_Summary'] = summary
        
        print(f"  Summary: {summary[:80]}...")
        
        # Save progress every 10 companies
        if processed % 10 == 0:
            df.to_csv(csv_file, index=False)
            print(f"  💾 Progress saved ({processed} done)")
        
        # Rate limiting
        await asyncio.sleep(2)
    
    # Final save
    df.to_csv(csv_file, index=False)
    
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"Total companies processed: {processed}")
    print(f"File updated: {csv_file}")

if __name__ == "__main__":
    asyncio.run(process_companies())
