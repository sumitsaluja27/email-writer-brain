import pandas as pd
import os

# Define the absolute path for the input file
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/asian_companies.csv"
JAPAN_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/japanese_companies.csv"
OTHER_ASIAN_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/asian_companies_excluded.csv"


# STEP 1 - DEFINE COUNTRY KEYWORDS
COUNTRY_KEYWORDS = {
    "China": ["shenzhen", "xiamen", "dongguan", "hangzhou", "beijing", "shanghai", "guangzhou", "suzhou", "chengdu", "wuhan", "nanjing", "tianjin", "qingdao", "foshan", "zhongshan", "china"],
    "Taiwan": ["taipei", "taichung", "kaohsiung", "tainan", "taiwan"],
    "Hong Kong": ["hong kong", "hongkong", " hk "],
    "Korea": ["seoul", "busan", "incheon", "daegu", "korea"],
    "Vietnam": ["hanoi", "ho chi minh", "hcmc", "saigon", "danang", "vietnam"],
    "Japan": ["tokyo", "osaka", "kyoto", "yokohama", "nagoya", "sapporo", "fukuoka", "kobe", "kawasaki", "hiroshima", "japan"],
    "Singapore": ["singapore"]
}

# STEP 2 - CREATE FUNCTION TO DETECT COUNTRY
def detect_country_from_text(company_name, website):
    """Detects country from company name or website domain"""
    text = f"{company_name} {website}".lower()
    
    for country, keywords in COUNTRY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return country
    
    return "Unknown"

def main():
    # STEP 3 - LOAD AND FIX DATA
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, encoding="utf-8")

    # Fix Country column
    for i in range(len(df)):
        current_country = str(df.loc[i, 'Country'])
        
        if current_country.lower() in ['unknown', 'nan', '']:
            company_name = str(df.loc[i, 'Exhibitor'])
            website = str(df.loc[i, 'Website']) if 'Website' in df.columns else ""
            
            detected = detect_country_from_text(company_name, website)
            df.loc[i, 'Country'] = detected

    # STEP 4 - REMOVE COMPANIES WITHOUT WEBSITES
    df['Website'] = df['Website'].fillna('')
    df_with_websites = df[df['Website'] != ''].copy()

    companies_removed = len(df) - len(df_with_websites)
    
    # STEP 5 - SPLIT BY REGION
    japan_df = df_with_websites[df_with_websites['Country'] == 'Japan'].copy()
    other_asian = df_with_websites[df_with_websites['Country'] != 'Japan'].copy()

    # Save files
    japan_df.to_csv(JAPAN_OUTPUT_FILE, index=False, encoding="utf-8")
    other_asian.to_csv(OTHER_ASIAN_OUTPUT_FILE, index=False, encoding="utf-8")

    # STEP 6 - PRINT DETAILED SUMMARY
    print("===== ASIAN COMPANIES CLEANUP SUMMARY =====")
    print(f"Total Asian companies processed: {len(df)}")
    print(f"Companies without websites removed: {companies_removed}")
    print(f"\nCompanies WITH websites by country:")

    for country in ["China", "Taiwan", "Hong Kong", "Korea", "Vietnam", "Singapore", "Japan"]:
        count = len(df_with_websites[df_with_websites['Country'] == country])
        print(f"  {country}: {count}")

    print(f"\nJapanese companies saved to: {JAPAN_OUTPUT_FILE}")
    print(f"Other Asian companies saved to: {OTHER_ASIAN_OUTPUT_FILE}")
    print("=" * 45)

if __name__ == "__main__":
    main()
