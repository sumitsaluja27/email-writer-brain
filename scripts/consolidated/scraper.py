"""
Rapidise Company Classification Pipeline - Scraper
===================================================

Consolidated website scraping functionality.
Combines: deep_scrape_samples.py, scrape_companies.py, scrape_company_descriptions.py,
          scrape_raw_language.py, scrape_sample_companies.py, smart_rescraper.py

Methods:
1. Direct HTTP + BeautifulSoup (fast, handles most sites)
2. Jina API (handles JavaScript-heavy sites)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os
from datetime import datetime

try:
    from .config import (
        JINA_API, SCRAPE_TIMEOUT, PAGE_PATTERNS, 
        MAX_CONTENT_PER_PAGE, MAX_TOTAL_CONTENT, PROFILES_DIR
    )
except ImportError:
    # Direct execution
    JINA_API = 'https://r.jina.ai/'
    SCRAPE_TIMEOUT = 30
    MAX_CONTENT_PER_PAGE = 15000
    MAX_TOTAL_CONTENT = 50000
    PAGE_PATTERNS = {
        'about': ['/about', '/company', '/who-we-are'],
        'products': ['/products', '/product', '/hardware'],
        'solutions': ['/solutions', '/platform'],
        'services': ['/services'],
        'industries': ['/industries', '/markets'],
        'use_cases': ['/use-cases', '/case-studies'],
        'partners': ['/partners', '/integrations']
    }


# =============================================================================
# HTTP SCRAPING (BeautifulSoup)
# =============================================================================

def scrape_with_requests(url, timeout=SCRAPE_TIMEOUT):
    """
    Direct HTTP scraping with BeautifulSoup.
    Fast, works for most sites, doesn't require JavaScript.
    """
    if not url:
        return ""
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        # Try HTTPS first
        response = requests.get(url, headers=headers, timeout=timeout, verify=True)
        response.raise_for_status()
    except requests.exceptions.SSLError:
        # Fall back to HTTP
        try:
            http_url = url.replace('https://', 'http://')
            response = requests.get(http_url, headers=headers, timeout=timeout)
            response.raise_for_status()
        except:
            return ""
    except Exception as e:
        return f"Error: {str(e)}"
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove unwanted elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
        tag.decompose()
    
    # Extract text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Limit size
    return text[:MAX_CONTENT_PER_PAGE]


# =============================================================================
# JINA API SCRAPING (JavaScript support)
# =============================================================================

def scrape_with_jina(url, max_chars=MAX_CONTENT_PER_PAGE):
    """
    Scrape website using Jina API.
    Good for JavaScript-heavy sites.
    """
    if not url:
        return ""
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        response = requests.get(
            JINA_API + url, 
            timeout=45, 
            headers={'Accept': 'text/plain'}
        )
        if response.status_code == 200:
            return response.text[:max_chars]
    except Exception as e:
        return f"Error: {str(e)}"
    
    return ""


# =============================================================================
# SMART SCRAPING (Tries multiple methods)
# =============================================================================

def smart_scrape(url, timeout=SCRAPE_TIMEOUT):
    """
    Smart scraping that tries multiple methods.
    1. First try direct HTTP (fast)
    2. Fall back to Jina if direct fails
    """
    # Try direct first
    content = scrape_with_requests(url, timeout)
    
    if content and len(content) > 100 and not content.startswith("Error"):
        return content, "http"
    
    # Fall back to Jina
    content = scrape_with_jina(url)
    
    if content and len(content) > 100 and not content.startswith("Error"):
        return content, "jina"
    
    return "", "failed"


# =============================================================================
# MULTI-PAGE SCRAPING
# =============================================================================

def find_page_urls(base_url, homepage_content):
    """Find URLs for different page types from homepage content."""
    found_urls = {'homepage': base_url}
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    for page_type, patterns in PAGE_PATTERNS.items():
        for pattern in patterns:
            test_url = base + pattern
            # Simple check - we'll validate when actually scraping
            found_urls[page_type] = test_url
            break
    
    return found_urls


def scrape_company_deep(name, website, output_dir=None):
    """
    Deep scrape a company - homepage + all key pages.
    Returns dict with all scraped content.
    """
    result = {
        'company_name': name,
        'website': website,
        'scraped_at': datetime.now().isoformat(),
        'pages': {},
        'total_chars': 0,
        'total_pages': 0
    }
    
    if not website:
        return result
    
    # Normalize URL
    if not website.startswith('http'):
        website = 'https://' + website
    
    print(f"\n{'='*60}")
    print(f"SCRAPING: {name}")
    print(f"Website: {website}")
    print(f"{'='*60}")
    
    # Scrape homepage first
    print("  [1/8] Homepage...", end=" ")
    content, method = smart_scrape(website)
    
    if content and len(content) > 50:
        result['pages']['homepage'] = content
        result['total_chars'] += len(content)
        result['total_pages'] += 1
        print(f"✓ ({len(content)} chars via {method})")
    else:
        print(f"✗ (No content)")
        return result
    
    # Find and scrape other pages
    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    page_num = 2
    for page_type, patterns in PAGE_PATTERNS.items():
        print(f"  [{page_num}/8] {page_type.title()}...", end=" ")
        
        for pattern in patterns:
            test_url = base + pattern
            content, method = smart_scrape(test_url, timeout=20)
            
            if content and len(content) > 100 and not content.startswith("Error"):
                result['pages'][page_type] = content
                result['total_chars'] += len(content)
                result['total_pages'] += 1
                print(f"✓ ({len(content)} chars)")
                break
        else:
            print(f"✗ (No content)")
        
        page_num += 1
        
        # Stop if we have enough content
        if result['total_chars'] > MAX_TOTAL_CONTENT:
            break
    
    print(f"\n  ✓ Complete! {result['total_pages']} pages, {result['total_chars']} chars total")
    
    # Save raw content if output_dir specified
    if output_dir:
        save_scraped_content(result, output_dir)
    
    return result


def save_scraped_content(result, output_dir):
    """Save scraped content to files."""
    company_dir = os.path.join(output_dir, result['company_name'].lower().replace(' ', '_'))
    raw_dir = os.path.join(company_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    for page_type, content in result['pages'].items():
        file_path = os.path.join(raw_dir, f"{page_type}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


# =============================================================================
# BATCH SCRAPING
# =============================================================================

def scrape_companies_batch(companies, output_dir=None, delay=1):
    """
    Scrape multiple companies.
    
    Args:
        companies: List of dicts with 'name' and 'website' keys
        output_dir: Optional directory to save results
        delay: Seconds between requests
    """
    results = []
    
    for i, company in enumerate(companies):
        name = company.get('name', company.get('Company Name', f'Company_{i}'))
        website = company.get('website', company.get('Website', ''))
        
        result = scrape_company_deep(name, website, output_dir)
        results.append(result)
        
        time.sleep(delay)
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape company websites")
    parser.add_argument("--url", help="Single URL to scrape")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--output", help="Output directory")
    
    args = parser.parse_args()
    
    if args.url:
        name = args.company or "Test Company"
        result = scrape_company_deep(name, args.url, args.output)
        print(f"\nResult: {result['total_pages']} pages, {result['total_chars']} chars")
    else:
        # Test with sample
        print("Testing scraper with sample URL...")
        content, method = smart_scrape("https://example.com")
        print(f"Got {len(content)} chars via {method}")
