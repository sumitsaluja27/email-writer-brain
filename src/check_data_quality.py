import pandas as pd

file_path = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv"

df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')

print("="*60)
print("🔍 DATA QUALITY REPORT")
print("="*60)

# Total rows
print(f"\n📊 Total rows in CSV: {len(df)}")

# Empty company names (junk rows)
df['Company Name'] = df['Company Name'].fillna('')
empty_names = df[df['Company Name'].str.strip() == '']
print(f"❌ Rows with EMPTY company name: {len(empty_names)}")

# Check the 114 "nothing" companies
df['Industry'] = df['Industry'].fillna('')
df['LinkedIn (company)'] = df['LinkedIn (company)'].fillna('')
df['Website'] = df['Website'].fillna('')

has_nothing = df[
    (df['Website'].str.strip() == '') & 
    (df['LinkedIn (company)'].str.strip() == '') & 
    (df['Industry'].str.strip() == '') &
    (df['Company Name'].str.strip() != '')  # BUT has a name
]

print(f"\n🔍 Companies with NAME but no Website/LinkedIn/Industry: {len(has_nothing)}")

# Show first 10
if len(has_nothing) > 0:
    print("\nFirst 10 examples:")
    print(has_nothing[['Company Name', 'Website', 'LinkedIn (company)', 'Industry']].head(10))

# Check for malformed LinkedIn URLs
df_with_linkedin = df[df['LinkedIn (company)'].str.strip() != '']
malformed_linkedin = df_with_linkedin[
    ~df_with_linkedin['LinkedIn (company)'].str.contains('linkedin.com', case=False, na=False)
]

print(f"\n⚠️  Malformed LinkedIn URLs (missing 'linkedin.com'): {len(malformed_linkedin)}")
if len(malformed_linkedin) > 0:
    print("\nExamples:")
    print(malformed_linkedin[['Company Name', 'LinkedIn (company)']].head(10))

print("="*60)