#!/usr/bin/env python3
"""Extract GOLD companies (score 9-10) for immediate outreach"""
import pandas as pd

df = pd.read_csv('data/Companies/CES_2026_ANALYSIS_PROGRESS.csv')

# Filter for score 9-10
gold = df[df['Relevance_Score'] >= 9].copy()

# Select key columns
columns = ['Company Name', 'Exhibitor', 'Website', 'LinkedIn URL', 
           'Relevance_Score', 'Matched_Products', 'ODM_Potential', 
           'Reasoning', 'Data_Tier']

gold = gold[columns].drop_duplicates()
gold = gold.sort_values('Relevance_Score', ascending=False)

# Save
gold.to_csv('data/Companies/GOLD_COMPANIES_Score9Plus.csv', index=False)
print(f'✅ Created GOLD file with {len(gold)} companies (Score 9-10)')
print(f'📁 Location: data/Companies/GOLD_COMPANIES_Score9Plus.csv')
