# Exercise 6.4: Build a Custom Agent and Skill

## Objective
Create a new agent definition and a new skill for the project. Reference the existing 8 agents and 7 skills as templates.

## Time: 30 minutes

---

## Part A: Create a Custom Agent (15 min)

### Step 1: Study an Existing Agent

Read one of the existing agents to understand the pattern:

```bash
# Pick one to read:
# .claude/agents/biostatistician/AGENT.md  (complex persona, opus)
# .claude/agents/function-auditor/AGENT.md (simple, haiku)
# .claude/agents/qc-programmer/AGENT.md    (file restrictions, opus)
```

> What frontmatter fields does every agent have?
> Required: _________________________________ (name, description)
> Optional: _________________________________ (tools, model, etc.)

> How does the agent persona differ from a generic prompt?
> _________________________________________________________________

### Step 2: Design Your Agent

Create a **TLF Reviewer** agent that reviews TLF outputs against the SAP.

Create the file: `.claude/agents/tlf-reviewer/AGENT.md`

Fill in this template:

```markdown
---
name: tlf-reviewer
description: [your description — when should Claude delegate to this agent?]
tools: [which tools does it need?]
model: [sonnet, opus, or haiku — and why?]
---

You are a [role description]...

## Your Role
[What does this agent do?]

## Key Files
[What files does it need to read?]

## Review Checklist
[What does it check?]

## Output Format
[How does it report findings?]
```

Design decisions to make:

> Which model did you choose and why?
> _________________________________________________________________

> Which tools did you include? Why not include Write?
> _________________________________________________________________

> What's in your review checklist? (list 3-5 items)
> 1. _______________________________________________
> 2. _______________________________________________
> 3. _______________________________________________
> 4. _______________________________________________
> 5. _______________________________________________

### Step 3: Test Your Agent

Ask Claude to delegate a task to your new agent:

> "Use the tlf-reviewer agent to review the sample TLF data in training/chapter_6_vibe_coding/tlf_search_app/sample_data/tlf_catalog.csv and check if the TLF titles follow SAP conventions."

> Did Claude successfully delegate to your agent? Yes / No
> Did the agent produce useful output? Yes / No
> What would you change about your agent design?
> _________________________________________________________________

---

## Part B: Create a Custom Skill (15 min)

### Step 1: Study an Existing Skill

Read one of the existing skills:

```bash
# Pick one to read:
# .claude/skills/validate-dataset/SKILL.md  (structured, step-by-step)
# .claude/skills/profile-data/SKILL.md      (data-focused)
# .claude/skills/check-environment/SKILL.md (simple checklist)
```

> What sections does every skill have?
> _________________________________________________________________

> How is a skill different from an agent?
> Skill: _________________________________
> Agent: _________________________________

### Step 2: Design Your Skill

Create a **TLF Search** skill that queries the TLF search app.

Create the file: `.claude/skills/search-tlf/SKILL.md`

Fill in this template:

```markdown
# Search TLF Database

Search the TLF title and footnote database for similar outputs across studies.

## Usage
`/search-tlf <query>`

## Instructions

1. [Step 1: what does Claude do first?]
2. [Step 2: ...]
3. [Step 3: ...]
4. [Step 4: how are results displayed?]

## Output Format
[What does the result look like?]
```

> What steps did you include in the instructions?
> _________________________________________________________________

> How does the skill know where the TLF database is?
> _________________________________________________________________

### Step 3: Verify the Skill File

After creating the file, verify it's in the right location:

```bash
ls .claude/skills/search-tlf/SKILL.md
```

> File exists? Yes / No
> (Note: you'll need to restart Claude Code for the skill to appear in the `/` menu)

---

## Reflection

> What's the key difference between when to create an agent vs a skill?
> Agent: _________________________________
> Skill: _________________________________

> If you could create one more agent for your team, what would it be?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] `.claude/agents/tlf-reviewer/AGENT.md` created with frontmatter + persona
- [ ] `.claude/skills/search-tlf/SKILL.md` created with usage + instructions
- [ ] Understanding of agent design decisions (model, tools, persona)
- [ ] Understanding of skill design decisions (steps, output format)
- [ ] Tested the agent with a delegated task
