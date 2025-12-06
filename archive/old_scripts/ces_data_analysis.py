import pandas as pd

# File path
CES_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_enriched.csv"

# Load the CSV
df = pd.read_csv(CES_FILE, encoding="utf-8")

# Total companies
total_companies = len(df)

# Count companies WITH summary (not empty, not null)
has_summary = df['Summary'].notna() & (df['Summary'] != '')
companies_with_summary = has_summary.sum()

# Count companies WITHOUT summary
companies_without_summary = total_companies - companies_with_summary

# Count companies WITH website
has_website = df['Website'].notna() & (df['Website'] != '')
companies_with_website = has_website.sum()

# Count companies WITHOUT website
companies_without_website = total_companies - companies_with_website

# Count companies WITH both summary AND website
both_summary_website = (has_summary & has_website).sum()

# Count companies WITH summary but NO website
summary_no_website = (has_summary & ~has_website).sum()

# Count companies WITHOUT summary but WITH website
no_summary_with_website = (~has_summary & has_website).sum()

# Count companies WITHOUT both
neither = (~has_summary & ~has_website).sum()

# Print the analysis
print("=" * 60)
print("CES 2026 COMPANIES - DATA ANALYSIS")
print("=" * 60)
print(f"\n📊 TOTAL COMPANIES: {total_companies}")
print("\n" + "-" * 60)
print("SUMMARY ANALYSIS:")
print("-" * 60)
print(f"  ✅ Companies WITH Summary:     {companies_with_summary:4d} ({companies_with_summary/total_companies*100:.1f}%)")
print(f"  ❌ Companies WITHOUT Summary:  {companies_without_summary:4d} ({companies_without_summary/total_companies*100:.1f}%)")
print("\n" + "-" * 60)
print("WEBSITE ANALYSIS:")
print("-" * 60)
print(f"  ✅ Companies WITH Website:     {companies_with_website:4d} ({companies_with_website/total_companies*100:.1f}%)")
print(f"  ❌ Companies WITHOUT Website:  {companies_without_website:4d} ({companies_without_website/total_companies*100:.1f}%)")
print("\n" + "-" * 60)
print("COMBINED ANALYSIS:")
print("-" * 60)
print(f"  ✅ Summary + Website:          {both_summary_website:4d} ({both_summary_website/total_companies*100:.1f}%)")
print(f"  ⚠️  Summary but NO Website:    {summary_no_website:4d} ({summary_no_website/total_companies*100:.1f}%)")
print(f"  ⚠️  Website but NO Summary:    {no_summary_with_website:4d} ({no_summary_with_website/total_companies*100:.1f}%)")
print(f"  ❌ NO Summary + NO Website:    {neither:4d} ({neither/total_companies*100:.1f}%)")
print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)
print(f"\n🎯 PRIORITY 1: Validate {both_summary_website} companies (Have both - can verify accuracy)")
print(f"🎯 PRIORITY 2: Find websites for {summary_no_website} companies (Have summary - easier search)")
print(f"⚠️  PRIORITY 3: Review {no_summary_with_website} companies (Need to verify without summary)")
print(f"⏸️  PRIORITY 4: Handle {neither} companies (Hardest - need both summary and website)")
print("\n" + "=" * 60)
