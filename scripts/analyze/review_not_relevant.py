#!/usr/bin/env python3
"""Review NOT_RELEVANT classifications for potential false negatives"""
import pandas as pd

# Load the classified data
df = pd.read_csv('data/Companies/sep_nov_rag_classified_v2.csv')

# Get NOT_RELEVANT companies
not_relevant = df[df['Classification'] == 'NOT_RELEVANT'].copy()

# Define keywords that suggest a company might actually be RELEVANT
camera_keywords = ['camera', 'video', 'surveillance', 'cctv', 'dvr', 'nvr', 'vision', 'imaging', 'security', 'monitor', 'recording']
telematics_keywords = ['telematics', 'fleet', 'dashcam', 'dash cam', 'gps', 'tracking', 'connected car']
access_keywords = ['access control', 'intercom', 'door', 'smart lock', 'entry']

# Find potentially misclassified companies
potential_false_negatives = []

for _, row in not_relevant.iterrows():
    name = str(row.get('Company Name', '')).lower()
    industry = str(row.get('Industry', '')).lower()
    reasoning = str(row.get('Reasoning', '')).lower()
    
    # Check if company name or industry contains relevant keywords
    is_suspicious = False
    match_reason = []
    
    for kw in camera_keywords:
        if kw in name or kw in industry:
            is_suspicious = True
            match_reason.append(f"'{kw}' in name/industry")
    
    # Check some specific companies known to be in security/camera industry
    suspicious_names = ['gentex', 'motorola', 'synectics', 'tkh', 'paxton', 'assa abloy', 
                       'almas', 'cdvi', 'baumer', 'abax', 'fleets', 'avigilon', 'dahua',
                       'hikvision', 'axis', 'hanwha', 'vivotek', 'intellimali', 'flir',
                       'lorex', 'swann', 'ring', 'nest', 'arlo', 'reolink']
    
    for susp in suspicious_names:
        if susp in name:
            is_suspicious = True
            match_reason.append(f"known brand '{susp}'")
    
    if is_suspicious:
        potential_false_negatives.append({
            'Company Name': row.get('Company Name'),
            'Industry': row.get('Industry'),
            'Reasoning': row.get('Reasoning')[:100] if pd.notna(row.get('Reasoning')) else '',
            'Match_Reason': '; '.join(match_reason)
        })

# Also check by industry - security companies
security_companies = not_relevant[not_relevant['Industry'].str.contains('security', case=False, na=False)]
for _, row in security_companies.iterrows():
    if row['Company Name'] not in [x['Company Name'] for x in potential_false_negatives]:
        potential_false_negatives.append({
            'Company Name': row.get('Company Name'),
            'Industry': row.get('Industry'),
            'Reasoning': row.get('Reasoning')[:100] if pd.notna(row.get('Reasoning')) else '',
            'Match_Reason': 'security industry'
        })

# Print results
print("=" * 80)
print("POTENTIAL FALSE NEGATIVES (companies that might actually be RELEVANT)")
print("=" * 80)
print(f"\nFound {len(potential_false_negatives)} potentially misclassified companies:\n")

for i, comp in enumerate(potential_false_negatives, 1):
    print(f"{i}. {comp['Company Name']}")
    print(f"   Industry: {comp['Industry']}")
    print(f"   Match: {comp['Match_Reason']}")
    print(f"   Reasoning: {comp['Reasoning']}...")
    print()

# Save to CSV for review
review_df = pd.DataFrame(potential_false_negatives)
review_df.to_csv('data/Companies/potential_false_negatives.csv', index=False)
print(f"\nSaved to: data/Companies/potential_false_negatives.csv")

# Summary by category
print("\n" + "=" * 80)
print("SUMMARY OF NOT_RELEVANT BY INDUSTRY")
print("=" * 80)
industry_counts = not_relevant['Industry'].value_counts().head(20)
print(industry_counts)
