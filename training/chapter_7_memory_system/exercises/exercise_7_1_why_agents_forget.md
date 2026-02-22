# Exercise 7.1: Why Agents Forget — The Problem of Stateless Pipelines

## Objective

Understand why multi-agent pipelines lose institutional knowledge between runs, and identify the specific gaps that a memory system must fill. You will trace a real pipeline run and document where decisions, errors, and lessons disappear.

## Time: 30 minutes

---

## Background

Every time you run the SDTM orchestrator, each agent starts fresh. The production programmer doesn't know that the last run failed because of an ambiguous date format. The human reviewer doesn't know what was decided for RACE in the previous study. The QC programmer doesn't know why the comparison mismatched last time.

In a real pharma company, this knowledge lives in people's heads, in email threads, and in tribal knowledge. The memory system makes it explicit and machine-readable.

---

## Steps

### Step 1: Run the Pipeline and Observe

Run the DM pipeline in study mode:

```bash
python orchestrator/main.py --study XYZ_2026_001 --domain DM --stage spec_build
python orchestrator/main.py --study XYZ_2026_001 --domain DM --stage spec_review
```

Now examine the draft spec:

```bash
python -c "
import json
spec = json.load(open('studies/XYZ_2026_001/sdtm/specs/dm_mapping_spec.json'))
for v in spec['variables']:
    if v.get('human_decision_required'):
        print(f\"{v['target_variable']}: {len(v.get('decision_options', []))} options\")
"
```

> How many decision points require human input? ___________

> List them: ___________

### Step 2: Identify Knowledge That Gets Lost

Read the pipeline state file:

```bash
python -c "
import json
state = json.load(open('studies/XYZ_2026_001/sdtm/pipeline_state.json'))
print('Phase:', state['current_phase'])
print('Human decisions:', state['human_decisions'])
print('Error log:', state['error_log'])
"
```

> What is in `human_decisions`? ___________

> Why is it empty even though decisions exist in the spec? (Hint: this was a known gap before the memory system)

> ___________

### Step 3: Map the Eight Memory Gaps

Based on what you've seen, fill in this table of memory gaps:

> | Gap | What gets lost | Where it should be stored |
> |-----|---------------|--------------------------|
> | 1. No pitfall tracking | Errors are logged but never analyzed or fed back | ___________ |
> | 2. No cross-run learning | Each run starts fresh | ___________ |
> | 3. No sponsor-level memory | Company patterns only in static YAML | ___________ |
> | 4. No decision audit trail | Decisions buried in spec files | ___________ |
> | 5. No agent-to-agent feedback | Comparison mismatches don't inform retry | ___________ |
> | 6. No cross-domain memory | DM decisions don't inform AE | ___________ |
> | 7. Programmers ignore decisions | human_decisions not read by code gen | ___________ |
> | 8. Dead code in state | human_decisions field never populated | ___________ |

### Step 4: Examine the Existing Conventions System

Read the company conventions:

```bash
python -c "
import yaml
with open('standards/conventions.yaml') as f:
    conv = yaml.safe_load(f)
for var, cfg in conv.get('decisions', {}).items():
    print(f'{var}: approach={cfg[\"approach\"]}, rationale={cfg[\"rationale\"][:50]}...')
"
```

> What does the conventions system do well? ___________

> What can't it do? (Think: does it learn? does it track outcomes?) ___________

---

## Reflection Questions

1. In your current work, where does institutional knowledge get lost between programming cycles?
2. If a new programmer joins your team, how do they learn "we always do RACE approach B because..."?
3. What's the difference between a static convention ("always do X") and a memory ("last time we did X and it worked/failed")?

---

## What You Should Have at the End

- [ ] Identified 3+ decision points in the DM spec that require human input
- [ ] Documented why `human_decisions` in pipeline state was empty
- [ ] Filled in the memory gaps table with storage locations
- [ ] Articulated the difference between conventions (static) and memory (dynamic)
