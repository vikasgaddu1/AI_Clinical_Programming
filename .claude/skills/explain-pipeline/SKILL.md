---
description: Explain any pipeline stage in plain language — what it does, which agent runs it, what it reads, what it writes, and which training chapter taught you to build it. Perfect for when you're looking at an unfamiliar file and want to understand where it fits.
user-invocable: true
argument-hint: "<stage_or_file>"
---

# Explain Pipeline Stage

Get a clear, plain-English explanation of any pipeline stage, agent, or output file — including which chapter in the training curriculum taught you to build or understand it.

## Usage
- `/explain-pipeline spec_build` — explain the spec building stage
- `/explain-pipeline production` — explain the production programming stage
- `/explain-pipeline compare` — explain the comparison module
- `/explain-pipeline dm_production.R` — explain what a production R script is and where it comes from
- `/explain-pipeline memory_manager.py` — explain the memory system
- `/explain-pipeline igclient` — explain the IG client and its role

## Instructions

1. **Parse the argument** to identify what's being asked about. Match against known stages, files, and components:

   **Pipeline Stages:** spec_build, spec_review, human_review, production, qc, compare, validate
   **Agents:** spec_builder, spec_reviewer, production_programmer, qc_programmer, validation_agent
   **Core components:** state_manager, spec_manager, function_loader, llm_client, compare, memory_manager, ig_client, config_resolver, conventions
   **Output files:** mapping_spec.json, mapping_spec_approved.json, *_production.R, *_qc.R, *.parquet, compare_report.txt, p21_report.txt, define_metadata.json, pipeline_state.json

2. **Generate a structured explanation** with these sections:

   ```
   =============================================================
   WHAT IS: {THING}
   =============================================================

   IN PLAIN ENGLISH:
   {2-3 sentences a clinical programmer would understand}

   WHERE IT LIVES:
   {file path(s)}

   WHAT IT READS (inputs):
   - {input 1}: {why}
   - {input 2}: {why}

   WHAT IT WRITES (outputs):
   - {output 1}: {what it contains}
   - {output 2}: {what it contains}

   WHICH AGENT OR MODULE DOES THIS:
   {name + one-line description of its role}

   THE CHAPTER THAT TAUGHT YOU THIS:
   Chapter {N}: {Title}
   Connection: {how this component uses what you learned in that chapter}

   COMMON QUESTIONS:
   Q: {question participants often ask}
   A: {clear answer}

   HOW TO INSPECT THIS RIGHT NOW:
   {1-2 commands to view or verify this component}
   =============================================================
   ```

3. **Use these mappings** to populate the "Chapter" field:

   | Component | Chapter | Connection |
   |-----------|---------|-----------|
   | IGClient, IG content files | Ch.3 (RAG System) | The IGClient is the RAG system you built — it chunks and retrieves markdown instead of using a database |
   | spec_builder.py | Ch.1 (NotebookLM) + Ch.3 (RAG) | Source grounding: agent queries IG just like NotebookLM queries uploaded docs |
   | Claude Code skills, MCP tools | Ch.2 (Claude Code) | The /run-pipeline skill, mcp_server.py, and hooks are exactly what Ch.2 taught |
   | function_registry.json, FunctionLoader | Ch.2B (Function Library) | The registry pattern you built in Ch.2B — agents read it before generating R code |
   | ct_lookup.csv, NCI EVS API calls | Ch.4 (REST API) | The CT matching pipeline from Ch.4 — same codelist lookup, same extensibility logic |
   | approved_packages.json, PackageManager | Ch.5 (Package Management) | The compliance system from Ch.5 — R scripts use only arrow + haven |
   | AGENT.md files, skill design | Ch.6 (Vibe Coding) | The agent and skill architecture you built in Ch.6 |
   | memory_manager.py, decisions_log.yaml, pitfalls.yaml | Ch.7 (Memory System) | The full memory architecture from Ch.7 — running live in every pipeline stage |
   | compare.py | Ch.3/4 | The comparison loop catches CT errors that Ch.3 (IG) and Ch.4 (CT) define |
   | human_review.py | All chapters | Human review is the gate where study comprehension (Ch.1) meets coding decisions |

4. **For specific stages, use these explanations as a starting point** (adapt as needed):

   **spec_build:**
   "The Spec Builder agent reads the raw data, asks the IG client what variables the DM domain requires, and generates a draft mapping specification. For each variable, it figures out the source column, the required codelist, the derivation logic, and — importantly — flags any decision that a human must make (like how to handle RACE 'Other Specify'). Think of it as an AI programmer's first pass at a mapping spec, grounded in the SDTM IG."

   **human_review:**
   "This is the only stage in the pipeline that cannot be automated. The approved spec is shown to a human clinical programmer who reviews each flagged decision and makes a choice. The system presents options with IG citations and pros/cons — like a spec review meeting, but structured. Every decision is recorded in the memory system for future reference. The spec doesn't move to production until a human says it's ready."

   **production:**
   "The Production Programmer agent reads the approved spec and the function registry, then generates an R script that implements every variable in the spec. It uses only registered functions (iso_date, derive_age, assign_ct) — it never invents custom logic when a validated function exists. The script is then executed with Rscript, and the output is a Parquet file. If the R script fails, the pipeline stops."

   **qc:**
   "The QC Programmer is a completely independent implementation. It uses a different LLM model (Opus instead of Sonnet), it does not see the production code, and it generates its own R script from scratch using only the approved spec and function registry. This mirrors real double-programming: two programmers, same spec, independent implementations. The independence is genuine because the model is different — Opus is more critical and will catch assumptions that Sonnet accepted."

   **compare:**
   "The compare module reads both Parquet files (production and QC) and does a column-by-column diff. If all values match, the pipeline moves to validation. If they don't match, the mismatch report is fed back to the production programmer for a re-run (up to 5 iterations). Matching doesn't mean the data is correct — it means both independent implementations agree. Correctness is checked by validation."

   **validate:**
   "The Validation Agent runs P21-style checks: required variables present, CT values in their codelists, ISO 8601 dates, USUBJID format, variable types and lengths. It also generates define.xml metadata and a P21 spec sheet. This is the final gate before the dataset would go into a submission package."

5. **For files, map them to their stage:**
   - `*_mapping_spec.json` → spec_build output
   - `*_mapping_spec_approved.json` → human_review output
   - `*_production.R` and `*.parquet` → production output
   - `*_qc.R` and `*_qc.parquet` → qc output
   - `*_compare_report.txt` → compare output
   - `p21_report.txt`, `define_metadata.json` → validate output
   - `pipeline_state.json` → state manager, updated after every stage

6. **Always end with an invitation:** "Want to go deeper? Try: `/trace-variable {relevant_var} DM` to see this stage's output for a specific variable, or ask me to open the relevant source file."
