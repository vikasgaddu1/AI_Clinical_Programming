# AI for Clinical Programming: Training Curriculum

A progressive, chapter-based training program for clinical programmers learning to use AI tools in SDTM programming workflows. Built around a fictitious Phase III Type 2 Diabetes study (XYZ-2026-001).

## Curriculum Overview

| Chapter | Title | Duration | What You Learn |
|---------|-------|----------|----------------|
| **1** | [Google NotebookLM for Clinical Programming](chapter_1_notebooklm/) | 2-3 hrs | Use AI to understand protocols, SAPs, and the SDTM IG with source-grounded answers |
| **2** | [AI Coding Assistants: Claude Code & Cursor](chapter_2_cli_tools/) | 4-5 hrs | Direct AI coding tools to read data, write R scripts, and automate clinical programming tasks |
| **2B** | [Making Your Function Library AI-Discoverable](chapter_2b_function_library/) | 3-4 hrs | Register your team's R functions and SAS macros so AI tools call them instead of reinventing the wheel |
| **3** | [Building a RAG System for SDTM IG](chapter_3_rag/) | 5-6 hrs | Build keyword and semantic search over regulatory documents (SDTM IG, CT, guidance) |
| **4** | [Querying CDISC CT via REST API](chapter_4_rest_api/) | 4-5 hrs | Query NCI EVS REST API for live controlled terminology, match raw data to CT, handle extensible vs non-extensible codelists |
| **5** | [Enterprise Package Management for AI](chapter_5_package_management/) | 3-4 hrs | Ensure AI uses only approved packages and versions via a package registry, MCP tools, and enforcement hooks |
| **6** | [Vibe Coding for Clinical Programmers](chapter_6_vibe_coding/) | 5-6 hrs | Use AI-directed development: plan mode, prompting patterns, debugging, custom agents/skills, and build a TLF search tool |
| **7** | [Agent Memory System](chapter_7_memory_system/) | 3-4 hrs | Build persistent memory for AI agents: coding standards, decision history, pitfall tracking, cross-domain context, and promotion workflows |
| **Capstone** | [SDTM Agentic Orchestrator](capstone/) | 6-8 hrs | Integrate all skills into a multi-agent system that automates the full SDTM DM workflow |

## Skill Progression

```
Ch.1         Ch.2          Ch.2B            Ch.3          Ch.4          Ch.5           Ch.6              Ch.7              Capstone
Consumer --> Operator  --> Oper/Builder --> Builder  --> Builder  --> Builder/Arch --> Builder/Arch  --> Builder/Arch  --> Architect

Understand   Direct AI     Function &       RAG for       REST API      Enterprise       Vibe coding,      Agent memory      Integrate
documents    coding tools  macro library    domain        for live      package          agents, skills,   decisions,        everything
w/ AI        & config      for AI           search        CDISC CT      management       TLF search        pitfalls, stds    into agents
```

## How the Chapters Connect

Each chapter builds directly on the previous:

- **Chapter 1** teaches source grounding -- AI answers backed by YOUR documents. This is the same principle the Capstone's agents use when querying the SDTM IG.
- **Chapter 2** introduces Claude Code's architecture (CLAUDE.md, skills, hooks, MCP). These are the exact tools that drive the Capstone's orchestrator.
- **Chapter 2B** teaches how to make your team's existing R functions and SAS macros discoverable by AI through a JSON registry. This is the `function_registry.json` pattern that the Capstone's agents use to generate correct R code.
- **Chapter 3** builds the RAG system that powers the `sdtm_variable_lookup` MCP tool from Chapter 2 and the IG client used by the Capstone's agents.
- **Chapter 4** teaches querying the NCI EVS REST API for live CDISC controlled terminology. The IG (Ch.3) tells you WHICH codelist a variable uses; the REST API (Ch.4) tells you WHAT values are in it, whether it's extensible, and how to match raw data against it.
- **Chapter 5** teaches enterprise package management -- ensuring AI-generated code uses only approved packages at validated versions. A package registry, MCP tools, and enforcement hooks create four layers of compliance: CLAUDE.md rules, MCP documentation, hooks, and CI/CD.
- **Chapter 6** teaches vibe coding -- using plan mode, effective prompting, and AI-assisted debugging to build applications. You create custom agents and skills, then build a TLF search tool live using the RAG patterns from Chapter 3. This prepares you for the Capstone, where these techniques drive the full orchestrator.
- **Chapter 7** teaches agent memory management -- how to make AI agents learn from past runs. Coding standards enforce consistent R code style, decision records capture human choices for reuse, pitfall records prevent repeated errors, and cross-domain context lets downstream agents see upstream decisions. The promotion workflow shows how study-level learnings become company-wide knowledge.
- **Capstone** brings it all together: study comprehension (Ch.1) + AI automation (Ch.2) + function libraries (Ch.2B) + domain knowledge retrieval (Ch.3) + live CT matching (Ch.4) + package compliance (Ch.5) + vibe coding (Ch.6) + agent memory (Ch.7) = automated SDTM pipeline.

## Prerequisites

| Prerequisite | Ch.1 | Ch.2 | Ch.2B | Ch.3 | Ch.4 | Ch.5 | Ch.6 | Ch.7 | Capstone |
|-------------|:----:|:----:|:-----:|:----:|:----:|:----:|:----:|:----:|:--------:|
| Google account + browser | Yes | -- | -- | -- | -- | -- | -- | -- | -- |
| Node.js 18+ | -- | Yes | Yes | -- | -- | Yes | Yes | -- | Yes |
| Python 3.11+ | -- | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| R 4.x + arrow + haven | -- | Rec. | Rec. | -- | -- | Rec. | Rec. | Rec. | Yes |
| VS Code | -- | Yes | -- | -- | -- | -- | -- | -- | -- |
| Cursor (free tier) | -- | Yes | -- | -- | -- | -- | -- | -- | -- |
| Internet access | -- | -- | -- | -- | Yes | -- | -- | -- | Opt. |
| Anthropic API key | -- | Opt. | -- | -- | -- | -- | Opt. | -- | Opt. |
| PostgreSQL | -- | -- | -- | Opt. | -- | -- | Rec. | -- | Opt. |

## Study Materials (Provided)

All chapters use the same fictitious study materials in `study_data/`:

- `protocol_excerpt_dm.pdf` -- Phase III T2DM study protocol
- `sap_excerpt_dm.pdf` -- Statistical Analysis Plan
- `raw_dm.csv` -- Raw demographics data (300 subjects, 6 sites, intentionally messy)
- `annotated_crf_dm.csv` -- CRF annotations
- `raw_dm_mapping_spec.csv` -- Source-to-target variable mapping

The SDTM IG reference is in `docs/SDTMIG_v3.4.pdf`.

## For Instructors

See the [instructor/](instructor/) directory for:
- Session timing and logistics
- Prerequisites verification by chapter
- Common issues and troubleshooting

## Generating New Chapters

Use the `/generate-training` skill in Claude Code or the CLI to generate complete training chapter packages for any domain and skill level:

```bash
# Via CLI
python orchestrator/main.py --domain DM --training --level operator --topic spec_building
python orchestrator/main.py --domain DM --training --level builder --topic full_pipeline
python orchestrator/main.py --domain AE --training --level architect --topic validation

# Via Claude Code slash command
/generate-training 5 operator DM spec_building
```

### Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| Chapter number | Any integer | Next available |
| Skill level | `consumer`, `operator`, `builder`, `architect` | `operator` |
| Domain | `DM`, `AE`, `VS`, `LB`, etc. | `DM` |
| Topic | `data_profiling`, `spec_building`, `production_programming`, `qc_and_comparison`, `validation`, `full_pipeline`, `human_review` | `full_pipeline` |

Each generated chapter includes: exercises, instructor guide, deliverables checklist, and a domain variable reference handout. Content adapts dynamically to the domain using IG content and the function registry.

## Getting Started

Start with **Chapter 1** -- all you need is a Google account and a browser.
