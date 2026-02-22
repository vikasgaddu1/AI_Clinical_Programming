# Capstone: SDTM Agentic Orchestrator -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 6-8 hours (1-2 sessions) |
| Format | Instructor-led workshop (architecture walkthrough + full pipeline run + deep exercises) |
| Audience | Clinical programmers who completed Chapters 1-7 |
| Prerequisites | Python 3.11+, R 4.x + arrow + haven, all env checks passing |
| Materials | Full `AI_Clinical_Programming` project |

## Key Teaching Message

This is where everything comes together. Every chapter in this curriculum was building toward this moment. The source grounding from Chapter 1, the Claude Code architecture from Chapter 2, function libraries from Chapter 2B, the RAG infrastructure from Chapter 3, live CT lookups from Chapter 4, package compliance from Chapter 5, vibe coding and agents from Chapter 6, and the memory system from Chapter 7 -- they're all running inside this orchestrator right now. You'll run the full SDTM pipeline -- from raw data to validated, submission-ready datasets -- and see exactly where each piece lives.

---

## Module C.0: The Real Problem (15 min)

### Why Does Any of This Matter?

Before you touch the code, be honest about what we're trying to fix. SDTM programming is:

- **Repetitive.** The same 20 DM variables get mapped study after study. The same date derivations, the same CT lookups, the same USUBJID logic.
- **High-stakes.** One wrong codelist code, one inconsistency between your spec and your code, and a P21 submission check flags it. FDA reviewers notice.
- **Slow.** QC double-programming means two people write the same boilerplate from scratch, then someone spends hours comparing line-by-line.
- **Hard to scale.** A typical study has 20+ SDTM domains. DM, AE, VS, LB, CM, MH... at a large pharma that's hundreds of datasets per submission.

None of this is fun. And none of it has to be done 100% manually anymore.

### The Challenge → Solution Map

Draw this table on the whiteboard. Come back to it at the end of the capstone to verify every row was addressed.

| Challenge | Why It's Hard | How the Orchestrator Solves It | Chapter Behind It |
|-----------|--------------|-------------------------------|-------------------|
| Consulting the SDTM IG for every variable | 400-page PDF, no search, manual cross-referencing | Spec Builder queries IGClient (local RAG over markdown) | Ch.3 |
| Matching raw values to CDISC controlled terminology | Codelists change, extensibility rules differ per variable | `assign_ct()` + NCI EVS REST API validation | Ch.4 |
| Deciding between valid IG options (e.g. RACE "Other Specify") | Wrong choice = submission risk; IG doesn't say which is right for your study | Decision flags + human review gate with rationale capture | Ch.7 |
| Writing boilerplate R code for standard derivations | Same iso_date, derive_age, assign_ct code written in every study | Production Programmer reads the function registry and uses registered functions | Ch.2B |
| Genuine QC independence | Using the same programmer defeats the purpose | Different LLM model (Opus for QC vs Sonnet for production) -- truly independent | Ch.6 |
| Catching errors before P21 | Without compare step, errors surface at validation too late | Column-by-column comparison loop; spec-driven validation catches CT errors | Ch.3/4 |
| Scaling to new domains | Every new domain means rewriting agent logic | Domain-generic agents: they read IG markdown, not hardcoded variable lists | Ch.3 |
| Package compliance | AI training data includes every package version; wrong one in prod = audit finding | Package enforcement in R script headers; coding standards in memory | Ch.5 |
| Agents forgetting past decisions | Each run starts fresh; repeat human review decisions; same errors recur | Memory system records decisions, pitfalls, cross-domain context | Ch.7 |

### Talking Point

"Every row in that table is a real problem clinical programmers deal with every day. By the end of this session, you'll be able to point to exactly which line of code or which agent solves each one."

---

## Module C.1: Connecting the Chapters (30 min)

### Talking Points

Draw this on the whiteboard. The left side is what you learned; the right side is where it lives in the orchestrator right now.

```
Chapter 1: NotebookLM          --> Spec Builder queries IG content
  "Understand the study"            (same source grounding principle --
                                    but automated via IGClient, not a browser)

Chapter 2: Claude Code          --> Orchestrator uses skills, MCP, hooks
  "Direct AI tools"                 (/run-pipeline skill, mcp_server.py,
                                    the settings.local.json hook you configured)

Chapter 2B: Function Library    --> Production Programmer reads function_registry.json
  "Make functions AI-discoverable"  (iso_date, derive_age, assign_ct --
                                    agents don't reinvent these)

Chapter 3: RAG System           --> IG Client powers Spec Builder + Spec Reviewer
  "Build knowledge retrieval"       (the same IGClient.get_required_variables()
                                    you tested is imported here)

Chapter 4: REST API             --> CT validation in Spec Builder + Validation Agent
  "Query live CDISC CT"             (assign_ct() backed by ct_lookup.csv with
                                    NCI EVS fallback; extensibility checks)

Chapter 5: Package Management   --> R script headers; PackageManager in prompts
  "Enforce approved packages"       (production R code uses only arrow + haven;
                                    coding standards enforced via memory system)

Chapter 6: Vibe Coding          --> How the entire orchestrator was built
  "Build agents and skills"         (plan mode, prompting patterns, the 8 agents
                                    and 7 skills you see in .claude/ right now)

Chapter 7: Memory System        --> memory_manager.py runs in every pipeline stage
  "Persistent learning"             (decisions logged, pitfalls tracked,
                                    coding standards injected into agent prompts)

Capstone: All Together          --> 5 agents automate the full DM workflow
```

**Key connections to call out explicitly:**
- The `IGClient` from Chapter 3 is imported directly by `spec_builder.py` and `spec_reviewer.py` -- open those files and show the import
- The `/run-pipeline` skill from Chapter 2 is what triggers this orchestrator -- it's the same CLI command the skill wraps
- The memory system from Chapter 7 is active right now: open `orchestrator/core/memory_manager.py` and show `get_coding_standards()` being called
- The source grounding principle from Chapter 1 applies to every agent query: the IG is the source, the agents are grounded to it

### The Real-World Workflow Being Automated

Walk through the 11-step manual process:
1. Receive study materials
2. Profile raw data
3. Consult SDTM IG
4. Create mapping specification
5. Human review
6. Production programming
7. QC programming
8. Compare
9. Iterate
10. Validation
11. Spec finalization

"Each step maps to an agent or orchestrator component. The human review step (step 5) is the only one that stays manual -- deliberately."

---

## Module C.2: Architecture Walkthrough (60 min)

Walk through each component with the actual code open.

### State Manager (10 min)
Open `orchestrator/core/state.py`:
- `PipelineState` class with phases: spec_building -> spec_review -> human_review -> production -> qc -> comparison -> validation
- JSON persistence to `outputs/pipeline_state.json`
- `save()` and `load()` methods for crash recovery
- The `--resume` flag reads from saved state

### Spec Manager (10 min)
Open `orchestrator/core/spec_manager.py`:
- Reads/writes spec in JSON + XLSX
- Version tracking: draft -> reviewed -> approved -> finalized
- Consistency validation: every codelist must be defined

### Function Loader (5 min)
Open `orchestrator/core/function_loader.py`:
- Reads `r_functions/function_registry.json`
- `get_dependency_order()` returns: iso_date -> derive_age -> assign_ct
- This is how agents know which R functions exist and in what order to call them

### LLM Client (5 min)
Open `orchestrator/core/llm_client.py`:
- Three modes: LIVE (API calls), DRY_RUN (log prompts), OFF (template logic)
- Template mode works without API key -- perfect for training
- Each agent calls `llm_client.call_agent(agent_name, system_prompt, user_prompt, model)`

### The 5 Agents (20 min)
For each agent, open the file and highlight the key logic:

1. **Spec Builder** (`agents/spec_builder.py`): profiles raw data, queries IG, builds draft spec with decision points
2. **Spec Reviewer** (`agents/spec_reviewer.py`): IG-driven completeness check, CT compliance, derivation logic review
3. **Production Programmer** (`agents/production_programmer.py`): reads approved spec + function registry, generates R script, executes Rscript
4. **QC Programmer** (`agents/qc_programmer.py`): independent implementation using different model (Opus vs Sonnet)
5. **Validation Agent** (`agents/validation_agent.py`): P21 checks, define.xml metadata, spec sheet

### Compare Module (5 min)
Open `orchestrator/core/compare.py`:
- pandas column-by-column diff
- Reads both Parquet outputs
- Returns (match, report) tuple
- On mismatch: the comparison loop re-runs up to 5 times

### Main Orchestrator (5 min)
Open `orchestrator/main.py`:
- CLI with `--domain`, `--stage`, `--config`, `--resume`, `--force`
- Error gates: spec review gate, production gate, QC gate, comparison loop
- State saved after every stage

---

## Module C.3: Full Pipeline Run (90 min)

### Pre-Run Check
```bash
python verify_setup.py
```
Ensure all checks pass (at minimum: Python, R, packages, config, data, registry, IG content).

### Run End-to-End
```bash
python orchestrator/main.py --domain DM
```

Walk through each stage as it runs. Pause after each to explain:

**Stage 1: Spec Building** (~5 min run time)
- Show: raw data profiling output
- Show: 20 DM variables being mapped
- Show: decision points flagged (RACE, ACTARMCD, RFENDTC)

**Stage 2: Spec Review** (~2 min)
- Show: IG-driven completeness check
- Show: review comments (any issues flagged)
- Note: if review fails, pipeline stops (use `--force` to override)

**Stage 3: Human Review** (interactive)
- The spec is presented for review
- Make decisions:
  - RACE: choose Option B (all Other -> RACE='OTHER' + SUPPDM)
  - Any other flagged items: choose based on discussion
- Approve the spec

**Stage 4: Production** (~3 min)
- Show: R script being generated (`dm_production.R`)
- Show: Rscript execution output
- Show: Parquet + XPT output files

**Stage 5: QC** (~3 min)
- Show: independent R script (`dm_qc.R`)
- Note: this uses a different model configuration (Opus vs Sonnet)
- Show: QC Parquet output

**Stage 6: Compare** (~1 min)
- Show: column-by-column comparison
- Show: match/mismatch result
- If mismatch: discuss what happens (re-run loop)

**Stage 7: Validate** (~2 min)
- Show: P21 check results
- Show: define.xml metadata
- Show: spec sheet

### Examine All Artifacts
After the run, list all generated files and show each:

| File | What It Is |
|------|-----------|
| `outputs/specs/dm_mapping_spec.json` | Draft spec (20 variables) |
| `outputs/specs/dm_mapping_spec.xlsx` | Human-readable draft |
| `outputs/specs/dm_mapping_spec_approved.json` | Approved with decisions |
| `outputs/programs/dm_production.R` | Generated R script |
| `outputs/datasets/dm.parquet` | Primary SDTM dataset |
| `outputs/validation/dm.xpt` | SAS transport for FDA |
| `outputs/qc/dm_qc.R` | Independent QC script |
| `outputs/qc/dm_qc.parquet` | QC dataset |
| `outputs/qc/dm_compare_report.txt` | Comparison report |
| `outputs/validation/p21_report.txt` | P21 results |
| `outputs/validation/p21_spec_sheet.xlsx` | P21 spec sheet |
| `outputs/validation/define_metadata.json` | define.xml metadata |
| `outputs/pipeline_state.json` | Saved state |

---

## Module C.4: Deep Dive Exercises (120 min)

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| C.1: Trace RACE Through the Pipeline | 30 min | End-to-end variable traceability |
| C.2: Introduce a Deliberate Error | 30 min | Error detection and spec-driven safety |
| C.3: Add DTHFL to the Spec | 30 min | Extending the spec and regenerating code |
| C.4: Design AE Domain Extension | 30 min | Conceptual design for a new domain |

### Facilitation Tips
- **Exercise C.1:** This is the most important exercise. It demonstrates the spec-driven architecture principle. Take time for group discussion.
- **Exercise C.2:** Deliberately breaking things teaches more than watching things work. Let participants discover the error messages.
- **Exercise C.3:** This shows that adding a variable is a spec change that flows through automatically.
- **Exercise C.4:** This is conceptual -- participants design on paper, not in code. Connect to Chapter 3's AE domain file.

---

## Wrap-Up (30 min)

### Group Discussion
1. "Which part of the pipeline surprised you most?"
2. "Where was human judgment most critical?"
3. "How does this compare to your current SDTM programming workflow?"
4. "What would need to change to use this in production at your organization?"
5. "Our orchestrator uses Python + Claude Code. How would a visual workflow tool like n8n or Zapier change this architecture? What would you gain (visual workflow editor, easy notifications, system integration) and what would you lose (fine-grained code control, R script generation, spec-driven logic)?"
6. "Some teams use LangGraph for agentic orchestration with explicit state graphs. How does that compare to our `main.py` sequential approach? When would the added complexity be worth it?"

### Key Takeaways
1. **The spec is the single source of truth** -- it drives code, QC, validation, and define.xml
2. **AI assists but doesn't replace** -- human review is mandatory, not optional
3. **Double programming with different models** provides genuine QC value
4. **The system is extensible** -- new domains = new IG content + spec entries
5. **Three grounding strategies** (NotebookLM, local RAG, database RAG) serve different needs

### What's Next for Participants
- Try extending to AE domain using the Chapter 3 AE content file
- Enable LLM mode (`use_llm: true`) with an API key for adaptive spec generation
- Explore additional MCP tools for your organization's specific needs
- Consider how this architecture maps to your company's SDTM workflow
- Explore visual orchestration with n8n (open-source, self-hosted) as a front-end trigger layer -- e.g., trigger the pipeline on data drop, send Slack notifications on completion
- Investigate graph databases (Neo4j) for modeling cross-domain dependencies when scaling to 20+ SDTM domains

---

## Slide Deck Outline (for `slides/capstone_slides.pptx`)

| Slide # | Title |
|---------|-------|
| 1 | Title: "Capstone: SDTM Agentic Orchestrator" |
| 2 | Learning Objectives (6 items) |
| 3 | The Real Problem: Why SDTM Programming Needs This (Challenge table) |
| 4 | Connecting Chapters 1-7 (full diagram) |
| 5 | The Real-World Workflow (11 steps) |
| 5 | Agent Architecture Overview (5 agents) |
| 6 | State Manager (pipeline phases, JSON persistence) |
| 7 | Spec Manager (version tracking, consistency) |
| 8 | Function Loader (registry -> agent code generation) |
| 9 | LLM Client (3 modes: LIVE / DRY_RUN / OFF) |
| 10 | Agent 1: Spec Builder |
| 11 | Agent 2: Spec Reviewer |
| 12 | Human Review Gate (decisions, not optional) |
| 13 | Agent 3: Production Programmer |
| 14 | Agent 4: QC Programmer (different model = genuine independence) |
| 15 | Agent 5: Validation Agent |
| 16 | Compare Module (comparison loop) |
| 17 | Pipeline Flow Diagram (full orchestrator) |
| 18 | Error Gates (where the pipeline stops) |
| 19 | Exercise C.1: Trace RACE |
| 20 | Exercise C.2: Deliberate Error |
| 21 | Exercise C.3: Add DTHFL |
| 22 | Exercise C.4: Design AE Extension |
| 23 | All Output Artifacts |
| 24 | Key Takeaways (5 bullets) |
| 25 | What's Next (extending, LLM mode, production use) |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| C.0: The Real Problem | 15 min | 0:15 |
| C.1: Connecting the Chapters | 30 min | 0:45 |
| C.2: Architecture Walkthrough | 60 min | 1:45 |
| -- Break -- | 15 min | 2:00 |
| C.3: Full Pipeline Run | 90 min | 3:30 |
| -- Lunch Break (if full day) -- | 45 min | 4:15 |
| C.4: Deep Dive Exercises | 120 min | 6:15 |
| -- Break -- | 10 min | 6:25 |
| Wrap-up + Discussion | 30 min | 6:55 |
