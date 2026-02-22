# Function Registry Schema Reference

Quick reference for the JSON structure used in `function_registry.json` and `macro_registry.json`.

---

## Top-Level Structure

```json
{
  "registry_version": "1.0",
  "registry_date": "2026-02-18",
  "description": "R function library for SDTM clinical programming",
  "library_path": "r_functions",
  "language": "R",
  "functions": [ ... ],
  "orchestrator_integration": { ... }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registry_version` | string | Yes | Semantic version of the registry schema |
| `registry_date` | string | Yes | Date of last registry update (YYYY-MM-DD) |
| `description` | string | Yes | Human-readable description of the library |
| `library_path` | string | Yes | Relative path to the function source files |
| `language` | string | Yes | Programming language: `"R"`, `"SAS"`, `"Python"` |
| `functions` | array | Yes | Array of function definition objects |
| `orchestrator_integration` | object | Yes | Instructions for AI agents using the registry |

---

## Function Entry Schema

Each entry in the `functions` array:

```json
{
  "name": "iso_date",
  "file": "iso_date.R",
  "category": "Date Handling",
  "purpose": "Convert non-standard date values to ISO 8601 format (YYYY-MM-DD)",
  "when_to_use": [ ... ],
  "parameters": [ ... ],
  "output_type": "Character variable in YYYY-MM-DD format",
  "dependencies": [],
  "usage_examples": [ ... ],
  "notes": [ ... ]
}
```

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Function name as called in code (no `%` prefix for SAS) |
| `file` | string | Yes | Source file name (relative to `library_path`) |
| `category` | string | Yes | Grouping: `"Date Handling"`, `"Demographic Derivations"`, `"Controlled Terminology Mapping"`, `"Sequencing"`, `"Unit Conversion"`, etc. |
| `purpose` | string | Yes | One-line description of what the function does |

### AI Decision Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `when_to_use` | string[] | Yes | Scenarios where AI should select this function. **This is the primary field AI reads to decide.** Write 2-4 specific entries. |
| `dependencies` | string[] | Yes | Function names that must run before this one. Empty array `[]` if none. Used for topological sort. |

### Parameter Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parameters` | object[] | Yes | Array of parameter definitions |

Each parameter object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name as used in function call |
| `type` | string | Yes | Data type: `"data frame"`, `"character"`, `"numeric"`, `"logical"`, `"character vector"` |
| `required` | boolean | Yes | `true` if parameter must be provided |
| `description` | string | Yes | What this parameter does |
| `default` | string | No | Default value if not provided (only for optional params) |
| `example` | string/any | Yes | Example value AI can use in generated code |

### Code Generation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output_type` | string | Yes | Description of what the function returns |
| `usage_examples` | object[] | Yes | 2-3 copy-paste-ready code examples |
| `notes` | string[] | No | Edge cases, warnings, limitations |

Each usage example:

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | What this example demonstrates |
| `code` | string | Complete, runnable code snippet |

### Optional Domain-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `supported_input_formats` | string[] | For date functions: formats the function can parse |
| `supported_codelists` | object[] | For CT functions: codelist codes and their values |
| `lookup_file_structure` | object | For functions that read external files: file format |
| `output_length` | number | Character length of output variable |
| `error_handling` | string[] | How the function handles errors (SAS registry only) |

---

## Orchestrator Integration Section

```json
{
  "orchestrator_integration": {
    "how_to_use": [ ... ],
    "example_sequence": [
      {
        "step": 1,
        "function": "iso_date",
        "reason": "Birth date to ISO before age derivation",
        "call": "dm <- iso_date(dm, invar = \"BRTHDT\", outvar = \"BRTHDTC\")"
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `how_to_use` | string[] | Step-by-step instructions for AI agents |
| `example_sequence` | object[] | Ordered sequence showing how functions chain together |

Each sequence step:

| Field | Type | Description |
|-------|------|-------------|
| `step` | number | Execution order |
| `function` | string | Function name |
| `reason` | string | Why this step is needed at this point |
| `call` | string | Complete function call |

---

## Writing Good `when_to_use` Entries

**Do:**
- Be specific about the SDTM context: "Map raw categorical values to CDISC CT for SDTM compliance"
- Include the variable types it handles: "Apply to SEX, RACE, ETHNICITY, COUNTRY and other CT-controlled variables"
- Include negative guidance: "Use this instead of writing custom date conversion code"
- Reference domain applicability: "Required for SDTM DM domain population"

**Don't:**
- Be too vague: "Process data" or "Transform values"
- Assume context: "Use for conversions"
- Duplicate the purpose field: just restating the purpose is not helpful

---

## Dependency Rules

- Dependencies reference function names (not files)
- The FunctionLoader performs topological sort to determine execution order
- Circular dependencies are not supported (and indicate a design error)
- An empty `dependencies` array means the function can run at any point

**Common patterns:**
```
iso_date → derive_age     (dates must be ISO before age calculation)
iso_date → derive_studyday (dates must be ISO before day calculation)
assign_ct has no function dependencies (but needs ct_lookup.csv file)
```

---

## Language Differences (R vs SAS)

| Aspect | R Registry | SAS Registry |
|--------|-----------|--------------|
| Function name | `"iso_date"` | `"%iso_date"` |
| Data parameter | `data` (data frame, passed directly) | `inds`/`outds` (dataset names as strings) |
| Boolean type | `"logical"` with `true`/`false` | `"flag (Y/N)"` |
| Default path style | `"macros/ct_lookup.csv"` | `"./ct_lookup.csv"` |
| Return mechanism | Returns modified data frame | Writes to output dataset |
| Error handling | R stops with `stop()` | SAS macro stops with `%abort` |

---

## Quick Checklist for New Registry Entries

- [ ] `name` matches the actual function name in source code
- [ ] `file` exists in the `library_path` directory
- [ ] `when_to_use` has 2-4 specific, actionable entries
- [ ] All `required: true` parameters have no `default` field
- [ ] All `required: false` parameters have a `default` field
- [ ] Every parameter has an `example` value
- [ ] `dependencies` lists function names (not file names)
- [ ] `usage_examples` has 2-3 copy-paste-ready snippets
- [ ] JSON is valid (use `python -c "import json; json.load(open('path'))"` to check)
