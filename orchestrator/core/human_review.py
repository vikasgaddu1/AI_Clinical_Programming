"""
Human review gate: present spec and collect decisions on flagged items.

CLI-based interface: display spec, show decision options for variables
with human_decision_required, accept user selection, record decisions.

Memory-aware: writes DecisionRecords via MemoryManager after review,
and shows past decision history for context.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False
    Console = None
    Table = None
    Prompt = None


def _show_decision_history(memory_context: Optional[Dict[str, Any]], variable: str) -> None:
    """Display past decision history for a variable, if available."""
    if not memory_context:
        return
    past = [
        d for d in memory_context.get("past_decisions", [])
        if d.get("variable") == variable
    ]
    if past:
        print(f"  [Past decisions for {variable}]:")
        for d in past[-3:]:  # show last 3
            print(f"    {d.get('run_timestamp', '?')}: chose {d.get('choice')} "
                  f"({d.get('source')}) -> {d.get('outcome', 'pending')}")


def present_spec_for_review(
    spec: Dict[str, Any],
    conventions: Any = None,
    memory_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Present the mapping spec and collect human decisions for any variable
    with human_decision_required.

    When *conventions* is provided (a ConventionsManager instance), pre-configured
    decisions are shown with their rationale and the reviewer can accept by
    pressing Enter or type an alternative to override.

    When *memory_context* is provided, past decision history is shown for
    each decision point to inform the reviewer.

    Returns the spec with human_decisions added.
    """
    decisions: Dict[str, Any] = {}
    variables = spec.get("variables", [])
    domain = spec.get("domain", "")

    if _RICH_AVAILABLE:
        console = Console()
        title = f"{domain} Mapping Spec (excerpt)" if domain else "Mapping Spec (excerpt)"
        table = Table(title=title)
        table.add_column("Variable", style="cyan")
        table.add_column("Source", style="green")
        table.add_column("Mapping", style="white")
        table.add_column("Decision?", style="yellow")
        for v in variables[:20]:
            table.add_row(
                str(v.get("target_variable")),
                str(v.get("source_variable")),
                (str(v.get("mapping_logic")) or "")[:40] + "..." if len(str(v.get("mapping_logic") or "")) > 40 else str(v.get("mapping_logic") or ""),
                "Yes" if v.get("human_decision_required") else "No",
            )
        console.print(table)

    for v in variables:
        if not v.get("human_decision_required"):
            continue
        target = v.get("target_variable", "?")
        options = v.get("decision_options", [])
        if not options:
            continue

        # Show past decision history if available
        _show_decision_history(memory_context, target)

        # Check conventions for a pre-configured default
        convention_default = None
        if conventions:
            conv = conventions.get_decision(target)
            if conv:
                convention_default = conv

        if convention_default:
            # Show convention with confirm prompt
            print(f"\nDecision for {target}:")
            print(f"  Convention default -> {convention_default.approach}")
            print(f"  Rationale: {convention_default.rationale}")
            print(f"  Source: {convention_default.source}")
            for opt in options:
                desc = (opt.get("description") or "").replace("\u2192", "->")[:80]
                print(f"  {opt.get('id')}: {desc}...")
            choice = input(
                f"Accept [{convention_default.approach}] or enter alternative: "
            ).strip().upper()
            if not choice:
                choice = convention_default.approach
            decisions[target] = {
                "choice": choice,
                "options_shown": [o.get("id") for o in options],
                "source": "convention" if choice == convention_default.approach else "manual_override",
                "convention_rationale": convention_default.rationale,
            }
        else:
            # Interactive prompt with no default (original behavior)
            print(f"\nDecision required for {target}:")
            for opt in options:
                desc = (opt.get("description") or "").replace("\u2192", "->")[:80]
                print(f"  {opt.get('id')}: {desc}...")
            choice = input("Select option (A/B/C or custom text): ").strip().upper() or "B"
            decisions[target] = {
                "choice": choice,
                "options_shown": [o.get("id") for o in options],
                "source": "manual",
            }

    spec["human_decisions"] = decisions
    return spec


def write_decisions_to_memory(
    spec: Dict[str, Any],
    memory_manager: Any,
) -> None:
    """
    Write all human decisions from the spec to the memory manager.

    Called after present_spec_for_review() completes. Records each
    decision as a DecisionRecord for future reference.
    """
    if memory_manager is None:
        return

    from orchestrator.core.memory_manager import DecisionRecord

    domain = spec.get("domain", "")
    study_id = spec.get("study_id", "")
    decisions = spec.get("human_decisions", {})

    for variable, decision in decisions.items():
        record = DecisionRecord(
            domain=domain,
            variable=variable,
            choice=decision.get("choice", ""),
            alternatives_shown=decision.get("options_shown", []),
            rationale=decision.get("convention_rationale", ""),
            source=decision.get("source", "manual"),
            outcome="pending",
            study_id=study_id,
        )
        memory_manager.record_decision(record)


def record_approval(spec: Dict[str, Any], approved: bool, reviewer_note: str = "") -> None:
    """Record approval status and optional note on the spec."""
    spec["approved"] = approved
    spec["reviewer_note"] = reviewer_note
