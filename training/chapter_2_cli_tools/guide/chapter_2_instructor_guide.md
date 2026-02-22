# Chapter 2: AI Coding Assistants -- Claude Code & Cursor -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 4-5 hours |
| Format | Instructor-led workshop (live demos + guided exercises) |
| Audience | Clinical programmers who completed Chapter 1 |
| Prerequisites | Node.js 18+, Python 3.11+, R 4.x (recommended), VS Code, Cursor (free tier) |
| Materials | The full `AI_Clinical_Programming` project directory |

## Key Teaching Message

Chapter 1 showed you how to *understand* clinical documents with AI. Now you learn to *direct* AI coding tools -- reading data, writing scripts, automating multi-step workflows. You move from consumer to operator. By the end, you'll know when to use Claude Code (agentic, multi-step pipelines), Cursor (interactive, IDE-based coding), and how to extend them with custom skills, hooks, and MCP tools.

## Connection to Chapter 1

"In Chapter 1, you uploaded the protocol and SDTM IG to NotebookLM and got source-grounded answers. Today, we'll connect NotebookLM directly to Claude Code via MCP -- so Claude can query your NotebookLM notebooks programmatically for grounded answers while it writes code. The same zero-hallucination principle, but now accessible to a coding agent."

---

## Module 2.1: The AI Coding Landscape (30 min)

### Talking Points

1. **Start with the problem:**
   "You need to write an R script that reads raw_dm.csv, converts dates to ISO 8601, maps race values to CDISC controlled terminology, derives age, and outputs a Parquet file. NotebookLM can't do any of this. What tools can?"

2. **Introduce the landscape -- two dimensions:**

   **Paradigm: IDE-based vs CLI-based**
   - IDE-based: Cursor, Windsurf, GitHub Copilot -- live inside your editor, see your code in real-time
   - CLI-based: Claude Code, Gemini CLI -- run in the terminal, can execute multi-step workflows autonomously

   **Mode: Completion vs Agent**
   - Completion: suggest the next line of code (Copilot, Cursor Tab)
   - Agent: run entire multi-step workflows (Claude Code, Cursor Composer, Gemini CLI)

3. **Overview table (show on slide):**

   | Tool | Type | Agent? | Context System | Best For |
   |------|------|--------|----------------|----------|
   | Claude Code | CLI | Yes | CLAUDE.md + MCP + Skills | Pipeline automation, multi-file tasks |
   | Cursor | IDE (VS Code fork) | Yes (Composer) | .cursorrules + docs | Interactive coding, refactoring |
   | Windsurf | IDE | Yes (Cascade) | Rules + flows | Multi-file agent edits |
   | GitHub Copilot | IDE extension | Limited | Instructions files | Line-by-line completion |
   | Gemini CLI | CLI | Yes | GEMINI.md | Google ecosystem, alternative to Claude Code |

4. **When to use which:**
   - Quick edits, autocomplete: Copilot
   - Interactive coding, exploring unfamiliar code: Cursor
   - Multi-step automation, pipelines, orchestration: Claude Code
   - "Today we do deep dives on Claude Code and Cursor -- the two most relevant for clinical programming."

5. **No-code/low-code workflow orchestration:**

   Beyond coding tools, clinical programming teams increasingly encounter **workflow orchestration platforms** that connect systems without writing code:

   | Tool | Type | AI Integration | Clinical Use Case | Limitation |
   |------|------|---------------|-------------------|------------|
   | **n8n** | Open-source, self-hosted | LLM nodes, HTTP nodes | Trigger pipeline on new data drop, notify team on validation failure | Requires hosting, no built-in SDTM knowledge |
   | **Zapier** | Cloud SaaS | AI actions, 6000+ integrations | Connect study management to pipeline trigger, auto-notify on spec approval | Cloud-only, cost at scale, data residency concerns |
   | **Claude Code + hooks** | CLI, local | Native LLM agent | Full SDTM pipeline with code generation, MCP, skills | Requires CLI comfort, no visual dashboard |

   Key distinction: "n8n and Zapier are excellent for **connecting systems** -- trigger a pipeline when a file arrives, send a Slack message when validation fails, log results to a database. Claude Code is better for **doing the clinical programming work itself** -- generating R code, reviewing specs, running validation. In practice, you might use n8n or Zapier as the outer orchestration layer that triggers Claude Code pipelines."

   "We won't dive deep into these today, but be aware they exist. In the Capstone, we'll discuss how they could wrap around the orchestrator we build."

### Transition
"Let's start with Claude Code, since it powers the orchestrator we'll use in the Capstone."

---

## Module 2.2: Claude Code Deep Dive (90 min)

### 2.2.1 Architecture (15 min)

**Talking Points:**
- Claude Code is a CLI tool: you run it in the terminal, it creates an interactive session with Claude
- The model can read files, write files, execute bash commands, search code, and call external tools
- Every action is visible: you see exactly what files it reads, what commands it runs, what it writes
- You can approve or deny each action (permission modes)

**Live Demo:**
1. Open a terminal in the project directory
2. Run `claude` (or show how Claude Code starts)
3. Ask: "What files are in the study_data directory?"
4. Show Claude reading the directory, listing files, describing each one
5. Ask: "Read the first 10 rows of study_data/raw_dm.csv and tell me about the data"
6. Show Claude reading the file and producing a structured summary

### 2.2.2 CLAUDE.md -- The Project Brain (15 min)

**Talking Points:**
- `CLAUDE.md` at the project root is automatically loaded into every Claude Code session
- It serves as persistent context: project description, directory structure, conventions, instructions
- Claude reads it before answering any question -- this is how it "knows" your project

**Live Demo:**
1. Open `CLAUDE.md` and scroll through key sections:
   - Project description and purpose
   - Directory structure (the file tree)
   - Agent architecture (the 5 agents)
   - Configuration options
2. Ask Claude: "What agents are in the orchestrator?" -- observe it answers from CLAUDE.md context
3. Show that without CLAUDE.md, Claude would need to explore the codebase from scratch each time

**Best Practices:**
- Keep it concise -- long CLAUDE.md files waste context window
- Include: project structure, key conventions, file paths, workflow
- Don't include: full code listings, step-by-step tutorials

### 2.2.3 Skills / Slash Commands (20 min)

**Talking Points:**
- Skills are markdown files in `.claude/skills/` that define reusable workflows
- You invoke them with `/command-name` in Claude Code
- Each skill is a set of instructions Claude follows step-by-step
- This project has 5 skills: `/run-pipeline`, `/profile-data`, `/review-spec`, `/validate-dataset`, `/check-environment`

**Live Demo -- Anatomy of a Skill:**
1. Open `.claude/skills/check-environment.md`
2. Walk through the structure:
   - Title and description
   - Usage section (how to invoke)
   - Instructions (numbered steps Claude follows)
   - Output format (what the result looks like)
3. Run `/check-environment` live -- show Claude following each step
4. Show the pass/fail checklist output

**Second Demo:**
1. Run `/profile-data` on the raw data
2. Observe: Claude reads the CSV, computes frequencies, identifies data quality issues
3. Point out: "This is what NotebookLM *couldn't* do in Chapter 1 -- actual data processing"

### 2.2.4 MCP -- Model Context Protocol (20 min)

**Talking Points:**
- MCP is a protocol that lets AI models call external tools
- Tools return data *to* the model (unlike skills, which are instruction scripts)
- Configured in `.claude/mcp.json`
- This project has an MCP server (`mcp_server.py`) with 5 tools:

  | Tool | What It Returns |
  |------|----------------|
  | `sdtm_variable_lookup(domain, variable)` | IG definition + CT info for a variable |
  | `ct_lookup(codelist_code)` | Raw-to-CT value mappings for a codelist |
  | `profile_raw_data(csv_path)` | Variable types, distinct values, missing counts |
  | `query_function_registry(function_name)` | R function parameters and usage |
  | `read_spec(domain, approved)` | Mapping specification JSON |

**Live Demo:**
1. Open `.claude/mcp.json` -- show the configuration
2. Open `mcp_server.py` -- show how tools are defined (function name, parameters, return value)
3. Ask Claude: "Look up the RACE variable in the SDTM IG" -- observe it calling `sdtm_variable_lookup`
4. Ask Claude: "What are the CT mappings for codelist C66731?" -- observe `ct_lookup` being called
5. Key point: "MCP tools give Claude domain-specific knowledge it wouldn't otherwise have"

**MCP vs Skills:**
| | Skills | MCP Tools |
|--|--------|-----------|
| Format | Markdown instructions | Python/JS functions |
| Direction | Claude follows steps | Tool returns data to Claude |
| Trigger | User types `/command` | Claude decides when to call |
| Use case | Workflows (run pipeline, validate) | Knowledge retrieval (IG lookup, CT query) |

### 2.2.5 NotebookLM via MCP -- Bridging Chapter 1 (15 min)

**This is the new module connecting Ch.1 to Ch.2.**

**Talking Points:**
1. "In Chapter 1, you used NotebookLM in the browser to get source-grounded answers from the protocol and SDTM IG. What if Claude Code could do that same lookup programmatically?"

2. **NotebookLM MCP server:** The `notebooklm-mcp` package connects Claude Code to your NotebookLM notebooks
   - Install: `claude mcp add notebooklm npx notebooklm-mcp@latest`
   - It exposes tools: `ask_question`, `list_notebooks`, `select_notebook`, `add_notebook`
   - Authentication: one-time Google login via browser automation

3. **The architecture:**
   ```
   Your question -> Claude Code -> MCP -> NotebookLM -> Gemini (grounded in YOUR docs) -> cited answer -> Claude Code uses it
   ```

4. **Why this matters for clinical programming:**
   - Claude Code can research regulatory questions in your NotebookLM before writing code
   - Answers are grounded in the documents you uploaded -- no hallucinated IG content
   - "Research this in NotebookLM before coding" becomes a workflow pattern

5. **Two grounding strategies now available:**

   | Strategy | How | When to Use |
   |----------|-----|-------------|
   | NotebookLM MCP | Upload docs, query via MCP | Quick grounding, any document type |
   | Custom RAG (Ch.3) | Build your own search | Production, full control, offline, GxP |
   | Local MCP tools | `sdtm_variable_lookup` from mcp_server.py | Domain-specific, structured queries |

**Live Demo (if time permits):**
1. Show the install command: `claude mcp add notebooklm npx notebooklm-mcp@latest`
2. Show the authentication flow (browser opens for Google login)
3. Add the Chapter 1 notebook to the library
4. Ask Claude: "Using NotebookLM, what does the SDTM IG say about required DM variables?"
5. Show the grounded, cited response

**Note to instructor:** If live demo is impractical (network, auth issues), show screenshots or a pre-recorded video. The exercise (2.2) has participants try it themselves.

### 2.2.6 Hooks -- Security Enforcement (10 min)

**Talking Points:**
- Hooks are interceptors that run before/after Claude takes an action
- Configured in `.claude/settings.local.json`
- Types: `PreToolUse` (before action), `PostToolUse` (after action)
- Use cases: security (block secret writes), governance (log all file changes), safety (prevent production overwrites)

**Live Demo:**
1. Open `.claude/settings.local.json`
2. Walk through the existing hook:
   ```json
   "PreToolUse": [{
     "matcher": "Write",
     "hooks": [{
       "type": "intercept",
       "command": "python -c \"...checks for .env, api_key, credential, secret...\"",
       "description": "Block writing files that may contain secrets"
     }]
   }]
   ```
3. Explain: before Claude writes ANY file, this Python script runs. If the file path contains `.env`, `api_key`, `credential`, or `secret`, the write is blocked.
4. Demo: ask Claude to create a file called `test_api_key.txt` -- watch the hook block it.
5. Discuss: "What other hooks would be useful for clinical programming?"
   - Block writing to production dataset directories
   - Log all R script modifications
   - Validate that generated R scripts don't contain hardcoded paths

### Transition
"Claude Code is powerful for agentic, multi-step workflows. But sometimes you want a more interactive experience -- editing code in real-time, getting inline suggestions. That's where Cursor comes in."

---

## Module 2.3: Cursor Deep Dive (60 min)

### Talking Points

1. **What Cursor is:**
   - A VS Code fork with AI built into the editor
   - Uses the same extensions, themes, and keybindings as VS Code
   - Adds: AI chat, Composer (agent mode), inline edits, codebase indexing

2. **Key features for clinical programmers:**

   **.cursorrules (parallel to CLAUDE.md):**
   - A file at the project root that tells Cursor's AI about your project
   - Same purpose as CLAUDE.md: project context, conventions, file structure
   - Show: you could create a `.cursorrules` that mirrors the project description from CLAUDE.md

   **Codebase indexing:**
   - Cursor automatically indexes your entire project
   - The AI can answer questions about code it hasn't explicitly been shown
   - "Where is the function that converts dates to ISO 8601?" -- Cursor finds it

   **Composer (agent mode):**
   - Multi-file agent mode: describe what you want, Cursor creates/edits multiple files
   - Similar to Claude Code's agentic behavior, but inside the editor
   - You see diffs in real-time and can accept/reject each change

   **Inline edits:**
   - Select code, press Ctrl+K, describe the change
   - Cursor modifies just the selected code
   - Great for: renaming, adding comments, refactoring logic, fixing a single function

   **Doc crawling:**
   - Point Cursor at documentation URLs (e.g., CDISC website, R package docs)
   - It indexes the docs and uses them for grounded suggestions
   - Parallel to MCP in Claude Code: external knowledge sources

3. **Live Demo (in Cursor):**
   - Open the project in Cursor
   - Show the chat panel: ask "Explain how the production programmer agent works"
   - Show Composer: "Add a comment header to each R function file explaining its purpose"
   - Show inline edit: select the `iso_date` function body, press Ctrl+K, type "add input validation for empty strings"
   - Show codebase search: ask "Where is RACE mapping handled?"

### When Claude Code vs When Cursor

| Scenario | Use Claude Code | Use Cursor |
|----------|----------------|------------|
| Run the full SDTM pipeline | Yes -- multi-step automation | No |
| Explore an unfamiliar codebase | Possible, but Cursor is faster | Yes -- codebase indexing |
| Write a new R function from spec | Both work | Both work |
| Refactor existing production code | Possible | Yes -- inline edits + diffs |
| Configure hooks and MCP | Yes -- it's Claude Code's system | No |
| Interactive pair programming | Slower (CLI round-trips) | Yes -- real-time in editor |
| Automate validation + reporting | Yes -- skills + MCP | Limited |

### Transition
"Now it's time to get hands-on. You'll explore the project with Claude Code, connect NotebookLM via MCP, run the pipeline, write a custom skill, and try Cursor."

---

## Module 2.4: Hands-On Exercises (90 min)

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| 2.1: Explore the Project with Claude Code | 20 min | File reading, data profiling, slash commands |
| 2.2: NotebookLM MCP Integration | 20 min | Connect NotebookLM to Claude Code, grounded queries |
| 2.3: Run the Pipeline | 20 min | `/run-pipeline`, examine artifacts |
| 2.4: Write a Custom Skill | 20 min | Create `/compare-codelists` skill |
| 2.5: Cursor Hands-On | 15 min | Composer, inline edits, codebase search |

### Facilitation Tips

- **Exercise 2.2 (NotebookLM MCP):** Requires internet access and Google authentication. Have a backup plan (screenshots, pre-recorded demo) in case of network issues. Participants need the NotebookLM notebook from Chapter 1.
- **Exercise 2.3:** The pipeline runs in template mode (`use_llm: false`) so no API key is needed. If R is not installed, the pipeline will stop at the production stage -- that's OK for the exercise, the spec_build stage still works.
- **Exercise 2.4:** Participants write a skill markdown file, not Python code. Provide the template handout. Review 2-3 participant skills as a group to discuss what makes a good skill.
- **Exercise 2.5:** Cursor free tier has limited AI usage. If limits are hit, have participants observe the instructor demo instead.

---

## Wrap-Up (15 min)

### Discussion Points

1. "What surprised you most about what Claude Code can do?"
2. "When would you use Claude Code vs Cursor in your daily work?"
3. "How does the NotebookLM MCP change your thinking about AI hallucination?"

### Preview Chapter 3

"Claude Code's MCP tools like `sdtm_variable_lookup` gave the AI access to SDTM IG knowledge. The NotebookLM MCP gave it grounded answers from your uploaded documents. But how do these knowledge retrieval systems work under the hood? In Chapter 3, we build a RAG system from scratch -- chunking, embeddings, vector search -- to understand exactly how grounded retrieval works and to build one you fully control."

---

## Slide Deck Outline (for `slides/chapter_2_slides.pptx`)

| Slide # | Title | Content |
|---------|-------|---------|
| 1 | Title | "Chapter 2: AI Coding Assistants -- Claude Code & Cursor" |
| 2 | Learning Objectives | 5 objectives |
| 3 | The Problem | "You need to write R code, process data, automate pipelines" |
| 4 | AI Coding Landscape | 2x2 grid: IDE/CLI x Completion/Agent |
| 5 | Tool Comparison Table | Claude Code, Cursor, Windsurf, Copilot, Gemini CLI |
| 5b | Workflow Orchestration | n8n, Zapier vs Claude Code -- connecting systems vs doing the work |
| 6 | Claude Code: What It Is | CLI agent, reads/writes/executes, agentic |
| 7 | CLAUDE.md | The project brain, persistent context |
| 8 | CLAUDE.md Example | Key sections from this project's CLAUDE.md |
| 9 | Skills Overview | 5 slash commands, markdown-based |
| 10 | Skill Anatomy | Walkthrough of `/check-environment` structure |
| 11 | Skills in Action | Screenshot of `/profile-data` output |
| 12 | MCP: What It Is | Protocol for external tool access |
| 13 | MCP Tools in This Project | Table of 5 tools with descriptions |
| 14 | MCP vs Skills | Comparison table |
| 15 | NotebookLM via MCP | Architecture diagram: Claude Code -> MCP -> NotebookLM -> Gemini (grounded) |
| 16 | NotebookLM MCP Setup | Install command, auth flow, usage |
| 17 | Two Grounding Strategies | NotebookLM MCP vs Custom RAG vs Local MCP tools |
| 18 | Hooks: Security Enforcement | PreToolUse example, clinical programming use cases |
| 19 | Cursor: What It Is | VS Code fork, codebase indexing, Composer |
| 20 | Cursor Key Features | .cursorrules, inline edits, doc crawling |
| 21 | Claude Code vs Cursor | When-to-use comparison table |
| 22 | Exercise 2.1 | Explore with Claude Code |
| 23 | Exercise 2.2 | NotebookLM MCP Integration |
| 24 | Exercise 2.3 | Run the Pipeline |
| 25 | Exercise 2.4 | Write a Custom Skill |
| 26 | Exercise 2.5 | Cursor Hands-On |
| 27 | Deliverables | Checklist |
| 28 | Key Takeaways | 3 bullets: agentic AI, MCP grounding, right tool for the job |
| 29 | What's Next | Chapter 3: Building a RAG System |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 2.1: AI Coding Landscape | 30 min | 0:30 |
| 2.2: Claude Code Deep Dive | 90 min | 2:00 |
| -- Break -- | 15 min | 2:15 |
| 2.3: Cursor Deep Dive | 60 min | 3:15 |
| -- Break -- | 10 min | 3:25 |
| 2.4: Exercises | 90 min | 4:55 |
| Wrap-up + Q&A | 15 min | 5:10 |
