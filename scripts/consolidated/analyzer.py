"""
Rapidise Company Classification Pipeline - Analyzer
====================================================

Consolidated analysis functionality.
Combines: review_not_relevant.py, extract_company_analysis.py, finalize_csv_v02.py

Handles:
- Reviewing classification results
- Analyzing company data
- Generating reports
"""

import pandas as pd
import json
from datetime import datetime
from collections import Counter

try:
    from .config import PRODUCTS, COMPANIES_DIR
except ImportError:
    COMPANIES_DIR = 'data/Companies'


# =============================================================================
# CLASSIFICATION REVIEW
# =============================================================================

def review_not_relevant(df, output_path=None):
    """
    Review companies classified as NOT_RELEVANT to catch false negatives.
    
    Flags companies that might be incorrectly classified based on:
    - Keywords in name/description
    - Industry signals
    - Known brands
    """
    print("=" * 60)
    print("REVIEWING NOT_RELEVANT CLASSIFICATIONS")
    print("=" * 60)
    
    # Filter NOT_RELEVANT
    not_relevant = df[df['Classification'] == 'NOT_RELEVANT'].copy()
    print(f"Companies marked NOT_RELEVANT: {len(not_relevant)}")
    
    # Keywords that suggest potential relevance
    relevant_keywords = [
        'camera', 'dashcam', 'video', 'fleet', 'telematics', 'security',
        'surveillance', 'bodycam', 'monitor', 'tracking', 'gps', 'adas',
        'driver', 'safety', 'automotive', 'vehicle'
    ]
    
    # Known brands that should be relevant
    known_brands = [
        'garmin', 'nexar', 'samsara', 'lytx', 'verizon connect',
        'geotab', 'blackvue', 'thinkware', 'viofo', 'rexing'
    ]
    
    flagged = []
    
    for idx, row in not_relevant.iterrows():
        name = str(row.get('Company Name', '')).lower()
        industry = str(row.get('Industry', '')).lower()
        description = str(row.get('Description', '')).lower()
        
        reasons = []
        
        # Check keywords
        text = f"{name} {industry} {description}"
        for keyword in relevant_keywords:
            if keyword in text:
                reasons.append(f"keyword: {keyword}")
        
        # Check known brands
        for brand in known_brands:
            if brand in name:
                reasons.append(f"known brand: {brand}")
        
        if reasons:
            flagged.append({
                'index': idx,
                'company': row.get('Company Name', ''),
                'industry': row.get('Industry', ''),
                'reasons': reasons
            })
    
    # Report
    print(f"\nFlagged for review: {len(flagged)}")
    for f in flagged[:20]:
        print(f"  - {f['company']}: {', '.join(f['reasons'][:3])}")
    
    # Save flagged
    if output_path and flagged:
        flagged_df = pd.DataFrame(flagged)
        flagged_df.to_csv(output_path, index=False)
        print(f"\nSaved flagged companies to: {output_path}")
    
    return flagged


def review_relevant(df, output_path=None):
    """
    Review companies classified as RELEVANT to catch false positives.
    """
    print("=" * 60)
    print("REVIEWING RELEVANT CLASSIFICATIONS")
    print("=" * 60)
    
    relevant = df[df['Classification'] == 'RELEVANT'].copy()
    print(f"Companies marked RELEVANT: {len(relevant)}")
    
    # Keywords that suggest potential false positive
    not_relevant_keywords = [
        'hospital', 'school', 'university', 'restaurant', 'hotel',
        'bank', 'insurance', 'law firm', 'accounting', 'consulting',
        'marketing', 'recruiting', 'real estate'
    ]
    
    flagged = []
    
    for idx, row in relevant.iterrows():
        name = str(row.get('Company Name', '')).lower()
        industry = str(row.get('Industry', '')).lower()
        description = str(row.get('Description', '')).lower()
        
        reasons = []
        
        text = f"{name} {industry} {description}"
        for keyword in not_relevant_keywords:
            if keyword in text:
                reasons.append(f"possible end-user: {keyword}")
        
        if reasons:
            flagged.append({
                'index': idx,
                'company': row.get('Company Name', ''),
                'industry': row.get('Industry', ''),
                'reasons': reasons
            })
    
    print(f"\nFlagged for review: {len(flagged)}")
    for f in flagged[:20]:
        print(f"  - {f['company']}: {', '.join(f['reasons'][:3])}")
    
    return flagged


# =============================================================================
# STATISTICS & REPORTS
# =============================================================================

def generate_classification_report(df, output_path=None):
    """Generate a classification summary report."""
    print("=" * 60)
    print("CLASSIFICATION REPORT")
    print(f"Generated: {datetime.now()}")
    print("=" * 60)
    
    report = {
        'total_companies': len(df),
        'classification_breakdown': {},
        'product_breakdown': {},
        'industry_breakdown': {},
        'confidence_stats': {}
    }
    
    # Classification breakdown
    if 'Classification' in df.columns:
        classification_counts = df['Classification'].value_counts().to_dict()
        report['classification_breakdown'] = classification_counts
        
        print(f"\nClassification:")
        for cls, count in classification_counts.items():
            pct = count / len(df) * 100
            print(f"  {cls}: {count} ({pct:.1f}%)")
    
    # Product breakdown
    if 'Products' in df.columns:
        products_flat = []
        for products in df['Products'].dropna():
            if isinstance(products, str):
                products_flat.extend([p.strip() for p in products.split(',')])
        
        product_counts = Counter(products_flat)
        report['product_breakdown'] = dict(product_counts.most_common(10))
        
        print(f"\nTop Products:")
        for product, count in product_counts.most_common(10):
            print(f"  {product}: {count}")
    
    # Industry breakdown
    if 'Industry' in df.columns:
        industry_counts = df['Industry'].value_counts().head(10).to_dict()
        report['industry_breakdown'] = industry_counts
        
        print(f"\nTop Industries:")
        for industry, count in list(industry_counts.items())[:10]:
            print(f"  {industry}: {count}")
    
    # Confidence stats
    if 'Confidence' in df.columns:
        report['confidence_stats'] = {
            'mean': df['Confidence'].mean(),
            'median': df['Confidence'].median(),
            'min': df['Confidence'].min(),
            'max': df['Confidence'].max()
        }
        
        print(f"\nConfidence Stats:")
        print(f"  Mean: {report['confidence_stats']['mean']:.2f}")
        print(f"  Median: {report['confidence_stats']['median']:.2f}")
    
    # Save report
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_path}")
    
    return report


def analyze_by_product(df):
    """Analyze companies by matched Rapidise products."""
    print("=" * 60)
    print("ANALYSIS BY PRODUCT")
    print("=" * 60)
    
    # Count companies per product
    product_companies = {
        'dashcam': [],
        'bodycam': [],
        'ip_camera': [],
        'in_cabin': [],
        'access_control': [],
        'beacon': []
    }
    
    for idx, row in df.iterrows():
        products = row.get('Products', '')
        company = row.get('Company Name', '')
        
        if isinstance(products, str):
            for product in product_companies.keys():
                if product in products.lower():
                    product_companies[product].append(company)
    
    print("\nCompanies per product:")
    for product, companies in product_companies.items():
        print(f"\n{product.upper()} ({len(companies)}):")
        for c in companies[:5]:
            print(f"  - {c}")
        if len(companies) > 5:
            print(f"  ... and {len(companies) - 5} more")
    
    return product_companies


# =============================================================================
# FINALIZATION
# =============================================================================

def finalize_csv(input_path, output_path):
    """
    Finalize CSV for output.
    - Clean up columns
    - Sort by relevance
    - Remove duplicates
    """
    print("=" * 60)
    print("FINALIZING CSV")
    print("=" * 60)
    
    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df)} rows")
    
    # Remove duplicates
    if 'Company Name' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=['Company Name'], keep='first')
        print(f"Removed {before - len(df)} duplicates")
    
    # Sort by classification and confidence
    sort_cols = []
    if 'Classification' in df.columns:
        sort_cols.append('Classification')
    if 'Confidence' in df.columns:
        sort_cols.append('Confidence')
    
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[True, False])
    
    # Select output columns
    output_cols = [
        'Company Name', 'Website', 'Industry', 'Country',
        'Classification', 'Confidence', 'Products', 'Description'
    ]
    output_cols = [c for c in output_cols if c in df.columns]
    
    df = df[output_cols]
    
    # Save
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path} ({len(df)} rows)")
    
    return df


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze company data")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--review-not-relevant", action="store_true", help="Review NOT_RELEVANT")
    parser.add_argument("--review-relevant", action="store_true", help="Review RELEVANT")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--by-product", action="store_true", help="Analyze by product")
    parser.add_argument("--finalize", help="Finalize to output path")
    parser.add_argument("--output", help="Output path for results")
    
    args = parser.parse_args()
    
    df = pd.read_csv(args.input)
    
    if args.review_not_relevant:
        review_not_relevant(df, args.output)
    
    if args.review_relevant:
        review_relevant(df, args.output)
    
    if args.report:
        generate_classification_report(df, args.output)
    
    if args.by_product:
        analyze_by_product(df)
    
    if args.finalize:
        finalize_csv(args.input, args.finalize)
