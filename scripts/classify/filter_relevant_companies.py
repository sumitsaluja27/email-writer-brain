"""
Keyword-Based Company Filter
- Filters companies by PRODUCT keywords (not components)
- Outputs companies relevant to Rapidise's ODM business
"""

import pandas as pd
import re

# Config
INPUT_FILE = 'data/Companies/unique_companies_list.csv'
OUTPUT_FILE = 'data/Companies/relevant_companies.csv'

# Product keywords (what Rapidise's customers SELL)
PRODUCT_KEYWORDS = {
    'dashcam': [
        'dashcam', 'dash cam', 'dash camera', 'car camera', 'driving recorder',
        'vehicle recorder', 'car dvr', 'automotive camera', 'fleet camera'
    ],
    'body_cam': [
        'body camera', 'body cam', 'bodycam', 'body-worn camera', 'bwc',
        'police camera', 'wearable camera', 'law enforcement camera'
    ],
    'ip_camera': [
        'ip camera', 'cctv', 'surveillance camera', 'security camera',
        'network camera', 'ptz camera', 'video surveillance', 'nvr', 
        'video monitoring'
    ],
    'beacon': [
        'beacon', 'ble tracker', 'gps tracker', 'asset tracker', 'fleet tracker',
        'location tracker', 'tracking device', 'vehicle tracker', 'telematics'
    ],
    'in_cabin': [
        'driver monitoring', 'dms', 'occupant monitoring', 'in-cabin camera',
        'cabin camera', 'fatigue detection', 'drowsiness detection',
        'driver safety', 'adas camera'
    ]
}

# Exclusion keywords (component-only or irrelevant companies)
EXCLUSION_KEYWORDS = [
    'semiconductor', 'chip manufacturer', 'fpga', 'soc provider',
    'healthcare', 'pharma', 'medical device', 'drug',
    'speech recognition', 'audio transcription', 'voice assistant',
    'saas platform', 'cloud analytics', 'data analytics',
    'marketing agency', 'consulting firm'
]

def classify_company(description):
    """Classify a company based on keywords in description."""
    if pd.isna(description) or description == '':
        return None, []
    
    desc_lower = str(description).lower()
    
    # Check exclusions first
    for excl in EXCLUSION_KEYWORDS:
        if excl in desc_lower:
            return None, []
    
    # Check product keywords
    matched_products = []
    for product, keywords in PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                matched_products.append(product)
                break  # Found match for this product category
    
    if matched_products:
        return matched_products[0], matched_products  # Primary product, all matches
    
    return None, []

def main():
    print("=" * 60)
    print("KEYWORD-BASED COMPANY FILTER")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(INPUT_FILE)
    print(f"Total companies: {len(df)}")
    
    # Classify each company
    results = []
    product_counts = {p: 0 for p in PRODUCT_KEYWORDS.keys()}
    
    for idx, row in df.iterrows():
        primary_product, all_products = classify_company(row.get('Description', ''))
        
        if primary_product:
            results.append({
                'Company Name': row['Company Name'],
                'Website': row.get('Website', ''),
                'LinkedIn': row.get('LinkedIn', ''),
                'Industry': row.get('Industry', ''),
                'Product Category': primary_product,
                'All Matches': ', '.join(all_products),
                'Description': row.get('Description', '')[:300]  # Truncate
            })
            product_counts[primary_product] += 1
    
    # Create output DataFrame
    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    
    print(f"\nRelevant companies found: {len(results)}")
    print("\nBy product category:")
    for product, count in product_counts.items():
        print(f"  {product}: {count}")
    
    print(f"\nSaved to: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
