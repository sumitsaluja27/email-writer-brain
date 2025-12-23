"""
Improved RAG Validation Test Script
- Uses customer patterns from sample_companies.csv
- Classifies companies into 3 valid customer types
- Filters out non-customers (end users, component makers, software-only)
"""

import pandas as pd
import requests
import json
import os

# Config
INPUT_FILE = 'data/Companies/complete_list.csv'
OUTPUT_FILE = 'data/Companies/rag_validation_test_v2.csv'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'deepseek-llm:7b'

# Improved classification prompt with customer patterns
CUSTOMER_PATTERNS = """
## Rapidise Customer Classification

Rapidise is an ODM (Original Design Manufacturer) that manufactures cameras and tracking devices. 
We need to identify companies that could BUY our manufactured products.

### VALID CUSTOMER TYPES (Choose ONE)

**1. dashcam** - Companies that SELL dashcams/fleet cameras
   Examples: Geotab, Lytx, Nexar, CameraMatics, SureCam, Garmin, MiX Telematics
   Industries: Fleet telematics, automotive accessories, consumer electronics
   
**2. body_cam** - Companies that SELL body-worn cameras
   Examples: Axon, Motorola Solutions, Digital Ally
   Industries: Law enforcement, security equipment

**3. ip_camera** - Companies that SELL IP/security cameras
   Examples: Verkada, Vivint, SimpliSafe, Alarm.com, Avigilon, Lorex
   Industries: Smart home security, enterprise security, video surveillance

**4. beacon** - Companies that SELL GPS trackers or use beacons for asset tracking
   Examples: Cold storage providers (USA Cold Storage, VersaCold), fleet tracking
   Industries: Logistics, warehousing, cold chain

**5. in_cabin** - Companies that SELL driver monitoring systems
   Examples: Smart Eye, Seeing Machines
   Industries: Automotive safety, ADAS

**6. fleet_telematics** - Companies that SELL telematics hardware + software
   Examples: Geotab, Fleet Complete, Trakm8, Platform Science
   Industries: Fleet management, logistics

**7. not_relevant** - Company is NOT a potential customer
   - Component manufacturers (LiDAR sensors, chips, semiconductors)
   - Software-only companies (no hardware)
   - End users who USE cameras but don't SELL them (warehouses, banks, YMCA)
   - Service companies (consulting, marketing)
   - Automotive OEMs (Ford, Toyota - too big, not ODM customers)

### DECISION LOGIC

Ask: "Does this company SELL cameras, trackers, or security hardware to their customers?"
- If YES → Choose the most specific category
- If NO → Mark as not_relevant

Ask: "Is this company a brand that needs a manufacturing partner?"
- OEM/Brand owners who sell under their brand → RELEVANT
- Platform companies bundling hardware with software → RELEVANT
- Integrators who resell security systems → RELEVANT
- Component makers, pure software, end users → NOT RELEVANT
"""

def classify_company(company_name, website, industry, linkedin):
    """Use LLM to classify a company based on customer patterns."""
    
    prompt = f"""{CUSTOMER_PATTERNS}

---
COMPANY TO CLASSIFY:
- Name: {company_name}
- Website: {website}
- Industry: {industry}
- LinkedIn: {linkedin}

Based on the company name, industry, and website, classify this company.

Respond in EXACTLY this JSON format (pick ONE category only):
{{"category": "dashcam", "confidence": "high", "reason": "Fleet telematics company that sells dashcams to commercial fleets"}}

Categories: dashcam, body_cam, ip_camera, beacon, in_cabin, fleet_telematics, not_relevant

IMPORTANT: Choose ONLY ONE category. If unsure, choose not_relevant.
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
            # Try to parse JSON from response
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    parsed = json.loads(json_str)
                    # Validate category
                    valid_cats = ['dashcam', 'body_cam', 'ip_camera', 'beacon', 'in_cabin', 'fleet_telematics', 'not_relevant']
                    if parsed.get('category') in valid_cats:
                        return parsed
            except:
                pass
        return {"category": "error", "confidence": "low", "reason": "Failed to parse LLM response"}
    except Exception as e:
        return {"category": "error", "confidence": "low", "reason": str(e)}

def main():
    print("=" * 60)
    print("IMPROVED RAG VALIDATION TEST (v2)")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(INPUT_FILE, encoding='utf-8', on_bad_lines='skip')
    print(f"Total rows in complete_list.csv: {len(df)}")
    
    # Get last 200 rows, then 50 unique companies
    last_rows = df.tail(200)
    unique = last_rows.drop_duplicates(subset=['Company Name'], keep='last').tail(50)
    print(f"Selected {len(unique)} unique companies for validation")
    
    # Prepare output data
    results = []
    
    for idx, row in unique.iterrows():
        company_name = str(row.get('Company Name', ''))
        if company_name == 'nan' or company_name == '':
            continue
            
        website = row.get('Website', '')
        industry = row.get('Industry', '')
        linkedin = row.get('LinkedIn (company)', '')
        revenue = row.get('Revenue', '')
        
        print(f"[{len(results)+1}/50] Classifying: {company_name}")
        
        # Classify using LLM
        classification = classify_company(company_name, website, industry, linkedin)
        
        results.append({
            'Company Name': company_name,
            'Website': website,
            'LinkedIn': linkedin,
            'Industry': industry,
            'Revenue': revenue,
            'Product Category': classification.get('category', 'unknown'),
            'Confidence': classification.get('confidence', 'low'),
            'Why Relevant': classification.get('reason', '')
        })
        
        cat = classification.get('category', 'error')
        conf = classification.get('confidence', 'low')
        print(f"   → {cat} ({conf})")
    
    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    summary = result_df['Product Category'].value_counts()
    print(summary)
    print(f"\nTotal: {len(results)} companies saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
