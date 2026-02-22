# Exercise 2B.1: Explore the Existing Function Registry

## Objective
Understand the structure and purpose of the function registry by reading and analyzing `r_functions/function_registry.json`.

## Time: 20 minutes

---

## Steps

### Step 1: Read the Registry File

Open `r_functions/function_registry.json` in your editor (or VS Code / Cursor). Answer:

> How many functions are registered? ___________
>
> What is the registry version? ___________
>
> What language are the functions written in? ___________

### Step 2: Examine the `iso_date` Entry

Find the `iso_date` function entry. Answer these questions:

> What category is `iso_date` in? ___________
>
> How many parameters does it have? ___________
>
> Which parameters are required vs optional?
> - Required: ___________
> - Optional: ___________
>
> What does `iso_date` do when it encounters an ambiguous date like `03/04/2020`?
> _________________________________________________________________

### Step 3: Understand `when_to_use`

The `when_to_use` field is an array of scenarios. This is what AI reads to decide whether to use a function.

> List the `when_to_use` entries for `assign_ct`:
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________
>
> If you were an AI agent and received a task "Map the raw SEX variable to CDISC controlled terminology", which `when_to_use` entry would trigger you to select `assign_ct`?
> _________________________________________________________________

### Step 4: Trace the Dependency Chain

Look at the `dependencies` field for each function:

| Function | Dependencies |
|----------|-------------|
| `iso_date` | ___________ |
| `derive_age` | ___________ |
| `assign_ct` | ___________ |

> Why does `derive_age` depend on `iso_date`?
> _________________________________________________________________

> What is the correct execution order for all three functions?
> 1. ___________
> 2. ___________
> 3. ___________

### Step 5: Use the FunctionLoader in Python

Run this script from the project root:

```python
import sys; sys.path.insert(0, 'orchestrator')
from core.function_loader import FunctionLoader

fl = FunctionLoader('r_functions/function_registry.json')

# List all functions
for fn in fl.get_functions():
    print(f"  {fn['name']:15s} - {fn['purpose']}")

# Get dependency order
print("\nExecution order:", fl.get_dependency_order())

# Look up a specific function
iso = fl.get_function_by_name('iso_date')
print(f"\niso_date parameters: {len(iso['parameters'])}")
for p in iso['parameters']:
    req = "REQUIRED" if p['required'] else "optional"
    print(f"  {p['name']:15s} ({req}): {p['description']}")
```

> What does `get_dependency_order()` return? ___________
>
> Does the order match what you determined in Step 4? ___________

### Step 6: See What the AI Sees

Run this to see how the registry is formatted for AI agent prompts:

```python
print(fl.format_for_prompt())
```

> How many lines of text does `format_for_prompt()` produce? ___________
>
> Compare this output to the raw JSON. What information is included? What is omitted?
> - Included: _________________________________________________________________
> - Omitted: _________________________________________________________________

### Step 7: Compare with the SAS Registry

Open `macros/macro_registry.json`. Compare the `%iso_date` entry with the R `iso_date` entry.

> What is structurally different between the SAS and R entries?
> _________________________________________________________________
>
> What is the same?
> _________________________________________________________________
>
> Could an AI use either registry to generate code in the corresponding language? Why?
> _________________________________________________________________

---

## Discussion Questions

1. What would happen if the registry entry for `iso_date` was missing the `infmt` optional parameter? How might AI-generated code be affected?

2. The `assign_ct` function has a `supported_codelists` field listing all CT codes it can handle. How does this help AI select the right codelist for a variable like RACE?

3. The registry has an `orchestrator_integration.example_sequence` section. Why is this valuable for AI agents?

---

## What You Should Have at the End

- [ ] Understanding of the registry's JSON structure
- [ ] Ability to read any function entry and explain its fields
- [ ] Working Python code using FunctionLoader
- [ ] Understanding of dependency ordering
- [ ] Comparison between R and SAS registry formats
