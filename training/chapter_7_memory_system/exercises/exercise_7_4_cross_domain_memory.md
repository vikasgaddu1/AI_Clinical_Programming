# Exercise 7.4: Cross-Domain Memory — How DM Decisions Inform AE

## Objective

Understand how domain context snapshots enable cross-domain awareness. You will create a DM domain context, then see how an AE pipeline run would receive it.

## Time: 30 minutes

---

## Background

In SDTM programming, domains are not independent. DM establishes RFSTDTC (reference start date), which AE, LB, and VS use to calculate --DY (study day) variables. If DM chose approach A for RFSTDTC (informed consent date), every other domain must use that same reference date.

Without cross-domain memory, each domain's pipeline runs in isolation. With `DomainContext`, the AE pipeline knows what DM decided.

---

## Steps

### Step 1: Create a DM Domain Context

```python
from orchestrator.core.memory_manager import MemoryManager, DomainContext
from pathlib import Path

mm = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))

# Save DM context (this happens automatically at end of DM pipeline)
dm_context = DomainContext(
    domain='DM',
    key_decisions={
        'RACE': 'B',           # SUPPDM approach
        'RFSTDTC': 'A',        # Informed consent date as reference
        'RFENDTC': 'A',        # Set to missing (no raw source)
        'ACTARMCD': 'A',       # Equal to ARMCD (no deviations)
        'date_imputation': 'first_of_period',
    },
    derived_variables=[
        'USUBJID',   # STUDYID + SUBJID
        'AGE',       # From BRTHDTC and RFSTDTC
        'AGEU',      # Always YEARS
        'BRTHDTC',   # ISO 8601 from BRTHDT
        'RFSTDTC',   # ISO 8601 reference start date
        'DMDY',      # Study day of demographics
    ],
    study_id='XYZ-2026-001',
)
mm.save_domain_context(dm_context)
print("Saved DM domain context")
```

### Step 2: Read the Context File

```python
import yaml
with open('studies/XYZ_2026_001/memory/domain_context.yaml') as f:
    data = yaml.safe_load(f)
print(yaml.dump(data, default_flow_style=False))
```

> What key decisions from DM would affect AE processing?

> ___________

> What derived variables from DM would other domains reference?

> ___________

### Step 3: Simulate AE Pipeline Reading DM Context

```python
# Fresh MemoryManager (simulating AE pipeline start)
mm_ae = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))

# What does the AE spec builder see?
all_contexts = mm_ae.get_all_domain_contexts()
print(f"Available domain contexts: {list(all_contexts.keys())}")

dm_ctx = mm_ae.get_domain_context('DM')
if dm_ctx:
    print(f"\nDM key decisions:")
    for var, choice in dm_ctx.key_decisions.items():
        print(f"  {var}: {choice}")
    print(f"\nDM derived variables: {dm_ctx.derived_variables}")

    # Critical for AE: which date is RFSTDTC?
    rfstdtc_approach = dm_ctx.key_decisions.get('RFSTDTC', 'unknown')
    print(f"\nRFSTDTC approach: {rfstdtc_approach}")
    print("AE must use the SAME reference date for --DY calculations!")
```

> Why is it critical that AE knows the RFSTDTC approach chosen in DM?

> ___________

### Step 4: Build AE Agent Context with Cross-Domain Awareness

```python
ae_ctx = mm_ae.build_agent_context('AE', 'production', 'XYZ-2026-001', 'ae_production.R')
print("AE agent context keys:", list(ae_ctx.keys()))
print(f"Cross-domain contexts available: {list(ae_ctx.get('cross_domain', {}).keys())}")

# The AE production programmer would see DM's decisions
if 'cross_domain' in ae_ctx and 'DM' in ae_ctx['cross_domain']:
    dm_info = ae_ctx['cross_domain']['DM']
    print(f"\nDM decisions visible to AE agent:")
    for var, choice in dm_info.get('key_decisions', {}).items():
        print(f"  {var}: {choice}")
```

### Step 5: Clean Up

```python
import os
path = 'studies/XYZ_2026_001/memory/domain_context.yaml'
if os.path.exists(path):
    os.remove(path)
    print(f"Cleaned up: {path}")
```

---

## Reflection Questions

1. What would happen if the AE pipeline ran BEFORE DM? How should the system handle missing domain context?
2. Beyond RFSTDTC, what other DM decisions might affect downstream domains?
3. In your experience, how do teams currently communicate cross-domain decisions? (Email? Meetings? Notes in specs?)

---

## What You Should Have at the End

- [ ] Created a DM domain context with key decisions and derived variables
- [ ] Verified the YAML file on disk
- [ ] Read DM context from a simulated AE pipeline
- [ ] Understood why RFSTDTC approach must be consistent across domains
- [ ] Built an AE agent context that includes DM cross-domain information
