"""
Clean CES 2026 CSV files for Looker Studio
- Rename columns to snake_case
- Force UTF-8 encoding
- Quote all fields
"""

import os
import pandas as pd
import re
import csv

# Target directory (note: folder has trailing space)
TARGET_DIR = '/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/CES 2026 '

def to_snake_case(column_name):
    """Convert column name to snake_case, removing special characters."""
    # Remove special characters like dots, parentheses
    cleaned = re.sub(r'[.\(\)\[\]\{\}]', '', str(column_name))
    # Replace spaces and hyphens with underscores
    cleaned = re.sub(r'[\s\-]+', '_', cleaned)
    # Convert to lowercase
    cleaned = cleaned.lower()
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    return cleaned

def clean_csv_file(filepath, output_path):
    """Clean a single CSV file."""
    try:
        # Try reading with different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(filepath, encoding=encoding, on_bad_lines='skip')
                break
            except:
                continue
        
        # Rename columns to snake_case
        original_columns = df.columns.tolist()
        new_columns = [to_snake_case(col) for col in original_columns]
        df.columns = new_columns
        
        # Save with UTF-8 encoding and quote all fields
        df.to_csv(
            output_path,
            index=False,
            encoding='utf-8',
            quoting=csv.QUOTE_ALL
        )
        
        return True, len(df), original_columns, new_columns
    except Exception as e:
        return False, 0, [], str(e)

def main():
    print("=" * 60)
    print("CLEANING CES 2026 CSV FILES FOR LOOKER STUDIO")
    print("=" * 60)
    
    # Verify path exists
    if not os.path.exists(TARGET_DIR):
        print(f"ERROR: Directory not found: {TARGET_DIR}")
        return
    
    print(f"\nTarget directory: {TARGET_DIR}")
    
    # Get all CSV files (excluding already cleaned ones)
    csv_files = [f for f in os.listdir(TARGET_DIR) 
                 if f.endswith('.csv') and not f.startswith('clean_')]
    
    print(f"Found {len(csv_files)} CSV files to clean\n")
    
    for filename in sorted(csv_files):
        filepath = os.path.join(TARGET_DIR, filename)
        output_filename = f"clean_{filename}"
        output_path = os.path.join(TARGET_DIR, output_filename)
        
        print(f"Processing: {filename}")
        
        success, rows, orig_cols, new_cols = clean_csv_file(filepath, output_path)
        
        if success:
            print(f"  ✓ Cleaned successfully!")
            print(f"    Rows: {rows}")
            print(f"    Columns: {len(orig_cols)}")
            print(f"    Output: {output_filename}")
            
            # Show column changes (first 5)
            changes = [(o, n) for o, n in zip(orig_cols[:5], new_cols[:5]) if o != n]
            if changes:
                print(f"    Column changes (sample):")
                for orig, new in changes:
                    print(f"      '{orig}' → '{new}'")
        else:
            print(f"  ✗ Error: {new_cols}")
        
        print()
    
    print("=" * 60)
    print("CLEANING COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
