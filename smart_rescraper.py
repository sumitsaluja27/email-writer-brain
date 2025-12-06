#!/usr/bin/env python3
"""
SMART Company Description Scraper - LLM Powered
================================================

This scraper uses llama3.1 to intelligently extract company descriptions
from website HTML, avoiding contact forms, navigation, and junk text.

WORKFLOW:
1. Visit website + about page
2. Extract all text content
3. Send to llama3.1 with prompt: "Extract what this company does"
4. Get clean, meaningful description
5. Update company_descriptions.csv IN-PLACE
"""

import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import ollama
import re
import sys

INPUT_FILE = 'data/Companies/companies_TO_FIX.csv'
FAILED_FILE = 'data/Companies/companies_RESCRAPE_FAILED.csv'

async def scrape_website_content(url):
    """Scrape raw text content from website"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Visit homepage
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'form']):
                element.decompose()
            
            # Get main text
            homepage_text = soup.get_text(separator=' ', strip=True)
            
            # Try to find and visit About page
            about_text = ""
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
                    
                    for element in about_soup(['script', 'style', 'nav', 'footer', 'header', 'form']):
                        element.decompose()
                    
                    about_text = about_soup.get_text(separator=' ', strip=True)
                except:
                    pass
            
            await browser.close()
            
            # Combine homepage + about page (limit length)
            combined_text = (homepage_text + " " + about_text)[:3000]
            return combined_text
            
    except Exception as e:
        return None

def extract_description_with_llm(company_name, industry, website_text):
    """Use llama3.1 to extract clean company description"""
    
    prompt = f"""You are analyzing website content to extract a company description.

Company Name: {company_name}
Industry: {industry}

Website Content (may contain junk):
{website_text}

Extract ONLY what this company actually does - their products, services, and business focus.
Ignore: contact forms, navigation menus, cookie notices, "fill out form" text.

Respond with ONLY a 2-3 sentence description of what the company does. Be specific and factual.
If you cannot find meaningful information, respond with: "Insufficient information"
"""
    
    try:
        response = ollama.generate(
            model='llama3.1:latest',
            prompt=prompt,
            options={'temperature': 0.3}
        )
        
        description = response['response'].strip()
        
        # Validate response
        if len(description) < 20 or 'insufficient' in description.lower():
            return None
        
        return description
        
    except Exception as e:
        print(f"    LLM Error: {str(e)[:50]}")
        return None

async def rescrape_company(company_name, industry, website):
    """Rescrape a company with LLM intelligence"""
    
    print(f"  Scraping website...")
    website_text = await scrape_website_content(website)
    
    if not website_text:
        print(f"  ❌ Failed to scrape website")
        return None
    
    print(f"  Sending to LLM for analysis...")
    description = extract_description_with_llm(company_name, industry, website_text)
    
    if description:
        print(f"  ✅ Got description: {description[:80]}...")
        return description
    else:
        print(f"  ❌ LLM could not extract description")
        return None

async def main():
    print("="*80)
    print("SMART RESCRAPING WITH LLM")
    print("="*80)
    
    # Load current file
    df = pd.read_csv(INPUT_FILE)
    print(f"\nTotal companies: {len(df)}")
    
    # Find companies with bad descriptions
    bad_descriptions = df[
        df['Scraped_Description'].str.contains('fill out|form|cookie|navigation', case=False, na=False) |
        (df['Scraped_Description'].str.len() < 50)
    ]
    
    print(f"Companies with bad descriptions: {len(bad_descriptions)}")
    print(f"\nStarting smart rescrape...\n")
    
    failed_companies = []
    improved_count = 0
    
    for idx, row in bad_descriptions.iterrows():
        company_name = row['Company Name']
        industry = row['Industry']
        website = row.get('Website', None)
        
        print(f"[{improved_count + len(failed_companies) + 1}/{len(bad_descriptions)}] {company_name}")
        
        # Skip if no website
        if pd.isna(website) or not website:
            print(f"  ⚠️  No website")
            failed_companies.append(row)
            continue
        
        # Rescrape with LLM
        new_description = await rescrape_company(company_name, industry, website)
        
        if new_description:
            # Update in dataframe
            df.at[idx, 'Scraped_Description'] = new_description
            improved_count += 1
            
            # Save progress every 10 companies
            if improved_count % 10 == 0:
                df.to_csv(INPUT_FILE, index=False)
                print(f"  💾 Progress saved ({improved_count} improved)")
        else:
            failed_companies.append(row)
        
        # Rate limiting
        await asyncio.sleep(3)
    
    # Final save
    df.to_csv(INPUT_FILE, index=False)
    
    # Save failed companies
    if failed_companies:
        failed_df = pd.DataFrame(failed_companies)
        failed_df.to_csv(FAILED_FILE, index=False)
    
    print("\n" + "="*80)
    print("RESCRAPING COMPLETE")
    print("="*80)
    print(f"Improved descriptions: {improved_count}")
    print(f"Failed to improve: {len(failed_companies)}")
    print(f"\n✅ Updated: {INPUT_FILE}")
    if failed_companies:
        print(f"❌ Failed companies saved to: {FAILED_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
