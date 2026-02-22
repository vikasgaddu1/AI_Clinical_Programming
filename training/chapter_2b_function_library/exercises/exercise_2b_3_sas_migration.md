# Exercise 2B.3: Build a SAS-to-R Migration Plan

## Objective
Compare the SAS macro registry with the R function registry, understand the migration pattern, and design a registry entry for a hypothetical SAS macro being converted to R.

## Time: 20 minutes

---

## Steps

### Step 1: Side-by-Side Comparison

Open both files:
- `macros/macro_registry.json` (SAS)
- `r_functions/function_registry.json` (R)

Compare the `%iso_date` / `iso_date` entries. Fill in this table:

| Aspect | SAS `%iso_date` | R `iso_date` |
|--------|-----------------|-------------|
| Function call syntax | `%iso_date(inds=..., outds=..., invar=..., outvar=...)` | `dm <- iso_date(dm, invar=..., outvar=...)` |
| Input data parameter | `inds` (dataset name as string) | ___________ |
| Output data parameter | `outds` (dataset name as string) | ___________ |
| How data flows | Macro reads and writes SAS datasets by name | ___________ |
| Boolean parameter style | `Y`/`N` flags | ___________ |
| Dependencies field | ___________ | ___________ |
| `when_to_use` field | ___________ | ___________ |
| CT lookup path | ___________ | ___________ |

> What is the most fundamental difference in how SAS macros and R functions handle data?
> _________________________________________________________________

### Step 2: Identify the Language-Agnostic Parts

Review both registry entries for `assign_ct`. Mark each field as "same" or "different":

| Field | Same or Different? | Why? |
|-------|--------------------|------|
| `name` | Different | SAS uses `%` prefix |
| `category` | ___________ | ___________ |
| `purpose` | ___________ | ___________ |
| `when_to_use` | ___________ | ___________ |
| `parameters` | ___________ | ___________ |
| `supported_codelists` | ___________ | ___________ |
| `dependencies` | ___________ | ___________ |
| `usage_examples` | ___________ | ___________ |
| `notes` | ___________ | ___________ |

> Which fields could be copied directly from a SAS registry to start an R registry entry?
> _________________________________________________________________

### Step 3: Design a Migration Strategy

Imagine your team has these 8 SAS macros (common in clinical programming):

| # | SAS Macro | Purpose |
|---|-----------|---------|
| 1 | `%iso_date` | Date conversion (already migrated) |
| 2 | `%derive_age` | Age derivation (already migrated) |
| 3 | `%assign_ct` | CT mapping (already migrated) |
| 4 | `%merge_supp` | Merge SUPPQUAL records back to parent domain |
| 5 | `%visit_window` | Assign analysis visits based on windowing rules |
| 6 | `%lab_convert` | Convert lab values between units (SI ↔ conventional) |
| 7 | `%build_seq` | Generate --SEQ variables (sequential numbering per subject) |
| 8 | `%check_ct` | Validate that all CT values match expected codelist |

Prioritize them for migration. Consider:
- Frequency of use across domains
- Complexity of migration
- Regulatory importance
- Reusability across studies

| Priority | Macro | Reasoning |
|----------|-------|-----------|
| 1 (next) | ___________ | ___________ |
| 2 | ___________ | ___________ |
| 3 | ___________ | ___________ |
| 4 | ___________ | ___________ |
| 5 (last) | ___________ | ___________ |

### Step 4: Design a Registry Entry for `build_seq`

The `%build_seq` macro generates sequential numbering per subject (e.g., AESEQ, VSSEQ, LBSEQ). Design the R function registry entry:

```
Function name: build_seq
R file: build_seq.R
```

> Category: ___________

> Purpose (one line): ___________

> When to use (3 entries):
> 1. ___________
> 2. ___________
> 3. ___________

> Parameters:
> | Name | Type | Required | Description | Example |
> |------|------|----------|-------------|---------|
> | data | data frame | Yes | ___________ | ae |
> | subjvar | character | Yes | ___________ | ___________ |
> | outvar | character | No (default: --SEQ) | ___________ | ___________ |
> | sortby | character vector | No | ___________ | ___________ |

> Dependencies: ___________
> (Hint: Does --SEQ need any prior transformations?)

> Usage examples:
> 1. `ae <- build_seq(ae, subjvar = "USUBJID", outvar = "___________")`
> 2. `vs <- build_seq(vs, subjvar = "USUBJID", outvar = "___________", sortby = c("___________", "___________"))`

> Notes:
> 1. ___________
> 2. ___________

### Step 5: The Shared CT Lookup Pattern

Both SAS and R use the same `macros/ct_lookup.csv` file for controlled terminology. Review it:

```python
import pandas as pd
ct = pd.read_csv('macros/ct_lookup.csv')
print(f"Total mappings: {len(ct)}")
print(f"Codelists: {ct['CODELIST'].unique().tolist()}")
print(f"\nSEX mappings:")
print(ct[ct['CODELIST'] == 'C66731'][['RAW_VALUE', 'CT_VALUE']].to_string(index=False))
```

> How many codelists are currently defined? ___________
>
> If you were adding the AE domain, what new codelist would you need to add?
> _________________________________________________________________
>
> Is ct_lookup.csv language-specific (SAS or R only) or language-agnostic?
> _________________________________________________________________

---

## Discussion Questions

1. Your team has 40 SAS macros but is moving to R. Should you convert all 40 at once, or take an incremental approach? What are the risks of each?

2. Some SAS macros use SAS-specific features (PROC SQL, hash tables, BY-group processing). How would you document these in the registry so the R equivalent handles them correctly?

3. Should the registry include entries for BOTH the SAS macro and R function side by side (for teams still running both languages), or maintain separate registries?

---

## What You Should Have at the End

- [ ] Completed comparison table (SAS vs R registry structure)
- [ ] Identified language-agnostic vs language-specific fields
- [ ] Prioritized migration plan for 5 remaining macros
- [ ] Designed registry entry for `build_seq`
- [ ] Understanding that CT lookup data is language-agnostic
