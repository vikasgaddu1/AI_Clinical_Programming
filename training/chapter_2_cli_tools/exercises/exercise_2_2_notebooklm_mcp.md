# Exercise 2.2: NotebookLM MCP Integration

## Objective
Connect Google NotebookLM to Claude Code via MCP, enabling Claude to query your study documents with source-grounded, zero-hallucination answers. This bridges Chapter 1 (manual NotebookLM) with Chapter 2 (programmatic AI tools).

## Time: 20 minutes

## Prerequisites
- Claude Code running in the project directory
- Google account (same one used in Chapter 1)
- NotebookLM notebook from Chapter 1 with protocol, SAP, and SDTM IG uploaded
- Internet access

---

## Background

In Chapter 1, you queried NotebookLM manually in the browser. The `notebooklm-mcp` package lets Claude Code call NotebookLM as an MCP tool -- so Claude can research your documents before writing code, getting grounded answers without hallucination.

**Architecture:**
```
You ask Claude Code a question
  -> Claude calls NotebookLM MCP tool
    -> MCP server queries your NotebookLM notebook
      -> Gemini generates answer grounded in YOUR documents
    -> Cited answer returns to Claude Code
  -> Claude uses the grounded answer in its response
```

---

## Steps

### Step 1: Install the NotebookLM MCP Server

In your terminal, run:
```bash
claude mcp add notebooklm npx notebooklm-mcp@latest
```

This registers NotebookLM as an MCP server available to Claude Code.

> Did the installation succeed?
> _________________________________________________________________

### Step 2: Authenticate with Google

In Claude Code, type:
```
Log me in to NotebookLM
```

A Chrome browser window will open for Google authentication.

1. Log in with the same Google account you used in Chapter 1
2. Complete any security prompts
3. The browser will close automatically when authentication succeeds

> Authentication status: Success / Failed
> If failed, note the error: _____________________________________________

### Step 3: Add Your Chapter 1 Notebook

Go to https://notebooklm.google.com in your browser and copy the URL of your "XYZ-2026-001 DM Programming" notebook (the one with protocol + SAP + IG from Chapter 1).

In Claude Code, type:
```
Add this notebook to my NotebookLM library: [paste your notebook URL]
```

Claude should confirm the notebook was added to the library.

### Step 4: Query NotebookLM Through Claude Code

Now ask Claude questions that it will route to NotebookLM for grounded answers:

**Question 1:**
```
Using NotebookLM, what are the required variables for the DM domain according to the SDTM IG?
```

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Did the answer include citations from the IG? Yes / No

**Question 2:**
```
Research this in NotebookLM: What treatment arms does the protocol define, and what should ARMCD and ARM values be?
```

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Which document(s) was the answer grounded in?
> _________________________________________________________________

### Step 5: Grounded Coding Workflow

Now ask Claude to combine NotebookLM research with actual coding:
```
First research in NotebookLM what the SDTM IG says about the RACE variable and controlled terminology. Then read the raw_dm.csv file and show me what actual RACE values exist in our data. Finally, explain what mapping is needed.
```

Observe how Claude:
1. Queries NotebookLM for IG-grounded requirements
2. Reads the actual data file for real values
3. Synthesizes both into a mapping recommendation

> Did Claude use NotebookLM first, then read the data? Yes / No
>
> Was the IG information grounded (from your docs) vs. potentially hallucinated?
> _________________________________________________________________

### Step 6: Compare Grounding Methods

You now have THREE ways for Claude to access domain knowledge:

| Method | Example | Grounded? | Speed |
|--------|---------|-----------|-------|
| NotebookLM MCP | "Using NotebookLM, what does the IG say..." | Yes (your docs) | Slow (API call) |
| Local MCP tool | `sdtm_variable_lookup("DM", "RACE")` | Yes (local markdown) | Fast (local file) |
| Claude's training data | "What does the SDTM IG say about RACE?" | Maybe -- may hallucinate | Instant |

Ask Claude the same question three ways and compare:

1. "Using NotebookLM, how should RFSTDTC be derived?"
2. "Use the sdtm_variable_lookup tool to look up RFSTDTC in the DM domain"
3. "From your knowledge, how should RFSTDTC be derived?"

> Were the answers consistent across all three methods? Note any differences:
> _________________________________________________________________
> _________________________________________________________________

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Browser not found" | Ensure Chrome is installed and accessible |
| Authentication timeout | Try `Repair NotebookLM authentication` in Claude Code |
| Notebook not found | Verify the notebook URL is correct and the notebook is shared or owned by your account |
| MCP server not responding | Run `claude mcp list` to verify it's registered; try `claude mcp remove notebooklm` and re-add |

---

## Reflection Questions

1. How does the NotebookLM MCP change your workflow compared to manual browser-based lookups?
2. When would you use NotebookLM MCP vs the local `sdtm_variable_lookup` tool?
3. Could this approach work with other document types (company SOPs, FDA guidance)?

---

## What You Should Have at the End

- [ ] NotebookLM MCP server installed and authenticated
- [ ] Chapter 1 notebook added to the library
- [ ] At least 2 grounded queries successfully answered via NotebookLM MCP
- [ ] Understanding of three grounding methods and when to use each
