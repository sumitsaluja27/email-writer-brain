"""
Company Categorization Script

This script categorizes CES 2026 companies into 5 data availability tiers:
1. GOLD: Summary + Website + LinkedIn (richest data)
2. SILVER: Website + LinkedIn 
3. BRONZE_WEB: Website only
4. BRONZE_LI: LinkedIn only
5. COPPER: Summary only

It also validates URLs and attempts to find missing websites using DuckDuckGo search.

Output: CES_2026_CATEGORIZED.csv with data tier classification
"""

import os
import sys
import pandas as pd
import requests
from urllib.parse import urlparse
from duckduckgo_search import DDGS
import time
from typing import Optional, Tuple

# Configuration
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
INPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES 2026_non_asian_validated_CLEAN.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES_2026_CATEGORIZED.csv")

# URL validation timeout (seconds)
URL_TIMEOUT = 5


def validate_url(url: str) -> bool:
    """
    Check if a URL is valid and accessible.
    
    Args:
        url: URL to validate
    
    Returns:
        True if URL is accessible, False otherwise
    """
    if not url or pd.isna(url) or url.strip() == "":
        return False
    
    # Clean up URL
    url = url.strip()
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Try to validate URL format
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        
        # Try to access URL with a quick HEAD request
        response = requests.head(url, timeout=URL_TIMEOUT, allow_redirects=True)
        return response.status_code < 400
    
    except Exception as e:
        # If HEAD fails, try GET
        try:
            response = requests.get(url, timeout=URL_TIMEOUT, allow_redirects=True)
            return response.status_code < 400
        except:
            return False


def search_company_website(company_name: str) -> Optional[str]:
    """
    Use DuckDuckGo to search for a company's website.
    
    Args:
        company_name: Name of the company
    
    Returns:
        Website URL if found, None otherwise
    """
    if not company_name or pd.isna(company_name):
        return None
    
    try:
        # Search using DuckDuckGo
        ddgs = DDGS()
        query = f"{company_name} official website"
        results = ddgs.text(query, max_results=3)
        
        if results and len(results) > 0:
            # Return the first result's link
            potential_url = results[0].get('href') or results[0].get('link')
            
            # Validate the found URL
            if potential_url and validate_url(potential_url):
                return potential_url
        
        return None
    
    except Exception as e:
        print(f"  Error searching for {company_name}: {e}")
        return None


def categorize_company(row: pd.Series) -> Tuple[str, dict]:
    """
    Categorize a company based on available data fields.
    
    Args:
        row: DataFrame row containing company data
    
    Returns:
        Tuple of (tier_name, validation_info_dict)
    """
    # Check what data is available
    has_summary = bool(row.get('Full_Summary') and not pd.isna(row.get('Full_Summary')) and str(row.get('Full_Summary')).strip())
    has_website = bool(row.get('Website') and not pd.isna(row.get('Website')) and str(row.get('Website')).strip())
    has_linkedin = bool(row.get('LinkedIn URL') and not pd.isna(row.get('LinkedIn URL')) and str(row.get('LinkedIn URL')).strip())
    
    # Validation info
    validation_info = {
        'website_valid': False,
        'linkedin_valid': False,
        'website_found': False
    }
    
    # Validate URLs if present
    if has_website:
        validation_info['website_valid'] = validate_url(row.get('Website'))
        has_website = validation_info['website_valid']
    
    if has_linkedin:
        validation_info['linkedin_valid'] = validate_url(row.get('LinkedIn URL'))
        has_linkedin = validation_info['linkedin_valid']
    
    # Determine tier
    if has_summary and has_website and has_linkedin:
        tier = "GOLD"
    elif has_website and has_linkedin:
        tier = "SILVER"
    elif has_website:
        tier = "BRONZE_WEB"
    elif has_linkedin:
        tier = "BRONZE_LI"
    elif has_summary:
        tier = "COPPER"
    else:
        tier = "INSUFFICIENT"
    
    return tier, validation_info


def main():
    print("=" * 80)
    print("COMPANY CATEGORIZATION SCRIPT")
    print("=" * 80)
    
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print(f"\n❌ ERROR: Input file not found: {INPUT_CSV}")
        sys.exit(1)
    
    print(f"\n📂 Loading CSV: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} companies")
    
    # Add new columns
    df['Data_Tier'] = None
    df['Website_Valid'] = False
    df['LinkedIn_Valid'] = False
    df['Website_Found_By_Search'] = None
    df['Processing_Notes'] = None
    
    print("\n🔍 Categorizing companies...")
    print("-" * 80)
    
    tier_counts = {
        "GOLD": 0,
        "SILVER": 0,
        "BRONZE_WEB": 0,
        "BRONZE_LI": 0,
        "COPPER": 0,
        "INSUFFICIENT": 0
    }
    
    # Process each company
    for idx, row in df.iterrows():
        company_name = row.get('Company Name') or row.get('Exhibitor') or f"Company_{idx}"
        
        # Categorize
        tier, validation_info = categorize_company(row)
        
        # Update dataframe
        df.at[idx, 'Data_Tier'] = tier
        df.at[idx, 'Website_Valid'] = validation_info['website_valid']
        df.at[idx, 'LinkedIn_Valid'] = validation_info['linkedin_valid']
        
        tier_counts[tier] += 1
        
        # If company has INSUFFICIENT data, try to find website
        if tier == "INSUFFICIENT" and company_name:
            print(f"  🔎 Searching for website: {company_name}...")
            found_url = search_company_website(company_name)
            
            if found_url:
                df.at[idx, 'Website_Found_By_Search'] = found_url
                df.at[idx, 'Processing_Notes'] = "Website found via DuckDuckGo search"
                print(f"    ✅ Found: {found_url}")
                
                # Re-categorize with found website
                row['Website'] = found_url
                tier, validation_info = categorize_company(row)
                df.at[idx, 'Data_Tier'] = tier
                df.at[idx, 'Website_Valid'] = True
                tier_counts["INSUFFICIENT"] -= 1
                tier_counts[tier] += 1
            else:
                df.at[idx, 'Processing_Notes'] = "No website found via search"
                print(f"    ❌ No website found")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        # Progress indicator every 100 companies
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(df)} companies...")
    
    print("\n" + "=" * 80)
    print("CATEGORIZATION SUMMARY")
    print("=" * 80)
    
    for tier, count in tier_counts.items():
        percentage = (count / len(df) * 100) if len(df) > 0 else 0
        print(f"  {tier:15} : {count:5} ({percentage:5.1f}%)")
    
    print(f"\n  TOTAL: {len(df)}")
    
    # Save output
    print(f"\n💾 Saving categorized data to: {OUTPUT_CSV}")
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print("✅ File saved successfully!")
    
    # Export tier-specific CSVs for easier processing
    print("\n📊 Exporting tier-specific CSVs...")
    for tier in ["GOLD", "SILVER", "BRONZE_WEB", "BRONZE_LI", "COPPER"]:
        tier_df = df[df['Data_Tier'] == tier]
        if len(tier_df) > 0:
            tier_file = os.path.join(BASE_DIR, "data", "Companies", f"CES_2026_{tier}.csv")
            tier_df.to_csv(tier_file, index=False)
            print(f"  ✅ {tier}: {len(tier_df)} companies → {os.path.basename(tier_file)}")
    
    print("\n" + "=" * 80)
    print("✅ CATEGORIZATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
