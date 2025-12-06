#!/usr/bin/env python3
"""
Tier 1: Filter complete_list.csv by relevant industries only
"""
import pandas as pd

# Relevant industries (based on your labeled sample companies)
RELEVANT_INDUSTRIES = [
    'security & investigations',
    'automotive',
    'electrical/electronic manufacturing',
    'information technology & services',
    'semiconductors',
    'machinery',
    'medical devices',
    'consumer electronics',
    'logistics & supply chain',
    'telecommunications',
    'computer hardware',
    'warehousing'  # For beacon
]

def main():
    print("="*80)
    print("TIER 1: INDUSTRY FILTERING")
    print("="*80)
    
    # Load complete list
    print("\nLoading complete_list.csv...")
    df = pd.read_csv('data/Companies/complete_list.csv')
    print(f"Total rows (contacts): {len(df)}")
    
    # Get unique companies
    print("\nExtracting unique companies...")
    companies_df = df.groupby('Company Name').agg({
        'Website': 'first',
        'LinkedIn (company)': 'first',
        'Industry': 'first',
        'Country': 'first',
        'Revenue': 'first',
        'Employee strenght': 'first'
    }).reset_index()
    
    print(f"Unique companies: {len(companies_df)}")
    
    # Filter by industry
    print("\n" + "="*80)
    print("FILTERING BY INDUSTRY")
    print("="*80)
    print(f"\nRelevant industries ({len(RELEVANT_INDUSTRIES)}):")
    for industry in RELEVANT_INDUSTRIES:
        print(f"  • {industry}")
    
    companies_df['industry_lower'] = companies_df['Industry'].str.lower()
    filtered_df = companies_df[companies_df['industry_lower'].isin(RELEVANT_INDUSTRIES)].copy()
    filtered_df = filtered_df.drop('industry_lower', axis=1)
    
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Relevant companies: {len(filtered_df)} (from {len(companies_df)} total)")
    print(f"Filtered out: {len(companies_df) - len(filtered_df)}")
    
    # Industry breakdown
    print(f"\nBreakdown by Industry:")
    industry_counts = filtered_df['Industry'].value_counts()
    for industry, count in industry_counts.items():
        print(f"  {count:4d} - {industry}")
    
    # Save
    output_file = 'data/Companies/COMPLETE_LIST_INDUSTRY_FILTERED.csv'
    filtered_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
