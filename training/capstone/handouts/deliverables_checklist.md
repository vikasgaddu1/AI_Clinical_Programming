# Capstone Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Pipeline Run

- [ ] Ran `python orchestrator/main.py --domain DM` end-to-end
- [ ] All 7 stages completed (spec_build, spec_review, human_review, production, qc, compare, validate)
- [ ] Made human decisions on flagged variables (RACE, others)
- [ ] Comparison result: MATCH (0 differences)
- [ ] Validation result: PASS

## Exercise C.1: Trace RACE Through the Pipeline

- [ ] Identified all distinct RACE values in raw data
- [ ] Checked IG requirements for RACE (codelist C74457)
- [ ] Reviewed RACE in draft spec (decision points)
- [ ] Reviewed RACE in approved spec (human decision recorded)
- [ ] Found RACE mapping in production R code
- [ ] Found RACE mapping in QC R code
- [ ] Checked comparison result for RACE
- [ ] Checked validation result for RACE
- [ ] Completed the traceability summary table

## Exercise C.2: Introduce a Deliberate Error

- [ ] Changed SEX codelist from C66731 to C74457
- [ ] Re-ran production and/or validation
- [ ] Identified which stages caught the error
- [ ] Restored the correct spec

## Exercise C.3: Add DTHFL to the Spec

- [ ] Added DTHFL variable to the approved spec JSON
- [ ] Re-ran production to regenerate the R script
- [ ] Verified DTHFL appears in the regenerated code
- [ ] Understood that spec changes flow automatically to code

## Exercise C.4: Design AE Domain Extension

- [ ] Designed AE variable mappings on paper
- [ ] Identified reusable R functions (iso_date, assign_ct)
- [ ] Identified new components needed (MedDRA function, new CT entries)
- [ ] Listed AE-specific decision points for human review
- [ ] Understood that most orchestrator code is domain-generic

---

## Final Deliverables

### RACE Traceability Document
Summarize the RACE variable's journey from raw data to validated dataset:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Where Human Judgment Was Required
List the decisions that could NOT be automated:
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

Why can't AI make these decisions autonomously?
_________________________________________________________________

### Key Takeaway
In one sentence, what is the most important principle of this system?
_________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Running the full SDTM pipeline | [ ] | [ ] | [ ] |
| Understanding the 5-agent architecture | [ ] | [ ] | [ ] |
| Tracing a variable through all pipeline stages | [ ] | [ ] | [ ] |
| Understanding the spec-driven approach | [ ] | [ ] | [ ] |
| Identifying where human judgment is needed | [ ] | [ ] | [ ] |
| Designing domain extensions (AE, VS, LB) | [ ] | [ ] | [ ] |
| Connecting all 7 chapters to the Capstone | [ ] | [ ] | [ ] |
| Source grounding (Ch.1) → IGClient in Spec Builder | [ ] | [ ] | [ ] |
| Claude Code architecture (Ch.2) → orchestrator skills + MCP | [ ] | [ ] | [ ] |
| Function registry (Ch.2B) → Production Programmer uses it | [ ] | [ ] | [ ] |
| RAG system (Ch.3) → IGClient powers all agents | [ ] | [ ] | [ ] |
| REST API / CDISC CT (Ch.4) → assign_ct() + CT validation | [ ] | [ ] | [ ] |
| Package management (Ch.5) → R code uses approved packages | [ ] | [ ] | [ ] |
| Vibe coding / agents (Ch.6) → how the orchestrator was built | [ ] | [ ] | [ ] |
| Memory system (Ch.7) → decisions, pitfalls, coding standards | [ ] | [ ] | [ ] |

## Chapter Connection Check

For each chapter, identify where you see its contribution in the running pipeline:

| Chapter | Where does it live in the capstone? |
|---------|-------------------------------------|
| Ch.1: NotebookLM (source grounding) | `orchestrator/core/ig_client.py` — agents query IG content the same way |
| Ch.2: Claude Code (skills, MCP, hooks) | `.claude/skills/`, `mcp_server.py`, `.claude/settings.local.json` |
| Ch.2B: Function library (registry) | `r_functions/function_registry.json` — Production Programmer reads this |
| Ch.3: RAG system | `sdtm_ig_db/sdtm_ig_content/*.md` — IGClient parses these files |
| Ch.4: REST API / CDISC CT | `macros/ct_lookup.csv` + NCI EVS API calls in `assign_ct()` |
| Ch.5: Package management | `standards/coding_standards.yaml` + R script `library()` calls |
| Ch.6: Vibe coding | `.claude/agents/*/AGENT.md` — the agent personas you built |
| Ch.7: Memory system | `orchestrator/core/memory_manager.py` — runs at every stage |
