"""
Training context gatherer: reads project state for training material generation.

Gathers domain context (IG variables, functions, raw data profile),
project context (skills, agents, pipeline stages, artifacts), and
existing training materials for reference.

Read-only module -- never modifies project state.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.core.function_loader import FunctionLoader
from orchestrator.core.ig_client import IGClient


@dataclass
class DomainContext:
    """All domain-specific information for training generation."""

    domain: str
    ig_variables: List[Dict[str, str]] = field(default_factory=list)
    required_variables: List[str] = field(default_factory=list)
    conditional_variables: List[str] = field(default_factory=list)
    ct_variables: List[Dict[str, str]] = field(default_factory=list)
    variable_details: Dict[str, str] = field(default_factory=dict)
    raw_data_profile: Dict[str, Any] = field(default_factory=dict)
    available_functions: List[Dict[str, Any]] = field(default_factory=list)
    function_dependency_order: List[str] = field(default_factory=list)
    ig_available: bool = False


@dataclass
class ProjectContext:
    """All project-level information for training generation."""

    study_id: str = ""
    skills: List[Dict[str, str]] = field(default_factory=list)
    agents: List[Dict[str, str]] = field(default_factory=list)
    pipeline_stages: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    existing_spec: Optional[Dict[str, Any]] = None
    existing_chapters: List[Dict[str, Any]] = field(default_factory=list)
    mcp_tools: List[Dict[str, str]] = field(default_factory=list)


def gather_domain_context(
    domain: str,
    ig_client: IGClient,
    function_loader: FunctionLoader,
    raw_data_path: str,
) -> DomainContext:
    """Read IG, function registry, and raw data to build domain context."""
    ctx = DomainContext(domain=domain)

    # IG variables
    ctx.ig_variables = ig_client.get_domain_variables(domain)
    ctx.required_variables = ig_client.get_required_variables(domain)
    ctx.conditional_variables = ig_client.get_conditional_variables(domain)
    ctx.ct_variables = ig_client.get_ct_variables(domain)
    ctx.ig_available = bool(ctx.ig_variables)

    # Variable details
    for var_info in ctx.ig_variables:
        var_name = var_info.get("variable", "")
        if var_name:
            detail = ig_client.get_variable_detail(domain, var_name)
            if detail:
                ctx.variable_details[var_name] = detail

    # Functions
    ctx.available_functions = function_loader.get_functions()
    ctx.function_dependency_order = function_loader.get_dependency_order()

    # Raw data profile
    raw_path = Path(raw_data_path)
    if raw_path.exists():
        try:
            from orchestrator.agents.spec_builder import profile_raw_data

            ctx.raw_data_profile = profile_raw_data(raw_data_path)
        except Exception:
            ctx.raw_data_profile = {"error": "Could not profile raw data"}
    else:
        ctx.raw_data_profile = {"error": f"File not found: {raw_data_path}"}

    return ctx


def gather_project_context(
    config: dict,
    spec_manager: Any,
    domain: str,
    project_root: Path,
) -> ProjectContext:
    """Scan project structure for skills, agents, stages, existing materials."""
    ctx = ProjectContext()
    ctx.study_id = config.get("study", {}).get("study_id", "XYZ-2026-001")
    ctx.config = config

    # Scan skills
    skills_dir = project_root / ".claude" / "skills"
    if skills_dir.exists():
        for md in sorted(skills_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            # Extract title from first heading
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = title_match.group(1) if title_match else md.stem
            # Extract description from frontmatter
            desc_match = re.search(r"description:\s*(.+)", text)
            desc = desc_match.group(1).strip() if desc_match else ""
            ctx.skills.append({
                "name": md.stem,
                "file": str(md.relative_to(project_root)),
                "title": title,
                "description": desc,
            })

    # Scan agents
    agents_dir = project_root / "orchestrator" / "agents"
    if agents_dir.exists():
        for py in sorted(agents_dir.glob("*.py")):
            if py.name.startswith("__"):
                continue
            text = py.read_text(encoding="utf-8")
            # Extract docstring first line
            doc_match = re.search(r'"""(.+?)(?:\n|""")', text)
            purpose = doc_match.group(1).strip() if doc_match else py.stem
            ctx.agents.append({
                "name": py.stem,
                "file": str(py.relative_to(project_root)),
                "purpose": purpose,
            })

    # Pipeline stages (hardcoded -- these are the stages in main.py)
    ctx.pipeline_stages = [
        "spec_build",
        "spec_review",
        "human_review",
        "production",
        "qc",
        "compare",
        "validate",
    ]

    # Existing spec
    if spec_manager:
        ctx.existing_spec = spec_manager.read_spec(domain, approved=True)
        if ctx.existing_spec is None:
            ctx.existing_spec = spec_manager.read_spec(domain, approved=False)

    # Existing training chapters
    training_dir = project_root / "training"
    if training_dir.exists():
        for chapter_dir in sorted(training_dir.iterdir()):
            if chapter_dir.is_dir() and chapter_dir.name.startswith("chapter_"):
                meta_file = chapter_dir / "metadata.json"
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    except Exception:
                        meta = {}
                else:
                    meta = {}
                # Extract chapter number from dir name
                num_match = re.match(r"chapter_(\d+)", chapter_dir.name)
                chapter_num = int(num_match.group(1)) if num_match else 0
                ctx.existing_chapters.append({
                    "number": chapter_num,
                    "directory": chapter_dir.name,
                    "title": meta.get("title", chapter_dir.name),
                    "skill_level": meta.get("skill_level", "unknown"),
                })

    # MCP tools (scan mcp_server.py for tool names)
    mcp_file = project_root / "mcp_server.py"
    if mcp_file.exists():
        text = mcp_file.read_text(encoding="utf-8")
        for match in re.finditer(r'name="(\w+)"', text):
            ctx.mcp_tools.append({"name": match.group(1)})

    return ctx
