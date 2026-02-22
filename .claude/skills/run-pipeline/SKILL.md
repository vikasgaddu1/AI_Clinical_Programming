---
description: Execute the SDTM orchestrator pipeline — full pipeline or individual stages (spec_build, spec_review, human_review, production, qc, compare, validate). Works for any domain and study.
user-invocable: true
argument-hint: "[stage]"
---

# Run SDTM Pipeline

Run the SDTM orchestrator pipeline for the current study and domain.

## Usage
- `/run-pipeline` — Run the full pipeline (all 7 stages)
- `/run-pipeline spec_build` — Run only the spec building stage
- `/run-pipeline production` — Run only the production programming stage
- `/run-pipeline validate` — Run only the validation stage

## Instructions

1. **Read config to determine the active study and domain:**
   - Read `orchestrator/config.yaml` for the domain (default: DM)
   - If running multi-study mode, check for `studies/{study}/config.yaml`

2. **Check prerequisites first:**
   - Run `Rscript --version` to verify R is available
   - Run `python -c "import yaml, pandas, pyarrow, openpyxl"` to verify Python packages
   - Verify config YAML exists

3. **Determine the stage to run:**
   - If the user specified a stage argument, use `--stage STAGE`
   - Otherwise run the full pipeline (no --stage flag)

4. **Run the pipeline:**
   ```bash
   # Single-study legacy mode
   python orchestrator/main.py --domain {domain} [--stage STAGE]

   # Multi-study mode
   python orchestrator/main.py --study {study_name} --domain {domain} [--stage STAGE]
   ```

5. **If the run fails, diagnose:**
   - If R script fails: check if `arrow` and `haven` R packages are installed (`Rscript -e "library(arrow); library(haven)"`)
   - If file not found: verify paths in config YAML resolve correctly from project root
   - If spec review fails: examine the review comments and suggest fixes
   - If comparison shows mismatch: read the compare report at `{output_dir}/qc/{domain}_compare_report.txt`

6. **Report results in three sections:**

   **(A) Artifact Inventory:**
   | Artifact | Path | Status |
   |----------|------|--------|
   List each expected artifact with EXISTS/MISSING status:
   - Draft spec, Approved spec, Production R script, Production dataset (.parquet)
   - QC R script, QC dataset, Compare report, P21 report, Define metadata, P21 spec sheet
   - XPT file (if write_xpt enabled), HTML report (if --report used)

   **(B) Quality Gate Summary:**
   | Gate | Result | Details |
   |------|--------|---------|
   - Spec Review: PASS/FAIL with review comments count
   - Production/QC Comparison: MATCH/MISMATCH with iteration count
   - P21 Validation: PASS/FAIL with issue count

   **(C) Next Steps:**
   - If all gates passed: "Pipeline complete — dataset is submission-ready"
   - If comparison mismatched: "Review compare report and re-run production/QC stages"
   - If validation failed: "Review P21 report issues and fix in spec or R code"
   - If HTML report exists: "Open {report_path} in browser for detailed review"

## Valid Stages
`spec_build`, `spec_review`, `human_review`, `production`, `qc`, `compare`, `validate`
