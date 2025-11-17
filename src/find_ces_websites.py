import pandas as pd
import time
import os
from ddgs import DDGS
from urllib.parse import urlparse
from ollama import Client   # This talks to your local Llava

# ───── CONFIG ─────
INPUT_FILE   = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026.csv"
OUTPUT_FILE  = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_enriched.csv"
SEARCH_DELAY = 3.0
SAVE_EVERY   = 50

ollama = Client()   # connects to your local Ollama (llava:7b)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def llava_check_website(url, company_name):
    """Asks your local Llava: Is this the real website of <company>?"""
    try:
        prompt = f"Webpage URL: {url}\nQuestion: Is this the official website of the company named exactly '{company_name}'? Answer only Yes or No."
        response = ollama.generate(model='llava:7b', prompt=prompt, options={'num_predict': 10})
        answer = response['response'].strip().lower()
        return 'yes' in answer
    except Exception as e:
        print(f"  Llava error: {e}")
        return False

def find_company_website(company_name):
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
            if llava_check_website(url, company_name):
                return url
        return None
    except Exception as e:
        print(f"  Search error: {e}")
        return None

# ───── MAIN ─────
df = pd.read_csv(INPUT_FILE, encoding='utf-8') if not os.path.exists(OUTPUT_FILE) else pd.read_csv(OUTPUT_FILE, encoding='utf-8')
if 'Website' not in df.columns:
    df['Website'] = ''

start = df[df['Website'].isnull() | (df['Website'] == '')].index[0] if any(df['Website'].isnull() | (df['Website'] == '')) else len(df)

for i in range(start, len(df)):
    company = df.loc[i, 'Exhibitor']
    print(f"\n({i+1}/{len(df)}) Working on → {company}")
    
    website = find_company_website(company)
    df.loc[i, 'Website'] = website or ''
    print(f"    Result → {website or 'Not found'}")
    
    if (i+1) % SAVE_EVERY == 0:
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print("    Saved progress")
    
    time.sleep(SEARCH_DELAY)

df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print("\nAll done! Final file saved.")