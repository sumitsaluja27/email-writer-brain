import pandas as pd

file_path = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv"

df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')

# Fill NaN
df['Industry'] = df['Industry'].fillna('')
df['LinkedIn (company)'] = df['LinkedIn (company)'].fillna('')
df['Website'] = df['Website'].fillna('')

# Companies WITH LinkedIn URL but NO Industry
has_linkedin_no_industry = df[
    (df['LinkedIn (company)'].str.strip() != '') & 
    (df['Industry'].str.strip() == '')
]

# Companies WITH Website but NO LinkedIn URL and NO Industry
has_website_no_linkedin_no_industry = df[
    (df['Website'].str.strip() != '') & 
    (df['LinkedIn (company)'].str.strip() == '') & 
    (df['Industry'].str.strip() == '')
]

# Companies with NOTHING
has_nothing = df[
    (df['Website'].str.strip() == '') & 
    (df['LinkedIn (company)'].str.strip() == '') & 
    (df['Industry'].str.strip() == '')
]

print("="*60)
print("📊 FAILURE ANALYSIS")
print("="*60)
print(f"Total companies missing industry: {len(df[df['Industry'].str.strip() == ''])}")
print()
print("Breakdown:")
print(f"  ✅ Have LinkedIn URL but failed to scrape industry: {len(has_linkedin_no_industry)}")
print(f"  🌐 Have Website but no LinkedIn URL found: {len(has_website_no_linkedin_no_industry)}")
print(f"  ❌ Have nothing (no website, no LinkedIn): {len(has_nothing)}")
print("="*60)

# Show a few examples
if len(has_linkedin_no_industry) > 0:
    print("\n🔍 Sample companies WITH LinkedIn but NO industry:")
    print(has_linkedin_no_industry[['Company Name', 'LinkedIn (company)']].head(5))

if len(has_website_no_linkedin_no_industry) > 0:
    print("\n🔍 Sample companies WITH Website but NO LinkedIn:")
    print(has_website_no_linkedin_no_industry[['Company Name', 'Website']].head(5))