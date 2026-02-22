"""
Spec manager: read/write mapping specification in JSON and XLSX.

Handles spec versions (draft -> reviewed -> approved -> finalized) and
validates consistency (codelists, variable metadata).

Domain name is used to generate file names (e.g. dm_mapping_spec.json,
ae_mapping_spec.json) so the system works for any SDTM domain.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    import openpyxl
    _EXCEL_AVAILABLE = True
except ImportError:
    _EXCEL_AVAILABLE = False
    pd = None


class SpecManager:
    """Read, write, and validate mapping specifications."""

    def __init__(self, output_dir: str, specs_dir: Optional[str] = None) -> None:
        self.output_dir = Path(output_dir)
        if specs_dir:
            self.specs_dir = Path(specs_dir)
        else:
            self.specs_dir = self.output_dir / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)

    def spec_path(self, domain: str, approved: bool = False) -> Path:
        """Path to spec JSON for a domain."""
        d = domain.lower()
        name = f"{d}_mapping_spec_approved.json" if approved else f"{d}_mapping_spec.json"
        return self.specs_dir / name

    def read_spec(self, domain: str, approved: bool = False) -> Optional[Dict[str, Any]]:
        """Read spec JSON; return None if file does not exist."""
        path = self.spec_path(domain, approved=approved)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def write_spec(self, domain: str, spec: Dict[str, Any], approved: bool = False) -> Path:
        """Write spec to JSON."""
        path = self.spec_path(domain, approved=approved)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
        return path

    def write_spec_xlsx(self, domain: str, spec: Dict[str, Any]) -> Optional[Path]:
        """Write a human-readable XLSX version of the spec (variables table)."""
        if not _EXCEL_AVAILABLE or "variables" not in spec:
            return None
        d = domain.lower()
        path = self.specs_dir / f"{d}_mapping_spec.xlsx"
        rows = []
        for v in spec["variables"]:
            row = {
                "target_variable": v.get("target_variable"),
                "target_domain": v.get("target_domain"),
                "source_variable": v.get("source_variable"),
                "mapping_logic": v.get("mapping_logic"),
                "macro_used": v.get("macro_used"),
                "codelist_code": v.get("codelist_code"),
                "human_decision_required": v.get("human_decision_required", False),
            }
            rows.append(row)
        df = pd.DataFrame(rows)
        df.to_excel(path, index=False)
        return path

    def validate_spec(self, spec: Dict[str, Any], ig_client=None) -> List[str]:
        """
        Validate spec; return list of error messages (empty if valid).

        If ig_client is provided, uses IG to determine required variables.
        Otherwise falls back to a minimal hardcoded set.
        """
        errors: List[str] = []
        if "variables" not in spec:
            errors.append("Spec must contain 'variables'")
            return errors

        domain = spec.get("domain", "DM")
        seen = {v.get("target_variable") for v in spec["variables"]}

        if ig_client and ig_client.is_available():
            required_vars = set(ig_client.get_required_variables(domain))
        else:
            required_vars = {
                "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC",
                "SITEID", "AGE", "AGEU", "SEX", "ARMCD", "ARM", "COUNTRY",
            }

        missing = required_vars - seen
        if missing:
            errors.append(f"Missing required variables: {sorted(missing)}")
        return errors
