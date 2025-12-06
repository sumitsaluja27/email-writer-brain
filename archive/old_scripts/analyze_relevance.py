"""
Company Relevance Analysis Script

This script analyzes enriched company data using a local LLM (llama3.1) to determine
ODM potential and relevance to Rapidise's product offerings.

Input: CES_2026_ENRICHED.csv
Output: Multiple CSVs categorized by relevance score
"""

import os
import sys
import pandas as pd
import json
from typing import Dict, Optional
import ollama
from rapidise_keywords import RAPIDISE_PRODUCT_KEYWORDS, ODM_INDICATORS, NEGATIVE_KEYWORDS

# Configuration
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
INPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES_2026_ENRICHED.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "Companies")

# LLM Configuration
LLM_MODEL = "llama3.1"  # Local Ollama model
LLM_TEMPERATURE = 0.3  # Lower temperature for more consistent analysis


def build_analysis_prompt(company_name: str, company_description: str) -> str:
    """
    Build a structured prompt for LLM analysis.
    
    Args:
        company_name: Name of the company
        company_description: Enriched company description
    
    Returns:
        Formatted prompt string
    """
    
    # Build product descriptions
    product_descriptions = []
    for product, keywords in RAPIDISE_PRODUCT_KEYWORDS.items():
        primary = ", ".join(keywords.get('primary', [])[:3])
        tech = ", ".join(keywords.get('technologies', [])[:5])
        product_descriptions.append(
            f"- {product.upper()}: {primary} | Technologies: {tech}"
        )
    
    products_text = "\n".join(product_descriptions)
    
    prompt = f"""You are analyzing a company for potential ODM (Original Design Manufacturer) partnership with Rapidise.

RAPIDISE PRODUCTS:
{products_text}

COMPANY TO ANALYZE:
Name: {company_name}
Description: {company_description[:3000]}

ANALYSIS REQUIRED:
Please analyze this company and return a JSON response with the following structure:

{{
    "odm_potential": "YES" | "NO" | "MAYBE",
    "relevance_score": <integer from 0-10>,
    "matched_products": [<list of matching Rapidise product categories>],
    "key_indicators": [<list of keywords/signals that suggest relevance>],
    "reasoning": "<one sentence explanation>",
    "concerns": "<any red flags or reasons for caution, or null>"
}}

SCORING GUIDELINES:
- 9-10: Perfect match - manufactures similar hardware, clear ODM potential
- 7-8: Strong match - related industry, likely interested in Rapidise products
- 5-6: Moderate match - some overlap, possible interest
- 3-4: Weak match - tangential relationship
- 0-2: No match - unrelated industry or software-only

IMPORTANT:
- Focus on hardware manufacturers, electronics companies, IoT device makers
- ODM potential means they could manufacture/integrate Rapidise products
- Consider if they make cameras, automotive electronics, security devices, IoT products
- Software-only companies are NOT good ODM candidates
- Return ONLY valid JSON, no additional text

JSON Response:"""
    
    return prompt


def analyze_company_with_llm(company_name: str, company_description: str) -> Optional[Dict]:
    """
    Analyze a company using the local LLM.
    
    Args:
        company_name: Company name
        company_description: Company description/summary
    
    Returns:
        Dictionary with analysis results or None if failed
    """
    if not company_description or pd.isna(company_description):
        return {
            'odm_potential': 'UNKNOWN',
            'relevance_score': 0,
            'matched_products': [],
            'key_indicators': [],
            'reasoning': 'No company description available',
            'concerns': 'Insufficient data'
        }
    
    try:
        # Build prompt
        prompt = build_analysis_prompt(company_name, company_description)
        
        # Query LLM
        response = ollama.generate(
            model=LLM_MODEL,
            prompt=prompt,
            options={
                'temperature': LLM_TEMPERATURE,
                'num_predict': 500  # Limit response length
            }
        )
        
        # Extract response text
        response_text = response['response'].strip()
        
        # Try to parse JSON from response
        # Sometimes LLM adds markdown formatting, so clean it
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        # Parse JSON
        analysis = json.loads(response_text)
        
        # Validate required fields
        required_fields = ['odm_potential', 'relevance_score', 'matched_products', 'reasoning']
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing required field: {field}")
        
        return analysis
    
    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error: {e}")
        print(f"    Response: {response_text[:200]}")
        return {
            'odm_potential': 'ERROR',
            'relevance_score': 0,
            'matched_products': [],
            'key_indicators': [],
            'reasoning': 'LLM response parsing failed',
            'concerns': f'JSON error: {str(e)}'
        }
    
    except Exception as e:
        print(f"    ❌ Analysis error: {e}")
        return {
            'odm_potential': 'ERROR',
            'relevance_score': 0,
            'matched_products': [],
            'key_indicators': [],
            'reasoning': 'Analysis failed',
            'concerns': str(e)
        }


def main():
    print("=" * 80)
    print("COMPANY RELEVANCE ANALYSIS SCRIPT")
    print(f"Using LLM: {LLM_MODEL}")
    print("=" * 80)
    
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print(f"\n❌ ERROR: Input file not found: {INPUT_CSV}")
        print(f"   Please run enrich_with_crawl4ai.py first")
        sys.exit(1)
    
    print(f"\n📂 Loading CSV: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} companies")
    
    # Add analysis columns
    df['ODM_Potential'] = None
    df['Relevance_Score'] = None
    df['Matched_Products'] = None
    df['Key_Indicators'] = None
    df['Reasoning'] = None
    df['Concerns'] = None
    df['Analysis_Status'] = None
    
    print(f"\n🤖 Starting LLM analysis with {LLM_MODEL}...")
    print("-" * 80)
    
    # Process each company
    for idx, row in df.iterrows():
        company_name = row.get('Company Name') or row.get('Exhibitor', f'Company_{idx}')
        
        # Use enriched summary if available, otherwise original
        description = row.get('Scraped_Summary') or row.get('Full_Summary', '')
        
        print(f"\n[{idx + 1}/{len(df)}] Analyzing: {company_name}")
        print(f"  Tier: {row.get('Data_Tier', 'UNKNOWN')}")
        
        # Analyze with LLM
        analysis = analyze_company_with_llm(company_name, description)
        
        if analysis:
            # Update dataframe
            df.at[idx, 'ODM_Potential'] = analysis.get('odm_potential', 'UNKNOWN')
            df.at[idx, 'Relevance_Score'] = analysis.get('relevance_score', 0)
            df.at[idx, 'Matched_Products'] = ', '.join(analysis.get('matched_products', []))
            df.at[idx, 'Key_Indicators'] = ', '.join(analysis.get('key_indicators', []))
            df.at[idx, 'Reasoning'] = analysis.get('reasoning', '')
            df.at[idx, 'Concerns'] = analysis.get('concerns')
            df.at[idx, 'Analysis_Status'] = 'completed'
            
            # Print results
            score = analysis.get('relevance_score', 0)
            odm = analysis.get('odm_potential', 'UNKNOWN')
            products = ', '.join(analysis.get('matched_products', [])[:3])
            
            score_emoji = "🔥" if score >= 7 else "✅" if score >= 5 else "⚠️" if score >= 3 else "❌"
            print(f"  {score_emoji} Score: {score}/10 | ODM: {odm} | Products: {products or 'None'}")
            print(f"  💭 {analysis.get('reasoning', '')}")
        else:
            df.at[idx, 'Analysis_Status'] = 'failed'
            print(f"  ❌ Analysis failed")
        
        # Save progress every 50 companies
        if (idx + 1) % 50 == 0:
            progress_file = os.path.join(OUTPUT_DIR, "CES_2026_ANALYSIS_PROGRESS.csv")
            df.to_csv(progress_file, index=False)
            print(f"\n💾 Progress saved ({idx + 1}/{len(df)} companies)")
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Summary statistics
    completed = df[df['Analysis_Status'] == 'completed']
    print(f"\n✅ Successfully analyzed: {len(completed)}/{len(df)} companies")
    
    if len(completed) > 0:
        print("\n📊 Score Distribution:")
        high_rel = len(completed[completed['Relevance_Score'] >= 7])
        med_rel = len(completed[(completed['Relevance_Score'] >= 4) & (completed['Relevance_Score'] < 7)])
        low_rel = len(completed[completed['Relevance_Score'] < 4])
        
        print(f"  HIGH (7-10)   : {high_rel:5} ({high_rel/len(completed)*100:5.1f}%)")
        print(f"  MEDIUM (4-6)  : {med_rel:5} ({med_rel/len(completed)*100:5.1f}%)")
        print(f"  LOW (0-3)     : {low_rel:5} ({low_rel/len(completed)*100:5.1f}%)")
        
        print("\n🎯 ODM Potential:")
        odm_counts = completed['ODM_Potential'].value_counts()
        for odm_status, count in odm_counts.items():
            percentage = (count / len(completed) * 100)
            print(f"  {odm_status:10} : {count:5} ({percentage:5.1f}%)")
    
    # Export categorized CSVs
    print("\n📁 Exporting categorized results...")
    
    # High relevance (score >= 7)
    high_df = df[df['Relevance_Score'] >= 7].sort_values('Relevance_Score', ascending=False)
    if len(high_df) > 0:
        high_file = os.path.join(OUTPUT_DIR, "CES_2026_HIGH_RELEVANCE.csv")
        high_df.to_csv(high_file, index=False)
        print(f"  🔥 HIGH RELEVANCE: {len(high_df)} companies → {os.path.basename(high_file)}")
    
    # Medium relevance (score 4-6)
    medium_df = df[(df['Relevance_Score'] >= 4) & (df['Relevance_Score'] < 7)].sort_values('Relevance_Score', ascending=False)
    if len(medium_df) > 0:
        medium_file = os.path.join(OUTPUT_DIR, "CES_2026_MEDIUM_RELEVANCE.csv")
        medium_df.to_csv(medium_file, index=False)
        print(f"  ✅ MEDIUM RELEVANCE: {len(medium_df)} companies → {os.path.basename(medium_file)}")
    
    # All scored companies
    all_file = os.path.join(OUTPUT_DIR, "CES_2026_ALL_SCORED.csv")
    df.to_csv(all_file, index=False)
    print(f"  📊 ALL COMPANIES: {len(df)} companies → {os.path.basename(all_file)}")
    
    # Missing/failed data
    missing_df = df[df['Analysis_Status'] != 'completed']
    if len(missing_df) > 0:
        missing_file = os.path.join(OUTPUT_DIR, "CES_2026_NEEDS_REVIEW.csv")
        missing_df.to_csv(missing_file, index=False)
        print(f"  ⚠️  NEEDS REVIEW: {len(missing_df)} companies → {os.path.basename(missing_file)}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    
    # Print top 10 companies
    if len(high_df) > 0:
        print("\n🏆 TOP 10 MOST RELEVANT COMPANIES:")
        print("-" * 80)
        top_10 = high_df.head(10)
        for idx, row in top_10.iterrows():
            name = row.get('Company Name') or row.get('Exhibitor', 'Unknown')
            score = row.get('Relevance_Score', 0)
            products = row.get('Matched_Products', 'None')
            print(f"  {score}/10 | {name}")
            print(f"         Products: {products}")
            print(f"         {row.get('Reasoning', '')}")
            print()


if __name__ == "__main__":
    main()
