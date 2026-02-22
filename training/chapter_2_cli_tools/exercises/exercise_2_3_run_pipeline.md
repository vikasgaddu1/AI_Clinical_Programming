# Exercise 2.3: Run the Pipeline

## Objective
Use the `/run-pipeline` skill to execute the SDTM spec building stage. Examine the generated mapping specification and understand how the orchestrator transforms raw data + IG knowledge into a structured spec.

## Time: 20 minutes

## Prerequisites
- Claude Code running in the project directory
- Environment check passing (at minimum: Python packages, config.yaml, study data, function registry)

---

## Steps

### Step 1: Run the Spec Building Stage

In Claude Code, type:
```
/run-pipeline spec_build
```

Watch the output. Claude will:
1. Check prerequisites (R, Python packages, config.yaml)
2. Run `python orchestrator/main.py --domain DM --stage spec_build`
3. Report the results

> Did the pipeline stage complete successfully? Yes / No
> If not, what error occurred? _________________________________________

### Step 2: Examine the Generated Spec

Ask Claude:
```
Read orchestrator/outputs/specs/dm_mapping_spec.json and show me a summary table of all variables
```

Claude should display a table like:

| Variable | Source | Type | Codelist | Decision Required? |
|----------|--------|------|----------|--------------------|

> How many variables are in the spec? ___________
>
> Which variables require human decisions? List them:
> _________________________________________________________________

### Step 3: Inspect a Decision Point

Ask Claude:
```
Show me the full decision options for the RACE variable from the spec, including pros and cons
```

> How many options are there for RACE mapping? ___________
>
> Briefly describe each option:
> Option A: _________________________________________________________
> Option B: _________________________________________________________
> Option C: _________________________________________________________

### Step 4: Look at the Excel Version

Ask Claude:
```
Check if orchestrator/outputs/specs/dm_mapping_spec.xlsx was generated
```

> Was the Excel file created? Yes / No
>
> Note: This Excel file is the human-readable version of the same spec. In real clinical programming, this is what you'd review with your lead programmer or sponsor.

### Step 5: Understand What Happened

Ask Claude:
```
Explain what the spec builder did step by step. What data sources did it read and how did it produce the mapping?
```

The answer should cover:
1. Raw data profiling (read `raw_dm.csv`, analyzed columns)
2. IG consultation (queried `dm_domain.md` for variable definitions)
3. Function registry check (matched variables to `iso_date`, `derive_age`, `assign_ct`)
4. CT mapping (identified codelists for SEX, RACE, ETHNIC)
5. Decision flagging (identified ambiguous mappings needing human input)

### Step 6: Run the Interactive Spec Review (Optional)

If time permits, try:
```
/review-spec
```

This presents the spec in a reviewable format and asks you to make decisions on flagged items. You'll do this more thoroughly in the Capstone.

---

## Key Artifacts to Note

After this exercise, these files should exist:

| File | What It Contains |
|------|-----------------|
| `orchestrator/outputs/specs/dm_mapping_spec.json` | Draft spec (machine-readable) |
| `orchestrator/outputs/specs/dm_mapping_spec.xlsx` | Draft spec (human-readable) |
| `orchestrator/outputs/pipeline_state.json` | Pipeline state (for crash recovery) |

---

## Reflection Questions

1. How does the spec builder know what SDTM variables to include? (Hint: it queries the IG content)
2. Why does the spec flag some variables for human decisions instead of choosing automatically?
3. How would this process change if you were working on an AE domain instead of DM?

---

## What You Should Have at the End

- [ ] Successfully ran the spec building stage
- [ ] Examined the generated spec JSON with variable summaries
- [ ] Reviewed at least one decision point (RACE) with its options
- [ ] Understanding of the data flow: raw data + IG + registry -> draft spec
