import pandas as pd
import re

file_path = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv"

# Read CSV
df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')

print("="*60)
print("🔧 LINKEDIN URL FIXER")
print("="*60)

# Fill NaN
df['LinkedIn (company)'] = df['LinkedIn (company)'].fillna('')

# Count malformed URLs BEFORE
malformed_before = df[
    (df['LinkedIn (company)'].str.strip() != '') &
    (~df['LinkedIn (company)'].str.contains('linkedin.com', case=False, na=False))
]
print(f"\n📊 Malformed LinkedIn URLs found: {len(malformed_before)}")

# Fix function
def fix_linkedin_url(url):
    """
    Fixes malformed LinkedIn URLs.
    
    Examples:
        'icodice' → 'https://www.linkedin.com/company/icodice/'
        'rockstar-coders' → 'https://www.linkedin.com/company/rockstar-coders/'
        'https://www.breezelabs.ai/' → Keep as is (not LinkedIn)
    """
    url = url.strip()
    
    # If empty, return as is
    if not url:
        return url
    
    # If already has linkedin.com, return as is
    if 'linkedin.com' in url.lower():
        return url
    
    # If it looks like a website URL (has http/https), return as is
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # Otherwise, assume it's a company slug and fix it
    # Remove any leading/trailing slashes
    slug = url.strip('/')
    
    # Build proper LinkedIn URL
    fixed_url = f"https://www.linkedin.com/company/{slug}/"
    
    return fixed_url

# Apply fix
print("\n🔄 Fixing URLs...")
df['LinkedIn (company)'] = df['LinkedIn (company)'].apply(fix_linkedin_url)

# Count malformed URLs AFTER
malformed_after = df[
    (df['LinkedIn (company)'].str.strip() != '') &
    (~df['LinkedIn (company)'].str.contains('linkedin.com', case=False, na=False))
]
print(f"✅ Malformed URLs remaining: {len(malformed_after)}")
print(f"✅ Fixed: {len(malformed_before) - len(malformed_after)} URLs")

# Show some examples
print("\n📋 Sample of fixed URLs:")
sample_fixed = df[
    df['LinkedIn (company)'].str.contains('/company/', case=False, na=False)
].head(5)
print(sample_fixed[['Company Name', 'LinkedIn (company)']])

# Save corrected CSV
print("\n💾 Saving corrected CSV...")
try:
    df.to_csv(file_path, index=False)
    print(f"✅ Saved to: {file_path}")
except Exception as e:
    print(f"❌ Error saving: {e}")

print("="*60)
print("✅ DONE!")
print("="*60)