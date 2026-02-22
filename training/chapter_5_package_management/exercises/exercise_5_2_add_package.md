# Exercise 5.2: Add a Package with Versioned Documentation

## Objective
Register a new package in the approved registry and create its versioned documentation file so AI agents can discover and use it correctly.

## Time: 25 minutes

---

## Scenario

Your team wants to use the R `stringr` package (v1.5.1) for string manipulation in SDTM programming. IT has validated it. You need to:
1. Add it to the approved registry
2. Write the versioned documentation
3. Verify the PackageManager picks it up

---

## Steps

### Step 1: Design the Registry Entry

Fill in this template for `stringr`:

```json
{
  "name": "stringr",
  "language": "R",
  "approved_version": "1.5.1",
  "minimum_version": "___________",
  "status": "approved",
  "validation_date": "2026-02-01",
  "validated_by": "IT Validation Team",
  "documentation_path": "package_docs/r/stringr/1.5.1.md",
  "install_command": "___________",
  "purpose": "___________",
  "key_functions": [
    {
      "name": "str_trim",
      "description": "___________",
      "example": "___________"
    },
    {
      "name": "str_to_upper",
      "description": "___________",
      "example": "___________"
    },
    {
      "name": "str_detect",
      "description": "___________",
      "example": "___________"
    },
    {
      "name": "str_replace",
      "description": "___________",
      "example": "___________"
    }
  ],
  "restrictions": [
    "___________",
    "___________"
  ],
  "known_issues": [],
  "dependencies": ["stringi"]
}
```

Think about:
- What `purpose` describes stringr for SDTM programming?
- What `restrictions` should apply? (Hint: think about when to use base R `trimws()`, `toupper()` vs stringr)
- What `install_command` uses the internal mirror?

### Step 2: Add to the Registry

Add your entry to the `packages` array in `package_manager/approved_packages.json`.

Validate the JSON:
```python
import json
with open('package_manager/approved_packages.json') as f:
    reg = json.load(f)
print(f"Total packages: {len(reg['packages'])}")
for pkg in reg['packages']:
    print(f"  {pkg['name']} ({pkg.get('language', '?')}): {pkg.get('status', '?')}")
```

> Total packages now: ___________
>
> Does stringr appear? ___________

### Step 3: Create the Documentation File

Create `package_manager/package_docs/r/stringr/1.5.1.md`:

```markdown
# R stringr Package v1.5.1 -- Approved Documentation

**Package:** stringr
**Version:** 1.5.1 (approved)
**Language:** R
**Validation Status:** Approved (2026-02-01)

---

## Overview

[Write 2-3 sentences about stringr's purpose for SDTM programming]

## Installation (Enterprise)

[Write the install command using internal mirror]

## Key Functions

### `str_trim(string, side = "both")`
[Document this function with SDTM-relevant examples]

### `str_to_upper(string)`
[Document with example: converting raw values before CT mapping]

### `str_detect(string, pattern)`
[Document with example: detecting date format patterns]

### `str_replace(string, pattern, replacement)`
[Document with example: cleaning raw data values]

## SDTM-Specific Patterns

[Show 2-3 common patterns for SDTM string manipulation]

## Restrictions

[List the restrictions from the registry entry]
```

### Step 4: Verify PackageManager Integration

```python
import sys; sys.path.insert(0, '.')
from package_manager.package_manager import PackageManager

pm = PackageManager()

# Check it's discoverable
result = pm.is_approved("stringr", language="R")
print(f"Approved: {result['approved']}")
print(f"Reason: {result['reason']}")

# Get the documentation
docs = pm.get_documentation("stringr", language="R")
print(f"\nDocumentation ({len(docs)} chars):")
print(docs[:500])

# Get restrictions
print(f"\nRestrictions:")
for r in pm.get_restrictions("stringr", "R"):
    print(f"  - {r}")

# Get key functions
print(f"\nKey functions:")
for fn in pm.get_key_functions("stringr", "R"):
    print(f"  {fn['name']}: {fn['description']}")
```

> Does PackageManager find stringr? ___________
>
> Can it read the documentation? ___________

### Step 5: Test Code Compliance

```python
# Test that code using stringr passes compliance check
test_code = """
library(stringr)
library(arrow)
dm$RACE <- str_to_upper(str_trim(dm$RACE))
"""

issues = pm.check_code_compliance(test_code, "R")
if not issues:
    print("No compliance issues found")
else:
    for issue in issues:
        print(f"  [{issue['type']}] {issue['message']}")
```

> Does the stringr code pass compliance? ___________

### Step 6: Test Non-Compliant Code

```python
# Test code with violations
bad_code = """
library(tidyverse)
library(data.table)
library(arrow)
haven::write_xpt(dm, "dm.xpt", version = 8)
"""

issues = pm.check_code_compliance(bad_code, "R")
for issue in issues:
    print(f"  [{issue['type']}] {issue['package']}: {issue['message']}")
```

> How many issues were found? ___________
>
> List them:
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________

---

## Discussion Questions

1. How would you handle a situation where a package is approved but has a critical security vulnerability discovered after validation? What registry fields would you add?

2. Should the documentation file include examples specific to your study (XYZ-2026-001), or should it be study-agnostic? Why?

3. If `stringr` depends on `stringi`, should `stringi` also be in the approved registry? What's the policy for transitive dependencies?

---

## What You Should Have at the End

- [ ] stringr entry added to approved_packages.json
- [ ] Documentation file created at package_docs/r/stringr/1.5.1.md
- [ ] PackageManager discovers and returns stringr data
- [ ] Compliance check passes for code using stringr
- [ ] Understanding of the full workflow: register → document → verify
