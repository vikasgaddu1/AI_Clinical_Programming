# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent orchestration system that automates SDTM (Study Data Tabulation Model) programming for clinical trials. Takes raw clinical data through spec building, human review, production/QC programming, comparison, and validation to produce submission-ready datasets. Built as a **training demonstration** for clinical programmers learning AI -- uses R (no SAS). Supports **multi-study architecture** with centralized standards and per-study overrides. Working example: DM domain, fictitious Phase III study XYZ-2026-001.

## Commands

```bash
# Verify prerequisites (Python packages, R, config, study data)
python verify_setup.py

# --- Legacy single-study mode (backward compatible) ---
python orchestrator/main.py --domain DM
python orchestrator/main.py --domain DM --stage spec_build

# --- Multi-study mode (standards with exceptions) ---
python orchestrator/main.py --study XYZ_2026_001 --domain DM
python orchestrator/main.py --study XYZ_2026_001 --domain DM --stage spec_build
python orchestrator/main.py --study XYZ_2026_001 --domain DM --stage human_review

# Resume after crash; --force to skip past spec review failures
python orchestrator/main.py --domain DM --resume
python orchestrator/main.py --domain DM --force

# Generate training materials
python orchestrator/main.py --domain DM --training --level operator --topic spec_building

# Install dependencies
pip install -r orchestrator/requirements.txt
Rscript -e 'install.packages(c("arrow", "haven"), repos="https://cloud.r-project.org")'
```

## Architecture

**Pipeline flow:** Spec Builder (Sonnet) -> Spec Reviewer (Opus) -> Human Review Gate -> Production Programmer (Sonnet) -> QC Programmer (Opus) -> Compare Loop -> Validation Agent (Sonnet)

**The mapping specification is the single source of truth.** The spec drives the R code, the define.xml, and the P21 validation. If the spec says SEX uses codelist C66731 with values M/F, then the code MUST produce M/F, the define.xml MUST reference C66731, and the data MUST contain only M/F. Any inconsistency is a submission risk.

### Key Components (all under `orchestrator/`)

| Layer | Files | Role |
|-------|-------|------|
| Entry point | `main.py` | Orchestrates all stages with error gates and comparison loop |
| Agents | `agents/spec_builder.py`, `spec_reviewer.py`, `production_programmer.py`, `qc_programmer.py`, `validation_agent.py` | Each agent reads the spec + function registry + IG, generates artifacts |
| Core | `core/state.py` | Pipeline state with JSON persistence (save/load for `--resume`) |
| | `core/ig_client.py` | SDTM IG queries -- parses `sdtm_ig_db/sdtm_ig_content/*.md` (file-based, no DB required) |
| | `core/function_loader.py` | Reads `r_functions/function_registry.json` -- the contract between orchestrator and R functions |
| | `core/llm_client.py` | Anthropic API wrapper with LIVE / DRY_RUN / OFF modes |
| | `core/spec_manager.py` | Spec read/write in JSON + XLSX, version tracking (draft -> reviewed -> approved -> finalized) |
| | `core/compare.py` | Column-by-column Parquet diff between production and QC datasets |
| | `core/human_review.py` | CLI interface for spec approval and decision collection; supports conventions auto-apply |
| | `core/config_resolver.py` | Layered config resolution: standards + study overrides (multi-study mode) |
| | `core/conventions.py` | Pre-configured decisions at company and study level (standards with exceptions) |
| | `core/memory_manager.py` | Persistent memory: decisions, pitfalls, coding standards, cross-domain context |
| Config | `config.yaml` | All paths, model selection, LLM mode, R settings |
| Multi-study | `standards/` | Company-level defaults: config, conventions, shared resources |
| | `studies/{study}/` | Per-study overrides: config, conventions, optional extra functions |

### Critical Patterns

- **Function registry (`r_functions/function_registry.json`):** Machine-readable catalog of R functions (iso_date, derive_age, assign_ct). Agents MUST use registry functions when one exists for the task -- never write custom logic when a function is available. Agents don't scan the filesystem; they read the registry.
- **IG client, not hardcoded lists:** Required variables, CT-controlled variables, and domain rules come from `ig_client.get_required_variables(domain)`, not hardcoded lists. This makes agents work for any SDTM domain.
- **Production vs QC independence:** Production (Sonnet) and QC (Opus) use different LLMs intentionally -- mirrors real double programming. QC MUST NOT see production code or output.
- **Human decisions are mandatory:** When the IG offers multiple valid approaches (e.g., RACE "Other Specify" handling), agents MUST flag the decision and present options with IG references -- never pick silently.
- **Error gates:** Spec review failure stops the pipeline (use `--force` to override). R script failure aborts before QC. Comparison mismatch triggers re-run loop (max 5 iterations).
- **Memory system (`core/memory_manager.py`):** Persistent memory across pipeline runs. Decisions, pitfalls, coding standards, and cross-domain context are stored in `standards/memory/` (company) and `studies/{study}/memory/` (study). Agents receive relevant memory as context. Pitfalls seen in 2+ studies are auto-flagged for promotion to company level (manual approval required).

### Data Flow

```
{raw_data} (e.g., study_data/raw_dm.csv)
  -> Spec Builder -> {output_dir}/specs/{domain}_mapping_spec.json
  -> Human Review -> {output_dir}/specs/{domain}_mapping_spec_approved.json
  -> Production   -> {output_dir}/programs/{domain}_production.R -> {output_dir}/datasets/{domain}.parquet
  -> QC           -> {output_dir}/qc/{domain}_qc.R -> {output_dir}/qc/{domain}_qc.parquet
  -> Compare      -> {output_dir}/qc/{domain}_compare_report.txt
  -> Validation   -> {output_dir}/validation/p21_report.txt + p21_spec_sheet.xlsx + define_metadata.json
```

## SDTM Domain Knowledge

- **NCI EVS REST API** for live CDISC controlled terminology: `https://api-evsrest.nci.nih.gov/api/v1/`. Use `/concept/ncit/{code}?include=summary` for codelist metadata (name, extensibility), `/subset/ncit/{code}/members?include=summary` for allowed values. No auth required. Check `Extensible_List` property: non-extensible codelists reject values not in the codelist; extensible codelists allow sponsor additions.
- **Static CT fallback:** `macros/ct_lookup.csv` has hand-curated mappings for 4 DM codelists (C66731 SEX, C74457 RACE, C66790 ETHNICITY, C71113 COUNTRY). API synonyms + CSV local mappings together provide full coverage.
- **IG content:** `sdtm_ig_db/sdtm_ig_content/dm_domain.md` and `general_assumptions.md`. To add domains, create `{domain}_domain.md` following the same `### VARNAME` section + summary table format.
- **R functions use base R only** (except arrow/haven for output). Three transform functions: `iso_date()` (messy dates -> ISO 8601), `derive_age()` (AGE/AGEU from birth + reference dates), `assign_ct()` (raw values -> CDISC CT via ct_lookup.csv).
- **iso_date ambiguity:** When both parts of a slash-separated date are <= 12 (e.g., `03/04/2020`), auto-detection defaults to MM/DD/YYYY. Use `infmt` parameter for non-US formats.

## MCP Server

`python mcp_server.py` exposes 5 tools (configured in `.claude/mcp.json`):
`sdtm_variable_lookup`, `ct_lookup`, `profile_raw_data`, `query_function_registry`, `read_spec`

## Training Curriculum

Seven chapters + capstone in `training/`: Ch.1 NotebookLM (Consumer), Ch.2 Claude Code & Cursor (Operator), Ch.2B Function Library (Operator/Builder), Ch.3 RAG for SDTM IG (Builder), Ch.4 REST API for CDISC CT (Builder), Ch.5 Enterprise Package Management (Builder/Architect), Ch.6 Vibe Coding (Builder/Architect), Ch.7 Agent Memory System (Builder/Architect), Capstone (Architect). See `training/README.md`.

## Multi-Study Architecture

The system follows a **standards with exceptions** pattern, mirroring how pharma companies operate: company-level SOPs and conventions apply by default, but individual studies can override specific decisions with documented rationale.

```
standards/                    <- Company-level shared defaults
  config.base.yaml            <- Default agent/R/comparison settings
  conventions.yaml            <- Default human-review decisions (RACE approach, date imputation, etc.)
  coding_standards.yaml       <- Enforced coding rules, variable naming, CDISC compliance
  memory/                     <- Company-wide memory (promoted patterns)
    program_header_template.txt <- Standard R program header
    pitfalls.yaml             <- Known pitfalls promoted from studies
    decisions_log.yaml        <- Cross-study decision patterns

studies/
  _template/                  <- Template for new studies (use /new-study skill)
  XYZ_2026_001/               <- Per-study overrides
    config.yaml               <- Study-specific settings (paths, study_id, domain)
    conventions.yaml           <- Study-specific decision overrides
    memory/                   <- Study-specific memory (auto-generated)
      decisions_log.yaml      <- Human review decision history
      pitfalls.yaml           <- Errors, mismatches, resolutions
      domain_context.yaml     <- Cross-domain decision snapshots
      modification_history.yaml <- Program change log
```

**Key design:**
- **Layered config:** `standards/config.base.yaml` is deep-merged with `studies/{study}/config.yaml`. Study configs contain only settings that DIFFER from the standard.
- **Conventions show + confirm:** Pre-configured decisions are displayed during human review with rationale. Reviewer presses Enter to accept or types an alternative. All decisions logged with source attribution.
- **Function registry merging:** Study-specific R functions are added to (or override by name) the standard registry.
- **IG content search order:** Study-specific IG content dir is searched first, then standard.
- **Backward compatible:** No `--study` flag = exactly the legacy single-study behavior.
- **`ConfigResolver`** (`core/config_resolver.py`): Resolves paths for function registries, IG content dirs, CT lookups, and output dirs based on study mode.
- **`ConventionsManager`** (`core/conventions.py`): Loads and merges conventions from both tiers with source attribution.
- **`MemoryManager`** (`core/memory_manager.py`): Persistent memory for decisions, pitfalls, coding standards, and cross-domain context. Reads company + study memory; writes to study memory only (company via promotion).

## Coding Standards

Enforced by `standards/coding_standards.yaml` and the `MemoryManager`. Agents read these before generating R code.

- **All R code in lowercase** (function calls, control flow, comments).
- **SDTM/ADaM variable names in UPPERCASE** (STUDYID, USUBJID, BRTHDTC, AVAL, PARAMCD).
- **R local variables in snake_case** (raw_dm, ct_path, suppdm_idx).
- **R functions in snake_case** (iso_date, derive_age, assign_ct).
- **Always check function registry before writing new logic.** If a registered function exists, USE IT.
- **Standard company program header** on every R program (from `standards/memory/program_header_template.txt`).
- **Modification history** updated on every program change after initial creation.
- **CDISC compliance rules** included: max variable name length (8), max label length (40), domain sort keys, XPT version 5.

## Memory System

The `MemoryManager` (`core/memory_manager.py`) provides persistent memory across pipeline runs:

- **Decision records**: Every human review decision logged with variable, choice, rationale, source, and outcome. Past decisions shown during subsequent reviews for context.
- **Pitfall records**: R script errors, comparison mismatches, and validation failures recorded with root cause and resolution. Fed into agent prompts so they avoid known mistakes.
- **Domain context**: Cross-domain snapshots (e.g., DM decisions inform AE processing). Key decisions and derived variables stored per domain.
- **Coding standards**: Loaded from `standards/coding_standards.yaml`, injected into all code-generating agents.
- **Program headers**: Rendered from template with populated fields (program name, study, author, modification history).
- **Pitfall promotion**: Pitfalls seen in 2+ studies auto-flagged for company-level promotion (requires human approval).

## Platform Notes

- Windows environment (paths use backslashes in filesystem, but Python/R handle forward slashes)
- R 4.x must be on PATH (`Rscript --version`)
- Python 3.11+
- PostgreSQL + pgvector is optional (file-based IG fallback works without it)
- Template mode (`use_llm: false`) works without ANTHROPIC_API_KEY but only produces DM hardcoded output
