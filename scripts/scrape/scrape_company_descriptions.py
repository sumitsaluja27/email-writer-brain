#!/usr/bin/env python3
"""
Scrape comprehensive company descriptions for RAG analysis.
Creates a clean CSV with: Company Name, Industry, Description
"""
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import os

# Files
INPUT_FILE = 'data/Companies/COMPLETE_LIST_INDUSTRY_FILTERED.csv'
OUTPUT_FILE = 'data/Companies/company_descriptions.csv'

async def extract_company_description(url):
    """Extract comprehensive company description from website"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Visit homepage
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            description_parts = []
            
            # 1. Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description_parts.append(meta_desc['content'].strip())
            
            # 2. Get main heading + nearby paragraphs
            h1 = soup.find('h1')
            if h1:
                # Get next few paragraphs after h1
                for sibling in h1.find_next_siblings(['p', 'div'], limit=3):
                    text = sibling.get_text().strip()
                    if len(text) > 50:  # Meaningful paragraph
                        description_parts.append(text)
            
            # 3. Look for "About Us" link and follow it
            about_link = soup.find('a', string=re.compile(r'about', re.IGNORECASE))
            if about_link and about_link.get('href'):
                try:
                    about_url = about_link['href']
                    if not about_url.startswith('http'):
                        from urllib.parse import urljoin
                        about_url = urljoin(url, about_url)
                    
                    await page.goto(about_url, wait_until='domcontentloaded', timeout=10000)
                    await page.wait_for_timeout(1500)
                    
                    about_content = await page.content()
                    about_soup = BeautifulSoup(about_content, 'html.parser')
                    
                    # Extract paragraphs from about page
                    about_paragraphs = about_soup.find_all('p', limit=5)
                    for para in about_paragraphs:
                        text = para.get_text().strip()
                        if len(text) > 50:
                            description_parts.append(text)
                except:
                    pass  # If about page fails, continue with what we have
            
            await browser.close()
            
            # Combine and clean
            if description_parts:
                full_description = ' '.join(description_parts)
                # Clean up
                full_description = re.sub(r'\s+', ' ', full_description)  # Normalize whitespace
                full_description = full_description[:1000]  # Limit to 1000 chars
                return full_description
            
            return "No description found"
    
    except Exception as e:
        return f"Error: {str(e)[:100]}"

async def scrape_all_companies():
    """Main scraping function"""
    print("="*80)
    print("SCRAPING COMPANY DESCRIPTIONS")
    print("="*80)
    
    # Load input
    print(f"\nLoading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"Total companies: {len(df)}")
    
    # Check for existing output
    if os.path.exists(OUTPUT_FILE):
        print(f"\nResuming from existing file: {OUTPUT_FILE}")
        output_df = pd.read_csv(OUTPUT_FILE)
        already_scraped = set(output_df['Company Name'].values)
        print(f"Already scraped: {len(already_scraped)} companies")
    else:
        output_df = pd.DataFrame(columns=['Company Name', 'Industry', 'Scraped_Description'])
        already_scraped = set()
    
    # Count companies with websites
    has_website = df['Website'].notna() & (df['Website'] != '')
    print(f"Companies with websites: {has_website.sum()}")
    print(f"Remaining to scrape: {has_website.sum() - len(already_scraped)}")
    
    print("\n" + "="*80)
    print("STARTING SCRAPE")
    print("="*80)
    print()
    
    scraped_count = len(already_scraped)
    
    for idx, row in df.iterrows():
        company_name = row['Company Name']
        
        # Skip if already scraped
        if company_name in already_scraped:
            continue
        
        industry = row['Industry']
        website = row.get('Website')
        
        if pd.isna(website) or not website:
            # Add with "no website" note
            new_row = pd.DataFrame([{
                'Company Name': company_name,
                'Industry': industry,
                'Scraped_Description': 'No website available'
            }])
            output_df = pd.concat([output_df, new_row], ignore_index=True)
            continue
        
        scraped_count += 1
        print(f"[{scraped_count}/{len(df)}] {company_name}")
        print(f"  URL: {website}")
        
        description = await extract_company_description(website)
        print(f"  Description: {description[:80]}...")
        
        # Add to output
        new_row = pd.DataFrame([{
            'Company Name': company_name,
            'Industry': industry,
            'Scraped_Description': description
        }])
        output_df = pd.concat([output_df, new_row], ignore_index=True)
        
        # Save progress every 10 companies
        if scraped_count % 10 == 0:
            output_df.to_csv(OUTPUT_FILE, index=False)
            print(f"  💾 Progress saved ({scraped_count} total)")
        
        # Rate limiting - be polite to servers
        await asyncio.sleep(2)
    
    # Final save
    output_df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*80)
    print("SCRAPING COMPLETE!")
    print("="*80)
    print(f"Total companies scraped: {len(output_df)}")
    print(f"Output saved to: {OUTPUT_FILE}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(scrape_all_companies())
