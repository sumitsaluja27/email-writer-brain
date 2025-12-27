"""
Rapidise Company Classification Pipeline - Data Cleaner
========================================================

Consolidated data cleaning functionality.
Combines: clean_ces_data.py, clean_descriptions.py, fix_csv_formatting.py,
          filter_complete_list.py, synchronize_and_balance.py

Handles:
- CSV cleaning and formatting
- Description cleaning
- Data validation
"""

import pandas as pd
import re
import os
from datetime import datetime


# =============================================================================
# TEXT CLEANING
# =============================================================================

def clean_text(text):
    """Clean and normalize text content."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?\-\'\"()]', '', text)
    
    return text.strip()


def clean_company_name(name):
    """Clean company name."""
    if pd.isna(name) or not isinstance(name, str):
        return ""
    
    # Remove common suffixes
    suffixes = [', Inc.', ', Inc', ' Inc.', ' Inc', ', LLC', ' LLC', 
                ', Ltd.', ', Ltd', ' Ltd.', ' Ltd', ', Corp.', ' Corp.']
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    return name.strip()


def clean_website(url):
    """Clean and normalize website URL."""
    if pd.isna(url) or not isinstance(url, str):
        return ""
    
    url = url.strip().lower()
    
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Ensure https://
    if url and not url.startswith('http'):
        url = 'https://' + url
    
    return url


# =============================================================================
# CSV CLEANING
# =============================================================================

def clean_csv(input_path, output_path=None, columns=None):
    """
    Clean a CSV file.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV (optional, overwrites if None)
        columns: Dict of column name -> cleaning function
    """
    print(f"Cleaning: {input_path}")
    
    # Read CSV
    df = pd.read_csv(input_path)
    print(f"  Loaded: {len(df)} rows")
    
    # Default column cleaning
    if columns is None:
        columns = {}
        
        # Auto-detect common columns
        for col in df.columns:
            col_lower = col.lower()
            if 'name' in col_lower and 'company' in col_lower:
                columns[col] = clean_company_name
            elif 'website' in col_lower or 'url' in col_lower:
                columns[col] = clean_website
            elif 'description' in col_lower or 'summary' in col_lower:
                columns[col] = clean_text
    
    # Apply cleaning
    for col, clean_fn in columns.items():
        if col in df.columns:
            df[col] = df[col].apply(clean_fn)
            print(f"  Cleaned: {col}")
    
    # Remove duplicates
    if 'Company Name' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=['Company Name'], keep='first')
        print(f"  Removed {before - len(df)} duplicates")
    
    # Remove empty rows
    before = len(df)
    df = df.dropna(how='all')
    print(f"  Removed {before - len(df)} empty rows")
    
    # Save
    output_path = output_path or input_path
    df.to_csv(output_path, index=False)
    print(f"  Saved: {output_path} ({len(df)} rows)")
    
    return df


def fix_csv_formatting(input_path, output_path=None):
    """Fix common CSV formatting issues."""
    print(f"Fixing formatting: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Fix column names (remove leading/trailing spaces)
    df.columns = [col.strip() for col in df.columns]
    
    # Fix encoding issues
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') if isinstance(x, str) else x)
    
    output_path = output_path or input_path
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"  Saved: {output_path}")
    
    return df


# =============================================================================
# DESCRIPTION CLEANING
# =============================================================================

def clean_description(text, min_length=50, max_length=2000):
    """Clean company description text."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Basic cleaning
    text = clean_text(text)
    
    # Check length
    if len(text) < min_length:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def is_valid_description(text, min_length=50):
    """Check if description is valid and useful."""
    if not text or len(text) < min_length:
        return False
    
    # Check for common error messages
    error_patterns = [
        'page not found', '404', 'error', 'access denied',
        'javascript required', 'loading', 'please wait'
    ]
    
    text_lower = text.lower()
    for pattern in error_patterns:
        if pattern in text_lower:
            return False
    
    return True


def identify_weak_descriptions(df, description_col='Description', min_length=50):
    """Identify rows with weak or missing descriptions."""
    weak_indices = []
    
    for idx, row in df.iterrows():
        desc = row.get(description_col, '')
        if not is_valid_description(desc, min_length):
            weak_indices.append(idx)
    
    return weak_indices


# =============================================================================
# DATA VALIDATION
# =============================================================================

def validate_company_data(df):
    """Validate company data and report issues."""
    issues = {
        'missing_name': [],
        'missing_website': [],
        'missing_description': [],
        'invalid_website': [],
        'duplicate_name': []
    }
    
    # Check for missing data
    for idx, row in df.iterrows():
        name = row.get('Company Name', row.get('name', ''))
        website = row.get('Website', row.get('website', ''))
        description = row.get('Description', row.get('Summary', ''))
        
        if not name or pd.isna(name):
            issues['missing_name'].append(idx)
        
        if not website or pd.isna(website):
            issues['missing_website'].append(idx)
        
        if not description or pd.isna(description) or len(str(description)) < 50:
            issues['missing_description'].append(idx)
        
        if website and not str(website).startswith('http'):
            issues['invalid_website'].append(idx)
    
    # Check for duplicates
    if 'Company Name' in df.columns:
        duplicates = df[df.duplicated(subset=['Company Name'], keep=False)]
        issues['duplicate_name'] = list(duplicates.index)
    
    # Print report
    print("\nData Validation Report:")
    print("-" * 40)
    for issue, indices in issues.items():
        print(f"  {issue}: {len(indices)} issues")
    
    return issues


# =============================================================================
# MERGE & SYNC
# =============================================================================

def merge_csv_files(file_paths, output_path, key_column='Company Name'):
    """Merge multiple CSV files, removing duplicates."""
    print(f"Merging {len(file_paths)} files...")
    
    dfs = []
    for path in file_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            dfs.append(df)
            print(f"  Loaded: {path} ({len(df)} rows)")
    
    if not dfs:
        print("No files to merge")
        return None
    
    # Concatenate
    merged = pd.concat(dfs, ignore_index=True)
    print(f"  Combined: {len(merged)} rows")
    
    # Remove duplicates
    if key_column in merged.columns:
        merged = merged.drop_duplicates(subset=[key_column], keep='first')
        print(f"  After dedup: {len(merged)} rows")
    
    # Save
    merged.to_csv(output_path, index=False)
    print(f"  Saved: {output_path}")
    
    return merged


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean company data")
    parser.add_argument("--input", help="Input CSV file")
    parser.add_argument("--output", help="Output CSV file")
    parser.add_argument("--validate", action="store_true", help="Validate only")
    parser.add_argument("--fix", action="store_true", help="Fix formatting")
    
    args = parser.parse_args()
    
    if args.input:
        if args.validate:
            df = pd.read_csv(args.input)
            validate_company_data(df)
        elif args.fix:
            fix_csv_formatting(args.input, args.output)
        else:
            clean_csv(args.input, args.output)
    else:
        print("Usage: python data_cleaner.py --input file.csv [--output out.csv] [--validate] [--fix]")
