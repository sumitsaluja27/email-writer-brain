"""
ENHANCED Final Company Classification Script
- Uses ChromaDB RAG with Rapidise PDFs + customer profiles
- Uses llama3.1:8b (better reasoning)  
- 3-tier classification: RELEVANT, NEEDS_REVIEW, NOT_RELEVANT
- Enhanced keywords from NotebookLM
- Resume logic to continue where stopped
"""

import pandas as pd
import requests
import json
import chromadb
from chromadb.config import Settings
import os
from datetime import datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1:8b'
JINA_API = 'https://r.jina.ai/'

# === ENHANCED KEYWORDS FROM NOTEBOOKLM ===
RELEVANT_KEYWORDS = [
    # CAMERAS
    'camera', 'video', 'cctv', 'surveillance', 'ip camera', 'ptz', 'dome camera',
    'bullet camera', 'imaging', 'low light camera', 'in-cabin camera',
    'rear seat entertainment', 'surveillance ai',
    
    # DASHCAM/BODYCAM
    'dashcam', 'dash cam', 'bodycam', 'body cam', 'lte bodycam', 'ai bodycam',
    'dual dashcam', 'oem fit dashcam', 'wearable camera', 'action cam',
    
    # RECORDING/VMS
    'dvr', 'nvr', 'vms', 'video management', 'recorder', 'recording',
    'cloud vms', 'webrtc', 'streaming',
    
    # SECURITY AI
    'security', 'alarm', 'intrusion', 'intrusion detection', 'access control',
    'biometric', 'facial recognition', 'face recognition', 'gun detection',
    'violence detection', 'fire detection', 'smoke detection', 'loitering',
    'license plate', 'anpr', 'lpr', 'perimeter', 'motion detection',
    
    # ADAS
    'adas', 'forward collision', 'collision warning', 'lane departure',
    'blind spot', 'pedestrian detection', 'tailgating', 'traffic sign',
    'crash detection', 'predictive crash',
    
    # DMS
    'dms', 'driver monitoring', 'drowsiness', 'distraction detection',
    'yawn detection', 'eye blink', 'mobile phone usage', 'seat belt detection',
    'fatigue', 'driver behavior', 'occupancy detection',
    
    # TELEMATICS/FLEET
    'telematics', 'fleet', 'fleet management', 'gps', 'tracker', 'tracking',
    'vehicle tracking', 'asset tracker', 'fuel monitoring', 'vehicle telemetry',
    'fota', 'eld', 'electronic logging',
    
    # ACCESS CONTROL
    'smart lock', 'smart gateway', 'multi-tenant access', 'smart mailbox',
    'smart switch', 'card reader', 'door access',
    
    # IOT/SENSORS
    'sensor', 'iot', 'ble beacon', 'beacon', 'presence detection', 'hpd',
    'radar', 'person detection', 'edge ai', 'iot gateway',
    
    # AUTOMOTIVE HMI
    'digital cockpit', 'head-up display', 'hud', 'instrument cluster',
    'industrial hmi', 'infotainment',
    
    # COMPETITOR BRANDS
    'hikvision', 'dahua', 'axis', 'pelco', 'bosch security', 'honeywell security',
    'genetec', 'milestone', 'avigilon', 'geovision', 'mobotix', 'vivotek',
    'hanwha', 'uniview', 'verkada', 'rhombus', 'samsara', 'verizon connect',
    'geotab', 'motive', 'lytx', 'smartwitness'
]

# Industries that warrant review
REVIEW_INDUSTRIES = [
    'public safety', 'security', 'electrical/electronic manufacturing',
    'defense', 'law enforcement', 'surveillance', 'fire safety',
    'automotive', 'transportation', 'logistics', 'fleet', 'trucking',
    'insurance', 'iot', 'smart home', 'construction', 'mining',
    'oil & gas', 'energy', 'utilities', 'government', 'military'
]

# Ollama embedding function for ChromaDB
class OllamaEmbeddingFunction:
    def __init__(self, model_name="mxbai-embed-large:latest"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/embeddings"

    def __call__(self, input_texts):
        embeddings = []
        for text in input_texts:
            try:
                response = requests.post(self.api_url, json={"model": self.model_name, "prompt": text}, timeout=60)
                if response.status_code == 200:
                    embeddings.append(response.json()["embedding"])
                else:
                    embeddings.append([0.0] * 1024)
            except:
                embeddings.append([0.0] * 1024)
        return embeddings

def get_chromadb_collection():
    """Load the ChromaDB collection."""
    db_path = "data/chroma_db"
    client = chromadb.PersistentClient(path=db_path)
    embedding_fn = OllamaEmbeddingFunction()
    collection = client.get_or_create_collection(name="rapidise_knowledge", embedding_function=embedding_fn)
    return collection

def query_rag(collection, company_info, top_k=3):
    """Query ChromaDB for relevant Rapidise products/profiles."""
    try:
        results = collection.query(query_texts=[company_info], n_results=top_k)
        if results and results['documents']:
            return "\n".join(results['documents'][0])
    except Exception as e:
        print(f"    RAG error: {e}")
    return ""

def scrape_website(url, try_subpages=True):
    """Scrape website with optional subpages."""
    if not url or str(url) == 'nan' or pd.isna(url):
        return ""
    
    all_text = ""
    try:
        if not str(url).startswith('http'):
            url = 'https://' + str(url)
        
        response = requests.get(JINA_API + url, timeout=30, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            all_text = response.text[:2500]
        
        # Try products/about page if homepage sparse
        if try_subpages and len(all_text) < 1500:
            for subpage in ['/products', '/solutions', '/about']:
                try:
                    sub_url = url.rstrip('/') + subpage
                    resp = requests.get(JINA_API + sub_url, timeout=15, headers={'Accept': 'text/plain'})
                    if resp.status_code == 200 and len(resp.text) > 500:
                        all_text += "\n\n=== PRODUCTS/ABOUT ===\n" + resp.text[:1500]
                        break
                except:
                    pass
    except:
        pass
    
    return all_text[:4000]

def quick_keyword_check(text):
    """Check if any relevant keywords exist in text."""
    text_lower = text.lower()
    found = [kw for kw in RELEVANT_KEYWORDS if kw in text_lower]
    return list(set(found))[:10]

def industry_needs_review(industry):
    """Check if industry warrants human review."""
    if not industry or str(industry) == 'nan':
        return False
    industry_lower = str(industry).lower()
    return any(ri in industry_lower for ri in REVIEW_INDUSTRIES)

def classify_company(company_name, website, industry, description, rag_matches):
    """Smart 3-tier classification with RAG context."""
    
    needs_review_industry = industry_needs_review(industry)
    keywords_found = quick_keyword_check(f"{company_name} {description}")
    
    # Build enhanced prompt
    prompt = f"""You are classifying companies for Rapidise - an ODM manufacturer that makes:

HARDWARE:
- Dashcams (vehicle cameras for fleets, trucks, cars)
- IP Cameras (CCTV, surveillance, PTZ, dome, bullet)
- Body Cameras (for security guards, police)
- GPS Trackers (vehicle tracking devices)
- Access Control devices (biometric, card readers)

SOFTWARE/CLOUD:
- Video Management Systems (VMS, NVR software)
- Telematics platforms (fleet tracking dashboards)
- AI/ADAS solutions (collision detection, driver monitoring)

=== RAPIDISE CONTEXT (from knowledge base) ===
{rag_matches[:800] if rag_matches else 'N/A'}

=== COMPANY TO CLASSIFY ===
Company: {company_name}
Industry: {industry}
Keywords detected: {keywords_found}
Website content: {description[:600] if description else 'N/A'}

=== CLASSIFICATION (pick one) ===
RELEVANT - They SELL/RESELL cameras, dashcams, security systems, telematics. Could buy from Rapidise.
NEEDS_REVIEW - Uncertain but in security/automotive space. HUMAN should verify.
NOT_RELEVANT - Clearly unrelated: pure software, retail, food, healthcare, entertainment.

RULES:
- Security integrators, alarm companies = RELEVANT
- Fleet management companies = RELEVANT  
- Insurance with telematics programs = RELEVANT
- Car manufacturers (OEMs like Tesla, Ford) = NOT_RELEVANT (they make their own)
- Chip manufacturers (Qualcomm, Intel) = NOT_RELEVANT
- If keywords found but unclear = NEEDS_REVIEW

Reply JSON ONLY:
{{"classification": "RELEVANT/NEEDS_REVIEW/NOT_RELEVANT", "confidence": "high/medium/low", "reasoning": "one sentence"}}
"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            'model': MODEL, 'prompt': prompt, 'stream': False,
            'options': {'temperature': 0.1}
        }, timeout=180)
        
        if response.status_code == 200:
            result = response.json()['response']
            start, end = result.find('{'), result.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(result[start:end])
                
                # OVERRIDE: If keywords found but LLM said NOT_RELEVANT, force NEEDS_REVIEW
                if keywords_found and parsed.get('classification') == 'NOT_RELEVANT':
                    parsed['classification'] = 'NEEDS_REVIEW'
                    parsed['reasoning'] = f"Keywords found: {keywords_found}. Forcing review."
                
                return parsed
    except Exception as e:
        print(f"  Error: {e}")
    
    return {"classification": "NEEDS_REVIEW", "confidence": "low", "reasoning": "parse error"}

def process_companies(input_file, output_file):
    """Process companies through the full pipeline with resume support."""
    
    print("=" * 60)
    print("ENHANCED COMPANY CLASSIFICATION")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Load input
    df = pd.read_csv(input_file)
    print(f"Total companies: {len(df)}")
    
    # Find company columns
    company_col = None
    website_col = None
    industry_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'exhibitor' in col_lower or 'company' in col_lower:
            company_col = col
        if 'website' in col_lower or 'url' in col_lower:
            website_col = col
        if 'industry' in col_lower:
            industry_col = col
    
    print(f"Company col: {company_col}")
    print(f"Website col: {website_col}")
    print(f"Industry col: {industry_col}")
    
    # Resume logic
    processed_names = set()
    existing_results = []
    
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_csv(output_file)
            existing_results = existing_df.to_dict('records')
            processed_names = set(existing_df['company_name'].str.strip().str.lower())
            print(f"Resuming: {len(processed_names)} already processed")
        except:
            print("Starting fresh")
    
    # Load RAG
    print("Loading ChromaDB...")
    try:
        collection = get_chromadb_collection()
        print(f"ChromaDB loaded: {collection.count()} documents")
    except Exception as e:
        print(f"ChromaDB error: {e} - continuing without RAG")
        collection = None
    
    results = existing_results.copy()
    
    for idx, row in df.iterrows():
        name = str(row.get(company_col, '')).strip()
        
        # Skip if already processed
        if name.lower() in processed_names:
            continue
        
        website = str(row.get(website_col, '')) if website_col else ''
        industry = str(row.get(industry_col, '')) if industry_col else ''
        
        print(f"[{len(results)+1}/{len(df)}] {name[:40]}...", end=" ")
        
        # Scrape website
        desc = scrape_website(website)
        
        # Query RAG
        rag_matches = ""
        if collection:
            try:
                rag_matches = query_rag(collection, f"{name} {industry} {desc[:500]}")
            except:
                pass
        
        # Classify
        result = classify_company(name, website, industry, desc, rag_matches)
        cat = result.get('classification', 'NEEDS_REVIEW')
        print(f"→ {cat}")
        
        results.append({
            'company_name': name,
            'website': website,
            'industry': industry,
            'classification': cat,
            'confidence': result.get('confidence', ''),
            'reasoning': result.get('reasoning', '')[:150]
        })
        
        processed_names.add(name.lower())
        
        # Save every 10
        if len(results) % 10 == 0:
            pd.DataFrame(results).to_csv(output_file, index=False)
            print(f"    [Saved {len(results)}]")
    
    # Final save
    pd.DataFrame(results).to_csv(output_file, index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    result_df = pd.DataFrame(results)
    print(result_df['classification'].value_counts())
    print("=" * 60)

def main():
    input_file = "data/Companies/complete_list.csv"
    output_file = "data/Companies/complete_list_FINAL.csv"
    process_companies(input_file, output_file)

if __name__ == "__main__":
    main()
