"""
COMPREHENSIVE CSV FIX - Fixes ALL issues:
1. Removes non-printable/garbage characters
2. Fixes encoding (ftfy)
3. Validates row structure (correct column count)
4. Removes rows with obvious garbage (OS:, Linux:, Language:)
5. Overwrites files IN-PLACE
"""

import os
import re
import csv
from io import StringIO

try:
    import ftfy
except ImportError:
    os.system("pip install ftfy")
    import ftfy

DATA_DIR = 'data/Companies/'

# ALL files that need fixing
FILES_TO_FIX = [
    'CES_2026_BEACON_CLEAN.csv',
    'CES_2026_BODY_CAM_CLEAN.csv',
    'CES_2026_IN_CABIN_CLEAN.csv',
    'CES_2026_IP_CAMERA_CLEAN.csv',
    'CES_2026_DASHCAM_CLEAN.csv',
    'CES_2026_ENRICHED.csv',
    'CES_2026_CATEGORIZED.csv',
    'CES_2026_RAG_MATCHED.csv',
    'company_descriptions.csv',
    'CES_2026_relevant_for_rapidise.csv'
]

# Patterns that indicate garbage data (not a valid company row)
GARBAGE_PATTERNS = [
    r'^OS\s*:',
    r'^Linux\s*:',
    r'^Language\s*:',
    r'^Android\s+\d',
    r'^Quectel',
    r'^\s*\d+\.\d+\s*$',  # Just a version number
    r'^Kernel',
]

def is_garbage_row(row_text):
    """Check if a row contains garbage data."""
    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, row_text, re.IGNORECASE):
            return True
    # Check for excessive non-ASCII (more than 30% non-ASCII = likely garbage)
    if len(row_text) > 10:
        non_ascii = sum(1 for c in row_text if ord(c) > 127)
        if non_ascii / len(row_text) > 0.3:
            return True
    return False

def clean_text(text):
    """Clean a single text field."""
    if not text:
        return ""
    # Fix encoding
    text = ftfy.fix_text(str(text))
    # Remove zero-width chars
    text = text.replace('\u200b', '').replace('\ufeff', '').replace('\u200c', '').replace('\u200d', '')
    # Remove control chars except newline/tab
    text = ''.join(c for c in text if c == '\n' or c == '\t' or (ord(c) >= 32 and ord(c) < 127) or (ord(c) >= 160))
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def fix_csv_file(file_path):
    """Fix a single CSV file comprehensively."""
    if not os.path.exists(file_path):
        print(f"⚠️  Skipping {os.path.basename(file_path)} (not found)")
        return
    
    print(f"🔧 Fixing {os.path.basename(file_path)}...")
    
    # Read raw content
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        raw_content = f.read()
    
    # Fix encoding first
    content = ftfy.fix_text(raw_content)
    
    # Parse as CSV
    try:
        reader = csv.reader(StringIO(content))
        rows = list(reader)
    except Exception as e:
        print(f"   ❌ CSV parse error: {e}")
        return
    
    if not rows:
        print(f"   ⚠️  Empty file")
        return
    
    header = rows[0]
    expected_cols = len(header)
    
    # Clean header
    header = [clean_text(h) for h in header]
    
    cleaned_rows = [header]
    garbage_count = 0
    malformed_count = 0
    
    for row in rows[1:]:
        # Skip rows with wrong column count
        if len(row) != expected_cols:
            malformed_count += 1
            continue
        
        # Clean each cell
        cleaned_row = [clean_text(cell) for cell in row]
        row_text = ','.join(cleaned_row)
        
        # Skip garbage rows
        if is_garbage_row(row_text):
            garbage_count += 1
            continue
        
        # Skip completely empty rows
        if all(cell == '' for cell in cleaned_row):
            continue
            
        cleaned_rows.append(cleaned_row)
    
    # Write back IN-PLACE
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)
    
    final_count = len(cleaned_rows) - 1  # Exclude header
    print(f"   ✅ Fixed: {final_count} rows (removed {garbage_count} garbage, {malformed_count} malformed)")

def main():
    print("=" * 70)
    print("COMPREHENSIVE CSV FIX")
    print("=" * 70)
    
    for filename in FILES_TO_FIX:
        file_path = os.path.join(DATA_DIR, filename)
        fix_csv_file(file_path)
    
    print("=" * 70)
    print("DONE - All files fixed in-place")
    print("=" * 70)

if __name__ == "__main__":
    main()
