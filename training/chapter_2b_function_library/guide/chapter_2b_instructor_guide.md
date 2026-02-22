# Chapter 2B Instructor Guide: Making Your Function Library AI-Discoverable

## Chapter Overview

| Item | Detail |
|------|--------|
| **Title** | Building an AI-Discoverable Function & Macro Library |
| **Duration** | 3-4 hours |
| **Skill Level** | Operator → Builder |
| **Prerequisites** | Chapter 2 completed (Claude Code basics, skills, MCP) |
| **Core Takeaway** | AI tools should call your team's existing functions, not reinvent them. A structured JSON registry is the communication contract between AI agents and your code library. |

## Why This Chapter Exists

Clinical programming teams have years of accumulated R functions and SAS macros -- date conversion, age derivation, controlled terminology mapping, visit windowing, lab unit conversion, and dozens more. When teams adopt AI coding tools, the single biggest risk is that the AI writes everything from scratch, ignoring battle-tested code that already handles edge cases, company standards, and regulatory requirements.

This chapter teaches participants how to make their existing code libraries discoverable by AI tools. The key mechanism is a **function registry** -- a structured JSON file that describes what functions exist, what parameters they take, when to use them, and how they depend on each other. This is the same pattern used by the SDTM Agentic Orchestrator in the Capstone.

## Learning Objectives

By the end of this chapter, participants will be able to:

1. Explain why AI tools need a machine-readable function catalog (not just source code)
2. Describe the anatomy of a function registry entry (name, parameters, when_to_use, dependencies, examples)
3. Read and interpret the existing `function_registry.json` and `macro_registry.json`
4. Register a new R function in the registry with correct metadata
5. Understand how the `FunctionLoader` class provides registry data to AI agents
6. Verify that Claude Code discovers and uses registered functions in generated code
7. Design a migration strategy for converting SAS macro libraries to R function libraries

## Connection to Other Chapters

| Chapter | Connection |
|---------|-----------|
| **Ch.1 (NotebookLM)** | NotebookLM grounds answers in documents; the registry grounds AI code in your functions |
| **Ch.2 (Claude Code)** | Claude Code reads the registry via CLAUDE.md instructions and MCP tools |
| **Ch.3 (RAG)** | RAG retrieves IG content; the registry retrieves function metadata -- similar pattern |
| **Capstone** | The orchestrator's agents use `FunctionLoader` to discover and call registered functions |

---

## Session Outline

### Module 2B.1: The Problem -- Why AI Rewrites Your Code (20 min)

**Key Point:** Without a discoverable catalog, AI tools have no way to know your team's code exists.

**Talking Points:**
- Scenario: you ask Claude Code to "convert birth dates to ISO 8601 format"
  - Without registry: Claude writes a custom date parser (50+ lines, misses edge cases your team already handles)
  - With registry: Claude finds `iso_date()` in the registry and generates `dm <- iso_date(dm, invar = "BRTHDT", outvar = "BRTHDTC")`
- The cost of reinvention:
  - Edge cases not handled (partial dates, ambiguous formats, non-US date conventions)
  - Company standards violated (your team always uses midpoint imputation; AI uses first-of-month)
  - Validation risk: new code needs testing; existing functions are already validated
  - Maintenance burden: now you have two implementations of the same logic
- Why can't AI just read the `.R` files?
  - It CAN, but parsing source code is unreliable for parameter discovery
  - Comments may be missing or outdated
  - No machine-readable metadata about when to use the function
  - No dependency information (which functions must run first?)
  - No usage examples that AI can copy directly

**Demo:** Open Claude Code in the project. Ask it to "profile what R functions are available" -- show how it reads `function_registry.json` and lists the functions with their purposes and parameters.

---

### Module 2B.2: The Function Registry Pattern (30 min)

**Key Point:** A JSON registry is the communication contract between your team and AI tools.

**Talking Points:**
- Walk through `r_functions/function_registry.json` on screen
- Anatomy of a registry entry (using `iso_date` as example):

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Function name AI uses in generated code | `"iso_date"` |
| `file` | Source file path | `"iso_date.R"` |
| `category` | Grouping for discovery | `"Date Handling"` |
| `purpose` | One-line description | `"Convert non-standard dates to ISO 8601"` |
| `when_to_use` | Array of scenarios (this is what AI reads to decide) | `["Whenever a raw date needs ISO conversion"]` |
| `parameters` | Full parameter spec with types, defaults, examples | `[{name, type, required, description, example}]` |
| `dependencies` | What must run before this function | `[]` for iso_date; `["iso_date"]` for derive_age |
| `usage_examples` | Copy-paste-ready code | `[{description, code}]` |
| `notes` | Edge cases and warnings | `["Ambiguous dates default to MM/DD/YYYY"]` |

- The `orchestrator_integration` section: tells the orchestrator HOW to use the registry
  - Discovery → Selection → Sequencing → Parameterization → Code Generation → Execution
- Why JSON (not YAML, not comments in source)?
  - JSON is universally parseable by any language
  - Schema is explicit and validatable
  - AI can read JSON natively in prompts
  - Same format works for R, SAS, Python, or any language

**Activity:** Display the full `iso_date` registry entry. Ask participants to identify which fields would help AI decide to use this function vs writing custom code.

---

### Module 2B.3: The FunctionLoader -- How Agents Read the Registry (25 min)

**Key Point:** The Python `FunctionLoader` class reads the JSON registry and provides it to AI agents in their prompts.

**Talking Points:**
- Walk through `orchestrator/core/function_loader.py`:
  - `load()`: reads the JSON file once, caches it
  - `get_functions()`: returns the list of function definitions
  - `get_function_by_name(name)`: look up a specific function
  - `get_usage_examples(name)`: get copy-paste examples for a function
  - `get_dependency_order()`: topological sort -- which functions run first?
  - `format_for_prompt()`: formats the entire registry as text for LLM prompts

- How agents receive the registry:
  1. `main.py` creates a `FunctionLoader` instance
  2. The Spec Builder agent receives `format_for_prompt()` output in its system prompt
  3. The Production Programmer agent receives it when generating R code
  4. The QC Programmer receives the same registry (same functions, independent implementation)

- Key design: agents don't scan the filesystem for `.R` files. They read the registry. This means:
  - You control exactly what the AI can use
  - You can add documentation that doesn't exist in source comments
  - You can deprecate functions by removing them from the registry (even if the file still exists)
  - You can add functions that don't exist yet (as stubs/planned)

**Demo:** Run this Python snippet live:
```python
from orchestrator.core.function_loader import FunctionLoader
fl = FunctionLoader("r_functions/function_registry.json")
print(fl.format_for_prompt())
print("---")
print("Dependency order:", fl.get_dependency_order())
```

---

### Module 2B.4: The SAS Parallel -- Macro Registries (20 min)

**Key Point:** The same pattern works for SAS macros. Teams migrating from SAS to R can maintain parallel registries.

**Talking Points:**
- Walk through `macros/macro_registry.json` side by side with `function_registry.json`
- Same 3 functions exist in both:
  - `%iso_date` (SAS) ↔ `iso_date` (R)
  - `%derive_age` (SAS) ↔ `derive_age` (R)
  - `%assign_ct` (SAS) ↔ `assign_ct` (R)
- Key differences in the registry entries:
  - SAS uses `inds`/`outds` parameters (dataset names); R uses `data` (data frame passed directly)
  - SAS uses flag parameters as `Y`/`N`; R uses `TRUE`/`FALSE`
  - SAS macros use `%` prefix; R functions don't
  - But the `when_to_use`, `dependencies`, and `category` fields are identical
- Migration strategy:
  1. Start with the SAS macro registry (teams likely already have documentation)
  2. Create R equivalents one function at a time
  3. Build the R function registry entry in parallel with the code
  4. The orchestrator reads whichever registry matches the `language` setting in config
- The CT lookup file (`macros/ct_lookup.csv`) is shared between SAS and R -- data is language-agnostic

**Discussion Question:** "Your team has 40 SAS macros. Which ones should you register first? What criteria would you use to prioritize?"

Expected answers: frequency of use, complexity (simple macros may not need registration), regulatory importance (CT mapping, date handling), domain coverage.

---

### Module 2B.5: Integration Points -- CLAUDE.md, MCP, and Skills (25 min)

**Key Point:** The registry integrates with multiple AI tool mechanisms.

**Talking Points:**

1. **CLAUDE.md integration:**
   - The project's `CLAUDE.md` explicitly references `function_registry.json`:
     > "The function registry is the communication contract between the orchestrator and the R function library."
   - Section on Production Programmer: "The Production Programmer uses functions from the registry whenever a function exists for the task."
   - This instruction is loaded into every Claude Code session -- AI always knows the registry exists

2. **MCP tool integration:**
   - The `query_function_registry` MCP tool (from `mcp_server.py`) lets Claude Code query the registry:
     ```
     query_function_registry("iso_date")  →  returns full function metadata
     query_function_registry("all")       →  returns all functions
     ```
   - This means Claude Code can look up function details mid-conversation without reading the file

3. **Skill integration:**
   - The `/run-pipeline` skill triggers agents that read the registry
   - The `/profile-data` skill suggests which functions might apply to profiled data
   - A custom skill could be built to validate registry entries (Exercise 2B.3 idea)

4. **Agent prompt integration:**
   - When the Spec Builder drafts a spec, it knows which functions exist → maps variables to functions
   - When the Production Programmer generates R code, it generates `source()` calls for registered functions
   - The spec includes `macro_used` and `function_parameters` fields that directly reference registry entries

**Demo:** In Claude Code, use the MCP tool:
- Ask: "What R function should I use to convert dates to ISO 8601?"
- Show how Claude looks up the registry and recommends `iso_date()` with correct parameters

---

### Module 2B.6: Designing Your Team's Registry (30 min)

**Key Point:** Practical guidance for teams starting their own function registry.

**Talking Points:**

1. **What to register:**
   - Functions used across multiple programs or domains (iso_date, assign_ct)
   - Functions with complex parameters that AI might get wrong
   - Functions with important edge cases documented in the registry
   - Functions with dependencies that must be called in order
   - Do NOT register: one-off utility functions, trivial wrappers, internal helpers

2. **Writing good `when_to_use` entries:**
   - Be specific: "Map raw categorical values to CDISC CT for SDTM compliance" (good)
   - Not vague: "Process data" (bad)
   - Include the domain context: "Apply to SEX, RACE, ETHNICITY, COUNTRY and other CT-controlled variables"
   - Include negative guidance: "Use this instead of writing custom date conversion code"

3. **Parameter documentation:**
   - Every parameter needs: name, type, required flag, description, example value
   - Include defaults for optional parameters
   - Include the `example` field -- AI uses this to generate correct calls

4. **Dependencies:**
   - List function names that must run before this one
   - The FunctionLoader does topological sorting -- so order in the JSON file doesn't matter
   - Example: `derive_age` depends on `iso_date` (dates must be ISO before age calculation)

5. **Usage examples:**
   - Provide 2-3 examples covering common use cases
   - Examples should be copy-paste-ready (actual variable names, actual codelist codes)
   - Include at least one example with optional parameters specified

6. **Registry versioning:**
   - Include `registry_version` and `registry_date` at the top level
   - Consider version history entries for audit trail
   - In a real project: the registry would be in version control (git)

**Activity:** Participants sketch a registry entry for a function they use frequently at their company (don't share proprietary details -- just the structure).

---

## Exercises (90 min total)

| Exercise | Duration | Description |
|----------|----------|-------------|
| 2B.1 | 20 min | Explore the existing function registry |
| 2B.2 | 30 min | Register a new R function |
| 2B.3 | 20 min | Build a SAS-to-R migration plan |
| 2B.4 | 20 min | Test AI function discovery and code generation |

---

## Slide Deck Outline (22 slides)

| # | Slide Title | Content | Notes |
|---|-------------|---------|-------|
| 1 | Chapter 2B: Making Your Function Library AI-Discoverable | Title slide | |
| 2 | The Problem | AI writes everything from scratch | Show before/after code comparison |
| 3 | What Happens Without a Registry | 50 lines of custom date parsing | Show actual custom code |
| 4 | What Happens With a Registry | 1 line: `dm <- iso_date(dm, ...)` | Same task, one function call |
| 5 | The Cost of Reinvention | Edge cases, standards, validation, maintenance | Bullet points |
| 6 | Why Can't AI Just Read the .R Files? | Missing metadata, no when_to_use, no dependencies | |
| 7 | The Function Registry Pattern | JSON as communication contract | Diagram: Team → Registry → AI |
| 8 | Anatomy of a Registry Entry | Field-by-field walkthrough | Use iso_date as example |
| 9 | `when_to_use` -- The AI Decision Field | Array of scenarios | Highlight this is what AI reads |
| 10 | Parameters: Types, Defaults, Examples | Required vs optional, example values | Table format |
| 11 | Dependencies and Execution Order | Topological sort diagram | iso_date → derive_age → assign_ct |
| 12 | Usage Examples: Copy-Paste Ready | Real code the AI can use directly | Show 2-3 examples |
| 13 | The FunctionLoader Class | Python class that reads the registry | Code walkthrough |
| 14 | `format_for_prompt()` | How registry becomes part of the AI prompt | Show actual prompt text |
| 15 | SAS Macros: Same Pattern | macro_registry.json side by side | Highlight differences |
| 16 | Migration Strategy: SAS → R | Start with registry, build R equivalents | 4-step process |
| 17 | Integration: CLAUDE.md | Registry referenced in project instructions | Show CLAUDE.md excerpt |
| 18 | Integration: MCP Tools | `query_function_registry` tool | Show MCP query/response |
| 19 | Integration: Agent Prompts | How agents receive registry in system prompt | Show prompt snippet |
| 20 | Designing Your Team's Registry | What to register, how to write entries | Best practices |
| 21 | Exercise Preview | 4 exercises overview | |
| 22 | Key Takeaway | Your validated functions + AI's code generation = best of both worlds | |

---

## Timing Summary

| Module | Duration | Cumulative |
|--------|----------|------------|
| 2B.1: The Problem | 20 min | 0:20 |
| 2B.2: The Registry Pattern | 30 min | 0:50 |
| 2B.3: The FunctionLoader | 25 min | 1:15 |
| 2B.4: SAS Parallel | 20 min | 1:35 |
| **Break** | **10 min** | **1:45** |
| 2B.5: Integration Points | 25 min | 2:10 |
| 2B.6: Designing Your Registry | 30 min | 2:40 |
| **Exercises** | **90 min** | **4:10** |
| **Total** | **~4 hours** | |

---

## Key Messages to Reinforce

1. **"The registry is the contract."** Your team owns the functions; the registry tells AI how to use them. Without the registry, AI doesn't know your code exists.

2. **"Don't let AI reinvent the wheel."** If your team has a validated `iso_date` function that handles 5 date formats and edge cases, the AI should call it -- not write a new date parser.

3. **"Same pattern, any language."** The registry pattern works for R, SAS, Python, or any language. The schema is the same; only the `language` field and code examples change.

4. **"The spec references functions."** In the Capstone pipeline, the mapping specification includes `macro_used` and `function_parameters` fields. This creates traceability: spec → registry → function → code → data.

5. **"Register what matters."** Not every utility function needs a registry entry. Focus on functions that are reused across programs, have complex parameters, or are critical for regulatory compliance.

---

## Bridge to Chapter 3

"You've now seen how to make your team's R functions and SAS macros discoverable by AI through a JSON registry. But what about domain knowledge -- the SDTM IG, controlled terminology, and regulatory guidance? In Chapter 3, we build a RAG (Retrieval-Augmented Generation) system that makes regulatory documents searchable, so AI agents can look up variable definitions and mapping rules just like they look up functions in the registry."

---

## Instructor Preparation

- [ ] Verify `r_functions/function_registry.json` loads correctly: `python -c "from orchestrator.core.function_loader import FunctionLoader; fl = FunctionLoader('r_functions/function_registry.json'); print(fl.format_for_prompt())"`
- [ ] Verify MCP tool works: test `query_function_registry` in Claude Code
- [ ] Have both `function_registry.json` and `macro_registry.json` open in side-by-side tabs for Module 2B.4
- [ ] Prepare a simple R function file for Exercise 2B.2 demo (or use the reference solution)
- [ ] Review the reference solution for Exercise 2B.2 at `training/chapter_2b_function_library/reference_solutions/`
