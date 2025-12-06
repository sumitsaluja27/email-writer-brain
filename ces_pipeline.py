#!/usr/bin/env python3
"""
CES 2026 Company Analysis - Master Pipeline
============================================

This is the MASTER script that runs the entire CES analysis workflow.

WORKFLOW:
    Stage 1: Categorize companies by data availability
    Stage 2: Enrich with website scraping
    Stage 3: RAG matching against Rapidise products
    Stage 4: Enrich matched companies (LinkedIn, Country)
    Stage 5: Export clean product-specific CSVs

USAGE:
    # Run entire pipeline
    python ces_pipeline.py --all
    
    # Run specific stage
    python ces_pipeline.py --stage 1
    python ces_pipeline.py --stage 2
    python ces_pipeline.py --stage 3
    
    # Skip to enrichment of final files
    python ces_pipeline.py --stage 4
"""

import subprocess
import sys
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data" / "Companies"

# Input/Output files for each stage
FILES = {
    "input": DATA_DIR / "CES 2026_non_asian_validated_CLEAN.csv",
    "categorized": DATA_DIR / "CES_2026_CATEGORIZED.csv",
    "enriched": DATA_DIR / "CES_2026_ENRICHED.csv",
    "rag_matched": DATA_DIR / "CES_2026_RAG_MATCHED.csv",
    # Final clean files
    "dashcam": DATA_DIR / "CES_2026_DASHCAM_CLEAN.csv",
    "in_cabin": DATA_DIR / "CES_2026_IN_CABIN_CLEAN.csv",
    "ip_camera": DATA_DIR / "CES_2026_IP_CAMERA_CLEAN.csv",
    "body_cam": DATA_DIR / "CES_2026_BODY_CAM_CLEAN.csv",
    "beacon": DATA_DIR /"CES_2026_BEACON_CLEAN.csv",
}

# Core scripts
SCRIPTS = {
    "categorize": SRC_DIR / "categorize_companies.py",
    "enrich": SRC_DIR / "enrich_with_crawl4ai.py",
    "rag_match": SRC_DIR / "find_relevant_companies.py",
    "enrich_final": BASE_DIR / "enrich_companies.py",
}

def run_script(name, script_path, description):
    """Run a Python script and handle errors"""
    print("\n" + "="*80)
    print(f"STAGE: {name}")
    print(f"Description: {description}")
    print("="*80)
    
    if not script_path.exists():
        print(f"❌ Error: Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            check=True,
            capture_output=False
        )
        print(f"✅ {name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed with error code {e.returncode}")
        return False

def stage_1_categorize():
    """Stage 1: Categorize companies by data availability"""
    return run_script(
        "Stage 1 - Categorization",
        SCRIPTS["categorize"],
        "Categorize companies into tiers based on available data (Website, LinkedIn, Summary)"
    )

def stage_2_enrich():
    """Stage 2: Enrich with website scraping"""
    return run_script(
        "Stage 2 - Enrichment",
        SCRIPTS["enrich"],
        "Scrape company websites to extract descriptions and validate data"
    )

def stage_3_rag_match():
    """Stage 3: RAG matching"""
    return run_script(
        "Stage 3 - RAG Matching",
        SCRIPTS["rag_match"],
        "Match companies against Rapidise product RAG databases"
    )

def stage_4_enrich_final():
    """Stage 4: Enrich final matched companies"""
    print("\n" + "="*80)
    print("STAGE 4: Enrich Final Company Lists")
    print("="*80)
    
    product_files = [
        ("Body Cam", FILES["body_cam"]),
        ("Dashcam", FILES["dashcam"]),
        ("Beacon", FILES["beacon"]),
        ("IP Camera", FILES["ip_camera"]),
        ("In-Cabin", FILES["in_cabin"]),
    ]
    
    for product_name, file_path in product_files:
        if not file_path.exists():
            print(f"⚠️  Skipping {product_name} - file not found")
            continue
        
        enriched_path = file_path.parent / file_path.name.replace("_CLEAN.csv", "_ENRICHED.csv")
        
        print(f"\nEnriching: {product_name}")
        try:
            subprocess.run(
                [sys.executable, str(SCRIPTS["enrich_final"]), str(file_path), str(enriched_path)],
                cwd=str(BASE_DIR),
                check=True
            )
            print(f"  ✅ {product_name} enriched")
        except subprocess.CalledProcessError:
            print(f"  ❌ {product_name} enrichment failed")
    
    return True

def run_full_pipeline():
    """Run the complete pipeline"""
    print("="*80)
    print("CES 2026 ANALYSIS - FULL PIPELINE")
    print("="*80)
    
    stages = [
        ("Categorization", stage_1_categorize),
        ("Enrichment", stage_2_enrich),
        ("RAG Matching", stage_3_rag_match),
        ("Final Enrichment", stage_4_enrich_final),
    ]
    
    for stage_name, stage_func in stages:
        if not stage_func():
            print(f"\n❌ Pipeline stopped at: {stage_name}")
            return False
    
    print("\n" + "="*80)
    print("✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nFinal outputs:")
    for product, file_path in [(k, v) for k, v in FILES.items() if "CLEAN" in str(v)]:
        if file_path.exists():
            print(f"  ✅ {file_path.name}")
    
    return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CES 2026 Analysis Pipeline")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], help="Run specific stage")
    
    args = parser.parse_args()
    
    if args.all:
        run_full_pipeline()
    elif args.stage == 1:
        stage_1_categorize()
    elif args.stage == 2:
        stage_2_enrich()
    elif args.stage == 3:
        stage_3_rag_match()
    elif args.stage == 4:
        stage_4_enrich_final()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
