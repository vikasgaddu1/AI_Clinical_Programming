# Exercise 7.5: Pitfall Promotion — From Study Knowledge to Company Wisdom

## Objective

Implement the full pitfall promotion workflow: create pitfalls in two studies, auto-detect the recurring pattern, and promote it to company-level memory. This is how individual study lessons become organizational knowledge.

## Time: 40 minutes

---

## Background

The promotion workflow follows an "auto-flag + manual approve" pattern:
1. Each study records pitfalls as they occur
2. After pipeline runs, `get_promotable_patterns()` scans all studies
3. Pitfalls seen in 2+ studies are flagged as candidates
4. A human reviewer approves or rejects each promotion
5. Approved pitfalls move to `standards/memory/pitfalls.yaml`

This mirrors how pharma companies operate: study teams discover issues locally, but only proven patterns become SOPs.

---

## Steps

### Step 1: Create Pitfalls in Two Studies

First, create a temporary second study directory for this exercise:

```python
import os
from pathlib import Path

# Create a minimal second study structure
study2 = Path('studies/ABC_2026_002/memory')
study2.mkdir(parents=True, exist_ok=True)
print(f"Created: {study2}")
```

Now record the same pitfall in both studies:

```python
from orchestrator.core.memory_manager import MemoryManager, PitfallRecord

# Study 1: XYZ_2026_001
mm1 = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))
mm1.record_pitfall(PitfallRecord(
    category='r_script_error', domain='DM',
    description='iso_date fails on ambiguous slash-separated dates',
    root_cause='Both parts <= 12 defaults to MM/DD/YYYY',
    resolution='Use infmt parameter for non-US date formats',
    severity='blocker', study_id='XYZ-2026-001',
))
print("Recorded in XYZ_2026_001")

# Study 2: ABC_2026_002
mm2 = MemoryManager(Path('standards'), Path('studies/ABC_2026_002'), Path('.'))
mm2.record_pitfall(PitfallRecord(
    category='r_script_error', domain='DM',
    description='iso_date fails on ambiguous slash-separated dates',
    root_cause='European date format not auto-detected',
    resolution='Specify infmt="DD/MM/YYYY" explicitly',
    severity='blocker', study_id='ABC-2026-002',
))
print("Recorded in ABC_2026_002")

# Also record a study-specific pitfall (should NOT be promoted)
mm2.record_pitfall(PitfallRecord(
    category='ct_mapping', domain='DM',
    description='RACE value "Tagalog" not in C74457 codelist',
    root_cause='Study-specific ethnicity not in standard CT',
    resolution='Added to study ct_overrides.csv as ASIAN',
    severity='warning', study_id='ABC-2026-002',
))
print("Recorded study-specific pitfall in ABC_2026_002")
```

### Step 2: Scan for Promotable Patterns

```python
# Use any MemoryManager — it scans all studies
mm = MemoryManager(Path('standards'), project_root=Path('.'))
promotable = mm.get_promotable_patterns()

print(f"\nPromotable patterns found: {len(promotable)}")
for p in promotable:
    print(f"\n  Description: {p['description']}")
    print(f"  Category: {p['category']}")
    print(f"  Seen in studies: {p['studies']}")
    print(f"  First occurrence root cause: {p['first_occurrence'].get('root_cause', 'N/A')}")
```

> How many patterns were flagged for promotion? ___________

> Why was the "Tagalog" CT mapping issue NOT flagged? ___________

### Step 3: Check Pending Promotions

```python
pending = mm.list_pending_promotions()
print(f"Pending promotions: {len(pending)}")
for p in pending:
    print(f"  [{p['category']}] {p['description']}")
    print(f"  Studies: {p['studies']}")
```

### Step 4: Approve the Promotion

```python
# Simulate reviewer approval
pitfall_to_promote = PitfallRecord(
    category='r_script_error', domain='DM',
    description='iso_date fails on ambiguous slash-separated dates',
    root_cause='Both parts <= 12 defaults to MM/DD/YYYY; non-US formats need infmt parameter',
    resolution='Always specify infmt parameter when date format is known; add to coding standards',
    severity='blocker',
)
mm.promote_pitfall(pitfall_to_promote, approved_by='clinical_programming_lead')
print("Pitfall promoted to company level!")
```

Verify the company-level file:

```python
import yaml
with open('standards/memory/pitfalls.yaml') as f:
    data = yaml.safe_load(f)
for p in data.get('pitfalls', []):
    print(f"Category: {p['category']}")
    print(f"Description: {p['description']}")
    print(f"Promoted by: {p.get('promoted_by', 'N/A')}")
    print(f"Promotion date: {p.get('promotion_date', 'N/A')}")
```

> What fields were added during promotion? ___________

### Step 5: Verify All Future Studies See This Pitfall

```python
# A brand new study would see the promoted pitfall
mm_new = MemoryManager(Path('standards'), Path('studies/NEW_2027_001'), Path('.'))
company_pitfalls = mm_new.get_relevant_pitfalls('DM', 'r_script_error')
print(f"Company-level DM pitfalls: {len(company_pitfalls)}")
for p in company_pitfalls:
    print(f"  [{p.severity}] {p.description[:60]}...")
    print(f"    Resolution: {p.resolution}")
```

### Step 6: Clean Up

```python
import shutil, os

# Remove test study
shutil.rmtree('studies/ABC_2026_002', ignore_errors=True)
print("Removed test study ABC_2026_002")

# Remove test memory from XYZ
for f in ['pitfalls.yaml', 'decisions_log.yaml']:
    path = f'studies/XYZ_2026_001/memory/{f}'
    if os.path.exists(path):
        os.remove(path)

# Reset company pitfalls to empty
with open('standards/memory/pitfalls.yaml', 'w') as f:
    f.write('# Company-wide known pitfalls\npitfalls: []\n')
print("Reset company pitfalls")
```

---

## Reflection Questions

1. What threshold should trigger promotion? 2 studies? 3? Should it depend on severity?
2. How does this compare to how your organization currently escalates recurring issues from studies to SOPs?
3. What safeguards prevent a study-specific quirk from being promoted to company level?
4. Could this same pattern work for promoting successful decisions (not just pitfalls)?

---

## What You Should Have at the End

- [ ] Created pitfalls in two separate studies
- [ ] Used `get_promotable_patterns()` to detect recurring issues
- [ ] Promoted a pitfall to company level with reviewer attribution
- [ ] Verified the promoted pitfall is visible to all future studies
- [ ] Understood the auto-flag + manual approve workflow
