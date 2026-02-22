# Exercise C.4: Design AE Domain Extension

## Objective
Design (on paper) how the orchestrator would extend to the Adverse Events (AE) domain. This is a conceptual exercise that connects Chapter 3's AE content file with the Capstone's multi-agent architecture.

## Time: 30 minutes

---

## Steps

### Step 1: Review What Exists for AE

If you created `ae_domain.md` in Chapter 3 Exercise 3.4, verify it works:
```python
import sys; sys.path.insert(0, 'orchestrator')
from core.ig_client import IGClient
ig = IGClient()
ae_vars = ig.get_domain_variables("AE")
print(f"AE variables: {len(ae_vars)}")
```

> AE variables available in IG client: ___________

If you didn't create it, use the reference solution at `training/chapter_3_rag/reference_solutions/ae_domain.md`. Copy it to `sdtm_ig_db/sdtm_ig_content/ae_domain.md`.

### Step 2: Design the AE Spec Structure

For each AE variable, design the mapping:

| Variable | Source in Raw Data | R Function | Codelist | Notes |
|----------|--------------------|------------|----------|-------|
| STUDYID | STUDYID (constant) | -- | -- | Pass-through |
| DOMAIN | -- (constant "AE") | -- | -- | Hardcoded |
| USUBJID | Derived | -- | -- | Same as DM |
| AESEQ | Derived | -- | -- | Sequential per subject |
| AETERM | AETERM | -- | -- | Verbatim, no mapping |
| AEDECOD | AETERM (coded) | ??? | MedDRA | Need new function? |
| AESTDTC | AE_START_DATE | iso_date() | -- | Reuse from DM |
| AEENDTC | AE_END_DATE | iso_date() | -- | Reuse from DM |
| AESER | AE_SERIOUS | assign_ct() | C66742 | Reuse from DM |
| AESEV | AE_SEVERITY | assign_ct() | C66769 | New codelist needed |
| AEREL | AE_RELATED | assign_ct() | C66742 | Reuse from DM |
| AEOUT | AE_OUTCOME | assign_ct() | C66768 | New codelist needed |

### Step 3: Identify Reusable vs New Components

**Reusable from DM (no changes needed):**
> List the R functions that work as-is for AE:
> _________________________________________________________________

**New R functions needed:**
> What new function would AE require that DM didn't need?
> _________________________________________________________________
> (Hint: AEDECOD requires MedDRA dictionary coding -- does assign_ct handle this?)

**New CT lookup entries needed:**
> What new codelists need to be added to macros/ct_lookup.csv?
> _________________________________________________________________

### Step 4: Identify Decision Points

What AE mapping decisions would need human review?

> Decision 1: _________________________________________________________________
> (e.g., How to handle partial AE start dates -- impute to Day 01 or Day 15?)
>
> Decision 2: _________________________________________________________________
> (e.g., How to map free-text severity descriptions to MILD/MODERATE/SEVERE?)
>
> Decision 3: _________________________________________________________________
> (e.g., How to handle causality when investigator used non-standard terms?)

### Step 5: What Changes in the Orchestrator?

Think about each component:

| Component | Change Needed? | What Changes? |
|-----------|---------------|---------------|
| `config.yaml` | Yes | Add `domain: "AE"`, update paths |
| `ig_client.py` | No | Already domain-generic (reads any domain md) |
| `function_registry.json` | Maybe | Add MedDRA coding function if needed |
| `ct_lookup.csv` | Yes | Add C66769, C66768 codelist entries |
| `spec_builder.py` | No* | Already domain-generic if IG-driven |
| `spec_reviewer.py` | No* | Uses `get_required_variables(domain)` |
| `production_programmer.py` | No* | Reads spec, generates R code |
| `qc_programmer.py` | No* | Same as production (independent) |
| `validation_agent.py` | No* | Reads spec for validation rules |
| `main.py` | No | Already accepts `--domain AE` |

*In LLM mode. In template/OFF mode, domain-specific templates would need to be created.

> The key insight: most orchestrator code is domain-generic because it reads from the IG and spec. The domain-specific content lives in markdown files and CSV lookups.

### Step 6: Cross-Domain Dependency Graph

When the orchestrator supports multiple domains, build order matters. DM must be built before AE because AE uses RFSTDTC from DM to derive AESTDY.

Sketch a dependency graph showing how DM and AE connect:

```
    DM
    ├── USUBJID ──────> AE.USUBJID (join key)
    ├── RFSTDTC ──────> AE.AESTDY derivation (AESTDTC - RFSTDTC + 1)
    └── RFENDTC ──────> AE.AEENDTC reference window
```

> **Question 1:** If you added VS (Vital Signs) and LB (Lab Results), what would the full dependency graph look like? Which domains depend on DM? Do any domains depend on each other?
> _________________________________________________________________

> **Question 2:** A graph database (e.g., Neo4j) can store these relationships as nodes and edges: `(DM)-[:PROVIDES]->(RFSTDTC)-[:USED_BY]->(AE.AESTDY)`. How would this help the orchestrator decide which domains to build first in a multi-domain pipeline?
> _________________________________________________________________

> **Question 3:** If RFSTDTC in DM changes after a spec revision, which downstream domains and variables would need to be rebuilt? How would a graph database answer this faster than searching through spec files?
> _________________________________________________________________

---

## Summary

> What three things would you need to add to support AE?
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________
>
> What is the single biggest challenge for AE that DM didn't have?
> _________________________________________________________________
> (Hint: MedDRA coding is a complex, dictionary-based process)

---

## What You Should Have at the End

- [ ] AE spec design on paper (variable-level mappings)
- [ ] Identified reusable R functions vs new ones needed
- [ ] Identified new CT lookup entries needed
- [ ] Listed AE-specific decision points for human review
- [ ] Understanding that most orchestrator code is domain-generic
