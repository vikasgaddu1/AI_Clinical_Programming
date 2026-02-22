# Vibe Coding Quick Reference

## What is Vibe Coding?

AI-directed development: start with intent, direct AI to build it, iterate until it's right. The key skill isn't writing code -- it's communicating clearly with AI.

---

## Plan Mode

### When to Use Plan Mode

| Situation | Use Plan Mode? |
|-----------|:-------------:|
| New feature or tool (TLF search app, new agent) | Yes |
| Multi-file change (spec + code + validation) | Yes |
| You're not sure of the approach | Yes |
| Simple one-line fix (typo, wrong codelist code) | No |
| Adding a comment or docstring | No |

### Plan Mode Flow

```
1. ENTER   — Enter plan mode
2. PROMPT  — Describe what you want to build
3. EXPLORE — Claude reads files, discovers patterns, identifies constraints
4. PLAN    — Claude proposes architecture and implementation steps
5. REVIEW  — You check: does this make sense? any missing requirements?
6. APPROVE — You approve (or ask for changes)
7. EXECUTE — Claude implements the plan
```

### Plan Mode Tips

- Give context: "Follow the pattern in sdtm_ig_db/setup_db.py"
- Name constraints: "Must work without an API key (mock embeddings)"
- State what you DON'T want: "Don't modify existing files, only create new ones"
- Ask questions during review: "Why did you choose this approach over X?"

---

## Five Clinical Prompting Patterns

### 1. Spec-First
**When:** You have a mapping specification.
**Template:** "Read the approved spec at [path]. Implement the [VARIABLE] mapping using [function] with codelist [code]."

### 2. IG-Grounded
**When:** You need standards compliance.
**Template:** "Look up [VARIABLE] in the SDTM IG (use sdtm_variable_lookup or read dm_domain.md). What controlled terminology applies? Is it required or permissible?"

### 3. SAP-to-Code
**When:** You have analysis requirements but no code.
**Template:** "The SAP Section [X] says [table description]. Read [dataset] and generate an R script that produces this [table/figure/listing]."

### 4. Error-Driven
**When:** Something failed.
**Template:** "I ran [script/command] and got this error: [error]. The script was supposed to [intent]. Here's the relevant code: [snippet]. What went wrong?"

### 5. Iterative Refinement
**When:** First attempt needs work.
**Template:** "Good start. Now: (1) [specific change], (2) [specific change], (3) [specific change]."

---

## Debugging Formula

```
Error message + Context + Intent = AI can fix it
```

| Component | What to Include | Example |
|-----------|----------------|---------|
| **Error** | Exact error text | "Error in assign_ct: codelist 'C66732' not found in lookup" |
| **Context** | What you were doing, what inputs | "Running dm_production.R on raw_dm.csv, mapping SEX variable" |
| **Intent** | What the correct behavior should be | "SEX should map to M/F/U using codelist C66731" |

### Common Clinical Debugging Scenarios

| Scenario | What to Show AI |
|----------|----------------|
| R script error | Error message + relevant code section + function registry entry |
| All NAs after CT mapping | Codelist code + sample raw values + ct_lookup.csv entries |
| Wrong AGE values | derive_age() parameter order + BRTHDTC/RFSTDTC sample values |
| Comparison mismatch | dm_compare_report.txt + specific variable diffs |
| Pipeline stage failure | pipeline_state.json error_log + stage name |

---

## Agent vs Skill vs Team

| | Agent | Skill | Team |
|--|-------|-------|------|
| **What** | Specialist persona | Reusable workflow | Parallel collaborators |
| **Lives in** | `.claude/agents/*/AGENT.md` | `.claude/skills/*/SKILL.md` | Session only |
| **Invoked by** | Claude delegates automatically | User types `/command` | User creates team |
| **Persistence** | Permanent | Permanent | Session only |
| **Best for** | Recurring expert tasks | Standard procedures | Research, exploration |
| **Example** | QC programmer reviews code | `/validate-dataset` checks P21 rules | 3 researchers explore approaches |

### Agent Design Checklist

- [ ] `name`: lowercase, hyphenated (e.g., `tlf-reviewer`)
- [ ] `description`: when Claude should delegate to this agent
- [ ] `model`: opus (critical), sonnet (standard), haiku (lightweight)
- [ ] `tools`: minimum set needed (don't give Write unless necessary)
- [ ] Persona: specific role, not generic "helpful assistant"
- [ ] Key files: list the files this agent needs
- [ ] Checklist: what does it check or produce?
- [ ] Output format: how does it report findings?

### Skill Design Checklist

- [ ] Title and description
- [ ] Usage section with example invocation
- [ ] Numbered instructions (Claude follows step-by-step)
- [ ] Output format section
- [ ] Error handling (what if prerequisites are missing?)

---

## The Vibe Coding Mindset

```
Traditional:   Read requirements → Write code → Debug → Iterate
Vibe coding:   Describe intent → Plan with AI → AI writes code → Review → Refine
```

**Key shifts:**
- From "writing code" to "directing AI"
- From "knowing every function" to "knowing what to ask for"
- From "debugging alone" to "debugging collaboratively"
- From "one-off scripts" to "building agents and skills that compound"
