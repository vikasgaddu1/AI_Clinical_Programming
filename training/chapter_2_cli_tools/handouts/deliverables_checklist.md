# Chapter 2 Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Exercise 2.1: Explore the Project with Claude Code

- [ ] Ran `/check-environment` and recorded results
- [ ] Asked Claude to read and analyze raw_dm.csv
- [ ] Ran `/profile-data` and reviewed column-level statistics
- [ ] Compared Claude Code's data processing with NotebookLM's limitations (Ch.1)
- [ ] Asked Claude to summarize the function registry

## Exercise 2.2: NotebookLM MCP Integration

- [ ] Installed `notebooklm-mcp` server
- [ ] Authenticated with Google account
- [ ] Added Chapter 1 notebook to the library
- [ ] Successfully queried NotebookLM through Claude Code (at least 2 questions)
- [ ] Compared three grounding methods: NotebookLM MCP vs local MCP vs training data

## Exercise 2.3: Run the Pipeline

- [ ] Ran `/run-pipeline spec_build` successfully
- [ ] Examined the generated spec JSON (variable summary)
- [ ] Reviewed the RACE decision point with all options and pros/cons
- [ ] Understood the data flow: raw data + IG + registry -> draft spec

## Exercise 2.4: Write a Custom Skill

- [ ] Designed the `/compare-codelists` skill (planned all sections)
- [ ] Wrote the skill markdown file (or detailed draft)
- [ ] Reviewed against the template checklist (clear title, explicit paths, output format)
- [ ] (Optional) Tested the skill in Claude Code

## Exercise 2.5: Cursor Hands-On

- [ ] Opened the project in Cursor and waited for indexing
- [ ] Used codebase chat to ask 2 questions
- [ ] Used Composer to generate a code change (reviewed but rejected)
- [ ] Used inline edit (Ctrl+K) on a function (reviewed but rejected)

---

## Final Deliverables

### Custom Skill File
Save your `/compare-codelists` skill to: `.claude/skills/compare-codelists.md`

### Claude Code vs Cursor Comparison

When would you use **Claude Code**?
_________________________________________________________________
_________________________________________________________________

When would you use **Cursor**?
_________________________________________________________________
_________________________________________________________________

When would you use **both together**?
_________________________________________________________________
_________________________________________________________________

### NotebookLM MCP Reflection

How does connecting NotebookLM to Claude Code change your workflow?
_________________________________________________________________
_________________________________________________________________

When would you use NotebookLM MCP vs the local `sdtm_variable_lookup` tool vs the RAG system (Ch.3)?
_________________________________________________________________
_________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Using Claude Code to explore and profile data | [ ] | [ ] | [ ] |
| Running skills (slash commands) | [ ] | [ ] | [ ] |
| Understanding CLAUDE.md and how it works | [ ] | [ ] | [ ] |
| Connecting NotebookLM via MCP | [ ] | [ ] | [ ] |
| Understanding MCP tools vs skills | [ ] | [ ] | [ ] |
| Writing a custom skill | [ ] | [ ] | [ ] |
| Using Cursor for interactive coding | [ ] | [ ] | [ ] |
| Knowing when to use Claude Code vs Cursor | [ ] | [ ] | [ ] |
