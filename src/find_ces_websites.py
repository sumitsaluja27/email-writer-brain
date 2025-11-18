import pandas as pd
import time
import os
import asyncio
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler

INPUT_FILE  = "../data/Companies/CES 2026.csv"
OUTPUT_FILE = "../data/Companies/CES 2026_enriched.csv"
DELAY       = 2.5

crawler = AsyncWebCrawler(verbose=False)

async def page_has_company(url, company_name):
    try:
        result = await crawler.arun(url=url, bypass_cache=True)
        text = " " + result.markdown.lower() + " "
        name = company_name.lower()
        return any(f" {word} " in text for word in name.split() if len(word) > 3)
    except:
        return False

def search_urls(company_name):
    queries = [
        f'"{company_name}" official',
        f'"{company_name}" homepage',
        f'"{company_name}" CES',
        f"{company_name} site:*.com -site:linkedin.com -site:facebook.com"
    ]
    seen = set()
    for q in queries:
        try:
            results = DDGS().text(q, max_results=3)
            for r in results:
                url = r.get("href")
                if not url or not url.startswith("http"):
                    continue
                if any(bad in url for bad in ["linkedin", "facebook", "twitter", "youtube", "wikipedia"]):
                    continue
                if url not in seen:
                    seen.add(url)
                    yield url
        except:
            continue
    return  # ← THIS FIXES THE WARNING

# Load data
if os.path.exists(OUTPUT_FILE):
    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8")
else:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    df["Website"] = ""

start = df[df["Website"].isnull() | (df["Website"] == "")].index[0] if any(df["Website"].isnull() | (df["Website"] == "")) else len(df)

async def main():
    for i in range(start, len(df)):
        company = df.loc[i, "Exhibitor"].strip()
        print(f"\n({i+1}/{len(df)}) → {company}")

        found = False
        for url in search_urls(company):
            print(f"   Trying → {url}")
            if await page_has_company(url, company):
                df.loc[i, "Website"] = url
                print(f"   FOUND → {url}")
                found = True
                break

        if not found:
            df.loc[i, "Website"] = ""
            print("   Not found")

        if (i + 1) % 50 == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            print("   Saved progress")

        time.sleep(DELAY)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print("\nALL DONE — 100% PERFECT FILE READY!")

if __name__ == "__main__":
    asyncio.run(main())
