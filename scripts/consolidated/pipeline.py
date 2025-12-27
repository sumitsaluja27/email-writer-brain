"""
Rapidise Company Classification Pipeline - Main Pipeline
=========================================================

Master pipeline that orchestrates all stages.
Combines: ces_pipeline.py

Stages:
1. Load & Clean data
2. Enrich with scraping
3. Build RAG databases
4. Classify companies
5. Analyze & Review
6. Export final results
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from .config import COMPANIES_DIR, CSV_FILES, ensure_dirs
    from .data_cleaner import clean_csv, validate_company_data
    from .enricher import enrich_companies_full
    from .rag_builder import build_customer_dna_db, build_rapidise_fit_db
    from .classifier import classify_companies_batch
    from .profiler import create_profiles_from_csv
    from .analyzer import generate_classification_report, review_not_relevant
except ImportError:
    # Direct execution - import from current directory
    print("Running in standalone mode")
    COMPANIES_DIR = Path('data/Companies')


# =============================================================================
# PIPELINE STAGES
# =============================================================================

def stage_1_clean(input_csv, output_csv=None):
    """Stage 1: Load and clean data."""
    print("\n" + "=" * 80)
    print("STAGE 1: DATA CLEANING")
    print("=" * 80)
    
    output_csv = output_csv or str(input_csv).replace('.csv', '_clean.csv')
    
    from .data_cleaner import clean_csv, validate_company_data
    import pandas as pd
    
    df = clean_csv(input_csv, output_csv)
    validate_company_data(df)
    
    return output_csv


def stage_2_enrich(input_csv, output_csv=None):
    """Stage 2: Enrich companies with scraping."""
    print("\n" + "=" * 80)
    print("STAGE 2: ENRICHMENT")
    print("=" * 80)
    
    output_csv = output_csv or str(input_csv).replace('.csv', '_enriched.csv')
    
    from .enricher import enrich_companies_full
    
    enrich_companies_full(input_csv, output_csv, ['scrape', 'country'])
    
    return output_csv


def stage_3_build_rag():
    """Stage 3: Build RAG databases."""
    print("\n" + "=" * 80)
    print("STAGE 3: BUILD RAG DATABASES")
    print("=" * 80)
    
    from .rag_builder import build_customer_dna_db, build_rapidise_fit_db
    
    build_customer_dna_db()
    build_rapidise_fit_db()
    
    return True


def stage_4_classify(input_csv, output_csv=None):
    """Stage 4: Classify companies."""
    print("\n" + "=" * 80)
    print("STAGE 4: CLASSIFICATION")
    print("=" * 80)
    
    output_csv = output_csv or str(input_csv).replace('.csv', '_classified.csv')
    
    import pandas as pd
    from .classifier import classify_companies_batch
    
    df = pd.read_csv(input_csv)
    companies = df.to_dict('records')
    
    results = classify_companies_batch(companies, use_rag=True)
    
    # Merge results back
    for i, result in enumerate(results):
        df.at[i, 'Classification'] = result.get('classification', '')
        df.at[i, 'Confidence'] = result.get('confidence', 0)
        df.at[i, 'Products'] = ', '.join(result.get('products', []))
        df.at[i, 'Reasoning'] = result.get('reasoning', '')
    
    df.to_csv(output_csv, index=False)
    print(f"Saved: {output_csv}")
    
    return output_csv


def stage_5_analyze(input_csv, output_dir=None):
    """Stage 5: Analyze results."""
    print("\n" + "=" * 80)
    print("STAGE 5: ANALYSIS")
    print("=" * 80)
    
    import pandas as pd
    from .analyzer import generate_classification_report, review_not_relevant
    
    df = pd.read_csv(input_csv)
    
    output_dir = output_dir or str(Path(input_csv).parent)
    
    generate_classification_report(df, f"{output_dir}/classification_report.json")
    review_not_relevant(df, f"{output_dir}/flagged_for_review.csv")
    
    return True


def stage_6_export(input_csv, output_dir=None):
    """Stage 6: Export final results by product."""
    print("\n" + "=" * 80)
    print("STAGE 6: EXPORT")
    print("=" * 80)
    
    import pandas as pd
    from .analyzer import finalize_csv
    
    df = pd.read_csv(input_csv)
    output_dir = output_dir or str(Path(input_csv).parent)
    
    # Export relevant companies
    relevant = df[df['Classification'] == 'RELEVANT']
    finalize_csv(input_csv, f"{output_dir}/RELEVANT_FINAL.csv")
    
    # Export by product
    products = ['dashcam', 'bodycam', 'ip_camera', 'in_cabin', 'access_control', 'beacon']
    
    for product in products:
        product_df = relevant[relevant['Products'].str.contains(product, na=False, case=False)]
        if len(product_df) > 0:
            product_path = f"{output_dir}/{product.upper()}_companies.csv"
            product_df.to_csv(product_path, index=False)
            print(f"  {product}: {len(product_df)} companies")
    
    return True


# =============================================================================
# FULL PIPELINE
# =============================================================================

def run_full_pipeline(input_csv):
    """Run complete classification pipeline."""
    print("=" * 80)
    print("RAPIDISE CLASSIFICATION PIPELINE")
    print(f"Started: {datetime.now()}")
    print("=" * 80)
    
    # Stage 1: Clean
    clean_csv = stage_1_clean(input_csv)
    
    # Stage 2: Enrich
    enriched_csv = stage_2_enrich(clean_csv)
    
    # Stage 3: Build RAG
    stage_3_build_rag()
    
    # Stage 4: Classify
    classified_csv = stage_4_classify(enriched_csv)
    
    # Stage 5: Analyze
    stage_5_analyze(classified_csv)
    
    # Stage 6: Export
    stage_6_export(classified_csv)
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE!")
    print(f"Finished: {datetime.now()}")
    print("=" * 80)
    
    return classified_csv


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Rapidise Company Classification Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full pipeline
    python pipeline.py --all --input companies.csv
    
    # Run specific stage
    python pipeline.py --stage 1 --input companies.csv
    python pipeline.py --stage 4 --input companies_enriched.csv
    
    # Build RAG databases only
    python pipeline.py --build-rag
        """
    )
    
    parser.add_argument("--input", help="Input CSV file")
    parser.add_argument("--output", help="Output directory or file")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4, 5, 6], 
                        help="Run specific stage")
    parser.add_argument("--build-rag", action="store_true", help="Build RAG databases only")
    
    args = parser.parse_args()
    
    if args.all and args.input:
        run_full_pipeline(args.input)
    
    elif args.build_rag:
        stage_3_build_rag()
    
    elif args.stage and args.input:
        if args.stage == 1:
            stage_1_clean(args.input, args.output)
        elif args.stage == 2:
            stage_2_enrich(args.input, args.output)
        elif args.stage == 3:
            stage_3_build_rag()
        elif args.stage == 4:
            stage_4_classify(args.input, args.output)
        elif args.stage == 5:
            stage_5_analyze(args.input, args.output)
        elif args.stage == 6:
            stage_6_export(args.input, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
