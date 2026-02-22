"""
Enterprise Package Manager — query approved packages, versions, and documentation.

Provides a Python API for AI agents and MCP tools to discover enterprise-approved
packages, check version compliance, and retrieve versioned documentation.

This is a training mock that reads from local JSON and markdown files.
In production, this would connect to the company's package management system
(e.g., Artifactory, internal CRAN mirror, internal PyPI).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PackageManager:
    """Query the enterprise-approved package registry."""

    def __init__(self, registry_path: str = None) -> None:
        if registry_path is None:
            registry_path = str(
                Path(__file__).resolve().parent / "approved_packages.json"
            )
        self.registry_path = Path(registry_path)
        self._registry: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load and return the full approved packages registry."""
        if self._registry is not None:
            return self._registry
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f"Approved packages registry not found: {self.registry_path}"
            )
        with open(self.registry_path, encoding="utf-8") as f:
            self._registry = json.load(f)
        return self._registry

    def get_all_packages(self) -> List[Dict[str, Any]]:
        """Return all package entries."""
        return self.load().get("packages", [])

    def get_approved_packages(self, language: str = None) -> List[Dict[str, Any]]:
        """Return only approved packages, optionally filtered by language."""
        packages = []
        for pkg in self.get_all_packages():
            if pkg.get("status") != "approved":
                continue
            if language and pkg.get("language", "").lower() != language.lower():
                continue
            packages.append(pkg)
        return packages

    def get_package(self, name: str, language: str = None) -> Optional[Dict[str, Any]]:
        """Look up a specific package by name (case-insensitive)."""
        for pkg in self.get_all_packages():
            if pkg.get("name", "").lower() == name.lower():
                if language and pkg.get("language", "").lower() != language.lower():
                    continue
                return pkg
        return None

    def is_approved(self, name: str, version: str = None, language: str = None) -> Dict[str, Any]:
        """
        Check if a package (and optionally a specific version) is approved.
        Returns a dict with 'approved' (bool), 'reason' (str), and 'package' (dict or None).
        """
        pkg = self.get_package(name, language)
        if pkg is None:
            return {
                "approved": False,
                "reason": f"Package '{name}' not found in approved registry",
                "package": None,
            }

        status = pkg.get("status", "unknown")
        if status == "not_approved":
            return {
                "approved": False,
                "reason": pkg.get("reason", f"Package '{name}' is not approved"),
                "alternative": pkg.get("alternative", ""),
                "package": pkg,
            }
        if status == "under_review":
            return {
                "approved": False,
                "reason": f"Package '{name}' is under review (expected: {pkg.get('expected_decision_date', 'TBD')})",
                "package": pkg,
            }
        if status != "approved":
            return {
                "approved": False,
                "reason": f"Package '{name}' has status '{status}'",
                "package": pkg,
            }

        # Check version if provided
        if version:
            min_ver = pkg.get("minimum_version")
            approved_ver = pkg.get("approved_version")
            if min_ver and self._version_lt(version, min_ver):
                return {
                    "approved": False,
                    "reason": f"Version {version} is below minimum approved version {min_ver}",
                    "package": pkg,
                }

        return {"approved": True, "reason": "Package is approved", "package": pkg}

    def get_documentation(self, name: str, language: str = None) -> str:
        """Read the versioned documentation for an approved package."""
        pkg = self.get_package(name, language)
        if pkg is None:
            return f"Package '{name}' not found in approved registry"

        doc_path = pkg.get("documentation_path")
        if not doc_path:
            return f"No documentation available for '{name}'"

        full_path = self.registry_path.parent / doc_path
        if not full_path.exists():
            return f"Documentation file not found: {full_path}"

        return full_path.read_text(encoding="utf-8")

    def get_restrictions(self, name: str, language: str = None) -> List[str]:
        """Get usage restrictions for a package."""
        pkg = self.get_package(name, language)
        if pkg is None:
            return [f"Package '{name}' not found"]
        return pkg.get("restrictions", [])

    def get_key_functions(self, name: str, language: str = None) -> List[Dict[str, str]]:
        """Get key functions/features for a package."""
        pkg = self.get_package(name, language)
        if pkg is None:
            return []
        return pkg.get("key_functions", [])

    def check_code_compliance(self, code: str, language: str) -> List[Dict[str, str]]:
        """
        Scan code for potential package compliance issues.
        Returns a list of warnings/violations.
        """
        issues = []
        approved_pkgs = {
            p["name"].lower(): p for p in self.get_approved_packages(language)
        }

        if language.lower() == "r":
            # Check for library() calls
            import re
            for match in re.finditer(r"library\((\w+)\)", code):
                pkg_name = match.group(1).lower()
                if pkg_name not in approved_pkgs:
                    pkg = self.get_package(pkg_name, "R")
                    if pkg and pkg.get("status") == "not_approved":
                        issues.append({
                            "type": "NOT_APPROVED",
                            "package": match.group(1),
                            "message": f"Package '{match.group(1)}' is not approved. {pkg.get('reason', '')}",
                            "alternative": pkg.get("alternative", ""),
                        })
                    elif pkg and pkg.get("status") == "under_review":
                        issues.append({
                            "type": "UNDER_REVIEW",
                            "package": match.group(1),
                            "message": f"Package '{match.group(1)}' is under review",
                        })
                    else:
                        issues.append({
                            "type": "UNKNOWN",
                            "package": match.group(1),
                            "message": f"Package '{match.group(1)}' not in approved registry",
                        })

            # Check for specific restriction violations
            for pkg_name, pkg in approved_pkgs.items():
                for restriction in pkg.get("restrictions", []):
                    if "open_dataset" in restriction and "open_dataset" in code:
                        issues.append({
                            "type": "RESTRICTION",
                            "package": pkg["name"],
                            "message": restriction,
                        })
                    if "version = 8" in restriction.lower() and "version = 8" in code.lower():
                        issues.append({
                            "type": "RESTRICTION",
                            "package": pkg["name"],
                            "message": restriction,
                        })

        elif language.lower() == "python":
            import re
            for match in re.finditer(r"import (\w+)|from (\w+)", code):
                pkg_name = (match.group(1) or match.group(2)).lower()
                if pkg_name in ("os", "sys", "re", "json", "pathlib", "datetime", "csv"):
                    continue  # stdlib
                if pkg_name not in approved_pkgs and pkg_name != "yaml":
                    # Check aliases
                    if pkg_name == "yaml":
                        pkg_name = "pyyaml"
                    pkg = self.get_package(pkg_name, "Python")
                    if not pkg:
                        issues.append({
                            "type": "UNKNOWN",
                            "package": match.group(1) or match.group(2),
                            "message": f"Package '{match.group(1) or match.group(2)}' not in approved registry",
                        })

            # Check for unsafe yaml usage
            if "yaml.load(" in code and "safe_load" not in code:
                issues.append({
                    "type": "RESTRICTION",
                    "package": "pyyaml",
                    "message": "ALWAYS use yaml.safe_load() -- NEVER use yaml.load() without Loader parameter",
                })

        return issues

    def format_for_prompt(self, language: str = None) -> str:
        """Format approved packages for inclusion in an LLM prompt."""
        lines = ["Approved package registry (use ONLY these packages):"]
        lines.append(f"Policy: {self.load().get('validation_policy', '')}")
        lines.append("")

        for pkg in self.get_approved_packages(language):
            lines.append(f"## {pkg['name']} v{pkg['approved_version']} ({pkg['language']})")
            lines.append(f"  Purpose: {pkg.get('purpose', '')}")
            lines.append(f"  Install: {pkg.get('install_command', '')}")
            if pkg.get("restrictions"):
                lines.append("  Restrictions:")
                for r in pkg["restrictions"][:3]:
                    lines.append(f"    - {r}")
            if pkg.get("key_functions"):
                lines.append("  Key functions:")
                for fn in pkg["key_functions"][:4]:
                    lines.append(f"    - {fn['name']}: {fn['description']}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _version_lt(v1: str, v2: str) -> bool:
        """Simple version comparison (a < b)."""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            return parts1 < parts2
        except (ValueError, AttributeError):
            return False


# CLI test mode
if __name__ == "__main__":
    pm = PackageManager()

    print("=== Enterprise Package Manager ===\n")

    print("Approved R packages:")
    for pkg in pm.get_approved_packages("R"):
        print(f"  {pkg['name']} v{pkg['approved_version']}")

    print("\nApproved Python packages:")
    for pkg in pm.get_approved_packages("Python"):
        print(f"  {pkg['name']} v{pkg['approved_version']}")

    print("\nIs 'arrow' approved?")
    result = pm.is_approved("arrow", language="R")
    print(f"  {result['approved']}: {result['reason']}")

    print("\nIs 'tidyverse' approved?")
    result = pm.is_approved("tidyverse", language="R")
    print(f"  {result['approved']}: {result['reason']}")

    print("\nRestrictions for 'haven':")
    for r in pm.get_restrictions("haven"):
        print(f"  - {r}")

    print("\n--- format_for_prompt (R) ---")
    print(pm.format_for_prompt("R")[:500])
