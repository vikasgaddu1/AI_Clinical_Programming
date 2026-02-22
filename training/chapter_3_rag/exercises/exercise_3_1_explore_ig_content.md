# Exercise 3.1: Explore IG Content Files

## Objective
Understand the structure of the SDTM IG markdown content files and identify natural chunk boundaries for RAG retrieval.

## Time: 20 minutes

---

## Steps

### Step 1: Read the DM Domain File

Open `sdtm_ig_db/sdtm_ig_content/dm_domain.md` in your editor or ask Claude Code to read it.

Observe the structure:
- `## DM Domain Overview and Purpose` -- high-level description
- `### VARNAME` sections -- one section per variable (STUDYID, DOMAIN, USUBJID, etc.)
- Each variable section includes: Format, Controlled Terminology, Requirement, Assumptions
- A summary table at the end

> How many `### VARNAME` sections are there? ___________
>
> What information does each section contain?
> _________________________________________________________________

### Step 2: Identify Natural Chunk Boundaries

Each `### VARNAME` section is a natural chunk -- it contains all the information about one variable.

Pick the RACE section (`### RACE`). Read it carefully.

> What controlled terminology codelist does RACE use? ___________
>
> How many approaches does the IG describe for handling "Other Specify"? ___________
>
> What is the length of the RACE section in approximate characters? ___________

### Step 3: Read the General Assumptions File

Open `sdtm_ig_db/sdtm_ig_content/general_assumptions.md`.

> What topics does this file cover?
> _________________________________________________________________
>
> Is this file domain-specific (DM only) or cross-domain? ___________

### Step 4: Think About Chunking

Consider: if you were building a search system for these files, how would you chunk them?

> Option A: One chunk per `###` section (variable-level)
> - Pros: _________________________________________________________________
> - Cons: _________________________________________________________________
>
> Option B: Fixed-size chunks of ~2000 characters with overlap
> - Pros: _________________________________________________________________
> - Cons: _________________________________________________________________
>
> Which approach would give better answers for "How should RACE be coded?" ___________

### Step 5: Search Manually

Do a Ctrl+F search for "partial date" in dm_domain.md.

> Which variable sections mention partial dates?
> _________________________________________________________________
>
> Now think: if someone searched for "incomplete date" instead, would Ctrl+F find it?
> _________________________________________________________________
> This is the keyword search limitation that semantic search solves.

---

## What You Should Have at the End

- [ ] Understanding of the markdown structure (overview -> variable sections -> summary table)
- [ ] Identified natural chunk boundaries (`### VARNAME`)
- [ ] Understanding of why keyword search misses synonyms
