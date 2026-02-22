# Skill Design Template

Use this template to design a new Claude Code skill. Fill in each section, then save the file to `.claude/skills/your-skill-name.md`.

---

## Template

```markdown
# [Skill Title]

[One-sentence description of what this skill does]

## Usage
- `/skill-name` — [What happens when invoked with no arguments]
- `/skill-name [arg]` — [What happens with an argument] (if applicable)

## Instructions

1. **[First action]:**
   - [Specific file to read or command to run]
   - [What to extract or check]

2. **[Second action]:**
   - [Next step with specific details]
   - [Error handling: what to do if something is missing or fails]

3. **[Processing / comparison / analysis]:**
   - [Core logic the skill performs]
   - [Be specific: "Compare column X against column Y" not "Compare the data"]

4. **Display results:**
   - [Exact output format]
   - [What PASS and FAIL look like]

## Output Format
[Show an example of what the output should look like]

```
[Example output here]
```
```

---

## Checklist for Good Skills

- [ ] **Title is clear:** anyone can tell what the skill does from the title
- [ ] **Usage shows invocation:** includes the slash command and any arguments
- [ ] **File paths are explicit:** exact paths, not "find the file" or "look for the config"
- [ ] **Steps are numbered:** Claude follows them in order
- [ ] **Logic is unambiguous:** "for each variable with a non-null codelist_code" not "for variables that need checking"
- [ ] **Error handling:** what should Claude do if a file doesn't exist or data is unexpected?
- [ ] **Output format is specified:** Claude knows what the result should look like
- [ ] **Example output included:** shows both success and failure cases

---

## Common Patterns from Existing Skills

### Reading and validating a file
```markdown
1. **Read the configuration:**
   - Read `orchestrator/config.yaml`
   - Verify it's valid YAML (parse it)
   - Check all paths resolve to existing files
```

### Checking a condition and reporting
```markdown
4. **Run these checks:**
   - SEX values in {M, F, U} per codelist C66731
   - RACE values in valid C74457 terms

5. **Display results as a table:**
   | Check | Status | Details |
   Show PASS/FAIL for each check with specific details on failures.
```

### Cross-referencing two data sources
```markdown
3. **Cross-check against annotated CRF** (`study_data/annotated_crf_dm.csv`):
   - Read the CRF file
   - For each CRF field, check if corresponding raw data column exists
   - Flag any CRF fields missing from the raw data
```

---

## Ideas for Clinical Programming Skills

| Skill Name | Purpose |
|------------|---------|
| `/compare-codelists` | Compare spec codelist values against ct_lookup.csv |
| `/check-dates` | Verify all DTC variables in a dataset are valid ISO 8601 |
| `/trace-variable` | Trace a variable from raw data through spec to final dataset |
| `/diff-specs` | Compare two spec versions and highlight changes |
| `/check-suppdm` | Verify SUPPDM records have matching DM parent records |
| `/list-decisions` | Extract all human_decision_required items from a spec |
