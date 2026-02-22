"""
Conventions manager: pre-configured decisions for human review.

Conventions capture recurring human review decisions (RACE approach,
RFSTDTC derivation, date imputation, etc.) at two tiers:

  1. Company-level:  standards/conventions.yaml
  2. Study-level:    studies/{study}/conventions.yaml  (overrides company)

During human review, pre-configured decisions are shown with rationale
and the reviewer can accept (Enter) or override.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class Convention:
    """A pre-configured decision for a variable or rule."""

    variable: str
    approach: str
    rationale: str
    source: str  # "standard" or "study"
    overridden: bool = False  # True if study overrides a standard convention


@dataclass
class ValidationException:
    """A waived validation rule with justification."""

    rule: str
    status: str  # e.g., "waived"
    justification: str
    source: str = "standard"


class ConventionsManager:
    """
    Load and merge conventions from company standards and study overrides.

    Usage::

        cm = ConventionsManager(
            standards_path=Path("standards/conventions.yaml"),
            study_path=Path("studies/XYZ_2026_001/conventions.yaml"),
        )
        cm.load()
        decision = cm.get_decision("RACE")
    """

    def __init__(
        self,
        standards_path: Optional[Path] = None,
        study_path: Optional[Path] = None,
    ) -> None:
        self._standards_path = standards_path
        self._study_path = study_path
        self._decisions: Dict[str, Convention] = {}
        self._validation_exceptions: List[ValidationException] = []
        self._ct_overrides: Dict[str, List[Dict[str, str]]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load and merge conventions from both tiers."""
        self._decisions.clear()
        self._validation_exceptions.clear()
        self._ct_overrides.clear()

        # Load company standards
        std = self._load_yaml(self._standards_path) if self._standards_path else {}
        for var_name, cfg in std.get("decisions", {}).items():
            self._decisions[var_name] = Convention(
                variable=var_name,
                approach=str(cfg.get("approach", "")),
                rationale=str(cfg.get("rationale", "")),
                source="standard",
            )
        for exc in std.get("validation_exceptions", []):
            self._validation_exceptions.append(ValidationException(
                rule=exc.get("rule", ""),
                status=exc.get("status", "waived"),
                justification=exc.get("justification", ""),
                source="standard",
            ))
        self._ct_overrides = dict(std.get("ct_overrides", {}))

        # Load study overrides (study values replace standard values)
        study = self._load_yaml(self._study_path) if self._study_path else {}
        for var_name, cfg in study.get("decisions", {}).items():
            was_standard = var_name in self._decisions
            self._decisions[var_name] = Convention(
                variable=var_name,
                approach=str(cfg.get("approach", "")),
                rationale=str(cfg.get("rationale", "")),
                source="study",
                overridden=was_standard,
            )
        for exc in study.get("validation_exceptions", []):
            self._validation_exceptions.append(ValidationException(
                rule=exc.get("rule", ""),
                status=exc.get("status", "waived"),
                justification=exc.get("justification", ""),
                source="study",
            ))
        # Merge CT overrides: study values extend/override per codelist
        for codelist, mappings in study.get("ct_overrides", {}).items():
            if codelist in self._ct_overrides:
                self._ct_overrides[codelist].extend(mappings)
            else:
                self._ct_overrides[codelist] = list(mappings)

        self._loaded = True

    def get_decision(self, variable: str) -> Optional[Convention]:
        """Get pre-configured decision for a variable (study overrides standard)."""
        if not self._loaded:
            self.load()
        return self._decisions.get(variable)

    def get_all_decisions(self) -> Dict[str, Convention]:
        """Return all active decisions with source attribution."""
        if not self._loaded:
            self.load()
        return dict(self._decisions)

    def get_validation_exceptions(self) -> List[ValidationException]:
        """Return all validation exceptions (standard + study combined)."""
        if not self._loaded:
            self.load()
        return list(self._validation_exceptions)

    def get_ct_overrides(self) -> Dict[str, List[Dict[str, str]]]:
        """Return CT mapping overrides keyed by codelist code."""
        if not self._loaded:
            self.load()
        return dict(self._ct_overrides)

    def has_decisions(self) -> bool:
        """Return True if any conventions are loaded."""
        if not self._loaded:
            self.load()
        return bool(self._decisions)

    def summary(self) -> str:
        """Return a human-readable summary of loaded conventions."""
        if not self._loaded:
            self.load()
        lines = [f"Conventions: {len(self._decisions)} decisions loaded"]
        for var, conv in self._decisions.items():
            override_tag = " (overrides standard)" if conv.overridden else ""
            lines.append(
                f"  {var}: approach={conv.approach}, "
                f"source={conv.source}{override_tag}"
            )
        if self._validation_exceptions:
            lines.append(f"Validation exceptions: {len(self._validation_exceptions)}")
            for exc in self._validation_exceptions:
                lines.append(f"  {exc.rule}: {exc.status} ({exc.source})")
        if self._ct_overrides:
            lines.append(f"CT overrides: {len(self._ct_overrides)} codelists")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _load_yaml(path: Optional[Path]) -> Dict[str, Any]:
        """Load a YAML file; return empty dict if missing or None."""
        if path is None or not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
