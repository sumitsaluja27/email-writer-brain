import pandas as pd
import time
import os
from ddgs import DDGS
from urllib.parse import urlparse
from ollama import Client

# ───── SETTINGS ─────
INPUT_FILE  = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_enriched.csv"
DELAY       = 3.0
SAVE_EVERY  = 50

ollama = Client()   # talks to your always-running Ollama

# ───── HELPERS ─────
def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and parsed.netloc
    except ValueError:
        return False

def llava_says_yes(url, company_name):
    try:
        prompt = f"Webpage: {url}\nQuestion: Is this the official website of '{company_name}'? Answer only Yes or No."
        answer = ollama.generate(model='llava:7b', prompt=prompt, options={'num_predict': 10})
        return "yes" in answer['response'].strip().lower()
    except Exception as e:
        print(f"    Llava had a problem: {e}")
        return False

def find_real_website(company_name):
    query = f'"{company_name}" CES 2026 official site -inurl:(linkedin twitter facebook youtube crunchbase)'
    try:
        results = DDGS().text(query, max_results=5)
        for r in results:
            url = r.get('href')
            if not url or not is_valid_url(url):
                continue
            if any(bad in url for bad in ['linkedin', 'twitter', 'facebook', 'youtube', 'crunchbase', 'ces.tech/profile']):
                continue

            print(f"    Checking → {url}")
            if llava_says_yes(url, company_name):
                return url
        return None
    except Exception as e:
        print(f"    Search problem: {e}")
        return None

# ───── MAIN PART (very easy to read now) ─────
# Load file
if os.path.exists(OUTPUT_FILE):
    df = pd.read_csv(OUTPUT_FILE, encoding='utf-8')
else:
    df = pd.read_csv(INPUT_FILE, encoding='utf-8')
    df['Website'] = ''

# Find where to start
start_index = 0
if 'Website' in df.columns:
    empty_rows = df[df['Website'].isnull() | (df['Website'] == '')]
    if len(empty_rows) > 0:
        start_index = empty_rows.index[0]
        print(f"Resuming from row {start_index} → {df.loc[start_index, 'Exhibitor']}")
    else:
        print("Everything already done!")
        exit()

# Do the work
for i in range(start_index, len(df)):
    company = df.loc[i, 'Exhibitor']
    print(f"\n({i+1}/{len(df)}) → {company}")

    website = find_real_website(company)
    df.loc[i, 'Website'] = website or ''
    print(f"    → {website or 'Not found'}")

    if (i + 1) % SAVE_EVERY == 0:
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print("    Progress saved")

    time.sleep(DELAY)

# Final save
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print("\nAll finished! Your file is ready")