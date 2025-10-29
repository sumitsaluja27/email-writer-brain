import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

file_path = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv"

def process_companies_two_pass():
    """
    Performs a two-pass operation:
    1. Finds/fixes LinkedIn company URLs from company websites for entries with missing industries.
    2. Scrapes industries from all available LinkedIn company URLs for entries with missing industries.
    """
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')
    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
        return

    # --- Column Definitions ---
    company_linkedin_col = 'LinkedIn (company)'
    industry_col = 'Industry'
    company_name_col = 'Company Name'
    website_col = 'Website'

    # Ensure columns exist and fill NaNs
    if industry_col not in df.columns: df[industry_col] = ''
    df[industry_col] = df[industry_col].fillna('')
    df[company_linkedin_col] = df[company_linkedin_col].fillna('')
    df[website_col] = df[website_col].fillna('')

    # --- Pass 1: Find/Fix LinkedIn URLs from Websites ---
    print("\n--- Pass 1: Finding/Fixing LinkedIn URLs from Websites ---")
    # Target rows where industry is not filled AND LinkedIn (company) is missing/invalid
    target_for_linkedin_fix = df[
        (df[industry_col].str.strip() == '') &
        (~df[company_linkedin_col].str.contains('linkedin.com/company/', na=False))
    ].copy()

    if target_for_linkedin_fix.empty:
        print("No companies found needing LinkedIn URL fixes from websites.")
    else:
        print(f"Found {len(target_for_linkedin_fix)} companies to check for LinkedIn URL fixes.")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        urls_fixed_in_pass1 = 0
        for index, row in target_for_linkedin_fix.iterrows():
            company_name = row[company_name_col]
            website_url = row[website_col]

            print(f"  Processing ({target_for_linkedin_fix.index.get_loc(index) + 1}/{len(target_for_linkedin_fix)}): {company_name}")

            if not website_url.strip() or not website_url.startswith('http'):
                print(f"    -> Skipping, invalid website URL: '{website_url}'")
                continue

            try:
                time.sleep(1) # Be respectful
                response = requests.get(website_url, headers=headers, timeout=20)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                linkedin_anchor = soup.find('a', href=lambda href: href and 'linkedin.com/company' in href)
                
                if linkedin_anchor:
                    found_url = linkedin_anchor['href']
                    found_url = urljoin(website_url, found_url)
                    
                    print(f"    -> Found LinkedIn URL: {found_url}")
                    df.loc[index, company_linkedin_col] = found_url
                    urls_fixed_in_pass1 += 1
                else:
                    print(f"    -> No LinkedIn company link found on website.")

            except requests.exceptions.RequestException as e:
                print(f"    -> Could not fetch website {website_url}. Error: {e}")
            except Exception as e:
                print(f"    -> An unexpected error occurred: {e}")
        print(f"Pass 1 complete. Found and updated {urls_fixed_in_pass1} LinkedIn URLs.\n")

    # --- Pass 2: Scrape Industries from LinkedIn URLs ---
    print("--- Pass 2: Scraping Industries from LinkedIn URLs ---")
    # Target rows where company LinkedIn exists AND industry is empty
    target_for_industry_scrape = df[
        (df[company_linkedin_col].str.strip() != '') &
        (df[industry_col].str.strip() == '')
    ].copy()

    if target_for_industry_scrape.empty:
        print("No companies found needing industry scraping. Exiting.")
    else:
        print(f"Found {len(target_for_industry_scrape)} companies to process for industry.")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        industries_found_in_pass2 = 0
        for index, row in target_for_industry_scrape.iterrows():
            company_name = row[company_name_col]
            url = row[company_linkedin_col]

            print(f"  Processing ({target_for_industry_scrape.index.get_loc(index) + 1}/{len(target_for_industry_scrape)}): {company_name}")

            if not url.startswith('http'):
                print(f"    -> Skipping invalid URL: {url}")
                continue

            try:
                time.sleep(1) # Be respectful to the server
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                industry_dt = soup.find('dt', string=lambda t: t and 'industry' in t.lower())
                found_industry = None
                if industry_dt:
                    industry_dd = industry_dt.find_next_sibling('dd')
                    if industry_dd:
                        found_industry = industry_dd.get_text(strip=True)
                
                if found_industry:
                    print(f"    -> Found Industry: {found_industry}")
                    df.loc[index, industry_col] = found_industry
                    industries_found_in_pass2 += 1
                else:
                    print(f"    -> Industry not found on page.")

            except requests.exceptions.RequestException as e:
                print(f"    -> Could not fetch URL {url}. Error: {e}")
            except Exception as e:
                print(f"    -> An unexpected error occurred: {e}")
        print(f"Pass 2 complete. Found and updated {industries_found_in_pass2} industries.\n")

    # --- Save Results ---
    print("--- Saving Final Results ---")
    print(f"Saving updated data back to {file_path}...")
    try:
        df.to_csv(file_path, index=False)
        print("File saved successfully.")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    process_companies_two_pass()