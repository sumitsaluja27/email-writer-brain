"""
Test the new customer_knowledge RAG with sample queries.
"""

import chromadb
import requests

class OllamaEmbed:
    """ChromaDB compatible embedding function for Ollama."""
    def __init__(self):
        self.api_url = 'http://localhost:11434/api/embeddings'
        self.model = 'mxbai-embed-large:latest'
    
    def name(self):
        return 'ollama_mxbai'
    
    def __call__(self, input):
        return self._get_embeddings(input)
    
    def embed_query(self, input):
        """For ChromaDB query interface."""
        return self._get_embeddings(input)
    
    def embed_documents(self, input):
        """For ChromaDB document interface."""
        return self._get_embeddings(input)
    
    def _get_embeddings(self, texts):
        embeddings = []
        for text in texts:
            try:
                resp = requests.post(
                    self.api_url, 
                    json={'model': self.model, 'prompt': text}, 
                    timeout=60
                )
                if resp.status_code == 200:
                    embeddings.append(resp.json()['embedding'])
                else:
                    embeddings.append([0.0]*1024)
            except:
                embeddings.append([0.0]*1024)
        return embeddings


def main():
    client = chromadb.PersistentClient(path='data/chroma_db_v2')
    collection = client.get_collection(
        name='customer_knowledge', 
        embedding_function=OllamaEmbed()
    )

    print('=== TESTING CUSTOMER KNOWLEDGE RAG ===')
    print(f'Collection has {collection.count()} documents')
    print()

    # Test 1: Query for fleet dashcam customer
    print('QUERY 1: Fleet safety video telematics')
    results = collection.query(query_texts=['fleet safety video telematics dashcam'], n_results=3)
    print('TOP 3 MATCHES:')
    for i, meta in enumerate(results['metadatas'][0]):
        print(f"  {i+1}. {meta['company_name']} | {meta['product_category']}")
    print()

    # Test 2: Query for security camera company
    print('QUERY 2: Home security monitoring cameras')
    results = collection.query(query_texts=['home security monitoring cameras surveillance'], n_results=3)
    print('TOP 3 MATCHES:')
    for i, meta in enumerate(results['metadatas'][0]):
        print(f"  {i+1}. {meta['company_name']} | {meta['product_category']}")
    print()

    # Test 3: Query for bodycam
    print('QUERY 3: Police body worn camera')
    results = collection.query(query_texts=['police body worn camera law enforcement'], n_results=3)
    print('TOP 3 MATCHES:')
    for i, meta in enumerate(results['metadatas'][0]):
        print(f"  {i+1}. {meta['company_name']} | {meta['product_category']}")


if __name__ == "__main__":
    main()
