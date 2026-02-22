# Exercise 2.4: Write a Custom Skill

## Objective
Design and write a new Claude Code skill (`/compare-codelists`) that compares codelist values between the mapping specification and the CT lookup table. This teaches you how to extend Claude Code with domain-specific workflows.

## Time: 20 minutes

## Prerequisites
- Familiarity with the existing skills (from Exercise 2.1)
- The skill design template handout (`skill_design_template.md`)

---

## Background

A skill is a markdown file in `.claude/skills/` that defines a reusable workflow. When you type `/skill-name` in Claude Code, it reads the markdown and follows the instructions step by step.

The existing skills follow a consistent pattern:
1. **Title** -- what the skill does
2. **Usage** -- how to invoke it (with optional arguments)
3. **Instructions** -- numbered steps Claude follows
4. **Output Format** -- what the result looks like

Review `.claude/skills/check-environment.md` as a reference (you saw this in Exercise 2.1).

---

## Steps

### Step 1: Understand the Problem

The mapping spec (`dm_mapping_spec.json`) says that SEX uses codelist C66731 with values M, F, U. The CT lookup table (`macros/ct_lookup.csv`) has the actual mapping from raw values to CT values for each codelist.

**The skill should verify:** Do the values in the spec match what's in the CT lookup? Are there any mismatches?

Example of a problem this skill would catch:
- Spec says SEX codelist is C66731 with values [M, F, U]
- CT lookup has C66731 mapping to [M, F] (no U)
- The skill flags: "SEX: spec includes 'U' but C66731 in ct_lookup does not have 'U'"

### Step 2: Plan the Skill

Before writing, plan the steps:

1. What files does the skill need to read?
   - `orchestrator/outputs/specs/dm_mapping_spec.json` (or the approved version)
   - `macros/ct_lookup.csv`

2. What logic does it perform?
   - For each variable in the spec that has a `codelist_code`:
     - Look up that codelist in ct_lookup.csv
     - Compare the spec's `controlled_terms` against the CT lookup's `CT_VALUE` column
     - Flag mismatches (values in spec but not in CT, or vice versa)

3. What does the output look like?
   - A table showing: Variable, Codelist, Spec Values, CT Values, Match/Mismatch

### Step 3: Write the Skill

Using the template, create the skill file. Write the content below (or directly create the file):

**File path:** `.claude/skills/compare-codelists.md`

Fill in each section:

```markdown
# [Title]

[One-line description]

## Usage
- `/compare-codelists` — [what it does with default files]
- `/compare-codelists approved` — [variant for approved spec]

## Instructions

1. **Read the mapping spec:**
   - [which file, which fields to extract]

2. **Read the CT lookup table:**
   - [which file, which columns]

3. **For each CT-controlled variable:**
   - [comparison logic]

4. **Display results:**
   - [output format]

## Output Format
[example table]
```

### Step 4: Review Against the Template

Compare your skill with the template handout. Check:

- [ ] Does it have a clear title and description?
- [ ] Does the Usage section show how to invoke it?
- [ ] Are the Instructions specific enough that Claude can follow them without ambiguity?
- [ ] Are file paths explicit (not "find the spec file" but the exact path)?
- [ ] Does the Output Format show what success and failure look like?

### Step 5: Test the Skill (Optional)

If time permits, save your skill file and test it in Claude Code:
```
/compare-codelists
```

Watch Claude follow your instructions. Did it:
- Read the correct files?
- Compare the right values?
- Produce the expected output format?

> Test result: ___________________________________________________________
>
> Did you need to adjust the instructions? What changed?
> _________________________________________________________________

---

## Reference Solution

Here's a complete version for comparison after you've written yours:

```markdown
# Compare Codelists

Compare controlled terminology values between the mapping specification
and the CT lookup table to verify consistency.

## Usage
- `/compare-codelists` — Compare the draft spec against ct_lookup.csv
- `/compare-codelists approved` — Compare the approved spec

## Instructions

1. **Read the mapping spec:**
   - If "approved" argument: read `orchestrator/outputs/specs/dm_mapping_spec_approved.json`
   - Otherwise: read `orchestrator/outputs/specs/dm_mapping_spec.json`
   - Extract all variables that have a non-null `codelist_code` field
   - For each, note: variable name, codelist_code, and controlled_terms array

2. **Read the CT lookup table:**
   - Read `macros/ct_lookup.csv`
   - Group by CODELIST column
   - For each codelist, collect the set of unique CT_VALUE values

3. **Compare for each CT-controlled variable:**
   - Look up the variable's codelist_code in the CT lookup
   - If codelist not found in CT lookup: flag as ERROR
   - Compare the spec's controlled_terms against the CT lookup's CT_VALUE set:
     - Values in spec but NOT in CT lookup: flag as "Spec-only"
     - Values in CT lookup but NOT in spec: flag as "CT-only" (informational)
     - Values in both: flag as "Match"

4. **Display results as a table:**
   | Variable | Codelist | Status | Details |
   Show MATCH if all spec values are in CT lookup, MISMATCH if any discrepancy.

5. **Generate summary:**
   - Total CT-controlled variables checked
   - Matches / Mismatches
   - Overall PASS or FAIL

## Output Format
```
Codelist Comparison Report
==========================
| Variable | Codelist | Status   | Details                           |
|----------|----------|----------|-----------------------------------|
| SEX      | C66731   | MATCH    | All values found in CT lookup     |
| RACE     | C74457   | MISMATCH | Spec-only: UNKNOWN                |
| ETHNIC   | C66790   | MATCH    | All values found in CT lookup     |

Summary: 3 variables checked, 2 MATCH, 1 MISMATCH
Overall: FAIL (1 mismatch found)
```
```

---

## Reflection Questions

1. What makes a skill effective? (Clear instructions, explicit file paths, defined output format)
2. Could you write skills for other clinical programming tasks? Name two.
3. How is a skill different from a Python script that does the same thing?

---

## What You Should Have at the End

- [ ] A `/compare-codelists` skill file (written or planned)
- [ ] Understanding of skill anatomy: title, usage, instructions, output format
- [ ] (Optional) A successful test run of the skill
