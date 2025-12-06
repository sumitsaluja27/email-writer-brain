#!/usr/bin/env python3
"""
Find missing websites using DuckDuckGo search and update enriched CSV files in-place.
"""
import pandas as pd
from duckduckgo_search import DDGS
import time
import sys

def search_company_website(company_name, industry=None):
    """Search for company website using DuckDuckGo"""
    try:
        # Create search query
        query = f"{company_name}"
        if industry and pd.notna(industry):
            query += f" {industry}"
        query += " official website"
        
        # Search
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
            if results:
                # Return first result URL
                return results[0].get('href', None)
    
    except Exception as e:
        print(f"    Error searching: {str(e)[:50]}")
        return None
    
    return None

def find_missing_websites(csv_file):
    """Find and update missing websites in CSV file"""
    print("="*80)
    print(f"PROCESSING: {csv_file}")
    print("="*80)
    
    df = pd.read_csv(csv_file)
    print(f"Total companies: {len(df)}")
    
    # Find companies without websites
    missing_website = df['Website'].isna() | (df['Website'] == '')
    missing_count = missing_website.sum()
    
    print(f"Companies without website: {missing_count}")
    
    if missing_count == 0:
        print("✅ All companies have websites!")
        return 0
    
    print(f"\nSearching for {missing_count} missing websites...\n")
    
    found_count = 0
    
    for idx in df[missing_website].index:
        company_name = df.at[idx, 'Company Name'] if pd.notna(df.at[idx, 'Company Name']) else df.at[idx, 'Exhibitor']
        industry = df.at[idx, 'Industry'] if 'Industry' in df.columns else None
        
        print(f"[{idx+1}/{len(df)}] Searching: {company_name}")
        
        website = search_company_website(company_name, industry)
        
        if website:
            df.at[idx, 'Website'] = website
            print(f"  ✅ Found: {website}")
            found_count += 1
            
            # Save progress after each find
            df.to_csv(csv_file, index=False)
        else:
            print(f"  ❌ Not found")
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"RESULTS: Found {found_count}/{missing_count} websites")
    print(f"Updated: {csv_file}")
    print(f"{'='*80}\n")
    
    return found_count

if __name__ == "__main__":
    enriched_files = [
        'data/Companies/CES_2026_BODY_CAM_ENRICHED.csv',
        'data/Companies/CES_2026_DASHCAM_ENRICHED.csv',
        'data/Companies/CES_2026_BEACON_ENRICHED.csv',
        'data/Companies/CES_2026_IP_CAMERA_ENRICHED.csv',
        'data/Companies/CES_2026_IN_CABIN_ENRICHED.csv'
    ]
    
    total_found = 0
    total_missing = 0
    
    for file in enriched_files:
        found = find_missing_websites(file)
        total_found += found
    
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total websites found: {total_found}")
    print("All files updated in-place!")
