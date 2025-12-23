"""
ENHANCED Smart Classification with Human Review Tier
- RELEVANT: High confidence matches
- NEEDS_REVIEW: Uncertain but promising (security/public safety industries)
- NOT_RELEVANT: Clearly not a fit

FIXES:
1. More keywords covering all Rapidise products
2. Deeper web scraping (tries product/about pages)
3. Better LLM prompt with specific product categories
4. Resume logic to continue where stopped
"""

import pandas as pd
import requests
import json
from datetime import datetime
import csv
import os

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1:8b'
JINA_API = 'https://r.jina.ai/'

# Industries that ALWAYS need human review (expanded)
REVIEW_INDUSTRIES = [
    'public safety', 'security', 'electrical/electronic manufacturing',
    'defense', 'law enforcement', 'surveillance', 'fire safety',
    'automotive', 'transportation', 'logistics', 'fleet', 'trucking',
    'insurance', 'iot', 'smart home', 'construction', 'mining',
    'oil & gas', 'energy', 'utilities', 'government', 'military'
]

# Keywords in company name/description that suggest relevance (FROM NOTEBOOKLM - FILTERED)
RELEVANT_KEYWORDS = [
    # === CAMERAS ===
    'camera', 'video', 'cctv', 'surveillance', 'ip camera', 'ptz', 'dome camera',
    'bullet camera', 'imaging', 'low light camera', 'in-cabin camera',
    'rear seat entertainment', 'surveillance ai',
    
    # === DASHCAM/BODYCAM ===
    'dashcam', 'dash cam', 'bodycam', 'body cam', 'lte bodycam', 'ai bodycam',
    'dual dashcam', 'oem fit dashcam', 'wearable camera', 'action cam',
    
    # === RECORDING/VMS ===
    'dvr', 'nvr', 'vms', 'video management', 'recorder', 'recording',
    'cloud vms', 'webrtc', 'streaming',
    
    # === SECURITY AI ===
    'security', 'alarm', 'intrusion', 'intrusion detection', 'access control',
    'biometric', 'facial recognition', 'face recognition', 'gun detection',
    'violence detection', 'fire detection', 'smoke detection', 'loitering',
    'license plate', 'anpr', 'lpr', 'perimeter', 'motion detection',
    
    # === ADAS (Advanced Driver Assistance) ===
    'adas', 'forward collision', 'collision warning', 'lane departure',
    'blind spot', 'pedestrian detection', 'tailgating', 'traffic sign',
    'crash detection', 'predictive crash',
    
    # === DMS (Driver Monitoring) ===
    'dms', 'driver monitoring', 'drowsiness', 'distraction detection',
    'yawn detection', 'eye blink', 'mobile phone usage', 'seat belt detection',
    'fatigue', 'driver behavior', 'occupancy detection',
    
    # === TELEMATICS/FLEET ===
    'telematics', 'fleet', 'fleet management', 'gps', 'tracker', 'tracking',
    'vehicle tracking', 'asset tracker', 'fuel monitoring', 'vehicle telemetry',
    'fota', 'eld', 'electronic logging',
    
    # === ACCESS CONTROL ===
    'smart lock', 'smart gateway', 'multi-tenant access', 'smart mailbox',
    'smart switch', 'card reader', 'door access',
    
    # === IOT/SENSORS ===
    'sensor', 'iot', 'ble beacon', 'beacon', 'presence detection', 'hpd',
    'radar', 'person detection', 'edge ai', 'iot gateway',
    
    # === AUTOMOTIVE HMI ===
    'digital cockpit', 'head-up display', 'hud', 'instrument cluster',
    'industrial hmi', 'infotainment',
    
    # === COMPETITOR BRANDS (companies they might resell/integrate) ===
    'hikvision', 'dahua', 'axis', 'pelco', 'bosch security', 'honeywell security',
    'genetec', 'milestone', 'avigilon', 'geovision', 'mobotix', 'vivotek',
    'hanwha', 'uniview', 'verkada', 'rhombus', 'samsara', 'verizon connect',
    'geotab', 'motive', 'lytx', 'smartwitness'
]

def scrape_website(url, try_subpages=True):
    """Scrape website - tries homepage + products/about if available."""
    if not url or str(url) == 'nan' or pd.isna(url):
        return ""
    
    all_text = ""
    
    try:
        if not str(url).startswith('http'):
            url = 'https://' + str(url)
        
        # Get homepage
        response = requests.get(JINA_API + url, timeout=30, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            all_text = response.text[:2500]
        
        # Try to get products page (common URLs)
        if try_subpages and len(all_text) < 1500:  # If homepage sparse, try more
            for subpage in ['/products', '/solutions', '/about', '/about-us']:
                try:
                    sub_url = url.rstrip('/') + subpage
                    resp = requests.get(JINA_API + sub_url, timeout=15, headers={'Accept': 'text/plain'})
                    if resp.status_code == 200 and len(resp.text) > 500:
                        all_text += "\n\n=== PRODUCTS/ABOUT ===\n" + resp.text[:1500]
                        break  # Got extra data, stop trying
                except:
                    pass
    except:
        pass
    
    return all_text[:4000]  # Increased to 4000 chars

def quick_keyword_check(text):
    """Check if any relevant keywords exist in text."""
    text_lower = text.lower()
    found = [kw for kw in RELEVANT_KEYWORDS if kw in text_lower]
    return list(set(found))[:10]  # Dedupe, max 10

def industry_needs_review(industry):
    """Check if industry warrants human review."""
    if not industry or str(industry) == 'nan':
        return False
    industry_lower = str(industry).lower()
    return any(ri in industry_lower for ri in REVIEW_INDUSTRIES)

def classify_smart(company_name, website, industry, description):
    """Smart classification with 3 tiers."""
    
    # Pre-check: Industry-based flagging
    needs_review_industry = industry_needs_review(industry)
    
    # Pre-check: Keyword-based flagging
    combined_text = f"{company_name} {description}"
    keywords_found = quick_keyword_check(combined_text)
    
    # Build the prompt based on context
    if keywords_found or needs_review_industry:
        # Use detailed prompt for promising companies
        prompt = f"""You are classifying companies for Rapidise - an ODM manufacturer that makes:

HARDWARE PRODUCTS:
- Dashcams (vehicle cameras for fleets, trucks, cars)
- IP Cameras (CCTV, surveillance, PTZ, dome, bullet)
- Body Cameras (for security guards, police)
- GPS Trackers (vehicle tracking devices)
- Access Control devices (biometric, card readers)

SOFTWARE/CLOUD:
- Video Management Systems (VMS, NVR software)
- Telematics platforms (fleet tracking dashboards)
- AI/ADAS solutions (collision detection, driver monitoring)

=== COMPANY TO CLASSIFY ===
Company: {company_name}
Industry: {industry}
Keywords detected: {keywords_found}
Website content: {description[:600] if description else 'N/A'}

=== CLASSIFICATION RULES ===
RELEVANT (they could buy from Rapidise):
- Sells/resells cameras, dashcams, security systems
- Provides video surveillance, CCTV solutions
- Fleet management companies needing dashcams
- Security integrators, alarm companies
- Insurance companies with telematics programs

NEEDS_REVIEW (uncertain, human should verify):
- In security industry but unclear if they need hardware
- Automotive but unclear about camera/telematics needs
- Construction/mining that might need surveillance

NOT_RELEVANT (clearly no fit):
- Pure software companies (no hardware needs)
- Consumer retail (selling to end consumers)
- Food, entertainment, healthcare (unrelated)
- Car manufacturers (OEMs) - they don't buy from ODMs

If in doubt, choose NEEDS_REVIEW. Only say NOT_RELEVANT if 100% certain.

Reply JSON ONLY:
{{"category": "RELEVANT", "confidence": "high/medium/low", "reason": "one sentence"}}
"""
    else:
        # Quick check for clearly irrelevant industries
        prompt = f"""Quick classification for camera/security ODM:

Company: {company_name}
Industry: {industry}
Website: {description[:400] if description else 'N/A'}

If clearly software/retail/food/entertainment/healthcare → NOT_RELEVANT
If automotive/security/fleet but unclear → NEEDS_REVIEW  
If clearly sells cameras/security/telematics → RELEVANT

JSON ONLY: {{"category": "RELEVANT/NEEDS_REVIEW/NOT_RELEVANT", "reason": "brief"}}
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL, 'prompt': prompt, 'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=180)
        if response.status_code == 200:
            result = response.json()['response']
            start, end = result.find('{'), result.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(result[start:end])
                # OVERRIDE: If keywords found but LLM said NOT_RELEVANT, force NEEDS_REVIEW
                if keywords_found and parsed.get('category') == 'NOT_RELEVANT':
                    parsed['category'] = 'NEEDS_REVIEW'
                    parsed['reason'] = f"Keywords found: {keywords_found}. Forcing review."
                return parsed
    except Exception as e:
        print(f"  Error: {e}")
    
    return {"category": "NEEDS_REVIEW", "confidence": "low", "reason": "parse error - needs review"}

def main():
    print("=" * 60)
    print("ENHANCED SMART CLASSIFICATION WITH HUMAN REVIEW TIER")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    # Load Sep-Nov companies
    input_file = 'data/Companies/sep_nov.csv'
    output_file = 'data/Companies/sep_nov_smart_classified.csv'
    
    df = pd.read_csv(input_file)
    print(f"Total: {len(df)} companies")
    
    # --- RESUME LOGIC ---
    processed_names = set()
    existing_results = []
    
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_csv(output_file)
            existing_results = existing_df.to_dict('records')
            processed_names = set(existing_df['Company Name'].str.strip().str.lower())
            print(f"Resuming: {len(processed_names)} already processed")
        except:
            print("Starting fresh")
    
    results = existing_results.copy()
    
    for idx, row in df.iterrows():
        name = str(row.get('Company Name', '')).strip()
        
        # Skip if already processed
        if name.lower() in processed_names:
            continue
            
        website = str(row.get('Website', ''))
        industry = str(row.get('Industry', ''))
        
        print(f"[{len(results)+1}/{len(df)}] {name[:35]}...", end=" ")
        
        desc = scrape_website(website)
        result = classify_smart(name, website, industry, desc)
        cat = result.get('category', 'NEEDS_REVIEW')
        print(f"→ {cat}")
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'Category': cat,
            'Confidence': result.get('confidence', ''),
            'Reason': result.get('reason', '')[:150]
        })
        
        processed_names.add(name.lower())
        
        # Save every 10 companies
        if len(results) % 10 == 0:
            pd.DataFrame(results).to_csv(output_file, index=False)
    
    pd.DataFrame(results).to_csv(output_file, index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    result_df = pd.DataFrame(results)
    print(result_df['Category'].value_counts())
    print("=" * 60)

if __name__ == "__main__":
    main()
