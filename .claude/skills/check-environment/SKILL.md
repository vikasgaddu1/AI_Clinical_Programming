---
description: Verify all prerequisites for the SDTM orchestrator — Python packages, R availability, R packages, config, study data, function registry, CT lookup, IG content, database, API key.
user-invocable: true
---

# Check Environment

Verify that all prerequisites for the SDTM orchestrator are installed and configured.

## Usage
- `/check-environment` — Run all environment checks

## Instructions

Run each check below and report PASS, FAIL, or SKIP with actionable fix instructions.

### 1. Python Packages
Run: `python -c "import yaml, pandas, pyarrow, openpyxl, rich"`
- If any import fails, report which package is missing
- Fix: `pip install pyyaml pandas pyarrow openpyxl rich`
- Also check: `python -c "import anthropic"` (optional — only needed for LLM mode)

### 2. R Availability
Run: `Rscript --version`
- Report R version
- If R is not found, suggest installing R 4.x and adding to PATH

### 3. R Packages
Run: `Rscript -e "library(arrow); library(haven); cat('OK\n')"`
- If either package fails, report which is missing
- Fix: `Rscript -e "install.packages(c('arrow', 'haven'), repos='https://cloud.r-project.org')"`

### 4. Configuration File
- Check `orchestrator/config.yaml` exists (or `studies/{study}/config.yaml` if in multi-study mode)
- Verify it's valid YAML (parse it)
- Check all paths resolve to existing files

### 5. Study Data
- Read `paths.raw_data` from config and check the file exists
- Verify it has STUDYID and SUBJID columns at minimum
- Report row count and column count

### 6. Function Registry
- Check `r_functions/function_registry.json` exists and is valid JSON
- Report the number of registered functions
- If in multi-study mode, also check for study-specific registries

### 7. CT Lookup
- Check `macros/ct_lookup.csv` exists
- Verify it has columns: CODELIST, RAW_VALUE, CT_VALUE
- Report number of entries

### 8. SDTM IG Content
- Check `sdtm_ig_db/sdtm_ig_content/{domain}_domain.md` exists for the active domain
- Check `sdtm_ig_db/sdtm_ig_content/general_assumptions.md` exists

### 9. Database (Optional)
- SKIP if database section not configured or if psycopg2 not installed
- If configured, try connecting to PostgreSQL

### 10. API Key (Optional)
- Check if `ANTHROPIC_API_KEY` is set in environment
- SKIP if `use_llm: false` in config.yaml
- Do NOT display the key value — only report whether it's set

## Output Format
Present as a checklist:
```
[PASS] Python packages — all required packages installed
[PASS] R availability — R 4.4.2
[FAIL] R packages — arrow not installed (run: install.packages("arrow"))
[PASS] Configuration — orchestrator/config.yaml valid
[PASS] Study data — raw_dm.csv (300 rows, 16 columns)
[PASS] Function registry — 3 functions registered
[PASS] CT lookup — 55 entries across 4 codelists
[PASS] IG content — DM domain and general assumptions available
[SKIP] Database — not configured
[SKIP] API key — use_llm: false
```
