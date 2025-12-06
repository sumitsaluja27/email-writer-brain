#!/usr/bin/env python3
"""
Enrich company CSV files by scraping websites for:
- Country/Location
- LinkedIn company URL
"""
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import sys

async def scrape_company_info(url):
    """Scrape website for location and LinkedIn URL"""
    result = {
        'country': None,
        'linkedin_url': None,
        'status': 'success'
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract LinkedIn URL
            linkedin_link = soup.find('a', href=re.compile(r'linkedin\.com/company'))
            if linkedin_link:
                result['linkedin_url'] = linkedin_link['href']
                # Clean up LinkedIn URL
                if 'linkedin.com/company/' in result['linkedin_url']:
                    result['linkedin_url'] = result['linkedin_url'].split('?')[0]
            
            # Extract country/location
            # Look for common patterns
            text = soup.get_text().lower()
            
            # Common location indicators
            location_patterns = [
                r'headquarters[:\s]+([^,\n]+)',
                r'based in[:\s]+([^,\n]+)',
                r'located in[:\s]+([^,\n]+)',
                r'address[:\s]+([^,\n]+)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    # Try to extract country from location
                    result['country'] = location
                    break
            
            # Also check footer for country/address
            footer = soup.find('footer')
            if footer and not result['country']:
                footer_text = footer.get_text()
                # Look for country names
                countries = ['USA', 'United States', 'UK', 'United Kingdom', 'Canada', 
                           'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 
                           'Sweden', 'Norway', 'Denmark', 'Finland', 'Australia',
                           'Singapore', 'India', 'Israel', 'Switzerland', 'Austria']
                
                for country in countries:
                    if country.lower() in footer_text.lower():
                        result['country'] = country
                        break
            
            await browser.close()
            
    except Exception as e:
        result['status'] = f'error: {str(e)[:100]}'
    
    return result

async def enrich_csv(input_file, output_file):
    """Enrich CSV file with scraped data"""
    print("="*80)
    print(f"ENRICHING: {input_file}")
    print("="*80)
    
    df = pd.read_csv(input_file)
    print(f"\nTotal companies: {len(df)}")
    
    # Add new columns if they don't exist
    if 'LinkedIn_Company' not in df.columns:
        df['LinkedIn_Company'] = None
    if 'Scraped_Country' not in df.columns:
        df['Scraped_Country'] = None
    if 'Scrape_Status' not in df.columns:
        df['Scrape_Status'] = None
    
    # Process each company
    for idx, row in df.iterrows():
        company_name = row['Company Name'] if pd.notna(row['Company Name']) else row['Exhibitor']
        website = row.get('Website')
        
        if pd.isna(website) or not website:
            print(f"[{idx+1}/{len(df)}] {company_name} - No website, skipping")
            df.at[idx, 'Scrape_Status'] = 'no_website'
            continue
        
        print(f"[{idx+1}/{len(df)}] Scraping: {company_name}")
        print(f"  URL: {website}")
        
        result = await scrape_company_info(website)
        
        # Update dataframe
        if result['linkedin_url']:
            df.at[idx, 'LinkedIn_Company'] = result['linkedin_url']
            print(f"  ✅ LinkedIn: {result['linkedin_url']}")
        
        if result['country']:
            df.at[idx, 'Scraped_Country'] = result['country']
            print(f"  ✅ Country: {result['country']}")
        
        df.at[idx, 'Scrape_Status'] = result['status']
        
        # Save progress after each company
        df.to_csv(output_file, index=False)
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    print(f"\n{'='*80}")
    print("ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Saved to: {output_file}")
    
    # Summary
    linkedin_found = df['LinkedIn_Company'].notna().sum()
    country_found = df['Scraped_Country'].notna().sum()
    print(f"\nResults:")
    print(f"  LinkedIn URLs found: {linkedin_found}/{len(df)}")
    print(f"  Countries found: {country_found}/{len(df)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python enrich_companies.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    asyncio.run(enrich_csv(input_file, output_file))
