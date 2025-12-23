"""
Finalize Company Analysis CSV - Phase 1 Lock
Creates company_analysis_v02.csv with:
1. Normalized columns (Company Type, Language Style)
2. New columns for execution
"""

import pandas as pd
import requests
import json
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1:8b'


def normalize_company_type(val):
    """Normalize Company Type to OEM/ODM or END_USER only."""
    val = str(val).upper()
    if 'END_USER' in val or 'END USER' in val:
        return 'END_USER'
    else:
        return 'OEM/ODM'


def normalize_language_style(val):
    """Normalize Language Style to Technical, Operational, or Executive."""
    val = str(val).lower()
    if 'technical' in val:
        return 'Technical'
    elif 'executive' in val:
        return 'Executive'
    else:
        return 'Operational'


def derive_new_fields(row):
    """Use LLM to derive new fields from existing columns. NO inventing - use only existing data."""
    
    problems = str(row.get('Problems Explicit', ''))[:500]
    outcomes = str(row.get('Outcomes Promised', ''))[:500]
    buyer_persona = str(row.get('Buyer Persona', ''))[:300]
    trust_signals = str(row.get('Trust Signals', ''))[:300]
    products = str(row.get('Products Mentioned', ''))[:300]
    company_type = str(row.get('Company Type', ''))
    
    prompt = f"""Based ONLY on the provided data, determine the following fields for this company.
DO NOT invent anything. Use ONLY the existing information.

COMPANY DATA:
- Company Type: {company_type}
- Problems: {problems}
- Outcomes: {outcomes}
- Buyer Persona: {buyer_persona}
- Trust Signals: {trust_signals}
- Products: {products}

DETERMINE:

1. PES_EMS_FIT - What service would this company need from an ODM?
   Options: "PES" (Product Engineering Services - design focus), "EMS" (Electronics Manufacturing Services - build focus), "ODM (Both)" (design + manufacturing)
   
2. PRIMARY_NARRATIVE - What is their core need?
   Options: "Build" (manufacturing only), "Design" (design/engineering only), "Design + Build" (full product development)

3. IDEAL_CONTENT_DAY - Best day for reaching this buyer persona?
   Options: "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
   (Use: Technical personas prefer mid-week, Executive prefer Mon/Fri, Operational prefer Tue-Thu)

4. SDR_OWNER - Who should own this lead?
   Options: "Rohit" (technical/engineering leads), "Khushi" (operations/business leads), "Both" (mixed)

5. MARKETING_ANGLE - Short phrase (2-4 words) capturing their main pain point.
   Extract from Problems/Outcomes. NO sentences.

6. EMAIL_ANGLE - Short phrase (2-4 words) for email outreach hook.
   Extract from Problems/Outcomes. NO sentences.

Reply JSON ONLY:
{{
  "pes_ems_fit": "...",
  "primary_narrative": "...",
  "ideal_content_day": "...",
  "sdr_owner": "...",
  "marketing_angle": "...",
  "email_angle": "..."
}}
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0.1}
        }, timeout=180)
        
        if response.status_code == 200:
            result = response.json()['response']
            try:
                return json.loads(result)
            except:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(result[start:end])
    except Exception as e:
        print(f"  Error: {e}")
    
    return None


def main():
    print("=" * 60)
    print("FINALIZING CSV - PHASE 1 LOCK")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load existing CSV
    df = pd.read_csv('data/company_analysis.csv')
    print(f"Loaded: {len(df)} companies")
    
    # 1. Normalize Company Type
    df['Company Type'] = df['Company Type'].apply(normalize_company_type)
    print(f"Company Type normalized: {df['Company Type'].value_counts().to_dict()}")
    
    # 2. Normalize Language Style
    df['Language Style'] = df['Language Style'].apply(normalize_language_style)
    print(f"Language Style normalized: {df['Language Style'].value_counts().to_dict()}")
    
    # 3. Add new columns
    new_columns = {
        'PES_EMS_FIT': [],
        'Primary Narrative': [],
        'Ideal Content Day': [],
        'SDR Owner': [],
        'Marketing Angle': [],
        'Email Angle': []
    }
    
    print("\nDeriving new fields from existing data...")
    
    for idx, row in df.iterrows():
        company = row['Company Name']
        print(f"[{idx+1}/{len(df)}] {company[:30]}...", end=" ", flush=True)
        
        fields = derive_new_fields(row)
        
        if fields:
            new_columns['PES_EMS_FIT'].append(fields.get('pes_ems_fit', 'ODM (Both)'))
            new_columns['Primary Narrative'].append(fields.get('primary_narrative', 'Design + Build'))
            new_columns['Ideal Content Day'].append(fields.get('ideal_content_day', 'Wednesday'))
            new_columns['SDR Owner'].append(fields.get('sdr_owner', 'Both'))
            new_columns['Marketing Angle'].append(fields.get('marketing_angle', '')[:30])
            new_columns['Email Angle'].append(fields.get('email_angle', '')[:30])
            print("✓")
        else:
            new_columns['PES_EMS_FIT'].append('ODM (Both)')
            new_columns['Primary Narrative'].append('Design + Build')
            new_columns['Ideal Content Day'].append('Wednesday')
            new_columns['SDR Owner'].append('Both')
            new_columns['Marketing Angle'].append('')
            new_columns['Email Angle'].append('')
            print("✗ (defaults)")
    
    # Add new columns to dataframe
    for col, values in new_columns.items():
        df[col] = values
    
    # Reorder columns for better readability
    cols_order = [
        'Company Name',
        'Company Type',
        'Product Category',
        'Primary Role',
        'PES_EMS_FIT',
        'Primary Narrative',
        'Language Style',
        'Buyer Persona',
        'Products Mentioned',
        'Problems Explicit',
        'Outcomes Promised',
        'Trust Signals',
        'Top Keywords',
        'Marketing Angle',
        'Email Angle',
        'Ideal Content Day',
        'SDR Owner',
        'Folder Type',
        'Your Assessment'
    ]
    
    # Only include columns that exist
    final_cols = [c for c in cols_order if c in df.columns]
    df = df[final_cols]
    
    # Save as v0.2
    output_path = 'data/company_analysis_v02.csv'
    df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 60)
    print("PHASE 1 LOCK COMPLETE")
    print("=" * 60)
    print(f"Output: {output_path}")
    print(f"Total: {len(df)} companies")
    print(f"\nCompany Type distribution:")
    print(df['Company Type'].value_counts())
    print(f"\nPES_EMS_FIT distribution:")
    print(df['PES_EMS_FIT'].value_counts())
    print(f"\nPrimary Narrative distribution:")
    print(df['Primary Narrative'].value_counts())


if __name__ == "__main__":
    main()
