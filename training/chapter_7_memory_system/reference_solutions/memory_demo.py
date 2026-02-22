"""
Chapter 7 Reference Solution: Full memory system demonstration.

This script demonstrates the complete memory workflow:
1. Load coding standards
2. Record decisions and pitfalls
3. Build agent context with memory
4. Generate R code with header and standards compliance
5. Save domain context for cross-domain use
6. Detect and promote recurring pitfalls

Run from project root:
    python training/chapter_7_memory_system/reference_solutions/memory_demo.py
"""

import sys
from pathlib import Path

# add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.core.memory_manager import (
    MemoryManager,
    DecisionRecord,
    DomainContext,
    PitfallRecord,
)
from orchestrator.agents.production_programmer import generate_r_script


def main() -> None:
    standards_dir = project_root / "standards"
    study_dir = project_root / "studies" / "XYZ_2026_001"

    mm = MemoryManager(standards_dir, study_dir, project_root)

    # ── 1. coding standards ──────────────────────────────────────────
    print("=" * 60)
    print("1. CODING STANDARDS")
    print("=" * 60)
    cs = mm.get_coding_standards()
    print(f"  code case:      {cs['code_style']['case']}")
    print(f"  sdtm vars:      {cs['variable_naming']['sdtm_variables']}")
    print(f"  r functions:    {cs['variable_naming']['r_functions']}")
    print(f"  max var name:   {cs['cdisc_compliance']['sdtm']['max_variable_name_length']}")
    print(f"  max label:      {cs['cdisc_compliance']['sdtm']['max_label_length']}")
    print()

    # ── 2. record decisions ──────────────────────────────────────────
    print("=" * 60)
    print("2. RECORD DECISIONS")
    print("=" * 60)
    decisions = [
        DecisionRecord(
            domain="DM", variable="RACE", choice="B",
            alternatives_shown=["A", "B", "C"],
            rationale="Company default: SUPPDM approach",
            source="convention", outcome="success",
            study_id="XYZ-2026-001",
        ),
        DecisionRecord(
            domain="DM", variable="RFSTDTC", choice="A",
            alternatives_shown=["A", "B"],
            rationale="Use informed consent date",
            source="convention", outcome="success",
            study_id="XYZ-2026-001",
        ),
    ]
    for d in decisions:
        mm.record_decision(d)
        print(f"  recorded: {d.variable} = {d.choice} ({d.source})")

    # read back
    history = mm.get_decision_history("DM")
    print(f"\n  decisions on disk: {len(history)}")
    print()

    # ── 3. record pitfalls ───────────────────────────────────────────
    print("=" * 60)
    print("3. RECORD PITFALLS")
    print("=" * 60)
    mm.record_pitfall(PitfallRecord(
        category="r_script_error", domain="DM",
        description="iso_date fails on ambiguous slash-separated dates",
        root_cause="Both parts <= 12 defaults to MM/DD/YYYY",
        resolution="Use infmt parameter for non-US formats",
        severity="blocker", study_id="XYZ-2026-001",
    ))
    print("  recorded: iso_date ambiguity pitfall")

    pitfalls = mm.get_relevant_pitfalls("DM", "r_script_error")
    print(f"  pitfalls on disk: {len(pitfalls)}")
    print()

    # ── 4. generate R code with memory ───────────────────────────────
    print("=" * 60)
    print("4. GENERATE R CODE WITH MEMORY CONTEXT")
    print("=" * 60)
    ctx = mm.build_agent_context("DM", "production", "XYZ-2026-001", "dm_production.R")
    print(f"  context keys: {list(ctx.keys())}")
    print(f"  known pitfalls: {len(ctx.get('known_pitfalls', []))}")

    spec = {
        "study_id": "XYZ-2026-001",
        "domain": "DM",
        "human_decisions": {"RACE": {"choice": "B"}},
        "variables": [],
    }
    script = generate_r_script(
        spec=spec,
        raw_data_path="study_data/raw_dm.csv",
        output_dataset_path="output/dm.parquet",
        function_library_path="r_functions",
        ct_lookup_path="macros/ct_lookup.csv",
        memory_context=ctx,
    )
    print(f"  generated script: {len(script.split(chr(10)))} lines")
    print(f"  starts with header: {script.startswith(\"#'\")}")
    print(f"  has RACE approach B: {'approach B' in script}")
    print()

    # ── 5. save domain context ───────────────────────────────────────
    print("=" * 60)
    print("5. SAVE DOMAIN CONTEXT (CROSS-DOMAIN)")
    print("=" * 60)
    mm.save_domain_context(DomainContext(
        domain="DM",
        key_decisions={"RACE": "B", "RFSTDTC": "A"},
        derived_variables=["USUBJID", "AGE", "AGEU", "BRTHDTC", "RFSTDTC"],
        study_id="XYZ-2026-001",
    ))
    print("  saved DM domain context")

    # simulate AE reading it
    ae_ctx = mm.build_agent_context("AE", "production", "XYZ-2026-001", "ae_production.R")
    dm_info = ae_ctx.get("cross_domain", {}).get("DM", {})
    if dm_info:
        print(f"  AE sees DM decisions: {dm_info.get('key_decisions', {})}")
    print()

    # ── 6. clean up ──────────────────────────────────────────────────
    print("=" * 60)
    print("6. CLEAN UP")
    print("=" * 60)
    import os
    for f in ["decisions_log.yaml", "pitfalls.yaml", "domain_context.yaml"]:
        path = study_dir / "memory" / f
        if path.exists():
            os.remove(path)
            print(f"  removed: {path.name}")

    print("\ndone.")


if __name__ == "__main__":
    main()
