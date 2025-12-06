
import pandas as pd
import sys

file_path = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv"

def analyze_data_final():
    """
    Reads and analyzes the CSV, reporting on total entries, unique companies,
    and the state of LinkedIn URL columns.
    """
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')
    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        sys.exit(1)

    # --- Column Names ---
    company_name_col = 'Company Name'
    company_linkedin_col = 'LinkedIn (company)'
    individual_linkedin_col = 'LinkedIn (individual)'

    # --- Perform Full Analysis ---
    total_entries = len(df)
    
    # Unique Companies
    unique_companies = df[company_name_col].nunique() if company_name_col in df.columns else 0

    # Fill NaN values for URL columns
    df[company_linkedin_col] = df[company_linkedin_col].fillna('')
    df[individual_linkedin_col] = df[individual_linkedin_col].fillna('')

    # Counts for different URL types
    num_company_links = df[df[company_linkedin_col].str.strip() != ''].shape[0]
    num_individual_links = df[df[individual_linkedin_col].str.strip() != ''].shape[0]
    num_both_missing = df[(df[company_linkedin_col] == '') & (df[individual_linkedin_col] == '')].shape[0]
    
    # Count actionable rows (company link exists, but industry is blank)
    if 'Industry' in df.columns:
        df['Industry'] = df['Industry'].fillna('')
        actionable_rows = df[(df[company_linkedin_col] != '') & (df['Industry'] == '')]
        num_to_fill = len(actionable_rows)
    else:
        # If no 'Industry' column, we can't determine who to fill
        num_to_fill = 0 

    # --- Report Findings ---
    print("--- Final Analysis of complete list.csv ---")
    print(f"Total number of rows (entries):         {total_entries}")
    print(f"Total number of unique companies:       {unique_companies}")
    print("-" * 45)
    print(f"Entries with a 'LinkedIn (company)' URL:      {num_company_links}")
    print(f"Entries with a 'LinkedIn (individual)' URL:  {num_individual_links}")
    print(f"Entries with NO LinkedIn URL of any kind:   {num_both_missing}")
    print("-" * 45)
    print(f"Companies needing 'Industry' filled:        {num_to_fill}")

if __name__ == "__main__":
    analyze_data_final()
