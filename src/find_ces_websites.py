import pandas as pd
import time
import re
import os
from duckduckgo_search import DDGS
from urllib.parse import urlparse

# --- Configuration ---
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_enriched.csv"
SEARCH_DELAY_SECONDS = 1.5 # 1-2 second delay
PROGRESS_REPORT_INTERVAL = 50
INCREMENTAL_SAVE_INTERVAL = 100
MAX_SEARCH_RESULTS = 3 # Top 3 results to check

def is_valid_url(url):
    """Checks if a string is a valid HTTP/HTTPS URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

def find_company_website(company_name):
    """
    Searches for the official website of a company using DuckDuckGo Search.
    Returns the first valid URL found in the top results, or None.
    """
    search_query = f"{company_name} official website"
    try:
        # DDGS().text() returns a list of dicts, each with 'href' key for URL
        results = DDGS().text(keywords=search_query, max_results=MAX_SEARCH_RESULTS)
        
        for result in results:
            url = result.get('href')
            if url and is_valid_url(url):
                # Basic filtering to avoid social media or directory links as primary website
                if "linkedin.com" not in url and \
                   "facebook.com" not in url and \
                   "twitter.com" not in url and \
                   "youtube.com" not in url and \
                   "crunchbase.com" not in url and \
                   "zoominfo.com" not in url and \
                   "ces.tech" not in url: # Avoid CES directory itself
                    return url
        return None
    except Exception as e:
        print(f"  Error during search for '{company_name}': {e}")
        return None

def main():
    print(f"Starting website enrichment for CES 2026 companies.")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")

    # Load existing data or create new DataFrame
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from existing output file: {OUTPUT_FILE}")
        df = pd.read_csv(OUTPUT_FILE, encoding='latin-1') # Added encoding
    else:
        print(f"Creating new output file. Loading input: {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE, encoding='latin-1') # Added encoding
        df['Website'] = '' # Add Website column if it doesn't exist

    total_companies = len(df)
    print(f"Total companies to process: {total_companies}")

    start_index = 0
    # Find where to resume from
    if 'Website' in df.columns:
        # Find the first row where 'Website' is empty or NaN
        first_empty_website_index = df[df['Website'].isnull() | (df['Website'] == '')].index
        if not first_empty_website_index.empty:
            start_index = first_empty_website_index[0]
            print(f"Resuming from company index: {start_index} (Company: {df.loc[start_index, 'Exhibitor']})")
        else:
            print("All companies already have a website. Exiting.")
            return

    for i in range(start_index, total_companies):
        company_name = df.loc[i, 'Exhibitor']
        
        # Skip if website already exists (for robustness, even if start_index is correct)
        if pd.notna(df.loc[i, 'Website']) and df.loc[i, 'Website'] != '':
            print(f"  Skipping {company_name} (Website already exists).")
            continue

        print(f"Processing {i+1}/{total_companies}: {company_name}")
        website_url = find_company_website(company_name)
        
        if website_url:
            df.loc[i, 'Website'] = website_url
            print(f"  Found: {website_url}")
        else:
            df.loc[i, 'Website'] = '' # Explicitly set to empty string if not found
            print(f"  No website found.")

        # Progress report
        if (i + 1) % PROGRESS_REPORT_INTERVAL == 0:
            print(f"--- Progress: {i+1}/{total_companies} companies processed ---")

        # Incremental save
        if (i + 1) % INCREMENTAL_SAVE_INTERVAL == 0:
            print(f"--- Saving progress to {OUTPUT_FILE} ---")
            df.to_csv(OUTPUT_FILE, index=False)
            print("--- Progress saved ---")

        time.sleep(SEARCH_DELAY_SECONDS)

    # Final save
    print(f"\nAll companies processed. Final save to {OUTPUT_FILE}.")
    df.to_csv(OUTPUT_FILE, index=False)
    print("Script finished.")

if __name__ == "__main__":
    main()