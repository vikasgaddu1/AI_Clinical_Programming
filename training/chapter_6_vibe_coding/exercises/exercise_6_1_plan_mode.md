# Exercise 6.1: Plan Mode Practice

## Objective
Use plan mode to design a small clinical utility before writing any code. Experience how planning prevents wasted iterations and catches edge cases early.

## Time: 20 minutes

---

## Steps

### Step 1: Enter Plan Mode

In Claude Code, enter plan mode. You can do this by:
- Typing `/plan` or using the plan mode toggle
- Or prompting: "Enter plan mode and help me design..."

### Step 2: Describe Your Intent

Give Claude this prompt (or adapt it to your own idea):

> "I want a Python script that reads study_data/raw_dm.csv, identifies all subjects with partial or inconsistent birth dates, and generates a report showing:
> 1. How many subjects have complete dates (YYYY-MM-DD)
> 2. How many have partial dates (YYYY-MM or YYYY only)
> 3. How many have missing dates
> 4. For each partial date, what imputation approach the SDTM IG recommends
> 5. A CSV output with columns: SUBJID, BRTHDT_raw, date_status, recommended_imputation"

### Step 3: Review the Plan

Claude will explore the codebase and propose a plan. As you review it, answer:

> Does the plan read raw_dm.csv to understand the actual date formats present?
> Yes / No

> Does the plan reference the SDTM IG content (dm_domain.md or general_assumptions.md) for imputation rules?
> Yes / No

> Does the plan identify edge cases you didn't think of? List them:
> _________________________________________________________________
> _________________________________________________________________

> Does the plan propose using any existing R functions (iso_date)?
> Yes / No — Which ones? _________________________________

### Step 4: Approve and Execute

Approve the plan. Let Claude implement the script.

> Did the implementation match the plan? Yes / No
> If not, what diverged? _________________________________

### Step 5: Reflect

> How many iterations would you have needed WITHOUT plan mode?
> Estimate: _____

> What did the plan catch that you wouldn't have thought of on your first prompt?
> _________________________________________________________________

> Rate your confidence in the output (1-5): _____

---

## What You Should Have at the End

- [ ] A plan that Claude generated (you can screenshot or copy it)
- [ ] A working Python script that profiles birth date quality
- [ ] Understanding of how plan mode explores the codebase before proposing solutions
- [ ] At least one edge case the plan caught that you didn't anticipate
