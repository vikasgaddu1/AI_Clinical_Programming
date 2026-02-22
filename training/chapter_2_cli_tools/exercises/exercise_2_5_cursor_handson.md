# Exercise 2.5: Cursor Hands-On

## Objective
Experience Cursor's IDE-based AI features -- Composer (agent mode), inline edits, and codebase search. Compare the interactive editing experience with Claude Code's CLI-based approach.

## Time: 15 minutes

## Prerequisites
- Cursor installed (free tier: https://cursor.com)
- The `AI_Clinical_Programming` project directory

---

## Steps

### Step 1: Open the Project in Cursor

1. Launch Cursor
2. Open the `AI_Clinical_Programming` folder (File > Open Folder)
3. Wait for Cursor to index the codebase (you'll see an indexing indicator)

### Step 2: Codebase Chat

Open the AI chat panel (Ctrl+L or Cmd+L) and ask:

**Question 1:**
```
How does the production programmer agent generate R code? Trace the flow from spec to R script.
```

> Observe: Cursor searches the indexed codebase and answers with specific file references.
>
> Which files did Cursor reference?
> _________________________________________________________________

**Question 2:**
```
Where is the RACE mapping handled in this codebase?
```

> Which files and line numbers did Cursor find?
> _________________________________________________________________

### Step 3: Composer (Agent Mode)

Open Composer (Ctrl+I or Cmd+I) and type:
```
Add a descriptive comment block at the top of r_functions/iso_date.R explaining what the function does, its parameters, return value, and a usage example
```

Observe:
1. Cursor shows you a diff of the proposed change
2. You can review line by line
3. You accept or reject the change

> Did Composer produce a reasonable comment block? Yes / No
>
> Were the parameter descriptions accurate? Yes / No
>
> **Important:** Reject the change (click "Reject" or press Escape) -- we don't want to modify the actual code.

### Step 4: Inline Edit

1. Open `r_functions/iso_date.R` in the editor
2. Select the function signature line (the `iso_date <- function(...)` line)
3. Press Ctrl+K (or Cmd+K) to open inline edit
4. Type: `Add input validation: if date_col is not character, stop with an error message`
5. Review the suggested code

> Did Cursor suggest reasonable input validation? Yes / No
>
> Where did it insert the validation code?
> _________________________________________________________________
>
> **Important:** Press Escape to reject -- don't save the change.

### Step 5: Compare with Claude Code

Reflect on how the same tasks differ between tools:

| Task | Claude Code Experience | Cursor Experience |
|------|----------------------|-------------------|
| "Explain the production programmer" | CLI text response | Chat panel with file links |
| "Add comments to iso_date.R" | Writes file directly (approve/deny) | Shows diff in editor (accept/reject) |
| "Find where RACE is handled" | Searches files, reports results | Indexed search, inline file navigation |
| "Run the pipeline" | `/run-pipeline` executes directly | Would need terminal integration |

> Which tool felt more natural for exploration?
> _________________________________________________________________
>
> Which tool felt more natural for making code changes?
> _________________________________________________________________
>
> Which tool would you use for running multi-step pipelines?
> _________________________________________________________________

---

## Optional: Create .cursorrules

If time permits, create a `.cursorrules` file for the project (Cursor's equivalent of `CLAUDE.md`):

1. Create a new file `.cursorrules` in the project root
2. Add a brief project description:
   ```
   This is an SDTM Agentic Orchestrator for clinical trial data programming.
   The primary language is Python (orchestrator) with R (data transformation).
   Key directories: orchestrator/ (agents, core), r_functions/ (R library), study_data/ (raw data).
   The mapping specification in outputs/specs/ is the single source of truth.
   ```
3. Ask Cursor a question and see if the context improves

---

## Reflection Questions

1. How does Cursor's inline diff compare to Claude Code writing files directly?
2. When would the IDE experience be better than the CLI? When would CLI be better?
3. Could you use both tools on the same project? (Yes -- they don't conflict)

---

## What You Should Have at the End

- [ ] Successfully queried Cursor's codebase chat (2 questions)
- [ ] Used Composer to generate a code change (reviewed but rejected)
- [ ] Used inline edit on a function (reviewed but rejected)
- [ ] Written comparison of Claude Code vs Cursor workflows
