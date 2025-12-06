# Project Structure - Clean & Organized

## 📁 Core Files Structure

```
email_writer/
│
├── 🎯 MASTER PIPELINES
│   ├── ces_pipeline.py              # CES 2026 analysis orchestrator
│   └── (complete_list pipeline - coming soon)
│
├── 🔧 UTILITIES
│   ├── enrich_companies.py          # Enrich final company lists
│   ├── filter_complete_list.py      # Filter complete list by industry
│   ├── scrape_company_descriptions.py # Scrape websites for descriptions
│   └── find_missing_websites.py     # Find missing websites via DuckDuckGo
│
├── 📂 src/ - CORE ANALYSIS SCRIPTS
│   ├── rapidise_capabilities.py     # 🔑 Creates RAG databases from PDFs
│   ├── rapidise_keywords.py         # Product keyword definitions
│   ├── categorize_companies.py      # CES Stage 1: Categorize by data tier
│   ├── enrich_with_crawl4ai.py     # CES Stage 2: Scrape websites
│   ├── find_relevant_companies.py   # CES Stage 3: RAG matching
│   └── analyze_relevance.py         # OLD: LLM-based analysis (archived)
│
├── 📂 data/Companies/ - DATA FILES
│   ├── CES_2026_*.csv              # CES analysis files
│   ├── COMPLETE_LIST_*.csv         # Complete list files
│   └── company_descriptions.csv    # Scraped descriptions (in progress)
│
├── 📂 knowledge_base/ - RAG DATABASES
│   ├── beacon_capabilities/
│   ├── body_cam_capabilities/
│   ├── dashcam_capabilities/
│   ├── in_cabin_capabilities/
│   ├── ip_camera_capabilities/
│   └── access_control_capabilities/
│
└── 📂 archive/old_scripts/ - ARCHIVED
    └── (Old test files and utilities)
```

## 🚀 How to Use

### CES 2026 Analysis

Run entire pipeline:
```bash
python ces_pipeline.py --all
```

Run specific stage:
```bash
python ces_pipeline.py --stage 1  # Categorization
python ces_pipeline.py --stage 2  # Enrichment
python ces_pipeline.py --stage 3  # RAG matching
python ces_pipeline.py --stage 4  # Final enrichment
```

### Complete List Analysis

Step 1: Filter by industry
```bash
python filter_complete_list.py
```

Step 2: Scrape company descriptions
```bash
python scrape_company_descriptions.py
```

Step 3: RAG matching (coming soon)

## 📊 Data Flow

```
CES Analysis:
Input → Categorize → Enrich → RAG Match → Enrich Final → Product CSVs

Complete List Analysis:
Input → Industry Filter → Scrape → RAG Match → Relevant Companies
```

## 🎯 Final Output Files

**CES 2026:**
- `CES_2026_DASHCAM_CLEAN.csv` (40 companies)
- `CES_2026_IN_CABIN_CLEAN.csv` (89 companies)
- `CES_2026_IP_CAMERA_CLEAN.csv` (64 companies)
- `CES_2026_BODY_CAM_CLEAN.csv` (14 companies)
- `CES_2026_BEACON_CLEAN.csv` (52 companies)

**Complete List:**
- `company_descriptions.csv` (in progress - 2,052 companies)
- (RAG-matched results - coming soon)
