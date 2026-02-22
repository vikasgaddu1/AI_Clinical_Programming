---
description: Interactively review an SDTM mapping specification — display formatted table, present human decision points with options/pros/cons, collect decisions, save approved spec.
user-invocable: true
argument-hint: "[approved]"
---

# Review Mapping Specification

Interactively review an SDTM mapping specification and collect human decisions.

## Usage
- `/review-spec` — Review the current draft spec
- `/review-spec approved` — Review the approved spec

## Instructions

1. **Read config to determine the active domain**, then read the spec file:
   - Draft: `{output_dir}/specs/{domain}_mapping_spec.json`
   - Approved: `{output_dir}/specs/{domain}_mapping_spec_approved.json`

2. **Display a formatted table** of all variables showing:
   | Variable | Source | Type | Length | Mapping Logic | CT Codelist | Decision? |
   Show all variables in the spec.

3. **Check review comments:**
   - If the spec has `review_comments`, display them prominently
   - If `review_pass` is false, highlight the issues that need fixing

4. **For each variable with `human_decision_required: true`:**
   - Display the variable name and current mapping logic
   - Show ALL decision options with:
     - Option ID and description
     - IG reference
     - Pros and cons
   - Ask the user to select an option (A, B, C, or provide custom text)
   - Record their choice

4b. **For CT-controlled variables, show inline data context:**
   - Before presenting a CT-controlled decision, use `profile_raw_data` (with `annotate=true`) to show the raw data profile for that column
   - Use `ct_lookup` with `check_values` parameter passing the actual distinct values from the raw data to show mapped/unmapped coverage
   - This gives reviewers data-driven context for their decisions

5. **Cross-reference with IG content:**
   - Read `sdtm_ig_db/sdtm_ig_content/{domain}_domain.md` for domain variable definitions
   - Check that all IG-required variables are present in the spec
   - Flag any discrepancies between spec and IG

6. **Ask for overall approval:**
   - Present options: Approved / Approved with Changes / Rejected
   - If approved, save the updated spec as the approved version
   - If rejected, note the reasons for the rejection

7. **Save the updated spec:**
   - Write to `{output_dir}/specs/{domain}_mapping_spec_approved.json`
   - Include all human decisions in the `human_decisions` field
