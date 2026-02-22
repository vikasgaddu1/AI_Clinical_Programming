# Exercise 7.3: Decision Memory and Pitfall Tracking

## Objective

Use the MemoryManager API to record decisions and pitfalls, then verify they persist across simulated pipeline runs. You will see how past decisions inform future reviews and how errors become lessons.

## Time: 40 minutes

---

## Background

The memory system has two core record types:
- **DecisionRecord**: What was decided, by whom, with what alternatives, and what happened after
- **PitfallRecord**: What went wrong, why, how it was fixed, and how severe it was

Both follow the layered architecture: study-level records are written during pipeline runs; company-level records are promoted when patterns recur across studies.

---

## Steps

### Step 1: Record Decisions Programmatically

```python
from orchestrator.core.memory_manager import MemoryManager, DecisionRecord
from pathlib import Path

mm = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))

# Simulate recording decisions from a human review
decisions = [
    DecisionRecord(
        domain='DM', variable='RACE', choice='B',
        alternatives_shown=['A', 'B', 'C'],
        rationale='Company default: SUPPDM approach per SOP-DM-003',
        source='convention', outcome='success',
        study_id='XYZ-2026-001',
    ),
    DecisionRecord(
        domain='DM', variable='RFENDTC', choice='A',
        alternatives_shown=['A', 'B'],
        rationale='No end-of-participation date available in raw DM data',
        source='manual', outcome='success',
        study_id='XYZ-2026-001',
    ),
    DecisionRecord(
        domain='DM', variable='ACTARMCD', choice='A',
        alternatives_shown=['A', 'B'],
        rationale='Protocol confirms no treatment deviations in this study',
        source='convention', outcome='success',
        study_id='XYZ-2026-001',
    ),
]

for d in decisions:
    mm.record_decision(d)
    print(f"Recorded: {d.variable} = {d.choice} ({d.source})")
```

Now verify the file was written:

```python
import yaml
with open('studies/XYZ_2026_001/memory/decisions_log.yaml') as f:
    data = yaml.safe_load(f)
print(f"\nDecisions on disk: {len(data.get('decisions', []))}")
for d in data['decisions']:
    print(f"  {d['variable']}: {d['choice']} ({d['source']}) -> {d['outcome']}")
```

> How many decisions were recorded? ___________

> What fields does each decision record contain? ___________

### Step 2: Record Pitfalls

```python
from orchestrator.core.memory_manager import PitfallRecord

pitfalls = [
    PitfallRecord(
        category='r_script_error', domain='DM',
        description='iso_date fails on dates like "03/04/2020" where both parts <= 12',
        root_cause='Ambiguous date format defaults to MM/DD/YYYY but source data is DD/MM/YYYY',
        resolution='Added infmt="DD/MM/YYYY" parameter to iso_date() call',
        severity='blocker', study_id='XYZ-2026-001',
    ),
    PitfallRecord(
        category='comparison_mismatch', domain='DM',
        description='DMDY differs between production and QC: production uses as.integer(), QC uses floor()',
        root_cause='Different rounding behavior for fractional days',
        resolution='Both programs now use as.integer() for consistency',
        severity='warning', study_id='XYZ-2026-001',
    ),
]

for p in pitfalls:
    mm.record_pitfall(p)
    print(f"Recorded pitfall: [{p.category}] {p.description[:60]}...")
```

> What categories of pitfalls exist? ___________

### Step 3: Read Memory Back (Simulating Next Run)

```python
# Create a fresh MemoryManager (simulating a new pipeline run)
mm2 = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))

# What does the next human reviewer see?
past_decisions = mm2.get_decision_history('DM')
print(f"Past decisions for DM: {len(past_decisions)}")
for d in past_decisions:
    print(f"  {d.variable}: chose {d.choice} ({d.source}) -> {d.outcome}")

# What does the next production programmer see?
pitfalls = mm2.get_relevant_pitfalls('DM', 'r_script_error')
print(f"\nKnown R script pitfalls for DM: {len(pitfalls)}")
for p in pitfalls:
    print(f"  [{p.severity}] {p.description[:60]}...")
    print(f"    Fix: {p.resolution}")
```

> How would seeing "iso_date fails on ambiguous dates" help the production programmer avoid the same mistake?

> ___________

### Step 4: Build Full Agent Context

```python
ctx = mm2.build_agent_context('DM', 'production', 'XYZ-2026-001', 'dm_production.R')
print("Context keys:", list(ctx.keys()))
print(f"Known pitfalls in context: {len(ctx.get('known_pitfalls', []))}")
print(f"Cross-domain contexts: {list(ctx.get('cross_domain', {}).keys())}")
```

> What is the purpose of cross_domain in the agent context?

> ___________

### Step 5: Clean Up Test Data

```python
import os
# Remove test memory files so they don't interfere with real runs
for f in ['decisions_log.yaml', 'pitfalls.yaml']:
    path = f'studies/XYZ_2026_001/memory/{f}'
    if os.path.exists(path):
        os.remove(path)
        print(f"Cleaned up: {path}")
```

---

## Reflection Questions

1. A decision has `outcome: "pending"` when first recorded. When and how should it be updated to "success" or "mismatch"?
2. If the same pitfall appears in 3 different studies, what should happen? (Hint: promotion workflow)
3. How is a DecisionRecord different from a Convention? When would you use each?

---

## What You Should Have at the End

- [ ] Recorded 3 decisions and 2 pitfalls via the MemoryManager API
- [ ] Verified persistence in YAML files on disk
- [ ] Read memory back with a fresh MemoryManager instance
- [ ] Built an agent context and understood what each agent receives
- [ ] Articulated how memory prevents repeated mistakes
