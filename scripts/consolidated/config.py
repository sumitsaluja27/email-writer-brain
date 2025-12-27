"""
Rapidise Company Classification Pipeline - Configuration
=========================================================

Centralized configuration for all pipeline components.
All paths, API settings, and product definitions in one place.
"""

from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent  # email_writer/
DATA_DIR = BASE_DIR / "data"
COMPANIES_DIR = DATA_DIR / "Companies"
DOCS_DIR = BASE_DIR / "docs"

# RAG Databases
RAG_DB_DIR = DATA_DIR / "rag_databases"
CUSTOMER_DNA_DB = RAG_DB_DIR / "customer_dna_db"
RAPIDISE_FIT_DB = RAG_DB_DIR / "rapidise_fit_db"

# Company Profiles
PROFILES_DIR = DATA_DIR / "company_profiles_v2"

# =============================================================================
# API SETTINGS
# =============================================================================

# Ollama (Local LLM)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
LLM_MODEL = "llama3.1:8b"
EMBED_MODEL = "mxbai-embed-large:latest"

# Jina (Web Scraping)
JINA_API = "https://r.jina.ai/"

# Timeouts
SCRAPE_TIMEOUT = 30
LLM_TIMEOUT = 120
EMBED_TIMEOUT = 60

# =============================================================================
# RAPIDISE PRODUCTS (6 Products)
# =============================================================================

PRODUCTS = {
    "dashcam": {
        "name": "Dashcam",
        "description": "Fleet and consumer dashcams for vehicles",
        "keywords": ["dashcam", "dash cam", "fleet camera", "vehicle camera", "DVR", "drive recorder"],
        "customer_types": ["fleet operators", "telematics providers", "automotive OEMs", "consumers"]
    },
    "in_cabin": {
        "name": "In-Cabin / Driver Monitoring",
        "description": "Driver monitoring systems (DMS), occupant monitoring (OMS)",
        "keywords": ["DMS", "driver monitoring", "in-cabin", "fatigue detection", "distraction", "OMS"],
        "customer_types": ["automotive OEMs", "fleet management", "ADAS suppliers", "commercial vehicles"]
    },
    "bodycam": {
        "name": "Body Camera",
        "description": "Body-worn cameras for law enforcement, security, enterprise",
        "keywords": ["body camera", "bodycam", "body-worn", "BWV", "police camera", "security camera"],
        "customer_types": ["law enforcement", "security companies", "retail", "healthcare"]
    },
    "ip_camera": {
        "name": "IP Camera / Security Camera",
        "description": "Network security cameras, surveillance systems",
        "keywords": ["IP camera", "security camera", "CCTV", "surveillance", "network camera", "NVR"],
        "customer_types": ["security integrators", "enterprise", "smart home", "retail"]
    },
    "access_control": {
        "name": "Access Control",
        "description": "Access control devices, readers, controllers",
        "keywords": ["access control", "door controller", "card reader", "biometric", "entry system"],
        "customer_types": ["security integrators", "enterprise", "real estate", "government"]
    },
    "beacon": {
        "name": "Beacon / IoT Tracker",
        "description": "BLE beacons, asset trackers, temperature monitors",
        "keywords": ["beacon", "BLE", "asset tracker", "temperature monitor", "IoT", "cold chain"],
        "customer_types": ["logistics", "cold chain", "pharma", "asset management", "retail"]
    }
}

# =============================================================================
# RAPIDISE SERVICES (3 Services)
# =============================================================================

SERVICES = {
    "ODM": {
        "name": "ODM (Original Design Manufacturing)",
        "description": "Rapidise designs AND manufactures complete products for brands",
        "ideal_customer": "Companies that want their own branded product but don't have design capability"
    },
    "PES": {
        "name": "PES (Product Engineering Services)",
        "description": "Rapidise provides design/engineering services, client may manufacture elsewhere",
        "ideal_customer": "Companies that need design help but may have their own manufacturing"
    },
    "EMS": {
        "name": "EMS (Electronics Manufacturing Services)",
        "description": "Rapidise assembles/manufactures client's existing designs",
        "ideal_customer": "Companies that have their own designs but need manufacturing partner"
    }
}

# =============================================================================
# CLASSIFICATION SETTINGS
# =============================================================================

CLASSIFICATION = {
    "relevant_types": [
        "product_company",      # Makes/sells cameras, devices
        "platform_provider",    # Software platform needing hardware
        "fleet_operator",       # Large fleet needing dashcams
        "oem_supplier",         # Tier 1/2 automotive supplier
        "security_integrator",  # Security system integrators
    ],
    "not_relevant_types": [
        "pure_software",        # Software-only, no hardware need
        "end_user",             # Just uses cameras, doesn't buy ODM
        "reseller",             # Resells others' products
        "unrelated_industry",   # Food, healthcare, finance, etc.
    ]
}

# =============================================================================
# FILE PATTERNS
# =============================================================================

CSV_FILES = {
    "sample_companies": COMPANIES_DIR / "sample_companies_for_review.csv",
    "complete_list": COMPANIES_DIR / "complete_list_FINAL.csv",
    "sep_nov": COMPANIES_DIR / "sep_nov.csv",
}

# =============================================================================
# SCRAPING SETTINGS
# =============================================================================

PAGE_PATTERNS = {
    'about': ['/about', '/company', '/who-we-are', '/our-story'],
    'products': ['/products', '/product', '/hardware', '/devices'],
    'solutions': ['/solutions', '/solution', '/platform'],
    'services': ['/services', '/service', '/offerings'],
    'industries': ['/industries', '/industry', '/markets', '/sectors'],
    'use_cases': ['/use-cases', '/case-studies', '/customers'],
    'partners': ['/partners', '/partner', '/integrations']
}

MAX_CONTENT_PER_PAGE = 15000  # Characters
MAX_TOTAL_CONTENT = 50000    # Characters per company


def ensure_dirs():
    """Create all required directories."""
    dirs = [
        DATA_DIR, COMPANIES_DIR, RAG_DB_DIR, 
        PROFILES_DIR, PROFILES_DIR / "odm_customer", PROFILES_DIR / "end_user"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("Rapidise Classification Pipeline - Configuration")
    print("=" * 50)
    print(f"Base directory: {BASE_DIR}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Products: {list(PRODUCTS.keys())}")
    print(f"Services: {list(SERVICES.keys())}")
