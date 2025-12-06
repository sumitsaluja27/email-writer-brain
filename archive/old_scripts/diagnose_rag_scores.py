import os
import math
import pandas as pd
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# Configuration
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
INPUT_FILE = os.path.join(BASE_DIR, "data/Companies/CES 2026_non_asian_validated_CLEAN.csv")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")
EMBEDDING_MODEL_NAME = "mxbai-embed-large"

# Load a sample company
df = pd.read_csv(INPUT_FILE)
sample_companies = df[df['Summary'].notna()].head(10)

print("Testing RAG distance values...")
print("=" * 60)

# Initialize embeddings
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

# Load one RAG database
db_path = os.path.join(KNOWLEDGE_BASE_PATH, "dashcam_capabilities")
db = Chroma(persist_directory=db_path, embedding_function=embeddings)

print(f"\nLoaded database: dashcam_capabilities")
print(f"Testing {len(sample_companies)} companies:\n")

for idx, row in sample_companies.iterrows():
    company_name = row['Exhibitor']
    summary = row['Summary']
    
    # Query the database
    results = db.similarity_search_with_score(summary, k=3)
    
    if results:
        print(f"\n{company_name}:")
        for i, (doc, distance) in enumerate(results):
            print(f"  Match {i+1}: Distance = {distance:.4f}")
            print(f"           exp(-dist) = {math.exp(-distance):.6f}")
            print(f"           1/(1+dist) = {1/(1+distance):.6f}")
        
        # Show the best match distance
        best_dist = results[0][1]
        print(f"  → Best distance: {best_dist:.4f}")

import math
