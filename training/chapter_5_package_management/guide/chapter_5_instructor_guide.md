# Chapter 5 Instructor Guide: Enterprise Package Management for AI Agents

## Chapter Overview

| Item | Detail |
|------|--------|
| **Title** | Enterprise Package Management for AI Agents |
| **Duration** | 3-4 hours |
| **Skill Level** | Builder → Architect |
| **Prerequisites** | Chapter 2 (Claude Code), Chapter 2B (Function Registry) |
| **Core Takeaway** | AI agents must use only enterprise-approved packages and versions. A package registry + MCP tools + enforcement hooks ensure compliance without slowing development. |

## Why This Chapter Exists

Enterprise clinical programming teams don't use public CRAN/PyPI directly. They maintain validated package environments where every package and version is approved by IT, tested for regulatory compliance, and locked to prevent unauthorized updates. When AI tools generate code, they must respect these constraints:

- Use only approved packages (not any package that exists on CRAN/PyPI)
- Use the correct approved version (not the latest public version)
- Follow package-specific restrictions (e.g., "never use `write_xpt(version=8)`")
- Access documentation for the approved version (not the latest docs online)

Without enforcement, AI-generated code will pull from general training knowledge and may use unapproved packages, wrong versions, deprecated APIs, or violate company-specific restrictions.

## Learning Objectives

By the end of this chapter, participants will be able to:

1. Explain why enterprise package management matters for AI-generated code
2. Design an approved package registry (`approved_packages.json`) with versions, restrictions, and documentation paths
3. Use the `PackageManager` class to query approved packages and check compliance
4. Build an MCP tool that AI agents call to look up package documentation
5. Create CLAUDE.md rules and hooks that enforce package compliance
6. Compare enterprise-local documentation with public documentation services (Context7)
7. Scan AI-generated code for unapproved package usage

## Connection to Other Chapters

| Chapter | Connection |
|---------|-----------|
| **Ch.2 (Claude Code)** | CLAUDE.md rules, MCP tools, and hooks are the enforcement mechanisms |
| **Ch.2B (Function Library)** | Functions call packages -- the function registry says WHAT functions to call; the package registry says WHICH VERSIONS of packages those functions depend on |
| **Ch.3 (RAG)** | RAG retrieves IG content; the package manager retrieves package documentation -- same retrieval pattern |
| **Capstone** | The orchestrator's generated R scripts must use only approved packages |

---

## Session Outline

### Module 5.1: The Problem -- Why AI Uses Wrong Packages (20 min)

**Key Point:** AI tools generate code from training data, which includes all public packages across all versions. Enterprise environments are far more restrictive.

**Talking Points:**
- Scenario: Ask Claude to "write R code to read a Parquet file"
  - Without package constraints: Claude might suggest `library(sparklyr)`, `library(data.table)`, or `library(arrow)` -- any of which could be valid R packages
  - With package registry: Claude knows `arrow v14.0.2` is the approved package and uses the correct API
- Three categories of package compliance issues:
  1. **Unapproved package:** Using `tidyverse` when only individual packages (dplyr, tidyr) are approved
  2. **Wrong version:** Using `pandas 2.2` features when only `pandas 2.1.4` is validated
  3. **Restriction violation:** Using `haven::write_xpt(version=8)` when FDA requires version 5
- Real-world impact:
  - Regulatory submission rejected because code uses non-validated packages
  - Reproducibility failure because package versions differ between dev and production
  - Security audit flags: unapproved packages may have unreviewed dependencies

**Demo:** Run `python package_manager/package_manager.py` to show the mock package manager in CLI mode. Show how it checks approval status for `arrow` (approved) vs `tidyverse` (not approved).

---

### Module 5.2: The Approved Package Registry (30 min)

**Key Point:** A JSON registry describes what packages are approved, at what versions, with what restrictions.

**Talking Points:**
- Walk through `package_manager/approved_packages.json`:

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Package name | `"arrow"` |
| `language` | R, Python, or SAS | `"R"` |
| `approved_version` | Exact validated version | `"14.0.2"` |
| `minimum_version` | Oldest acceptable version | `"14.0.0"` |
| `status` | `approved`, `not_approved`, `under_review` | `"approved"` |
| `validation_date` | When IT validated this version | `"2025-12-01"` |
| `documentation_path` | Path to version-specific docs | `"package_docs/r/arrow/14.0.2.md"` |
| `install_command` | Internal repo install command | `"install.packages('arrow', repos='https://internal-cran.company.com')"` |
| `key_functions` | Functions AI should know about | `[{name, description, example}]` |
| `restrictions` | Rules AI must follow | `["Do NOT use open_dataset() in validated programs"]` |
| `known_issues` | Version-specific bugs/limitations | `["Timestamp timezone issue on Windows in 14.0.0"]` |

- Three statuses and what they mean for AI:
  - `approved`: AI can use this package freely (with restrictions)
  - `not_approved`: AI must NOT use this package; suggest alternatives
  - `under_review`: AI should warn the user, not use in production code
- The `restrictions` array: these are RULES that AI must follow, not suggestions
- The `key_functions` array: AI uses these to generate correct function calls for the approved version

**Activity:** Display the `tidyverse` entry (not_approved) and `data.table` entry (under_review). Discuss why a meta-package gets rejected and what "under review" means.

---

### Module 5.3: Versioned Documentation Store (25 min)

**Key Point:** AI should read documentation for the APPROVED version, not the latest public version.

**Talking Points:**
- The problem with public documentation:
  - CRAN/PyPI docs are for the latest version -- which may not be your approved version
  - API changes between versions can cause subtle bugs in generated code
  - Enterprise-specific notes (restrictions, known issues) aren't in public docs
- The documentation store structure:
  ```
  package_docs/
  ├── r/
  │   ├── arrow/
  │   │   └── 14.0.2.md      <- docs for approved version
  │   └── haven/
  │       └── 2.5.4.md
  ├── python/
  │   └── pandas/
  │       └── 2.1.4.md
  └── sas/
      └── base_sas/
          └── 9.4_M8.md
  ```
- Each doc file includes:
  - Function signatures with parameters and examples
  - Enterprise-specific restrictions (highlighted prominently)
  - Version-specific notes and known issues
  - Common patterns for SDTM programming
- Walk through `package_docs/r/haven/2.5.4.md`:
  - Note the `write_xpt()` documentation explicitly says `version = 5`
  - Note the restrictions about label truncation
  - This is the documentation AI will read -- not the CRAN haven page

**Discussion:** "If your company upgrades `arrow` from 14.0.2 to 15.0.0, what needs to change?" (Answer: update approved_packages.json, create 15.0.0.md docs, re-validate, keep 14.0.2 docs for existing projects)

---

### Module 5.4: The PackageManager Class (25 min)

**Key Point:** A Python class provides programmatic access to the package registry for AI agents and MCP tools.

**Talking Points:**
- Walk through `package_manager/package_manager.py`:
  - `get_approved_packages(language)`: list all approved packages for a language
  - `get_package(name, language)`: look up a specific package
  - `is_approved(name, version, language)`: check if a package+version is approved
  - `get_documentation(name, language)`: read the versioned docs
  - `get_restrictions(name, language)`: get the restrictions list
  - `get_key_functions(name, language)`: get the key function reference
  - `check_code_compliance(code, language)`: scan code for violations
  - `format_for_prompt(language)`: format for AI agent prompts

- Parallel with FunctionLoader (Chapter 2B):
  - FunctionLoader reads function_registry.json → tells AI what R functions to call
  - PackageManager reads approved_packages.json → tells AI what packages are approved
  - Both have `format_for_prompt()` for injection into agent system prompts

**Demo:** Run Python interactively:
```python
from package_manager.package_manager import PackageManager
pm = PackageManager()

# Check if a package is approved
print(pm.is_approved("arrow", language="R"))
print(pm.is_approved("tidyverse", language="R"))

# Get documentation
print(pm.get_documentation("haven", language="R")[:500])

# Check code compliance
code = 'library(tidyverse)\nlibrary(arrow)\nhaven::write_xpt(dm, "dm.xpt", version = 8)'
issues = pm.check_code_compliance(code, "R")
for issue in issues:
    print(f"  [{issue['type']}] {issue['message']}")
```

---

### Module 5.5: MCP Tools and Skills for Package Lookup (30 min)

**Key Point:** Expose the package manager as an MCP tool so Claude Code can query it mid-conversation.

**Talking Points:**
- The existing MCP server (`mcp_server.py`) has 5 tools. We'll add a 6th: `package_lookup`
- What the MCP tool provides that CLAUDE.md instructions can't:
  - Dynamic queries: "Is package X approved?" (can't hardcode every possible question)
  - Documentation retrieval: returns the full versioned docs on demand
  - Compliance checking: scans generated code for violations
- Tool design:
  ```
  package_lookup(name, language, action)
    action = "check"    → is it approved? what version?
    action = "docs"     → return versioned documentation
    action = "restrict" → return restrictions list
    action = "scan"     → scan code for compliance issues
  ```
- Skill design: `/check-packages` skill that:
  1. Reads all R scripts in `orchestrator/outputs/programs/`
  2. Scans each for unapproved packages or restriction violations
  3. Reports findings

**Demo (conceptual):** Show how Claude Code would use the MCP tool:
- User: "Write an R script to read the raw DM data and write it as XPT"
- Claude calls `package_lookup(name="haven", action="docs")` → gets haven 2.5.4 docs
- Claude generates code with `haven::write_xpt(dm, path="dm.xpt", version=5)` (correct)
- Claude does NOT generate `version=8` because the docs say FDA requires v5

---

### Module 5.6: Enforcement -- CLAUDE.md Rules and Hooks (25 min)

**Key Point:** Multiple enforcement layers ensure AI-generated code stays compliant.

**Talking Points:**

1. **CLAUDE.md rules (soft enforcement):**
   Add to the project's CLAUDE.md:
   ```markdown
   ## Package Policy
   - ONLY use packages listed in package_manager/approved_packages.json
   - Check package approval status before using any library() or import statement
   - Use the package_lookup MCP tool to verify packages and get versioned documentation
   - If a package is not_approved, suggest the documented alternative
   - If a package is under_review, warn the user and do not use it in production code
   ```
   This works because Claude Code loads CLAUDE.md every session.

2. **Hooks (hard enforcement):**
   Add a PostToolUse hook that scans generated R/Python files:
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Write",
           "command": "python package_manager/check_compliance.py $FILE_PATH"
         }
       ]
     }
   }
   ```
   This catches violations even if the AI ignores CLAUDE.md instructions.

3. **Agent prompt injection:**
   The orchestrator's agents receive `PackageManager.format_for_prompt()` in their system prompts, just like they receive `FunctionLoader.format_for_prompt()`.

4. **CI/CD integration (production):**
   In a real deployment, a pre-commit hook or CI pipeline would scan all generated code against the approved registry before allowing commits.

**Discussion:** "Which layer catches which type of error?"
- CLAUDE.md: prevents generation of unapproved code (proactive)
- MCP tool: provides correct documentation so code is generated right (informative)
- Hook: catches violations that slip through (reactive)
- CI/CD: final gate before code enters the repository (audit)

---

### Module 5.7: Context7 vs Enterprise Package Manager (20 min)

**Key Point:** Context7 fetches public docs; your package manager fetches enterprise-approved docs. Both can coexist.

**Talking Points:**
- What Context7 does well:
  - Retrieves up-to-date documentation for any public library
  - Useful for open-source exploration, prototyping, and learning
  - Example: `resolve-library-id("arrow R package")` → returns Arrow docs
- What Context7 doesn't do:
  - Doesn't know which VERSION is approved at your company
  - Doesn't include enterprise-specific restrictions or known issues
  - Doesn't enforce compliance -- it's read-only public documentation
  - May return docs for a version you haven't validated
- The recommended pattern:
  1. **Development/prototyping:** Use Context7 for exploring packages, reading docs, prototyping
  2. **Production/submission code:** Use enterprise PackageManager for approved versions and restrictions
  3. **CLAUDE.md rule:** "For production code, always use the package_lookup MCP tool. For exploration, Context7 is acceptable."
- Hybrid approach: use Context7 to initially research a package, then check enterprise approval status with PackageManager before using it in production code

**Activity:** Use Context7 to look up Apache Arrow docs. Compare the documentation returned with the enterprise `14.0.2.md` file. Identify what's different (version-specific notes, restrictions, enterprise install commands).

---

## Exercises (90 min total)

| Exercise | Duration | Description |
|----------|----------|-------------|
| 5.1 | 20 min | Explore the approved package registry |
| 5.2 | 25 min | Add a new package with versioned documentation |
| 5.3 | 25 min | Build an MCP tool for package lookup |
| 5.4 | 20 min | Create enforcement rules and test compliance |

---

## Slide Deck Outline (22 slides)

| # | Slide Title | Content | Notes |
|---|-------------|---------|-------|
| 1 | Chapter 5: Enterprise Package Management for AI | Title slide | |
| 2 | The Problem | AI uses any package from training data | Show wrong version example |
| 3 | Three Types of Violations | Unapproved, wrong version, restriction violation | Examples of each |
| 4 | Real-World Impact | Submission rejected, reproducibility failure, security audit | |
| 5 | The Approved Package Registry | JSON structure overview | Show approved_packages.json |
| 6 | Anatomy of a Package Entry | Field-by-field walkthrough | Use arrow as example |
| 7 | Three Statuses | approved, not_approved, under_review | What each means for AI |
| 8 | Restrictions: Rules for AI | Array of hard rules | Show haven restrictions |
| 9 | Versioned Documentation | Why public docs aren't enough | Version mismatch example |
| 10 | Documentation Store Structure | File tree diagram | package_docs/ hierarchy |
| 11 | What's in a Doc File | Function signatures + enterprise notes | Show haven 2.5.4.md excerpt |
| 12 | The PackageManager Class | Python API overview | Show key methods |
| 13 | is_approved() | Check package + version | Demo output |
| 14 | check_code_compliance() | Scan code for violations | Demo with tidyverse code |
| 15 | format_for_prompt() | How registry reaches AI agents | Show prompt text |
| 16 | MCP Tool: package_lookup | Expose PackageManager via MCP | Tool design |
| 17 | CLAUDE.md Rules | Soft enforcement in project instructions | Show rule text |
| 18 | Hooks: Hard Enforcement | PostToolUse hook scans generated files | Show hook config |
| 19 | Four Enforcement Layers | CLAUDE.md → MCP → Hook → CI/CD | Diagram |
| 20 | Context7 vs Enterprise PM | Public docs vs approved docs | Comparison table |
| 21 | When to Use Which | Development vs production | Decision flowchart |
| 22 | Key Takeaway | Approved packages + versioned docs + enforcement = compliant AI code | |

---

## Timing Summary

| Module | Duration | Cumulative |
|--------|----------|------------|
| 5.1: The Problem | 20 min | 0:20 |
| 5.2: Approved Package Registry | 30 min | 0:50 |
| 5.3: Versioned Documentation | 25 min | 1:15 |
| 5.4: PackageManager Class | 25 min | 1:40 |
| **Break** | **10 min** | **1:50** |
| 5.5: MCP Tools and Skills | 30 min | 2:20 |
| 5.6: Enforcement (CLAUDE.md + Hooks) | 25 min | 2:45 |
| 5.7: Context7 vs Enterprise PM | 20 min | 3:05 |
| **Exercises** | **90 min** | **4:35** |
| **Total** | **~4.5 hours** | |

---

## Key Messages to Reinforce

1. **"Approved means approved."** If a package isn't in the registry, AI must not use it in production code. Period.

2. **"Version matters."** The same package at different versions can have different APIs, bugs, and behaviors. Documentation must match the approved version.

3. **"Restrictions are rules, not suggestions."** When the registry says "Do NOT use write_xpt(version=8)", the AI must never generate that code.

4. **"Four layers of defense."** CLAUDE.md (proactive) → MCP (informative) → Hooks (reactive) → CI/CD (audit). Each catches what the previous missed.

5. **"Context7 for exploration, PackageManager for production."** Both have their place. Don't confuse exploration tools with production compliance tools.

---

## Bridge to Capstone

"You've now built the complete infrastructure that the Capstone's orchestrator relies on: study comprehension (Ch.1), AI tool configuration (Ch.2), function libraries (Ch.2B), IG knowledge retrieval (Ch.3), CDISC CT lookups (Ch.4), and now package compliance (Ch.5). In the Capstone, all of these components work together -- the Production Programmer agent generates R code that uses registered functions from approved packages, with versioned documentation and compliance enforcement at every step."

---

## Instructor Preparation

- [ ] Verify `package_manager/package_manager.py` runs: `python package_manager/package_manager.py`
- [ ] Verify documentation files exist in `package_manager/package_docs/`
- [ ] Have `approved_packages.json` open for Module 5.2 walkthrough
- [ ] Prepare a code snippet with intentional violations for Module 5.4 demo
- [ ] Test Context7 availability (MCP tool) for Module 5.7 comparison
- [ ] Review the reference solution for Exercise 5.3 (MCP tool extension)
