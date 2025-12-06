import pandas as pd
import re

# Test Data from the grep output
data = {
    'Exhibitor': ['Accurate Meditech Inc', 'AidALL Inc.'],
    'Summary': [
        "Accurate Meditech Inc. is a Taiwan-based medtech startup...",
        "AidALL Inc. is a South Korean AI robotics startup..."
    ],
    'Country': ['Unknown', '']
}
df = pd.DataFrame(data)

# Keywords from the script
TARGET_COUNTRIES = ["china", "korea", "vietnam", "taiwan", "south korea", "prc", "r.o.c", "hong kong"]
DEMONYMS = ["chinese", "korean", "vietnamese", "taiwanese"]
all_summary_keywords = TARGET_COUNTRIES + DEMONYMS

# Create Regex
summary_pattern = '|'.join([rf'\b{re.escape(word)}\b' for word in all_summary_keywords])
print(f"Regex Pattern: {summary_pattern}")

# Apply Logic
df['Summary'] = df['Summary'].fillna('').astype(str)
summary_mask = df['Summary'].str.lower().str.contains(summary_pattern, regex=True)

print("\nResults:")
print(df[summary_mask])

print("\nMissed:")
print(df[~summary_mask])
