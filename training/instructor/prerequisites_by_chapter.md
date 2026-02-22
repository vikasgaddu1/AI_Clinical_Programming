# Prerequisites by Chapter

## Chapter 1: Google NotebookLM

| Prerequisite | Required/Optional | How to Verify |
|-------------|-------------------|---------------|
| Google account | Required | Log in to https://accounts.google.com |
| Chrome browser | Required | Open Chrome, navigate to https://notebooklm.google.com |
| Study PDFs accessible | Required | Can open `study_data/protocol_excerpt_dm.pdf` locally |

**No software installation needed.** This is the lowest barrier chapter.

---

## Chapter 2: AI Coding Assistants

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| Node.js 18+ | Required | `node --version` | https://nodejs.org |
| Claude Code | Required | `claude --version` | `npm install -g @anthropic-ai/claude-code` |
| Python 3.11+ | Required | `python --version` | https://python.org |
| Python packages | Required | `python -c "import yaml, pandas, pyarrow"` | `pip install pyyaml pandas pyarrow openpyxl rich` |
| VS Code | Required (for Cursor) | Open VS Code | https://code.visualstudio.com |
| Cursor | Required | Open Cursor | https://cursor.com |
| R 4.x | Recommended | `Rscript --version` | https://cran.r-project.org |
| Anthropic API key | Optional | Set in environment | https://console.anthropic.com |

**Verification script:** Run `/check-environment` in Claude Code.

---

## Chapter 2B: Function & Macro Library

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| All Ch.2 prereqs | Required | `/check-environment` | (from Ch.2) |
| Python 3.11+ | Required | `python --version` | (from Ch.2) |
| Claude Code | Required | `claude --version` | (from Ch.2) |
| Function registry | Required | `ls r_functions/function_registry.json` | Included in project |
| Macro registry | Required | `ls macros/macro_registry.json` | Included in project |
| R 4.x | Recommended | `Rscript --version` | https://cran.r-project.org |

**Verification:** `python -c "from orchestrator.core.function_loader import FunctionLoader; fl = FunctionLoader('r_functions/function_registry.json'); print(len(fl.get_functions()), 'functions loaded')"`

---

## Chapter 3: RAG System

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| Python 3.11+ | Required | `python --version` | (from Ch.2) |
| Python packages | Required | `python -c "import yaml, pandas"` | (from Ch.2) |
| Project directory | Required | `ls sdtm_ig_db/sdtm_ig_content/dm_domain.md` | Clone/download project |
| PostgreSQL 14+ | Optional | `psql --version` | https://postgresql.org |
| psycopg2 | Optional | `python -c "import psycopg2"` | `pip install psycopg2-binary` |

---

## Chapter 5: Enterprise Package Management

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| All Ch.2 prereqs | Required | `/check-environment` | (from Ch.2) |
| Python 3.11+ | Required | `python --version` | (from Ch.2) |
| Claude Code | Required | `claude --version` | (from Ch.2) |
| Package registry | Required | `ls package_manager/approved_packages.json` | Included in project |
| PackageManager module | Required | `python -c "from package_manager.package_manager import PackageManager"` | Included in project |
| R 4.x | Recommended | `Rscript --version` | https://cran.r-project.org |

**Verification:** `python -c "from package_manager.package_manager import PackageManager; pm = PackageManager('package_manager/approved_packages.json'); print(len(pm.get_all_packages()), 'packages loaded')"`

---

## Chapter 6: Vibe Coding for Clinical Programmers

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| All Ch.2 prereqs | Required | `/check-environment` | (from Ch.2) |
| Python 3.11+ | Required | `python --version` | (from Ch.2) |
| Claude Code | Required | `claude --version` | (from Ch.2) |
| PostgreSQL 14+ | Recommended | `psql --version` | https://postgresql.org |
| psycopg2 | Recommended | `python -c "import psycopg2"` | `pip install psycopg2-binary` |
| R 4.x | Recommended | `Rscript --version` | https://cran.r-project.org |

**Note:** PostgreSQL is recommended for the TLF Search Tool live demo (Module 6.5). Without it, the instructor can walk through the code and architecture without running the actual database queries. The exercises (6.1-6.4) do not require PostgreSQL.

**Verification:** `python -c "import psycopg2; print('psycopg2 OK')"` and `python training/chapter_6_vibe_coding/tlf_search_app/setup_db.py` (if PostgreSQL is available).

---

## Capstone

| Prerequisite | Required/Optional | How to Verify | Install Command |
|-------------|-------------------|---------------|-----------------|
| All Ch.2 prereqs | Required | `/check-environment` | (from Ch.2) |
| R 4.x | Required | `Rscript --version` | https://cran.r-project.org |
| R arrow package | Required | `Rscript -e "library(arrow)"` | `Rscript -e "install.packages('arrow')"` |
| R haven package | Required | `Rscript -e "library(haven)"` | `Rscript -e "install.packages('haven')"` |
| Config file | Required | `ls orchestrator/config.yaml` | Copy from config.yaml.example |

**Full verification:** Run `python verify_setup.py` from the project root.
