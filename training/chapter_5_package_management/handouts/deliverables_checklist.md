# Chapter 5 Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Exercise 5.1: Explore the Approved Package Registry

- [ ] Read and understood approved_packages.json structure
- [ ] Identified all three statuses (approved, not_approved, under_review)
- [ ] Used PackageManager to query packages by language
- [ ] Checked approval status for approved and non-approved packages
- [ ] Read versioned documentation for an approved package
- [ ] Reviewed restrictions for SDTM-relevant packages
- [ ] Ran format_for_prompt() and understood the AI prompt format

## Exercise 5.2: Add a Package with Versioned Documentation

- [ ] Designed a complete registry entry for stringr
- [ ] Added entry to approved_packages.json (valid JSON)
- [ ] Created versioned documentation file (1.5.1.md)
- [ ] Verified PackageManager discovers the new package
- [ ] Tested code compliance for code using stringr
- [ ] Tested non-compliant code detection (tidyverse, wrong version)

## Exercise 5.3: Build an MCP Tool for Package Lookup

- [ ] Implemented _package_lookup helper function
- [ ] Added Tool definition to MCP server
- [ ] Added handler routing to call_tool()
- [ ] Tested check, docs, restrict, and list actions in CLI mode
- [ ] Designed /check-packages skill (conceptual)

## Exercise 5.4: Create Enforcement Rules

- [ ] Wrote CLAUDE.md package policy rules (5-7 rules)
- [ ] Tested compliance scanning on compliant and non-compliant code
- [ ] Designed PostToolUse hook for package enforcement
- [ ] Mapped four enforcement layers to violation types
- [ ] Compared function registry and package registry patterns

---

## Key Concepts

### Why Enterprise Package Management Matters for AI
_________________________________________________________________
_________________________________________________________________

### The Three Package Statuses and What They Mean for AI
1. approved: _________________________________________________________________
2. not_approved: _________________________________________________________________
3. under_review: _________________________________________________________________

### The Four Enforcement Layers
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________
4. _________________________________________________________________

### Context7 vs Enterprise Package Manager
_________________________________________________________________
_________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Reading and interpreting the approved package registry | [ ] | [ ] | [ ] |
| Adding a new package with documentation | [ ] | [ ] | [ ] |
| Using PackageManager to check compliance | [ ] | [ ] | [ ] |
| Building an MCP tool for package lookup | [ ] | [ ] | [ ] |
| Writing CLAUDE.md enforcement rules | [ ] | [ ] | [ ] |
| Designing hooks for package compliance | [ ] | [ ] | [ ] |
| Distinguishing Context7 from enterprise docs | [ ] | [ ] | [ ] |
