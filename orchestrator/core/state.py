"""
Pipeline state management for the SDTM orchestrator.

Tracks current phase, spec status, production/QC status, comparison result,
and paths to all generated artifacts.  Supports JSON persistence so the
pipeline can be resumed after a crash or interruption.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PipelineState:
    """Shared state across all agents and orchestration steps."""

    study_id: str = ""
    domain: str = ""
    current_phase: str = "spec_building"  # spec_building | spec_review | human_review | production | qc | comparison | validation
    spec_status: str = "draft"  # draft | reviewed | approved | finalized
    production_status: str = "pending"
    qc_status: str = "pending"
    comparison_result: str = "pending"  # pending | match | mismatch
    comparison_iteration: int = 0
    validation_status: str = "pending"
    human_decisions: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)

    def set_phase(self, phase: str) -> None:
        self.current_phase = phase

    def set_spec_status(self, status: str) -> None:
        self.spec_status = status

    def record_error(self, message: str) -> None:
        self.error_log.append(message)

    def set_artifact(self, key: str, path: str) -> None:
        self.artifacts[key] = path

    def get_artifact(self, key: str) -> Optional[str]:
        return self.artifacts.get(key)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Persist pipeline state to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "PipelineState":
        """Load pipeline state from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
