# Company Relevance Analysis System - Usage Guide

## Overview
This system identifies potential ODM customers for Rapidise from the CES 2026 company list through a three-stage pipeline:
1. **Categorization** - Tier companies by data availability
2. **Enrichment** - Scrape websites/LinkedIn for comprehensive data
3. **Analysis** - Use LLM to score relevance and ODM potential

---

## Prerequisites

### Required Python Packages
```bash
pip install pandas requests duckduckgo-search crawl4ai ollama
```

### Local LLM Setup
Ensure Ollama is installed and running with llama3.1:
```bash
ollama pull llama3.1
```

---

## Pipeline Execution

### Step 1: Categorize Companies
Categorizes companies into 5 data tiers and validates URLs.

```bash
cd src
python categorize_companies.py
```

**Input:** `data/Companies/CES 2026_non_asian_validated_CLEAN.csv`

**Outputs:**
- `CES_2026_CATEGORIZED.csv` - Main output with tier classifications
- `CES_2026_GOLD.csv` - Tier 1: Summary + Website + LinkedIn
- `CES_2026_SILVER.csv` - Tier 2: Website + LinkedIn
- `CES_2026_BRONZE_WEB.csv` - Tier 3: Website only
- `CES_2026_BRONZE_LI.csv` - Tier 4: LinkedIn only
- `CES_2026_COPPER.csv` - Tier 5: Summary only

**Features:**
- URL validation (checks accessibility)
- DuckDuckGo search for missing websites
- Progress indicators

**Estimated Time:** 5-10 minutes (depending on DuckDuckGo searches)

---

### Step 2: Enrich with Web Scraping
Scrapes websites and LinkedIn pages using Crawl4AI.

```bash
python enrich_with_crawl4ai.py
```

**Input:** `data/Companies/CES_2026_CATEGORIZED.csv`

**Output:** `CES_2026_ENRICHED.csv` with scraped summaries

**Features:**
- Async batch processing (10 companies at a time)
- Progress saving after each batch
- Handles scrape failures gracefully
- 2-second delay between requests

**Estimated Time:** 2-4 hours for 1700+ companies

**Important Notes:**
- Process runs in GOLD → COPPER priority order
- Progress saved incrementally (can resume if interrupted)
- Some sites may block scraping (logged as errors)
- LinkedIn scraping may be limited without authentication

---

### Step 3: Analyze Relevance
Uses llama3.1 to score companies and identify ODM potential.

```bash
python analyze_relevance.py
```

**Input:** `data/Companies/CES_2026_ENRICHED.csv`

**Outputs:**
- `CES_2026_HIGH_RELEVANCE.csv` - Score 7-10 (top prospects)
- `CES_2026_MEDIUM_RELEVANCE.csv` - Score 4-6 (worth reviewing)
- `CES_2026_ALL_SCORED.csv` - Complete results
- `CES_2026_NEEDS_REVIEW.csv` - Failed analysis cases

**Features:**
- Structured JSON prompts for consistent analysis
- Progress saving every 50 companies
- Detailed scoring (0-10) and reasoning
- Product category matching
- ODM potential assessment

**Estimated Time:** 3-5 hours for 1700+ companies (local LLM)

**Scoring Guide:**
- **9-10:** Perfect match - manufactures similar hardware
- **7-8:** Strong match - related industry, clear fit
- **5-6:** Moderate match - some overlap
- **3-4:** Weak match - tangential relationship
- **0-2:** No match - unrelated/software-only

---

## Testing Strategy

### Small Batch Test (Recommended First Step)
Test on 50 companies before full run:

1. **Create test subset:**
```python
import pandas as pd
df = pd.read_csv("data/Companies/CES 2026_non_asian_validated_CLEAN.csv")
df.head(50).to_csv("data/Companies/CES_TEST_50.csv", index=False)
```

2. **Modify INPUT_CSV in each script:**
```python
INPUT_CSV = os.path.join(BASE_DIR, "data", "Companies", "CES_TEST_50.csv")
```

3. **Run pipeline on test set**
4. **Review output quality**
5. **Adjust if needed, then run full dataset**

---

## Output File Structure

### CES_2026_CATEGORIZED.csv
New columns added:
- `Data_Tier` - GOLD/SILVER/BRONZE_WEB/BRONZE_LI/COPPER
- `Website_Valid` - Boolean
- `LinkedIn_Valid` - Boolean
- `Website_Found_By_Search` - URL found via DuckDuckGo
- `Processing_Notes` - Any issues/notes

### CES_2026_ENRICHED.csv
Additional columns:
- `Scraped_Summary` - Combined website + LinkedIn content
- `Scrape_Status` - success/no_new_data/failed
- `Scrape_Errors` - Error messages if failed

### CES_2026_HIGH_RELEVANCE.csv
Analysis columns:
- `ODM_Potential` - YES/NO/MAYBE
- `Relevance_Score` - 0-10 integer
- `Matched_Products` - Comma-separated list
- `Key_Indicators` - Keywords that triggered match
- `Reasoning` - One-sentence explanation
- `Concerns` - Red flags (if any)
- `Analysis_Status` - completed/failed

---

## Troubleshooting

### Issue: Crawl4AI not installed
```bash
pip install 'crawl4ai[all]'
```

### Issue: Ollama not responding
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service if needed
ollama serve
```

### Issue: DuckDuckGo rate limiting
- Increase `CRAWL_DELAY` in `categorize_companies.py`
- Process in smaller batches

### Issue: Out of memory during LLM analysis
- Reduce batch size in `analyze_relevance.py`
- Limit `num_predict` in LLM options
- Process in chunks and merge results

### Issue: Resume interrupted processing
All scripts save progress incrementally:
- Categorization: No easy resume (fast process)
- Enrichment: Progress saved after each batch
- Analysis: Progress saved every 50 companies

To resume: Check output file, skip already-processed rows

---

## Configuration Options

### Adjusting Crawl Settings
In `enrich_with_crawl4ai.py`:
```python
CRAWL_DELAY = 2  # Increase to 5+ if rate limited
MAX_RETRIES = 2  # Increase for flaky sites
TIMEOUT = 30     # Increase for slow sites
BATCH_SIZE = 10  # Reduce if memory issues
```

### Adjusting LLM Settings
In `analyze_relevance.py`:
```python
LLM_MODEL = "llama3.1"      # Or "deepseek-llm:7b"
LLM_TEMPERATURE = 0.3       # Lower = more consistent
num_predict = 500           # Max response tokens
```

### Relevance Thresholds
Modify in output export section:
```python
high_df = df[df['Relevance_Score'] >= 7]    # Adjust threshold
medium_df = df[df['Relevance_Score'] >= 4]  # Adjust threshold
```

---

## Expected Results

### Typical Distribution (estimated):
- **High Relevance (7-10):** 5-10% of companies (~85-170)
- **Medium Relevance (4-6):** 15-25% of companies (~255-425)
- **Low Relevance (0-3):** 65-80% of companies (~1100-1360)

### Top Company Profiles:
- Electronics manufacturers
- Camera/surveillance companies
- Automotive electronics suppliers
- IoT device makers
- Security equipment manufacturers
- Fleet management solution providers

---

## Support Files

### rapidise_keywords.py
Configuration file with keyword mappings. Edit to:
- Add new product categories
- Refine keyword lists
- Adjust ODM indicators
- Add negative keywords

**No execution needed** - imported by other scripts.

---

## Next Steps After Analysis

1. **Review HIGH_RELEVANCE.csv** - Top prospects for outreach
2. **Manual validation** - Verify LLM assessments on high scorers
3. **Export for CRM** - Import scored list into sales pipeline
4. **Follow-up research** - Deep dive on top 50-100 companies
5. **Prepare outreach** - Customize messaging by matched products

---

## Questions?

Check logs in terminal output for detailed processing information.
Each script prints progress indicators and summary statistics.
