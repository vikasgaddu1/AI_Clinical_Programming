"""
Load and expose the R function registry for agents.

Reads r_functions/function_registry.json so agents can discover available
R functions, parameters, dependencies, and usage examples without parsing
R source code.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class FunctionLoader:
    """Loads the R function registry and provides it to agents.

    Supports layered registries: a primary (standard) registry and optional
    additional registries (e.g., study-specific).  Functions from additional
    registries are merged in: same-name entries override, new entries are added.
    """

    def __init__(self, registry_path: str, additional_paths: Optional[List[str]] = None) -> None:
        self.registry_path = Path(registry_path)
        self._additional_paths: List[Path] = [
            Path(p) for p in (additional_paths or [])
        ]
        self._registry: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load and return the merged registry JSON."""
        if self._registry is not None:
            return self._registry
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Function registry not found: {self.registry_path}")
        with open(self.registry_path, encoding="utf-8") as f:
            self._registry = json.load(f)

        # Merge additional registries (study-specific overrides / additions)
        for extra_path in self._additional_paths:
            if not extra_path.exists():
                continue
            with open(extra_path, encoding="utf-8") as f:
                extra = json.load(f)
            extra_funcs = extra.get("functions", [])
            if not extra_funcs:
                continue
            # Build lookup by name for existing functions
            existing = {
                fn["name"]: i
                for i, fn in enumerate(self._registry.get("functions", []))
            }
            for fn in extra_funcs:
                name = fn.get("name", "")
                if name in existing:
                    # Override: study version replaces standard
                    self._registry["functions"][existing[name]] = fn
                else:
                    # Add: new study-specific function
                    self._registry.setdefault("functions", []).append(fn)

        return self._registry

    def get_functions(self) -> List[Dict[str, Any]]:
        """Return the list of function definitions."""
        reg = self.load()
        return reg.get("functions", [])

    def get_function_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Return a single function definition by name (e.g. 'iso_date', 'assign_ct')."""
        for fn in self.get_functions():
            if fn.get("name") == name:
                return fn
        return None

    def get_usage_examples(self, function_name: str) -> List[Dict[str, str]]:
        """Return usage examples for a function."""
        fn = self.get_function_by_name(function_name)
        if not fn:
            return []
        return fn.get("usage_examples", [])

    def get_dependency_order(self) -> List[str]:
        """
        Return function names in an order that respects dependencies
        (e.g. iso_date before derive_age before assign_ct).
        """
        funcs = self.get_functions()
        names = [f["name"] for f in funcs]
        deps: Dict[str, List[str]] = {}
        for f in funcs:
            deps[f["name"]] = f.get("dependencies", [])
        # Topological sort: dependencies first (by name match in our small set)
        known = set(names)
        order: List[str] = []
        seen: set = set()

        def visit(n: str) -> None:
            if n in seen:
                return
            seen.add(n)
            for d in deps.get(n, []):
                if d in known and d not in order:
                    visit(d)
            order.append(n)

        for n in names:
            visit(n)
        return order

    def format_for_prompt(self) -> str:
        """Format the registry for inclusion in an LLM prompt."""
        reg = self.load()
        lines = [
            "R function registry (use these when generating R code):",
            f"Library path: {reg.get('library_path', 'r_functions')}",
            "",
        ]
        for fn in self.get_functions():
            lines.append(f"## {fn['name']} (file: {fn.get('file', '')})")
            lines.append(f"  Purpose: {fn.get('purpose', '')}")
            lines.append("  When to use:")
            for w in fn.get("when_to_use", [])[:3]:
                lines.append(f"    - {w}")
            lines.append("  Parameters:")
            for p in fn.get("parameters", []):
                req = "required" if p.get("required", True) else "optional"
                lines.append(f"    - {p['name']} ({req}): {p.get('description', '')}")
            for ex in fn.get("usage_examples", [])[:2]:
                lines.append(f"  Example: {ex.get('code', '')}")
            lines.append("")
        return "\n".join(lines)
