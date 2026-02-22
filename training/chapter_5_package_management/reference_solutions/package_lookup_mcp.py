"""
Reference solution for Exercise 5.3: package_lookup MCP tool.

This shows the complete _package_lookup helper function and
how it integrates with the existing MCP server.
"""

import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _package_lookup(name: str, language: str, action: str) -> str:
    """
    Look up package information from the enterprise approved registry.

    Actions:
      - list:     List all approved packages (optionally filtered by language)
      - check:    Check if a specific package is approved
      - docs:     Retrieve versioned documentation for a package
      - restrict: List usage restrictions for a package
      - scan:     Scan R/Python code for compliance issues
    """
    sys.path.insert(0, str(PROJECT_ROOT))
    from package_manager.package_manager import PackageManager

    pm = PackageManager(
        str(PROJECT_ROOT / "package_manager" / "approved_packages.json")
    )

    # --- LIST: show all approved packages ---
    if action == "list":
        pkgs = pm.get_approved_packages(language or None)
        if not pkgs:
            return f"No approved packages found" + (
                f" for language '{language}'" if language else ""
            )
        lines = [f"Approved {language or 'all'} packages:", ""]
        for p in pkgs:
            ver = p.get("approved_version", "?")
            lines.append(f"- **{p['name']}** v{ver} ({p['language']}) — {p.get('purpose', '')}")
            if p.get("restrictions"):
                lines.append(f"  Restrictions: {len(p['restrictions'])} rules")
        return "\n".join(lines)

    # For all other actions, name is required
    if not name:
        return "Package name is required for check/docs/restrict/scan actions"

    # --- CHECK: is the package approved? ---
    if action == "check":
        result = pm.is_approved(name, language=language or None)
        pkg = result.get("package")
        lines = [f"Package: {name}"]
        if language:
            lines[0] += f" ({language})"
        lines.append(f"Status: {'APPROVED' if result['approved'] else 'NOT APPROVED'}")
        lines.append(f"Reason: {result['reason']}")
        if pkg:
            if pkg.get("approved_version"):
                lines.append(f"Approved version: {pkg['approved_version']}")
            if pkg.get("minimum_version"):
                lines.append(f"Minimum version: {pkg['minimum_version']}")
            if pkg.get("install_command"):
                lines.append(f"Install: {pkg['install_command']}")
            if result.get("alternative"):
                lines.append(f"Alternative: {result['alternative']}")
        return "\n".join(lines)

    # --- DOCS: retrieve versioned documentation ---
    elif action == "docs":
        docs = pm.get_documentation(name, language=language or None)
        return docs

    # --- RESTRICT: list restrictions ---
    elif action == "restrict":
        restrictions = pm.get_restrictions(name, language=language or None)
        if not restrictions:
            return f"No restrictions found for '{name}'"
        lines = [f"Restrictions for {name}:", ""]
        for i, r in enumerate(restrictions, 1):
            lines.append(f"{i}. {r}")

        # Also include known issues
        pkg = pm.get_package(name, language=language or None)
        if pkg and pkg.get("known_issues"):
            lines.append("")
            lines.append("Known issues:")
            for issue in pkg["known_issues"]:
                lines.append(f"  - {issue}")

        return "\n".join(lines)

    # --- SCAN: check code for compliance ---
    elif action == "scan":
        # For scan, the 'name' parameter is actually the code to scan
        # and 'language' specifies the language
        if not language:
            return "Language is required for scan action (R or Python)"
        issues = pm.check_code_compliance(name, language)
        if not issues:
            return "No compliance issues found. All packages are approved."
        lines = [f"Found {len(issues)} compliance issue(s):", ""]
        for issue in issues:
            lines.append(f"- [{issue['type']}] {issue.get('package', '?')}: {issue['message']}")
            if issue.get("alternative"):
                lines.append(f"  Alternative: {issue['alternative']}")
        return "\n".join(lines)

    else:
        return f"Unknown action: '{action}'. Valid actions: list, check, docs, restrict, scan"


# --- Integration with existing MCP server ---
# Add this Tool to list_tools():
TOOL_DEFINITION = {
    "name": "package_lookup",
    "description": (
        "Look up enterprise-approved packages. Check approval status, "
        "retrieve versioned documentation, list restrictions, or scan code "
        "for compliance issues. Use this before generating code that imports packages."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Package name (e.g., 'arrow', 'haven', 'pandas'). "
                    "For 'scan' action, pass the code to scan instead."
                ),
            },
            "language": {
                "type": "string",
                "enum": ["R", "Python", "SAS"],
                "description": "Programming language filter",
            },
            "action": {
                "type": "string",
                "enum": ["list", "check", "docs", "restrict", "scan"],
                "description": (
                    "list=all approved packages, check=approval status, "
                    "docs=versioned documentation, restrict=usage restrictions, "
                    "scan=check code for violations"
                ),
            },
        },
        "required": ["action"],
    },
}

# Add this to call_tool():
# elif name == "package_lookup":
#     result = _package_lookup(
#         arguments.get("name", ""),
#         arguments.get("language", ""),
#         arguments.get("action", "list"),
#     )
#     return [TextContent(type="text", text=result)]


# --- CLI test ---
if __name__ == "__main__":
    print("=== Package Lookup MCP Tool (CLI Test) ===\n")

    print("1. List approved R packages:")
    print(_package_lookup("", "R", "list"))

    print("\n2. Check arrow (R):")
    print(_package_lookup("arrow", "R", "check"))

    print("\n3. Check tidyverse (R):")
    print(_package_lookup("tidyverse", "R", "check"))

    print("\n4. Get haven restrictions:")
    print(_package_lookup("haven", "R", "restrict"))

    print("\n5. Scan code for issues:")
    test_code = "library(tidyverse)\nlibrary(arrow)\nhaven::write_xpt(dm, 'dm.xpt', version = 8)"
    print(_package_lookup(test_code, "R", "scan"))
