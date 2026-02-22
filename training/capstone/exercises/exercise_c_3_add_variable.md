# Exercise C.3: Add DTHFL to the Spec

## Objective
Add a new variable (DTHFL -- Death Flag) to the approved spec and observe how the change flows through to production code generation. This demonstrates that the spec drives everything downstream.

## Time: 30 minutes

---

## Steps

### Step 1: Check the IG

Ask Claude Code:
```
Use the sdtm_variable_lookup tool to look up DTHFL in the DM domain
```

> What does the IG say about DTHFL?
> _________________________________________________________________
> What are the valid values? ___________
> Is it Required, Expected, or Permissible? ___________

### Step 2: Check the Current Spec

```
Read orchestrator/outputs/specs/dm_mapping_spec_approved.json and check if DTHFL is already included
```

> Is DTHFL in the current spec? Yes / No

### Step 3: Add DTHFL to the Spec

Ask Claude Code to add a new variable entry:

```
Add DTHFL (Death Flag) to the approved spec at orchestrator/outputs/specs/dm_mapping_spec_approved.json with these properties:
- target_variable: DTHFL
- target_domain: DM
- source_variable: derived
- source_dataset: raw_dm
- data_type: Char
- length: 1
- codelist_code: C66742
- codelist_name: No Yes Response
- mapping_logic: "If DTHDTC is non-null, DTHFL = 'Y'. Otherwise leave blank."
- controlled_terms: ["Y"]
- human_decision_required: false
```

> Was DTHFL added successfully? ___________

### Step 4: Re-Run Production

```
/run-pipeline production
```

> Did the production stage regenerate the R script? ___________
>
> Read the new dm_production.R. Does it include DTHFL logic?
> _________________________________________________________________
>
> What R code was generated for DTHFL?
> _________________________________________________________________

### Step 5: Validate

```
/validate-dataset
```

> Does DTHFL appear in the validation checks? ___________
> Does it pass validation? ___________

### Step 6: Reflect

> How much code did you write to add DTHFL? ___________
> What did you actually change? (Just the spec JSON)
>
> What happened automatically?
> - [ ] R script regenerated with DTHFL logic
> - [ ] Dataset includes DTHFL column
> - [ ] Validation checks DTHFL values
>
> This is the spec-driven principle: change the spec, everything else follows.

---

## What You Should Have at the End

- [ ] DTHFL added to the approved spec
- [ ] Production R script regenerated with DTHFL logic
- [ ] Understanding that spec changes flow through automatically
