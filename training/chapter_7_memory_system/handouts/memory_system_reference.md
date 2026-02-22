# Agent Memory System — Quick Reference

## Architecture Overview

```
standards/                          studies/{study}/
  coding_standards.yaml               memory/
  memory/                               decisions_log.yaml    <- auto-written
    program_header_template.txt          pitfalls.yaml         <- auto-written
    pitfalls.yaml      (promoted)        domain_context.yaml   <- auto-written
    decisions_log.yaml (patterns)        modification_history.yaml <- auto-written
```

**Read order**: company-level first, then study-level overlaid.
**Write target**: always study-level (company via promotion only).

---

## MemoryManager API

### Initialization

```python
from orchestrator.core.memory_manager import MemoryManager
mm = MemoryManager(
    standards_dir=Path('standards'),
    study_dir=Path('studies/XYZ_2026_001'),
    project_root=Path('.'),
)
```

### Read Methods

| Method | Returns | Used By |
|--------|---------|---------|
| `get_coding_standards()` | `Dict[str, Any]` | All agents |
| `get_program_header(**fields)` | `str` (rendered header) | Production, QC |
| `get_relevant_pitfalls(domain, category?)` | `List[PitfallRecord]` | All agents |
| `get_decision_history(domain, variable?)` | `List[DecisionRecord]` | Human review, Spec builder |
| `get_domain_context(domain)` | `Optional[DomainContext]` | Cross-domain agents |
| `get_all_domain_contexts()` | `Dict[str, DomainContext]` | Production, QC |
| `get_modification_history(program_name)` | `str` (formatted lines) | Production, QC |
| `build_agent_context(domain, agent_type, study_id, program_name)` | `Dict[str, Any]` | Pipeline orchestrator |

### Write Methods

| Method | Records | Called When |
|--------|---------|------------|
| `record_decision(DecisionRecord)` | Human review choice | After human review |
| `record_pitfall(PitfallRecord)` | Error/mismatch | On R failure, comparison mismatch, validation fail |
| `update_pitfall_resolution(domain, desc, resolution)` | Fix for prior pitfall | After retry succeeds |
| `save_domain_context(DomainContext)` | Cross-domain snapshot | End of domain pipeline |
| `update_modification_history(program, author, desc)` | Program change | Before R script write |

### Promotion Methods

| Method | Purpose |
|--------|---------|
| `get_promotable_patterns()` | Scan all studies, return pitfalls seen in 2+ |
| `list_pending_promotions()` | Promotable minus already-promoted |
| `promote_pitfall(PitfallRecord, approved_by)` | Copy to company level |

---

## Data Models

### DecisionRecord

```python
@dataclass
class DecisionRecord:
    domain: str              # "DM", "AE", etc.
    variable: str            # "RACE", "RFSTDTC", etc.
    choice: str              # "A", "B", "C", or custom text
    alternatives_shown: List[str]
    rationale: str
    source: str              # "convention" | "manual" | "manual_override"
    outcome: str             # "pending" | "success" | "mismatch" | "validation_fail"
    run_timestamp: str
    study_id: str
```

### PitfallRecord

```python
@dataclass
class PitfallRecord:
    category: str            # "r_script_error" | "comparison_mismatch" | "validation_fail" | "ct_mapping"
    domain: str
    description: str
    root_cause: str
    resolution: str
    severity: str            # "blocker" | "warning" | "info"
    run_timestamp: str
    study_id: str
    promotion_status: str    # "" | "pending" | "promoted"
```

### DomainContext

```python
@dataclass
class DomainContext:
    domain: str
    key_decisions: Dict[str, str]    # variable -> chosen approach
    derived_variables: List[str]      # variables other domains reference
    timestamp: str
    study_id: str
```

---

## Coding Standards Quick Reference

| Rule | Value | Example |
|------|-------|---------|
| R code case | lowercase | `library(arrow)`, `dm <- raw_dm` |
| SDTM variable names | UPPERCASE | `dm$STUDYID`, `dm$USUBJID` |
| ADaM variable names | UPPERCASE | `adsl$TRTA`, `adae$AVAL` |
| R local variables | snake_case | `raw_dm`, `ct_path`, `suppdm_idx` |
| R function names | snake_case | `iso_date()`, `derive_age()` |
| Indentation | 2 spaces | Standard R convention |
| Max line length | 120 characters | |
| Function reuse | Always check registry first | Never duplicate registered functions |
| Program header | Required on every program | From template with modification history |
| SDTM max var name | 8 characters | XPT transport limit |
| SDTM max label | 40 characters | IG label limit |

---

## Pipeline Integration Points

```
Spec Builder ←── coding_standards + decision_history + pitfalls
     ↓
Spec Reviewer
     ↓
Human Review ←── past_decisions + cross_domain ──→ writes DecisionRecords
     ↓
Production ←── coding_standards + header + pitfalls + cross_domain ──→ writes pitfalls on failure
     ↓
QC ←── coding_standards + header + pitfalls ──→ writes pitfalls on failure
     ↓
Compare ──→ writes pitfalls on mismatch
     ↓
Validate ──→ writes pitfalls on findings
     ↓
End ──→ saves DomainContext
```

---

## Key Files

| File | Purpose |
|------|---------|
| `orchestrator/core/memory_manager.py` | MemoryManager class and data models |
| `standards/coding_standards.yaml` | Company coding rules and CDISC compliance |
| `standards/memory/program_header_template.txt` | R program header template |
| `standards/memory/pitfalls.yaml` | Company-wide promoted pitfalls |
| `standards/memory/decisions_log.yaml` | Cross-study decision patterns |
| `studies/{study}/memory/decisions_log.yaml` | Study decision history |
| `studies/{study}/memory/pitfalls.yaml` | Study error/mismatch records |
| `studies/{study}/memory/domain_context.yaml` | Cross-domain decision snapshots |
| `studies/{study}/memory/modification_history.yaml` | Program change log |
