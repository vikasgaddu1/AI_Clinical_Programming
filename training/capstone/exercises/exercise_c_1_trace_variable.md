# Exercise C.1: Trace RACE Through the Pipeline

## Objective
Follow the RACE variable from raw data through every pipeline stage to the validated dataset. This demonstrates the spec-driven architecture and end-to-end traceability.

## Time: 30 minutes

---

## Steps

### Step 1: Raw Data

Ask Claude Code:
```
Read study_data/raw_dm.csv and show me all distinct RACE values with their frequencies
```

> Distinct RACE values and counts:
> _________________________________________________________________
> _________________________________________________________________
>
> Are there any "Other Specify" values? What are they?
> _________________________________________________________________

### Step 2: IG Requirements

Ask Claude Code:
```
Use the sdtm_variable_lookup tool to look up RACE in the DM domain
```

> What codelist does the IG specify for RACE? ___________
> What valid controlled terminology values are listed? ___________
> What approaches does the IG offer for "Other Specify"? ___________

### Step 3: Draft Spec

Read the draft spec:
```
Read orchestrator/outputs/specs/dm_mapping_spec.json and show me the RACE variable entry
```

> What codelist_code is in the spec? ___________
> Is human_decision_required set to true? ___________
> How many decision_options are there? ___________

### Step 4: Human Decision

Read the approved spec:
```
Read orchestrator/outputs/specs/dm_mapping_spec_approved.json and show me what decision was made for RACE
```

> Which option was selected (A, B, or C)? ___________
> What is the approved mapping logic?
> _________________________________________________________________

### Step 5: Production R Code

```
Read orchestrator/outputs/programs/dm_production.R and find the section where RACE is mapped
```

> How is RACE mapped in the production code?
> _________________________________________________________________
> Does it use assign_ct()? With which codelist? ___________
> How are "Other Specify" values handled? ___________

### Step 6: QC R Code

```
Read orchestrator/outputs/qc/dm_qc.R and find the RACE mapping section
```

> How does the QC code handle RACE differently from production?
> _________________________________________________________________
> Does it arrive at the same output values? ___________

### Step 7: Comparison

```
Read orchestrator/outputs/qc/dm_compare_report.txt and check if RACE has any mismatches
```

> RACE comparison result: MATCH / MISMATCH
> If mismatch, what values differ? _________________________________

### Step 8: Validation

```
Read orchestrator/outputs/validation/p21_report.txt and check the RACE validation result
```

> RACE CT validation: PASS / FAIL
> Are all RACE values in codelist C74457? ___________

### Step 9: Traceability Summary

Fill in the complete RACE traceability chain:

| Stage | RACE Status |
|-------|-------------|
| Raw data | Values: _________________________ |
| IG requirement | Codelist: ________, Approaches: ________ |
| Draft spec | Codelist: ________, Decision required: ________ |
| Human decision | Option: ________, Logic: ________ |
| Production code | Function: ________, Unmapped handling: ________ |
| QC code | Independent implementation: ________ |
| Comparison | Result: ________ |
| Validation | CT check: ________ |

---

## Reflection

1. At which stage could an error in RACE mapping be caught?
2. If the spec said codelist C66731 (SEX) instead of C74457 (RACE), at which stage would the error be detected?
3. How does the spec-driven architecture ensure consistency from code to data to define.xml?

---

## What You Should Have at the End

- [ ] Complete RACE traceability from raw data to validated dataset
- [ ] Understanding of how each pipeline stage uses the spec
- [ ] Clarity on where errors would be caught
