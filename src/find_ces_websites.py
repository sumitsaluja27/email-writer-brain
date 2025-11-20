import pandas as pd
import time
import os
from ddgs import DDGS
from crawl4ai import WebCrawler
from ollama import Client

# ───── SETTINGS ─────
CES_FILE    = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_enriched.csv"
DELAY       = 3.0
SAVE_EVERY  = 50

ollama = Client()
crawler = WebCrawler()
crawler.warmup()  # one-time prep

# ───── SUPER SMART SEARCH ─────
def smart_search(company_name):
    query = f'"{company_name}" CES 2026 exhibitor official website intitle:"{company_name}" -inurl:(linkedin twitter facebook youtube crunchbase ces.tech/profile)'
    try:
        results = DDGS().text(query, max_results=5)
        for r in results:
            url = r.get("href")
            if url and url.startswith("http") and "ces.tech" not in url:
                yield url
    except Exception as e:
        print(f"  Error in smart_search for {company_name}: {e}")

# ───── LLAVA CHECK WITH CLEAN TEXT + CONTEXT ─────
def is_real_website(url, company_name):
    try:
        result = crawler.run(url=url, bypass_cache=True)
        clean_text = result.markdown[:7000]  # clean readable text
        
        prompt = f"""Company: {company_name}
This company makes dashcams / AI cameras and is exhibiting at CES 2026.

Website content:
{clean_text}

Question: Is this the official website of the company above?
Answer only Yes or No."""

        answer = ollama.generate(
            model="llava:7b",
            prompt=prompt,
            options={"num_predict": 10, "temperature": 0}
        )
        return "yes" in answer["response"].strip().lower()
    except Exception as e:
        print(f"  Error processing {url}: {e}")
        return False

# ───── MAIN LOOP (very easy to read) ─────
# Load data
if os.path.exists(CES_FILE):
    df = pd.read_csv(CES_FILE, encoding="utf-8")
else:
    print(f"Error: The file {CES_FILE} was not found.")
    exit()

# Add 'Website' and 'Country' columns if they don't exist
if "Website" not in df.columns:
    df["Website"] = ""
if "Country" not in df.columns:
    df["Country"] = ""

# Process companies
for i in range(len(df)):
    # Check if the website is already filled
    if pd.notna(df.loc[i, 'Website']) and df.loc[i, 'Website'] != '':
        continue

    company = df.loc[i, "Exhibitor"].strip()
    print(f"\n({i+1}/{len(df)}) → {company}")

    found = False
    for url in smart_search(company):
        print(f"   Checking → {url}")
        if is_real_website(url, company):
            df.loc[i, "Website"] = url
            print(f"   FOUND → {url}")
            found = True
            break

    if not found:
        df.loc[i, "Website"] = ""
        print("   Not found")

    # Auto-save
    if (i + 1) % SAVE_EVERY == 0:
        df.to_csv(CES_FILE, index=False, encoding="utf-8")
        print("   Progress saved")

    time.sleep(DELAY)

# Final save
df.to_csv(CES_FILE, index=False, encoding="utf-8")
print("\nAll finished! Your perfect CSV is ready")
