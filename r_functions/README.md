# R Function Library for SDTM Clinical Programming

This folder contains R functions that replace the SAS macro library for the
SDTM Agentic Orchestrator. The orchestrator (and AI agents) discover available
functions via **`function_registry.json`**.

## Functions

| Function      | File           | Purpose |
|---------------|----------------|---------|
| `iso_date`    | `iso_date.R`   | Convert non-standard dates to ISO 8601 (YYYY-MM-DD) |
| `derive_age`  | `derive_age.R` | Derive AGE and AGEU from birth and reference dates |
| `assign_ct`   | `assign_ct.R`  | Map raw values to CDISC Controlled Terminology |

## Required R Packages

Install once in R before running the pipeline:

```r
install.packages(c("arrow", "haven"))
```

| Package | Purpose |
|---------|---------|
| **arrow** | `arrow::write_parquet()` — writes Parquet files (primary output format) |
| **haven** | `haven::write_xpt()` — writes SAS transport files (.xpt) for regulatory submission |

The three transform functions (`iso_date`, `derive_age`, `assign_ct`) use **base R only**
and have no package dependencies.

## How to Use in R

Set the working directory to the project root (or adjust paths), then source
the functions and call them:

```r
# Source function files (from project root)
source("r_functions/iso_date.R")
source("r_functions/derive_age.R")
source("r_functions/assign_ct.R")

library(arrow)   # for write_parquet
library(haven)   # for write_xpt

ct_path <- "macros/ct_lookup.csv"
raw_dm  <- read.csv("study_data/raw_dm.csv", stringsAsFactors = FALSE)
dm      <- raw_dm

# 1. Convert dates to ISO 8601
dm <- iso_date(dm, invar = "BRTHDT",  outvar = "BRTHDTC")
dm <- iso_date(dm, invar = "RFSTDTC", outvar = "RFSTDTC")

# 2. Derive AGE / AGEU
dm <- derive_age(dm, brthdt = "BRTHDTC", refdt = "RFSTDTC")

# 3. Apply controlled terminology
dm <- assign_ct(dm, invar = "SEX",    outvar = "SEX",    codelist = "C66731", ctpath = ct_path)
dm <- assign_ct(dm, invar = "RACE",   outvar = "RACE",   codelist = "C74457", ctpath = ct_path)
dm <- assign_ct(dm, invar = "ETHNIC", outvar = "ETHNIC", codelist = "C66790", ctpath = ct_path)

# 4. Constants
dm$STUDYID <- "XYZ-2026-001"
dm$DOMAIN  <- "DM"
dm$USUBJID <- paste(dm$STUDYID, dm$SUBJID, sep = "-")

# 5. Write Parquet (primary) and XPT (regulatory)
arrow::write_parquet(dm, "orchestrator/outputs/datasets/dm.parquet")
haven::write_xpt(dm, path = "orchestrator/outputs/validation/dm.xpt", version = 5)
```

## Output Formats

| Format | File | Purpose |
|--------|------|---------|
| **Parquet** | `outputs/datasets/dm.parquet` | Primary workflow format: comparison, validation |
| **XPT**     | `outputs/validation/dm.xpt`   | SAS transport v5 for FDA regulatory submission |

Raw input remains CSV (`study_data/raw_dm.csv`). XPT is written by `haven::write_xpt()` with `version = 5` (SAS XPORT transport format, the standard for regulatory submissions).

## CT Lookup

Controlled terminology is read from **`macros/ct_lookup.csv`** (shared with the legacy SAS
macros). Columns: `CODELIST`, `RAW_VALUE`, `CT_VALUE`.

## For the Orchestrator

- **function_registry.json** — Machine-readable catalog: function names, parameters,
  `when_to_use`, dependencies, and R usage examples.
- The Python orchestrator reads this registry so agents can generate correct R code
  without parsing the `.R` files.
