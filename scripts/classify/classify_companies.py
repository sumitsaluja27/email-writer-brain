"""
Company Classification Script
- Uses customer profiles to classify companies
- Runs in background, saves progress
- Resumable
"""

import pandas as pd
import requests
import json
import time
import os
from datetime import datetime

# Config
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'deepseek-llm:7b'

# Customer profiles summary for LLM prompt
CUSTOMER_PROFILES = """
## Rapidise Customer Classification

Rapidise is an ODM manufacturer of cameras and tracking devices. Classify companies as potential customers.

### CATEGORIES (Choose ONE):

**1. dashcam** - ODM Customer
Companies that SELL dashcams/fleet cameras to trucking, logistics, delivery.
Website patterns: "fleet management", "telematics", "dash cam", "video telematics"
Examples: Geotab, Lytx, Nexar, CameraMatics, SureCam, Fleet Complete

**2. ip_camera** - ODM Customer
Companies that SELL IP cameras/security cameras to consumers or enterprises.
Website patterns: "security camera", "surveillance", "smart home security"
Examples: Verkada, SimpliSafe, Vivint, Alarm.com, Rhombus

**3. bodycam** - ODM Customer
Companies that SELL body-worn cameras to law enforcement, security.
Website patterns: "body camera", "body worn", "public safety devices"
Examples: Axon, HALO Body Cameras, Reveal Media

**4. in_cabin** - ODM Customer
Companies that SELL driver monitoring systems (DMS) for vehicles.
Website patterns: "driver monitoring", "fatigue detection", "in-cabin"
Examples: Smart Eye, Seeing Machines

**5. access_control** - ODM Customer
Companies that SELL access control devices (readers, controllers, cameras).
Website patterns: "access control", "door controllers", "card readers"
Examples: Acre Security, Rhombus, Verkada

**6. beacon** - End User (Buyer)
Companies that USE beacons/trackers for cold storage, logistics.
Website patterns: "cold storage", "warehousing", "logistics", "asset tracking"
Examples: USA Cold Storage, VersaCold

**7. bodycam_enduser** - End User (Buyer)
Police departments and security companies that BUY body cameras.
Website patterns: "police department", "security services", "law enforcement"
Examples: Edmonton Police, G4S

**8. not_relevant** - Not a Customer
- Component manufacturers (chips, sensors, LiDAR)
- Software-only companies
- Automotive OEMs (too big)
- General consulting, marketing, banks

### DECISION RULES:
1. If company SELLS cameras/trackers → Choose specific category
2. If company USES cameras but doesn't sell → beacon or bodycam_enduser
3. If unsure → not_relevant
"""

def classify_company(company_name, website, industry, description=""):
    """Use LLM to classify company."""
    
    prompt = f"""{CUSTOMER_PROFILES}

COMPANY TO CLASSIFY:
- Name: {company_name}
- Website: {website}
- Industry: {industry}
- Description: {description[:500] if description else 'N/A'}

Based on the above, classify this company. Respond ONLY with JSON:
{{"category": "dashcam", "confidence": "high", "reason": "Fleet telematics company selling dashcams"}}

Choose ONE category. If unsure, use "not_relevant".
"""

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=120)
        
        if response.status_code == 200:
            result = response.json()['response']
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = result[start:end]
                parsed = json.loads(json_str)
                valid_cats = ['dashcam', 'ip_camera', 'bodycam', 'in_cabin', 'access_control', 
                              'beacon', 'bodycam_enduser', 'not_relevant']
                if parsed.get('category') in valid_cats:
                    return parsed
        return {"category": "error", "confidence": "low", "reason": "Parse error"}
    except Exception as e:
        return {"category": "error", "confidence": "low", "reason": str(e)[:50]}

def process_file(input_file, output_file, name_col='Company Name', website_col='Website', 
                 industry_col='Industry', desc_col=None):
    """Process a CSV file and classify companies."""
    
    print(f"\n{'='*60}")
    print(f"Processing: {input_file}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")
    
    # Load input
    df = pd.read_csv(input_file, encoding='utf-8', on_bad_lines='skip')
    print(f"Total rows: {len(df)}")
    
    # Get unique companies
    if name_col in df.columns:
        unique = df.drop_duplicates(subset=[name_col], keep='first')
    else:
        unique = df
    print(f"Unique companies: {len(unique)}")
    
    # Check for existing progress
    if os.path.exists(output_file):
        existing = pd.read_csv(output_file)
        processed_names = set(existing[name_col].tolist())
        print(f"Already processed: {len(processed_names)}")
    else:
        existing = pd.DataFrame()
        processed_names = set()
    
    # Process new companies
    results = existing.to_dict('records') if len(existing) > 0 else []
    
    count = 0
    for idx, row in unique.iterrows():
        company_name = str(row.get(name_col, ''))
        if company_name == 'nan' or company_name == '' or company_name in processed_names:
            continue
        
        website = str(row.get(website_col, ''))
        industry = str(row.get(industry_col, ''))
        description = str(row.get(desc_col, '')) if desc_col and desc_col in row else ''
        
        count += 1
        print(f"[{count}/{len(unique) - len(processed_names)}] {company_name[:40]}", end=' ')
        
        # Classify
        result = classify_company(company_name, website, industry, description)
        
        results.append({
            name_col: company_name,
            website_col: website,
            industry_col: industry,
            'Category': result.get('category', 'error'),
            'Confidence': result.get('confidence', 'low'),
            'Reason': result.get('reason', '')
        })
        
        print(f"→ {result.get('category')}")
        
        # Save progress every 10 companies
        if count % 10 == 0:
            pd.DataFrame(results).to_csv(output_file, index=False)
            print(f"  [Saved progress: {len(results)} companies]")
    
    # Final save
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_file, index=False)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    if 'Category' in result_df.columns:
        print(result_df['Category'].value_counts())
    print(f"\nTotal saved: {len(result_df)} companies")
    
    return result_df

def main():
    print("="*60)
    print("COMPANY CLASSIFICATION - STARTED")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Process complete_list.csv first
    process_file(
        input_file='data/Companies/complete_list.csv',
        output_file='data/Companies/complete_list_CLASSIFIED.csv',
        name_col='Company Name',
        website_col='Website',
        industry_col='Industry'
    )
    
    # Then CES file - use Full_Summary or Summary for context
    process_file(
        input_file='data/Companies/CES_2026_ENRICHED.csv',
        output_file='data/Companies/CES_2026_CLASSIFIED.csv',
        name_col='Company Name',
        website_col='Website',
        industry_col='Industry',
        desc_col='Full_Summary'  # Use summary for companies without good website
    )
    
    print("\n" + "="*60)
    print("ALL DONE!")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
