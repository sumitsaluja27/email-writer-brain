#!/usr/bin/env python3
"""
Rapidise Company Classification Pipeline - Main Entry Point
============================================================

This is the main entry point for the consolidated pipeline.

Usage:
    # Run full pipeline
    python main.py --all --input data/Companies/companies.csv
    
    # Run specific operations
    python main.py scrape --company "Samsara" --website "https://samsara.com"
    python main.py classify --input companies.csv
    python main.py build-rag
    python main.py analyze --input classified.csv
    
    # Get help
    python main.py --help
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.consolidated.config import PRODUCTS, SERVICES, ensure_dirs
from scripts.consolidated.pipeline import run_full_pipeline


def cmd_scrape(args):
    """Scrape company websites."""
    from scripts.consolidated.scraper import scrape_company_deep, smart_scrape
    
    if args.company and args.website:
        result = scrape_company_deep(args.company, args.website, args.output)
        print(f"\nScraped {result['total_pages']} pages, {result['total_chars']} chars")
    elif args.url:
        content, method = smart_scrape(args.url)
        print(f"Scraped {len(content)} chars via {method}")
        if args.output:
            with open(args.output, 'w') as f:
                f.write(content)
    elif args.csv:
        import pandas as pd
        from scripts.consolidated.scraper import scrape_companies_batch
        
        df = pd.read_csv(args.csv)
        companies = df.to_dict('records')
        scrape_companies_batch(companies, args.output)


def cmd_classify(args):
    """Classify companies."""
    from scripts.consolidated.classifier import classify_with_rag, classify_companies_batch
    import pandas as pd
    
    if args.company:
        result = classify_with_rag(args.company, args.website or "", args.industry or "")
        print(f"\nResult: {result['classification']} ({result['confidence']:.2f})")
        print(f"Reasoning: {result['reasoning']}")
    
    elif args.input:
        df = pd.read_csv(args.input)
        companies = df.to_dict('records')
        
        results = classify_companies_batch(companies)
        
        for i, result in enumerate(results):
            df.at[i, 'Classification'] = result.get('classification', '')
            df.at[i, 'Confidence'] = result.get('confidence', 0)
        
        output = args.output or args.input.replace('.csv', '_classified.csv')
        df.to_csv(output, index=False)
        print(f"\nSaved: {output}")


def cmd_build_rag(args):
    """Build RAG databases."""
    from scripts.consolidated.rag_builder import build_customer_dna_db, build_rapidise_fit_db
    
    if args.customer_dna or args.all:
        build_customer_dna_db(args.csv)
    
    if args.rapidise_fit or args.all:
        build_rapidise_fit_db()


def cmd_analyze(args):
    """Analyze classification results."""
    from scripts.consolidated.analyzer import (
        generate_classification_report, 
        review_not_relevant, 
        analyze_by_product
    )
    import pandas as pd
    
    df = pd.read_csv(args.input)
    
    if args.report:
        generate_classification_report(df, args.output)
    
    if args.review:
        review_not_relevant(df, args.output)
    
    if args.by_product:
        analyze_by_product(df)


def cmd_profile(args):
    """Create company profiles."""
    from scripts.consolidated.profiler import create_company_profile, create_profiles_from_csv
    
    if args.company and args.website:
        create_company_profile(args.company, args.website, output_dir=args.output)
    
    elif args.csv:
        create_profiles_from_csv(args.csv, args.output)


def main():
    parser = argparse.ArgumentParser(
        description="Rapidise Company Classification Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Full pipeline
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--input", help="Input CSV for full pipeline")
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape websites')
    scrape_parser.add_argument("--company", help="Company name")
    scrape_parser.add_argument("--website", help="Company website")
    scrape_parser.add_argument("--url", help="Single URL to scrape")
    scrape_parser.add_argument("--csv", help="CSV file with companies")
    scrape_parser.add_argument("--output", help="Output directory/file")
    
    # Classify command
    classify_parser = subparsers.add_parser('classify', help='Classify companies')
    classify_parser.add_argument("--company", help="Single company name")
    classify_parser.add_argument("--website", help="Company website")
    classify_parser.add_argument("--industry", help="Company industry")
    classify_parser.add_argument("--input", help="Input CSV file")
    classify_parser.add_argument("--output", help="Output CSV file")
    
    # Build RAG command
    rag_parser = subparsers.add_parser('build-rag', help='Build RAG databases')
    rag_parser.add_argument("--customer-dna", action="store_true", help="Build Customer DNA DB")
    rag_parser.add_argument("--rapidise-fit", action="store_true", help="Build Rapidise Fit DB")
    rag_parser.add_argument("--all", action="store_true", help="Build all databases")
    rag_parser.add_argument("--csv", help="CSV file for Customer DNA")
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze results')
    analyze_parser.add_argument("--input", required=True, help="Input CSV file")
    analyze_parser.add_argument("--report", action="store_true", help="Generate report")
    analyze_parser.add_argument("--review", action="store_true", help="Review classifications")
    analyze_parser.add_argument("--by-product", action="store_true", help="Analyze by product")
    analyze_parser.add_argument("--output", help="Output file")
    
    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Create company profiles')
    profile_parser.add_argument("--company", help="Company name")
    profile_parser.add_argument("--website", help="Company website")
    profile_parser.add_argument("--csv", help="CSV file with companies")
    profile_parser.add_argument("--output", help="Output directory")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_dirs()
    
    # Route to command
    if args.all and args.input:
        run_full_pipeline(args.input)
    elif args.command == 'scrape':
        cmd_scrape(args)
    elif args.command == 'classify':
        cmd_classify(args)
    elif args.command == 'build-rag':
        cmd_build_rag(args)
    elif args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'profile':
        cmd_profile(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
