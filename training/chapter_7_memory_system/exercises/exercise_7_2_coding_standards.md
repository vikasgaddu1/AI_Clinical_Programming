# Exercise 7.2: Coding Standards — Teaching Agents Your House Rules

## Objective

Explore how company coding standards are captured in YAML and enforced during R code generation. You will read the standards file, trace how it flows into agent prompts, and verify that generated code complies.

## Time: 35 minutes

---

## Background

Every pharma company has house rules: lowercase code, standard headers, modification history, specific naming conventions. Before the memory system, these rules existed only in SOPs and people's heads. Now they're in `standards/coding_standards.yaml` — machine-readable, version-controlled, and automatically injected into every agent that generates code.

---

## Steps

### Step 1: Read the Coding Standards

```bash
python -c "
import yaml
with open('standards/coding_standards.yaml') as f:
    cs = yaml.safe_load(f)
for section in cs:
    print(f'Section: {section}')
    if isinstance(cs[section], dict):
        for k, v in cs[section].items():
            print(f'  {k}: {v}')
    print()
"
```

> What case must all R code use? ___________

> What case must SDTM variable names use? ___________

> What naming convention do R functions follow? ___________

> What is the function reuse policy? ___________

### Step 2: Examine the Program Header Template

```bash
python -c "
with open('standards/memory/program_header_template.txt') as f:
    print(f.read())
"
```

> List the fields in the header template:

> ___________

> Why is a modification history section important for regulatory submissions?

> ___________

### Step 3: Trace Standards Into Generated Code

Use the MemoryManager to build agent context and generate a script:

```python
from orchestrator.core.memory_manager import MemoryManager
from orchestrator.agents.production_programmer import generate_r_script
from pathlib import Path

mm = MemoryManager(Path('standards'), Path('studies/XYZ_2026_001'), Path('.'))
ctx = mm.build_agent_context('DM', 'production', 'XYZ-2026-001', 'dm_production.R')

# Check what the agent receives
print("Keys in context:", list(ctx.keys()))
print("\nProgram header (first 5 lines):")
for line in ctx['program_header'].split('\n')[:5]:
    print(line)

print("\nCoding standards - code style:")
print(ctx['coding_standards']['code_style'])
```

> What keys does the agent context contain? ___________

> Is the header pre-rendered or does the agent render it? ___________

### Step 4: Verify Compliance in Generated Code

Generate a production script and check compliance:

```python
spec = {
    'study_id': 'XYZ-2026-001', 'domain': 'DM',
    'human_decisions': {'RACE': {'choice': 'B'}},
    'variables': [],
}
script = generate_r_script(
    spec=spec,
    raw_data_path='study_data/raw_dm.csv',
    output_dataset_path='output/dm.parquet',
    function_library_path='r_functions',
    ct_lookup_path='macros/ct_lookup.csv',
    memory_context=ctx,
)

# Check: does the script start with the header?
lines = script.split('\n')
print("Line 1:", lines[0])
print("Has header:", lines[0].startswith("#'"))

# Check: are comments lowercase?
comment_lines = [l for l in lines if l.strip().startswith('#') and not l.startswith("#'")]
uppercase_comments = [l for l in comment_lines if l.strip('#').strip() != l.strip('#').strip().lower()]
print(f"\nComments: {len(comment_lines)} total, {len(uppercase_comments)} with uppercase")

# Check: are SDTM vars uppercase?
import re
dollar_refs = re.findall(r'\$(\w+)', script)
sdtm_vars = [v for v in dollar_refs if v.isupper()]
print(f"\nSDTM variable references: {sdtm_vars[:10]}...")
```

> Does the script include the standard header? ___________

> Are SDTM variable names in UPPERCASE? ___________

### Step 5: Examine the CDISC Compliance Rules

```python
cdisc = ctx['coding_standards']['cdisc_compliance']['sdtm']
print("Max variable name length:", cdisc['max_variable_name_length'])
print("Max label length:", cdisc['max_label_length'])
print("DM sort keys:", cdisc['required_sort_keys']['DM'])
print("XPT version:", cdisc['xpt_version'])
```

> How would you use `max_variable_name_length` to validate a dataset before writing XPT?

> ___________

---

## Reflection Questions

1. What happens if a study needs different coding standards (e.g., a Japanese submission requiring different date formats)?
2. How would you add a new rule to the coding standards (e.g., "all programs must include a data integrity check")?
3. Compare this approach to having rules in a Word document SOP. What are the advantages?

---

## What You Should Have at the End

- [ ] Read and understood all sections of `coding_standards.yaml`
- [ ] Traced the flow: YAML -> MemoryManager -> agent context -> generated R code
- [ ] Verified the generated script has a standard header
- [ ] Confirmed SDTM variables are UPPERCASE in generated code
- [ ] Understood how CDISC compliance rules can drive validation
