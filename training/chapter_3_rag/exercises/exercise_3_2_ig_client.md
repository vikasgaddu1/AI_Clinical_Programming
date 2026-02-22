# Exercise 3.2: Use the File-Based IG Client

## Objective
Write Python scripts that use the `IGClient` to query SDTM IG content programmatically. Compare these results with what NotebookLM told you in Chapter 1.

## Time: 30 minutes

---

## Steps

### Step 1: Initialize the IG Client

In Claude Code or a Python terminal, run:

```python
import sys
sys.path.insert(0, 'orchestrator')
from core.ig_client import IGClient

ig = IGClient()
print(f"IG client available: {ig.is_available()}")
```

> Result: ___________

### Step 2: Get All DM Variables

```python
all_vars = ig.get_domain_variables("DM")
print(f"Total DM variables: {len(all_vars)}")
for var in all_vars:
    print(f"  {var['name']:15s} {var.get('requirement', 'N/A'):8s} {var.get('ct', 'None')}")
```

> How many DM variables are returned? ___________
>
> List 5 required variables:
> _________________________________________________________________

### Step 3: Get Required vs Conditional Variables

```python
required = ig.get_required_variables("DM")
conditional = ig.get_conditional_variables("DM")
ct_vars = ig.get_ct_variables("DM")

print(f"Required: {len(required)} variables")
print(f"Conditional/Expected: {len(conditional)} variables")
print(f"CT-controlled: {len(ct_vars)} variables")
```

> Required count: ___________
> Conditional count: ___________
> CT-controlled count: ___________

### Step 4: Get RACE Variable Detail

```python
race_detail = ig.get_variable_detail("DM", "RACE")
print(race_detail[:1000])  # First 1000 characters
```

> Does the detail include the "Other Specify" approaches? Yes / No
>
> Does it mention codelist C74457? Yes / No

### Step 5: Compare with Chapter 1 (NotebookLM)

In Chapter 1, you asked NotebookLM: "What are the required variables for the DM domain?"

Compare:

| Source | Required Variables Listed | Cited? |
|--------|-------------------------|--------|
| NotebookLM (Ch.1) | [from your Chapter 1 notes] | Yes (citations) |
| IGClient (Ch.3) | [from Step 3 output] | N/A (direct parse) |

> Are the lists consistent? ___________
>
> Which source gives more structured data? ___________

### Step 6: Try a Domain That Doesn't Exist

```python
ae_vars = ig.get_domain_variables("AE")
print(f"AE variables: {ae_vars}")
```

> What happened? ___________
>
> This gap motivates Exercise 3.4 -- you'll create the AE content file.

---

## What You Should Have at the End

- [ ] Successfully queried IGClient for DM variables, required variables, and RACE detail
- [ ] Compared IGClient results with Chapter 1 NotebookLM results
- [ ] Observed the AE domain gap (motivating Exercise 3.4)
