"""
Rapidise Company Classification Pipeline - Enricher
====================================================

Consolidated company enrichment functionality.
Combines: enrich_companies.py, find_missing_websites.py

Handles:
- Adding missing data (websites, LinkedIn, country)
- Enriching with scraped content
- Adding classification results
"""

import pandas as pd
import requests
from datetime import datetime
import json

try:
    from .scraper import smart_scrape, scrape_company_deep
    from .classifier import classify_by_keywords
except ImportError:
    pass


# =============================================================================
# WEBSITE FINDING
# =============================================================================

def find_website_for_company(company_name, industry=""):
    """
    Try to find a company's website using search.
    
    Note: This is a basic implementation. 
    For production, use a proper search API.
    """
    # Clean company name
    search_query = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
    
    # Common domain patterns
    domain_guesses = [
        f"https://www.{search_query}.com",
        f"https://{search_query}.com",
        f"https://www.{search_query}.io",
        f"https://{search_query}.io",
    ]
    
    for domain in domain_guesses:
        try:
            response = requests.head(domain, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return domain
        except:
            continue
    
    return ""


def enrich_missing_websites(df, company_col='Company Name', website_col='Website'):
    """Add missing websites to dataframe."""
    print("Enriching missing websites...")
    
    missing = df[df[website_col].isna() | (df[website_col] == '')]
    print(f"  Companies without websites: {len(missing)}")
    
    found = 0
    for idx in missing.index:
        company = df.at[idx, company_col]
        industry = df.at[idx, 'Industry'] if 'Industry' in df.columns else ""
        
        website = find_website_for_company(company, industry)
        if website:
            df.at[idx, website_col] = website
            found += 1
            print(f"  Found: {company} -> {website}")
    
    print(f"  Found websites for {found} companies")
    return df


# =============================================================================
# DESCRIPTION ENRICHMENT
# =============================================================================

def enrich_with_scraping(df, website_col='Website', description_col='Description'):
    """Enrich companies by scraping their websites."""
    print("Enriching with website scraping...")
    
    # Find companies needing enrichment
    needs_enrichment = df[
        (df[description_col].isna()) | 
        (df[description_col] == '') |
        (df[description_col].str.len() < 50)
    ]
    
    print(f"  Companies needing enrichment: {len(needs_enrichment)}")
    
    enriched = 0
    for idx in needs_enrichment.index:
        website = df.at[idx, website_col]
        if not website or pd.isna(website):
            continue
        
        try:
            content, method = smart_scrape(website)
            if content and len(content) > 100:
                df.at[idx, description_col] = content[:2000]
                enriched += 1
        except Exception as e:
            print(f"  Error scraping {website}: {e}")
    
    print(f"  Enriched {enriched} companies")
    return df


# =============================================================================
# CLASSIFICATION ENRICHMENT
# =============================================================================

def enrich_with_classification(df, use_llm=False):
    """Add classification results to dataframe."""
    print("Enriching with classification...")
    
    # Add classification columns if not exist
    if 'Classification' not in df.columns:
        df['Classification'] = ''
    if 'Confidence' not in df.columns:
        df['Confidence'] = 0.0
    if 'Products' not in df.columns:
        df['Products'] = ''
    
    for idx, row in df.iterrows():
        name = row.get('Company Name', '')
        industry = row.get('Industry', '')
        description = row.get('Description', '')
        
        # Quick keyword classification
        result = classify_by_keywords(name, industry, description)
        
        df.at[idx, 'Classification'] = result['classification']
        df.at[idx, 'Confidence'] = result['confidence']
        df.at[idx, 'Products'] = ', '.join(result.get('products', []))
    
    # Summary
    relevant = len(df[df['Classification'].str.contains('RELEVANT', na=False)])
    print(f"  Relevant: {relevant}")
    print(f"  Not Relevant: {len(df) - relevant}")
    
    return df


# =============================================================================
# COUNTRY DETECTION
# =============================================================================

def detect_country(row):
    """Detect country from company data."""
    # Check existing country column
    if 'Country' in row and pd.notna(row['Country']) and row['Country']:
        return row['Country']
    
    # Check website TLD
    website = row.get('Website', '')
    if website:
        if '.uk' in website or '.co.uk' in website:
            return 'United Kingdom'
        elif '.de' in website:
            return 'Germany'
        elif '.fr' in website:
            return 'France'
        elif '.jp' in website:
            return 'Japan'
        elif '.cn' in website:
            return 'China'
        elif '.in' in website:
            return 'India'
        elif '.com' in website or '.io' in website:
            return 'United States'  # Default for .com
    
    return ''


def enrich_with_country(df):
    """Add country information to dataframe."""
    print("Enriching with country detection...")
    
    if 'Country' not in df.columns:
        df['Country'] = ''
    
    df['Country'] = df.apply(detect_country, axis=1)
    
    # Summary
    countries = df['Country'].value_counts()
    print(f"  Top countries: {dict(countries.head())}")
    
    return df


# =============================================================================
# BATCH ENRICHMENT
# =============================================================================

def enrich_companies_full(input_path, output_path, options=None):
    """
    Full enrichment pipeline.
    
    Options:
        - websites: Find missing websites
        - scrape: Scrape website content
        - classify: Add classification
        - country: Add country detection
    """
    options = options or ['websites', 'scrape', 'classify', 'country']
    
    print("=" * 60)
    print("COMPANY ENRICHMENT PIPELINE")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df)} companies from {input_path}")
    
    # Apply enrichments
    if 'websites' in options:
        df = enrich_missing_websites(df)
    
    if 'scrape' in options:
        df = enrich_with_scraping(df)
    
    if 'classify' in options:
        df = enrich_with_classification(df)
    
    if 'country' in options:
        df = enrich_with_country(df)
    
    # Save
    df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")
    print(f"Total: {len(df)} companies")
    
    return df


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich company data")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", help="Output CSV file")
    parser.add_argument("--websites", action="store_true", help="Find missing websites")
    parser.add_argument("--scrape", action="store_true", help="Scrape website content")
    parser.add_argument("--classify", action="store_true", help="Add classification")
    parser.add_argument("--country", action="store_true", help="Add country detection")
    parser.add_argument("--all", action="store_true", help="All enrichments")
    
    args = parser.parse_args()
    
    output = args.output or args.input.replace('.csv', '_enriched.csv')
    
    options = []
    if args.all:
        options = ['websites', 'scrape', 'classify', 'country']
    else:
        if args.websites:
            options.append('websites')
        if args.scrape:
            options.append('scrape')
        if args.classify:
            options.append('classify')
        if args.country:
            options.append('country')
    
    if options:
        enrich_companies_full(args.input, output, options)
    else:
        print("Specify at least one enrichment option or --all")
