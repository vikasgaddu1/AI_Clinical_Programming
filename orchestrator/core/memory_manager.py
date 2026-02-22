"""
Memory manager: persistent memory across pipeline runs.

Manages three categories of memory at two tiers (company + study):

  1. Decision records   — human review choices with outcomes
  2. Pitfall records    — errors, mismatches, and resolutions
  3. Domain context     — cross-domain decision snapshots
  4. Coding standards   — enforced code style and CDISC rules
  5. Program headers    — standard header template with modification history

Memory files live in:
  standards/memory/          (company-wide, promoted patterns)
  studies/{study}/memory/    (study-specific, accumulated per run)
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

@dataclass
class DecisionRecord:
    """A single human review decision."""

    domain: str
    variable: str
    choice: str
    alternatives_shown: List[str]
    rationale: str
    source: str = "manual"  # "convention" | "manual" | "manual_override"
    outcome: str = "pending"  # "success" | "mismatch" | "validation_fail"
    run_timestamp: str = ""
    study_id: str = ""


@dataclass
class PitfallRecord:
    """A known failure pattern with root cause and resolution."""

    category: str  # "r_script_error" | "comparison_mismatch" | "validation_fail" | "ct_mapping"
    domain: str
    description: str
    root_cause: str = ""
    resolution: str = ""
    severity: str = "warning"  # "blocker" | "warning" | "info"
    run_timestamp: str = ""
    study_id: str = ""
    promotion_status: str = ""  # "" | "pending" | "promoted"


@dataclass
class DomainContext:
    """Cross-domain snapshot of key decisions and derived variables."""

    domain: str
    key_decisions: Dict[str, str] = field(default_factory=dict)
    derived_variables: List[str] = field(default_factory=list)
    timestamp: str = ""
    study_id: str = ""


# ------------------------------------------------------------------
# MemoryManager
# ------------------------------------------------------------------

class MemoryManager:
    """
    Persistent memory across pipeline runs.

    Reads from company standards + study-specific memory directories.
    Writes to study-specific memory only (company-level via promotion).

    Usage::

        memory = MemoryManager(
            standards_dir=Path("standards"),
            study_dir=Path("studies/XYZ_2026_001"),
        )
        standards = memory.get_coding_standards()
        header = memory.get_program_header(program_name="dm_production.R", ...)
        pitfalls = memory.get_relevant_pitfalls("DM", "r_script_error")
    """

    def __init__(
        self,
        standards_dir: Path,
        study_dir: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self._standards_dir = standards_dir
        self._study_dir = study_dir
        self._project_root = project_root or standards_dir.parent
        self._standards_memory = standards_dir / "memory"
        self._study_memory = study_dir / "memory" if study_dir else None

    # ------------------------------------------------------------------
    # Read: coding standards
    # ------------------------------------------------------------------

    def get_coding_standards(self) -> Dict[str, Any]:
        """Load coding standards from standards/coding_standards.yaml."""
        path = self._standards_dir / "coding_standards.yaml"
        return self._load_yaml(path)

    def get_program_header(self, **fields: str) -> str:
        """
        Render the program header template with the given fields.

        Required fields: program_name, description, domain, study_id,
        author, creation_date, input_datasets, output_datasets, macros_used.

        Optional: modification_history (multi-line string of prior edits).
        """
        template_path = self._standards_memory / "program_header_template.txt"
        if not template_path.exists():
            return ""
        template = template_path.read_text(encoding="utf-8")

        # Default modification_history to empty placeholder
        if "modification_history" not in fields:
            fields["modification_history"] = "#'          |          | Initial creation"

        # Fill template
        for key, value in fields.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    # ------------------------------------------------------------------
    # Read: pitfalls (layered: company + study)
    # ------------------------------------------------------------------

    def get_relevant_pitfalls(
        self, domain: str, category: Optional[str] = None
    ) -> List[PitfallRecord]:
        """
        Get pitfalls relevant to a domain, merged from company + study.

        Study-specific pitfalls appear first (more relevant to current work).
        Optionally filter by category.
        """
        result: List[PitfallRecord] = []

        # Study-specific first
        if self._study_memory:
            result.extend(self._load_pitfalls(self._study_memory / "pitfalls.yaml"))

        # Then company-wide
        result.extend(self._load_pitfalls(self._standards_memory / "pitfalls.yaml"))

        # Filter by domain
        result = [p for p in result if p.domain == domain or p.domain == "*"]

        # Filter by category if specified
        if category:
            result = [p for p in result if p.category == category]

        return result

    # ------------------------------------------------------------------
    # Read: decision history (layered: company patterns + study history)
    # ------------------------------------------------------------------

    def get_decision_history(
        self, domain: str, variable: Optional[str] = None
    ) -> List[DecisionRecord]:
        """
        Get past decisions for a domain, from study memory.

        Optionally filter to a specific variable.
        """
        records: List[DecisionRecord] = []

        if self._study_memory:
            records.extend(
                self._load_decisions(self._study_memory / "decisions_log.yaml")
            )

        # Filter
        records = [r for r in records if r.domain == domain]
        if variable:
            records = [r for r in records if r.variable == variable]

        return records

    # ------------------------------------------------------------------
    # Read: domain context (cross-domain awareness)
    # ------------------------------------------------------------------

    def get_domain_context(self, domain: str) -> Optional[DomainContext]:
        """Get the latest context snapshot for a specific domain."""
        all_ctx = self.get_all_domain_contexts()
        return all_ctx.get(domain)

    def get_all_domain_contexts(self) -> Dict[str, DomainContext]:
        """Get all domain context snapshots for the current study."""
        if not self._study_memory:
            return {}
        path = self._study_memory / "domain_context.yaml"
        data = self._load_yaml(path)
        result: Dict[str, DomainContext] = {}
        for domain, ctx_data in data.get("domains", {}).items():
            result[domain] = DomainContext(
                domain=domain,
                key_decisions=ctx_data.get("key_decisions", {}),
                derived_variables=ctx_data.get("derived_variables", []),
                timestamp=ctx_data.get("timestamp", ""),
                study_id=ctx_data.get("study_id", ""),
            )
        return result

    # ------------------------------------------------------------------
    # Write: decision records
    # ------------------------------------------------------------------

    def record_decision(self, record: DecisionRecord) -> None:
        """Append a decision record to the study's decisions log."""
        if not self._study_memory:
            return
        self._study_memory.mkdir(parents=True, exist_ok=True)
        path = self._study_memory / "decisions_log.yaml"
        data = self._load_yaml(path)
        if "decisions" not in data:
            data["decisions"] = []

        # Add timestamp if not set
        if not record.run_timestamp:
            record.run_timestamp = datetime.now().isoformat()

        data["decisions"].append(asdict(record))
        self._save_yaml(path, data)

    # ------------------------------------------------------------------
    # Write: pitfall records
    # ------------------------------------------------------------------

    def record_pitfall(self, record: PitfallRecord) -> None:
        """Append a pitfall record to the study's pitfalls log."""
        if not self._study_memory:
            return
        self._study_memory.mkdir(parents=True, exist_ok=True)
        path = self._study_memory / "pitfalls.yaml"
        data = self._load_yaml(path)
        if "pitfalls" not in data:
            data["pitfalls"] = []

        if not record.run_timestamp:
            record.run_timestamp = datetime.now().isoformat()

        data["pitfalls"].append(asdict(record))
        self._save_yaml(path, data)

    def update_pitfall_resolution(
        self, domain: str, description_match: str, resolution: str
    ) -> None:
        """Update the resolution field of a matching pitfall (e.g., after retry succeeds)."""
        if not self._study_memory:
            return
        path = self._study_memory / "pitfalls.yaml"
        data = self._load_yaml(path)
        for entry in data.get("pitfalls", []):
            if entry.get("domain") == domain and description_match in entry.get(
                "description", ""
            ):
                entry["resolution"] = resolution
        self._save_yaml(path, data)

    # ------------------------------------------------------------------
    # Write: domain context
    # ------------------------------------------------------------------

    def save_domain_context(self, context: DomainContext) -> None:
        """Save or update a domain context snapshot."""
        if not self._study_memory:
            return
        self._study_memory.mkdir(parents=True, exist_ok=True)
        path = self._study_memory / "domain_context.yaml"
        data = self._load_yaml(path)
        if "domains" not in data:
            data["domains"] = {}

        if not context.timestamp:
            context.timestamp = datetime.now().isoformat()

        data["domains"][context.domain] = asdict(context)
        self._save_yaml(path, data)

    # ------------------------------------------------------------------
    # Write: modification history
    # ------------------------------------------------------------------

    def update_modification_history(
        self,
        program_name: str,
        author: str,
        description: str,
    ) -> None:
        """Record a modification history entry for a program."""
        if not self._study_memory:
            return
        self._study_memory.mkdir(parents=True, exist_ok=True)
        path = self._study_memory / "modification_history.yaml"
        data = self._load_yaml(path)
        if "programs" not in data:
            data["programs"] = {}
        if program_name not in data["programs"]:
            data["programs"][program_name] = []

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "author": author,
            "description": description,
        }
        data["programs"][program_name].append(entry)
        self._save_yaml(path, data)

    def get_modification_history(self, program_name: str) -> str:
        """
        Get formatted modification history lines for a program header.

        Returns multi-line string of '#' date | author | description' entries.
        """
        if not self._study_memory:
            return "#'          |          | Initial creation"
        path = self._study_memory / "modification_history.yaml"
        data = self._load_yaml(path)
        entries = data.get("programs", {}).get(program_name, [])
        if not entries:
            return "#'          |          | Initial creation"
        lines = []
        for e in entries:
            lines.append(
                f"#' {e.get('date', ''):<9}| {e.get('author', ''):<9}| {e.get('description', '')}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Promotion: study -> company (auto-flag + manual approve)
    # ------------------------------------------------------------------

    def get_promotable_patterns(self) -> List[Dict[str, Any]]:
        """
        Scan all studies for pitfalls that appear in 2+ studies.

        Returns a list of dicts with the pitfall details and the studies
        where it was observed.
        """
        studies_dir = self._project_root / "studies"
        if not studies_dir.exists():
            return []

        # Collect all study pitfalls keyed by (category, description)
        pattern_map: Dict[tuple, List[Dict[str, Any]]] = {}
        for study_path in studies_dir.iterdir():
            if study_path.name.startswith("_") or not study_path.is_dir():
                continue
            pitfalls_file = study_path / "memory" / "pitfalls.yaml"
            if not pitfalls_file.exists():
                continue
            data = self._load_yaml(pitfalls_file)
            for p in data.get("pitfalls", []):
                key = (p.get("category", ""), p.get("description", ""))
                if key not in pattern_map:
                    pattern_map[key] = []
                pattern_map[key].append({
                    "study": study_path.name,
                    "pitfall": p,
                })

        # Filter to patterns seen in 2+ studies
        promotable = []
        for key, occurrences in pattern_map.items():
            study_names = {o["study"] for o in occurrences}
            if len(study_names) >= 2:
                promotable.append({
                    "category": key[0],
                    "description": key[1],
                    "studies": list(study_names),
                    "occurrences": occurrences,
                    "first_occurrence": occurrences[0]["pitfall"],
                })

        return promotable

    def promote_pitfall(
        self, pitfall: PitfallRecord, approved_by: str
    ) -> None:
        """
        Promote a study-level pitfall to company standards.

        Requires explicit approval (approved_by identifies the reviewer).
        """
        self._standards_memory.mkdir(parents=True, exist_ok=True)
        path = self._standards_memory / "pitfalls.yaml"
        data = self._load_yaml(path)
        if "pitfalls" not in data:
            data["pitfalls"] = []

        entry = asdict(pitfall)
        entry["promoted_by"] = approved_by
        entry["promotion_date"] = datetime.now().strftime("%Y-%m-%d")
        entry["promotion_status"] = "promoted"
        data["pitfalls"].append(entry)
        self._save_yaml(path, data)

    def list_pending_promotions(self) -> List[Dict[str, Any]]:
        """
        List pitfalls flagged for promotion but not yet approved.

        Convenience wrapper around get_promotable_patterns() that
        excludes already-promoted items.
        """
        already_promoted = set()
        std_data = self._load_yaml(self._standards_memory / "pitfalls.yaml")
        for p in std_data.get("pitfalls", []):
            already_promoted.add((p.get("category", ""), p.get("description", "")))

        candidates = self.get_promotable_patterns()
        return [
            c
            for c in candidates
            if (c["category"], c["description"]) not in already_promoted
        ]

    # ------------------------------------------------------------------
    # Context builder (convenience for agents)
    # ------------------------------------------------------------------

    def build_agent_context(
        self,
        domain: str,
        agent_type: str,
        study_id: str = "",
        program_name: str = "",
    ) -> Dict[str, Any]:
        """
        Build a memory context dict for injection into an agent's prompt.

        Parameters
        ----------
        domain : str
            SDTM domain (e.g., "DM", "AE").
        agent_type : str
            One of "spec_builder", "production", "qc", "validation", "human_review".
        study_id : str
            Study identifier for header population.
        program_name : str
            R program filename (for header and modification history).
        """
        context: Dict[str, Any] = {
            "coding_standards": self.get_coding_standards(),
        }

        if agent_type in ("production", "qc"):
            # Program header
            standards = context["coding_standards"]
            header_cfg = standards.get("program_header", {})
            author = (
                header_cfg.get("qc_author", "QC Programmer Agent (AI-generated)")
                if agent_type == "qc"
                else header_cfg.get(
                    "default_author",
                    "Production Programmer Agent (AI-generated)",
                )
            )
            mod_history = self.get_modification_history(program_name)
            context["program_header"] = self.get_program_header(
                program_name=program_name,
                description=f"{domain} {agent_type} program",
                domain=domain,
                study_id=study_id,
                author=author,
                creation_date=datetime.now().strftime("%Y-%m-%d"),
                modification_history=mod_history,
                input_datasets=f"raw_{domain.lower()}.csv",
                output_datasets=f"{domain.lower()}.parquet, {domain.lower()}.xpt",
                macros_used="iso_date, derive_age, assign_ct",
            )
            context["known_pitfalls"] = [
                asdict(p)
                for p in self.get_relevant_pitfalls(domain, "r_script_error")
            ]
            context["cross_domain"] = {
                k: asdict(v) for k, v in self.get_all_domain_contexts().items()
            }

        if agent_type == "spec_builder":
            context["past_decisions"] = [
                asdict(r) for r in self.get_decision_history(domain)
            ]
            context["known_pitfalls"] = [
                asdict(p) for p in self.get_relevant_pitfalls(domain)
            ]

        if agent_type == "validation":
            context["known_pitfalls"] = [
                asdict(p)
                for p in self.get_relevant_pitfalls(domain, "validation_fail")
            ]
            context["past_decisions"] = [
                asdict(r) for r in self.get_decision_history(domain)
            ]

        if agent_type == "human_review":
            context["past_decisions"] = [
                asdict(r) for r in self.get_decision_history(domain)
            ]
            context["cross_domain"] = {
                k: asdict(v) for k, v in self.get_all_domain_contexts().items()
            }

        return context

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_pitfalls(self, path: Path) -> List[PitfallRecord]:
        """Load pitfall records from a YAML file."""
        data = self._load_yaml(path)
        result = []
        for entry in data.get("pitfalls", []):
            result.append(PitfallRecord(
                category=entry.get("category", ""),
                domain=entry.get("domain", ""),
                description=entry.get("description", ""),
                root_cause=entry.get("root_cause", ""),
                resolution=entry.get("resolution", ""),
                severity=entry.get("severity", "warning"),
                run_timestamp=entry.get("run_timestamp", ""),
                study_id=entry.get("study_id", ""),
                promotion_status=entry.get("promotion_status", ""),
            ))
        return result

    def _load_decisions(self, path: Path) -> List[DecisionRecord]:
        """Load decision records from a YAML file."""
        data = self._load_yaml(path)
        result = []
        for entry in data.get("decisions", []):
            result.append(DecisionRecord(
                domain=entry.get("domain", ""),
                variable=entry.get("variable", ""),
                choice=entry.get("choice", ""),
                alternatives_shown=entry.get("alternatives_shown", []),
                rationale=entry.get("rationale", ""),
                source=entry.get("source", "manual"),
                outcome=entry.get("outcome", "pending"),
                run_timestamp=entry.get("run_timestamp", ""),
                study_id=entry.get("study_id", ""),
            ))
        return result

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        """Load a YAML file; return empty dict if missing."""
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
        """Write a dict to a YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
