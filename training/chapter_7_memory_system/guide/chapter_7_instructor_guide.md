# Chapter 7: Agent Memory System — Instructor Guide

## Session Overview

| Field | Value |
|-------|-------|
| Duration | 3 hours (including breaks) |
| Format | Interactive lab with guided exercises |
| Audience | Builder / Architect level |
| Prerequisites | Chapters 2 (CLI tools), 2B (function library), familiarity with SDTM pipeline |
| Skills Used | Python, YAML, MemoryManager API, pipeline architecture |

## Key Teaching Message

AI agents are powerful but forgetful. Every pipeline run starts from zero — no memory of past decisions, no awareness of past failures, no institutional knowledge. The memory system transforms stateless agents into a learning organization where decisions accumulate, mistakes become lessons, and company standards are enforced automatically.

The key insight: **memory is not AI magic — it's structured YAML files read by agents before they generate code.** This makes it auditable, editable, and transparent — exactly what regulators and quality teams need.

## Connection to Previous Chapters

In Chapter 2, you used Claude Code as an operator. In Chapter 2B, you made functions discoverable via a registry. In Chapters 3-4, you built RAG and API components. In Chapter 6, you designed agents and skills. Now you're adding the final architectural layer: **persistent memory** that makes the whole system learn and improve over time.

---

## Module 7.1: Why Agents Forget (30 min)

### Talking Points

1. Every pipeline run creates a fresh `PipelineState` — no carryover from previous runs
2. The `human_decisions` field in state existed but was never populated (dead code)
3. Decisions were embedded in spec JSON files — not centralized, not queryable
4. Show the eight memory gaps: no pitfall tracking, no cross-run learning, no decision audit trail, etc.
5. Draw the analogy: "Imagine a new programmer starting every Monday with amnesia"

### Live Demo: Trace a Gap (10 min)

1. Run `python orchestrator/main.py --study XYZ_2026_001 --domain DM --stage spec_build`
2. Show the draft spec's `human_decision_required` fields
3. Show `pipeline_state.json` — `human_decisions` is empty
4. Ask: "Where did the decisions go?" (Answer: nowhere yet, they're in the spec file after human review)

### Transition

"Now let's see how the memory system fills these gaps — starting with coding standards."

---

## Module 7.2: Coding Standards (35 min)

### Talking Points

1. Every pharma company has house rules — the memory system makes them machine-readable
2. Walk through `standards/coding_standards.yaml` section by section
3. Key principle: **the YAML is the single source of truth for style**, not a Word doc SOP
4. CDISC compliance rules (variable name length, label length) are in the same file — agents see everything in one place
5. The program header template: emphasize **modification history** for regulatory audit trails

### Live Demo: Standards Flow (15 min)

1. Open `standards/coding_standards.yaml` — walk through each section
2. Open `standards/memory/program_header_template.txt` — show the placeholders
3. Run the Python code from Exercise 7.2 Step 3 to show context building
4. Generate a script and scroll to the top — show the rendered header
5. Point out: "Notice lowercase comments, UPPERCASE SDTM vars — this is enforced, not optional"

### Common Question

**Q: "What if my company uses SAS, not R?"**
A: The memory system is language-agnostic. Replace the R-specific rules with SAS rules (PROC SQL conventions, macro naming, etc.). The architecture — YAML standards + template headers + agent context injection — works for any language.

### Transition

"Standards tell agents HOW to write code. Memory tells them WHAT happened before. Let's add decisions and pitfalls."

---

## Module 7.3: Decisions and Pitfalls (40 min)

### Talking Points

1. Two core record types: `DecisionRecord` (what was chosen) and `PitfallRecord` (what went wrong)
2. Decisions are recorded during human review — `write_decisions_to_memory()` in `human_review.py`
3. Pitfalls are recorded at failure points — R script errors, comparison mismatches, validation failures
4. Memory is layered: study-specific + company-level, just like conventions
5. Key API methods: `record_decision()`, `record_pitfall()`, `get_decision_history()`, `get_relevant_pitfalls()`

### Live Demo: Record and Read (15 min)

Walk through Exercise 7.3 Steps 1-3 interactively:
1. Record 3 decisions
2. Show the YAML file on disk — human-readable, editable
3. Create a fresh MemoryManager and read back — demonstrate persistence

### Discussion Point

Ask the class: "In your current workflow, when a program fails, what happens to the error message after you fix it?" Expected answer: "It disappears — we fix it and move on." The memory system is the fix: errors become permanent lessons.

### Transition

"Individual studies learn from their own mistakes. But what about cross-domain and cross-study learning?"

---

## Module 7.4: Cross-Domain Memory (30 min)

### Talking Points

1. SDTM domains are interconnected — DM's RFSTDTC affects every --DY calculation
2. `DomainContext` captures key decisions and derived variables per domain
3. When AE runs, it receives DM's context — knows the reference date approach
4. This prevents the classic bug: "DM used consent date, but AE used first dose date"

### Live Demo: DM Context for AE (10 min)

1. Save a DM domain context (Exercise 7.4 Step 1)
2. Show the YAML file — simple, transparent
3. Build an AE agent context — show DM info in `cross_domain`
4. Ask: "What would happen if AE ran first?" (Answer: no DM context available — the system should warn but not fail)

### Transition

"We've covered study-level memory. The final piece: how do study lessons become company knowledge?"

---

## Module 7.5: Pitfall Promotion (40 min)

### Talking Points

1. The "auto-flag + manual approve" pattern mirrors how SOPs evolve in pharma
2. `get_promotable_patterns()` scans all `studies/*/memory/pitfalls.yaml`
3. Pitfalls matching in 2+ studies are flagged (same category + description)
4. A human reviewer must approve promotion — prevents study-specific quirks from becoming company rules
5. Promoted pitfalls live in `standards/memory/pitfalls.yaml` — visible to ALL future studies

### Live Demo: Full Promotion Workflow (20 min)

Walk through Exercise 7.5 Steps 1-5:
1. Create pitfalls in two studies
2. Run promotion scan
3. Show that study-specific issues are NOT flagged
4. Approve one promotion
5. Verify a new study would see it

### Key Architectural Point

Draw this on the whiteboard:

```
Study A: pitfall discovered  ----\
                                  +---> scan: 2+ studies? ---> flag ---> human approve ---> company level
Study B: same pitfall  ----------/
```

This is the same "standards with exceptions" pattern used for conventions and config — just applied to memory.

---

## Wrap-Up (15 min)

### Summary

1. **Coding standards**: Machine-readable rules in YAML, enforced via program headers and agent context
2. **Decision memory**: Every human choice recorded with rationale and outcome
3. **Pitfall memory**: Every failure recorded with root cause and resolution
4. **Cross-domain context**: Domain decisions flow to downstream domains
5. **Promotion**: Study lessons become company wisdom through auto-flag + manual approve

### Connection to Capstone

The capstone project brings all these layers together. Memory is what makes the orchestrator not just an automation tool but a **learning system** that improves with every study.

### Discussion

Ask the class:
1. "What recurring issues in your current work would benefit from a pitfall memory?"
2. "How would you convince your quality team that machine-readable coding standards are auditable?"
3. "What other types of memory would be valuable?" (e.g., reviewer preferences, data quality patterns, CRF annotation issues)

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 7.1: Why Agents Forget | 30 min | 0:30 |
| Break | 5 min | 0:35 |
| 7.2: Coding Standards | 35 min | 1:10 |
| 7.3: Decisions and Pitfalls | 40 min | 1:50 |
| Break | 10 min | 2:00 |
| 7.4: Cross-Domain Memory | 30 min | 2:30 |
| 7.5: Pitfall Promotion | 40 min | 3:10 |
| Wrap-Up | 15 min | 3:25 |
| **Total (with breaks)** | | **~3.5 hours** |
