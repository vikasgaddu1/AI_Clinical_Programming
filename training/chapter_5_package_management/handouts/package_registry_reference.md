# Enterprise Package Registry Reference

Quick reference for the `approved_packages.json` schema and `PackageManager` API.

---

## Registry JSON Schema

### Top-Level Structure

```json
{
  "registry_version": "1.0",
  "registry_date": "2026-02-21",
  "organization": "Clinical Programming Department",
  "description": "Enterprise-approved package registry...",
  "validation_policy": "All packages must pass IT validation...",
  "languages": ["R", "Python", "SAS"],
  "packages": [ ... ]
}
```

### Package Entry (Approved)

```json
{
  "name": "arrow",
  "language": "R",
  "approved_version": "14.0.2",
  "minimum_version": "14.0.0",
  "status": "approved",
  "validation_date": "2025-12-01",
  "validated_by": "IT Validation Team",
  "documentation_path": "package_docs/r/arrow/14.0.2.md",
  "install_command": "install.packages('arrow', repos='...')",
  "purpose": "Read and write Apache Parquet and Arrow IPC files",
  "key_functions": [ {name, description, example} ],
  "restrictions": [ "Do NOT use open_dataset()..." ],
  "known_issues": [ "Version 14.0.0 has timezone issue..." ],
  "dependencies": []
}
```

### Package Entry (Not Approved)

```json
{
  "name": "tidyverse",
  "language": "R",
  "approved_version": null,
  "status": "not_approved",
  "reason": "Meta-package installs 30+ packages...",
  "alternative": "Use individual packages: dplyr, tidyr, ggplot2"
}
```

### Package Entry (Under Review)

```json
{
  "name": "data.table",
  "language": "R",
  "approved_version": null,
  "status": "under_review",
  "reason": "Performance benefits but non-standard syntax...",
  "expected_decision_date": "2026-Q2"
}
```

---

## Package Statuses

| Status | AI Behavior | Color Code |
|--------|-------------|------------|
| `approved` | Use freely (with restrictions) | Green |
| `not_approved` | Do NOT use; suggest alternative | Red |
| `under_review` | Warn user; do not use in production | Yellow |

---

## Key Fields for AI Decision-Making

| Field | AI Uses It To... |
|-------|-----------------|
| `status` | Decide whether to use the package at all |
| `approved_version` | Generate code for the correct version |
| `key_functions` | Know which functions/APIs are available |
| `restrictions` | Avoid generating prohibited code patterns |
| `documentation_path` | Read versioned docs for correct API usage |
| `install_command` | Suggest correct installation from internal repo |
| `alternative` | Suggest replacement when package is not approved |
| `known_issues` | Avoid triggering documented bugs |

---

## PackageManager API

```python
from package_manager.package_manager import PackageManager
pm = PackageManager()
```

| Method | Returns | Description |
|--------|---------|-------------|
| `get_all_packages()` | `List[dict]` | All entries (any status) |
| `get_approved_packages(language)` | `List[dict]` | Only approved, filtered by language |
| `get_package(name, language)` | `dict or None` | Single package lookup |
| `is_approved(name, version, language)` | `dict` | `{approved: bool, reason: str}` |
| `get_documentation(name, language)` | `str` | Versioned markdown documentation |
| `get_restrictions(name, language)` | `List[str]` | Restriction rules |
| `get_key_functions(name, language)` | `List[dict]` | Key function reference |
| `check_code_compliance(code, language)` | `List[dict]` | Violations found in code |
| `format_for_prompt(language)` | `str` | Registry formatted for AI prompts |

---

## Versioned Documentation Structure

```
package_manager/
├── approved_packages.json
├── package_manager.py
└── package_docs/
    ├── r/
    │   ├── arrow/
    │   │   └── 14.0.2.md
    │   ├── haven/
    │   │   └── 2.5.4.md
    │   └── stringr/
    │       └── 1.5.1.md
    ├── python/
    │   ├── pandas/
    │   │   └── 2.1.4.md
    │   └── pyarrow/
    │       └── 14.0.2.md
    └── sas/
        └── base_sas/
            └── 9.4_M8.md
```

Each doc file includes:
- Package overview and purpose
- Enterprise installation command
- Key function signatures with parameters
- SDTM-specific usage patterns
- **Enterprise restrictions** (highlighted)
- **Version-specific notes** and known issues

---

## Four Enforcement Layers

```
Layer 1: CLAUDE.md Rules (Proactive)
  → Prevents AI from generating non-compliant code

Layer 2: MCP Tool (Informative)
  → Provides correct docs so code is generated right

Layer 3: PostToolUse Hook (Reactive)
  → Catches violations in generated files

Layer 4: CI/CD Pipeline (Audit)
  → Final gate before code enters repository
```

---

## Context7 vs Enterprise Package Manager

| Feature | Context7 (Public) | Enterprise PM (Local) |
|---------|-------------------|----------------------|
| Documentation source | Public (CRAN, PyPI, GitHub) | Internal (version-locked) |
| Version control | Latest public version | Approved version only |
| Restrictions | None | Company-specific rules |
| Known issues | Community-reported | IT-validated |
| Install commands | Public repos | Internal mirrors |
| Compliance checking | No | Yes |
| Use case | Exploration, prototyping | Production, submission code |

**Rule of thumb:** Context7 for learning, PackageManager for building.

---

## Quick Checklist for New Package Entries

- [ ] `name` matches the exact CRAN/PyPI package name
- [ ] `approved_version` matches what IT validated
- [ ] `minimum_version` is set (oldest acceptable version)
- [ ] `documentation_path` points to an existing markdown file
- [ ] `install_command` uses the internal repository URL
- [ ] `key_functions` lists the 3-5 most important functions with examples
- [ ] `restrictions` includes any company-specific or regulatory rules
- [ ] `known_issues` documents version-specific bugs
- [ ] Documentation file covers the approved version's API (not latest)
- [ ] JSON is valid after adding the entry
