---
description: Scaffold a new study directory from the template — creates config, conventions, raw_data, documents, SDTM/ADaM/TLG directory structure. Use when setting up a new study.
user-invocable: true
argument-hint: "<study_name> [domain]"
---

# New Study Setup

Scaffold a new study directory from the `studies/_template/` template.

## Usage
- `/new-study ABC_2027_002 DM` — Create study ABC_2027_002 for DM domain
- `/new-study XYZ_2028_003 AE` — Create study XYZ_2028_003 for AE domain
- `/new-study MY_STUDY` — Create study MY_STUDY (defaults to DM domain)

## Instructions

1. **Parse arguments:**
   - Argument 1 (required): Study name (used as directory name under `studies/`)
   - Argument 2 (optional): Domain (default: DM)

2. **Validate:**
   - Check that `studies/_template/` exists
   - Check that `studies/{study_name}/` does NOT already exist (refuse to overwrite)

3. **Copy template to new study directory:**
   - Copy `studies/_template/` to `studies/{study_name}/`
   - This copies the full directory structure including:
     - `config.yaml`, `conventions.yaml`
     - `raw_data/`, `external_data/`, `r_functions/`
     - `documents/protocol/`, `documents/sap/`, `documents/crf/`
     - `sdtm/` (specs, production, qc, validation)
     - `adam/` (specs, production, qc, validation)
     - `tlg/` (specs, production, qc)

4. **Replace placeholders in config.yaml:**
   - `__STUDY_ID__` -> the study name with hyphens (e.g., `ABC_2027_002` -> `ABC-2027-002`)
   - `__STUDY_DIR__` -> the study name as-is (directory name)
   - `__DOMAIN__` -> the domain argument (e.g., `DM`)
   - `__RAW_DATA_FILE__` -> `raw_{domain}.csv` (lowercase domain)
   - `__CRF_FILE__` -> `annotated_crf_{domain}.csv`
   - `__PROTOCOL_FILE__` -> `protocol_excerpt_{domain}.pdf`
   - `__SAP_FILE__` -> `sap_excerpt_{domain}.pdf`

5. **Report what was created:**
   ```
   New Study Created
   =================
   Study: ABC_2027_002
   Domain: DM
   Directory: studies/ABC_2027_002/

   Directory structure:
     studies/ABC_2027_002/
     ├── config.yaml              <- Study config (edit paths here)
     ├── conventions.yaml         <- Study-specific decision overrides
     ├── raw_data/                <- Place raw clinical data here
     ├── external_data/           <- External/reference data
     ├── r_functions/             <- Study-specific R functions (optional)
     ├── documents/
     │   ├── protocol/            <- Protocol versions
     │   ├── sap/                 <- SAP versions
     │   └── crf/                 <- CRF/aCRF versions
     ├── sdtm/
     │   ├── specs/               <- Mapping specifications
     │   ├── production/
     │   │   ├── programs/        <- Production R programs
     │   │   └── datasets/        <- Production datasets (Parquet + XPT)
     │   ├── qc/
     │   │   ├── programs/        <- QC R programs
     │   │   ├── datasets/        <- QC datasets
     │   │   └── compare/         <- Comparison reports
     │   └── validation/          <- P21, define.xml, spec sheets
     ├── adam/                    <- ADaM deliverables (future)
     └── tlg/                     <- TLG deliverables (future)

   Next steps:
     1. Place raw data in studies/ABC_2027_002/raw_data/
     2. Place study documents in studies/ABC_2027_002/documents/
     3. Edit studies/ABC_2027_002/config.yaml to set correct paths
     4. Edit studies/ABC_2027_002/conventions.yaml for study-specific decisions
     5. Run: python orchestrator/main.py --study ABC_2027_002 --domain DM
   ```

6. **If study-specific conventions differ from standard:**
   - Remind the user they can edit `studies/{study_name}/conventions.yaml`
   - Show the available standard conventions from `standards/conventions.yaml`
