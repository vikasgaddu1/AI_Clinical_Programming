# Exercise 6.5: TLF Search Tool Exploration

## Objective
Extend or explore the TLF Search Tool demo app built during Module 6.5. Practice vibe coding by adding features using plan mode and iterative prompting.

## Time: 30 minutes

## Prerequisites
- The TLF Search Tool demo was completed in Module 6.5
- PostgreSQL is available (if not, choose Option C)

---

## Choose One Option

### Option A: Add Domain Tracking (Builder level)

The current TLF database stores titles and footnotes but doesn't let you search by SDTM domain source. Add this capability.

**Task:** Use vibe coding to:

1. Enter plan mode: "I want to add a feature to the TLF search tool that lets me filter search results by SDTM domain source. For example, 'find all TLFs that use the AE domain' should return only AE-related tables."

2. Review the plan Claude proposes. It should:
   - Note that `domain_source` already exists in the schema and sample data
   - Propose adding a `--domain` filter to `search_tlfs.py`

3. Approve and implement.

4. Test:
   ```bash
   python search_tlfs.py "summary" --domain AE
   python search_tlfs.py "demographics" --domain DM
   ```

> Did the plan identify that domain_source already existed? Yes / No
> Does the filter work correctly? Yes / No
> How many prompts did it take? _____

---

### Option B: Cross-Study Search (Builder level)

The current tool searches within a single study. Design how it would work across multiple studies.

**Task:**

1. Enter plan mode: "I want to extend the TLF search tool to search across multiple studies. When a new study starts, the stats programmer should be able to search: 'Has anyone at our company created a demographics summary table like the one in our SAP?' and find matching TLFs from previous studies."

2. Review the plan. Consider:
   - How would you load TLFs from multiple studies?
   - How would you display which study each result came from?
   - Would you need a new table or just more rows in `tlf_outputs`?

3. Don't implement -- just save the plan and answer:

> How would the schema change (if at all)?
> _________________________________________________________________

> How would the loader change?
> _________________________________________________________________

> How would the search results display change?
> _________________________________________________________________

> What's the most useful thing about cross-study search for a stats programmer?
> _________________________________________________________________

---

### Option C: Design an MCP Tool (Architect level -- no PostgreSQL needed)

Wrap the TLF search tool as an MCP tool so Claude Code can query it directly during coding sessions.

**Task:**

1. Enter plan mode: "I want to create an MCP tool called `search_tlf` that Claude Code can use during coding sessions. When a programmer asks 'has anyone created a table like this before?', Claude should automatically call the tool and return matching TLFs with program paths."

2. Review the plan. Reference the existing MCP server at `mcp_server.py` as the pattern.

3. Design the MCP tool definition (on paper or in a markdown file):

> **Tool name:** search_tlf

> **Parameters:**
> - query (string): _______________________________________________
> - domain (string, optional): _______________________________________________
> - top_k (int, optional): _______________________________________________

> **Return format:**
> _________________________________________________________________

> **How would it integrate with mcp_server.py?**
> _________________________________________________________________

> **How would you add it to .claude/mcp.json?**
> _________________________________________________________________

4. Consider: how would this MCP tool change a stats programmer's workflow?

> Before (without MCP tool):
> _________________________________________________________________

> After (with MCP tool):
> _________________________________________________________________

---

## Reflection

> Which vibe coding technique was most useful in this exercise?
> [ ] Plan mode  [ ] Iterative prompting  [ ] Context-giving  [ ] Debugging

> How would the TLF search tool change your team's workflow?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] (Option A) Domain filtering added and tested
- [ ] (Option B) Cross-study search plan documented
- [ ] (Option C) MCP tool design documented
- [ ] Practice with plan mode on a real feature extension
- [ ] Understanding of how the TLF search tool connects to daily clinical programming work
