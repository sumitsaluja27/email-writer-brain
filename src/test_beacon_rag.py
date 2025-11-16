

import os
import sys
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# --- Configuration ---
BASE_DIR = "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")
BEACON_CHROMA_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "beacon_capabilities")
EMBEDDING_MODEL_NAME = "mxbai-embed-large"

def test_beacon_retrieval():
    print("\n--- Testing Beacon RAG Retrieval ---")
    print(f"Loading Beacon RAG from: {BEACON_CHROMA_PATH}")
    print(f"Using Embedding Model: {EMBEDDING_MODEL_NAME}")

    # Initialize embeddings
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

    # Load Chroma DB
    try:
        beacon_db = Chroma(persist_directory=BEACON_CHROMA_PATH, embedding_function=embeddings)
        print("Beacon RAG loaded successfully.")
    except Exception as e:
        print(f"Error loading Beacon RAG: {e}")
        sys.exit(1)

    # Define the query
    query = "What types of beacons does Rapidise offer?"
    print(f"\nPerforming similarity search with query: \"{query}\"")

    # Perform similarity search
    try:
        # similarity_search_with_score returns a list of (Document, score) tuples
        results = beacon_db.similarity_search_with_score(query, k=3)
        
        if not results:
            print("No relevant documents found.")
            return

        print("\n--- Top 3 Retrieved Chunks ---")
        for i, (doc, score) in enumerate(results):
            print(f"\n--- Chunk {i+1} (Score: {score:.4f}) ---")
            print("Content:")
            print(doc.page_content)
            print("\nMetadata:")
            for key, value in doc.metadata.items():
                print(f"  {key}: {value}")
            print("-----------------------------")

    except Exception as e:
        print(f"An error occurred during similarity search: {e}")

if __name__ == "__main__":
    test_beacon_retrieval()

