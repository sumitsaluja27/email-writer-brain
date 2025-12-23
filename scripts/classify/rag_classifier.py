"""
RAG-based Company Classifier using Customer DNA Knowledge Base.

Flow:
1. Take new company (name, website, industry)
2. Scrape website content
3. Query Customer DNA KB for similarity
4. Use LLM to classify based on similarity
5. Output: RELEVANT / NOT_RELEVANT + reasoning
"""

import chromadb
import requests
import json
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_EMBED_URL = 'http://localhost:11434/api/embeddings'
MODEL = 'llama3.1:8b'
EMBED_MODEL = 'mxbai-embed-large:latest'
JINA_API = 'https://r.jina.ai/'


class OllamaEmbed:
    """ChromaDB compatible embedding function for Ollama."""
    def __init__(self):
        self.api_url = OLLAMA_EMBED_URL
        self.model = EMBED_MODEL
    
    def name(self):
        return 'ollama_mxbai'
    
    def __call__(self, input):
        return self._get_embeddings(input)
    
    def embed_query(self, input):
        return self._get_embeddings(input)
    
    def _get_embeddings(self, texts):
        embeddings = []
        for text in texts:
            try:
                resp = requests.post(
                    self.api_url, 
                    json={'model': self.model, 'prompt': str(text)}, 
                    timeout=60
                )
                if resp.status_code == 200:
                    embeddings.append(resp.json()['embedding'])
                else:
                    embeddings.append([0.0]*1024)
            except:
                embeddings.append([0.0]*1024)
        return embeddings


def scrape_website(url, max_chars=4000):
    """Scrape website content using Jina API."""
    if not url:
        return ""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        response = requests.get(JINA_API + url, timeout=45, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            return response.text[:max_chars]
    except:
        pass
    return ""


def get_customer_dna_collection():
    """Get the Customer DNA KB collection."""
    client = chromadb.PersistentClient(path='data/customer_dna_db')
    return client.get_collection(name='customer_dna', embedding_function=OllamaEmbed())


def classify_company(name, website, industry, verbose=True):
    """
    Classify a company as RELEVANT or NOT_RELEVANT using RAG.
    
    Returns:
        dict with keys: classification, confidence, reasoning, similar_customers
    """
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"CLASSIFYING: {name}")
        print(f"{'='*60}")
    
    # Step 1: Scrape website
    if verbose:
        print("Step 1: Scraping website...")
    content = scrape_website(website)
    if len(content) < 100:
        return {
            'classification': 'NOT_RELEVANT',
            'confidence': 0.9,
            'reasoning': 'Could not access website content',
            'similar_customers': []
        }
    if verbose:
        print(f"  Got {len(content)} chars")
    
    # Step 2: Query Customer DNA KB
    if verbose:
        print("Step 2: Querying Customer DNA KB...")
    collection = get_customer_dna_collection()
    
    # Create query from company info
    query = f"{name} {industry} {content[:1500]}"
    
    results = collection.query(
        query_texts=[query],
        n_results=5,
        include=['documents', 'metadatas', 'distances']
    )
    
    similar_customers = []
    if results['metadatas'] and results['metadatas'][0]:
        for meta, dist in zip(results['metadatas'][0], results['distances'][0]):
            similar_customers.append({
                'company': meta.get('company_name', 'Unknown'),
                'product_category': meta.get('product_category', ''),
                'type': meta.get('type', ''),
                'distance': round(dist, 3)
            })
    
    if verbose:
        print(f"  Found {len(similar_customers)} similar customers:")
        for c in similar_customers[:3]:
            print(f"    - {c['company']} ({c['product_category']}) - distance: {c['distance']}")
    
    # Step 3: LLM Classification
    if verbose:
        print("Step 3: LLM Classification...")
    
    # Check if distances are high (not similar)
    avg_distance = sum(c['distance'] for c in similar_customers) / max(len(similar_customers), 1)
    
    similar_info = "\n".join([
        f"- {c['company']} ({c['product_category']}, distance: {c['distance']})"
        for c in similar_customers[:5]
    ])
    
    prompt = f"""You are classifying if a company is RELEVANT for an ODM manufacturer (Rapidise) that makes:
- Dashcams
- Body cameras  
- IP cameras / Security cameras
- Access control devices
- Beacons / IoT trackers

COMPANY TO CLASSIFY:
Name: {name}
Industry: {industry}

WEBSITE CONTENT (excerpt):
{content[:2000]}

SIMILAR CUSTOMERS FROM OUR DATABASE:
{similar_info}

Average similarity distance: {avg_distance:.3f} (lower = more similar)

CLASSIFICATION RULES:
1. RELEVANT if they SELL products similar to our existing customers (cameras, video, telematics)
2. RELEVANT if they NEED cameras/devices for their product/service
3. NOT_RELEVANT if they just USE cameras (end user, not a buyer of ODM services)
4. NOT_RELEVANT if they make completely unrelated products (software-only, food, healthcare, etc.)

Respond in JSON:
{{
  "classification": "RELEVANT" or "NOT_RELEVANT",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0.1}
        }, timeout=120)
        
        if response.status_code == 200:
            result = response.json()['response']
            parsed = json.loads(result)
            
            return {
                'classification': parsed.get('classification', 'NOT_RELEVANT'),
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', ''),
                'similar_customers': similar_customers,
                'avg_distance': avg_distance
            }
    except Exception as e:
        if verbose:
            print(f"  LLM error: {e}")
    
    return {
        'classification': 'NOT_RELEVANT',
        'confidence': 0.5,
        'reasoning': 'Classification failed',
        'similar_customers': similar_customers
    }


def test_classifier():
    """Test the classifier with sample companies."""
    
    print("=" * 60)
    print("TESTING RAG CLASSIFIER")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    test_cases = [
        # Should be RELEVANT
        ("Samsara", "https://samsara.com", "Fleet Telematics"),
        ("Blackvue", "https://blackvue.com", "Consumer Electronics"),
        ("WatchGuard Video", "https://watchguardvideo.com", "Public Safety"),
        
        # Should be NOT_RELEVANT
        ("Stripe", "https://stripe.com", "Financial Services"),
        ("Snowflake", "https://snowflake.com", "Data Cloud"),
        ("Slack", "https://slack.com", "Software"),
    ]
    
    results = []
    for name, website, industry in test_cases:
        result = classify_company(name, website, industry)
        results.append({
            'name': name,
            'expected': 'RELEVANT' if 'camera' in industry.lower() or 'fleet' in industry.lower() or 'safety' in industry.lower() else 'NOT_RELEVANT',
            'got': result['classification'],
            'confidence': result['confidence'],
            'reasoning': result['reasoning'][:80]
        })
        print(f"\nResult: {result['classification']} (confidence: {result['confidence']})")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        match = "✓" if r['expected'] == r['got'] else "✗"
        print(f"{match} {r['name']:20} | Expected: {r['expected']:12} | Got: {r['got']:12} | Conf: {r['confidence']}")


if __name__ == "__main__":
    test_classifier()
