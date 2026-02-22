"""
SDTM Orchestrator main entry point.

Run from project root:
  python orchestrator/main.py --domain DM
  python orchestrator/main.py --domain DM --stage spec_build
  python orchestrator/main.py --domain DM --stage production
  python orchestrator/main.py --domain DM --stage qc
  python orchestrator/main.py --domain DM --stage validate
  python orchestrator/main.py --domain DM --resume   # resume from saved state

Stages: spec_build, spec_review, human_review, production, qc, compare, validate
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from orchestrator.core.state import PipelineState
from orchestrator.core.function_loader import FunctionLoader
from orchestrator.core.ig_client import IGClient
from orchestrator.core.spec_manager import SpecManager
from orchestrator.core.human_review import present_spec_for_review, write_decisions_to_memory
from orchestrator.core.compare import compare_datasets
from orchestrator.core.memory_manager import MemoryManager, PitfallRecord, DomainContext
from orchestrator.agents.spec_builder import build_draft_spec
from orchestrator.agents.spec_reviewer import review_spec
from orchestrator.agents.production_programmer import generate_r_script
from orchestrator.agents.qc_programmer import generate_qc_r_script
from orchestrator.agents.validation_agent import (
    validate_dataset,
    generate_define_metadata,
    generate_p21_spec_sheet,
)


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ext(output_format: str) -> str:
    """Return file extension for the chosen primary format."""
    fmt = output_format.lower()
    if fmt == "parquet":
        return ".parquet"
    if fmt == "rds":
        return ".rds"
    return ".csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="SDTM Orchestrator (R)")
    parser.add_argument("--domain", default="DM", help="SDTM domain (default: DM)")
    parser.add_argument("--study", default=None, help="Study name (matches studies/{name}/ directory)")
    parser.add_argument("--stage", default=None, help="Run a single stage and exit")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--resume", action="store_true", help="Resume from saved pipeline state")
    parser.add_argument("--force", action="store_true", help="Continue past spec review failures")
    parser.add_argument("--training", action="store_true", help="Generate training materials instead of running pipeline")
    parser.add_argument("--level", default="operator", help="Skill level for training: consumer, operator, builder, architect")
    parser.add_argument("--topic", default="full_pipeline", help="Training topic: data_profiling, spec_building, production_programming, qc_and_comparison, validation, full_pipeline, human_review")
    parser.add_argument("--chapter", type=int, default=None, help="Chapter number for training generation")
    parser.add_argument("--report", action="store_true", help="Generate HTML pipeline report (standalone or after pipeline)")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Configuration resolution: multi-study mode vs legacy single-study
    # ------------------------------------------------------------------
    from orchestrator.core.config_resolver import OutputPaths

    conventions = None  # Will be set in study mode
    memory = None  # Will be set in study mode (MemoryManager)

    if args.study:
        # Multi-study mode: resolve layered config from standards + study
        from orchestrator.core.config_resolver import ConfigResolver
        from orchestrator.core.conventions import ConventionsManager

        resolver = ConfigResolver(PROJECT_ROOT, args.study)
        resolved = resolver.resolve()
        config = resolved.config

        # Conventions: standard + study-level overrides
        conv_std = resolved.standards_dir / "conventions.yaml"
        conv_study = resolved.study_dir / "conventions.yaml" if resolved.study_dir else None
        conventions = ConventionsManager(
            standards_path=conv_std if conv_std.exists() else None,
            study_path=conv_study if conv_study and conv_study.exists() else None,
        )
        conventions.load()
        if conventions.has_decisions():
            print(f"Loaded conventions: {conventions.summary()}")

        # Resolve paths from study config
        paths = config.get("paths", {})
        def _p(key: str, default: str) -> Path:
            val = str(paths.get(key, default)).lstrip("./")
            return PROJECT_ROOT / val

        raw_data          = _p("raw_data", "study_data/raw_dm.csv")
        annotated_crf     = _p("annotated_crf", "study_data/annotated_crf_dm.csv")
        function_library  = _p("function_library", "r_functions")
        ct_lookup         = _p("ct_lookup", "macros/ct_lookup.csv")

        # Granular output paths (study directory structure)
        op = resolver.resolve_output_paths()

        # Function registry: layered (standard + study-specific)
        registry_paths = resolver.resolve_function_registries()
        function_registry = registry_paths[0]
        additional_registries = registry_paths[1:]

        # IG content: layered (study-specific searched first, then standard)
        ig_content_dirs = resolver.resolve_ig_content_dirs()

        # Memory manager: persistent memory across pipeline runs
        memory = MemoryManager(
            standards_dir=resolved.standards_dir,
            study_dir=resolved.study_dir,
            project_root=PROJECT_ROOT,
        )

    else:
        # Legacy single-study mode: use orchestrator/config.yaml directly
        config_path = Path(args.config) if args.config else PROJECT_ROOT / "orchestrator" / "config.yaml"
        config = load_config(config_path)

        paths = config.get("paths", {})
        def _p(key: str, default: str) -> Path:
            return PROJECT_ROOT / str(paths.get(key, default)).lstrip("./")

        raw_data          = _p("raw_data", "study_data/raw_dm.csv")
        annotated_crf     = _p("annotated_crf", "study_data/annotated_crf_dm.csv")
        function_registry = _p("function_registry", "r_functions/function_registry.json")
        function_library  = _p("function_library", "r_functions")
        ct_lookup         = _p("ct_lookup", "macros/ct_lookup.csv")
        additional_registries = []
        ig_content_dirs = None  # IGClient will use default

        # Legacy flat output paths
        output_dir = _p("output_dir", "orchestrator/outputs")
        op = OutputPaths(
            specs=output_dir / "specs",
            production_programs=output_dir / "programs",
            production_datasets=output_dir / "datasets",
            qc_programs=output_dir / "qc",
            qc_datasets=output_dir / "qc",
            compare=output_dir / "qc",
            validation=output_dir / "validation",
            reports=output_dir / "reports",
            state=output_dir,
        )

    # Ensure all output directories exist
    for d in (op.specs, op.production_programs, op.production_datasets,
              op.qc_programs, op.qc_datasets, op.compare, op.validation,
              op.reports, op.state):
        d.mkdir(parents=True, exist_ok=True)

    study_id      = config.get("study", {}).get("study_id", "XYZ-2026-001")
    domain        = args.domain
    r_config      = config.get("r", {})
    output_format = r_config.get("output_format", "parquet")
    rscript_path  = r_config.get("rscript_path", "Rscript")
    write_xpt     = bool(r_config.get("write_xpt", True))
    max_iterations = config.get("comparison", {}).get("max_iterations", 5)

    # XPT goes alongside production datasets or in validation dir
    xpt_dir = op.validation
    xpt_dir.mkdir(parents=True, exist_ok=True)

    ext = _ext(output_format)

    # State: load from disk if --resume, otherwise fresh
    state_file = op.state / "pipeline_state.json"
    if args.resume and state_file.exists():
        state = PipelineState.load(str(state_file))
        print(f"Resumed pipeline from phase: {state.current_phase}")
    else:
        state = PipelineState(study_id=study_id, domain=domain)

    function_loader = FunctionLoader(
        str(function_registry),
        additional_paths=[str(p) for p in additional_registries] if additional_registries else None,
    )
    ig_client = IGClient(
        config.get("database"),
        content_dirs=[str(d) for d in ig_content_dirs] if ig_content_dirs else None,
    )
    spec_manager = SpecManager(output_dir=".", specs_dir=str(op.specs))

    # ------ Training generation mode (independent from pipeline) ------
    if args.training:
        from orchestrator.agents.training_generator import generate_training_chapter

        def _next_chapter_number() -> int:
            """Scan training/ for existing chapter dirs, return next number."""
            training_dir = PROJECT_ROOT / "training"
            if not training_dir.exists():
                return 1
            nums = []
            import re as _re
            for d in training_dir.iterdir():
                m = _re.match(r"chapter_(\d+)", d.name)
                if m:
                    nums.append(int(m.group(1)))
            return max(nums) + 1 if nums else 1

        chapter_num = args.chapter if args.chapter else _next_chapter_number()
        result = generate_training_chapter(
            chapter_number=chapter_num,
            skill_level=args.level,
            domain=domain,
            topic=args.topic,
            study_id=study_id,
            output_dir=str(PROJECT_ROOT / "training"),
            function_loader=function_loader,
            ig_client=ig_client,
            spec_manager=spec_manager,
        )
        print(json.dumps(result, indent=2))
        return

    def _save_state() -> None:
        """Persist state after each stage for resume capability."""
        state.save(str(state_file))

    # --------------------------------------------------------------------------
    def run_stage_spec_build() -> None:
        state.set_phase("spec_building")
        spec = build_draft_spec(study_id, domain, str(raw_data), function_loader, ig_client)
        spec_manager.write_spec(domain, spec, approved=False)
        spec_manager.write_spec_xlsx(domain, spec)
        state.set_spec_status("draft")
        state.set_artifact("draft_spec", str(spec_manager.spec_path(domain)))
        _save_state()
        print("Draft spec written to", spec_manager.spec_path(domain))

    # --------------------------------------------------------------------------
    def run_stage_spec_review() -> bool:
        """Returns True if review passed, False otherwise."""
        state.set_phase("spec_review")
        spec = spec_manager.read_spec(domain, approved=False)
        if not spec:
            print("No draft spec found. Run --stage spec_build first.")
            return False
        # Pass IG client and CRF path for IG-driven and CRF coverage checks
        crf_path = str(annotated_crf) if annotated_crf.exists() else None
        spec = review_spec(spec, ig_client=ig_client, crf_path=crf_path)
        spec_manager.write_spec(domain, spec, approved=False)
        passed = spec.get("review_pass", False)
        state.set_spec_status("reviewed" if passed else "draft")
        _save_state()
        print("Review pass:", passed, "Comments:", spec.get("review_comments", []))
        return passed

    # --------------------------------------------------------------------------
    def run_stage_human_review() -> None:
        state.set_phase("human_review")
        spec = spec_manager.read_spec(domain, approved=False)
        if not spec:
            print("No spec found. Run spec_build and spec_review first.")
            return

        # Build memory context for reviewer (past decisions, cross-domain)
        memory_ctx = memory.build_agent_context(domain, "human_review", study_id) if memory else None
        spec = present_spec_for_review(spec, conventions=conventions, memory_context=memory_ctx)

        # Write decisions to memory for future reference
        write_decisions_to_memory(spec, memory)

        # Populate state.human_decisions (was previously dead code)
        state.human_decisions = spec.get("human_decisions", {})

        spec_manager.write_spec(domain, spec, approved=True)
        state.set_spec_status("approved")
        state.set_artifact("approved_spec", str(spec_manager.spec_path(domain, approved=True)))
        _save_state()
        print("Approved spec written to", spec_manager.spec_path(domain, approved=True))

    # --------------------------------------------------------------------------
    def run_stage_production() -> bool:
        """Returns True if R script succeeded."""
        state.set_phase("production")
        spec = spec_manager.read_spec(domain, approved=True) or spec_manager.read_spec(domain, approved=False)
        if not spec:
            print("No spec found. Run spec_build and human_review first.")
            return False

        d = domain.lower()
        out_path: Path = op.production_datasets / f"{d}{ext}"
        xpt_path: Optional[str] = str(xpt_dir / f"{d}.xpt") if write_xpt else None
        program_name = f"{d}_production.R"

        # Build memory context (header, coding standards, pitfalls)
        memory_ctx = memory.build_agent_context(
            domain, "production", study_id, program_name
        ) if memory else None

        script = generate_r_script(
            spec=spec,
            raw_data_path=str(raw_data),
            output_dataset_path=str(out_path),
            function_library_path=str(function_library),
            ct_lookup_path=str(ct_lookup),
            output_format=output_format,
            write_xpt=write_xpt,
            xpt_path=xpt_path,
            memory_context=memory_ctx,
        )
        script_path = op.production_programs / program_name
        script_path.write_text(script, encoding="utf-8")
        state.set_artifact("production_script", str(script_path))
        state.set_artifact("production_dataset", str(out_path))
        if xpt_path:
            state.set_artifact("production_xpt", xpt_path)

        # Track modification history
        if memory:
            memory.update_modification_history(
                program_name, "Production Programmer Agent", "Generated from approved spec"
            )

        result = subprocess.run(
            [rscript_path, "--vanilla", str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("Production R script FAILED.")
            print("R stderr:", result.stderr[:2000])
            state.record_error(result.stderr or "Production R script failed")
            state.production_status = "failed"
            # Record pitfall in memory
            if memory:
                memory.record_pitfall(PitfallRecord(
                    category="r_script_error",
                    domain=domain,
                    description=f"Production R script failed: {(result.stderr or '')[:200]}",
                    root_cause="",
                    severity="blocker",
                    study_id=study_id,
                ))
            _save_state()
            return False

        print("Production script wrote", out_path)
        if xpt_path:
            print("XPT written to", xpt_path)
        state.production_status = "completed"
        _save_state()
        return True

    # --------------------------------------------------------------------------
    def run_stage_qc() -> bool:
        """Returns True if QC R script succeeded."""
        state.set_phase("qc")
        spec = spec_manager.read_spec(domain, approved=True) or spec_manager.read_spec(domain, approved=False)
        if not spec:
            print("No spec found.")
            return False

        d = domain.lower()
        qc_out_path: Path = op.qc_datasets / f"{d}_qc{ext}"
        qc_xpt_path: Optional[str] = None
        program_name = f"{d}_qc.R"

        # Build memory context (header, coding standards, pitfalls)
        memory_ctx = memory.build_agent_context(
            domain, "qc", study_id, program_name
        ) if memory else None

        script = generate_qc_r_script(
            spec=spec,
            raw_data_path=str(raw_data),
            output_dataset_path=str(qc_out_path),
            function_library_path=str(function_library),
            ct_lookup_path=str(ct_lookup),
            output_format=output_format,
            write_xpt=False,
            xpt_path=qc_xpt_path,
            memory_context=memory_ctx,
        )
        script_path = op.qc_programs / program_name
        script_path.write_text(script, encoding="utf-8")
        state.set_artifact("qc_script", str(script_path))
        state.set_artifact("qc_dataset", str(qc_out_path))

        # Track modification history
        if memory:
            memory.update_modification_history(
                program_name, "QC Programmer Agent", "Generated from approved spec"
            )

        result = subprocess.run(
            [rscript_path, "--vanilla", str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("QC R script FAILED.")
            print("R stderr:", result.stderr[:2000])
            state.record_error(result.stderr or "QC R script failed")
            state.qc_status = "failed"
            # Record pitfall in memory
            if memory:
                memory.record_pitfall(PitfallRecord(
                    category="r_script_error",
                    domain=domain,
                    description=f"QC R script failed: {(result.stderr or '')[:200]}",
                    root_cause="",
                    severity="blocker",
                    study_id=study_id,
                ))
            _save_state()
            return False

        print("QC script wrote", qc_out_path)
        state.qc_status = "completed"
        _save_state()
        return True

    # --------------------------------------------------------------------------
    def run_stage_compare() -> None:
        state.set_phase("comparison")
        d = domain.lower()
        prod_path = state.get_artifact("production_dataset") or str(op.production_datasets / f"{d}{ext}")
        qc_path   = state.get_artifact("qc_dataset")        or str(op.qc_datasets / f"{d}_qc{ext}")
        report_path = op.compare / f"{d}_compare_report.txt"
        try:
            match, report = compare_datasets(prod_path, qc_path, id_column="USUBJID")
            report_path.write_text(report, encoding="utf-8")
            state.comparison_result = "match" if match else "mismatch"
            print(report)
            # Record mismatch as pitfall
            if not match and memory:
                memory.record_pitfall(PitfallRecord(
                    category="comparison_mismatch",
                    domain=domain,
                    description=f"Production vs QC mismatch (iteration {state.comparison_iteration}): {report[:200]}",
                    root_cause="",
                    severity="warning",
                    study_id=study_id,
                ))
        except Exception as e:
            state.comparison_result = "mismatch"
            report_path.write_text(f"Comparison error: {e}\n", encoding="utf-8")
            print("Compare error:", e)
        _save_state()

    # --------------------------------------------------------------------------
    def run_stage_validate() -> None:
        state.set_phase("validation")
        spec = spec_manager.read_spec(domain, approved=True) or spec_manager.read_spec(domain, approved=False)
        if not spec:
            print("No spec found.")
            return
        d = domain.lower()
        dataset_path = state.get_artifact("production_dataset") or str(op.production_datasets / f"{d}{ext}")

        # Run validation with IG client for comprehensive checks
        report = validate_dataset(dataset_path, spec, ig_client=ig_client)
        report_path = op.validation / "p21_report.txt"
        lines = [f"Validation pass: {report['pass']}", ""]
        if report.get("issues"):
            lines.append("Issues:")
            for issue in report["issues"]:
                lines.append(f"  - {issue}")
        else:
            lines.append("No issues found.")
        lines.append("")
        lines.append("Checks:")
        for check, result in report.get("checks", {}).items():
            lines.append(f"  {check}: {'PASS' if result else 'FAIL'}")
        report_path.write_text("\n".join(lines), encoding="utf-8")

        # Write structured JSON report for HTML report generator
        json_report_path = op.validation / "p21_report.json"
        json_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Generate define.xml metadata
        define_meta = generate_define_metadata(spec)
        (op.validation / "define_metadata.json").write_text(
            json.dumps(define_meta, indent=2),
            encoding="utf-8",
        )

        # Generate P21 spec sheet (xlsx)
        p21_path = op.validation / "p21_spec_sheet.xlsx"
        generate_p21_spec_sheet(spec, str(p21_path))

        print("Validation pass:", report["pass"])
        if report.get("issues"):
            for issue in report["issues"]:
                print(f"  - {issue}")
        state.validation_status = "passed" if report["pass"] else "failed"
        _save_state()

    # --------------------------------------------------------------------------
    if args.stage:
        stages = {
            "spec_build":   run_stage_spec_build,
            "spec_review":  run_stage_spec_review,
            "human_review": run_stage_human_review,
            "production":   run_stage_production,
            "qc":           run_stage_qc,
            "compare":      run_stage_compare,
            "validate":     run_stage_validate,
        }
        if args.stage not in stages:
            print("Unknown stage. Use one of:", list(stages.keys()))
            sys.exit(1)
        stages[args.stage]()
        return

    # Standalone report generation
    if args.report:
        from orchestrator.core.report_generator import generate_report
        report_file = generate_report(
            output_dir=str(op.state),
            state=state,
            domain=domain,
            study_id=study_id,
            report_path=str(op.reports / f"{domain.lower()}_pipeline_report.html"),
        )
        print(f"Report generated: {report_file}")
        return

    # ========== Full pipeline with error gates and comparison loop ==========

    # 1. Spec building
    run_stage_spec_build()

    # 2. Spec review (with error gate)
    review_passed = run_stage_spec_review()
    if not review_passed and not args.force:
        print("\nSpec review FAILED. Fix issues and re-run, or use --force to continue.")
        _save_state()
        sys.exit(1)

    # 3. Human review
    run_stage_human_review()

    # 4. Production programming (with error gate)
    if not run_stage_production():
        print("\nABORT: Production R script failed. Cannot continue to QC.")
        _save_state()
        sys.exit(1)

    # 5. QC programming (with error gate)
    if not run_stage_qc():
        print("\nABORT: QC R script failed. Cannot continue to comparison.")
        _save_state()
        sys.exit(1)

    # 6. Comparison with mismatch loop
    run_stage_compare()
    iteration = 0
    while state.comparison_result == "mismatch" and iteration < max_iterations:
        iteration += 1
        state.comparison_iteration = iteration
        print(f"\nComparison iteration {iteration}/{max_iterations}: mismatch detected, re-running...")
        # Re-run both programmers and compare
        if not run_stage_production():
            print("ABORT: Production R script failed during re-run.")
            break
        if not run_stage_qc():
            print("ABORT: QC R script failed during re-run.")
            break
        run_stage_compare()

    if state.comparison_result == "mismatch":
        print(f"\nWARNING: Still mismatched after {iteration} iteration(s)")

    # 7. Validation
    run_stage_validate()

    # Save domain context for cross-domain memory
    if memory:
        spec = spec_manager.read_spec(domain, approved=True) or spec_manager.read_spec(domain, approved=False)
        decisions = spec.get("human_decisions", {}) if spec else {}
        memory.save_domain_context(DomainContext(
            domain=domain,
            key_decisions={k: v.get("choice", "") for k, v in decisions.items()},
            derived_variables=[
                v.get("target_variable", "")
                for v in (spec or {}).get("variables", [])
                if v.get("source_dataset") == "derived"
            ],
            study_id=study_id,
        ))

    print(f"\nPipeline complete.")
    print(f"  Phase: {state.current_phase}")
    print(f"  Comparison: {state.comparison_result} (iterations: {state.comparison_iteration})")
    print(f"  Validation: {state.validation_status}")
    _save_state()

    # Auto-generate HTML report at end of full pipeline
    try:
        from orchestrator.core.report_generator import generate_report
        report_file = generate_report(
            output_dir=str(op.state),
            state=state,
            domain=domain,
            study_id=study_id,
            report_path=str(op.reports / f"{domain.lower()}_pipeline_report.html"),
        )
        print(f"  Report: {report_file}")
    except Exception as e:
        print(f"  Report generation skipped: {e}")


if __name__ == "__main__":
    main()
