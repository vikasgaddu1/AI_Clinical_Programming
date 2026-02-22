# SDTM Agentic Orchestrator — Implementation Plan

## What This Project Is

A multi-agent orchestration system that automates the SDTM (Study Data Tabulation Model) programming workflow for clinical trials. The system uses AI agents to go from raw clinical data to validated, submission-ready SDTM datasets — mirroring the exact workflow clinical programmers follow manually, but with AI assistance at every step.

This is a **training demonstration** for clinical programmers learning to use AI. The implementation uses **R** (no SAS or Viya required); most programmers know R, and for those who haven't used it recently this serves as a refresher. The working example is focused on the **DM (Demographics) domain** using a fictitious Phase III Type 2 Diabetes study (XYZ-2026-001).

## Project Directory Structure

```
AI_Clinical_Programming/
├── CLAUDE.md                          ← You are here
├── AI_Training_Program.pptx           ← Training presentation (22 slides)
├── AI_Training_Program_Plan.docx      ← Original plan document
│
├── study_data/                        ← Fictitious study materials
│   ├── raw_dm.csv                     ← Primary raw input (300 subjects, 6 sites, messy data)
│   ├── raw_dm.sas7bdat                ← Optional; same data (e.g. for haven in R)
│   ├── annotated_crf_dm.csv           ← CRF field → SDTM variable annotations
│   ├── raw_dm_mapping_spec.csv        ← Source-to-target variable mapping
│   ├── protocol_excerpt_dm.pdf        ← Fictitious protocol (Phase III, T2DM)
│   └── sap_excerpt_dm.pdf             ← Fictitious SAP with demographics analysis plan
│
├── r_functions/                       ← R function library (replaces SAS macros)
│   ├── function_registry.json         ← *** CRITICAL: Machine-readable function catalog ***
│   ├── iso_date.R                     ← iso_date() — converts messy dates → ISO 8601
│   ├── derive_age.R                    ← derive_age() — AGE/AGEU from birth + reference dates
│   ├── assign_ct.R                    ← assign_ct() — maps raw values → CDISC CT
│   ├── README.md                      ← How to source and use functions
│   └── packages.txt                   ← Required R packages (arrow, haven)
│
├── macros/                            ← Legacy/reference (SAS macros + shared CT lookup)
│   ├── macro_registry.json            ← Original SAS macro catalog (reference)
│   ├── iso_date.sas                   ← Legacy SAS version
│   ├── derive_age.sas                 ← Legacy SAS version
│   ├── assign_ct.sas                  ← Legacy SAS version
│   └── ct_lookup.csv                  ← CT mapping table (used by R assign_ct)
│
├── sdtm_ig_db/                        ← SDTM IG knowledge base (RAG + file fallback)
│   ├── config.py                      ← Database + embedding + chunking config
│   ├── setup_db.py                    ← PostgreSQL + pgvector schema creation
│   ├── load_sdtm_ig.py                ← Chunk and load IG content
│   ├── query_ig.py                    ← Semantic search interface (database mode)
│   └── sdtm_ig_content/               ← Markdown IG content (file-based fallback)
│       ├── dm_domain.md               ← DM domain variable definitions + assumptions
│       └── general_assumptions.md     ← General SDTM rules (ISO dates, USUBJID, etc.)
│
├── .gitignore                         ← Git ignore rules (cache, secrets, outputs)
├── .claude/                           ← Claude Code configuration
│   ├── skills/                        ← Claude Code skills (6 slash commands)
│   │   ├── run-pipeline/SKILL.md      ← /run-pipeline — execute pipeline stages
│   │   ├── profile-data/SKILL.md      ← /profile-data — profile raw clinical data
│   │   ├── review-spec/SKILL.md       ← /review-spec — interactive spec review
│   │   ├── validate-dataset/SKILL.md  ← /validate-dataset — P21-style validation
│   │   ├── check-environment/SKILL.md ← /check-environment — verify prerequisites
│   │   └── generate-training/SKILL.md ← /generate-training — generate training chapters
│   ├── mcp.json                       ← MCP server configuration
│   └── settings.local.json            ← Hooks and permission settings
│
├── mcp_server.py                      ← MCP server (5 tools for IG/CT/spec lookup)
├── verify_setup.py                    ← Automated verification script (12 checks)
│
└── orchestrator/                      ← Orchestrator implementation
    ├── main.py                        ← Main orchestration entry point
    ├── agents/                        ← Individual agent implementations
    │   ├── spec_builder.py            ← Draft spec from raw data + IG + registry
    │   ├── spec_reviewer.py           ← IG-driven spec review (required vars from IG)
    │   ├── production_programmer.py   ← R script generation + SUPPDM
    │   ├── qc_programmer.py           ← Independent QC R script (does NOT import production)
    │   ├── validation_agent.py        ← P21 checks, define.xml, spec sheet generation
    │   └── training_generator.py      ← Training chapter generation (all skill levels)
    ├── core/
    │   ├── state.py                   ← Pipeline state with JSON persistence (save/load)
    │   ├── spec_manager.py            ← Domain-aware spec read/write/sync
    │   ├── function_loader.py         ← Reads function_registry.json for agents
    │   ├── ig_client.py               ← IG queries (file-based fallback, no DB required)
    │   ├── llm_client.py              ← LLM integration (LIVE / DRY_RUN / OFF modes)
    │   ├── compare.py                 ← Dataset comparison (Parquet/CSV/RDS)
    │   ├── human_review.py            ← Human-in-the-loop interface
    │   └── training_context.py        ← Domain + project context for training generation
    ├── outputs/                       ← Generated artifacts
    │   ├── specs/                     ← Mapping specifications (JSON + XLSX)
    │   ├── programs/                  ← Generated R programs (.R)
    │   ├── datasets/                  ← Output Parquet (dm.parquet) — primary format
    │   ├── qc/                        ← QC programs (dm_qc.R, dm_qc.parquet) and comparison results
    │   └── validation/                ← XPT for submission (dm.xpt), P21 results, define.xml
    └── config.yaml                    ← Orchestrator configuration
```

---

## The Real-World Workflow Being Automated

This is the manual process clinical programmers follow. Each numbered step maps to an agent or orchestrator action:

1. **Receive study materials** — Protocol, SAP, annotated CRF, raw data
2. **Profile the raw data** — Understand what variables exist, their values, formats, quality issues
3. **Consult the SDTM IG** — Look up how each raw variable maps to SDTM domains/variables, what controlled terminology applies
4. **Create a mapping specification** — Document every source→target mapping, derivation rule, and CT application. This spec is the single source of truth for everything downstream
5. **Human review** — Programmer reviews the spec, makes decisions where multiple approaches exist
6. **Production programming** — Implement the spec in R code, using available functions where applicable. Save as Parquet (primary) and XPT (regulatory submission)
7. **QC programming** — A second programmer independently implements the same spec in R. They do NOT see the production code
8. **Compare** — Run a comparison between production and QC Parquet datasets (Python/pandas)
9. **Iterate** — If mismatches exist, both programmers review their code, identify the error source, fix, and re-compare until 100% match
10. **Validation** — Fill Pinnacle 21 spec sheet, run P21 checks, generate define.xml
11. **Spec finalization** — Ensure the spec, the data, and the define.xml are all consistent (same codelists, same value-level metadata, same derivation descriptions)

### Critical Principle: The Spec Is the Single Source of Truth

The mapping specification drives EVERYTHING:
- The R code that creates the datasets (Parquet + XPT)
- The define.xml that describes the datasets for regulatory submission
- The P21 validation that checks the datasets

If the spec says SEX uses codelist C66731 with values M/F, then the R code MUST map to M/F using that codelist, AND the define.xml MUST reference codelist C66731, AND the data MUST contain only M/F values. Any inconsistency is a submission risk.

---

## Agent Architecture

### Agent 1: Spec Builder (Claude Sonnet)

**Purpose:** Analyze raw data + study docs → produce draft mapping specification

**Inputs:**
- `study_data/raw_dm.csv` (primary; or `raw_dm.sas7bdat` via haven in R) — the raw data
- `study_data/annotated_crf_dm.csv` — CRF annotations
- `study_data/protocol_excerpt_dm.pdf` — protocol for study context
- `study_data/sap_excerpt_dm.pdf` — SAP for analysis requirements
- SDTM IG knowledge base (via `sdtm_ig_db/query_ig.py`)
- Function registry (`r_functions/function_registry.json`) — to know what R functions are available

**Process:**
1. Read and profile the raw data:
   - List all variables, their types, lengths
   - For each variable: distinct values, frequencies, missing counts
   - Identify data quality issues (mixed coding, non-standard dates, missing values)
2. For each raw variable, query the SDTM IG database:
   - Which SDTM domain and variable does it map to?
   - What controlled terminology applies?
   - Are there specific derivation rules or assumptions?
3. Read the function registry to understand what R functions are available:
   - Which functions can handle which transformations?
   - What parameters do they need?
   - In what order should they be called (dependency chain)?
4. Produce a draft mapping specification with these columns:
   - Source Dataset, Source Variable, Source Values (sample)
   - Target Domain, Target Variable, Target Data Type, Target Length
   - Mapping Logic (plain English + R pseudocode)
   - Controlled Terminology (codelist code + name)
   - Function to Use (from registry, if applicable)
   - Derivation Method
   - Assumptions / Open Questions

**Decision Points that Require Human Input:**
When the IG offers multiple valid approaches, the Spec Builder MUST NOT pick one silently. Instead, it must flag the decision and present options. Key examples for DM:

- **RACE "Other Specify" mapping:**
  - Approach A: Map specific free-text values to closest CT term (e.g., "Filipino" → ASIAN)
  - Approach B: Keep as OTHER and populate SUPPDM.RACEOTH
  - Approach C: Use MULTIPLE for mixed-race entries
  - The agent presents all three with IG references and pros/cons, then asks the human

- **RFSTDTC derivation:**
  - Approach A: Use informed consent date (RFICDTC)
  - Approach B: Use first dose date (RFXSTDTC)
  - Approach C: Use randomization date
  - The IG says RFSTDTC is "the date of the first study-related activity" — which is ambiguous

- **Date imputation for partial dates:**
  - Approach A: Set to first of month for missing day
  - Approach B: Set to 15th (midpoint) for missing day
  - Approach C: Leave as partial (YYYY-MM)
  - Different companies have different conventions

- **ARM vs ACTARM when protocol deviations exist:**
  - Does ACTARM differ from ARM for subjects who received wrong treatment?

**Output:** `outputs/specs/dm_mapping_spec.json` (structured) + `outputs/specs/dm_mapping_spec.xlsx` (human-readable)

The spec JSON structure should include:
```json
{
  "study_id": "XYZ-2026-001",
  "domain": "DM",
  "spec_version": "1.0",
  "created_by": "Spec Builder Agent",
  "variables": [
    {
      "target_variable": "SEX",
      "target_domain": "DM",
      "source_variable": "SEX",
      "source_dataset": "raw_dm",
      "data_type": "Char",
      "length": 2,
      "codelist_code": "C66731",
      "codelist_name": "Sex",
      "mapping_logic": "Apply assign_ct() with codelist C66731",
      "macro_used": "assign_ct",
      "function_parameters": {
        "codelist": "C66731",
        "unmapped": "FLAG"
      },
      "controlled_terms": ["M", "F", "U"],
      "assumptions": [],
      "human_decision_required": false
    },
    {
      "target_variable": "RACE",
      "target_domain": "DM",
      "source_variable": "RACE",
      "source_dataset": "raw_dm",
      "data_type": "Char",
      "length": 60,
      "codelist_code": "C74457",
      "codelist_name": "Race",
      "mapping_logic": "See decision required — multiple approaches for OTHER specify values",
      "macro_used": "assign_ct",
      "assumptions": [],
      "human_decision_required": true,
      "decision_options": [
        {
          "id": "A",
          "description": "Map free-text to closest CT term where possible (Filipino→ASIAN, Pacific Islander→NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER). Remaining unmapped values → OTHER with SUPPDM.",
          "ig_reference": "SDTM IG 3.4, Section 6.1 — Demographics, Race variable assumptions",
          "pros": ["Maximizes use of standard CT", "Fewer SUPPDM records"],
          "cons": ["Requires judgment calls on ambiguous mappings", "May lose specificity"]
        },
        {
          "id": "B",
          "description": "All Other Specify values → RACE='OTHER', free text preserved in SUPPDM.QVAL with QNAM='RACEOTH'",
          "ig_reference": "SDTM IG 3.4, Appendix C2",
          "pros": ["Conservative, preserves all original data", "No judgment calls needed"],
          "cons": ["Many SUPPDM records", "Less informative for analysis"]
        },
        {
          "id": "C",
          "description": "Mixed/biracial entries → RACE='MULTIPLE', individual races in SUPPDM with QNAM='RACEn'. Single other entries → approach A or B.",
          "ig_reference": "SDTM IG 3.4, Section 6.1 — When subject reports more than one race",
          "pros": ["Most complete representation of multi-race subjects"],
          "cons": ["Complex SUPPDM structure", "Requires parsing free text to identify individual races"]
        }
      ]
    }
  ]
}
```

---

### Agent 2: Spec Reviewer (Claude Opus)

**Purpose:** Critically review the draft spec for completeness and CDISC compliance

**Inputs:**
- Draft spec from Spec Builder
- SDTM IG knowledge base (via `ig_client` — required variables fetched from IG, not hardcoded)
- Annotated CRF (to verify all CRF fields are covered — permissible/supplemental variables come from CRF)

**Process:**
1. **IG-driven completeness check:** Required variables are fetched from the IG via `ig_client.get_required_variables(domain)` — not hardcoded. This makes the reviewer work for any SDTM domain, not just DM.
2. **CRF coverage check:** If an annotated CRF is provided, verify that all CRF-annotated variables appear in the spec. Permissible and supplemental variables are identified from the CRF, not from a hardcoded list.
3. CT compliance check: Does every CT-controlled variable reference a valid codelist?
4. Derivation logic review: Are derivations logically sound?
   - Is AGE derived from BRTHDTC and RFSTDTC (not from raw AGE field, which may be calculated differently)?
   - Is DMDY correctly derived as (DMDTC - RFSTDTC) + 1 when DMDTC >= RFSTDTC?
   - Are derivation dependencies satisfied (e.g., iso_date before derive_age)?
5. Function validation: Are the right R functions selected? Are parameters correct? Is the execution order right?
6. Flag any issues for the Spec Builder to fix before human review

**Output:** Annotated spec with review comments + pass/fail status

---

### Human Review Gate

**Purpose:** Present the spec to the programmer for approval, collecting decisions on flagged items

**This is NOT optional.** The system assists but does not replace human judgment.

**Interface:**
- Display the full mapping spec in a readable format
- For each variable with `human_decision_required: true`:
  - Show the decision options with IG references, pros, and cons
  - Ask the user to select an approach (A, B, C, or custom)
  - Record the decision and rationale
- Allow the reviewer to edit any mapping logic
- Allow the reviewer to add study-specific assumptions
- Collect a sign-off (approved / approved with changes / rejected)

**Output:** Approved spec with all decisions resolved → `outputs/specs/dm_mapping_spec_approved.json`

---

### Agent 3: Production Programmer (Claude Sonnet)

**Purpose:** Implement the approved spec into a complete R script

**Inputs:**
- Approved mapping spec (`dm_mapping_spec_approved.json`)
- Function registry (`r_functions/function_registry.json`)
- R function library (`r_functions/*.R`)
- Raw data location (`study_data/raw_dm.csv`)

**Process:**
1. Read the approved spec
2. Read the function registry to understand available R functions and their calling syntax
3. Generate a complete R script that:
   - Sources the R function files (e.g. `source("r_functions/iso_date.R")`, etc.)
   - Reads the raw data (e.g. `read.csv("study_data/raw_dm.csv")` or `haven::read_sas()` if using .sas7bdat)
   - Calls functions in the correct dependency order:
     a. `iso_date()` for BRTHDT → BRTHDTC
     b. `iso_date()` for RFSTDTC → RFSTDTC (ISO)
     c. `derive_age()` for AGE/AGEU from BRTHDTC + RFSTDTC
     d. `assign_ct()` for SEX (codelist C66731)
     e. `assign_ct()` for RACE (codelist C74457) with the human-selected approach
     f. `assign_ct()` for ETHNIC (codelist C66790)
   - Handles variables not covered by functions with inline R logic:
     a. STUDYID, DOMAIN (constants)
     b. USUBJID derivation (paste(STUDYID, SUBJID, sep = "-"))
     c. SITEID, INVNAM (pass-through or recoding)
     d. ARMCD, ARM, ACTARMCD, ACTARM mapping
     e. COUNTRY mapping (or assign_ct with C71113)
     f. DMDTC, DMDY derivation
     g. RFENDTC derivation (if applicable)
   - Keeps variables in SDTM-required order with correct types/lengths
   - Writes the final dataset to Parquet (primary): `arrow::write_parquet(dm, "outputs/datasets/dm.parquet")` and XPT (regulatory): `haven::write_xpt(dm, path = "outputs/validation/dm.xpt", version = 5)`
   - Uses a project-root-appropriate working directory or paths so the script runs via `Rscript dm_production.R`

4. The generated script must include comments referencing the spec for traceability:
   ```r
   # Variable: SEX
   # Spec Reference: dm_mapping_spec_approved, variable SEX
   # Codelist: C66731 (Sex)
   # Mapping: assign_ct() with codelist C66731
   # Decision: N/A (standard mapping)
   ```

**Critical rule:** The Production Programmer uses functions from the registry whenever a function exists for the task. It does NOT write custom date conversion when `iso_date` exists. It does NOT write custom CT mapping when `assign_ct` exists. The function registry is the source of truth for what reusable code is available.

**Output:** `outputs/programs/dm_production.R` + `outputs/datasets/dm.parquet` (primary) + `outputs/validation/dm.xpt` (regulatory submission)

---

### Agent 4: QC Programmer (Claude Opus)

**Purpose:** Independently implement the same spec. MUST NOT see or reference the production code.

**Inputs:**
- Approved mapping spec (same as Production Programmer)
- Function registry (same R functions available)
- Raw data (same source data)
- **DOES NOT RECEIVE:** Production code, production output, or any artifact from Agent 3

**Why Opus (different model from Production's Sonnet):**
This mirrors real-world double programming where two different people independently code the same spec. Using a different LLM ensures genuinely different implementation choices — different variable ordering, different intermediate object names — while arriving at the same final result.

**Process:**
1. Read the approved spec independently
2. Generate a complete R script using its own implementation approach
3. The QC script:
   - May use the same functions (they're available in the registry)
   - But should write the logic independently
   - Must produce a dataset with identical variable names, types, lengths, and values
4. Run a comparison between its output and the production dataset (see below)
5. Generate a comparison report

**Comparison:** The orchestrator reads both Parquet outputs with pandas (`pd.read_parquet`) and does a column-by-column diff, writing `dm_compare_report.txt`. Using Python for comparison avoids an extra R process and keeps comparison logic in the orchestrator.

**On mismatch:**
- If the comparison shows differences, the QC Programmer:
  1. Identifies which variables have discrepancies
  2. For each discrepancy, traces back to the spec to determine which implementation is correct
  3. Fixes its own code if the error is on the QC side
  4. Reports back to the orchestrator if the error appears to be on the production side
- The orchestrator routes production-side errors back to Agent 3
- Both agents re-run and re-compare
- This loop continues until the comparison shows 0 differences

**Output:** `outputs/qc/dm_qc.R` + `outputs/qc/dm_qc.parquet` + `outputs/qc/dm_compare_report.txt`

---

### Agent 5: Validation Agent (Claude Sonnet)

**Purpose:** Run final validation checks and generate submission metadata

**Inputs:**
- Final approved datasets (`outputs/datasets/dm.parquet`)
- Approved spec (`dm_mapping_spec_approved.json`)
- Study metadata (from protocol/SAP)

**Process:**
1. Generate the Pinnacle 21 specification sheet from the approved spec:
   - Variable-level metadata: name, label, data type, length, codelist, origin, comment
   - Value-level metadata: where clauses, codelist entries, decode values
   - This MUST match what's in the spec AND what's in the data
2. Run P21-style validation checks:
   - Required variables present?
   - Controlled terminology values match codelist?
   - ISO 8601 date formats correct?
   - Variable attributes (type, length) correct?
   - USUBJID format consistent?
   - No unexpected missing values in required fields?
3. Generate define.xml metadata structure
4. Route any validation failures back to the appropriate agent:
   - Data content issues → Production Programmer (Agent 3)
   - Spec inconsistencies → Spec Builder (Agent 1) + Human Review
   - Metadata issues → fix in-place

**Output:** `outputs/validation/p21_spec_sheet.xlsx` + `outputs/validation/p21_report.txt` + `outputs/validation/define_metadata.json`

---

## Orchestrator Core Components

### State Manager (`core/state.py`)

Maintains the pipeline state across all agents with JSON persistence for crash recovery:

```python
class PipelineState:
    study_id: str
    domain: str
    current_phase: str  # "spec_building" | "spec_review" | "human_review" | "production" | "qc" | "comparison" | "validation"
    spec_status: str    # "draft" | "reviewed" | "approved" | "finalized"
    production_status: str
    qc_status: str
    comparison_result: str  # "pending" | "match" | "mismatch"
    comparison_iteration: int  # Track how many compare cycles
    validation_status: str
    human_decisions: dict  # Recorded decisions from human review
    error_log: list
    artifacts: dict  # Paths to all generated files

    def save(self, path: str) -> None: ...     # Persist to JSON
    @classmethod
    def load(cls, path: str) -> "PipelineState": ...  # Resume from JSON
```

State is saved after every pipeline stage to `outputs/pipeline_state.json`. Use `--resume` to continue from the last saved state after a crash or interruption.

### LLM Client (`core/llm_client.py`)

Wraps the Anthropic Claude API for all agent calls. Supports three modes:

| Mode | Config | Behavior |
|------|--------|----------|
| **LIVE** | `use_llm: true, dry_run: false` | Calls the Anthropic API |
| **DRY_RUN** | `dry_run: true` | Logs prompts to JSON files without calling API |
| **OFF** | `use_llm: false` | Uses template/rule-based logic only |

- Reads `ANTHROPIC_API_KEY` from environment or `.env` file at project root
- Logs all interactions (system prompt, user prompt, response) for audit trail
- Each agent can call `llm_client.call_agent(agent_name, system_prompt, user_prompt, model)`

### Compare Module (`core/compare.py`)

Reads both production and QC datasets (Parquet, CSV, or RDS) using pandas and performs:
- Column-by-column diff with detailed mismatch reporting
- Handles data type normalization (numeric precision, string trimming)
- Returns `(match: bool, report: str)` tuple
- Report includes per-variable mismatch counts and sample discrepancies

### Function Loader (`core/function_loader.py`)

Reads `r_functions/function_registry.json` and provides the agents with:
- List of available R functions and when to use each one
- Parameter signatures (required, optional, defaults)
- Dependency ordering (e.g., `iso_date` must run before `derive_age`)
- R usage examples for code generation context

This is how the orchestrator "communicates" what R functions exist to each agent. The agents don't scan the filesystem — they read the registry.

### IG Client (`core/ig_client.py`)

Provides agents with SDTM IG content via two backends:

1. **File-based fallback (default):** Parses markdown files in `sdtm_ig_db/sdtm_ig_content/` — no database required. Extracts variable metadata from markdown tables (Name, Label, Type, Controlled Terminology, Required/Conditional).
2. **Database mode:** Wraps `sdtm_ig_db/query_ig.py` for semantic search via PostgreSQL + pgvector (optional).

Public API:
- `get_domain_variables(domain)` — all variables with metadata for a domain
- `get_required_variables(domain)` — only variables marked "Req" in the IG
- `get_conditional_variables(domain)` — variables marked "Cond" or "Exp"
- `get_ct_variables(domain)` — variables that use controlled terminology
- `get_variable_detail(domain, variable)` — detailed definition for a specific variable
- `is_available()` — True if IG content exists (file or database)

This is the **source of truth for domain-specific logic**: required variables, decision approaches (RACE handling, conversion factors, LBTESTCD mappings, visit mappings, trial design domains) should all be driven by IG content, not hardcoded.

### Spec Manager (`core/spec_manager.py`)

Handles the specification as a living document:
- Read/write the spec in both JSON (machine) and XLSX (human) formats
- Track spec versions (draft → reviewed → approved → finalized)
- Validate spec consistency: every codelist referenced must be defined, every variable listed must have complete metadata
- Generate define.xml metadata from the spec
- **Consistency enforcement:** After code generation, verify that the R program's actual mappings match what the spec says. If the spec says C66731 for SEX, the Parquet comparison must confirm M/F values only. The XPT file is validated separately as part of the P21 process.

### Human Review Interface (`core/human_review.py`)

CLI-based interface (since this runs in Claude Code) that:
- Presents the spec in a readable table format
- Highlights variables requiring human decisions
- For each decision point:
  - Displays all options with IG references
  - Shows pros and cons
  - Accepts user selection (A/B/C or custom text)
  - Records the decision with timestamp
- Supports approve / approve-with-changes / reject actions
- Logs all human interactions for audit trail

---

## Orchestrator Flow (main.py)

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                             │
│                                                             │
│  1. Load Configuration                                       │
│     ├── Read function_registry.json                          │
│     ├── Initialize IG database client                        │
│     └── Set up pipeline state                                │
│                                                             │
│  2. SPEC BUILDER AGENT (Sonnet)                              │
│     ├── Profile raw data                                     │
│     ├── Query IG for each variable                           │
│     ├── Consult function registry for available tools        │
│     ├── Build draft spec                                     │
│     └── Flag decision points (RACE, RFSTDTC, dates, etc.)   │
│                                                             │
│  3. SPEC REVIEWER AGENT (Opus)                               │
│     ├── Completeness check                                   │
│     ├── CT compliance check                                  │
│     ├── Derivation logic review                              │
│     └── Function selection validation                        │
│     ↓                                                        │
│     If issues found → back to Spec Builder                   │
│                                                             │
│  4. HUMAN REVIEW GATE                                        │
│     ├── Present spec for review                              │
│     ├── Collect decisions on flagged items                    │
│     │   "The IG shows 3 approaches for RACE Other Specify:   │
│     │    A) Map to closest CT term                            │
│     │    B) All → OTHER + SUPPDM                             │
│     │    C) Mixed → MULTIPLE + SUPPDM                        │
│     │    Which approach for this study?"                      │
│     └── Record approval + decisions                          │
│     ↓                                                        │
│     If rejected → back to Spec Builder with feedback         │
│                                                             │
│  5. PRODUCTION PROGRAMMER (Sonnet)                           │
│     ├── Read approved spec                                   │
│     ├── Read function registry for available R functions    │
│     ├── Generate R script using functions where available    │
│     ├── Execute Rscript                                       │
│     ├── Save dataset (Parquet primary + XPT regulatory)      │
│     └── Generate SUPPDM if applicable                        │
│                                                             │
│  6. QC PROGRAMMER (Opus) — runs independently                │
│     ├── Read approved spec (same as production)              │
│     ├── Read function registry (same functions available)    │
│     ├── Generate independent R script (different structure)  │
│     ├── Execute Rscript                                      │
│     └── Save QC dataset (Parquet)                            │
│     ↓                                                        │
│  7. COMPARISON LOOP                                          │
│     ├── If 0 differences → proceed to validation             │
│     └── If differences found:                                │
│         ├── QC agent reviews its logic vs spec               │
│         ├── Production agent reviews its logic vs spec       │
│         ├── Correct agent fixes code                         │
│         ├── Re-run and re-compare                            │
│         └── Repeat until 0 differences (max 5 iterations)   │
│                                                             │
│  8. VALIDATION AGENT (Sonnet)                                │
│     ├── Generate P21 spec sheet from approved spec           │
│     ├── Run validation checks against final dataset          │
│     ├── Verify spec ↔ data ↔ define.xml consistency          │
│     ├── Generate define.xml metadata                         │
│     └── Route failures back to appropriate agent             │
│                                                             │
│  9. FINALIZATION                                             │
│     ├── Verify: spec codelist refs = data values = define CT │
│     ├── Archive all artifacts with audit trail               │
│     └── Generate pipeline completion report                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Orchestrator | Python 3.11+ | Main coordination logic |
| LLM API | Anthropic Claude API | Sonnet for production agents, Opus for QC/review; optional (template mode works without API key) |
| IG Knowledge | Markdown files (primary) | File-based parsing of `sdtm_ig_content/*.md`; PostgreSQL + pgvector optional for RAG |
| R Execution | subprocess (Rscript) | Execute generated R scripts; no SAS required |
| Primary Output | Parquet (`arrow::write_parquet`) | Fast, columnar; used for comparison and validation |
| Submission Output | XPT (`haven::write_xpt`) | SAS transport v5; required for FDA regulatory submission |
| Function Registry | JSON (`function_registry.json`) | Machine-readable R function catalog |
| Spec Format | JSON (machine) + XLSX (human) | Single source of truth |
| Configuration | YAML (`config.yaml`) | Paths, model selection, LLM mode, R settings |
| Automation | Claude Code skills + MCP + hooks | 5 skills, 5 MCP tools, security hooks |

### Python Dependencies

```
anthropic           # Claude API client
psycopg2-binary     # PostgreSQL client
pandas>=2.0.0       # Data manipulation and Parquet comparison
pyarrow>=14.0.0     # Parquet read/write (required by pandas for .parquet)
openpyxl            # Excel spec generation
pyyaml              # Configuration
rich                # CLI formatting for human review
```

### R Package Dependencies

```r
install.packages(c("arrow", "haven"))
# arrow  — write_parquet() / read_parquet()
# haven  — write_xpt() (SAS transport v5 for submission)
```

R 4.x must be on PATH (`Rscript --version` should work). The three R transform functions use base R only.

---

## Configuration (`config.yaml`)

```yaml
study:
  study_id: "XYZ-2026-001"
  domain: "DM"

paths:
  raw_data: "./study_data/raw_dm.csv"
  annotated_crf: "./study_data/annotated_crf_dm.csv"
  protocol: "./study_data/protocol_excerpt_dm.pdf"
  sap: "./study_data/sap_excerpt_dm.pdf"
  function_registry: "./r_functions/function_registry.json"
  function_library: "./r_functions/"
  ct_lookup: "./macros/ct_lookup.csv"
  output_dir: "./orchestrator/outputs/"

agents:
  use_llm: false                # Set to true when ANTHROPIC_API_KEY is available
  dry_run: false                # Log prompts without calling API (for training)
  spec_builder:
    model: "claude-sonnet-4-20250514"
    max_tokens: 8000
  spec_reviewer:
    model: "claude-opus-4-20250514"
    max_tokens: 4000
  production_programmer:
    model: "claude-sonnet-4-20250514"
    max_tokens: 8000
  qc_programmer:
    model: "claude-opus-4-20250514"
    max_tokens: 8000
  validation_agent:
    model: "claude-sonnet-4-20250514"
    max_tokens: 4000

comparison:
  max_iterations: 5             # Max production+QC re-runs on mismatch
  method: "exact"

database:                       # Optional — file-based IG fallback works without this
  host: "localhost"
  port: 5432
  name: "sdtm_ig_rag"
  user: "sdtm_user"

r:
  rscript_path: "Rscript"       # Must be on PATH
  output_format: "parquet"      # parquet (primary), csv, or rds
  write_xpt: true               # also write XPT for regulatory submission
  xpt_dir: "./orchestrator/outputs/validation"
```

---

## Key Design Decisions

### Why JSON for the Function Registry?
So agents can programmatically discover what R functions exist, understand their parameters, and generate correct R code — without needing to parse R source. The registry is the communication contract between the orchestrator and the R function library.

### Why Different LLMs for Production vs QC?
Genuine independence. If both agents used the same model with the same prompt patterns, they'd likely produce identical code — defeating the purpose of double programming. Sonnet and Opus have different reasoning patterns, which means they'll write different (but functionally equivalent) R scripts, providing real QC value.

### Why Human-in-the-Loop for Spec Approval?
The SDTM IG is often ambiguous. Real-world SDTM programming requires judgment calls based on company standards, sponsor preferences, and regulatory precedent. The AI presents options with evidence; the human makes the call. This is also a key training point — showing programmers where AI cannot (and should not) make autonomous decisions.

### Why Spec-Driven Architecture?
In real clinical programming, you never code first and document later. The specification is written and approved before any R (or SAS) code is generated. The define.xml (regulatory metadata) is also generated from the spec, not reverse-engineered from the data. Keeping the spec as the single source ensures consistency across code, data, and documentation.

---

## Implementation Status

All core components are built and functional for the DM domain:

| # | Component | Status | Files |
|---|-----------|--------|-------|
| 1 | State management | Done | `core/state.py` (with JSON persistence) |
| 2 | Function loader | Done | `core/function_loader.py` |
| 3 | IG client | Done | `core/ig_client.py` (file-based fallback) |
| 4 | Spec builder | Done | `agents/spec_builder.py` (20 required DM vars) |
| 5 | Human review | Done | `core/human_review.py` |
| 6 | Spec reviewer | Done | `agents/spec_reviewer.py` (IG-driven) |
| 7 | Spec manager | Done | `core/spec_manager.py` (domain-aware) |
| 8 | Production programmer | Done | `agents/production_programmer.py` (+ SUPPDM) |
| 9 | QC programmer | Done | `agents/qc_programmer.py` (independent) |
| 10 | Validation agent | Done | `agents/validation_agent.py` (P21 + define.xml + spec sheet) |
| 11 | LLM client | Done | `core/llm_client.py` (LIVE/DRY_RUN/OFF) |
| 12 | Compare module | Done | `core/compare.py` |
| 13 | Main orchestrator | Done | `main.py` (error gates + comparison loop) |
| 14 | Training context | Done | `core/training_context.py` (domain + project context gathering) |
| 15 | Training generator | Done | `agents/training_generator.py` (chapter packages for all levels) |

**Next:** Extend to additional domains (AE, VS, LB, etc.) by adding domain-specific IG content markdown files to `sdtm_ig_db/sdtm_ig_content/`.

---

## How to Run

```bash
# 1. Ensure R is on PATH and required R packages are installed
Rscript --version
Rscript -e 'install.packages(c("arrow", "haven"), repos="https://cloud.r-project.org")'

# 2. Set up the Python environment
pip install -r orchestrator/requirements.txt

# 3. Configure
cp orchestrator/config.yaml.example orchestrator/config.yaml
# Edit config.yaml — no API key needed for template mode (use_llm: false)

# 4. Verify prerequisites
python verify_setup.py

# 5. Run the full pipeline for DM domain
python orchestrator/main.py --domain DM

# Or run individual stages
python orchestrator/main.py --domain DM --stage spec_build
python orchestrator/main.py --domain DM --stage spec_review
python orchestrator/main.py --domain DM --stage human_review
python orchestrator/main.py --domain DM --stage production
python orchestrator/main.py --domain DM --stage qc
python orchestrator/main.py --domain DM --stage compare
python orchestrator/main.py --domain DM --stage validate

# Resume after crash or interruption
python orchestrator/main.py --domain DM --resume

# Continue past spec review failures
python orchestrator/main.py --domain DM --force

# Generate training materials
python orchestrator/main.py --domain DM --training --level operator --topic spec_building
python orchestrator/main.py --domain DM --training --level builder --topic full_pipeline
python orchestrator/main.py --domain DM --training --chapter 5 --level architect --topic validation
```

### Pipeline Error Gates

The pipeline includes error gates that prevent cascading failures:
- **Spec review gate:** If review fails, pipeline stops (use `--force` to override)
- **Production gate:** If R script fails, pipeline aborts before QC
- **QC gate:** If QC R script fails, pipeline aborts before comparison
- **Comparison loop:** On mismatch, re-runs production+QC+compare up to `max_iterations` times (default: 5)

### Output Artifacts

No SAS or Viya is required. The pipeline produces:
- `outputs/datasets/dm.parquet` — primary working format for comparison and validation
- `outputs/validation/dm.xpt` — SAS transport v5 for regulatory submission (FDA)
- `outputs/specs/dm_mapping_spec.json` + `.xlsx` — draft spec
- `outputs/specs/dm_mapping_spec_approved.json` — approved spec
- `outputs/programs/dm_production.R` — production R script
- `outputs/qc/dm_qc.R` + `dm_qc.parquet` — QC R script and dataset
- `outputs/qc/dm_compare_report.txt` — comparison report
- `outputs/validation/p21_report.txt` — P21 validation results
- `outputs/validation/p21_spec_sheet.xlsx` — P21 specification sheet
- `outputs/validation/define_metadata.json` — define.xml metadata
- `outputs/pipeline_state.json` — saved pipeline state for resume

---

## Claude Code Skills

Six slash commands are available in `.claude/skills/`:

| Command | File | Purpose |
|---------|------|---------|
| `/run-pipeline` | `run-pipeline.md` | Execute the full pipeline or individual stages. Checks prerequisites, runs `python orchestrator/main.py`, parses output for errors, diagnoses R package issues, reports generated artifacts. |
| `/profile-data` | `profile-data.md` | Profile raw clinical data: types, distinct values, missing counts, date format inconsistencies, CT mapping candidates. Cross-checks against annotated CRF. |
| `/review-spec` | `review-spec.md` | Interactive spec review: reads spec JSON, displays formatted table, presents `human_decision_required` variables with options/pros/cons, collects user decisions, saves approved spec. |
| `/validate-dataset` | `validate-dataset.md` | Run comprehensive P21-style checks on a dataset: required variables, CT values, ISO dates, USUBJID format, variable types/lengths. Displays pass/fail table. |
| `/check-environment` | `check-environment.md` | Verify all prerequisites: Python packages, R availability, R packages (arrow, haven), config.yaml validity, study data, function registry, CT lookup, IG content, database (optional), API key (optional). |
| `/generate-training` | `generate-training.md` | Generate complete training chapter packages (exercises, instructor guide, handouts) for any SDTM domain and skill level (consumer, operator, builder, architect). |

---

## MCP Tools

The MCP server (`mcp_server.py`) exposes 5 tools configured in `.claude/mcp.json`:

| Tool | Purpose |
|------|---------|
| `sdtm_variable_lookup(domain, variable)` | Look up variable definition and CT info from IG markdown content |
| `ct_lookup(codelist_code)` | Read ct_lookup.csv and return raw→CT mappings for a codelist |
| `profile_raw_data(csv_path)` | Profile a CSV dataset (types, distinct values, missing, quality) |
| `query_function_registry(function_name)` | Return function details from function_registry.json |
| `read_spec(domain, approved)` | Read and return the mapping specification JSON |

Run locally via: `python mcp_server.py` (falls back to CLI test mode if `mcp` package not installed).

---

## Hooks

Configured in `.claude/settings.local.json`:

- **PreToolUse (Write):** Blocks writing files whose paths contain `.env`, `api_key`, `credential`, or `secret` — prevents accidental secret exposure.

---

## Raw Data (`study_data/raw_dm.csv`)

300 subjects across 6 sites. 16 columns:

| Column | Description | Notes |
|--------|-------------|-------|
| STUDYID | Study identifier | Constant: XYZ-2026-001 |
| SITEID | Site number | 6 sites |
| SUBJID | Subject ID | Unique within site |
| BRTHDT | Birth date | Mixed formats (DD-MON-YYYY, MM/DD/YYYY, ISO) |
| RFSTDTC | Reference start date | Enrollment date; some partial dates |
| SEX | Sex | Raw values: Male, Female, M, F, etc. |
| RACE | Race | Includes "Other Specify" free text |
| RACEOTH | Race Other Specify | Free text for OTHER race values |
| RACEO | Race Other (alternate) | Alternate field for OTHER |
| ETHNIC | Ethnicity | Raw values mapped to CT |
| ARMCD | Arm code | Treatment arm code |
| ARM | Arm description | Treatment arm description |
| COUNTRY | Country | Country code |
| INVNAM | Investigator name | PI name per site |
| ... | (additional) | Other raw fields |

---

## Known Limitations

1. **iso_date ambiguity:** When both parts of a slash-separated date are <= 12 (e.g., `03/04/2020`), auto-detection defaults to MM/DD/YYYY. Use the `infmt` parameter to force DD/MM/YYYY when working with non-US date formats.

2. **IG content scope:** Currently only `dm_domain.md` and `general_assumptions.md` are available. To extend to other domains (AE, VS, LB, etc.), add corresponding markdown files to `sdtm_ig_db/sdtm_ig_content/` following the same table format.

3. **LLM mode:** Template-based logic (OFF mode) produces hardcoded R scripts for DM only. For other domains or adaptive spec generation, enable LLM mode (`use_llm: true`) with an API key.

4. **Database optional:** The PostgreSQL + pgvector database is not required. The IG client falls back to parsing markdown files directly. The database is only needed for semantic search (RAG) across large IG content.

5. **SUPPDM:** Generated for RACE "Other Specify" values only. Other supplemental qualifiers (e.g., RFICDTC, custom qualifiers) require spec extensions.

6. **Comparison precision:** Parquet comparison uses pandas with default float precision. Numeric derivations (AGE, DMDY) should produce exact integer matches; floating-point discrepancies may need tolerance settings.
