"""
Synchronize and Balance CES 2026 Data Files
Creates Chain of Custody with master_row_id across all files
"""

import pandas as pd
import csv
import re

# Paths
DATA_DIR = '/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/CES 2026 /'

def to_snake_case(col):
    cleaned = re.sub(r'[.\(\)\[\]\{\}:"]', '', str(col))
    cleaned = re.sub(r'[\s\-]+', '_', cleaned)
    cleaned = cleaned.lower().strip('_')
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned

def save_csv(df, filepath):
    df.columns = [to_snake_case(c) for c in df.columns]
    df.to_csv(filepath, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)

print("=" * 60)
print("SYNCHRONIZING CES 2026 DATA FILES")
print("=" * 60)

# ============================================================
# STEP 1: Load Master and Create IDs
# ============================================================
print("\n[1] Loading Master File...")
master_path = DATA_DIR + 'clean_2. Complete list.csv'
master = pd.read_csv(master_path, encoding='utf-8')
print(f"    Rows: {len(master)}")

# Find company name column
company_col = None
for col in master.columns:
    if 'company' in col.lower() or 'exhibitor' in col.lower():
        company_col = col
        break

if not company_col:
    company_col = master.columns[0]
print(f"    Company column: {company_col}")

# Create master_row_id (1 to N)
master['master_row_id'] = range(1, len(master) + 1)

# Create dictionary {company_name: master_row_id}
master_dict = {}
for idx, row in master.iterrows():
    name = str(row[company_col]).strip().lower()
    master_dict[name] = row['master_row_id']

print(f"    Dictionary size: {len(master_dict)}")

# ============================================================
# STEP 2: Process Geo-Files (Asian & N Asian)
# ============================================================
print("\n[2] Processing Geo-Files...")

# Load Asian
asian_path = DATA_DIR + 'clean_3. Asian comps.csv'
asian = pd.read_csv(asian_path, encoding='utf-8')
print(f"    Asian comps: {len(asian)} rows")

# Load N Asian
n_asian_path = DATA_DIR + 'clean_4. N Asian.csv'
n_asian = pd.read_csv(n_asian_path, encoding='utf-8')
print(f"    N Asian: {len(n_asian)} rows")

# Find company columns in geo files
asian_company_col = None
for col in asian.columns:
    if 'company' in col.lower() or 'exhibitor' in col.lower():
        asian_company_col = col
        break
if not asian_company_col:
    asian_company_col = asian.columns[0]

n_asian_company_col = None
for col in n_asian.columns:
    if 'company' in col.lower() or 'exhibitor' in col.lower():
        n_asian_company_col = col
        break
if not n_asian_company_col:
    n_asian_company_col = n_asian.columns[0]

# Map IDs to existing rows
def map_id(name, master_dict):
    return master_dict.get(str(name).strip().lower(), None)

asian['master_row_id'] = asian[asian_company_col].apply(lambda x: map_id(x, master_dict))
n_asian['master_row_id'] = n_asian[n_asian_company_col].apply(lambda x: map_id(x, master_dict))

# Find which IDs are covered
asian_ids = set(asian['master_row_id'].dropna().astype(int).tolist())
n_asian_ids = set(n_asian['master_row_id'].dropna().astype(int).tolist())
covered_ids = asian_ids.union(n_asian_ids)
all_ids = set(range(1, len(master) + 1))
missing_ids = all_ids - covered_ids

print(f"    Covered IDs: {len(covered_ids)}")
print(f"    Missing IDs: {len(missing_ids)}")

# Get missing companies from master
missing_companies = master[master['master_row_id'].isin(missing_ids)].copy()

# Split 50/50
half = len(missing_companies) // 2
first_half = missing_companies.iloc[:half]
second_half = missing_companies.iloc[half:]

print(f"    Appending {len(first_half)} to Asian")
print(f"    Appending {len(second_half)} to N Asian")

# Prepare columns for appending
# Asian columns
asian_append = pd.DataFrame()
asian_append[asian_company_col] = first_half[company_col].values
asian_append['master_row_id'] = first_half['master_row_id'].values

# N Asian columns
n_asian_append = pd.DataFrame()
n_asian_append[n_asian_company_col] = second_half[company_col].values
n_asian_append['master_row_id'] = second_half['master_row_id'].values

# Append
asian = pd.concat([asian, asian_append], ignore_index=True)
n_asian = pd.concat([n_asian, n_asian_append], ignore_index=True)

print(f"    New Asian count: {len(asian)}")
print(f"    New N Asian count: {len(n_asian)}")

# ============================================================
# STEP 3: Process Funnel Files
# ============================================================
print("\n[3] Processing Funnel Files...")

secret_id_counter = 8000
total_secret_ids = 0

funnel_files = [
    ('clean_5. Category Fit.csv', 'company_name'),
    ('clean_6. Relevant after scrutinizing.csv', 'company_name'),
    ('clean_7. Final list (HML).csv', 'company'),
]

for filename, expected_col in funnel_files:
    filepath = DATA_DIR + filename
    df = pd.read_csv(filepath, encoding='utf-8')
    
    # Find company column
    company_col_funnel = None
    for col in df.columns:
        if 'company' in col.lower():
            company_col_funnel = col
            break
    if not company_col_funnel:
        company_col_funnel = df.columns[0]
    
    # Map IDs
    ids = []
    file_secret_count = 0
    for name in df[company_col_funnel]:
        mapped_id = map_id(name, master_dict)
        if mapped_id:
            ids.append(int(mapped_id))
        else:
            ids.append(secret_id_counter)
            secret_id_counter += 1
            file_secret_count += 1
    
    df['master_row_id'] = ids
    total_secret_ids += file_secret_count
    
    # Save
    save_csv(df, filepath)
    print(f"    {filename}: {len(df)} rows, {file_secret_count} secret IDs")

# ============================================================
# STEP 4: Save Geo & Master Files
# ============================================================
print("\n[4] Saving Files...")

save_csv(master, master_path)
print(f"    Saved: clean_2. Complete list.csv")

save_csv(asian, asian_path)
print(f"    Saved: clean_3. Asian comps.csv")

save_csv(n_asian, n_asian_path)
print(f"    Saved: clean_4. N Asian.csv")

# ============================================================
# STEP 5: Final Report
# ============================================================
print("\n" + "=" * 60)
print("FINAL REPORT")
print("=" * 60)
print(f"Master count:           {len(master)}")
print(f"Asian + N Asian count:  {len(asian)} + {len(n_asian)} = {len(asian) + len(n_asian)}")
print(f"Secret IDs generated:   {total_secret_ids} (range: 8000-{secret_id_counter-1})")
print("=" * 60)
print("✓ SYNCHRONIZATION COMPLETE!")
