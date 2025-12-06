import pandas as pd
import asyncio
import os
import re
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler

# ───── SETTINGS ─────
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_with_websites.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_validated.csv"
DELAY = 2.0
SAVE_EVERY = 100

JUNK_DOMAINS = [
    "wikipedia.org", "linkedin.com", "facebook.com", "twitter.com", "youtube.com",
    "zhihu.com", "yahoo.com", "zoom.us", "ces.tech", "restaurantguru.com",
    "wongnai.com", "puzzle", "forum", "directory", "blog", "news", "telegram",
    "bing.com", "amazon", "ebay", "alibaba", "devex", "ceatec", "archive",
    "koreashop", "yellowpages", "crunchbase", "reddit", "quora", "medium",
    "prnewswire", "businesswire"
]

SUBPAGE_PATTERNS = ["/news/", "/article/", "/profile/", "/blog/"]

COUNTRY_INDICATORS = {
    "China": ["china", "shenzhen", "beijing", "guangdong"],
    "Taiwan": ["taiwan", "taipei"],
    "Hong Kong": ["hong kong", "hk"],
    "Korea": ["korea", "seoul"],
    "Vietnam": ["vietnam", "hanoi"],
    "Singapore": ["singapore"]
}

# ───── HELPER FUNCTIONS ─────

def get_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

def check_domain_name_match(domain, company_name):
    """Check if a significant part of the company name is in the domain."""
    name_parts = [part.lower() for part in re.split(r'\W+', company_name) if len(part) >= 4]
    if not name_parts:
        return False
    return any(part in domain for part in name_parts)

def check_homepage(url):
    """Check if the URL looks like a homepage (not a subpage)."""
    path = urlparse(url).path
    return not any(pattern in path.lower() for pattern in SUBPAGE_PATTERNS)

def detect_country(text, company_name):
    """Detect country from text or company name."""
    content = (text + " " + company_name).lower()
    for country, indicators in COUNTRY_INDICATORS.items():
        if any(indicator in content for indicator in indicators):
            return country
    return "Unknown"

def check_name(text, company_name):
    name_words = {word.lower() for word in re.split(r'\W+', company_name) if len(word) >= 3}
    text_lower = text.lower()
    for word in name_words:
        if word in text_lower:
            return True
    return False

def check_keywords(text, summary):
    if not isinstance(summary, str) or not summary.strip():
        return False, "Summary is empty"
    summary_words = {word.lower() for word in re.split(r'\W+', summary) if len(word) > 4}
    if not summary_words:
        return False, "No suitable keywords in summary"
    text_lower = text.lower()
    matches = sum(1 for word in summary_words if word in text_lower)
    return matches >= 2, f"{matches} keyword(s) found"

async def revalidate_and_detect(crawler, row):
    """Performs stricter validation and country detection."""
    company_name = row["Exhibitor"]
    website_url = row["Website"]
    summary = row.get("Summary", "")
    notes = []

    # 1. Stricter URL validation
    domain = get_domain(website_url)
    is_junk = any(junk in domain for junk in JUNK_DOMAINS)
    name_in_domain = check_domain_name_match(domain, company_name)
    is_homepage = check_homepage(website_url)

    if is_junk: notes.append("Junk domain")
    if not name_in_domain: notes.append("Name not in domain")
    if not is_homepage: notes.append("Likely a subpage")

    correct_website = not is_junk and name_in_domain and is_homepage
    if not correct_website:
        return correct_website, "Unknown", "❌ WRONG", "; ".join(notes)

    # 2. Crawl and perform content checks
    try:
        result = await crawler.arun(url=website_url, bypass_cache=True)
        if not result or not result.markdown:
            return False, "Unknown", "⚠️ UNCLEAR", "Crawl failed or empty content"
        page_text = result.markdown
    except Exception as e:
        return False, "Unknown", "⚠️ UNCLEAR", f"Crawl failed: {str(e)}"

    # 3. Detect Country
    country = detect_country(page_text, company_name)

    # 4. Re-validate with content
    name_found = check_name(page_text, company_name)
    keywords_found, kw_note = check_keywords(page_text, summary)

    if not name_found: notes.append("Name not in content")
    if not keywords_found: notes.append(kw_note)

    if name_found and keywords_found:
        status = "✅ GOOD"
        if not notes: notes.append("All checks passed.")
    else:
        status = "⚠️ UNCLEAR"

    return correct_website, country, status, "; ".join(notes)

async def main():
    print("Starting website re-validation and country detection script.")

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        return

    # Load the enriched data
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")

    # Overwrite or create new columns for validation
    df["Correct_Website"] = pd.NA
    df["Country"] = ""
    df["Validation_Status"] = ""
    df["Validation_Notes"] = ""

    # Filter for the 1451 companies with Website and Summary
    to_process = df[
        (df["Website"].notna()) & (df["Website"] != "") &
        (df.get("Summary", pd.Series(dtype=str)).notna()) & (df.get("Summary", pd.Series(dtype=str)) != "")
    ].copy()

    if to_process.empty:
        print("No companies with both Website and Summary to process.")
        return

    print(f"Found {len(to_process)} companies to re-validate.")

    crawler = AsyncWebCrawler()

    processed_count = 0
    for i, row in to_process.iterrows():
        company = row["Exhibitor"]
        print(f"\n({i+1}/{len(df)}) Re-validating → {company}")

        correct, country, status, notes = await revalidate_and_detect(crawler, row)

        df.loc[i, "Correct_Website"] = correct
        df.loc[i, "Country"] = country
        df.loc[i, "Validation_Status"] = status
        df.loc[i, "Validation_Notes"] = notes
        print(f"   Result: {status} | Country: {country} | Correct: {correct}")

        processed_count += 1
        if processed_count > 0 and processed_count % SAVE_EVERY == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            print(f"   --- Progress saved ({processed_count} processed) ---")

        await asyncio.sleep(DELAY)

    # Final save
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print("\nRe-validation complete. Final file saved.")

    # Print summary
    summary = df["Validation_Status"].value_counts().to_dict()
    print("\n===== VALIDATION SUMMARY =====")
    print(f"✅ GOOD:    {summary.get('✅ GOOD', 0)}")
    print(f"❌ WRONG:   {summary.get('❌ WRONG', 0)}")
    print(f"⚠️ UNCLEAR: {summary.get('⚠️ UNCLEAR', 0)}")
    print("==============================")


if __name__ == "__main__":
    asyncio.run(main())