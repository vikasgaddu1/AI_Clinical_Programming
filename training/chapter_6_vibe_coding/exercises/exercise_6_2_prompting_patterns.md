# Exercise 6.2: Clinical Prompting Patterns

## Objective
Practice the five clinical prompting patterns on real tasks. Compare prompt quality and output quality side-by-side.

## Time: 20 minutes

---

## Steps

### Step 1: Spec-First Pattern

Use the approved spec to drive code generation:

> "Read the approved spec at orchestrator/outputs/specs/dm_mapping_spec_approved.json (or the draft at dm_mapping_spec.json). Find the ETHNIC variable mapping. Generate the R code that implements this exact mapping using the assign_ct() function and codelist C66790."

> Did Claude read the spec before generating code? Yes / No
> Does the generated code match the spec's codelist and mapping logic? Yes / No
> Record the R code snippet:
> _________________________________________________________________

### Step 2: IG-Grounded Pattern

Use the SDTM IG as the authority:

> "Use the sdtm_variable_lookup MCP tool (or read sdtm_ig_db/sdtm_ig_content/dm_domain.md) to look up DTHFL (Death Flag). Is DTHFL a required variable for the DM domain? What controlled terminology does it use? Should we add it to our spec?"

> What did the IG say about DTHFL?
> Required/Expected/Permissible: _______________
> Codelist: _______________
> Your recommendation (add to spec or not): _______________

### Step 3: SAP-to-Code Pattern

Start from the analysis plan:

> "The SAP says Table 14.1.1 should show a summary of demographics by treatment group. The table should include: Age (mean, SD, median, min-max), Sex (n, %), Race (n, %), and Ethnicity (n, %). Read study_data/raw_dm.csv and generate an R script that produces this summary table."

> Did Claude ask clarifying questions or make assumptions? List them:
> _________________________________________________________________
> Does the output match what a stats programmer would expect? Yes / Partially / No

### Step 4: Error-Driven Pattern

Here's a broken R snippet. Ask Claude to fix it:

```r
# This code should map SEX to CDISC CT but it's broken
library(arrow)
source("r_functions/assign_ct.R")
dm <- read.csv("study_data/raw_dm.csv")
dm$SEX <- assign_ct(dm$SEX, codelist = "C66732", lookup_path = "macros/ct_lookup.csv")
write_parquet(dm, "output.parquet")
```

> Prompt Claude: "This R script maps SEX values but produces all NA results. The spec says SEX should use codelist C66731. Here's the code: [paste above]. What's wrong?"

> Did Claude identify the bug? Yes / No
> What was the fix? _________________________________

### Step 5: Iterative Refinement Pattern

Start simple and build up:

**First prompt:** "Generate an R script that counts subjects per treatment arm from raw_dm.csv."

> Record what Claude produces (basic version):
> _________________________________________________________________

**Second prompt:** "Good. Now add percentages based on total randomized subjects."

**Third prompt:** "Now add a row for 'Total' at the bottom, and format as a publication-ready table using the gt or flextable package."

> How many iterations did it take to get a polished result? _____
> Was each iteration incremental or did Claude start over? _________________________________

---

## Reflection

> Which prompting pattern felt most natural to you?
> _________________________________________________________________

> Which pattern do you think you'll use most in your daily SDTM work?
> _________________________________________________________________

> What's the single most important thing about prompt quality?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] Practiced all 5 prompting patterns with real clinical tasks
- [ ] Identified the codelist bug using the error-driven pattern
- [ ] Built a table iteratively using the refinement pattern
- [ ] A personal opinion on which pattern suits your workflow
