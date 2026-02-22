# Exercise 6.3: Debug a Broken R Script with AI

## Objective
Use AI-assisted debugging to find and fix 3 planted bugs in a production R script. Practice providing error messages with context and intent.

## Time: 20 minutes

---

## Background

The following R script is a modified version of `dm_production.R` with **3 deliberate bugs**. Your job is to use Claude Code to find and fix all 3 without reading through the code line by line yourself.

## The Broken Script

Create a file called `dm_buggy.R` with this content (or ask Claude to create it):

```r
# Buggy DM Production Script — 3 bugs hidden
library(arrow)

source("r_functions/iso_date.R")
source("r_functions/derive_age.R")
source("r_functions/assign_ct.R")

dm <- read.csv("study_data/raw_dm.csv", stringsAsFactors = FALSE)

# Bug 1 is somewhere in the date conversion
dm$BRTHDTC <- iso_date(dm$BRTHDT)
dm$RFSTDTC <- iso_date(dm$RFSTDTC)

# Bug 2 is somewhere in the derivations
dm$AGE <- derive_age(dm$RFSTDTC, dm$BRTHDTC)
dm$AGEU <- "YEARS"

# Bug 3 is somewhere in the CT mapping
dm$SEX <- assign_ct(dm$SEX, codelist = "C66731", lookup_path = "macros/ct_lookup.csv")
dm$RACE <- assign_ct(dm$RACE, codelist = "C74457", lookup_path = "macros/ct_lookup.csv")
dm$ETHNIC <- assign_ct(dm$ETHNIC, codelist = "C66790", lookup_path = "macros/ct_lookup.csv")

# USUBJID derivation
dm$DOMAIN <- "DM"
dm$STUDYID <- dm$STUDYID

write_parquet(dm, "orchestrator/outputs/datasets/dm_buggy.parquet")
```

**The 3 bugs:**
1. `derive_age()` arguments are in the wrong order (should be `birth_date, reference_date`, not `reference_date, birth_date`)
2. USUBJID is never derived -- the script sets DOMAIN and STUDYID but never creates USUBJID (should be `paste(STUDYID, SUBJID, sep = "-")`)
3. One of the CT mappings is correct but the ETHNIC variable name in raw data might be different (check `raw_dm.csv` column names)

---

## Steps

### Step 1: Run the Script

```bash
Rscript dm_buggy.R
```

> Did it run without errors? Yes / No
> If errors occurred, record the first error:
> _________________________________________________________________

### Step 2: Debug with AI — Bug 1

Show Claude the error (or the unexpected output) with context:

> "I'm running dm_buggy.R to create a DM dataset. The AGE values look wrong -- some subjects show negative ages. The script derives AGE using derive_age(). Here's the relevant code: [paste the derive_age line]. The function signature in function_registry.json says derive_age(birth_date, reference_date). What's wrong?"

> Did Claude find Bug 1? Yes / No
> What was the fix? _________________________________
> Did you provide enough context on the first try? Yes / No

### Step 3: Debug with AI — Bug 2

> "I fixed the age issue. Now I'm checking the output and USUBJID is missing from the dataset. The spec says USUBJID should be STUDYID-SUBJID. Here's the full script: [paste]. Where should the USUBJID derivation go?"

> Did Claude find Bug 2? Yes / No
> What was the fix? _________________________________

### Step 4: Debug with AI — Bug 3

> "Ages and USUBJID are fixed. Now ETHNIC has all NA values after assign_ct(). The spec says codelist C66790 for ETHNIC. I checked ct_lookup.csv and the mappings look correct. What else could cause all NAs?"

Hint: The issue might be that the raw data column is named differently than expected.

> Did Claude find Bug 3? Yes / No
> What was the root cause? _________________________________
> What was the fix? _________________________________

### Step 5: Verify

Re-run the fixed script and check:

```r
dm <- arrow::read_parquet("orchestrator/outputs/datasets/dm_buggy.parquet")
summary(dm$AGE)        # Should be reasonable ages (18-90)
table(dm$SEX)          # Should be M, F
head(dm$USUBJID)       # Should be STUDYID-SUBJID format
table(dm$ETHNIC, useNA = "always")  # Should have mapped values, not all NA
```

---

## Reflection

> Rate the quality of your debugging prompts (1-5):
> Bug 1: ___  Bug 2: ___  Bug 3: ___

> Which bug was hardest to find? Why?
> _________________________________________________________________

> What did you learn about providing context when debugging?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] All 3 bugs identified and fixed
- [ ] A working dm_buggy.R that produces valid output
- [ ] Understanding of the debugging formula: error + context + intent
- [ ] Self-assessment of your prompt quality during debugging
