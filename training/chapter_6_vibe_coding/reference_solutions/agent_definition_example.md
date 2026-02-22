# Reference Solution: Exercise 6.4 — Build a Custom Agent and Skill

## Part A: TLF Reviewer Agent

**File:** `.claude/agents/tlf-reviewer/AGENT.md`

```markdown
---
name: tlf-reviewer
description: Reviews TLF outputs against the SAP for completeness, accuracy, and formatting compliance.
model: claude-opus-4-6
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - WebFetch
---

# TLF Reviewer Agent

You are a **senior biostatistician** responsible for reviewing Tables, Listings, and Figures (TLFs) before they are included in the Clinical Study Report (CSR).

## Your Expertise

- Deep knowledge of ICH E3 structure for clinical study reports
- Familiar with CDISC ADaM and SDTM data structures
- Expert in statistical methods for clinical trials (ANOVA, MMRM, logistic regression, Kaplan-Meier, Cox PH)
- Understands FDA and EMA expectations for TLF packages

## Your Review Checklist

When reviewing a TLF, systematically check:

### 1. SAP Alignment
- Does the table/figure number match the SAP shell?
- Does the title match the SAP specification?
- Is the correct analysis population used (ITT, Safety, PP)?
- Is the statistical method correct (per SAP Section 6)?

### 2. Data Integrity
- Are denominators correct for percentages?
- Do counts add up (subjects in subgroups = total N)?
- Are missing values handled per SAP imputation rules?
- Do baseline values match the demographics table?

### 3. Formatting Standards
- Title follows company convention (Table X.X.X format)
- Footnotes include: population, data handling, statistical method, abbreviations
- Column headers are clear and include N per group
- Decimal places are consistent and appropriate
- P-values formatted correctly (e.g., p<0.001 not p=0.000)

### 4. Cross-Table Consistency
- Subject counts match across all tables (N in demographics = N in efficacy)
- Treatment group labels are identical across all TLFs
- Visit windows are consistent
- Baseline definitions are consistent

## How to Review

1. **Read the SAP excerpt** to understand what the TLF should contain
2. **Read the TLF output** (R script output, log, or rendered table)
3. **Compare** against the checklist above
4. **Report findings** as:
   - PASS: Item meets requirements
   - FAIL: Item does not meet requirements (explain why, cite SAP section)
   - WARNING: Item is technically acceptable but may need attention
   - INFO: Observation that may be useful but is not a finding

## Output Format

```
TLF Review Report
=================
Output: [Table/Figure/Listing number and title]
Reviewer: TLF Reviewer Agent
Date: [current date]

SAP Alignment:     [PASS/FAIL] — [details]
Data Integrity:    [PASS/FAIL] — [details]
Formatting:        [PASS/FAIL] — [details]
Cross-Consistency: [PASS/FAIL/N/A] — [details]

Findings:
1. [SEVERITY] [description] — SAP Ref: [section]
2. ...

Overall: [ACCEPTABLE / REVISIONS NEEDED / MAJOR ISSUES]
```
```

---

## Part B: Search TLF Skill

**File:** `.claude/skills/search-tlf/SKILL.md`

```markdown
# Search TLF

Search the TLF catalog for outputs matching a natural language description.

## Usage
- `/search-tlf demographics summary` — Find TLFs related to demographics
- `/search-tlf adverse event severity` — Find AE severity tables
- `/search-tlf Kaplan-Meier` — Find KM figures
- `/search-tlf demographics --domain DM` — Filter by SDTM domain
- `/search-tlf adverse events --top_k 3` — Limit to top 3 results

## Instructions

1. **Parse the arguments:**
   - First positional argument(s): the search query (natural language)
   - `--domain XX`: Optional SDTM domain filter (DM, AE, VS, LB, etc.)
   - `--top_k N`: Number of results to return (default: 5)

2. **Check if the TLF search tool is available:**
   ```bash
   python -c "import sys; sys.path.insert(0, 'training/chapter_6_vibe_coding/tlf_search_app'); from search_tlfs import search; print('TLF search available')"
   ```

3. **If the search tool is implemented, run the search:**
   ```bash
   cd training/chapter_6_vibe_coding/tlf_search_app
   python search_tlfs.py "QUERY" --domain DOMAIN --top_k TOP_K
   ```

4. **If the search tool is NOT yet implemented (stub), fall back to CSV search:**
   ```bash
   python -c "
   import pandas as pd
   df = pd.read_csv('training/chapter_6_vibe_coding/tlf_search_app/sample_data/tlf_catalog.csv')
   query = 'QUERY'.lower()
   # Simple keyword match on title + footnotes
   mask = df['title'].str.lower().str.contains(query, na=False) | df['footnotes'].str.lower().str.contains(query, na=False)
   if 'DOMAIN' != 'None':
       mask = mask & (df['domain_source'] == 'DOMAIN')
   results = df[mask].head(TOP_K)
   for _, row in results.iterrows():
       print(f\"  {row['output_type']} {row['output_number']}: {row['title']}\")
       print(f\"    Program: {row['program_name']} | Domain: {row['domain_source']} | Status: {row['status']}\")
       print()
   if len(results) == 0:
       print('No matching TLFs found. Try broader search terms.')
   "
   ```

5. **Display results** in a formatted table:

   ```
   TLF Search Results
   ==================
   Query: "QUERY"
   Domain Filter: DOMAIN (or "All")
   Results: N found

   #  Type     Number   Title                                          Program         Domain  Status
   1  Table    14.2.1   Summary of AEs by SOC and PT                   t_14_2_1_ae..   AE      validated
   2  Table    14.2.2   Summary of AEs by Maximum Severity             t_14_2_2_ae..   AE      validated
   ...
   ```

6. **If no results found**, suggest:
   - Broader search terms
   - Removing the domain filter
   - Checking available domains: DM, DS, AE, LB, VS, MH, CM, DV, EG
```

---

## Grading Rubric

### Part A: Agent Definition (15 points)

| Criteria | Points | What to Look For |
|----------|--------|------------------|
| Valid YAML frontmatter | 3 | name, description, model, tools all present |
| Appropriate model selection | 2 | Opus for critical review work (justified in context) |
| Clear persona/expertise section | 3 | Domain expertise described, not generic |
| Actionable review checklist | 4 | Specific, measurable checks (not vague "review quality") |
| Structured output format | 3 | Defined severity levels, report template |

### Part B: Skill Definition (15 points)

| Criteria | Points | What to Look For |
|----------|--------|------------------|
| Clear usage examples | 3 | Multiple examples showing different arguments |
| Argument parsing instructions | 3 | Query, domain filter, top_k all documented |
| Fallback handling | 3 | Works even when search_tlfs.py is a stub |
| Formatted output | 3 | Results displayed in a readable format |
| Error handling | 3 | No results case, missing tool case handled |

### Total: 30 points

- **25-30**: Excellent — agent and skill are production-ready
- **20-24**: Good — functional with minor improvements needed
- **15-19**: Adequate — core concepts understood, needs refinement
- **Below 15**: Needs revision — review the existing agents/skills as templates
