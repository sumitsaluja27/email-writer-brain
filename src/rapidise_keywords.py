"""
Rapidise Product Keywords and Definitions

This module contains detailed keyword mappings for all Rapidise product categories.
Used by the relevance analysis system to identify potential ODM customers.

Each product category includes:
- Primary terms: Direct product names
- Technologies: Technical features and capabilities
- Use cases: Application scenarios and market segments
- Related terms: Industry-specific terminology
"""

RAPIDISE_PRODUCT_KEYWORDS = {
    "dashcam": {
        "primary": [
            "dash cam", "dashcam", "dashboard camera", "car camera", 
            "vehicle camera", "driving recorder", "car DVR",
            "automotive camera", "windshield camera"
        ],
        "technologies": [
            "DVR", "digital video recorder", "dual channel", "dual lens",
            "front and rear camera", "parking mode", "loop recording",
            "G-sensor", "GPS tracking", "night vision", "wide angle lens",
            "1080p", "4K recording", "cloud storage", "WiFi dashcam",
            "motion detection", "time lapse"
        ],
        "use_cases": [
            "fleet management", "insurance telematics", "driver safety",
            "accident documentation", "vehicle tracking", "commercial fleet",
            "taxi camera", "uber camera", "ride-share monitoring",
            "truck camera", "bus camera", "evidence recording"
        ],
        "related_terms": [
            "vehicle telematics", "automotive IoT", "connected car",
            "smart vehicle", "automotive electronics"
        ]
    },
    
    "in_cabin": {
        "primary": [
            "in-cabin monitoring", "driver monitoring", "cabin camera",
            "driver monitoring system", "DMS", "in-vehicle monitoring",
            "driver facing camera", "interior camera"
        ],
        "technologies": [
            "DMS", "driver monitoring system", 
            "ADAS", "advanced driver assistance system", "advanced driver assistance",
            "telematics", "fleet telematics", "vehicle telematics",
            "fatigue detection", "drowsiness detection", "distraction detection",
            "eye tracking", "gaze detection", "facial recognition",
            "AI monitoring", "computer vision", "driver behavior",
            "attention monitoring", "yawn detection", "head pose tracking",
            "seat belt detection", "phone usage detection",
            "driver identification", "biometric authentication"
        ],
        "use_cases": [
            "fleet safety", "commercial vehicles", "ride-share monitoring",
            "driver coaching", "safety compliance", "insurance risk assessment",
            "truck safety", "bus driver monitoring", "delivery fleet",
            "driver training", "accident prevention", "risk management"
        ],
        "related_terms": [
            "automotive safety", "driver assistance", "vehicle safety systems",
            "smart cabin", "intelligent vehicle", "automotive AI"
        ]
    },
    
    "body_cam": {
        "primary": [
            "body camera", "body-worn camera", "BWC", "body cam",
            "wearable camera", "personal camera", "chest camera",
            "shoulder camera", "clip-on camera"
        ],
        "technologies": [
            "police camera", "law enforcement camera", "evidence camera",
            "HD recording", "night vision", "GPS tagging", "WiFi upload",
            "cloud storage", "pre-event recording", "tamper-proof",
            "encryption", "live streaming", "rugged design",
            "long battery life", "water resistant", "shock resistant"
        ],
        "use_cases": [
            "law enforcement", "police", "security personnel", 
            "event recording", "evidence collection", "security guard",
            "parking enforcement", "traffic officer", "first responder",
            "emergency services", "loss prevention", "retail security",
            "campus security", "hospital security", "transportation security"
        ],
        "related_terms": [
            "public safety", "security equipment", "surveillance",
            "wearable technology", "personal safety device"
        ]
    },
    
    "ip_camera": {
        "primary": [
            "IP camera", "network camera", "surveillance camera",
            "security camera", "CCTV", "internet camera",
            "WiFi camera", "wireless camera", "smart camera"
        ],
        "technologies": [
            "CCTV", "PTZ camera", "pan tilt zoom",
            "PoE camera", "power over ethernet",
            "wireless camera", "WiFi camera", "4G camera",
            "AI camera", "smart camera", "edge AI", "AI analytics",
            "facial recognition", "object detection", "motion tracking",
            "night vision", "IR camera", "thermal camera",
            "4K camera", "HD camera", "cloud storage",
            "NVR", "network video recorder", "video management system",
            "two-way audio", "weatherproof", "vandal-proof"
        ],
        "use_cases": [
            "video surveillance", "security systems", "monitoring solution",
            "perimeter security", "retail surveillance", "office security",
            "warehouse monitoring", "parking lot security", "building security",
            "home security", "smart home", "remote monitoring",
            "construction site", "traffic monitoring", "city surveillance"
        ],
        "related_terms": [
            "video analytics", "intelligent video", "IoT security",
            "smart building", "security solutions", "surveillance technology"
        ]
    },
    
    "access_control": {
        "primary": [
            "access control", "door access", "entry system",
            "access management", "door controller", "access reader",
            "entry control", "security access"
        ],
        "technologies": [
            "RFID", "card reader", "proximity reader",
            "biometric access", "fingerprint reader", "fingerprint scanner",
            "facial recognition access", "face recognition system",
            "keyless entry", "smart lock", "electronic lock",
            "mobile access", "smartphone access", "Bluetooth access",
            "PIN pad", "keypad entry", "multi-factor authentication",
            "cloud access control", "wireless access control",
            "time attendance", "visitor management"
        ],
        "use_cases": [
            "building security", "office access", "smart lock",
            "visitor management", "employee access", "time and attendance",
            "gym access", "hotel lock", "apartment access",
            "parking access", "gate control", "turnstile",
            "enterprise security", "commercial building", "residential building"
        ],
        "related_terms": [
            "physical security", "identity management", "security infrastructure",
            "smart building", "building automation", "IoT security"
        ]
    },
    
    "beacon": {
        "primary": [
            "beacon", "BLE beacon", "Bluetooth beacon",
            "iBeacon", "Eddystone", "proximity beacon",
            "wireless beacon", "smart beacon"
        ],
        "technologies": [
            "BLE", "Bluetooth Low Energy", "proximity marketing",
            "indoor positioning", "indoor navigation", "RTLS",
            "real-time location", "asset tracking", "location tracking",
            "geofencing", "proximity detection", "contactless",
            "NFC", "ultra-wideband", "UWB"
        ],
        "use_cases": [
            "proximity marketing", "retail analytics", "customer engagement",
            "location-based services", "indoor navigation", "wayfinding",
            "asset tracking", "inventory management", "equipment tracking",
            "museum guide", "exhibition guide", "conference navigation",
            "hospital asset tracking", "warehouse tracking", "people tracking"
        ],
        "related_terms": [
            "IoT", "location technology", "proximity technology",
            "retail technology", "smart retail", "location intelligence"
        ]
    },
    
    "rapidise_core": {
        "primary": [
            "ODM", "original design manufacturer", "OEM", "original equipment manufacturer",
            "contract manufacturer", "white label", "private label",
            "electronics manufacturer", "hardware manufacturer"
        ],
        "technologies": [
            "IoT", "Internet of Things", "connected devices",
            "embedded systems", "firmware development", "hardware design",
            "AI edge", "edge computing", "computer vision",
            "image processing", "video analytics", "machine learning",
            "wireless connectivity", "cloud integration", "mobile app"
        ],
        "use_cases": [
            "smart devices", "consumer electronics", "automotive electronics",
            "security products", "IoT solutions", "connected products",
            "B2B electronics", "enterprise hardware", "industrial IoT"
        ],
        "related_terms": [
            "technology integration", "product development", "hardware solutions",
            "electronics design", "manufacturing partner", "technology supplier"
        ]
    }
}

# Negative indicators - companies likely NOT relevant
NEGATIVE_KEYWORDS = [
    # Pure software/cloud companies
    "software only", "SaaS", "cloud platform", "web app", "mobile app",
    "software development", "IT services", "consulting",
    
    # Unrelated industries
    "fashion", "apparel", "clothing", "textile",
    "food", "beverage", "restaurant", "catering",
    "pharmaceutical", "medicine", "healthcare software",
    "finance", "banking", "fintech", "cryptocurrency", "blockchain",
    "gaming", "video game", "entertainment software",
    "publishing", "media", "advertising agency",
    "real estate", "property management",
    
    # Service-only companies
    "marketing agency", "design agency", "consulting firm",
    "training", "education platform", "e-learning"
]

# ODM potential indicators
ODM_INDICATORS = [
    # Manufacturing capabilities
    "manufacturer", "manufacturing", "factory", "production facility",
    "contract manufacturing", "OEM", "ODM", "white label", "private label",
    
    # Hardware/electronics terms
    "hardware", "electronics", "circuit", "PCB", "embedded",
    "semiconductor", "chip", "sensor", "module",
    
    # Product development
    "product development", "R&D", "research and development",
    "design and manufacturing", "turnkey solution",
    "custom design", "prototype", "product design",
    
    # Distribution/integration
    "system integrator", "distributor", "value-added reseller",
    "solutions provider", "technology partner"
]

def get_all_keywords_for_product(product_name: str) -> list:
    """
    Get all keywords for a specific product category.
    
    Args:
        product_name: One of the product keys (dashcam, in_cabin, etc.)
    
    Returns:
        List of all keywords for that product
    """
    if product_name not in RAPIDISE_PRODUCT_KEYWORDS:
        return []
    
    product_data = RAPIDISE_PRODUCT_KEYWORDS[product_name]
    all_keywords = []
    
    for category in ["primary", "technologies", "use_cases", "related_terms"]:
        if category in product_data:
            all_keywords.extend(product_data[category])
    
    return all_keywords

def get_all_keywords() -> dict:
    """
    Get all keywords organized by product category.
    
    Returns:
        Dictionary mapping product names to their complete keyword lists
    """
    return {
        product: get_all_keywords_for_product(product)
        for product in RAPIDISE_PRODUCT_KEYWORDS.keys()
    }
