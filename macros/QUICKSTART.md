# Quick Start Guide - SAS Macro Library for AI Orchestration

## What You Have

A complete **AI-orchestrator-ready SAS macro library** in `/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/`

**Key File: `macro_registry.json`** - This is what the AI orchestrator reads to discover and use macros.

## Files in This Library

| File | Purpose | Who Uses It |
|------|---------|-----------|
| `macro_registry.json` | Machine-readable catalog of all macros | **AI Orchestrators (PRIMARY)** |
| `iso_date.sas` | SAS macro for date conversion | SAS system |
| `derive_age.sas` | SAS macro for age calculation | SAS system |
| `assign_ct.sas` | SAS macro for CT mapping | SAS system |
| `ct_lookup.csv` | Controlled terminology reference data | `assign_ct.sas` macro |
| `README.md` | Complete library documentation | Everyone |
| `IMPLEMENTATION_GUIDE.md` | How to build an AI orchestrator | AI Developers |
| `LIBRARY_STRUCTURE.txt` | Quick reference | Quick lookup |
| `orchestrator_example.py` | Working Python example | AI Developers |
| `QUICKSTART.md` | This file | You (first-time users) |

## For AI Orchestrators: 30-Second Overview

```
1. Read macro_registry.json
2. For each macro in the "macros" array:
   - name: macro identifier (e.g., "%iso_date")
   - purpose: what it does
   - parameters: required and optional inputs
   - dependencies: other macros it needs
   - when_to_use: guidance on when to apply it
3. Match input dataset variables to macro purposes
4. Sort macros by dependencies
5. Generate SAS code with proper parameter values
6. Execute the SAS code
7. Validate results
```

See `orchestrator_example.py` for a complete working example.

## For SAS Programmers: 30-Second Overview

**Using %iso_date macro:**
```sas
%include "/path/to/iso_date.sas";

%iso_date(
  inds=raw.dm,              /* Input dataset */
  outds=work.dm_iso,        /* Output dataset */
  invar=BRTHDT,             /* Variable to convert */
  outvar=BRTHDTC            /* Output variable name */
);
```

**Using %derive_age macro:**
```sas
%include "/path/to/derive_age.sas";

%derive_age(
  inds=work.dm_iso,         /* Input dataset */
  outds=work.dm_derived,    /* Output dataset */
  brthdt=BRTHDTC,           /* Birth date variable */
  refdt=RFSTDTC,            /* Reference date variable */
  agevar=AGE                /* Output age variable */
);
```

**Using %assign_ct macro:**
```sas
%include "/path/to/assign_ct.sas";

%assign_ct(
  inds=work.dm_derived,     /* Input dataset */
  outds=work.dm_final,      /* Output dataset */
  invar=RAW_SEX,            /* Input variable with raw values */
  outvar=SEX,               /* Output variable with CT values */
  codelist=C66731,          /* CDISC codelist code for SEX */
  ctpath=/path/to/ct_lookup.csv
);
```

## Understanding macro_registry.json

The registry is a JSON file with this structure:

```json
{
  "registry_version": "1.0",
  "macros": [
    {
      "name": "%iso_date",
      "file": "iso_date.sas",
      "purpose": "Convert dates to ISO 8601 format",
      "when_to_use": [
        "When converting raw dates to SDTM format",
        "Before doing age calculations with dates"
      ],
      "parameters": [
        {
          "name": "inds",
          "type": "dataset name",
          "required": true,
          "description": "Input dataset",
          "example": "raw.dm"
        },
        ...
      ],
      "dependencies": [],
      "output_type": "Character variable in YYYY-MM-DD format",
      "usage_examples": [
        {
          "description": "Convert birth dates",
          "code": "%iso_date(inds=raw.dm, outds=work.dm_iso, invar=BRTHDT, outvar=BRTHDTC);"
        }
      ]
    }
  ]
}
```

### What Each Section Means

- **name** - The macro name with % (e.g., "%iso_date")
- **file** - The SAS file containing the macro
- **purpose** - One-sentence description
- **when_to_use** - Array of use cases (helps AI decide whether to use this macro)
- **parameters** - Array of input parameters with metadata
- **dependencies** - List of other macros this depends on
- **output_type** - What the macro produces
- **usage_examples** - Example SAS code

## Example: How an AI Orchestrator Uses This

### Input Dataset
Raw demographics with these variables:
```
USUBJID, RAW_BRTHDT, RAW_RFSTDTC, RAW_SEX, RAW_RACE
```

### Orchestrator Steps

1. **Read registry** → Discover 3 macros: %iso_date, %derive_age, %assign_ct

2. **Analyze input** → Found:
   - RAW_BRTHDT needs conversion (matches %iso_date)
   - RAW_RFSTDTC needs conversion (matches %iso_date)
   - RAW_SEX needs CT mapping (matches %assign_ct)
   - RAW_RACE needs CT mapping (matches %assign_ct)

3. **Check dependencies**:
   - %iso_date: no dependencies ✓
   - %derive_age: depends on %iso_date output ✓
   - %assign_ct: no dependencies ✓

4. **Order macros**:
   1. %iso_date (convert BRTHDT)
   2. %iso_date (convert RFSTDTC)
   3. %derive_age (needs both ISO dates)
   4. %assign_ct (convert SEX)
   5. %assign_ct (convert RACE)

5. **Generate SAS code** with proper parameters filled in

6. **Execute** → Get SDTM-compliant output with BRTHDTC, RFSTDTC, AGE, SEX, RACE

## The Three Macros Explained

### 1. %iso_date - Date Conversion
- **What:** Convert any date format to YYYY-MM-DD (ISO 8601)
- **Why:** SDTM requires ISO 8601 date format
- **Auto-detects:** DD-MON-YYYY, MM/DD/YYYY, DD/MM/YYYY, DDMONYYYY formats
- **Input:** Dataset with raw date variable
- **Output:** Same dataset with new ISO-formatted date variable

### 2. %derive_age - Age Calculation
- **What:** Calculate age in years from birth date and reference date
- **Why:** SDTM Demographics needs AGE variable
- **Algorithm:** Uses YRDIF function for accurate age calculation
- **Input:** Dataset with BRTHDTC and RFSTDTC (ISO format)
- **Output:** Same dataset with AGE and AGEU variables

### 3. %assign_ct - Controlled Terminology Mapping
- **What:** Map raw values (M, MALE, MALE) to CT values (M)
- **Why:** SDTM requires standardized CDISC CT values
- **Lookups:** Supports SEX, RACE, ETHNICITY, COUNTRY via ct_lookup.csv
- **Flexible:** Case-insensitive, handles unmapped values
- **Input:** Dataset with raw categorical variable
- **Output:** Same dataset with new CT-mapped variable

## Supported Controlled Terminology

The `ct_lookup.csv` file includes mappings for:

| Codelist | Variable | Values |
|----------|----------|--------|
| C66731 | SEX | M, F, U |
| C74457 | RACE | WHITE, BLACK OR AFRICAN AMERICAN, ASIAN, AMERICAN INDIAN OR ALASKA NATIVE, NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER, OTHER, MULTIPLE |
| C66790 | ETHNICITY | HISPANIC OR LATINO, NOT HISPANIC OR LATINO, NOT REPORTED, UNKNOWN |
| C71113 | COUNTRY | USA, CANADA, UNITED KINGDOM, MEXICO |

Each codelist has multiple raw value variations that map to the same CT value.

## Running the Example

Python example showing the full orchestration:

```bash
cd /sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/

python3 orchestrator_example.py
```

This will:
1. Load the registry
2. Analyze sample input variables
3. Select appropriate macros
4. Order by dependencies
5. Generate SAS code
6. Show the output

## Common Questions

### Q: Can I add more macros?
**A:** Yes! Add new entries to `macro_registry.json` with complete metadata, plus create the .sas file.

### Q: Can I add more CT mappings?
**A:** Yes! Add rows to `ct_lookup.csv` with CODELIST, RAW_VALUE, CT_VALUE columns.

### Q: What if a date format isn't recognized?
**A:** Specify the format explicitly with the `infmt` parameter in %iso_date.

### Q: What if a value doesn't map to CT?
**A:** Use the `unmapped` parameter: KEEP (keep raw value), MISSING (set to missing), or FLAG (log warning).

### Q: How does the orchestrator decide which macros to use?
**A:** By matching input variable names to the "when_to_use" criteria in the registry.

### Q: Is the order of macro calls important?
**A:** Yes! The orchestrator uses the "dependencies" field to ensure correct ordering.

## File Locations

All files are in:
```
/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/
```

Access them from SAS:
```sas
%include "/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/iso_date.sas";
%include "/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/derive_age.sas";
%include "/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/assign_ct.sas";
```

Access for Python:
```python
import json

with open('/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/macro_registry.json') as f:
    registry = json.load(f)
```

## Next Steps

1. **For AI Developers:** Read `IMPLEMENTATION_GUIDE.md` and review `orchestrator_example.py`
2. **For SAS Programmers:** Read `README.md` and see usage examples in `macro_registry.json`
3. **For Both:** Check `LIBRARY_STRUCTURE.txt` for quick reference

## Key Takeaway

**`macro_registry.json` is the bridge between human expertise (the macro implementations) and machine intelligence (AI orchestrators).** 

It provides all the metadata an AI system needs to:
- Discover available transformations
- Understand when to apply them
- Sequence them correctly
- Generate executable code automatically

This enables **autonomous AI-driven clinical programming** with full human oversight and traceability.

---

**Status:** Production Ready v1.0  
**Created:** 2026-02-16  
**Path:** `/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/`
