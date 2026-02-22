# Exercise 5.1: Explore the Approved Package Registry

## Objective
Understand the structure and purpose of the enterprise approved package registry by reading `approved_packages.json` and using the `PackageManager` class.

## Time: 20 minutes

---

## Steps

### Step 1: Read the Registry

Open `package_manager/approved_packages.json`. Answer:

> How many total packages are in the registry? ___________
>
> How many are approved? ___________
>
> How many are NOT approved? ___________
>
> How many are under review? ___________
>
> What languages are covered? ___________

### Step 2: Examine an Approved Package

Find the `arrow` (R) entry. Answer:

> Approved version: ___________
>
> Minimum version: ___________
>
> How many key_functions are listed? ___________
>
> How many restrictions? ___________
>
> What is the documentation_path? ___________

### Step 3: Examine a Not-Approved Package

Find the `tidyverse` entry.

> Why was tidyverse not approved?
> _________________________________________________________________
>
> What alternative does the registry suggest?
> _________________________________________________________________
>
> If a participant asks Claude Code to "use tidyverse to process data", what should Claude do?
> _________________________________________________________________

### Step 4: Use PackageManager in Python

Run from the project root:

```python
import sys; sys.path.insert(0, '.')
from package_manager.package_manager import PackageManager

pm = PackageManager()

# List all approved R packages
print("Approved R packages:")
for pkg in pm.get_approved_packages("R"):
    print(f"  {pkg['name']} v{pkg['approved_version']} - {pkg['purpose']}")

print("\nApproved Python packages:")
for pkg in pm.get_approved_packages("Python"):
    print(f"  {pkg['name']} v{pkg['approved_version']} - {pkg['purpose']}")
```

> How many approved R packages? ___________
>
> How many approved Python packages? ___________

### Step 5: Check Package Approval Status

```python
# Check various packages
packages_to_check = [
    ("arrow", "R"),
    ("haven", "R"),
    ("tidyverse", "R"),
    ("data.table", "R"),
    ("pandas", "Python"),
    ("numpy", "Python"),
]

for name, lang in packages_to_check:
    result = pm.is_approved(name, language=lang)
    status = "APPROVED" if result['approved'] else "NOT APPROVED"
    print(f"  {name} ({lang}): {status} - {result['reason']}")
```

Fill in the results:

| Package | Language | Status | Reason |
|---------|----------|--------|--------|
| arrow | R | ___________ | ___________ |
| haven | R | ___________ | ___________ |
| tidyverse | R | ___________ | ___________ |
| data.table | R | ___________ | ___________ |
| pandas | Python | ___________ | ___________ |
| numpy | Python | ___________ | ___________ |

### Step 6: Read Versioned Documentation

```python
# Get haven documentation
docs = pm.get_documentation("haven", language="R")
print(docs[:1000])
```

> What version of haven is documented? ___________
>
> What does the documentation say about write_xpt version parameter?
> _________________________________________________________________
>
> Is this information in the public CRAN haven page? Why does the enterprise doc include it?
> _________________________________________________________________

### Step 7: Check Package Restrictions

```python
# Get restrictions for all approved R packages
for pkg in pm.get_approved_packages("R"):
    restrictions = pm.get_restrictions(pkg['name'], "R")
    if restrictions:
        print(f"\n{pkg['name']} restrictions:")
        for r in restrictions:
            print(f"  - {r}")
```

> Which package has the most restrictions? ___________
>
> List two restrictions that directly affect SDTM programming:
> 1. _________________________________________________________________
> 2. _________________________________________________________________

### Step 8: See What AI Sees

```python
# Format for an AI agent prompt
prompt_text = pm.format_for_prompt("R")
print(prompt_text)
print(f"\n--- {len(prompt_text)} characters ---")
```

> How does this compare to FunctionLoader.format_for_prompt() from Chapter 2B?
> _________________________________________________________________

---

## Discussion Questions

1. Why does the registry include a `minimum_version` in addition to `approved_version`? When would a team use a version between minimum and approved?

2. The `install_command` uses an internal repository URL (`internal-cran.company.com`). Why not just use the public CRAN? What are the risks?

3. If your team needs a package that isn't in the registry (like `stringr`), what should the process be?

---

## What You Should Have at the End

- [ ] Understanding of the approved_packages.json structure
- [ ] Ability to query the PackageManager for any package
- [ ] Understanding of the three statuses (approved, not_approved, under_review)
- [ ] Ability to read versioned documentation for an approved package
- [ ] Understanding of how restrictions protect regulatory compliance
