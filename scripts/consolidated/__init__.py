"""
Rapidise Company Classification Pipeline
=========================================

A consolidated pipeline for:
- Scraping company websites
- Building RAG databases
- Classifying companies by relevance to Rapidise products/services
- Analyzing and exporting results

Usage:
    python -m scripts.consolidated.main --help
    python -m scripts.consolidated.main --all --input companies.csv
"""

from .config import (
    PRODUCTS, SERVICES, 
    COMPANIES_DIR, DATA_DIR, PROFILES_DIR,
    OLLAMA_URL, LLM_MODEL
)

from .scraper import (
    smart_scrape, scrape_company_deep, 
    scrape_with_requests, scrape_with_jina
)

from .rag_builder import (
    build_customer_dna_db, build_rapidise_fit_db,
    query_customer_dna, query_rapidise_fit,
    OllamaEmbed
)

from .classifier import (
    classify_with_rag, classify_by_keywords,
    classify_companies_batch
)

from .data_cleaner import (
    clean_csv, clean_text, clean_company_name,
    validate_company_data
)

from .enricher import (
    enrich_companies_full, enrich_with_scraping,
    enrich_with_classification
)

from .profiler import (
    create_company_profile, create_profiles_from_csv,
    load_profile, list_profiles
)

from .analyzer import (
    review_not_relevant, review_relevant,
    generate_classification_report, analyze_by_product
)

from .pipeline import run_full_pipeline


__version__ = "2.0.0"
__all__ = [
    # Config
    'PRODUCTS', 'SERVICES',
    
    # Scraping
    'smart_scrape', 'scrape_company_deep',
    
    # RAG
    'build_customer_dna_db', 'build_rapidise_fit_db',
    'query_customer_dna', 'query_rapidise_fit',
    
    # Classification
    'classify_with_rag', 'classify_by_keywords',
    
    # Data cleaning
    'clean_csv', 'validate_company_data',
    
    # Enrichment
    'enrich_companies_full',
    
    # Profiling
    'create_company_profile', 'create_profiles_from_csv',
    
    # Analysis
    'generate_classification_report', 'analyze_by_product',
    
    # Pipeline
    'run_full_pipeline'
]
