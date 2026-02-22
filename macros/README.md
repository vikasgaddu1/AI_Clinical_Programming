# SAS Macro Library for SDTM Clinical Programming

## Overview

This macro library provides a curated set of SAS macros for SDTM (Study Data Tabulation Model) clinical programming tasks. The library is designed to be **AI-Orchestrator-Ready**, with a machine-readable registry that enables automated macro discovery, selection, and execution.

## Directory Structure

```
/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/
├── iso_date.sas              # Date format conversion macro
├── derive_age.sas            # Age calculation macro
├── assign_ct.sas             # Controlled terminology mapping macro
├── ct_lookup.csv             # CT mapping reference file
├── macro_registry.json       # Machine-readable macro registry (AI Orchestrator uses this)
└── README.md                 # This file
```

## The Macro Registry: Hub of the AI Orchestrator

### What is macro_registry.json?

The **macro_registry.json** file is the central hub that enables AI orchestrators to:

1. **Discover** - Find all available macros in the library
2. **Understand** - Read detailed metadata about each macro
3. **Select** - Choose appropriate macros for a task
4. **Sequence** - Order macro calls respecting dependencies
5. **Parametrize** - Understand required and optional parameters
6. **Generate** - Automatically create SAS code
7. **Execute** - Run the generated SAS code

### Registry Structure

```json
{
  "registry_version": "1.0",
  "macros": [
    {
      "name": "%iso_date",
      "file": "iso_date.sas",
      "category": "Date Handling",
      "purpose": "...",
      "when_to_use": [...],
      "parameters": [...],
      "dependencies": [],
      "usage_examples": [...]
    },
    ...
  ],
  "orchestrator_integration": {
    "decision_logic": {...},
    "example_orchestration_scenario": {...}
  }
}
```

## Available Macros

### 1. %iso_date - Date Format Conversion

**Purpose:** Convert various date formats to ISO 8601 (YYYY-MM-DD) format required by SDTM

**When to use:**
- Converting raw birth dates to BRTHDTC
- Converting raw event dates to standardized date variables
- Handling mixed date formats from different data sources
- Preparing dates for downstream derivations

**Supported input formats:**
- DD-MON-YYYY (e.g., 01-JAN-2020)
- MM/DD/YYYY (e.g., 01/12/2020)
- DD/MM/YYYY (e.g., 01/12/2020)
- DDMONYYYY (e.g., 01JAN2020)
- YYYY-MM-DD (e.g., 2020-01-01)

**Example:**
```sas
%iso_date(inds=raw.dm, outds=work.dm_iso, invar=BRTHDT, outvar=BRTHDTC);
```

**Key Features:**
- Auto-detects date formats (no need to specify input format)
- Handles leading/trailing spaces automatically
- Sets invalid dates to missing with warnings
- SDTM-compliant output

---

### 2. %derive_age - Age Calculation

**Purpose:** Calculate age in completed years from birth date and reference date

**When to use:**
- Deriving AGE variable in SDTM Demographics (DM) domain
- Calculating age at study start (using RFSTDTC)
- Age derivations for analysis datasets

**Example:**
```sas
%derive_age(inds=work.dm, outds=work.dm_age, brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);
```

**Key Features:**
- Calculates completed years using YRDIF function
- Handles both character (ISO format) and numeric SAS dates
- Creates AGEU (age unit) variable set to 'YEARS'
- Validates that birth date ≤ reference date

---

### 3. %assign_ct - Controlled Terminology Mapping

**Purpose:** Map raw categorical values to CDISC Controlled Terminology standards

**When to use:**
- Mapping SEX values (M, F, U)
- Mapping RACE values
- Mapping ETHNICITY values
- Mapping COUNTRY values
- Standardizing any SDTM CT-controlled variable

**Supported codelists:**
- **C66731** - SEX: M, F, U
- **C74457** - RACE: WHITE, BLACK OR AFRICAN AMERICAN, ASIAN, etc.
- **C66790** - ETHNICITY: HISPANIC OR LATINO, NOT HISPANIC OR LATINO, etc.
- **C71113** - COUNTRY: USA, CANADA, UNITED KINGDOM, MEXICO

**Example:**
```sas
%assign_ct(inds=work.dm, outds=work.dm_ct, invar=SEX_RAW, outvar=SEX, 
           codelist=C66731, ctpath=/path/to/ct_lookup.csv);
```

**Key Features:**
- Maps multiple raw value variations to single CT value
- Case-insensitive matching by default
- Handles unmapped values with configurable actions (KEEP, MISSING, FLAG)
- Comprehensive lookup table (ct_lookup.csv) included

---

## How the AI Orchestrator Uses This Library

### The Orchestration Process

```
┌─────────────────────────────────────────────────────────────┐
│ 1. AI Orchestrator Reads macro_registry.json                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Analyze Input Dataset Structure                          │
│    - Identify available variables                           │
│    - Determine data types and formats                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Match Input Variables to Macro "when_to_use" Criteria   │
│    - Example: Found RAW_BRTHDT → Consider %iso_date        │
│    - Example: Found RAW_SEX → Consider %assign_ct          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Sequence Macros Respecting Dependencies                 │
│    - %iso_date → %derive_age (derive_age depends on       │
│                  iso_date output)                          │
│    - %assign_ct (no dependencies)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Parametrize Each Macro Call                             │
│    - Extract parameter metadata from registry               │
│    - Map actual variable names to parameter names           │
│    - Apply defaults for optional parameters                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Generate SAS Code                                        │
│    %iso_date(inds=raw.dm, outds=work.dm_dates,            │
│              invar=BRTHDT, outvar=BRTHDTC);               │
│    %derive_age(inds=work.dm_dates, outds=work.dm_derived, │
│                brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Execute Generated Code & Collect Results                │
└─────────────────────────────────────────────────────────────┘
```

### Example: Converting Raw DM Domain to SDTM

**Input:** Raw dataset with columns
- `RAW_SEX` = "M", "F", "MALE", etc.
- `RAW_RACE` = "White", "BLACK", "ASIAN", etc.
- `RAW_BRTHDT` = "01-JAN-1990", "1990-01-01", etc.
- `RAW_RFSTDTC` = "01/01/2020", "01-JAN-2020", etc.

**Orchestrator Decision Logic:**

1. **Read Registry** → Find %iso_date, %derive_age, %assign_ct macros
2. **Analyze Input** → Found RAW_BRTHDT and RAW_RFSTDTC → Need date conversion
3. **Analyze Input** → Found RAW_SEX and RAW_RACE → Need CT mapping
4. **Order Steps:**
   - Step 1: %iso_date on RAW_BRTHDT → BRTHDTC
   - Step 2: %iso_date on RAW_RFSTDTC → RFSTDTC
   - Step 3: %derive_age using BRTHDTC and RFSTDTC → AGE
   - Step 4: %assign_ct on RAW_SEX → SEX
   - Step 5: %assign_ct on RAW_RACE → RACE

5. **Generate SAS Code:**
```sas
%iso_date(inds=raw.dm, outds=work.dm_step1, invar=RAW_BRTHDT, outvar=BRTHDTC);
%iso_date(inds=work.dm_step1, outds=work.dm_step2, invar=RAW_RFSTDTC, outvar=RFSTDTC);
%derive_age(inds=work.dm_step2, outds=work.dm_step3, brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);
%assign_ct(inds=work.dm_step3, outds=work.dm_step4, invar=RAW_SEX, outvar=SEX, codelist=C66731);
%assign_ct(inds=work.dm_step4, outds=work.dm_final, invar=RAW_RACE, outvar=RACE, codelist=C74457);
```

6. **Execute** → Produces SDTM-compliant DM dataset

## The Registry JSON: Machine-Readable Metadata

Every macro entry in `macro_registry.json` includes:

### Basic Information
```json
{
  "name": "%macro_name",
  "file": "macro_file.sas",
  "category": "Domain Category",
  "purpose": "What the macro does",
  "when_to_use": ["When to apply...", "Use case 1...", "Use case 2..."]
}
```

### Parameters
```json
"parameters": [
  {
    "name": "param_name",
    "type": "data type",
    "required": true|false,
    "default": "default_value_or_null",
    "description": "What this parameter does",
    "example": "example_usage"
  }
]
```

### Capabilities
```json
{
  "output_type": "What type of output is produced",
  "dependencies": ["List of macros this depends on"],
  "usage_examples": [
    {
      "description": "Example scenario",
      "code": "%macro_call(...);"
    }
  ]
}
```

### Orchestrator Integration
```json
"orchestrator_integration": {
  "registry_format": "JSON",
  "how_to_use": [
    "Step 1: Read registry...",
    "Step 2: Select macros...",
    "..."
  ],
  "decision_logic": {
    "step_1_discovery": "...",
    "step_2_selection": "...",
    "..."
  }
}
```

## Using This Library with Your Orchestrator

### For AI Orchestrators

1. **Load the Registry:**
   ```python
   import json
   
   with open('macro_registry.json') as f:
       registry = json.load(f)
   ```

2. **Discover Available Macros:**
   ```python
   for macro in registry['macros']:
       print(f"Macro: {macro['name']}")
       print(f"Purpose: {macro['purpose']}")
   ```

3. **Get Parameter Metadata:**
   ```python
   macro_iso_date = registry['macros'][0]  # %iso_date
   for param in macro_iso_date['parameters']:
       print(f"{param['name']}: {param['description']}")
   ```

4. **Check Dependencies:**
   ```python
   for macro in registry['macros']:
       if macro['dependencies']:
           print(f"{macro['name']} depends on: {macro['dependencies']}")
   ```

5. **Generate SAS Code:**
   ```python
   macro_call = f"%{macro_name}(inds={input_ds}, outds={output_ds}, ...);"
   ```

### For SAS Programmers

**Manually calling macros:**
```sas
/* Include the macro library */
%include "/path/to/iso_date.sas";
%include "/path/to/derive_age.sas";
%include "/path/to/assign_ct.sas";

/* Call macros in sequence */
%iso_date(inds=raw.dm, outds=work.dm_dates, invar=BRTHDT, outvar=BRTHDTC);
%derive_age(inds=work.dm_dates, outds=work.dm_final, brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);
```

## Error Handling

All macros include comprehensive error handling:

- **Missing Required Parameters** → ERROR message stops macro execution
- **Missing Input Dataset** → ERROR message
- **Invalid Format** → WARNING message, continues with missing values
- **Invalid Dates** → WARNING message, sets to missing
- **Unmapped Values** → WARNING message (configurable action)

Example SAS log output:
```
ERROR: inds parameter is required
WARNING: Could not parse date value "invalid_date" for observation from BRTHDT
WARNING: Unmapped value in codelist C66731: "X"
NOTE: Macro %iso_date completed. Output dataset: WORK.DM_ISO
```

## Registry Extensibility

To add new macros to the library:

1. **Create the SAS macro file** with proper documentation
2. **Add an entry to macro_registry.json** with complete metadata
3. **Include the new macro in orchestration scenarios** if applicable
4. **Update version_history** in the registry

Example new macro entry structure:
```json
{
  "name": "%new_macro",
  "file": "new_macro.sas",
  "category": "New Category",
  "purpose": "What it does",
  "when_to_use": ["..."],
  "parameters": [{"name": "...", "type": "...", ...}],
  "dependencies": [],
  "usage_examples": [{"description": "...", "code": "..."}]
}
```

## Reference Files

### ct_lookup.csv

The controlled terminology lookup file contains mappings for common SDTM CT codelists:

**Columns:**
- `CODELIST` - NCI codelist code (e.g., C66731)
- `CODELIST_NAME` - Readable name (e.g., SEX)
- `RAW_VALUE` - Raw value as found in source data
- `CT_VALUE` - CDISC-standardized CT value
- `DESCRIPTION` - Explanation of the mapping

**Example entries:**
```csv
C66731,SEX,M,M,Male
C66731,SEX,MALE,M,Male - expanded form
C66731,SEX,F,F,Female
C74457,RACE,WHITE,WHITE,White
C74457,RACE,BLACK,BLACK OR AFRICAN AMERICAN,Black or African American
```

Extend this file with additional mappings for your organization's specific needs.

## Best Practices

1. **Always use macros for standardization** - Don't write custom date/CT code
2. **Sequence macros correctly** - Run %iso_date before %derive_age
3. **Validate intermediate outputs** - Check that dates converted correctly
4. **Document raw values** - Know what raw values map to before using %assign_ct
5. **Handle unmapped values** - Decide whether to KEEP, set to MISSING, or FLAG
6. **Version your CT lookup** - Update ct_lookup.csv as new mappings are discovered
7. **Use the registry** - Let AI orchestrators or documentation drive macro selection

## Support

For questions about:
- **Macro usage** → See "Usage Examples" in macro_registry.json
- **CT mappings** → Check ct_lookup.csv and "supported_codelists" in registry
- **Orchestrator integration** → See "orchestrator_integration" section in registry
- **Error messages** → See "error_handling" in each macro's registry entry

## Version Information

- **Registry Version:** 1.0
- **Release Date:** 2026-02-16
- **Status:** Production Ready
- **Last Updated:** 2026-02-16

---

**Created for: AI-Orchestrated SDTM Clinical Programming**

This library bridges human clinical programming expertise with AI automation through machine-readable metadata.
