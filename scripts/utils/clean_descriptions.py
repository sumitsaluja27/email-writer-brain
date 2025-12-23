"""
Clean Description Data
- Removes markdown formatting (images, links)
- Removes CSS/HTML/JavaScript garbage
- Extracts clean text only
- Updates files IN-PLACE
"""

import pandas as pd
import re

# Files to clean
FILES = [
    'data/Companies/unique_companies_list.csv',
    'data/Companies/relevant_companies.csv'
]

def clean_description(text):
    """Remove markdown, HTML, CSS garbage from description."""
    if pd.isna(text) or text == '':
        return ''
    
    text = str(text)
    
    # Remove "Title: ... URL Source: ..." header
    text = re.sub(r'^Title:\s*.*?URL Source:\s*\S+\s*', '', text, flags=re.IGNORECASE)
    
    # Remove "Markdown Content:" prefix
    text = re.sub(r'Markdown Content:\s*', '', text, flags=re.IGNORECASE)
    
    # Remove image markdown: ![Image X: ...](...)
    text = re.sub(r'!\[Image[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'!\[Image[^\]]*\]', '', text)
    
    # Remove links markdown: [text](url) - keep the text
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove empty/broken links
    text = re.sub(r'\[[^\]]*\]\(', '', text)
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove CSS/JavaScript blocks
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove markdown headers (####, ###, etc)
    text = re.sub(r'#{1,6}\s*', '', text)
    
    # Remove special characters and excessive punctuation
    text = re.sub(r'[=]{2,}', '', text)
    text = re.sub(r'[-]{2,}', ' ', text)
    text = re.sub(r'[*]{1,}', '', text)
    
    # Remove navigation patterns
    text = re.sub(r'Skip to (main )?content', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Skip to footer', '', text, flags=re.IGNORECASE)
    text = re.sub(r'View Sitemap', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\* Home \*', '', text)
    text = re.sub(r'Home ›', '', text)
    
    # Remove "Home" repeated patterns
    text = re.sub(r'\bHome\b\s*\*?\s*', '', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove if too short (likely garbage)
    if len(text) < 20:
        return ''
    
    # Truncate to reasonable length
    if len(text) > 500:
        text = text[:500] + '...'
    
    return text

def main():
    print("=" * 60)
    print("CLEANING DESCRIPTIONS")
    print("=" * 60)
    
    for file_path in FILES:
        try:
            df = pd.read_csv(file_path)
            print(f"\n🔧 Cleaning: {file_path}")
            
            if 'Description' in df.columns:
                df['Description'] = df['Description'].apply(clean_description)
                df.to_csv(file_path, index=False, encoding='utf-8')
                print(f"   ✅ Cleaned {len(df)} rows")
            else:
                print(f"   ⚠️  No Description column")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

if __name__ == "__main__":
    main()
