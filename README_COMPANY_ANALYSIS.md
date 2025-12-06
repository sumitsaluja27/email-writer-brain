# 🎯 Company Relevance Analysis System

**AI-powered pipeline to identify potential ODM customers for Rapidise from CES 2026 exhibitor list**

---

## 📋 Overview

This system automates the process of finding companies that could be potential ODM (Original Design Manufacturer) partners for Rapidise by:

1. **Categorizing** 1700+ companies by data availability (5 tiers)
2. **Enriching** company profiles via web scraping (Crawl4AI)
3. **Analyzing** relevance using local LLM (llama3.1)

**Key Features:**
- ✅ Multi-tier data processing (prioritizes companies with rich data)
- ✅ Async web scraping with Crawl4AI
- ✅ DuckDuckGo search for missing websites
- ✅ Local LLM analysis (no API costs)
- ✅ Comprehensive product keyword matching
- ✅ Progress saving & resume capability

---

## 🏗️ System Architecture

```
Input CSV (CES 2026 companies)
         ↓
┌────────────────────────┐
│ 1. CATEGORIZATION      │  → 5 data tiers (GOLD → COPPER)
│    categorize_companies │  → URL validation
└────────────────────────┘  → Find missing websites
         ↓
┌────────────────────────┐
│ 2. ENRICHMENT          │  → Scrape websites
│    enrich_with_crawl4ai │  → Scrape LinkedIn
└────────────────────────┘  → Create comprehensive summaries
         ↓
┌────────────────────────┐
│ 3. ANALYSIS            │  → LLM scoring (0-10)
│    analyze_relevance    │  → Product matching
└────────────────────────┘  → ODM potential assessment
         ↓
Output CSVs (High/Medium/Low relevance)
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/apple/Downloads/Automation\ projects/AI\ agent/Dashcam\ AI\ agent/email_writer
python3 -m pip install -r requirements.txt
```

### 2. Verify Ollama Setup

```bash
ollama list
# Should show llama3.1
```

If not installed:
```bash
ollama pull llama3.1
```

### 3. Run the Pipeline

```bash
cd src

# Step 1: Categorize companies by data tier
python3 categorize_companies.py

# Step 2: Enrich with web scraping (2-4 hours)
python3 enrich_with_crawl4ai.py

# Step 3: Analyze relevance with LLM (3-5 hours)
python3 analyze_relevance.py
```

---

## 📁 Project Structure

```
email_writer/
├── src/
│   ├── rapidise_keywords.py          # Product keyword mappings
│   ├── categorize_companies.py       # Tier companies by data
│   ├── enrich_with_crawl4ai.py      # Web scraping pipeline
│   └── analyze_relevance.py          # LLM analysis
├── data/
│   └── Companies/
│       ├── CES 2026_non_asian_validated_CLEAN.csv  # INPUT
│       ├── CES_2026_CATEGORIZED.csv                # After step 1
│       ├── CES_2026_ENRICHED.csv                   # After step 2
│       ├── CES_2026_HIGH_RELEVANCE.csv            # FINAL OUTPUT
│       ├── CES_2026_MEDIUM_RELEVANCE.csv          # FINAL OUTPUT
│       └── CES_2026_ALL_SCORED.csv                # FINAL OUTPUT
├── docs/
│   └── USAGE_GUIDE.md                # Detailed documentation
└── requirements.txt                  # Python dependencies
```

---

## 🎯 Output Files

| File | Description | Use Case |
|------|-------------|----------|
| `CES_2026_HIGH_RELEVANCE.csv` | Score 7-10 | **Top prospects** - Priority outreach |
| `CES_2026_MEDIUM_RELEVANCE.csv` | Score 4-6 | Worth reviewing manually |
| `CES_2026_ALL_SCORED.csv` | All companies | Complete analysis record |
| `CES_2026_NEEDS_REVIEW.csv` | Failed/insufficient | Manual research needed |

---

## 🔍 Data Tiers

Companies are categorized into 5 tiers based on data availability:

| Tier | Data Available | Processing Priority |
|------|---------------|-------------------|
| **GOLD** | Summary + Website + LinkedIn | 🥇 Highest |
| **SILVER** | Website + LinkedIn | 🥈 High |
| **BRONZE_WEB** | Website only | 🥉 Medium |
| **BRONZE_LI** | LinkedIn only | 🥉 Medium |
| **COPPER** | Summary only | ⚪ Low |

---

## 🧠 Product Categories

The system matches companies against **7 Rapidise product lines**:

1. **Dashcams** - Vehicle cameras, DVR, fleet management
2. **In-Cabin Monitoring** - DMS, ADAS, driver safety, telematics
3. **Body Cameras** - BWC, law enforcement, security
4. **IP Cameras** - Surveillance, CCTV, smart cameras
5. **Access Control** - Biometric, RFID, smart locks
6. **Beacons** - BLE, proximity marketing, asset tracking
7. **Core** - General ODM indicators, electronics manufacturing

Each category has **100+ keywords** covering:
- Primary terms
- Technologies
- Use cases
- Related terminology

---

## 📊 Expected Results

Based on typical CES exhibitor profiles:

- **High Relevance (7-10):** ~5-10% (85-170 companies)
  - Electronics manufacturers
  - Camera/IoT companies
  - Automotive electronics suppliers
  
- **Medium Relevance (4-6):** ~15-25% (255-425 companies)
  - Adjacent industries
  - Potential distributors
  
- **Low Relevance (0-3):** ~65-80% (1100-1360 companies)
  - Unrelated industries
  - Software-only companies

---

## ⚙️ Configuration

### Crawl Settings
Edit `enrich_with_crawl4ai.py`:
```python
CRAWL_DELAY = 2      # Seconds between requests
BATCH_SIZE = 10      # Companies per batch
TIMEOUT = 30         # Request timeout
```

### LLM Settings
Edit `analyze_relevance.py`:
```python
LLM_MODEL = "llama3.1"        # Or "deepseek-llm:7b"
LLM_TEMPERATURE = 0.3         # 0.0 = deterministic
```

### Keyword Customization
Edit `rapidise_keywords.py` to add/refine product keywords.

---

## 🧪 Testing

**Recommended:** Test on 50 companies first:

```python
import pandas as pd
df = pd.read_csv("data/Companies/CES 2026_non_asian_validated_CLEAN.csv")
df.head(50).to_csv("data/Companies/CES_TEST_50.csv", index=False)
```

Then modify `INPUT_CSV` in each script to use test file.

---

## 📚 Documentation

- **[USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** - Complete user guide
- **[task.md](../.gemini/antigravity/brain/.../task.md)** - Development checklist
- **Script docstrings** - In-code documentation

---

## 🛠️ Troubleshooting

### Crawl4AI Issues
```bash
pip install 'crawl4ai[all]'
playwright install
```

### Ollama Not Responding
```bash
ollama serve
ollama list
```

### Rate Limiting
Increase `CRAWL_DELAY` in scripts

### Memory Issues
Reduce `BATCH_SIZE` in scripts

---

## 🎓 Technologies Used

- **Pandas** - Data manipulation
- **Crawl4AI** - Intelligent web scraping
- **DuckDuckGo Search** - Free search API
- **Ollama** - Local LLM inference
- **Llama 3.1** - Language model for analysis
- **AsyncIO** - Concurrent processing

---

## 📈 Next Steps After Analysis

1. ✅ Review `CES_2026_HIGH_RELEVANCE.csv`
2. 🔍 Manually validate top 50 companies
3. 📧 Prepare customized outreach messages
4. 💼 Import to CRM/sales pipeline
5. 🎯 Schedule meetings at CES 2026

---

## 👥 Support

For questions or issues:
- Check `docs/USAGE_GUIDE.md`
- Review terminal output logs
- Verify Ollama is running
- Check input file paths

---

## 📄 License

Internal Rapidise project - For business development use only.

---

**Built with ❤️ for Rapidise Business Development Team**
