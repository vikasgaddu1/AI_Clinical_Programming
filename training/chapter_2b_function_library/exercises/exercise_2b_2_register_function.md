# Exercise 2B.2: Register a New R Function

## Objective
Write a new R function and register it in `function_registry.json` so that AI agents can discover and use it.

## Time: 30 minutes

---

## Scenario

Your team frequently needs to derive the study day variable (e.g., DMDY, VSDY, AEENDY) across multiple SDTM domains. The formula is:

```
If event_date >= reference_date:
    study_day = (event_date - reference_date) + 1
If event_date < reference_date:
    study_day = (event_date - reference_date)
```

Note: There is no Day 0 in SDTM. Day -1 is the day before Day 1.

You will create an R function `derive_studyday` and register it.

---

## Steps

### Step 1: Write the R Function

Create `r_functions/derive_studyday.R`:

```r
################################################################################
# Function: derive_studyday
# Purpose:  Calculate study day from event date and reference date (RFSTDTC)
#
# Parameters:
#   data    - Data frame with event and reference dates
#   evtdt   - Name of the event date variable (ISO YYYY-MM-DD character)
#   refdt   - Name of the reference date variable (ISO YYYY-MM-DD character)
#   outvar  - Name of the output study day variable (numeric)
#
# Returns: Data frame with outvar added (numeric, no Day 0 per SDTM)
#
# Rules:
#   event_date >= reference_date: study_day = (event - ref) + 1
#   event_date <  reference_date: study_day = (event - ref)
#   Missing event or reference date: study_day = NA
################################################################################

derive_studyday <- function(data, evtdt, refdt, outvar = "STUDYDAY") {
  # YOUR CODE HERE
  # Hint:
  # 1. Parse both dates with as.Date()
  # 2. Calculate difference in days: as.integer(difftime(evt, ref, units = "days"))
  # 3. Apply the no-Day-0 rule
  # 4. Add the result as a new column
}
```

> Fill in the function body. Test with:
> ```r
> test_data <- data.frame(
>   DMDTC = c("2026-01-15", "2025-12-20", "2026-01-10", NA),
>   RFSTDTC = c("2026-01-10", "2026-01-10", "2026-01-10", "2026-01-10")
> )
> source("r_functions/derive_studyday.R")
> result <- derive_studyday(test_data, evtdt = "DMDTC", refdt = "RFSTDTC", outvar = "DMDY")
> print(result$DMDY)
> # Expected: 6, -21, 1, NA
> ```

### Step 2: Write the Registry Entry

Now register your function. Add a new entry to the `functions` array in `r_functions/function_registry.json`.

Design the entry by filling in this template:

```json
{
  "name": "derive_studyday",
  "file": "derive_studyday.R",
  "category": "___________",
  "purpose": "___________",
  "when_to_use": [
    "___________",
    "___________",
    "___________"
  ],
  "parameters": [
    {
      "name": "data",
      "type": "data frame",
      "required": true,
      "description": "___________",
      "example": "dm"
    },
    {
      "name": "evtdt",
      "type": "character",
      "required": true,
      "description": "___________",
      "example": "___________"
    },
    {
      "name": "refdt",
      "type": "character",
      "required": true,
      "description": "___________",
      "example": "___________"
    },
    {
      "name": "outvar",
      "type": "character",
      "required": false,
      "default": "STUDYDAY",
      "description": "___________",
      "example": "DMDY"
    }
  ],
  "output_type": "___________",
  "dependencies": ["___________"],
  "usage_examples": [
    {
      "description": "Derive DMDY from DMDTC and RFSTDTC",
      "code": "___________"
    },
    {
      "description": "Derive AEENDY for adverse events",
      "code": "___________"
    }
  ],
  "notes": [
    "No Day 0: day before reference = -1, day of reference = 1",
    "___________",
    "___________"
  ]
}
```

> Fill in all the blank fields. Think carefully about:
> - What `category` best describes this function?
> - What scenarios should go in `when_to_use`?
> - What are the dependencies? (Hint: dates must be ISO first)
> - What notes should warn about edge cases?

### Step 3: Validate the Registry

After adding your entry, verify the JSON is still valid:

```python
import json
with open('r_functions/function_registry.json') as f:
    reg = json.load(f)
print(f"Functions in registry: {len(reg['functions'])}")
for fn in reg['functions']:
    print(f"  {fn['name']}")
```

> How many functions are now in the registry? ___________
>
> Does `derive_studyday` appear in the list? ___________

### Step 4: Verify FunctionLoader Picks It Up

```python
import sys; sys.path.insert(0, 'orchestrator')
from core.function_loader import FunctionLoader

fl = FunctionLoader('r_functions/function_registry.json')

# Check it's discoverable
fn = fl.get_function_by_name('derive_studyday')
print(f"Found: {fn['name']}")
print(f"Purpose: {fn['purpose']}")
print(f"When to use: {fn['when_to_use']}")

# Check dependency order
print(f"\nExecution order: {fl.get_dependency_order()}")
```

> Does `derive_studyday` appear in the dependency order? ___________
>
> Does it appear after `iso_date` (since it depends on ISO dates)? ___________

### Step 5: Update the Orchestrator Integration Section

Add `derive_studyday` to the `orchestrator_integration.example_sequence`:

```json
{
  "step": 6,
  "function": "derive_studyday",
  "reason": "DMDY from DMDTC and RFSTDTC after dates are ISO",
  "call": "dm <- derive_studyday(dm, evtdt = \"DMDTC\", refdt = \"RFSTDTC\", outvar = \"DMDY\")"
}
```

> Where in the sequence does this step belong (after which existing step)?
> _________________________________________________________________

---

## Reference Solution

A complete reference solution is available at `training/chapter_2b_function_library/reference_solutions/derive_studyday.R` and `training/chapter_2b_function_library/reference_solutions/derive_studyday_registry_entry.json`.

---

## Discussion Questions

1. Your team also needs `derive_duration` (e.g., AEDUR = AEENDTC - AESTDTC + 1). How would the registry entry differ from `derive_studyday`?

2. Should the `when_to_use` field include negative guidance (e.g., "Do NOT use for datetime variables with time components")? Why?

3. If you needed to support partial dates (e.g., "2026-01" with missing day), how would you document this in the registry?

---

## What You Should Have at the End

- [ ] Working `derive_studyday.R` function file
- [ ] Registry entry added to `function_registry.json`
- [ ] JSON validated (no parse errors)
- [ ] FunctionLoader discovers the new function
- [ ] Dependency order is correct (iso_date before derive_studyday)
