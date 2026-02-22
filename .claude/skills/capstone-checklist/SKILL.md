---
description: Check capstone progress — reads all expected output files and reports which pipeline stages have run, which exercises are complete, and what's still missing. Use this to see where you are in the capstone at any time.
user-invocable: true
argument-hint: ""
---

# Capstone Progress Checklist

Check your capstone progress at a glance. This skill scans all expected output files and tells you what's done, what's missing, and what to do next.

## Usage
- `/capstone-checklist` — check all 7 pipeline stages + 4 exercises

## Instructions

1. **Read the active config** to determine output paths:
   - Read `orchestrator/config.yaml` → find `output_dir` and `domain`
   - Default: `orchestrator/outputs/`, domain `DM`

2. **Check Pipeline Stage Artifacts.** For each stage, check if the key output file exists:

   | Stage | Key File | Status |
   |-------|----------|--------|
   | 1. Spec Build | `{output_dir}/specs/{domain}_mapping_spec.json` | EXISTS / MISSING |
   | 2. Spec Review | `{output_dir}/specs/{domain}_mapping_spec.json` → check `review_comments` field | REVIEWED / DRAFT |
   | 3. Human Review | `{output_dir}/specs/{domain}_mapping_spec_approved.json` | EXISTS / MISSING |
   | 4. Production | `{output_dir}/programs/{domain}_production.R` AND `{output_dir}/datasets/{domain}.parquet` | EXISTS / MISSING |
   | 5. QC | `{output_dir}/qc/{domain}_qc.R` AND `{output_dir}/qc/{domain}_qc.parquet` | EXISTS / MISSING |
   | 6. Compare | `{output_dir}/qc/{domain}_compare_report.txt` | EXISTS / MISSING |
   | 7. Validate | `{output_dir}/validation/p21_report.txt` | EXISTS / MISSING |

   For files that exist, also check content:
   - Compare report: does it say MATCH or MISMATCH?
   - P21 report: does it say PASS or FAIL?
   - Approved spec: how many human decisions are recorded?

3. **Check Exercise Completion.** Use these heuristics:

   **Exercise C.1 (Trace RACE):** Check if approved spec contains a RACE entry with a decision recorded.

   **Exercise C.2 (Deliberate Error):** This is hard to detect automatically. Ask the user: "Did you complete Exercise C.2 — introduce a deliberate error and identify which stage caught it? (yes/no)"

   **Exercise C.3 (Add DTHFL):** Check if `{domain}_mapping_spec_approved.json` contains a DTHFL variable entry AND if the production R script contains "DTHFL".

   **Exercise C.4 (AE Extension Design):** Ask the user: "Did you complete Exercise C.4 — design the AE domain extension on paper? (yes/no)"

4. **Output a formatted progress report:**

```
=============================================================
CAPSTONE PROGRESS REPORT
Study: {study}    Domain: {domain}    Date: {timestamp}
=============================================================

PIPELINE STAGES
  [ ] or [X] 1. Spec Build      → {filename}  ({status})
  [ ] or [X] 2. Spec Review     → review_comments in spec  ({status})
  [ ] or [X] 3. Human Review    → {filename}  ({status})
  [ ] or [X] 4. Production      → R script + parquet  ({status})
  [ ] or [X] 5. QC              → QC R script + parquet  ({status})
  [ ] or [X] 6. Compare         → {filename}  (MATCH / MISMATCH)
  [ ] or [X] 7. Validate        → {filename}  (PASS / FAIL)

PIPELINE COMPLETION: X/7 stages done

EXERCISES
  [ ] or [X] C.1: Trace RACE Through Pipeline
  [ ] or [?] C.2: Introduce Deliberate Error  (self-reported)
  [ ] or [X] C.3: Add DTHFL to Spec
  [ ] or [?] C.4: Design AE Domain Extension  (self-reported)

EXERCISE COMPLETION: X/4 exercises done (Y confirmed, Z self-reported)

KEY QUALITY RESULTS
  Comparison: MATCH / MISMATCH / NOT RUN
  Validation: PASS / FAIL / NOT RUN
  Human decisions recorded: N variables
  Memory pitfalls recorded: N entries (check studies/{study}/memory/pitfalls.yaml)

=============================================================
WHAT TO DO NEXT
  {Smart suggestion based on what's missing}
=============================================================
```

5. **Provide a smart "what to do next" recommendation:**
   - If stages 1-3 not done: "Start by running the full pipeline: `python orchestrator/main.py --domain DM`"
   - If spec build done but no human review: "Run human review stage: `python orchestrator/main.py --domain DM --stage human_review`"
   - If pipeline complete but compare = MISMATCH: "Check the compare report and re-run: `python orchestrator/main.py --domain DM --stage production`"
   - If pipeline complete + MATCH + PASS: "Great! Move to Exercise C.1: `/trace-variable RACE DM`"
   - If C.1 done: "Move to Exercise C.2: edit the approved spec and change SEX codelist to a wrong value, then re-run validation"
   - If all done: "You've completed the capstone! Consider extending to the AE domain using Ch.3's ae_domain.md"
