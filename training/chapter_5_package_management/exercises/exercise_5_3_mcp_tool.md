# Exercise 5.3: Build an MCP Tool for Package Lookup

## Objective
Extend the existing MCP server with a `package_lookup` tool that AI agents can call to check package approval, retrieve documentation, and scan code for compliance.

## Time: 25 minutes

---

## Background

The existing `mcp_server.py` exposes 5 tools for SDTM programming. In this exercise, you'll add a 6th tool: `package_lookup`, which provides AI agents with on-demand access to the enterprise package registry.

## Steps

### Step 1: Understand the Existing MCP Pattern

Review `mcp_server.py`. Note the pattern for each tool:
1. A helper function (e.g., `_query_registry`) that does the actual work
2. A Tool definition in `list_tools()` with name, description, and inputSchema
3. A handler in `call_tool()` that routes to the helper function

> How many tools are currently defined? ___________
>
> What parameters does `query_function_registry` accept? ___________

### Step 2: Write the Helper Function

Add this function to `mcp_server.py` (or create a separate file):

```python
def _package_lookup(name: str, language: str, action: str) -> str:
    """Look up package information from the enterprise registry."""
    # Import PackageManager
    # YOUR CODE: Initialize PackageManager
    # Handle each action:
    #   "check"    → pm.is_approved(name, language=language) → format result
    #   "docs"     → pm.get_documentation(name, language) → return docs
    #   "restrict" → pm.get_restrictions(name, language) → format list
    #   "list"     → pm.get_approved_packages(language) → format summary
    pass
```

Fill in the implementation. Here's a starter:

```python
def _package_lookup(name: str, language: str, action: str) -> str:
    """Look up package information from the enterprise registry."""
    from package_manager.package_manager import PackageManager

    pm = PackageManager(str(PROJECT_ROOT / "package_manager" / "approved_packages.json"))

    if action == "list":
        pkgs = pm.get_approved_packages(language or None)
        if not pkgs:
            return f"No approved packages found for language '{language}'"
        lines = [f"Approved {language or 'all'} packages:", ""]
        for p in pkgs:
            lines.append(f"- **{p['name']}** v{p['approved_version']} — {p.get('purpose', '')}")
        return "\n".join(lines)

    if not name:
        return "Package name is required for check/docs/restrict actions"

    if action == "check":
        # YOUR CODE: call is_approved and format the result
        pass

    elif action == "docs":
        # YOUR CODE: call get_documentation and return it
        pass

    elif action == "restrict":
        # YOUR CODE: call get_restrictions and format the list
        pass

    else:
        return f"Unknown action: {action}. Use: list, check, docs, restrict"
```

> Complete the `check`, `docs`, and `restrict` branches.

### Step 3: Add the Tool Definition

Add to the `list_tools()` function:

```python
Tool(
    name="package_lookup",
    description="Look up enterprise-approved packages. Check approval status, retrieve versioned documentation, or list restrictions.",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Package name (e.g., 'arrow', 'haven', 'pandas')"
            },
            "language": {
                "type": "string",
                "description": "Language filter: R, Python, or SAS"
            },
            "action": {
                "type": "string",
                "enum": ["check", "docs", "restrict", "list"],
                "description": "Action: check (approval status), docs (versioned documentation), restrict (usage restrictions), list (all approved packages)"
            }
        },
        "required": ["action"]
    }
)
```

### Step 4: Add the Handler

Add to the `call_tool()` function:

```python
elif name == "package_lookup":
    result = _package_lookup(
        arguments.get("name", ""),
        arguments.get("language", ""),
        arguments.get("action", "list"),
    )
    return [TextContent(type="text", text=result)]
```

### Step 5: Test in CLI Mode

Update the CLI test section at the bottom of `mcp_server.py`:

```python
print("\n6. Package Lookup (arrow, R, check):")
print(_package_lookup("arrow", "R", "check"))
print("\n7. Package Lookup (tidyverse, R, check):")
print(_package_lookup("tidyverse", "R", "check"))
print("\n8. Package Lookup (haven, R, restrict):")
print(_package_lookup("haven", "R", "restrict"))
```

Run: `python mcp_server.py`

> Does `arrow` show as approved? ___________
>
> Does `tidyverse` show as not approved with an alternative? ___________
>
> Are haven restrictions listed? ___________

### Step 6: Design a `/check-packages` Skill

Without implementing it, design a Claude Code skill that uses the MCP tool:

```markdown
# /check-packages

## Title
Check Package Compliance

## Description
Scan generated R or Python scripts for unapproved package usage.

## Steps
1. [What should the skill do first?]
   ___________________________________________________________

2. [How should it check each script?]
   ___________________________________________________________

3. [What should it report?]
   ___________________________________________________________

4. [What should it do if violations are found?]
   ___________________________________________________________
```

---

## Discussion Questions

1. Should the MCP tool return the FULL documentation for a package, or just a summary? What are the trade-offs for LLM context window?

2. How would you add a `scan` action that takes R code as input and returns compliance issues? (Hint: PackageManager already has `check_code_compliance`)

3. If the MCP server is unavailable (e.g., Python not installed), how should Claude Code fall back? (Hint: CLAUDE.md instructions as static fallback)

---

## Reference Solution

A complete implementation is available at `training/chapter_5_package_management/reference_solutions/package_lookup_mcp.py`.

---

## What You Should Have at the End

- [ ] `_package_lookup` helper function implemented
- [ ] Tool definition added to MCP server
- [ ] Handler routing added to call_tool()
- [ ] CLI test shows correct results for check/docs/restrict actions
- [ ] Skill design documented for `/check-packages`
