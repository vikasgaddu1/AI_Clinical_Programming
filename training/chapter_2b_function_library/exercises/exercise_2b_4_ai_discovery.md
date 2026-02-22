# Exercise 2B.4: Test AI Function Discovery and Code Generation

## Objective
Verify that Claude Code discovers and uses registered functions when generating R code, instead of writing custom implementations.

## Time: 20 minutes

---

## Steps

### Step 1: Ask Claude Code Without Context

Open Claude Code in the project directory. Ask this question:

```
What R functions are available in this project for SDTM programming?
```

> Did Claude list the functions from function_registry.json? ___________
>
> Did it mention the FunctionLoader or function_registry.json? ___________
>
> How did Claude discover the functions -- from CLAUDE.md, the registry file, or both?
> _________________________________________________________________

### Step 2: Request Code Using a Registered Function

Ask Claude Code:

```
Write R code to convert the BRTHDT column in raw_dm.csv to ISO 8601 format for the BRTHDTC variable.
```

> Did Claude use `iso_date()` or write custom date parsing code?
> _________________________________________________________________
>
> If it used `iso_date()`, did it include the correct `source()` call?
> _________________________________________________________________
>
> Did the parameters match what's in the registry? Check:
> - `invar`: should be `"BRTHDT"` ___________
> - `outvar`: should be `"BRTHDTC"` ___________

### Step 3: Request a Multi-Function Pipeline

Ask Claude Code:

```
Write a complete R script that reads raw_dm.csv and applies all necessary SDTM transformations:
convert birth dates and reference dates to ISO, derive age, and map SEX/RACE/ETHNIC to controlled terminology.
```

> How many registered functions did Claude use? ___________
>
> List them in the order Claude called them:
> 1. ___________
> 2. ___________
> 3. ___________
>
> Does the order match the dependency chain from the registry?
> _________________________________________________________________
>
> Did Claude include `source()` calls for each R function file?
> _________________________________________________________________

### Step 4: Test with Your New Function

If you completed Exercise 2B.2 (registering `derive_studyday`), ask Claude Code:

```
I need to derive DMDY (study day) for the DM domain. DMDY = days from RFSTDTC to DMDTC with no Day 0.
```

> Did Claude discover `derive_studyday` in the registry? ___________
>
> Did it use `derive_studyday()` or write custom code? ___________
>
> If it wrote custom code, why? (Check: is the registry entry loaded correctly?)
> _________________________________________________________________

### Step 5: Test the MCP Tool

If the MCP server is running, ask Claude Code:

```
Look up the assign_ct function details using the MCP tool.
```

> Did Claude use the `query_function_registry` MCP tool? ___________
>
> What information did the tool return?
> - Purpose: _________________________________________________________________
> - Parameters: _________________________________________________________________
> - Supported codelists: _________________________________________________________________

### Step 6: Test Edge Case Awareness

Ask Claude Code:

```
I have dates in DD/MM/YYYY format from a UK site. How should I convert them to ISO 8601?
```

> Did Claude mention the `infmt` parameter from the registry? ___________
>
> Did it reference the ambiguity warning from the `notes` field? ___________
>
> What code did it generate?
> _________________________________________________________________
>
> Compare this to the registry's note:
> "AMBIGUITY: Slash dates with both parts <= 12 (e.g. 03/04/2020) default to MM/DD/YYYY — use infmt='DD/MM/YYYY' for non-US data"

### Step 7: Compare With and Without the Registry

This is a thought experiment. Consider:

| Scenario | What AI Generates |
|----------|-------------------|
| **With registry** | `dm <- iso_date(dm, invar = "BRTHDT", outvar = "BRTHDTC")` |
| **Without registry** | ~50 lines of custom date parsing using `as.Date()`, `format()`, regex patterns, etc. |

> What are the risks of the "without registry" code?
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________
>
> What are the benefits of the "with registry" code?
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________

---

## Bonus: Ask Claude to Suggest a Missing Function

Ask Claude Code:

```
Based on the current function registry and the DM domain variables,
are there any common SDTM derivations that are NOT covered by registered functions?
What function would you recommend adding?
```

> What did Claude suggest?
> _________________________________________________________________
>
> Does the suggestion make sense given the DM domain requirements?
> _________________________________________________________________

---

## Discussion Questions

1. If Claude Code generates code using a registered function but with wrong parameter values, where should you look to fix the issue -- the function source code, the registry, or the CLAUDE.md?

2. When Claude uses `format_for_prompt()` to include the registry in agent prompts, what happens if the registry is very large (100+ functions)? How might you optimize this?

3. How would you verify that AI-generated code actually calls the registered function correctly, not just naming it but passing correct parameters?

---

## What You Should Have at the End

- [ ] Verified Claude Code discovers registered functions
- [ ] Verified Claude generates code using `iso_date()`, `derive_age()`, `assign_ct()`
- [ ] Verified correct function call order (dependency chain)
- [ ] Tested registry awareness for edge cases (date format ambiguity)
- [ ] Understanding of why registries produce better AI-generated code
