# AI Coding Assistants: Quick Comparison Reference

## The Landscape

```
                    Completion Mode              Agent Mode
                    (suggest next line)          (multi-step workflows)

  IDE-based         GitHub Copilot               Cursor Composer
  (in editor)       Cursor Tab                   Windsurf Cascade

  CLI-based         --                           Claude Code
  (terminal)                                     Gemini CLI
```

---

## Tool-by-Tool Summary

### Claude Code
| Aspect | Detail |
|--------|--------|
| **Type** | CLI agent (runs in terminal) |
| **Model** | Claude (Anthropic) |
| **Context system** | CLAUDE.md (project root) |
| **Key features** | Skills (slash commands), MCP (external tools), Hooks (security), Agentic execution |
| **Best for** | Multi-step automation, pipeline orchestration, batch operations |
| **Limitation** | No real-time editor integration; text-based interaction |

### Cursor
| Aspect | Detail |
|--------|--------|
| **Type** | IDE (VS Code fork) |
| **Model** | Multiple (Claude, GPT, etc.) |
| **Context system** | .cursorrules (project root) + codebase indexing |
| **Key features** | Composer (agent), inline edits (Ctrl+K), Tab completion, doc crawling |
| **Best for** | Interactive coding, refactoring, exploring unfamiliar code |
| **Limitation** | Limited multi-step automation; no built-in skill/hook system |

### GitHub Copilot
| Aspect | Detail |
|--------|--------|
| **Type** | IDE extension (VS Code, JetBrains, etc.) |
| **Model** | GPT / Claude (configurable) |
| **Context system** | Instructions files + workspace indexing |
| **Key features** | Inline completion, chat panel, code review |
| **Best for** | Line-by-line coding assistance, autocomplete |
| **Limitation** | Weaker agent capabilities; primarily completion-focused |

### Gemini CLI
| Aspect | Detail |
|--------|--------|
| **Type** | CLI agent (runs in terminal) |
| **Model** | Gemini (Google) |
| **Context system** | GEMINI.md (project root) |
| **Key features** | Google ecosystem integration, similar agent pattern to Claude Code |
| **Best for** | Teams in Google ecosystem; alternative to Claude Code |
| **Limitation** | Smaller tool ecosystem than Claude Code |

### Windsurf
| Aspect | Detail |
|--------|--------|
| **Type** | IDE (VS Code fork) |
| **Model** | Multiple |
| **Context system** | Rules files + codebase indexing |
| **Key features** | Cascade (agent mode), multi-file edits, flow-based workflows |
| **Best for** | Multi-file agent edits in an IDE environment |
| **Limitation** | Smaller community; fewer integrations |

---

## When to Use What: Clinical Programming Scenarios

| Scenario | Recommended Tool | Why |
|----------|-----------------|-----|
| Run the full SDTM pipeline (spec -> code -> QC -> validate) | **Claude Code** | Multi-step orchestration with skills |
| Explore an unfamiliar legacy SAS codebase | **Cursor** | Codebase indexing + chat |
| Write a new R function from a spec | **Either** | Both handle single-file creation well |
| Refactor an existing production R script | **Cursor** | Inline edits + visual diffs |
| Profile raw data and generate a quality report | **Claude Code** | `/profile-data` skill with data processing |
| Get autocomplete while typing R code | **Copilot** or **Cursor Tab** | Real-time completion |
| Validate a dataset against P21 rules | **Claude Code** | `/validate-dataset` skill |
| Research SDTM IG requirements grounded in your docs | **Claude Code + NotebookLM MCP** | Source-grounded retrieval |
| Quick one-line fix to a comment or variable name | **Cursor inline edit** | Ctrl+K, describe change, done |
| Batch rename a function across 10 files | **Cursor Composer** or **Claude Code** | Both handle multi-file edits |

---

## Key Concepts

### CLAUDE.md vs .cursorrules
Both serve the same purpose: persistent project context for the AI. CLAUDE.md is loaded by Claude Code; .cursorrules is loaded by Cursor. You can have both in the same project.

### Skills vs Composer
Claude Code skills are reusable markdown workflows (e.g., `/run-pipeline`). Cursor Composer is an interactive agent session. Skills are more repeatable and shareable; Composer is more flexible and improvisational.

### MCP vs Doc Crawling
Claude Code's MCP connects to external tools (NotebookLM, custom servers). Cursor's doc crawling indexes web-based documentation. Both provide external knowledge, but MCP is more structured and programmable.

### Hooks vs (nothing in Cursor)
Claude Code hooks enforce security and governance (block secret writes, log actions). Cursor has no equivalent -- you rely on VS Code extensions and .gitignore for governance.
