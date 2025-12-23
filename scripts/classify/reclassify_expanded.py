#!/usr/bin/env python3
"""
Re-classify NOT_RELEVANT companies with expanded Rapidise product criteria.

Rapidise Full Product Range:
1. ADAS - Advanced Driver Assistance Systems
2. DMS - Driver Monitoring System  
3. Dash Camera
4. ECU Development
5. Infotainment system
6. Instrument Cluster
7. Connected Vehicles
8. Vehicle telematics
9. Body Cameras
10. IP Cameras / CCTV
11. Access Control
12. Beacons

Target BUYERS (not just makers):
- Security service companies -> Body cam buyers
- Logistics/Fleet companies -> Dashcam, beacon, telematics buyers
- Automotive OEMs -> Infotainment, ADAS, DMS, instrument cluster buyers
"""

import pandas as pd
import json
import requests
import time

# Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

def call_ollama(prompt, json_mode=True):
    """Call Ollama LLM"""
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json" if json_mode else None
        }, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception as e:
        print(f"Error: {e}")
    return "{}"

def reclassify_company(row):
    """Re-classify a company with expanded criteria"""
    name = row.get('Company Name', '')
    industry = row.get('Industry', '')
    original_reasoning = row.get('Reasoning', '')[:200]
    
    prompt = f"""You are classifying companies for Rapidise, an ODM manufacturer.

RAPIDISE PRODUCTS (they can MAKE or SUPPLY these):
1. ADAS systems (cameras, sensors, lane keeping, collision warning)
2. DMS/In-cabin monitoring (driver fatigue, distraction detection)
3. Dash cameras (fleet, consumer)
4. Infotainment systems (head units, displays, entertainment)
5. Instrument clusters (digital dashboards)
6. ECU development
7. Connected vehicle solutions
8. Vehicle telematics (GPS, fleet tracking)
9. Body cameras (for security guards, police)
10. IP cameras / CCTV
11. Access control systems
12. Beacons (asset tracking, warehouse)

COMPANY TO CLASSIFY:
Name: {name}
Industry: {industry}
Previous analysis: {original_reasoning}

RULES - Mark as RELEVANT if the company:
- MAKES any of the above products (potential partner/competitor)
- BUYS/USES any of the above products (potential customer)
- Is an automotive OEM that needs infotainment, ADAS, DMS, instrument clusters
- Is a fleet/logistics company that needs dashcams, telematics, beacons
- Is a security service company that needs body cameras
- Has vehicles/fleets that need monitoring
- Has warehouses that need beacons/cameras

Mark as NOT_RELEVANT only if:
- Pure software/consulting with no hardware needs
- EV charging infrastructure only
- Basic auto parts (springs, fasteners, tires) with no electronics
- Financial services, pure research, associations

Respond JSON only:
{{"classification": "RELEVANT" or "NOT_RELEVANT", "confidence": 0.0-1.0, "reasoning": "brief reason"}}
"""
    
    result = call_ollama(prompt)
    try:
        parsed = json.loads(result)
        return {
            'classification': parsed.get('classification', 'NOT_RELEVANT'),
            'confidence': parsed.get('confidence', 0.5),
            'reasoning': parsed.get('reasoning', '')
        }
    except:
        return {'classification': 'NOT_RELEVANT', 'confidence': 0.5, 'reasoning': 'Parse error'}

def main():
    # Load current classification
    df = pd.read_csv('data/Companies/sep_nov_rag_classified_v2.csv')
    
    # Get NOT_RELEVANT companies to re-evaluate
    not_relevant = df[df['Classification'] == 'NOT_RELEVANT'].copy()
    
    # Focus on specific industries that might be false negatives
    target_industries = [
        'security',
        'logistics',
        'supply chain',
        'automotive',
        'transportation',
        'fleet',
        'trucking'
    ]
    
    # Filter to companies in target industries
    mask = not_relevant['Industry'].str.lower().apply(
        lambda x: any(t in str(x).lower() for t in target_industries) if pd.notna(x) else False
    )
    to_review = not_relevant[mask]
    
    print(f"Total NOT_RELEVANT: {len(not_relevant)}")
    print(f"To re-evaluate (security/logistics/automotive): {len(to_review)}")
    print("=" * 60)
    
    # Re-classify
    reclassified = []
    changed_to_relevant = 0
    
    for idx, (_, row) in enumerate(to_review.iterrows()):
        name = row['Company Name']
        result = reclassify_company(row)
        
        new_class = result['classification']
        if new_class == 'RELEVANT':
            changed_to_relevant += 1
            print(f"[{idx+1}/{len(to_review)}] {name[:40]}... CHANGED → RELEVANT")
        else:
            print(f"[{idx+1}/{len(to_review)}] {name[:40]}... stays NOT_RELEVANT")
        
        reclassified.append({
            'Company Name': name,
            'Original_Classification': 'NOT_RELEVANT',
            'New_Classification': new_class,
            'Confidence': result['confidence'],
            'Reasoning': result['reasoning'],
            'Industry': row['Industry']
        })
        
        time.sleep(0.5)  # Rate limit
    
    # Save reclassification results
    reclass_df = pd.DataFrame(reclassified)
    reclass_df.to_csv('data/Companies/reclassification_results.csv', index=False)
    
    # Update main dataframe with changed classifications
    changes = reclass_df[reclass_df['New_Classification'] == 'RELEVANT']
    
    for _, change in changes.iterrows():
        mask = df['Company Name'] == change['Company Name']
        df.loc[mask, 'Classification'] = 'RELEVANT'
        df.loc[mask, 'Confidence'] = change['Confidence']
        df.loc[mask, 'Reasoning'] = change['Reasoning']
    
    # Save updated classification
    df.to_csv('data/Companies/sep_nov_rag_classified_v3.csv', index=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Companies re-evaluated: {len(to_review)}")
    print(f"Changed to RELEVANT: {changed_to_relevant}")
    print(f"\nNew totals:")
    print(df['Classification'].value_counts())
    print(f"\nSaved to: data/Companies/sep_nov_rag_classified_v3.csv")
    print(f"Changes log: data/Companies/reclassification_results.csv")

if __name__ == "__main__":
    main()
