# Chapter 2B Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Exercise 2B.1: Explore the Existing Function Registry

- [ ] Read and understood `function_registry.json` structure
- [ ] Identified all registered functions and their purposes
- [ ] Traced the dependency chain (iso_date → derive_age → assign_ct)
- [ ] Used FunctionLoader in Python to query the registry
- [ ] Ran `format_for_prompt()` and understood the AI prompt format
- [ ] Compared R and SAS registry entries (identified similarities and differences)

## Exercise 2B.2: Register a New R Function

- [ ] Wrote `derive_studyday.R` function with correct logic (no Day 0 rule)
- [ ] Tested function with sample data (expected: 6, -21, 1, NA)
- [ ] Created complete registry entry for `derive_studyday`
- [ ] Added entry to `function_registry.json` with valid JSON
- [ ] Verified FunctionLoader discovers the new function
- [ ] Verified dependency order is correct (iso_date before derive_studyday)

## Exercise 2B.3: Build a SAS-to-R Migration Plan

- [ ] Completed SAS vs R comparison table
- [ ] Identified language-agnostic vs language-specific registry fields
- [ ] Prioritized migration order for 5 remaining macros
- [ ] Designed registry entry for `build_seq` function
- [ ] Understood that CT lookup data is shared across languages

## Exercise 2B.4: Test AI Function Discovery

- [ ] Claude Code discovered registered functions from the registry
- [ ] Claude generated code using `iso_date()` (not custom date parsing)
- [ ] Claude called functions in correct dependency order
- [ ] Claude used correct parameters matching registry definitions
- [ ] Tested edge case awareness (date format ambiguity, `infmt` parameter)

---

## Key Concepts

### Why AI Needs a Registry (Not Just Source Code)
_________________________________________________________________
_________________________________________________________________

### The Three Things Every Registry Entry Must Have
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

### How the FunctionLoader Connects Registry to Agents
_________________________________________________________________
_________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Reading and interpreting a function registry entry | [ ] | [ ] | [ ] |
| Writing a new registry entry for an existing function | [ ] | [ ] | [ ] |
| Understanding dependency ordering | [ ] | [ ] | [ ] |
| Using FunctionLoader in Python | [ ] | [ ] | [ ] |
| Comparing SAS and R registry patterns | [ ] | [ ] | [ ] |
| Verifying AI discovers and uses registered functions | [ ] | [ ] | [ ] |
| Designing a migration plan for existing macros | [ ] | [ ] | [ ] |
