# Exercise C.2: Introduce a Deliberate Error

## Objective
Deliberately introduce a spec error and observe whether the pipeline catches it. This demonstrates the safety net provided by spec-driven architecture and validation gates.

## Time: 30 minutes

---

## Steps

### Step 1: Save a Backup

Before modifying anything, save a backup of the approved spec:
```
Copy orchestrator/outputs/specs/dm_mapping_spec_approved.json to dm_mapping_spec_approved.json.bak
```

### Step 2: Introduce the Error

Ask Claude Code:
```
Read orchestrator/outputs/specs/dm_mapping_spec_approved.json, find the SEX variable, and change its codelist_code from "C66731" to "C74457" (which is the RACE codelist). Save the modified file.
```

**What this does:** The spec now claims SEX uses the RACE codelist (C74457) instead of the SEX codelist (C66731). The controlled terms would be wrong -- RACE values instead of M/F.

> Confirm: SEX codelist_code is now C74457? ___________

### Step 3: Re-Run Production

```
/run-pipeline production
```

> Did the production stage complete? Yes / No
>
> What happened in the R script? Did it try to map SEX values using the RACE codelist?
> _________________________________________________________________

### Step 4: Run Validation

```
/validate-dataset
```

> Did the validation catch the error? Yes / No
>
> What specific check failed?
> _________________________________________________________________
>
> What error message was generated?
> _________________________________________________________________

### Step 5: Analyze the Error Chain

Think about where this error could have been caught:

| Stage | Would it catch this error? | How? |
|-------|---------------------------|------|
| Spec Review | _____ | CT compliance check: does SEX use a valid sex codelist? |
| Human Review | _____ | Reviewer sees C74457 (RACE) listed for SEX |
| Production | _____ | assign_ct() maps SEX values against RACE terms |
| QC | _____ | Independent QC might use the correct codelist |
| Comparison | _____ | Production vs QC would differ on SEX values |
| Validation | _____ | P21 check: SEX values not in C74457 |

### Step 6: Restore the Correct Spec

```
Restore orchestrator/outputs/specs/dm_mapping_spec_approved.json from the backup
```

> Confirm: SEX codelist_code is back to C66731? ___________

---

## Discussion Points

1. **Defense in depth:** The spec-driven architecture has multiple checkpoints. Even if the spec reviewer missed it, the human reviewer, comparison, and validation would catch it.
2. **Spec as single source of truth:** Because everything flows from the spec, a single spec error propagates -- but it also means fixing the spec fixes everything downstream.
3. **Without a spec:** If programmers coded directly without a spec, this kind of error would be much harder to trace. The code might "work" (produce output) but produce wrong CT values.

---

## What You Should Have at the End

- [ ] Introduced a deliberate spec error (wrong codelist for SEX)
- [ ] Observed pipeline behavior with the error
- [ ] Identified which stages caught (or would catch) the error
- [ ] Restored the correct spec
- [ ] Understanding of defense-in-depth validation
