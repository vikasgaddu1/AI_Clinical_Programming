# Exercise 1.4: Limitations Discovery (Optional)

## Objective
Deliberately test NotebookLM's boundaries by asking it to do things it cannot do. This builds awareness of when you need a different tool (which is exactly what Chapters 2-3 and the Capstone provide).

## Time: 10 minutes

## Prerequisites
- NotebookLM notebook from previous exercises
- CSV file: `study_data/raw_dm.csv`

---

## Steps

### Step 1: Try Uploading a CSV Data File

1. In your notebook, click **"Add Source"**
2. Try uploading `raw_dm.csv`
3. Observe what happens

> What happened when you uploaded the CSV?
> _________________________________________________________________
> Did it process it? If so, can it distinguish between variable names and data values?
> _________________________________________________________________

### Step 2: Ask a Data Processing Question

If the CSV uploaded (even partially), ask:

**Question:** "How many subjects are in the raw_dm dataset? How many are at each site?"

> Record the answer:
> _________________________________________________________________
>
> Was the answer correct? Could NotebookLM actually count subjects?
> _________________________________________________________________

### Step 3: Ask for Code Generation

**Question:** "Write an R script that reads raw_dm.csv and converts the BRTHDT column to ISO 8601 format."

> Record the answer:
> _________________________________________________________________
>
> Did NotebookLM generate code? If so, is it grounded in your sources or from its training data?
> _________________________________________________________________

### Step 4: Ask for a Real-Time Lookup

**Question:** "What is the latest version of the SDTM Implementation Guide published by CDISC?"

> Record the answer:
> _________________________________________________________________
>
> Did it answer from your uploaded IG or refuse because it can't access the internet?
> _________________________________________________________________

---

## What These Limitations Tell Us

| Task | NotebookLM | What You Need Instead |
|------|-----------|----------------------|
| Count subjects per site | Cannot do | Claude Code / R / Python (Chapter 2) |
| Profile data quality | Cannot do | `/profile-data` skill in Claude Code (Chapter 2) |
| Write R code | May generate from training data (not source-grounded) | Production Programmer agent (Capstone) |
| Search live internet | Cannot do | Web search tools, updated document uploads |
| Run validation checks | Cannot do | `/validate-dataset` skill (Chapter 2) |
| Build a searchable IG index | Cannot do | RAG system (Chapter 3) |

---

## What You Should Have at the End

- [ ] Understanding of 4 specific things NotebookLM cannot do
- [ ] Clarity on which training chapter addresses each limitation
