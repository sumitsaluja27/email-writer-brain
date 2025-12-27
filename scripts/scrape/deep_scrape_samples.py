"""
Deep Scrape Sample Companies - Comprehensive Foundation Builder

Scrapes ALL pages from sample companies using multiple methods:
1. crawl4ai (browser-based, handles JavaScript)
2. Direct HTTP + BeautifulSoup (fallback)

Pages to scrape per company:
- Homepage
- About/Company
- Products
- Solutions  
- Services
- Industries
- Use Cases / Case Studies
- Partners

Output:
- company_profiles_v2/{type}/{company}/raw/*.txt (raw text per page)
- company_profiles_v2/{type}/{company}/profile.json (structured summary)
"""

import pandas as pd
import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Using direct HTTP scraping (crawl4ai has Python 3.9 compatibility issues)
CRAWL4AI_AVAILABLE = False

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

# Page patterns to look for
PAGE_PATTERNS = {
    'about': ['/about', '/company', '/who-we-are', '/our-story', '/our-company'],
    'products': ['/products', '/product', '/hardware', '/devices', '/cameras', '/solutions/products'],
    'solutions': ['/solutions', '/solution', '/offerings', '/what-we-do'],
    'services': ['/services', '/service', '/support'],
    'industries': ['/industries', '/industry', '/sectors', '/markets', '/verticals', '/who-we-serve'],
    'use_cases': ['/use-cases', '/case-studies', '/customers', '/success-stories', '/resources'],
    'partners': ['/partners', '/partner', '/integrations', '/ecosystem']
}


def scrape_with_requests(url, timeout=30):
    """Direct HTTP scraping with BeautifulSoup."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove script, style, nav, footer
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
                tag.decompose()
            
            # Get title
            title = soup.title.string if soup.title else ""
            
            # Get main content
            main = soup.find('main') or soup.find('article') or soup.find('body')
            text = main.get_text(separator='\n', strip=True) if main else soup.get_text(separator='\n', strip=True)
            
            # Clean up
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            return {
                'title': title,
                'content': clean_text[:50000],  # Limit to 50KB
                'success': True
            }
    except Exception as e:
        return {'title': '', 'content': '', 'success': False, 'error': str(e)}
    
    return {'title': '', 'content': '', 'success': False}


def scrape_with_crawl4ai(url, timeout=60):
    """Browser-based scraping with crawl4ai."""
    if not CRAWL4AI_AVAILABLE:
        return scrape_with_requests(url, timeout)
    
    try:
        crawler = WebCrawler()
        crawler.warmup()
        result = crawler.run(url=url)
        
        if result.success:
            return {
                'title': result.metadata.get('title', ''),
                'content': result.markdown[:50000],
                'success': True
            }
    except Exception as e:
        pass
    
    # Fallback to requests
    return scrape_with_requests(url, timeout)


def find_page_urls(base_url, content):
    """Find URLs for different page types from homepage content."""
    found_urls = {'homepage': base_url}
    base_domain = urlparse(base_url).netloc
    
    # Parse links from content
    try:
        soup = BeautifulSoup(requests.get(base_url, timeout=20, headers={
            'User-Agent': 'Mozilla/5.0'
        }).text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only same domain
            if urlparse(full_url).netloc != base_domain:
                continue
            
            # Check against patterns
            for page_type, patterns in PAGE_PATTERNS.items():
                if page_type not in found_urls:
                    for pattern in patterns:
                        if pattern in href.lower():
                            found_urls[page_type] = full_url
                            break
    except:
        pass
    
    # Add standard URLs if not found
    for page_type, patterns in PAGE_PATTERNS.items():
        if page_type not in found_urls:
            # Try first pattern
            test_url = urljoin(base_url, patterns[0])
            found_urls[page_type] = test_url
    
    return found_urls


def extract_structured_profile(company_name, all_content, customer_type, product_category, assessment):
    """Use LLM to extract structured profile from all scraped content."""
    
    combined = "\n\n---\n\n".join([f"[{page.upper()}]\n{content[:5000]}" for page, content in all_content.items() if content])
    
    prompt = f"""Analyze this company's website content and extract a structured profile.

COMPANY: {company_name}
KNOWN INFO: 
- Customer Type: {customer_type}
- Product Category: {product_category}
- Assessment: {assessment}

WEBSITE CONTENT:
{combined[:15000]}

Extract the following in JSON format:
{{
    "company_name": "{company_name}",
    "what_they_do": "Clear 2-3 sentence description of their core business",
    "business_model": "How they make money (manufacturer/platform/service/retail)",
    "products_they_make": ["list of products they manufacture or develop"],
    "products_they_sell": ["list of products they sell but may not make"],
    "services_they_offer": ["list of services"],
    "who_they_sell_to": ["target customers/buyers"],
    "industries_served": ["industries they serve"],
    "key_differentiators": ["what makes them unique"],
    "technology_focus": ["key technologies they use or develop"],
    "company_size_signals": "any indicators of company size",
    "partnership_potential": "How could they work with an ODM manufacturer"
}}

JSON only:"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=120)
        
        if resp.status_code == 200:
            result = resp.json().get("response", "{}")
            return json.loads(result)
    except Exception as e:
        print(f"    LLM error: {e}")
    
    return {"error": "Failed to extract profile"}


def scrape_company(row, output_dir):
    """Deep scrape a single company."""
    company_name = row['Company Name']
    website = row['Website']
    industry = row['Industry']
    product_category = row['Product relevance']
    assessment = row['My Assessment']
    
    # Determine customer type from assessment
    if 'End User' in assessment or 'USES' in assessment or 'BUYS' in assessment:
        customer_type = 'end_user'
    else:
        customer_type = 'odm_customer'
    
    # Create directory
    clean_name = re.sub(r'[^\w\s-]', '', company_name).replace(' ', '_').lower()
    company_dir = os.path.join(output_dir, customer_type, clean_name)
    raw_dir = os.path.join(company_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING: {company_name}")
    print(f"Website: {website}")
    print(f"Type: {customer_type}")
    print(f"{'='*60}")
    
    # Normalize URL
    if not website.startswith('http'):
        website = 'https://' + website
    
    # First scrape homepage
    print("  [1/8] Homepage...", end=' ')
    homepage_result = scrape_with_crawl4ai(website)
    if homepage_result['success']:
        print(f"✓ ({len(homepage_result['content'])} chars)")
    else:
        print("✗ Failed, trying HTTP...")
        homepage_result = scrape_with_requests(website)
        if homepage_result['success']:
            print(f"    ✓ HTTP fallback ({len(homepage_result['content'])} chars)")
    
    # Save homepage
    with open(os.path.join(raw_dir, 'homepage.txt'), 'w') as f:
        f.write(f"URL: {website}\n")
        f.write(f"Title: {homepage_result.get('title', '')}\n\n")
        f.write(homepage_result.get('content', ''))
    
    # Find other page URLs
    page_urls = find_page_urls(website, homepage_result.get('content', ''))
    
    all_content = {'homepage': homepage_result.get('content', '')}
    
    # Scrape other pages
    page_names = ['about', 'products', 'solutions', 'services', 'industries', 'use_cases', 'partners']
    
    for i, page_type in enumerate(page_names, 2):
        print(f"  [{i}/8] {page_type.title()}...", end=' ')
        
        url = page_urls.get(page_type)
        if not url:
            print("✗ No URL found")
            continue
        
        result = scrape_with_requests(url, timeout=20)
        
        if result['success'] and len(result['content']) > 200:
            print(f"✓ ({len(result['content'])} chars)")
            all_content[page_type] = result['content']
            
            # Save
            with open(os.path.join(raw_dir, f'{page_type}.txt'), 'w') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Title: {result.get('title', '')}\n\n")
                f.write(result['content'])
        else:
            print(f"✗ ({result.get('error', 'No content')})")
    
    # Extract structured profile
    print("\n  Extracting structured profile with LLM...")
    profile = extract_structured_profile(
        company_name, all_content, customer_type, product_category, assessment
    )
    
    # Add metadata
    profile['_metadata'] = {
        'website': website,
        'industry': industry,
        'product_category': product_category,
        'customer_type': customer_type,
        'original_assessment': assessment,
        'scraped_at': datetime.now().isoformat(),
        'pages_scraped': list(all_content.keys())
    }
    
    # Save profile
    with open(os.path.join(company_dir, 'profile.json'), 'w') as f:
        json.dump(profile, f, indent=2)
    
    # Create summary text file
    with open(os.path.join(company_dir, 'summary.txt'), 'w') as f:
        f.write(f"COMPANY: {company_name}\n")
        f.write(f"TYPE: {customer_type.upper()}\n")
        f.write(f"PRODUCT CATEGORY: {product_category}\n")
        f.write(f"INDUSTRY: {industry}\n\n")
        f.write(f"WHAT THEY DO:\n{profile.get('what_they_do', 'N/A')}\n\n")
        f.write(f"BUSINESS MODEL:\n{profile.get('business_model', 'N/A')}\n\n")
        f.write(f"PRODUCTS THEY MAKE:\n{', '.join(profile.get('products_they_make', []))}\n\n")
        f.write(f"PRODUCTS THEY SELL:\n{', '.join(profile.get('products_they_sell', []))}\n\n")
        f.write(f"WHO THEY SELL TO:\n{', '.join(profile.get('who_they_sell_to', []))}\n\n")
        f.write(f"PARTNERSHIP POTENTIAL:\n{profile.get('partnership_potential', 'N/A')}\n")
    
    total_content = sum(len(c) for c in all_content.values())
    print(f"\n  ✓ Complete! {len(all_content)} pages, {total_content:,} chars total")
    
    return {
        'company': company_name,
        'type': customer_type,
        'pages_scraped': len(all_content),
        'total_chars': total_content,
        'profile_extracted': 'error' not in profile
    }


def main():
    print("="*70)
    print("DEEP SCRAPE SAMPLE COMPANIES - BUILDING FOUNDATION")
    print(f"Started: {datetime.now()}")
    print("="*70)
    
    # Load sample companies
    df = pd.read_csv('data/Companies/sample_companies_for_review.csv')
    print(f"\nLoaded {len(df)} companies to scrape")
    
    # Output directory
    output_dir = 'data/company_profiles_v2'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'odm_customer'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'end_user'), exist_ok=True)
    
    # Scrape each company
    results = []
    for idx, row in df.iterrows():
        try:
            result = scrape_company(row, output_dir)
            results.append(result)
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append({
                'company': row['Company Name'],
                'type': 'unknown',
                'pages_scraped': 0,
                'total_chars': 0,
                'profile_extracted': False,
                'error': str(e)
            })
        
        time.sleep(1)  # Be nice to servers
    
    # Summary
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    
    results_df = pd.DataFrame(results)
    print(f"\nTotal companies: {len(results_df)}")
    print(f"Successful profiles: {results_df['profile_extracted'].sum()}")
    print(f"Total pages scraped: {results_df['pages_scraped'].sum()}")
    print(f"Total content: {results_df['total_chars'].sum():,} chars")
    
    # By type
    print("\nBy customer type:")
    print(results_df.groupby('type')['company'].count())
    
    # Save results
    results_df.to_csv('data/Companies/deep_scrape_results.csv', index=False)
    print(f"\nResults saved to: data/Companies/deep_scrape_results.csv")
    print(f"Profiles saved to: {output_dir}/")


if __name__ == "__main__":
    main()
