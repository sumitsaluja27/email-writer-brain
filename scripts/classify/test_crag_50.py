"""
Test CRAG Classification on 50 companies from sep_nov.csv
"""

import pandas as pd
from datetime import datetime
import sys
sys.path.append('scripts/classify')
from crag_classify import classify_company_crag

def main():
    print("=" * 60)
    print("CRAG CLASSIFICATION - 50 COMPANY TEST")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load first 50 from sep_nov
    df = pd.read_csv('data/Companies/sep_nov.csv')
    test_df = df.head(50)
    
    print(f"Testing {len(test_df)} companies\n")
    
    results = []
    for idx, row in test_df.iterrows():
        name = str(row.get('Company Name', '')).strip()
        website = str(row.get('Website', ''))
        industry = str(row.get('Industry', ''))
        
        print(f"[{idx+1}/50] {name[:35]}...", end=" ", flush=True)
        
        result = classify_company_crag(name, website, industry)
        cat = result.get('classification', 'NEEDS_REVIEW')
        print(f"→ {cat}")
        
        results.append({
            'Company Name': name,
            'Website': website,
            'Industry': industry,
            'Classification': cat,
            'Type': result.get('company_type', ''),
            'Reasoning': result.get('reasoning', '')[:100],
            'Steps': ' > '.join(result.get('steps', []))
        })
    
    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_csv('data/Companies/crag_test_50.csv', index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(result_df['Classification'].value_counts())
    print("\nTypes:")
    print(result_df['Type'].value_counts())
    print(f"\nResults saved to: data/Companies/crag_test_50.csv")

if __name__ == "__main__":
    main()
