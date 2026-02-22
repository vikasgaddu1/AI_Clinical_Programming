# Common Issues and Troubleshooting

## Chapter 1: NotebookLM

| Issue | Symptom | Solution |
|-------|---------|----------|
| Large PDF slow to process | Spinner for 2+ minutes after uploading SDTM IG | Normal for large PDFs. Wait up to 3 minutes. If it fails, try refreshing and re-uploading. |
| Audio Overview won't generate | "Unable to generate" error | Try a smaller source set. The IG PDF alone may work; three large PDFs together may exceed limits. |
| CSV upload doesn't work well | NotebookLM treats CSV as text, not data | Expected behavior. This is a limitation exercise (1.4). NotebookLM cannot process structured data. |
| Citations point to wrong section | Answer seems right but citation is off | NotebookLM occasionally maps citations imprecisely for large documents. Verify by reading the cited passage. |
| Company policy blocks Google tools | Participant cannot use NotebookLM | Discuss the data governance concern. Participant observes instructor demo instead. |

## Chapter 2: Claude Code & Cursor

| Issue | Symptom | Solution |
|-------|---------|----------|
| Claude Code not found | `claude: command not found` | Ensure Node.js 18+ is installed, then `npm install -g @anthropic-ai/claude-code` |
| CLAUDE.md not loading | Claude doesn't know about the project | Ensure you're running Claude Code from the project root where CLAUDE.md exists |
| MCP server won't start | "Cannot connect to sdtm-tools MCP server" | Run `python mcp_server.py` manually to check for Python import errors. Install missing packages. |
| NotebookLM MCP auth fails | Browser opens but login fails | Try `Repair NotebookLM authentication` in Claude Code. Ensure Chrome is installed. |
| NotebookLM MCP not available | Network restrictions | Use pre-recorded demo video. Skip Exercise 2.2 and do extra time on 2.4. |
| `/check-environment` shows FAIL | Missing Python or R packages | Follow the fix instructions in the output. Most common: `pip install pyyaml pandas pyarrow openpyxl rich` |
| R not found | "Rscript: command not found" | Install R 4.x and ensure it's on PATH. On Windows: add `C:\Program Files\R\R-4.x.x\bin` to PATH. |
| R packages missing | `library(arrow)` fails | `Rscript -e "install.packages('arrow', repos='https://cloud.r-project.org')"` -- arrow can take several minutes to compile. |
| Cursor free tier limit | "You've reached your limit" | Participant observes instructor demo for Exercise 2.5. Or switch to VS Code with Copilot free tier. |
| Pipeline spec_build fails | Config file not found | Ensure `orchestrator/config.yaml` exists. Copy from example if needed. |
| Hook blocks legitimate write | "Blocked by PreToolUse hook" | The hook blocks files with "secret", "api_key", etc. in the path. Rename the file to avoid trigger words. |

## Chapter 2B: Function & Macro Library

| Issue | Symptom | Solution |
|-------|---------|----------|
| FunctionLoader import fails | `ModuleNotFoundError: No module named 'core'` | Run from the project root. Use `sys.path.insert(0, 'orchestrator')` before importing. |
| Registry JSON invalid | `json.decoder.JSONDecodeError` after editing | Validate JSON: `python -c "import json; json.load(open('r_functions/function_registry.json'))"`. Common issue: trailing comma after last array element. |
| New function not discovered | FunctionLoader doesn't list the new function | Ensure the entry was added inside the `"functions": [...]` array, not outside it. Check JSON syntax. |
| Dependency order wrong | `get_dependency_order()` returns unexpected order | Check that `dependencies` field references function names (e.g., `"iso_date"`), not file names (e.g., `"iso_date.R"`). |
| R function test fails | `derive_studyday` returns wrong values | Check the no-Day-0 rule: same day should be Day 1 (not Day 0). Verify `difftime` uses `units = "days"`. |
| MCP tool returns empty | `query_function_registry` returns no results | Ensure MCP server is running (`python mcp_server.py`). Check that the function name matches exactly (case-sensitive). |
| SAS registry not found | Can't open `macro_registry.json` | File is at `macros/macro_registry.json` (not `r_functions/`). Verify the path. |
| Claude ignores registry | Claude writes custom code instead of using registered functions | Ensure CLAUDE.md is loaded (run from project root). Ask Claude to "check what R functions are available in the registry" first. |

## Chapter 3: RAG System

| Issue | Symptom | Solution |
|-------|---------|----------|
| IGClient returns empty | `get_domain_variables("DM")` returns `[]` | Check that `sdtm_ig_db/sdtm_ig_content/dm_domain.md` exists and has the expected `### VARNAME` structure |
| Import error for ig_client | `ModuleNotFoundError` | Run from the project root. Use `sys.path.insert(0, 'orchestrator')` before importing. |
| TextChunker import fails | Can't import from load_sdtm_ig | Use `sys.path.insert(0, 'sdtm_ig_db')` before importing. |
| Config import fails | Can't import from config | Same path issue. Set `sys.path.insert(0, 'sdtm_ig_db')`. |
| AE domain not parsed | `get_domain_variables("AE")` returns `[]` | Check file name: must be `ae_domain.md` (lowercase). Check structure: needs `### VARNAME` headings and a summary table. |
| PostgreSQL not installed | Can't run Exercise 3.5 | Skip to reflection questions. This exercise is optional. |
| pgvector not available | `CREATE EXTENSION vector` fails | Install pgvector: `apt install postgresql-14-pgvector` (Linux) or see https://github.com/pgvector/pgvector for other platforms. |
| Embedding errors | Mock mode producing zeros | Expected in training (mock mode). Real embeddings need an OpenAI or compatible API key. |

## Chapter 5: Enterprise Package Management

| Issue | Symptom | Solution |
|-------|---------|----------|
| PackageManager import fails | `ModuleNotFoundError: No module named 'package_manager'` | Run from the project root. Use `sys.path.insert(0, '.')` before importing, or run `python -c "from package_manager.package_manager import PackageManager"`. |
| approved_packages.json parse error | `json.decoder.JSONDecodeError` after editing | Validate JSON: `python -c "import json; json.load(open('package_manager/approved_packages.json'))"`. Common issue: trailing comma after last entry in the `packages` array. |
| Documentation file not found | `get_documentation()` returns "not found" | Check the file path matches `documentation_path` in the registry. Files must be at `package_manager/package_docs/{language}/{package}/{version}.md`. Ensure lowercase language and package name. |
| Compliance scan false positives | `check_code_compliance()` flags approved packages | The scan checks package status in the registry. Ensure the package entry has `"status": "approved"`. If the version differs, update `approved_version` or `minimum_version`. |
| MCP package_lookup tool error | "Tool not found" or connection refused | Ensure the MCP server is running and `package_lookup` is registered. Check `.claude/mcp.json` for the tool configuration. |
| New package not appearing | Added to JSON but PackageManager doesn't list it | Ensure the entry is inside the `"packages": [...]` array. Re-instantiate PackageManager (it reads the file on `__init__`). |
| Hook blocks valid package | PostToolUse hook rejects code with approved package | Check that the hook script reads the current registry (not a cached version). Verify the package name and version match exactly. |
| Context7 comparison confusion | Participants unsure when to use Context7 vs PackageManager | Context7 = public documentation for exploration and learning. PackageManager = approved versions for production code. Both have a role; they serve different purposes. |
| Version mismatch warning | `is_approved()` returns False for installed version | The installed version must be >= `minimum_version` and <= `approved_version`. Update the registry entry or install the approved version. |

## Capstone

| Issue | Symptom | Solution |
|-------|---------|----------|
| Pipeline fails at production | R script execution error | Check R packages: `Rscript -e "library(arrow); library(haven)"`. Install if missing. |
| Pipeline fails at spec_review | "Review FAILED" message | Normal -- some issues may be flagged. Use `--force` to proceed past review failures. |
| Comparison shows mismatches | Production vs QC differ | In template mode, both scripts are deterministic so they should match. If mismatched: check for floating-point issues in AGE or DMDY. |
| XPT file not generated | No dm.xpt in validation dir | Check config.yaml: `write_xpt: true`. Also verify `haven` R package is installed. |
| Pipeline hangs at human_review | Waiting for input | The human review stage is interactive. Answer the prompts (select options for RACE, etc.) or skip with `--stage production`. |
| Spec already approved | "Spec already exists" message | Delete `orchestrator/outputs/specs/dm_mapping_spec_approved.json` to force re-generation, or use `--force`. |
| Exercise C.2 can't modify spec | JSON parse error after editing | Ensure the JSON is still valid after modification. Use Claude Code to make the edit (it validates JSON). |
| State file conflicts | "Pipeline in unexpected state" | Delete `orchestrator/outputs/pipeline_state.json` to start fresh, or use `--resume` to continue from saved state. |

## General

| Issue | Symptom | Solution |
|-------|---------|----------|
| Path issues on Windows | Forward slash vs backslash | The project uses forward slashes. In Python, use raw strings (`r"path\to\file"`) or forward slashes. |
| Encoding issues | UnicodeDecodeError | Ensure files are UTF-8. Add `encoding='utf-8'` to `open()` calls if needed. |
| Permission denied | Can't write to outputs directory | Check that `orchestrator/outputs/` exists and is writable. Create subdirectories if missing. |
| Git not initialized | Git commands fail | The project may not be a git repository. Initialize with `git init` if needed for exercises. |
