#!/usr/bin/env python3
"""Create test dataset with 50 companies"""
import sys
sys.path.insert(0, '/Users/apple/Library/Python/3.9/lib/python/site-packages')

import pandas as pd

df = pd.read_csv('data/Companies/CES 2026_non_asian_validated_CLEAN.csv')
print(f'Total companies: {len(df)}')

test_df = df.head(50)
test_df.to_csv('data/Companies/CES_TEST_50.csv', index=False)
print(f'✅ Test file created: CES_TEST_50.csv with {len(test_df)} companies')
