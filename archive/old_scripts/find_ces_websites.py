import pandas as pd
import time
import os
import re
import asyncio
from urllib.parse import urlparse
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler

# ───── SETTINGS ─────
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_with_websites.csv"
DELAY = 2.0
SAVE_EVERY = 50

JUNK_DOMAINS = [
    "reddit.com", "wikipedia.org", "github.com", "linkedin.com",
    "facebook.com", "twitter.com", "youtube.com", "instagram.com",
    "amazon.com", "ebay.com", "alibaba.com", "aliexpress.com",
    "zhihu.com", "sogou.com", "bing.com", "yahoo.com", "baidu.com",
    "cnn.com", "bbc.com", "techradar.com", "theverge.com", "wired.com",
    "forbes.com", "bloomberg.com", "reuters.com",
    "ces.tech", "exhibitors.ces.tech", "devex.com", "ceatec.com",
    "archive.org", "koreashop", "yellowpages", "crunchbase.com",
    "zoominfo.com", "pitchbook.com", "businesswire.com", "prnewswire.com",
    "tradeindia.com", "made-in-china.com", "globalsources.com"
]

# ───── HELPER & SEARCH FUNCTIONS ─────

def smart_search(company_name, summary=""):
    """Yields potential website URLs from a search query."""
    # Extract 2-3 key words from summary (ignore common words)
    summary_keywords = ""
    if summary and isinstance(summary, str):
        words = [w for w in re.split(r'\W+', summary) if len(w) > 4]
        summary_keywords = " ".join(words[:3]) if words else ""
    
    query = f'"{company_name}" {summary_keywords} official website -inurl:(linkedin twitter facebook youtube crunchbase ces.tech)'
    try:
        results = DDGS().text(query, max_results=5)
        for r in results:
            url = r.get("href")
            if url and url.startswith("http") and not any(junk in url.lower() for junk in JUNK_DOMAINS):
                yield url
    except Exception as e:
        print(f"  Search error: {e}")

def check_name(text, company_name):
    """Checks if any significant word from the company name appears in the text."""
    name_words = {word.lower() for word in re.split(r'\W+', company_name) if len(word) >= 3}
    text_lower = text.lower()
    for word in name_words:
        if word in text_lower:
            return True
    return False

def domain_matches_company(url, company_name):
    """Check if domain contains company name (fuzzy match)"""
    try:
        domain = urlparse(url).netloc.lower()
        # Remove common suffixes from company name
        clean_name = re.sub(r'\b(inc|ltd|corp|co|llc|corporation|company|international|group|limited)\b', '', company_name, flags=re.IGNORECASE)
        # Check if any significant word from company name is in domain
        name_words = [w.lower() for w in re.split(r'\W+', clean_name) if len(w) >= 4]
        return any(word in domain for word in name_words)
    except:
        return False

async def is_real_website(crawler, url, company_name):
    """Crawls a website and checks if the company name is in the content."""
    # Quick domain check before crawling
    if not domain_matches_company(url, company_name):
        print(f"  Domain mismatch for {url}")
        return False
    
    try:
        result = await crawler.arun(url=url, bypass_cache=True)
        if not result or not result.markdown:
            return False
        return check_name(result.markdown, company_name)
    except:
        return False

async def find_and_validate_website(crawler, company_name, summary=""):
    """Iterates through search results and returns the first validated URL."""
    for url in smart_search(company_name, summary):
        print(f"   Checking → {url}")
        if await is_real_website(crawler, url, company_name):
            return url
    return None

# ───── MAIN SCRIPT ─────

async def process_companies():
    print("Starting processing of non-Asian companies list.")

    # Load data, resuming if output file exists
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from existing output file: {OUTPUT_FILE}")
        df = pd.read_csv(OUTPUT_FILE, encoding="utf-8")
    elif os.path.exists(INPUT_FILE):
        print(f"Loading input file: {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    else:
        print(f"Error: Input file not found at {INPUT_FILE}")
        return

    # Ensure required columns exist
    if "Search_Status" not in df.columns:
        df["Search_Status"] = ""
    df['Correct_Website'] = df.get('Correct_Website', pd.Series(dtype=bool)).fillna(False)
    df['Validation_Status'] = df.get('Validation_Status', pd.Series(dtype=str)).fillna('')
    
    crawler = AsyncWebCrawler()

    for i, row in df.iterrows():
        # Skip if already processed in a previous run
        if df.loc[i, "Search_Status"] == "Skipped - Valid":
            continue

        company = row["Exhibitor"].strip()
        status_to_set = ""
        
        print(f"\n({i+1}/{len(df)}) Processing → {company}")

        # Apply logic based on the row's state
        if row['Correct_Website'] == True:
            status_to_set = "Skipped - Valid"
            print(f"   Action: {status_to_set}")

        elif row['Correct_Website'] == False:
            status_to_set = "Re-searched"
            print(f"   Action: {status_to_set} (was previously marked incorrect)")
            df.loc[i, 'Website'] = ""
            new_website = await find_and_validate_website(crawler, company, row.get("Summary", ""))
            if new_website:
                df.loc[i, 'Website'] = new_website
                print(f"   New Website Found → {new_website}")
            else:
                print("   No new website found.")

        elif pd.isna(row['Website']) or row['Website'] == '':
            status_to_set = "Newly searched"
            print(f"   Action: {status_to_set}")
            new_website = await find_and_validate_website(crawler, company, row.get("Summary", ""))
            if new_website:
                df.loc[i, 'Website'] = new_website
                print(f"   Website Found → {new_website}")
            else:
                print("   No website found.")

        elif "⚠️ UNCLEAR" in row['Validation_Status']:
            status_to_set = "Retried"
            print(f"   Action: {status_to_set} (was previously unclear)")
            if await is_real_website(crawler, row['Website'], company):
                df.loc[i, 'Validation_Status'] = '✅ GOOD'
                df.loc[i, 'Validation_Notes'] = 'Passed on retry'
                df.loc[i, 'Correct_Website'] = True
                print("   Result: Validation passed on retry.")
            else:
                print("   Result: Validation still failed.")
        
        else:
            status_to_set = "Skipped - No Action Needed"

        df.loc[i, 'Search_Status'] = status_to_set

        # Auto-save
        if (i + 1) % SAVE_EVERY == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            print(f"   --- Progress saved ---")

        await asyncio.sleep(DELAY)

    # Final save and summary
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print("\nProcessing complete. Final file saved.")

    summary = df["Search_Status"].value_counts().to_dict()
    print("\n===== PROCESSING SUMMARY =====")
    for status, count in summary.items():
        print(f"{status}: {count}")
    print("==============================")


if __name__ == "__main__":
    asyncio.run(process_companies())
