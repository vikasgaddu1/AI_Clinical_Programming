---
description: Profile raw clinical data — types, distinct values, missing counts, date formats, CT mapping candidates. Cross-checks against annotated CRF.
user-invocable: true
argument-hint: "[csv_path]"
---

# Profile Raw Clinical Data

Analyze a raw clinical dataset and generate a comprehensive data profile report.

## Usage
- `/profile-data` — Profile the raw data from config (`paths.raw_data` in `orchestrator/config.yaml`)
- `/profile-data path/to/data.csv` — Profile a specific CSV file

## Instructions

1. **Read the CSV file** using Python pandas or by reading it directly.

2. **For each column, report:**
   - Variable name and inferred data type (numeric, character, date-like)
   - Number of non-missing values and missing count (with percentage)
   - Distinct value count
   - If < 20 distinct values: show ALL values with frequency counts
   - If >= 20 distinct values: show top 10 most frequent with counts, plus min/max
   - For numeric columns: min, max, mean, median
   - For date-like columns: min/max dates, identify date formats present

3. **Cross-check against annotated CRF** (path from `paths.annotated_crf` in config):
   - Read the CRF file
   - For each CRF field, check if corresponding raw data column exists
   - Flag any CRF fields missing from the raw data
   - Flag any raw data columns not mapped in the CRF

4. **Data quality assessment:**
   - Flag columns with mixed case values (e.g., "Male", "MALE", "male")
   - Flag columns with potential date values in non-standard formats
   - Flag columns that appear to need controlled terminology mapping
   - Flag any potential coding issues (numeric codes mixed with text)
   - Identify columns with > 5% missing values

5. **Generate summary** suitable for the Spec Builder agent:
   - Recommended SDTM variable mapping for each raw column
   - Which R functions from the registry should be applied
   - Which columns need human decisions

## Output Format
Present results as formatted markdown tables for readability.
