# Chapter 6: Vibe Coding for Clinical Programmers -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 5-6 hours (full day or 2 half-day sessions) |
| Format | Instructor-led workshop (demos + guided exercises + live build) |
| Audience | Clinical programmers who completed Chapters 1-5 |
| Prerequisites | Python 3.11+, Node.js 18+, PostgreSQL (recommended), R 4.x (recommended) |
| Materials | Full `AI_Clinical_Programming` project, Claude Code installed |

## Key Teaching Message

You don't need to know every line of code before you start. Vibe coding is AI-directed development: start with intent, use plan mode to think through architecture, prompt effectively, debug collaboratively, and build extensibility into your tools. This chapter teaches you to go from "the SAP says Table 14.1.1 shows demographics by treatment arm" to working code -- using AI as your pair programmer.

## Connection to Previous Chapters

"In Chapter 2, you learned to operate Claude Code -- skills, MCP, hooks. In Chapter 3, you built a RAG system. In Chapter 5, you managed packages. Now you put it all together: you'll use plan mode to think before coding, effective prompts to direct AI, and you'll build custom agents and skills that make your AI smarter over time. The TLF search tool we build today reuses the RAG patterns from Chapter 3, and the agents/skills you create here are the same patterns the Capstone orchestrator relies on."

---

## Module 6.1: What is Vibe Coding? (30 min)

### Talking Points

1. **Define vibe coding:**
   "Vibe coding means starting with intent -- not syntax. You describe what you want to build, and AI helps you get there. The key skill isn't writing code; it's directing AI clearly."

2. **The spectrum of clarity:**

   | Starting Point | Example | Approach |
   |---------------|---------|----------|
   | **Crystal clear** | "Map SEX from raw values to C66731 using assign_ct()" | Direct prompt, AI executes |
   | **Mostly clear** | "I need a demographics summary table like the SAP describes" | Spec-first prompt, AI fills gaps |
   | **Rough vision** | "I want a tool that helps me find similar TLFs across studies" | Plan mode, iterate, refine |
   | **Just an idea** | "There must be a better way to track our TLF inventory" | Explore with AI, shape the vision together |

   "All four starting points are valid. The skill is knowing which approach to use."

3. **Plan mode as the key discipline:**
   - Plan mode forces you to explore the codebase and design before writing
   - Claude reads files, understands patterns, then proposes an architecture
   - You review the plan, ask questions, and approve before any code is written
   - This prevents the #1 vibe coding failure: AI writes 500 lines in the wrong direction

4. **"It's OK to not have 100% clear vision":**
   - The plan sharpens through exploration
   - AI discovers constraints you didn't know about (missing files, wrong formats, dependency issues)
   - Each iteration brings more clarity

5. **Clinical context:**
   "The SAP says Table 14.1.1 shows demographics by treatment arm. That's your vibe. Plan mode helps you figure out: which dataset? which variables? what statistical tests? what footnotes? Then AI generates the code."

### Live Demo: Plan Mode (10 min)

1. Open Claude Code in the project directory
2. Enter plan mode (show the UI/command)
3. Prompt: "I want a script that reads raw_dm.csv, identifies all subjects with partial birth dates, and generates a report showing what imputation decisions are needed."
4. Walk through what Claude does:
   - Reads `raw_dm.csv` to understand the data
   - Reads `sdtm_ig_db/sdtm_ig_content/dm_domain.md` for BRTHDTC rules
   - Proposes a plan: read CSV, detect partial dates, categorize by type (YYYY only, YYYY-MM, missing), output report
5. Approve the plan
6. Watch Claude implement it
7. Key point: "Notice how the plan caught the need to check multiple date formats? That's why we plan first."

### Transition
"Now that you understand the philosophy, let's get specific about prompting techniques."

---

## Module 6.2: Prompting for Clinical Programming (45 min)

### Talking Points

1. **Context is king:**
   - CLAUDE.md gives AI your project structure and conventions
   - MCP tools (`sdtm_variable_lookup`, `ct_lookup`) give domain-specific knowledge
   - Study documents (protocol, SAP, annotated CRF) ground everything in your study
   - "The quality of AI output is directly proportional to the context you provide."

2. **Five clinical prompting patterns:**

   | Pattern | When to Use | Example Prompt |
   |---------|------------|----------------|
   | **Spec-first** | You have a mapping spec | "Implement the SEX variable mapping from the approved spec. Use assign_ct() with codelist C66731." |
   | **IG-grounded** | You need standards compliance | "Look up RACE in the SDTM IG using the sdtm_variable_lookup tool and tell me the valid controlled terminology values." |
   | **SAP-to-code** | You have analysis requirements | "The SAP Section 8.1 says Table 14.1.1 shows demographics by treatment arm. Generate an R script that reads dm.parquet and produces this table." |
   | **Error-driven** | Something failed | "Here's the R error from running dm_production.R. The script was supposed to derive AGE from BRTHDTC and RFSTDTC using derive_age(). What went wrong?" |
   | **Iterative refinement** | First attempt needs work | "Good start on the demographics table. Now add: (1) p-values for chi-square test on categorical variables, (2) a footnote explaining the population, (3) column headers matching SAP format." |

3. **Anti-patterns to avoid:**

   | Bad Prompt | Why It Fails | Better Prompt |
   |-----------|-------------|---------------|
   | "Write SDTM code" | No context, no specificity | "Implement the DM domain from the approved spec at outputs/specs/dm_mapping_spec_approved.json" |
   | "Fix this" (paste 200 lines) | Too much code, no focus | "Line 45 throws an error when BRTHDT is missing. Here's the error message: ..." |
   | "Make it perfect" | Undefined quality bar | "Add validation: check that all SEX values are in {M, F, U} after CT mapping" |

### Live Demo: Prompting Comparison (15 min)

Show the same task with a weak prompt vs a strong prompt:

**Task:** Generate an R script that summarizes treatment arm distribution.

**Weak prompt:** "Write R code for treatment arms"
- Show the vague, possibly wrong output

**Strong prompt:** "Read study_data/raw_dm.csv. Count subjects per ARMCD value. Use the ct_lookup for ARMCD mapping. Output a formatted table with columns: Arm Code, Arm Description, N, Percentage. Save as a CSV to orchestrator/outputs/."
- Show the focused, correct output

"Same task. Different prompts. Different results."

### Transition
"Good prompts get you 80% there. The other 20% is debugging. Let's talk about that."

---

## Module 6.3: Debugging with AI (30 min)

### Talking Points

1. **The debugging formula:**
   ```
   Error message + Context + Intent = AI can fix it
   ```
   - Error message: what went wrong (paste the actual error)
   - Context: what you were trying to do, what inputs you used
   - Intent: what the correct behavior should be

2. **Three debugging patterns:**

   **Pattern 1: R script errors**
   - Paste the error + relevant code section
   - Tell AI what the code should do
   - Example: "iso_date('03/04/2020') returned '2020-03-04' but I expected '2020-04-03' because this is UK date format"

   **Pattern 2: Data mismatches (production vs QC)**
   - Show the comparison report
   - AI traces which variable diverged
   - Example: "The dm_compare_report.txt shows 15 mismatches in AGE. Production has 67 for subject 101-001, QC has 68."

   **Pattern 3: Pipeline failures**
   - Show pipeline state + error log
   - AI diagnoses which stage failed and why
   - Example: "The pipeline stopped at the production stage. Here's the error from pipeline_state.json."

3. **Key principle:** "Don't just paste the error. Give context."

### Live Demo: Deliberate Bug (15 min)

1. Show a modified `dm_production.R` with a planted bug (wrong codelist code: C66732 instead of C66731 for SEX)
2. Run it: `Rscript dm_production.R`
3. Show the error or unexpected output
4. Prompt Claude: "I ran dm_production.R and SEX values are all unmapped. The spec says codelist C66731 for SEX. Here's the relevant section of the R script: [paste]. What's wrong?"
5. Watch Claude identify the typo
6. Fix and re-run

### Transition
"So far we've been using Claude Code's built-in capabilities. Now let's make it smarter by building custom agents and skills."

---

## Module 6.4: Building Your AI Team (60 min)

### Talking Points

1. **Three extensibility mechanisms:**

   | Mechanism | What It Is | Lives In | When to Use |
   |-----------|-----------|----------|------------|
   | **Agents** | Specialist personas with expertise | `.claude/agents/*/AGENT.md` | Recurring specialized tasks |
   | **Skills** | Reusable multi-step workflows | `.claude/skills/*/SKILL.md` | Procedures anyone should run the same way |
   | **Teams** | Multiple agents working in parallel | Session-only (experimental) | Complex research, competing hypotheses |

2. **Agent anatomy:**
   ```markdown
   ---
   name: biostatistician
   description: Reviews SDTM/ADaM datasets for SAP alignment
   tools: Read, Grep, Glob, Bash, WebFetch
   model: opus
   ---

   You are a Senior Biostatistician...
   [persona + instructions + key files + review checklist]
   ```

   Key design decisions:
   - **Model selection:** Opus for critical/independent roles (QC, biostat), Sonnet for production, Haiku for lightweight auditing
   - **Tool restrictions:** Only give agents the tools they need
   - **Persona matters:** A QC programmer thinks differently than a production programmer -- encode that difference

3. **Walk through existing agents (show on screen):**

   | Agent | Model | Persona |
   |-------|-------|---------|
   | production-programmer | Sonnet | By-the-book, follows spec exactly |
   | qc-programmer | Opus | Critical eye, challenges assumptions |
   | biostatistician | Opus | SAP alignment, analysis readiness |
   | spec-analyzer | Sonnet | CDISC compliance, completeness |
   | data-validator | Sonnet | P21 checks, variable validation |
   | function-auditor | Haiku | Registry alignment, R function testing |
   | training-reviewer | Sonnet | Content accuracy, cross-chapter consistency |
   | pipeline-runner | Sonnet | Pipeline execution, troubleshooting |

4. **Skill anatomy:**
   ```markdown
   # Skill Title

   Description of what this skill does.

   ## Usage
   `/skill-name [args]`

   ## Instructions
   1. Step one...
   2. Step two...
   3. Step three...
   ```

   Walk through `/run-pipeline`, `/validate-dataset`, `/profile-data` as examples.

5. **Agent teams:**
   - Enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in settings.local.json
   - `teammateMode: "in-process"` -- all teammates in same terminal
   - Spawn teammates for parallel research: "Create a team with 2 researchers -- one explores approach A, one explores approach B"
   - Teams are session-only; agents and skills persist across sessions

### Live Demo: Create an Agent + Skill (20 min)

**Create a new agent:**
1. Create `.claude/agents/tlf-reviewer/AGENT.md`
2. Define frontmatter: name, description, model (opus), tools
3. Write the persona: "You are a TLF reviewer who checks outputs against the SAP..."
4. Test it by asking Claude to delegate a task to the new agent

**Create a new skill:**
1. Create `.claude/skills/search-tlf/SKILL.md`
2. Define usage and instructions
3. Show the skill appearing in the `/` menu (after restart)

### Transition
"You now know how to extend Claude Code with custom agents and skills. Let's put everything together by building a real clinical tool."

---

## Module 6.5: Demo -- Building the TLF Search Tool (90 min)

### The Vision (5 min)

"Every stats programmer has this problem: you need to create Table 14.2.3 -- Summary of AEs by Severity. Has anyone at your company created a similar table before? Which study? Which program? You end up searching through shared drives, asking colleagues, or starting from scratch."

"We're going to build a tool that solves this. It scans TLF outputs, extracts titles and footnotes, stores them in PostgreSQL with vector embeddings, and lets you search semantically. Ask 'adverse event severity summary' and it finds Table 14.2.3 from Study ABC-2024-001."

### Pre-Demo Setup (5 min)

Show the scaffold already in place:
- `tlf_search_app/README.md` -- architecture and purpose
- `tlf_search_app/config.py` -- database config (already works)
- `tlf_search_app/setup_db.py` -- schema (already works)
- `tlf_search_app/sample_data/tlf_catalog.csv` -- 35 realistic TLF entries
- `tlf_search_app/load_tlfs.py` -- stub with docstrings, no implementation
- `tlf_search_app/search_tlfs.py` -- stub with docstrings, no implementation

"The schema and sample data are ready. The implementation stubs are empty. We'll fill them in live using everything we learned today."

### Step 1: Plan Phase (15 min)

Enter plan mode:
"I want to implement load_tlfs.py. It should read tlf_catalog.csv, generate embeddings for each TLF's title + footnotes combined, and insert everything into the tlf_outputs table in PostgreSQL. Use mock embeddings like sdtm_ig_db/load_sdtm_ig.py does."

Walk through the plan Claude generates. Point out:
- It discovers the existing EmbeddingGenerator pattern in `sdtm_ig_db/load_sdtm_ig.py`
- It reads the schema from `setup_db.py` to understand the table structure
- It proposes: read CSV with pandas, concatenate title+footnotes for embedding text, generate mock embeddings, batch insert

Approve and proceed.

### Step 2: Schema Setup (10 min)

```bash
cd training/chapter_6_vibe_coding/tlf_search_app
python setup_db.py
```

Show the table created. If PostgreSQL isn't available, show the SQL and explain what it would create.

### Step 3: Implement load_tlfs.py (25 min)

Let Claude implement the loader. Show:
- How it reads the existing pattern from `sdtm_ig_db/load_sdtm_ig.py`
- Iterative prompting: "Good, but also handle missing footnotes gracefully"
- The prompt→review→refine cycle in action

### Step 4: Implement search_tlfs.py (25 min)

"Now implement search_tlfs.py. It should take a natural language query, embed it, find the top 5 most similar TLFs by cosine similarity, and print: output number, title, program name, and similarity score."

Show:
- AI reusing the query pattern from `sdtm_ig_db/query_ig.py`
- Debugging when the first query returns unexpected results
- Refining the output format

### Step 5: Test It (15 min)

```bash
python load_tlfs.py
python search_tlfs.py "demographics summary by treatment"
python search_tlfs.py "adverse event severity"
python search_tlfs.py "Kaplan-Meier survival"
```

Show results. Discuss:
- "demographics summary" finds Table 14.1.1 -- correct!
- "adverse event severity" finds Table 14.2.3 -- correct!
- "How would this help you in your daily work?"

### Key Teaching Moments

Throughout the demo, explicitly call out:
- "I started in plan mode -- I didn't just say 'write it'"
- "I gave context: 'follow the pattern in sdtm_ig_db/load_sdtm_ig.py'"
- "When the query didn't work, I showed Claude the error + what I expected"
- "This entire app was built using the patterns you learned today"

---

## Module 6.6: Hands-On Exercises (90 min)

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| 6.1: Plan Mode Practice | 20 min | Design before coding |
| 6.2: Prompting Patterns | 20 min | Five clinical prompting patterns |
| 6.3: Debug a Broken Script | 20 min | AI-assisted debugging |
| 6.4: Build Agent + Skill | 30 min | Extend Claude Code |
| 6.5: TLF Search Tool | 30 min | Extend the demo app |

Participants should do at least exercises 6.1-6.3. Exercises 6.4 and 6.5 are for those who finish early or want deeper engagement.

### Facilitation Tips

- **Exercise 6.1:** Emphasize that the plan is the deliverable, not the code. Review 2-3 participant plans as a group.
- **Exercise 6.2:** Pair participants to compare prompt quality. Have them try the same task with different prompts and compare outputs.
- **Exercise 6.3:** The broken script has 3 bugs. Some participants will find all 3 quickly; challenge them to also explain WHY each bug produced the error it did.
- **Exercise 6.4:** Provide the reference solution after 20 minutes so participants can compare their agent/skill design with the example.
- **Exercise 6.5:** This requires PostgreSQL. If unavailable, have participants do Option C (design the MCP tool on paper using plan mode).

---

## Wrap-Up (15 min)

### Group Discussion

1. "How does plan mode change your approach to starting a new programming task?"
2. "Which prompting pattern do you think you'll use most in your daily work?"
3. "Where would custom agents be most useful at your organization?"
4. "How would the TLF search tool change how your team starts new studies?"

### Key Takeaways

1. **Plan before you code** -- plan mode prevents wasted iterations and catches edge cases early
2. **Context determines quality** -- CLAUDE.md, MCP tools, and study docs are your secret weapon
3. **Debug collaboratively** -- error message + context + intent = AI can fix it
4. **Build your AI team** -- agents encode expertise, skills encode procedures, teams enable parallel work
5. **Vibe coding is a skill** -- the more you practice prompting and iterating, the better you get

### Preview Capstone

"In the Capstone, you'll see all of this at scale: 5 agents with different personas, a full pipeline orchestrated by Python, plan-mode thinking baked into every agent's design. The TLF search tool you explored today is the same RAG pattern the orchestrator uses to query the SDTM IG. Everything connects."

---

## Slide Deck Outline (for `slides/chapter_6_slides.pptx`)

| Slide # | Title |
|---------|-------|
| 1 | Title: "Chapter 6: Vibe Coding for Clinical Programmers" |
| 2 | Learning Objectives (6 items) |
| 3 | What is Vibe Coding? (definition + spectrum of clarity) |
| 4 | Plan Mode: Think Before You Code |
| 5 | Plan Mode Demo: Design -> Approve -> Execute |
| 6 | Five Clinical Prompting Patterns (table) |
| 7 | Pattern Deep Dive: Spec-First vs SAP-to-Code |
| 8 | Context is King: CLAUDE.md + MCP + Study Docs |
| 9 | Prompting Anti-Patterns (what not to do) |
| 10 | Debugging with AI: Error + Context + Intent |
| 11 | Three Debug Patterns (R errors, data mismatch, pipeline failure) |
| 12 | Building Your AI Team: Agents vs Skills vs Teams |
| 13 | Agent Anatomy: AGENT.md frontmatter + persona |
| 14 | Skill Anatomy: SKILL.md procedure + steps |
| 15 | Agent Teams: Parallel Collaboration (experimental) |
| 16 | Our 8 Agents + 7 Skills (roster table) |
| 17 | Demo: TLF Search Tool -- The Vision |
| 18 | TLF Search Tool Architecture (PostgreSQL + pgvector + embeddings) |
| 19 | Live Build: Plan -> Schema -> Loader -> Search |
| 20 | Exercise 6.1: Plan Mode Practice |
| 21 | Exercise 6.2: Prompting Patterns |
| 22 | Exercise 6.3: Debug a Broken Script |
| 23 | Exercise 6.4: Build Agent + Skill |
| 24 | Exercise 6.5: TLF Search Tool Extension |
| 25 | Key Takeaways (5 bullets) |
| 26 | What's Next: Capstone |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 6.1: What is Vibe Coding? | 30 min | 0:30 |
| 6.2: Prompting for Clinical Programming | 45 min | 1:15 |
| -- Break -- | 15 min | 1:30 |
| 6.3: Debugging with AI | 30 min | 2:00 |
| 6.4: Building Your AI Team | 60 min | 3:00 |
| -- Break -- | 15 min | 3:15 |
| 6.5: Demo -- TLF Search Tool | 90 min | 4:45 |
| -- Break -- | 10 min | 4:55 |
| 6.6: Hands-On Exercises | 90 min | 6:25 |
| Wrap-Up + Discussion | 15 min | 6:40 |
