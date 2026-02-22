"""
Config resolver: layered configuration for multi-study architecture.

Resolves configuration by merging:
  1. standards/config.base.yaml  (company defaults)
  2. studies/{study}/config.yaml (study overrides)

Falls back to orchestrator/config.yaml when no --study flag is used.
"""

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge *overrides* into *base*.

    - Dict values are merged recursively.
    - All other types in *overrides* replace the base value.
    - Keys only in *base* are preserved.
    - Keys only in *overrides* are added.
    """
    result = copy.deepcopy(base)
    for key, val in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


@dataclass
class OutputPaths:
    """Granular output paths for each artifact type.

    In study mode these map to the comprehensive directory structure
    (sdtm/production/programs, sdtm/qc/datasets, etc.).  In legacy mode
    they map to the flat orchestrator/outputs/ layout.
    """

    specs: Path
    production_programs: Path
    production_datasets: Path
    qc_programs: Path
    qc_datasets: Path
    compare: Path
    validation: Path
    reports: Path
    state: Path  # Where pipeline_state.json is stored


@dataclass
class ResolvedConfig:
    """Fully resolved configuration with path information."""

    config: Dict[str, Any]
    standards_dir: Path
    study_dir: Optional[Path]
    study_id: str
    is_study_mode: bool
    project_root: Path


class ConfigResolver:
    """
    Resolve configuration by layering company standards with study overrides.

    Usage::

        resolver = ConfigResolver(project_root, study="XYZ_2026_001")
        resolved = resolver.resolve()
        config = resolved.config
    """

    def __init__(self, project_root: Path, study: Optional[str] = None) -> None:
        self.project_root = project_root
        self.study = study
        self.standards_dir = project_root / "standards"
        self.study_dir = project_root / "studies" / study if study else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> ResolvedConfig:
        """
        Build a merged config dict.

        When *study* is set:
          standards/config.base.yaml  <-merged-  studies/{study}/config.yaml

        When *study* is None (backward compat):
          orchestrator/config.yaml    (used as-is)
        """
        if self.study and self.study_dir:
            base = self._load_yaml(self.standards_dir / "config.base.yaml")
            study_cfg = self._load_yaml(self.study_dir / "config.yaml")
            config = deep_merge(base, study_cfg)
            study_id = config.get("study", {}).get("study_id", self.study)
            return ResolvedConfig(
                config=config,
                standards_dir=self.standards_dir,
                study_dir=self.study_dir,
                study_id=study_id,
                is_study_mode=True,
                project_root=self.project_root,
            )

        # Backward-compatible: single config.yaml
        config = self._load_yaml(self.project_root / "orchestrator" / "config.yaml")
        study_id = config.get("study", {}).get("study_id", "")
        return ResolvedConfig(
            config=config,
            standards_dir=self.standards_dir,
            study_dir=None,
            study_id=study_id,
            is_study_mode=False,
            project_root=self.project_root,
        )

    def resolve_function_registries(self) -> List[Path]:
        """
        Return function registry paths in merge order.

        [0] = standard registry (base)
        [1] = study-specific registry (overrides / additions)  -- optional
        """
        paths: List[Path] = []

        # Standard registry
        std_reg = self.standards_dir / "r_functions" / "function_registry.json"
        if std_reg.exists():
            paths.append(std_reg.resolve())
        else:
            # Fall back to root-level
            fallback = self.project_root / "r_functions" / "function_registry.json"
            if fallback.exists():
                paths.append(fallback)

        # Study-specific additional registry
        if self.study_dir:
            study_reg = self.study_dir / "r_functions" / "function_registry.json"
            if study_reg.exists():
                paths.append(study_reg)

        return paths

    def resolve_ig_content_dirs(self) -> List[Path]:
        """
        Return IG content directories in search order (study-specific first).
        """
        dirs: List[Path] = []

        # Study-specific IG content (searched first)
        if self.study_dir:
            study_ig = self.study_dir / "ig_content"
            if study_ig.exists():
                dirs.append(study_ig)

        # Standard IG content
        std_ig = self.standards_dir / "ig_content"
        if std_ig.exists():
            dirs.append(std_ig.resolve())
        else:
            # Fall back to root-level
            fallback = self.project_root / "sdtm_ig_db" / "sdtm_ig_content"
            if fallback.exists():
                dirs.append(fallback)

        return dirs

    def resolve_ct_lookups(self) -> List[Path]:
        """
        Return CT lookup paths in merge order.

        [0] = standard CT lookup
        [1] = study-specific overrides  -- optional
        """
        paths: List[Path] = []

        # Standard CT
        std_ct = self.standards_dir / "ct_lookup.csv"
        if std_ct.exists():
            paths.append(std_ct.resolve())
        else:
            fallback = self.project_root / "macros" / "ct_lookup.csv"
            if fallback.exists():
                paths.append(fallback)

        # Study-specific CT overrides
        if self.study_dir:
            study_ct = self.study_dir / "ct_overrides.csv"
            if study_ct.exists():
                paths.append(study_ct)

        return paths

    def resolve_memory_dirs(self) -> List[Path]:
        """
        Return memory directories in merge order.

        [0] = standard memory (company-level)
        [1] = study-specific memory -- optional
        """
        dirs: List[Path] = []

        # Standard memory
        std_mem = self.standards_dir / "memory"
        if std_mem.exists():
            dirs.append(std_mem.resolve())

        # Study-specific memory
        if self.study_dir:
            study_mem = self.study_dir / "memory"
            dirs.append(study_mem)  # may not exist yet; MemoryManager creates on write

        return dirs

    def resolve_coding_standards(self) -> Path:
        """Return path to the coding standards file."""
        return self.standards_dir / "coding_standards.yaml"

    def resolve_output_dir(self) -> Path:
        """Return the output directory (study-specific or default).

        In study mode this returns the study directory itself (output_paths
        are relative to it).  In legacy mode, orchestrator/outputs/.
        """
        if self.study_dir:
            return self.study_dir
        # From config
        cfg = self.resolve().config
        raw = cfg.get("paths", {}).get("output_dir", "orchestrator/outputs")
        return self.project_root / str(raw).lstrip("./")

    def resolve_output_paths(self) -> OutputPaths:
        """Return granular output paths for each artifact type.

        In study mode, reads ``output_paths`` from the merged config and
        resolves them relative to the study directory.  In legacy mode,
        derives paths from the flat ``output_dir`` layout.
        """
        cfg = self.resolve().config
        op = cfg.get("output_paths", {})

        if self.study_dir and op:
            # Study mode: resolve paths relative to study directory
            def _rel(key: str, fallback: str) -> Path:
                raw = str(op.get(key, fallback)).lstrip("./")
                return self.study_dir / raw

            return OutputPaths(
                specs=_rel("specs", "sdtm/specs"),
                production_programs=_rel("production_programs", "sdtm/production/programs"),
                production_datasets=_rel("production_datasets", "sdtm/production/datasets"),
                qc_programs=_rel("qc_programs", "sdtm/qc/programs"),
                qc_datasets=_rel("qc_datasets", "sdtm/qc/datasets"),
                compare=_rel("compare", "sdtm/qc/compare"),
                validation=_rel("validation", "sdtm/validation"),
                reports=_rel("reports", "sdtm/reports"),
                state=self.study_dir / "sdtm",
            )

        # Legacy mode: flat structure under output_dir
        out = self.resolve_output_dir()
        return OutputPaths(
            specs=out / "specs",
            production_programs=out / "programs",
            production_datasets=out / "datasets",
            qc_programs=out / "qc",
            qc_datasets=out / "qc",
            compare=out / "qc",
            validation=out / "validation",
            reports=out / "reports",
            state=out,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load a YAML file; return empty dict if missing."""
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
