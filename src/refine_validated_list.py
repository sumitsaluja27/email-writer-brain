import pandas as pd
import os
import re

# ───── SETTINGS ─────
INPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_validated.csv"
CLEAN_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian_validated_CLEAN.csv"
REMOVED_OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_asian companies_from non asian.csv"

# ───── KEYWORDS ─────
# Target Countries: China, Korea, Vietnam, Taiwan
# Target Countries (Nouns)
TARGET_COUNTRIES = ["china", "korea", "vietnam", "taiwan", "south korea", "prc", "r.o.c", "hong kong", "hongkong", "hk"]

# Demonyms (Adjectives) - New
DEMONYMS = ["chinese", "korean", "vietnamese", "taiwanese"]

# City Keywords (Expanded list)
CITY_KEYWORDS = [
    # China
    "shenzhen", "xiamen", "dongguan", "hangzhou", "beijing", "shanghai", "guangzhou", 
    "suzhou", "chengdu", "wuhan", "nanjing", "tianjin", "qingdao", "foshan", "zhongshan", 
    "ningbo", "hefei", "changsha", "wuxi", "kunshan", "zhuhai", "jinan", "dalian", 
    "fuzhou", "harbin", "shijiazhuang", "zhengzhou", "changchun", "nanchang", "wenzhou",
    # Taiwan
    "taipei", "taichung", "kaohsiung", "tainan", "hsinchu", "taoyuan", "new taipei", 
    "keelung", "chiayi",
    # Vietnam
    "hanoi", "ho chi minh", "hcmc", "saigon", "danang", "haiphong", "can tho",
    # Korea
    "seoul", "busan", "incheon", "daegu", "daejeon", "gwangju", "suwon", "ulsan", 
    "changwon", "goyang", "yongin", "seongnam", "cheongju", "jeonju",
    # Hong Kong
    "hong kong", "hongkong", "kowloon", "tsim sha tsui", "causeway bay", "wan chai", "new territories"
]

# Province Keywords (New)
PROVINCE_KEYWORDS = [
    "zhejiang", "guangdong", "jiangsu", "shandong", "fujian", "sichuan", "hubei", 
    "hunan", "anhui", "henan", "hebei", "liaoning", "shaanxi", "jiangxi", "yunnan", 
    "guangxi", "shanxi", "guizhou", "jilin", "heilongjiang", "hainan", "gansu", 
    "ningxia", "qinghai", "xinjiang", "tibet", "inner mongolia"
]

def refine_list():
    print(f"Loading input file: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found.")
        return

    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    print(f"Loaded {len(df)} companies.")

    # Ensure columns exist and handle missing values
    if 'Exhibitor' not in df.columns:
        print("Error: 'Exhibitor' column missing.")
        return
    
    df['Exhibitor'] = df['Exhibitor'].fillna('').astype(str)
    df['Exhibitor'] = df['Exhibitor'].fillna('').astype(str)
    df['Summary'] = df['Summary'].fillna('').astype(str)
    
    # Check 'Brief Summary' if it exists
    if 'Brief Summary' in df.columns:
        df['Brief Summary'] = df['Brief Summary'].fillna('').astype(str)
        # Combine Summary and Brief Summary for the check
        df['Full_Summary'] = df['Summary'] + " " + df['Brief Summary']
    else:
        df['Full_Summary'] = df['Summary']

    # 1. Check for City Names in Company Name (Exhibitor)
    # We use word boundaries to avoid partial matches (e.g. "chang" in "exchange")
    # 1. Check for City/Province/Country Names in Company Name (Exhibitor)
    # Combine City, Province, AND Country keywords for the name check
    all_location_keywords = CITY_KEYWORDS + PROVINCE_KEYWORDS + TARGET_COUNTRIES
    location_pattern = '|'.join([rf'\b{re.escape(loc)}\b' for loc in all_location_keywords])
    name_mask = df['Exhibitor'].str.lower().str.contains(location_pattern, regex=True)

    # 2. Check for Country Mentions in Summary
    # Include Demonyms (Chinese, Korean, etc.)
    all_summary_keywords = TARGET_COUNTRIES + DEMONYMS
    summary_pattern = '|'.join([rf'\b{re.escape(word)}\b' for word in all_summary_keywords])
    summary_mask = df['Full_Summary'].str.lower().str.contains(summary_pattern, regex=True)

    # 3. Check the 'Country' Column (New)
    if 'Country' in df.columns:
        df['Country'] = df['Country'].fillna('').astype(str)
        country_col_mask = df['Country'].str.lower().isin(TARGET_COUNTRIES)
    else:
        country_col_mask = pd.Series([False] * len(df), index=df.index)

    # Combine masks: Identify companies to REMOVE
    to_remove_mask = name_mask | summary_mask | country_col_mask

    # Split Data
    removed_df = df[to_remove_mask].copy()
    clean_df = df[~to_remove_mask].copy()

    # Save Files
    print(f"\nSaving {len(removed_df)} removed companies to: {REMOVED_OUTPUT_FILE}")
    removed_df.to_csv(REMOVED_OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"Saving {len(clean_df)} clean companies to: {CLEAN_OUTPUT_FILE}")
    clean_df.to_csv(CLEAN_OUTPUT_FILE, index=False, encoding="utf-8")

    # Summary
    print("\n===== REFINEMENT SUMMARY =====")
    print(f"Original Count: {len(df)}")
    print(f"Removed (Asian): {len(removed_df)}")
    print(f"Cleaned Count:  {len(clean_df)}")
    print("==============================")

if __name__ == "__main__":
    refine_list()
