#!/usr/bin/env python3
"""
Filter GOLD companies using strict criteria based on labeled training data.
Uses patterns identified in LABELED_COMPANY_ANALYSIS.md
"""
import pandas as pd
import re

# Load the analysis results
INPUT_FILE = 'data/Companies/CES_2026_ANALYSIS_PROGRESS.csv'
OUTPUT_FILE = 'data/Companies/GOLD_COMPANIES_FILTERED.csv'

# Negative keywords to exclude (based on labeled data analysis)
NEGATIVE_KEYWORDS = [
    # Consumer electronics (NOT security cameras)
    'television', 'tv', 'led bulb', 'lighting solution', 'lamp', 'appliance',
    'refrigerator', 'washing machine', 'microwave', 'oven',
    
    # Physical security without electronics
    'padlock', 'physical lock', 'door hardware', 'fence', 'barrier',
    
    # General automotive without cameras
    'tire', 'wheel', 'brake', 'engine', 'transmission', 'fuel',
    
    # General electronics
    'smartphone', 'tablet', 'laptop', 'desktop computer', 'printer',
    
    # Software only
    'software development', 'cloud services', 'consulting firm',
    
    # Unrelated
    'furniture', 'clothing', 'food', 'beverage', 'restaurant'
]

# Required keywords per product
REQUIRED_KEYWORDS = {
    'DASHCAM': [
        'dashcam', 'dash cam', 'fleet', 'telematics', 'vehicle camera',
        'driver monitoring', 'in-cabin', 'in cabin', 'fleet management',
        'commercial vehicle', 'video telematics'
    ],
    'IN_CABIN': [
        'in-cabin', 'in cabin', 'driver monitoring', 'driver safety',
        'fleet', 'telematics', 'adas', 'driver attention', 'drowsiness'
    ],
    'IP_CAMERA': [
        'ip camera', 'surveillance', 'video surveillance', 'cctv',
        'security camera', 'network camera', 'video security',
        'security system'
    ],
    'BODY_CAM': [
        'body cam', 'body camera', 'body-worn', 'bodycam',
        'wearable camera', 'police', 'law enforcement', 'security guard',
        'public safety'
    ],
    'ACCESS_CONTROL': [
        'access control', 'door access', 'card reader', 'biometric',
        'security system', 'smart lock', 'electronic lock', 'entry system'
    ],
    'BEACON': [
        'beacon', 'ble beacon', 'bluetooth beacon', 'asset tracking',
        'warehouse', 'cold storage', 'inventory tracking', 'rfid'
    ]
}

def has_negative_keyword(text):
    """Check if text contains any negative keywords"""
    if pd.isna(text):
        return False
    text_lower = str(text).lower()
    return any(keyword in text_lower for keyword in NEGATIVE_KEYWORDS)

def validate_product_match(matched_products, reasoning):
    """Validate if matched products are supported by reasoning"""
    if pd.isna(matched_products) or pd.isna(reasoning):
        return False, []
    
    matched_list = str(matched_products).split(',')
    reasoning_lower = str(reasoning).lower()
    
    validated_products = []
    
    for product in matched_list:
        product = product.strip()
        if product in REQUIRED_KEYWORDS:
            # Check if ANY required keyword is in reasoning
            if any(keyword in reasoning_lower for keyword in REQUIRED_KEYWORDS[product]):
                validated_products.append(product)
    
    return len(validated_products) > 0, validated_products

def main():
    print("="*80)
    print("FILTERING GOLD COMPANIES - STRICT CRITERIA")
    print("="*80)
    
    # Load data
    print(f"\nLoading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"Total companies in analysis: {len(df)}")
    
    # Initial filter: Score >= 9 and ODM_Potential = YES
    gold_initial = df[(df['Relevance_Score'] >= 9) & (df['ODM_Potential'] == 'YES')].copy()
    print(f"\nInitial GOLD candidates (Score 9-10, ODM=YES): {len(gold_initial)}")
    
    # Apply negative keyword filter
    print("\nApplying negative keyword filter...")
    gold_initial['Has_Negative'] = gold_initial['Reasoning'].apply(has_negative_keyword)
    gold_filtered = gold_initial[~gold_initial['Has_Negative']].copy()
    print(f"After negative keyword filter: {len(gold_filtered)} (removed {len(gold_initial) - len(gold_filtered)})")
    
    # Validate product matches
    print("\nValidating product matches...")
    validation_results = gold_filtered.apply(
        lambda row: validate_product_match(row['Matched_Products'], row['Reasoning']),
        axis=1
    )
    
    gold_filtered['Product_Validated'] = validation_results.apply(lambda x: x[0])
    gold_filtered['Validated_Products'] = validation_results.apply(lambda x: ', '.join(x[1]))
    
    gold_final = gold_filtered[gold_filtered['Product_Validated']].copy()
    print(f"After product validation: {len(gold_final)} (removed {len(gold_filtered) - len(gold_final)})")
    
    # Sort by score
    gold_final = gold_final.sort_values('Relevance_Score', ascending=False)
    
    # Select useful columns
    output_columns = [
        'Company Name', 'Exhibitor', 'Website', 'LinkedIn URL',
        'Relevance_Score', 'ODM_Potential', 'Validated_Products',
        'Reasoning', 'Data_Tier', 'Website_Verified'
    ]
    
    # Keep only columns that exist
    output_columns = [col for col in output_columns if col in gold_final.columns]
    gold_output = gold_final[output_columns]
    
    # Save
    gold_output.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Final GOLD companies: {len(gold_output)}")
    print(f"Output saved to: {OUTPUT_FILE}")
    
    # Summary by product
    print("\nBreakdown by Product:")
    for product in REQUIRED_KEYWORDS.keys():
        count = gold_output['Validated_Products'].str.contains(product, na=False).sum()
        if count > 0:
            print(f"  {product}: {count} companies")
    
    print("="*80)
    
    # Show sample companies
    print("\nSample GOLD Companies:")
    for idx, row in gold_output.head(10).iterrows():
        name = row.get('Company Name') or row.get('Exhibitor', 'Unknown')
        score = row['Relevance_Score']
        products = row['Validated_Products']
        print(f"  • {name} (Score: {score}) - {products}")

if __name__ == "__main__":
    main()
