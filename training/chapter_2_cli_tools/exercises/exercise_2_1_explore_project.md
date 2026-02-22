# Exercise 2.1: Explore the Project with Claude Code

## Objective
Get comfortable with Claude Code by using it to explore the project -- reading files, profiling data, and running slash commands. Experience the difference between NotebookLM (document understanding) and Claude Code (data processing + code execution).

## Time: 20 minutes

## Prerequisites
- Claude Code installed and accessible in the terminal
- The `AI_Clinical_Programming` project directory
- Python 3.11+ with required packages installed

---

## Steps

### Step 1: Start Claude Code

Open a terminal in the `AI_Clinical_Programming` project directory and start Claude Code.

Observe: Claude automatically loads `CLAUDE.md` as project context.

### Step 2: Run Your First Skill

Type the following command:
```
/check-environment
```

Watch Claude execute each check. Record the results:

> Python packages: PASS / FAIL
> R availability: PASS / FAIL / SKIP
> R packages: PASS / FAIL / SKIP
> Configuration: PASS / FAIL
> Study data: PASS / FAIL
> Function registry: PASS / FAIL
> CT lookup: PASS / FAIL
> IG content: PASS / FAIL
> Database: PASS / FAIL / SKIP
> API key: PASS / FAIL / SKIP

If any checks fail, note the suggested fix but don't fix it now -- we'll proceed with what works.

### Step 3: Explore Study Data

Ask Claude:
```
Read the first 10 rows of study_data/raw_dm.csv and tell me about the data quality issues you see
```

Observe how Claude:
1. Reads the actual CSV file (not a document description like NotebookLM)
2. Reports specific data values, counts, and issues
3. Can identify mixed coding, date format inconsistencies, etc.

> What data quality issues did Claude find?
> _________________________________________________________________
> _________________________________________________________________

### Step 4: Profile the Data

Run the profiling skill:
```
/profile-data
```

Watch Claude analyze every column with frequencies, missing counts, and data type detection.

> How many distinct RACE values are there? List the top 5:
> _________________________________________________________________
>
> What date formats did Claude find in BRTHDT?
> _________________________________________________________________
>
> Which columns have missing values > 5%?
> _________________________________________________________________

### Step 5: Compare with Chapter 1

Think back to Chapter 1 (NotebookLM):

| Task | NotebookLM (Ch.1) | Claude Code (Ch.2) |
|------|-------------------|-------------------|
| "How many subjects in the study?" | Could not answer from CSV | _________________ |
| "What RACE values exist in the data?" | Could not process data | _________________ |
| "What does the IG say about RACE?" | Answered from uploaded PDF | _________________ |
| "What date formats are in BRTHDT?" | Could not analyze data | _________________ |

### Step 6: Explore the Function Registry

Ask Claude:
```
Read r_functions/function_registry.json and explain what R functions are available, what order they should run in, and what parameters each one takes
```

> List the 3 functions and their execution order:
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________

---

## Reflection Questions

1. What tasks does Claude Code handle that NotebookLM cannot?
2. Did you notice Claude reading files and executing commands? Could you follow what it was doing?
3. How is the `/profile-data` skill different from manually writing a Python script to profile data?

---

## What You Should Have at the End

- [ ] Completed environment check with results recorded
- [ ] Data profiling output showing column statistics and quality issues
- [ ] Understanding of how Claude Code reads and processes files (vs. NotebookLM's document-only approach)
- [ ] Function registry summary in your notes
