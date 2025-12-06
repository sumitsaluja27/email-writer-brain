import os
import pandas as pd
from typing import List, Dict, Tuple
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# --- Configuration ---
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
INPUT_FILE = os.path.join(BASE_DIR, "data/Companies/CES_2026_ENRICHED.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data/Companies/CES_2026_RAG_MATCHED.csv")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")
EMBEDDING_MODEL_NAME = "mxbai-embed-large"
DISTANCE_THRESHOLD = 180  # Maximum L2 distance to be considered "high relevance" (lower = better match)

# RAG database names - PRODUCT-SPECIFIC ONLY (excluding general core capabilities)
RAG_DATABASES = [
    "beacon_capabilities",
    "body_cam_capabilities", 
    "dashcam_capabilities",
    "in_cabin_capabilities",
    "ip_camera_capabilities",
    "access_control_capabilities"
]

def load_rag_databases(embeddings) -> Dict[str, Chroma]:
    """Load all Rapidise RAG databases"""
    print("Loading Rapidise RAG databases...")
    databases = {}
    
    for db_name in RAG_DATABASES:
        db_path = os.path.join(KNOWLEDGE_BASE_PATH, db_name)
        if os.path.exists(db_path):
            try:
                db = Chroma(
                    persist_directory=db_path,
                    embedding_function=embeddings
                )
                databases[db_name] = db
                print(f"  ✓ Loaded {db_name}")
            except Exception as e:
                print(f"  ✗ Failed to load {db_name}: {e}")
        else:
            print(f"  ✗ Database not found: {db_path}")
    
    return databases

def query_company_relevance(company_text: str, databases: Dict[str, Chroma], k: int = 3) -> Tuple[float, str, str]:
    """
    Query company description against all RAG databases.
    Returns: (best_distance, matched_product, match_reason)
    Note: Lower distance = better match
    """
    best_distance = float('inf')  # Start with worst possible distance
    matched_product = "None"
    match_reason = ""
    
    for db_name, db in databases.items():
        try:
            # Query the database with distance scores (L2 distance)
            results = db.similarity_search_with_score(company_text, k=k)
            
            if results:
                # Get the best match from this database
                doc, distance = results[0]
                
                # Lower distance = better match
                if distance < best_distance:
                    best_distance = distance
                    matched_product = db_name.replace("_capabilities", "")
                    # Extract a snippet from the matched document
                    match_reason = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        
        except Exception as e:
            print(f"    Error querying {db_name}: {e}")
            continue
    
    return best_distance, matched_product, match_reason

def categorize_company(row) -> str:
    """Determine which tier the company belongs to based on available data"""
    has_website = pd.notna(row.get('Website')) and row.get('Website') != ''
    has_linkedin = pd.notna(row.get('LinkedIn URL')) and row.get('LinkedIn URL') not in ['', 'Not Found', 'Not found on website']
    has_summary = pd.notna(row.get('Summary')) and row.get('Summary') != ''
    has_brief = pd.notna(row.get('Brief Summary')) and row.get('Brief Summary') != ''
    
    if has_website and has_linkedin and (has_summary or has_brief):
        return "Tier1_All"
    elif (has_summary or has_brief) and not has_website and not has_linkedin:
        return "Tier2_SummaryOnly"
    elif has_website and not (has_summary or has_brief):
        return "Tier3_WebsiteOnly"
    elif has_summary or has_brief:
        return "Tier2_SummaryOnly"
    else:
        return "Tier_Insufficient"

def prepare_company_text(row, tier: str) -> str:
    """Prepare the text to query based on the tier"""
    texts = []
    
    # Prioritize scraped summary (from enrichment)
    if pd.notna(row.get('Scraped_Summary')) and row.get('Scraped_Summary') != '':
        texts.append(row['Scraped_Summary'])
    # Fall back to original summaries
    elif pd.notna(row.get('Full_Summary')) and row.get('Full_Summary') != '':
        texts.append(row['Full_Summary'])
    elif pd.notna(row.get('Summary')) and row.get('Summary') != '':
        texts.append(row['Summary'])
    
    if not texts:
        return ""
    
    return " ".join(texts)

def main():
    print("=" * 60)
    print("Finding Relevant CES Companies for Rapidise")
    print("=" * 60)
    
    # Load input CSV
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found: {INPUT_FILE}")
        return
    
    print(f"\nLoading companies from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    print(f"Total companies: {len(df)}")
    
    # Initialize embeddings
    print(f"\nInitializing Ollama embeddings with model: {EMBEDDING_MODEL_NAME}")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    
    # Load all RAG databases
    databases = load_rag_databases(embeddings)
    
    if not databases:
        print("Error: No RAG databases loaded. Please run rapidise_capabilities.py first.")
        return
    
    print(f"\nSuccessfully loaded {len(databases)} RAG database(s)")
    
    # Process companies
    print("\n" + "=" * 60)
    print("Processing Companies")
    print("=" * 60)
    
    results = []
    tier_counts = {"Tier1_All": 0, "Tier2_SummaryOnly": 0, "Tier3_WebsiteOnly": 0, "Tier_Insufficient": 0}
    relevant_count = 0
    
    for idx, row in df.iterrows():
        company_name = row.get('Exhibitor', 'Unknown')
        
        # Categorize company
        tier = categorize_company(row)
        tier_counts[tier] += 1
        
        # Prepare text for querying
        company_text = prepare_company_text(row, tier)
        
        if not company_text:
            print(f"  [{idx+1}/{len(df)}] {company_name} - Skipped (no data)")
            continue
        
        # Query RAG databases
        distance, matched_product, match_reason = query_company_relevance(company_text, databases)
        
        # Check if meets threshold (lower distance = better match)
        is_relevant = distance < DISTANCE_THRESHOLD
        
        if is_relevant:
            relevant_count += 1
            print(f"  ✓ [{idx+1}/{len(df)}] {company_name} - Distance: {distance:.2f} - Product: {matched_product}")
            
            # Add to results
            result = row.to_dict()
            result['Distance_Score'] = round(distance, 2)
            result['Matched_Product'] = matched_product
            result['Match_Reason'] = match_reason
            result['Data_Tier'] = tier
            results.append(result)
        else:
            print(f"  [{idx+1}/{len(df)}] {company_name} - Distance: {distance:.2f} (above threshold)")
    
    # Save results
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Total companies processed: {len(df)}")
        print(f"Tier distribution:")
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count}")
        print(f"\nHigh relevance companies found: {relevant_count}")
        print(f"Output saved to: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\nNo relevant companies found above threshold.")

if __name__ == "__main__":
    main()
