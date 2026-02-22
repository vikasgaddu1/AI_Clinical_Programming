---
description: Trace any SDTM variable end-to-end through raw data, spec, production code, QC code, comparison report, and validation — produces a complete traceability table. Perfect for capstone Exercise C.1.
user-invocable: true
argument-hint: "<VARNAME> [DOMAIN]"
---

# Trace Variable Through Pipeline

Follow a single SDTM variable through every stage of the pipeline and produce a full traceability report. Great for understanding the spec-driven architecture and for capstone Exercise C.1.

## Usage
- `/trace-variable RACE` — trace RACE in the default domain (DM)
- `/trace-variable RACE DM` — trace RACE in the DM domain explicitly
- `/trace-variable SEX DM` — trace SEX through all DM pipeline artifacts
- `/trace-variable BRTHDTC DM` — trace birth date derivation end-to-end

## Instructions

1. **Parse arguments.** Extract VARNAME (required) and DOMAIN (default: DM from config).

2. **Stage 1 — Raw Data.** Read `study_data/raw_dm.csv` (or the configured raw data path).
   - Find the source column(s) that map to VARNAME (look at column names; also check `raw_dm_mapping_spec.csv` if it exists)
   - Count distinct values and their frequencies
   - Note any messy values, mixed formats, or missing data

3. **Stage 2 — SDTM IG Requirements.** Use the `sdtm_variable_lookup` MCP tool:
   - Look up VARNAME in the IG for the given DOMAIN
   - Extract: required/expected status, codelist code (if any), derivation rules
   - Note if extensible or non-extensible codelist

4. **Stage 3 — Draft Spec.** Read `orchestrator/outputs/specs/{domain}_mapping_spec.json`:
   - Find the entry where `sdtm_variable == VARNAME` (case-insensitive)
   - Extract: source_variable, codelist_code, derivation, human_decision_required, decision_options
   - If file doesn't exist, note "pipeline not yet run"

5. **Stage 4 — Approved Spec.** Read `orchestrator/outputs/specs/{domain}_mapping_spec_approved.json`:
   - Find VARNAME entry
   - Extract: approved_mapping_logic, decision_made, rationale
   - If file doesn't exist, note "human review not yet completed"

6. **Stage 5 — Production R Code.** Read `orchestrator/outputs/programs/{domain}_production.R`:
   - Search (grep) for VARNAME (case-insensitive, since R uses it as a string)
   - Extract the relevant lines (± 5 lines context)
   - Identify: which R function is used (iso_date, derive_age, assign_ct, or custom), which codelist

7. **Stage 6 — QC R Code.** Read `orchestrator/outputs/qc/{domain}_qc.R`:
   - Same search as production
   - Note if the QC approach differs from production (different function, different codelist, etc.)

8. **Stage 7 — Comparison Report.** Read `orchestrator/outputs/qc/{domain}_compare_report.txt`:
   - Search for VARNAME
   - Extract: MATCH or MISMATCH, any difference counts or example differences

9. **Stage 8 — Validation.** Read `orchestrator/outputs/validation/p21_report.txt`:
   - Search for VARNAME
   - Extract: PASS or FAIL, any validation issue descriptions

10. **Produce the Traceability Report** in this format:

```
=============================================================
VARIABLE TRACEABILITY REPORT: {VARNAME} ({DOMAIN} domain)
Generated: {timestamp}
=============================================================

STAGE 1: Raw Data
  Source column(s): ___
  Distinct values: ___ (e.g., "M"=150, "F"=148, "OTHER"=2)
  Data quality notes: ___

STAGE 2: SDTM IG
  Required/Expected: ___
  Codelist: ___ (extensible: yes/no)
  Derivation rule: ___

STAGE 3: Draft Spec
  Status: FOUND / NOT FOUND / PIPELINE NOT RUN
  Codelist in spec: ___
  Human decision required: yes/no
  Decision options offered: ___

STAGE 4: Approved Spec
  Status: FOUND / NOT FOUND / HUMAN REVIEW NOT DONE
  Approved mapping: ___
  Decision made: ___
  Rationale: ___

STAGE 5: Production R Code
  Status: FOUND / NOT FOUND
  R function used: ___
  Codelist applied: ___
  Key lines:
    [line numbers and code]

STAGE 6: QC R Code
  Status: FOUND / NOT FOUND
  R function used: ___
  Same as production: yes/no
  Differences (if any): ___

STAGE 7: Comparison
  Result: MATCH / MISMATCH / FILE NOT FOUND
  Details: ___

STAGE 8: Validation
  Result: PASS / FAIL / FILE NOT FOUND
  Details: ___

=============================================================
TRACEABILITY CHAIN SUMMARY
  Raw → Spec → Code → QC → Compare → Validate
  [GOOD if all MATCH/PASS, flag any gaps]
=============================================================

REFLECTION QUESTIONS (for training):
  1. At which stage could an error in {VARNAME} mapping be caught first?
  2. If the spec listed the wrong codelist, which stages would surface that?
  3. Is the mapping logic consistent between production and QC? Why does that matter?
=============================================================
```

11. **Handle missing files gracefully.** If a stage's file doesn't exist, mark it as "NOT RUN" and continue. Don't abort the entire trace.

12. **Flag anything unusual:** mismatched codelist between spec and code, different approaches in production vs QC, validation failures, or raw values that don't map to any CT value.
