"""
CRAG (Corrective RAG) Company Classification Pipeline
Using LangGraph for structured multi-step classification with self-correction.

Flow:
1. RETRIEVE - Get similar products from RAG
2. GRADE - Is the retrieved context relevant?
3. DECIDE - Check industry blacklist + grading result
4. CLASSIFY - Is this company a buyer or maker?
5. VERIFY - Final sanity check
"""

from typing import List, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
import requests
import json
import chromadb
from chromadb.config import Settings

# === CONFIGURATION ===
OLLAMA_URL = 'http://localhost:11434/api/generate'
JINA_API = 'https://r.jina.ai/'

# Models for different tasks
GRADER_MODEL = 'llama3.1:8b'      # Fast, good at yes/no
CLASSIFIER_MODEL = 'deepseek-llm:7b'  # Good at reasoning
VERIFIER_MODEL = 'llama3.1:8b'    # Second opinion

# Industries to auto-exclude (no LLM needed)
BLACKLIST_INDUSTRIES = [
    'semiconductors', 'semiconductor',
    'hospital & health care', 'healthcare', 'health care',
    'real estate', 'real estate services',
    'cryptocurrency', 'crypto', 'blockchain',
    'food & beverages', 'food production', 'restaurants',
    'entertainment', 'music', 'gaming', 'gambling',
    'banking', 'investment banking', 'venture capital',
    'law practice', 'legal services',
    'education', 'higher education',
    'nonprofit', 'philanthropy',
    'farming', 'agriculture',
    'cosmetics', 'apparel & fashion',
]

# Industries that are promising
WHITELIST_INDUSTRIES = [
    'security', 'public safety', 'defense',
    'transportation', 'logistics', 'trucking', 'fleet',
    'surveillance', 'fire safety', 'law enforcement',
]


# === GRAPH STATE ===
class GraphState(TypedDict):
    """State passed between nodes."""
    company_name: str
    website: str
    industry: str
    website_content: str
    rag_context: str
    rag_relevant: str  # "yes" or "no"
    company_type: str  # "buyer", "maker", or "unclear"
    final_decision: str  # "RELEVANT", "NEEDS_REVIEW", "NOT_RELEVANT"
    reasoning: str
    steps: List[str]


# === HELPER FUNCTIONS ===

def call_ollama(model: str, prompt: str, json_mode: bool = False) -> str:
    """Call Ollama with optional JSON mode."""
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1}
        }
        if json_mode:
            payload['format'] = 'json'
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        if response.status_code == 200:
            return response.json()['response']
    except Exception as e:
        print(f"  Ollama error: {e}")
    return ""


def scrape_website(url: str) -> str:
    """Scrape website using Jina API."""
    if not url or url == 'nan':
        return ""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        response = requests.get(JINA_API + url, timeout=30, headers={'Accept': 'text/plain'})
        if response.status_code == 200:
            return response.text[:3000]
    except:
        pass
    return ""


def get_chromadb_collection():
    """Load ChromaDB collection."""
    from chromadb.config import Settings
    
    class OllamaEmbedding:
        def __init__(self):
            self.api_url = "http://localhost:11434/api/embeddings"
        
        def __call__(self, input_texts):
            embeddings = []
            for text in input_texts:
                try:
                    response = requests.post(self.api_url, 
                        json={"model": "mxbai-embed-large:latest", "prompt": text}, 
                        timeout=60)
                    if response.status_code == 200:
                        embeddings.append(response.json()["embedding"])
                    else:
                        embeddings.append([0.0] * 1024)
                except:
                    embeddings.append([0.0] * 1024)
            return embeddings
    
    client = chromadb.PersistentClient(path="data/chroma_db")
    collection = client.get_or_create_collection(
        name="rapidise_knowledge",
        embedding_function=OllamaEmbedding()
    )
    return collection


# === NODE FUNCTIONS ===

def retrieve(state: GraphState) -> GraphState:
    """Node 1: Retrieve similar products from RAG."""
    state["steps"].append("retrieve")
    
    # Build query
    query = f"{state['company_name']} {state['industry']} {state['website_content'][:500]}"
    
    try:
        collection = get_chromadb_collection()
        results = collection.query(query_texts=[query], n_results=3)
        if results and results['documents']:
            state["rag_context"] = "\n".join(results['documents'][0])
        else:
            state["rag_context"] = ""
    except Exception as e:
        print(f"  RAG error: {e}")
        state["rag_context"] = ""
    
    return state


def grade_context(state: GraphState) -> GraphState:
    """Node 2: Grade if RAG context is relevant to this company."""
    state["steps"].append("grade_context")
    
    if not state["rag_context"]:
        state["rag_relevant"] = "no"
        return state
    
    prompt = f"""You are grading whether the retrieved context is relevant to understand if a company is a potential customer.

COMPANY: {state['company_name']}
INDUSTRY: {state['industry']}

RETRIEVED CONTEXT:
{state['rag_context'][:1000]}

Question: Is this context helpful to determine if {state['company_name']} would buy cameras, dashcams, or security devices from a manufacturer?

Give a binary score 'yes' or 'no'. Provide as JSON with key 'score'.
"""
    
    result = call_ollama(GRADER_MODEL, prompt, json_mode=True)
    try:
        parsed = json.loads(result)
        state["rag_relevant"] = parsed.get("score", "no").lower()
    except:
        state["rag_relevant"] = "no"
    
    return state


def check_blacklist(state: GraphState) -> Literal["blacklisted", "promising", "classify"]:
    """Decision node: Check industry blacklist."""
    industry = state.get("industry", "").lower()
    
    # Check blacklist
    for bl in BLACKLIST_INDUSTRIES:
        if bl in industry:
            return "blacklisted"
    
    # Check whitelist
    for wl in WHITELIST_INDUSTRIES:
        if wl in industry:
            return "promising"
    
    return "classify"


def mark_not_relevant(state: GraphState) -> GraphState:
    """Node: Mark as NOT_RELEVANT due to blacklisted industry."""
    state["steps"].append("blacklisted")
    state["final_decision"] = "NOT_RELEVANT"
    state["reasoning"] = f"Industry '{state['industry']}' is blacklisted (not a target customer)"
    return state


def classify_company(state: GraphState) -> GraphState:
    """Node 3: Classify if company is a BUYER or MAKER."""
    state["steps"].append("classify")
    
    prompt = f"""You are classifying a company for Rapidise, an ODM (Original Design Manufacturer) that makes cameras and security devices.

COMPANY: {state['company_name']}
INDUSTRY: {state['industry']}
WEBSITE CONTENT: {state['website_content'][:1000]}

CLASSIFY AS:

**BUYER** (Definite customer - they need to buy products from an ODM):
- Security providers that install/monitor systems (ADT, Vivint, SimpliSafe)
- Fleet management companies that provide dashcams (Samsara, Lytx, Motive)
- Alarm/security integrators that resell cameras
- Body camera brands (Axon, Reveal Media)
- Insurance companies with telematics programs

**PARTNER** (Camera OEM - potential partner for specific product lines):
- Camera manufacturers who might partner for white-label products (Axis, Bosch, Garmin)
- Security OEMs who could use Rapidise for new product lines
- Companies that make some cameras but might outsource others

**SUPPLIER** (They sell components TO camera makers - NOT a customer):
- Semiconductor companies (Qualcomm, NVIDIA, Hamamatsu)
- Chip manufacturers
- Sensor/lens manufacturers

**NEITHER** (Not relevant):
- Pure software/SaaS companies with no hardware needs
- Consulting firms
- Unrelated industries

Respond JSON: {{"type": "buyer" or "partner" or "supplier" or "neither", "reason": "one sentence"}}
"""
    
    result = call_ollama(CLASSIFIER_MODEL, prompt, json_mode=True)
    try:
        parsed = json.loads(result)
        state["company_type"] = parsed.get("type", "unclear").lower()
        state["reasoning"] = parsed.get("reason", "")
    except:
        state["company_type"] = "unclear"
        state["reasoning"] = "Failed to parse classification"
    
    return state


def route_after_classify(state: GraphState) -> Literal["verify", "needs_review", "not_relevant"]:
    """Decision node: Route based on classification."""
    company_type = state.get("company_type", "unclear")
    
    if company_type == "buyer":
        return "verify"  # Definite customer, verify first
    elif company_type == "partner":
        return "needs_review"  # Potential partner, human should review
    elif company_type == "supplier":
        return "not_relevant"  # Component supplier, not a customer
    elif company_type == "neither":
        return "not_relevant"  # Unrelated industry
    else:
        return "needs_review"  # Unclear, human should check


def verify_decision(state: GraphState) -> GraphState:
    """Node 4: Verify with second opinion - would an ODM approach this company?"""
    state["steps"].append("verify")
    
    prompt = f"""Final verification: Would an ODM camera manufacturer approach this company as a potential customer?

COMPANY: {state['company_name']}
INDUSTRY: {state['industry']}
PREVIOUS ASSESSMENT: {state['company_type']} - {state['reasoning']}

An ODM manufacturer (like Rapidise) makes:
- Dashcams for fleets
- Body cameras for security
- IP cameras for surveillance
- GPS trackers
- Access control devices

Would this company likely need to buy these products from a manufacturer to resell under their brand?

Answer JSON: {{"relevant": "yes" or "no", "confidence": "high" or "low"}}
"""
    
    result = call_ollama(VERIFIER_MODEL, prompt, json_mode=True)
    try:
        parsed = json.loads(result)
        relevant = parsed.get("relevant", "no").lower()
        confidence = parsed.get("confidence", "low").lower()
        
        if relevant == "yes" and confidence == "high":
            state["final_decision"] = "RELEVANT"
        elif relevant == "yes":
            state["final_decision"] = "NEEDS_REVIEW"
        else:
            state["final_decision"] = "NOT_RELEVANT"
    except:
        state["final_decision"] = "NEEDS_REVIEW"
    
    return state


def mark_needs_review(state: GraphState) -> GraphState:
    """Node: Mark as NEEDS_REVIEW."""
    state["steps"].append("needs_review")
    state["final_decision"] = "NEEDS_REVIEW"
    if not state.get("reasoning"):
        state["reasoning"] = "Classification unclear, needs human review"
    return state


def mark_not_relevant_maker(state: GraphState) -> GraphState:
    """Node: Mark as NOT_RELEVANT because company is a maker/competitor."""
    state["steps"].append("not_relevant_maker")
    state["final_decision"] = "NOT_RELEVANT"
    state["reasoning"] = f"Company is a MAKER/manufacturer: {state.get('reasoning', '')}"
    return state


def mark_promising(state: GraphState) -> GraphState:
    """Node: Fast-track promising industries."""
    state["steps"].append("promising_industry")
    # Still need to classify, but with positive bias
    return classify_company(state)


# === BUILD THE GRAPH ===

def build_crag_graph():
    """Build the LangGraph workflow."""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_context", grade_context)
    workflow.add_node("classify", classify_company)
    workflow.add_node("verify", verify_decision)
    workflow.add_node("mark_not_relevant", mark_not_relevant)
    workflow.add_node("mark_not_relevant_maker", mark_not_relevant_maker)
    workflow.add_node("mark_needs_review", mark_needs_review)
    workflow.add_node("mark_promising", mark_promising)
    
    # Define edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_context")
    
    # After grading, check blacklist
    workflow.add_conditional_edges(
        "grade_context",
        check_blacklist,
        {
            "blacklisted": "mark_not_relevant",
            "promising": "mark_promising",
            "classify": "classify",
        }
    )
    
    # After promising fast-track, route based on classification
    workflow.add_conditional_edges(
        "mark_promising",
        route_after_classify,
        {
            "verify": "verify",
            "needs_review": "mark_needs_review",
            "not_relevant": "mark_not_relevant_maker",
        }
    )
    
    # After classification, route
    workflow.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "verify": "verify",
            "needs_review": "mark_needs_review",
            "not_relevant": "mark_not_relevant_maker",
        }
    )
    
    # Terminal nodes
    workflow.add_edge("verify", END)
    workflow.add_edge("mark_not_relevant", END)
    workflow.add_edge("mark_not_relevant_maker", END)
    workflow.add_edge("mark_needs_review", END)
    
    return workflow.compile()


# === MAIN CLASSIFICATION FUNCTION ===

def classify_company_crag(company_name: str, website: str, industry: str) -> dict:
    """Classify a single company using CRAG pipeline."""
    
    # Scrape website first
    website_content = scrape_website(website)
    
    # Initialize state
    initial_state: GraphState = {
        "company_name": company_name,
        "website": website,
        "industry": industry,
        "website_content": website_content,
        "rag_context": "",
        "rag_relevant": "",
        "company_type": "",
        "final_decision": "",
        "reasoning": "",
        "steps": [],
    }
    
    # Run the graph
    graph = build_crag_graph()
    final_state = graph.invoke(initial_state)
    
    return {
        "classification": final_state["final_decision"],
        "reasoning": final_state["reasoning"],
        "company_type": final_state["company_type"],
        "steps": final_state["steps"],
    }


# === TEST ===
if __name__ == "__main__":
    print("=" * 60)
    print("CRAG COMPANY CLASSIFICATION - TEST")
    print("=" * 60)
    
    # Test cases
    test_companies = [
        # Should be NOT_RELEVANT (semiconductor = supplier)
        ("Hamamatsu Photonics", "https://hamamatsu.com", "semiconductors"),
        # Should be NOT_RELEVANT (healthcare = blacklisted)
        ("Thyme Care", "https://thymecare.com", "hospital & health care"),
        # Should be RELEVANT (security provider = buyer)
        ("ADT Security", "https://adt.com", "security & investigations"),
        # Should be RELEVANT (fleet = buyer)
        ("Samsara", "https://samsara.com", "transportation/logistics"),
        # Should be NEEDS_REVIEW (camera OEM = partner)
        ("Axis Communications", "https://axis.com", "security & investigations"),
        # Should be NEEDS_REVIEW (camera OEM = partner)
        ("Bosch Security", "https://boschsecurity.com", "electrical/electronic manufacturing"),
    ]
    
    for name, website, industry in test_companies:
        print(f"\nTesting: {name}")
        print(f"  Industry: {industry}")
        result = classify_company_crag(name, website, industry)
        print(f"  → {result['classification']}")
        print(f"  Reason: {result['reasoning'][:80]}")
        print(f"  Steps: {result['steps']}")
