import pandas as pd
import asyncio
import os
import re
from urllib.parse import urlparse
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

# ───── SETTINGS ─────
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_validated.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_validated.csv" # Read and write to the same file
DELAY = 2.0
SAVE_EVERY = 50

# ───── HELPER FUNCTIONS ─────

def get_domain(url):
    """Extracts the domain from a URL."""
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

async def find_linkedin_on_site(crawler, url):
    """Crawls a website and looks for a link to a LinkedIn company page."""
    print(f"   Crawling {url} for LinkedIn link...")
    try:
        result = await crawler.arun(url=url)
        if not result or not result.html:
            return None
        
        soup = BeautifulSoup(result.html, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if "linkedin.com/company/" in href:
                print(f"   Found on-site → {href}")
                return href
        return None
    except Exception as e:
        print(f"   Error crawling site: {e}")
        return None

async def find_linkedin_by_search(company_name, summary, website_domain):
    """Falls back to a web search to find the LinkedIn URL."""
    print("   Falling back to web search...")
    
    # Extract 2-3 key words from summary
    summary_words = " ".join([w for w in re.split(r'\W+', summary) if len(w) > 4][:3])

    # Build enhanced query
    query = f'"{company_name}" {summary_words} {website_domain} linkedin'
    
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(DDGS().text, query, max_results=3),
            timeout=10.0
        )
        # Check each result for linkedin.com/company/ URL
        for result in results:
            url = result.get("href", "")
            if "linkedin.com/company/" in url:
                print(f"   Found via search → {url}")
                return url
        return None
    except asyncio.TimeoutError:
        print("   Web search timed out.")
        return None
    except Exception as e:
        print(f"   Web search error: {e}")
        return None

# ───── MAIN SCRIPT ─────

async def main():
    print(f"Starting LinkedIn profile finder.")
    
    # Load data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        return
    
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    print(f"Loaded {len(df)} companies.")

    # Add LinkedIn_URL column if it doesn't exist
    if "LinkedIn_URL" not in df.columns:
        df["LinkedIn_URL"] = ""

    # Filter for rows to process
    to_process = df[df['Correct_Website'] == True].copy()
    if to_process.empty:
        print("No companies with validated websites to process.")
        return
        
    print(f"Found {len(to_process)} companies with valid websites to check for LinkedIn profiles.")

    crawler = AsyncWebCrawler()
    
    newly_found_count = 0
    for i, row in to_process.iterrows():
        # Skip if already found
        if pd.notna(df.loc[i, "LinkedIn_URL"]) and df.loc[i, "LinkedIn_URL"] not in ["", "Not Found"]:
            continue

        company = row["Exhibitor"]
        website = row["Website"]
        summary = row.get("Summary", "")
        
        print(f"\n({i+1}/{len(df)}) Processing → {company}")

        # Strategy 1: On-site search
        linkedin_url = await find_linkedin_on_site(crawler, website)

        # Strategy 2: Web search (fallback)
        if not linkedin_url:
            website_domain = get_domain(website)
            linkedin_url = await find_linkedin_by_search(company, summary, website_domain)

        if linkedin_url:
            df.loc[i, "LinkedIn_URL"] = linkedin_url
            newly_found_count += 1
        else:
            df.loc[i, "LinkedIn_URL"] = "Not Found" # Mark as processed
            print("   No LinkedIn profile found.")

        # Auto-save
        if (newly_found_count > 0 and newly_found_count % SAVE_EVERY == 0):
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            print(f"   --- Progress saved ---")

        await asyncio.sleep(DELAY)

    # Final save
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print("\nProcessing complete. Final file saved.")
    print(f"Found {newly_found_count} new LinkedIn profiles.")

if __name__ == "__main__":
    asyncio.run(main())