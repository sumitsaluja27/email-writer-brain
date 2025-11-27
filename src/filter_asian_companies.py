import pandas as pd
import os
import re

# ───── SETTINGS ─────
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_validated.csv"
ASIAN_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/asian_companies.csv"
NON_ASIAN_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian.csv"

# ───── KEYWORDS AND PATTERNS ─────

# Rule 1: Direct country matches
ASIAN_COUNTRIES = ["china", "taiwan", "hong kong", "vietnam", "korea"]

# Rule 2: City keywords in company name
CITY_KEYWORDS = {
    "China": ["shenzhen", "xiamen", "dongguan", "hangzhou", "beijing", "shanghai", "guangzhou", "suzhou", "chengdu", "wuhan", "nanjing", "tianjin", "qingdao", "foshan", "zhongshan", "ningbo", "hefei", "changsha", "wuxi", "kunshan", "zhuhai", "jinan", "dalian", "fuzhou", "harbin", "shijiazhuang", "zhengzhou", "changchun", "nanchang", "wenzhou"],
    "Taiwan": ["taipei", "taichung", "kaohsiung", "tainan", "hsinchu", "taoyuan", "new taipei", "keelung", "chiayi"],
    "Hong Kong": ["hong kong", " hk ", "(hk)", "hongkong"],
    "Vietnam": ["hanoi", "ho chi minh", "hcmc", "saigon", "danang", "haiphong", "can tho"],
    "Korea": ["seoul", "busan", "incheon", "daegu", "daejeon", "gwangju", "suwon", "ulsan", "changwon", "goyang", "yongin", "seongnam", "cheongju", "jeonju"]
}
ALL_CITY_KEYWORDS = [city for cities in CITY_KEYWORDS.values() for city in cities]

# Rule 3: Common patterns in company name
COMMON_PATTERNS = ["co., ltd", "technology co.,", "ltd.", "(shenzhen)", "(beijing)", "electronic co", "industrial co", "intelligent tech", "innovation tech"]

# ───── MAIN SCRIPT ─────

def filter_companies():
    """Filters companies based on Asian country indicators."""
    print(f"Loading input file: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found.")
        return

    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    print(f"Loaded {len(df)} companies.")

    # Create boolean masks for each rule (case-insensitive) 
    
    # Rule 1: Match country column
    # Ensure 'Country' column exists and is string type before using .str
    if 'Country' in df.columns:
        df['Country'] = df['Country'].astype(str)
        rule1_mask = df['Country'].str.lower().isin(ASIAN_COUNTRIES)
    else:
        rule1_mask = pd.Series([False] * len(df), index=df.index)

    # Rules 2 & 3: Match keywords and patterns in company name
    # Ensure 'Exhibitor' column exists and is string type
    if 'Exhibitor' in df.columns:
        df['Exhibitor'] = df['Exhibitor'].astype(str)
        company_name_lower = df['Exhibitor'].str.lower()
        
        # Combine all keywords and patterns into a single regex for efficiency
        all_keywords = ALL_CITY_KEYWORDS + COMMON_PATTERNS
        regex_pattern = '|'.join(map(re.escape, all_keywords))
        
        rule2_3_mask = company_name_lower.str.contains(regex_pattern, na=False)
    else:
        rule2_3_mask = pd.Series([False] * len(df), index=df.index)

    # Rule 4: Check Summary for Asian keywords (Countries + Cities)
    if 'Summary' in df.columns:
        df['Summary'] = df['Summary'].astype(str)
        summary_lower = df['Summary'].str.lower()
        
        # Create a broader pattern for summary that includes country names
        summary_keywords = ASIAN_COUNTRIES + ALL_CITY_KEYWORDS
        summary_regex = '|'.join(map(re.escape, summary_keywords))
        
        rule4_mask = summary_lower.str.contains(summary_regex, na=False)
    else:
        rule4_mask = pd.Series([False] * len(df), index=df.index)

    # Rule 5: Check Website for Asian keywords
    if 'Website' in df.columns:
        df['Website'] = df['Website'].astype(str)
        website_lower = df['Website'].str.lower()
        rule5_mask = website_lower.str.contains(summary_regex, na=False)
    else:
        rule5_mask = pd.Series([False] * len(df), index=df.index)

    # Combine the masks to get all Asian companies
    is_asian_mask = rule1_mask | rule2_3_mask | rule4_mask | rule5_mask

    # Split the DataFrame
    asian_companies_df = df[is_asian_mask]
    non_asian_companies_df = df[~is_asian_mask]

    # Save the output files
    print(f"\nSaving {len(asian_companies_df)} Asian companies to: {ASIAN_OUTPUT_FILE}")
    asian_companies_df.to_csv(ASIAN_OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"Saving {len(non_asian_companies_df)} remaining companies to: {NON_ASIAN_OUTPUT_FILE}")
    non_asian_companies_df.to_csv(NON_ASIAN_OUTPUT_FILE, index=False, encoding="utf-8")

    # Print summary
    print("\n===== SUMMARY =====")
    print(f"Asian companies found: {len(asian_companies_df)}")
    print(f"Remaining companies:   {len(non_asian_companies_df)}")
    print("=====================")

if __name__ == "__main__":
    filter_companies()
