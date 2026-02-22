---
description: Run P21-style validation checks on an SDTM dataset — required variables, controlled terminology, ISO dates, USUBJID format, variable types/lengths.
user-invocable: true
argument-hint: "[dataset_path]"
---

# Validate SDTM Dataset

Run comprehensive P21-style validation checks on a generated SDTM dataset.

## Usage
- `/validate-dataset` — Validate the production dataset for the active domain
- `/validate-dataset path/to/dataset.parquet` — Validate a specific dataset

## Instructions

1. **Read config to determine the active domain and paths**, then read the dataset (Parquet preferred, also supports CSV and RDS):
   - Default path: `{output_dir}/datasets/{domain}.parquet`
   - Use pandas with pyarrow for Parquet files

2. **Read the approved spec:**
   - Path: `{output_dir}/specs/{domain}_mapping_spec_approved.json`
   - Fall back to draft spec if approved doesn't exist

3. **Read domain requirements from IG:**
   - Parse `sdtm_ig_db/sdtm_ig_content/{domain}_domain.md`
   - Extract the summary table for required/conditional variable list

4. **Run these validation checks:**

   **Required Variables:**
   - All IG-required variables present in dataset
   - All spec variables present in dataset

   **Controlled Terminology:**
   - For each variable with a codelist in the spec, verify values match the codelist definitions in `macros/ct_lookup.csv`

   **ISO 8601 Dates:**
   - ALL variables ending in DTC must match YYYY-MM-DD format

   **USUBJID:**
   - Must be unique per subject (no duplicate USUBJIDs for observations domains; unique for subject-level domains)
   - Must start with STUDYID
   - Must follow consistent format

   **Variable Types:**
   - Types (Char/Num) must match the IG specification for the domain

   **Required Fields Not Null:**
   - STUDYID, DOMAIN, USUBJID must never be null
   - Additional required fields per domain IG definition

   **Derivation Spot-Checks:**
   - For each derived variable in the spec, sample 5 records and verify the derivation is correct
   - Verify USUBJID = STUDYID + "-" + SUBJID (or per study convention)

4b. **Cross-reference comparison results:**
   - Read `{output_dir}/qc/{domain}_compare_report.txt`
   - If available, use `get_comparison_summary` MCP tool for structured diff analysis
   - Report whether production and QC datasets match alongside validation results

5. **Display results as a formatted table:**
   | Check | Status | Details |
   Show PASS/FAIL for each check with specific details on failures.

6. **Generate summary with overall verdict:**
   - Total checks run
   - Passed / Failed counts
   - Overall PASS or FAIL verdict
   - **Overall Verdict:**
     - **SUBMISSION READY**: Validation PASS + QC comparison MATCH
     - **VALIDATION PASS / QC MISMATCH**: Validation passed but prod/QC datasets differ — investigate
     - **VALIDATION FAIL**: Fix validation issues before submission
