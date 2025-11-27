import pandas as pd
import numpy as np
import os

# Define absolute paths for input and output files
JAPAN_COMPANIES_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/japanese_companies.csv"
NON_ASIAN_COMPANIES_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/CES 2026_non_asian.csv"
OUTPUT_FILE = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/master_workable_companies.csv"

def create_master_list():
    """
    Loads, processes, and combines Japanese and non-Asian company data
    to create a master workable list.
    """
    # Check if input files exist
    if not os.path.exists(JAPAN_COMPANIES_FILE):
        print(f"Error: Japanese companies file not found at {JAPAN_COMPANIES_FILE}")
        return
    if not os.path.exists(NON_ASIAN_COMPANIES_FILE):
        print(f"Error: Non-Asian companies file not found at {NON_ASIAN_COMPANIES_FILE}")
        return

    # 1. Load Japanese companies and assign category
    japanese_df = pd.read_csv(JAPAN_COMPANIES_FILE)
    japanese_df['Category'] = 'Japanese'
    japanese_count = len(japanese_df)

    # 2. Load and filter non-Asian validated companies
    non_asian_df = pd.read_csv(NON_ASIAN_COMPANIES_FILE)
    
    # Ensure 'Correct_Website' is treated as boolean
    if 'Correct_Website' in non_asian_df.columns:
         non_asian_df['Correct_Website'] = non_asian_df['Correct_Website'].astype(str).str.lower() == 'true'

    # Rename 'LinkedIn URL' to 'LinkedIn_URL' if present
    if 'LinkedIn URL' in non_asian_df.columns:
        non_asian_df.rename(columns={'LinkedIn URL': 'LinkedIn_URL'}, inplace=True)

    workable_non_asian = non_asian_df[
        (non_asian_df['Validation_Status'] == '✅ GOOD') &
        (non_asian_df['Correct_Website'] == True)
    ].copy()

    # Assign categories based on LinkedIn URL presence
    workable_non_asian['LinkedIn_URL'] = workable_non_asian['LinkedIn_URL'].fillna('Not Found')
    
    has_linkedin_mask = (workable_non_asian['LinkedIn_URL'].notna()) & (workable_non_asian['LinkedIn_URL'] != 'Not Found') & (workable_non_asian['LinkedIn_URL'] != '')
    
    workable_non_asian['Category'] = np.where(
        has_linkedin_mask,
        'Website + LinkedIn',
        'Website Only'
    )

    # Count categories for summary
    website_linkedin_count = len(workable_non_asian[workable_non_asian['Category'] == 'Website + LinkedIn'])
    website_only_count = len(workable_non_asian[workable_non_asian['Category'] == 'Website Only'])

    # 3. Combine all categories
    # Ensure columns match for concatenation, fill missing with NaN
    required_columns = [
        'Exhibitor', 'Summary', 'Website', 'LinkedIn_URL', 
        'Country', 'Category', 'Validation_Status'
    ]
    
    # Align columns for both dataframes
    japanese_aligned = japanese_df.reindex(columns=required_columns)
    non_asian_aligned = workable_non_asian.reindex(columns=required_columns)

    master_df = pd.concat([japanese_aligned, non_asian_aligned], ignore_index=True)

    # 4. Keep only specified columns (already done by reindexing) 
    
    # 5. Save the output file
    master_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    # 6. Print summary
    total_workable = len(master_df)
    print("===== MASTER WORKABLE COMPANIES SUMMARY =====")
    print(f"Japanese companies: {japanese_count}")
    print(f"Non-Asian with Website + LinkedIn: {website_linkedin_count}")
    print(f"Non-Asian with Website Only: {website_only_count}")
    print("-" * 45)
    print(f"TOTAL WORKABLE: {total_workable}")
    print(f"\nMaster list saved to: {OUTPUT_FILE}")
    print("=" * 45)


if __name__ == "__main__":
    create_master_list()
