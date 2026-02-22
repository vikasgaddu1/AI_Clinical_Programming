# Exercise 5.4: Create Enforcement Rules and Test Compliance

## Objective
Set up multiple layers of package enforcement: CLAUDE.md rules, compliance scanning, and hook design. Then test that AI-generated code stays compliant.

## Time: 20 minutes

---

## Steps

### Step 1: Write CLAUDE.md Package Rules

Design the package policy section for CLAUDE.md. Write rules that Claude Code will follow every session:

```markdown
## Package Policy

[Write 5-7 rules that cover:]
1. Where to find approved packages
   > ___________________________________________________________

2. What to do before using any library() or import statement
   > ___________________________________________________________

3. What to do if a package is not_approved
   > ___________________________________________________________

4. What to do if a package is under_review
   > ___________________________________________________________

5. How to get versioned documentation
   > ___________________________________________________________

6. What restrictions must be followed
   > ___________________________________________________________

7. When Context7 (public docs) is acceptable vs when enterprise docs are required
   > ___________________________________________________________
```

### Step 2: Test Compliance Scanning

Use the PackageManager to scan example code:

```python
import sys; sys.path.insert(0, '.')
from package_manager.package_manager import PackageManager

pm = PackageManager()

# Compliant R code
good_code = """
library(arrow)
library(haven)
dm <- arrow::read_parquet("dm.parquet")
haven::write_xpt(dm, path = "dm.xpt", version = 5)
"""

# Non-compliant R code
bad_code = """
library(tidyverse)
library(data.table)
library(arrow)
dm <- read_parquet("dm.parquet")
haven::write_xpt(dm, path = "dm.xpt", version = 8)
"""

print("=== Good Code ===")
issues = pm.check_code_compliance(good_code, "R")
print(f"Issues: {len(issues)}")
for i in issues:
    print(f"  [{i['type']}] {i['message']}")

print("\n=== Bad Code ===")
issues = pm.check_code_compliance(bad_code, "R")
print(f"Issues: {len(issues)}")
for i in issues:
    print(f"  [{i['type']}] {i['message']}")
```

> How many issues in the good code? ___________
>
> How many issues in the bad code? ___________
>
> List the violations found:
> 1. _________________________________________________________________
> 2. _________________________________________________________________
> 3. _________________________________________________________________

### Step 3: Design a PostToolUse Hook

The existing project has a PreToolUse hook that blocks writing files with secrets. Design a PostToolUse hook for package compliance:

> **Hook trigger:** When Claude Code writes a `.R` or `.py` file
>
> **What the hook should do:**
> _________________________________________________________________
>
> **Hook command (conceptual):**
> ```json
> {
>   "hooks": {
>     "PostToolUse": [
>       {
>         "matcher": "___________",
>         "command": "___________"
>       }
>     ]
>   }
> }
> ```
>
> **What should happen if violations are found?**
> - Option A: Block the write and show the violation
> - Option B: Allow the write but print a warning
> - Option C: Allow the write and log to an audit file
>
> Which option would you choose for production? ___________
> Why? _________________________________________________________________

### Step 4: Test with Claude Code (Interactive)

If Claude Code is available, test the enforcement:

1. Ask Claude Code:
   ```
   Write R code to read raw_dm.csv and reshape it using data.table.
   ```

   > Did Claude use data.table? ___________
   >
   > If CLAUDE.md rules are in place, what should Claude say?
   > _________________________________________________________________

2. Ask Claude Code:
   ```
   What R packages are approved for use in this project?
   ```

   > Did Claude reference the approved_packages.json registry? ___________
   >
   > Did it list the correct packages and versions? ___________

3. Ask Claude Code:
   ```
   Write R code to write the DM dataset as XPT for FDA submission.
   ```

   > Did Claude use `haven::write_xpt()` with `version = 5`? ___________
   >
   > Did it set labels before writing? ___________

### Step 5: Map the Four Enforcement Layers

For each violation type, identify which enforcement layer catches it:

| Violation | CLAUDE.md | MCP Tool | Hook | CI/CD |
|-----------|:---------:|:--------:|:----:|:-----:|
| Using `library(tidyverse)` | ___ | ___ | ___ | ___ |
| Using `write_xpt(version=8)` | ___ | ___ | ___ | ___ |
| Using arrow v12.0 (below minimum) | ___ | ___ | ___ | ___ |
| Using a package not in registry | ___ | ___ | ___ | ___ |
| Using `yaml.load()` (security risk) | ___ | ___ | ___ | ___ |

Mark each cell: P (primary defense), S (secondary), or -- (doesn't catch this)

### Step 6: Compare with Function Registry Enforcement

In Chapter 2B, the function registry ensures AI calls existing functions. Compare:

| Aspect | Function Registry (Ch.2B) | Package Registry (Ch.4) |
|--------|---------------------------|-------------------------|
| What it controls | Which R functions to call | ___________ |
| JSON file | function_registry.json | ___________ |
| Python class | FunctionLoader | ___________ |
| MCP tool | query_function_registry | ___________ |
| CLAUDE.md mention | "Use functions from the registry" | ___________ |
| What happens if AI ignores it | Writes custom code | ___________ |

> How do these two registries work together?
> _________________________________________________________________
> (Hint: Functions DEPEND ON packages. `iso_date()` uses base R; `write_parquet()` uses the `arrow` package.)

---

## Discussion Questions

1. A programmer manually adds `library(ggplot2)` to a generated R script (ggplot2 is not in the registry). Should the hook catch this? How?

2. Your company acquires another company whose programmers use Python `polars` instead of `pandas`. How would you handle the transition in the package registry?

3. Should the package registry be per-project (like function_registry.json) or company-wide? What are the trade-offs?

---

## What You Should Have at the End

- [ ] CLAUDE.md package policy rules written
- [ ] Compliance scanning tested on good and bad code
- [ ] PostToolUse hook designed for package enforcement
- [ ] Understanding of four enforcement layers
- [ ] Comparison of function registry vs package registry patterns
