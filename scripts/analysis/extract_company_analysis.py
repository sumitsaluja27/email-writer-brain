"""
Analyze company profiles and extract structured data into CSV.
CRITICAL: Preserve exact phrases from website, minimal interpretation.

Fields to extract:
1. Company Type: OEM / ODM / End User
2. Primary Role in Value Chain (platform, manufacturer, operator, reseller)
3. Products Mentioned (raw words, no interpretation)
4. Problems They Explicitly Talk About (exact phrases)
5. Outcomes They Promise (exact phrases)
6. Buyer Persona Signals (roles, industries, scale)
7. Trust Signals (deployment scale, years, awards, geography)
8. Language Style (technical / operational / executive)
9. Keywords Used Repeatedly (top 10)
"""

import os
import pandas as pd
import requests
import json
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1:8b'


def extract_analysis(company_name, content, your_assessment):
    """Use LLM to extract structured analysis from company profile."""
    
    prompt = f"""Analyze this company's website content and extract the following fields.
CRITICAL: Use EXACT PHRASES from the text where specified. Do not interpret or paraphrase.

COMPANY: {company_name}
YOUR NOTES: {your_assessment}

WEBSITE CONTENT:
{content[:6000]}

Extract the following fields. Use EXACT QUOTES from the website where marked.

1. COMPANY_TYPE: Is this company an OEM (makes own products), ODM (makes for other brands), or END_USER (buys/uses cameras)?
   Answer: OEM / ODM / END_USER

2. PRIMARY_ROLE: What is their role in the value chain?
   Answer: platform / manufacturer / operator / reseller / integrator / service_provider

3. PRODUCTS_MENTIONED: List the products/devices they mention. Use EXACT words from website.
   Answer: (comma-separated list, raw words only)

4. PROBLEMS_EXPLICIT: What problems do they explicitly talk about? Use EXACT phrases from website.
   Answer: (comma-separated exact quotes from website)

5. OUTCOMES_PROMISED: What outcomes/benefits do they promise? Use EXACT phrases from website.
   Answer: (comma-separated exact quotes from website)

6. BUYER_PERSONA: Who are their target customers? Mention roles, industries, scale.
   Answer: (describe based on content)

7. TRUST_SIGNALS: Any deployment scale, years in business, awards, certifications, geography?
   Answer: (extract exact mentions)

8. LANGUAGE_STYLE: How do they communicate?
   Answer: technical / operational / executive / marketing

9. TOP_KEYWORDS: What words/phrases appear repeatedly? List top 10.
   Answer: (comma-separated list)

Respond in JSON format ONLY:
{{
  "company_type": "...",
  "primary_role": "...",
  "products_mentioned": "...",
  "problems_explicit": "...",
  "outcomes_promised": "...",
  "buyer_persona": "...",
  "trust_signals": "...",
  "language_style": "...",
  "top_keywords": "..."
}}
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0.1}
        }, timeout=300)
        
        if response.status_code == 200:
            result = response.json()['response']
            # Parse JSON
            try:
                parsed = json.loads(result)
                return parsed
            except:
                # Try to extract JSON from response
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(result[start:end])
    except Exception as e:
        print(f"  LLM error: {e}")
    
    return None


def main():
    print("=" * 60)
    print("EXTRACTING COMPANY ANALYSIS TO CSV")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    results = []
    
    # Process ODM customers
    odm_dir = 'data/company_profiles_raw/odm_customers'
    end_user_dir = 'data/company_profiles_raw/end_users'
    
    all_files = []
    for f in os.listdir(odm_dir):
        if f.endswith('.txt'):
            all_files.append((os.path.join(odm_dir, f), 'odm_customer'))
    for f in os.listdir(end_user_dir):
        if f.endswith('.txt'):
            all_files.append((os.path.join(end_user_dir, f), 'end_user'))
    
    print(f"Total profiles: {len(all_files)}")
    print()
    
    for idx, (filepath, folder_type) in enumerate(all_files):
        # Read profile
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract company name and assessment from header
        lines = content.split('\n')
        company_name = ""
        your_assessment = ""
        product_category = ""
        
        for line in lines[:15]:
            if line.startswith('COMPANY:'):
                company_name = line.replace('COMPANY:', '').strip()
            if line.startswith('YOUR ASSESSMENT:'):
                your_assessment = line.replace('YOUR ASSESSMENT:', '').strip()
            if line.startswith('PRODUCT CATEGORY:'):
                product_category = line.replace('PRODUCT CATEGORY:', '').strip()
        
        print(f"[{idx+1}/{len(all_files)}] {company_name[:35]}...", end=" ", flush=True)
        
        # Extract analysis using LLM
        analysis = extract_analysis(company_name, content, your_assessment)
        
        if analysis:
            results.append({
                'Company Name': company_name,
                'Folder Type': folder_type,
                'Product Category': product_category,
                'Your Assessment': your_assessment,
                'Company Type': analysis.get('company_type', ''),
                'Primary Role': analysis.get('primary_role', ''),
                'Products Mentioned': analysis.get('products_mentioned', ''),
                'Problems Explicit': analysis.get('problems_explicit', ''),
                'Outcomes Promised': analysis.get('outcomes_promised', ''),
                'Buyer Persona': analysis.get('buyer_persona', ''),
                'Trust Signals': analysis.get('trust_signals', ''),
                'Language Style': analysis.get('language_style', ''),
                'Top Keywords': analysis.get('top_keywords', '')
            })
            print("✓")
        else:
            print("✗")
    
    # Save to CSV
    df = pd.DataFrame(results)
    output_path = 'data/company_analysis.csv'
    df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total analyzed: {len(results)}")
    print(f"\nSaved to: {output_path}")
    
    # Show breakdown
    print("\nCompany Type breakdown:")
    print(df['Company Type'].value_counts())


if __name__ == "__main__":
    main()
