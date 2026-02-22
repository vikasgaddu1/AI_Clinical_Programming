"""
SDTM Tools MCP Server — provides SDTM-specific tools to Claude Code.

Exposes eight tools via the Model Context Protocol:
1. sdtm_variable_lookup    — Look up SDTM IG variable definitions for any domain
2. ct_lookup               — Look up controlled terminology mappings (+ check_values)
3. profile_raw_data        — Profile a raw clinical dataset (+ annotate)
4. query_function_registry — Query the R function registry
5. read_spec               — Read the current mapping specification (+ view modes)
6. get_pipeline_status     — Show pipeline stage progress and artifact inventory
7. get_comparison_summary  — Summarize production vs QC comparison results
8. get_validation_summary  — Summarize P21 validation results and fix suggestions

Run this server with:
  python mcp_server.py

Configure in .claude/mcp.json to auto-start with Claude Code.

Requirements: mcp (pip install mcp)
"""

import csv
import json
import re
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent

# Paths
IG_CONTENT_DIR = PROJECT_ROOT / "sdtm_ig_db" / "sdtm_ig_content"
FUNCTION_REGISTRY = PROJECT_ROOT / "r_functions" / "function_registry.json"
CT_LOOKUP = PROJECT_ROOT / "macros" / "ct_lookup.csv"
SPECS_DIR = PROJECT_ROOT / "orchestrator" / "outputs" / "specs"
RAW_DATA_DEFAULT = PROJECT_ROOT / "study_data" / "raw_dm.csv"

# Codelist extensibility map (non-extensible codelists reject values not in the codelist)
NON_EXTENSIBLE_CODELISTS = {"C66731", "C74457", "C66790"}
EXTENSIBLE_CODELISTS = {"C71113"}

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _resolve_output_dir(domain: str, study: str = "") -> Path:
    """Resolve the output directory based on study mode."""
    if study:
        return PROJECT_ROOT / "studies" / study / "outputs"
    return PROJECT_ROOT / "orchestrator" / "outputs"


def _load_ct_lookup_rows() -> list:
    """Load all rows from ct_lookup.csv as list of dicts."""
    if not CT_LOOKUP.exists():
        return []
    rows = []
    with open(CT_LOOKUP, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _load_registry_functions() -> list:
    """Load functions list from function_registry.json."""
    if not FUNCTION_REGISTRY.exists():
        return []
    with open(FUNCTION_REGISTRY, encoding="utf-8") as f:
        registry = json.load(f)
    return registry.get("functions", [])


# ---------------------------------------------------------------------------
# Existing helpers (original 5 tools)
# ---------------------------------------------------------------------------

def _read_ig_variable(domain: str, variable: str) -> str:
    """Read IG variable definition from markdown content."""
    md_path = IG_CONTENT_DIR / f"{domain.lower()}_domain.md"
    if not md_path.exists():
        return f"No IG content found for domain '{domain}'"

    text = md_path.read_text(encoding="utf-8")

    # Find the section for this variable
    pattern = rf"### {variable}\s*-.*?(?=\n### [A-Z]|\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0).strip()

    return f"Variable '{variable}' not found in {domain} domain IG content"


def _read_ig_domain_summary(domain: str) -> str:
    """Read the domain summary table from IG markdown."""
    md_path = IG_CONTENT_DIR / f"{domain.lower()}_domain.md"
    if not md_path.exists():
        return f"No IG content found for domain '{domain}'"

    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"## Summary Table.*?(?=\n## |\Z)", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return "Summary table not found"


def _lookup_ct(codelist_code: str, check_values: list = None) -> str:
    """Look up controlled terminology mappings from ct_lookup.csv.

    When check_values is provided, additionally reports MAPPED/UNMAPPED status
    for each value and suggests actions for unmapped values.
    """
    if not CT_LOOKUP.exists():
        return f"CT lookup file not found: {CT_LOOKUP}"

    rows = []
    with open(CT_LOOKUP, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("CODELIST", "") == codelist_code:
                rows.append(row)

    if not rows:
        return f"Codelist '{codelist_code}' not found in ct_lookup.csv"

    lines = [f"Codelist {codelist_code} ({rows[0].get('CODELIST_NAME', '')}):", ""]
    lines.append("| RAW_VALUE | CT_VALUE | DESCRIPTION |")
    lines.append("|-----------|----------|-------------|")
    for row in rows:
        lines.append(
            f"| {row.get('RAW_VALUE', '')} | {row.get('CT_VALUE', '')} | {row.get('DESCRIPTION', '')} |"
        )

    # --- Enhanced: check_values ---
    if check_values:
        lines.append("")
        lines.append("## Value Check Results")
        lines.append("")
        lines.append("| Value | Status | CT_VALUE | Action |")
        lines.append("|-------|--------|----------|--------|")

        # Build raw-value -> ct-value lookup (case-insensitive)
        raw_to_ct = {}
        for row in rows:
            raw_val = row.get("RAW_VALUE", "").strip().upper()
            ct_val = row.get("CT_VALUE", "")
            raw_to_ct[raw_val] = ct_val

        is_extensible = codelist_code in EXTENSIBLE_CODELISTS
        is_non_extensible = codelist_code in NON_EXTENSIBLE_CODELISTS
        codelist_type = "extensible" if is_extensible else ("non-extensible" if is_non_extensible else "unknown")

        for val in check_values:
            val_upper = val.strip().upper()
            if val_upper in raw_to_ct:
                ct_mapped = raw_to_ct[val_upper]
                lines.append(f"| {val} | MAPPED | {ct_mapped} | -- |")
            else:
                if is_extensible:
                    action = "Add to ct_lookup.csv"
                elif is_non_extensible:
                    action = "Review data - value not in codelist"
                else:
                    action = "Check codelist extensibility"
                lines.append(f"| {val} | UNMAPPED | -- | {action} |")

        lines.append("")
        lines.append(f"Codelist type: **{codelist_type}**")

    return "\n".join(lines)


def _profile_data(csv_path: str, annotate: bool = True) -> str:
    """Profile a raw clinical dataset.

    When annotate is True, adds function suggestions, CT cross-references,
    date format detection, and mixed-case flags.
    """
    path = Path(csv_path) if csv_path else RAW_DATA_DEFAULT
    if not path.exists():
        return f"File not found: {path}"

    try:
        import pandas as pd
    except ImportError:
        return "pandas not installed — cannot profile data"

    df = pd.read_csv(path, nrows=1000)

    # --- Prepare annotation data if needed ---
    ct_rows = []
    registry_functions = []
    ct_raw_values_set = set()
    if annotate:
        ct_rows = _load_ct_lookup_rows()
        registry_functions = _load_registry_functions()
        for row in ct_rows:
            ct_raw_values_set.add(row.get("RAW_VALUE", "").strip().upper())

    # Build per-column annotations
    col_annotations = {}  # col -> list of annotation strings
    col_actions = {}  # col -> suggested action string
    flags_section = []

    if annotate:
        for col in df.columns:
            annotations = []
            actions = []
            col_upper = col.upper()
            col_values = df[col].dropna()
            distinct_count = int(df[col].nunique())
            sample_vals = [str(v) for v in col_values.head(20).tolist()]

            # --- Date detection ---
            date_keywords = ["DT", "DATE", "date"]
            is_date_candidate = any(kw in col for kw in date_keywords)

            if is_date_candidate or col_upper in ("BRTHDT", "RFSTDTC", "RFENDTC", "DMDTC", "BRTHDTC"):
                actions.append("iso_date()")
                # Detect date formats in sample values
                formats_found = set()
                ambiguous_count = 0
                for val in sample_vals:
                    val_str = str(val).strip()
                    if re.match(r"\d{2}-[A-Za-z]{3}-\d{4}", val_str):
                        formats_found.add("DD-MON-YYYY")
                    elif re.match(r"\d{4}-\d{2}-\d{2}", val_str):
                        formats_found.add("ISO (YYYY-MM-DD)")
                    elif re.match(r"\d{1,2}/\d{1,2}/\d{4}", val_str):
                        parts = val_str.split("/")
                        p1, p2 = int(parts[0]), int(parts[1])
                        if p1 <= 12 and p2 <= 12:
                            formats_found.add("MM/DD/YYYY (ambiguous)")
                            ambiguous_count += 1
                        elif p1 > 12:
                            formats_found.add("DD/MM/YYYY")
                        else:
                            formats_found.add("MM/DD/YYYY")
                if formats_found:
                    fmt_str = ", ".join(sorted(formats_found))
                    annotations.append(f"Date formats detected: {fmt_str}")
                if ambiguous_count > 0:
                    flag_msg = f"Column `{col}`: {ambiguous_count} ambiguous slash date(s) where both parts <= 12. Defaults to MM/DD/YYYY; use `infmt='DD/MM/YYYY'` for non-US data."
                    flags_section.append(flag_msg)

            # --- CT / categorical detection ---
            known_ct_vars = {"SEX", "RACE", "ETHNIC", "COUNTRY", "ETHNICITY"}
            if col_upper in known_ct_vars:
                actions.append("assign_ct()")
                # Cross-reference values against ct_lookup
                matched = 0
                unmatched_vals = []
                for val in col_values.unique():
                    val_upper = str(val).strip().upper()
                    if val_upper in ct_raw_values_set:
                        matched += 1
                    else:
                        unmatched_vals.append(str(val))
                total = int(col_values.nunique())
                annotations.append(f"CT match: {matched}/{total} distinct values found in ct_lookup.csv")
                if unmatched_vals:
                    unmatch_display = ", ".join(unmatched_vals[:5])
                    annotations.append(f"Unmapped values: {unmatch_display}")
            elif distinct_count < 20 and df[col].dtype == object:
                # Check if looks like categorical data
                ct_match_count = 0
                for val in col_values.unique():
                    val_upper = str(val).strip().upper()
                    if val_upper in ct_raw_values_set:
                        ct_match_count += 1
                if ct_match_count > 0:
                    actions.append("assign_ct() candidate")
                    annotations.append(f"{ct_match_count} value(s) found in ct_lookup.csv")

            # --- Age detection ---
            age_keywords = ["AGE", "AGEU", "age"]
            if any(kw in col for kw in age_keywords):
                actions.append("derive_age()")

            # --- Mixed case detection ---
            if df[col].dtype == object:
                lower_to_original = {}
                mixed_examples = []
                for val in col_values.unique():
                    val_str = str(val).strip()
                    val_lower = val_str.lower()
                    if val_lower in lower_to_original:
                        existing = lower_to_original[val_lower]
                        if existing != val_str and len(mixed_examples) < 3:
                            mixed_examples.append(f"'{existing}' vs '{val_str}'")
                    else:
                        lower_to_original[val_lower] = val_str
                if mixed_examples:
                    flag_msg = f"Column `{col}`: Mixed case detected: {'; '.join(mixed_examples)}"
                    flags_section.append(flag_msg)

            col_annotations[col] = annotations
            col_actions[col] = " / ".join(actions) if actions else "--"

    # --- Build output ---
    lines = [f"Data Profile: {path.name}", f"Rows: {len(df)}, Columns: {len(df.columns)}", ""]

    if annotate:
        lines.append("| Column | Type | Non-Null | Distinct | Sample Values | Action |")
        lines.append("|--------|------|----------|----------|---------------|--------|")
    else:
        lines.append("| Column | Type | Non-Null | Distinct | Sample Values |")
        lines.append("|--------|------|----------|----------|---------------|")

    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = int(df[col].notna().sum())
        distinct = int(df[col].nunique())
        samples = df[col].dropna().head(3).tolist()
        sample_str = ", ".join(str(s) for s in samples)[:50]
        if annotate:
            action = col_actions.get(col, "--")
            lines.append(f"| {col} | {dtype} | {non_null} | {distinct} | {sample_str} | {action} |")
        else:
            lines.append(f"| {col} | {dtype} | {non_null} | {distinct} | {sample_str} |")

    # --- Annotation details ---
    if annotate:
        # Per-column annotations
        has_annotations = any(v for v in col_annotations.values())
        if has_annotations:
            lines.append("")
            lines.append("## Column Annotations")
            for col, anns in col_annotations.items():
                if anns:
                    lines.append(f"- **{col}**: {'; '.join(anns)}")

        # Flags section
        if flags_section:
            lines.append("")
            lines.append("## Flags")
            for flag in flags_section:
                lines.append(f"- {flag}")

    return "\n".join(lines)


def _query_registry(function_name: str) -> str:
    """Query the R function registry."""
    if not FUNCTION_REGISTRY.exists():
        return f"Registry not found: {FUNCTION_REGISTRY}"

    with open(FUNCTION_REGISTRY, encoding="utf-8") as f:
        registry = json.load(f)

    functions = registry.get("functions", [])

    if not function_name:
        # Return all functions summary
        lines = ["R Function Registry:", ""]
        for fn in functions:
            lines.append(f"- **{fn['name']}** ({fn.get('file', '')}): {fn.get('purpose', '')}")
        return "\n".join(lines)

    for fn in functions:
        if fn.get("name") == function_name:
            return json.dumps(fn, indent=2)

    return f"Function '{function_name}' not found in registry"


def _read_spec(domain: str, approved: bool, view: str = "full") -> str:
    """Read the mapping specification.

    Views:
      full      - return raw JSON (default, original behavior)
      summary   - compact markdown table of all variables
      decisions - only variables with human_decision_required=true
      ct_variables - only variables with a codelist_code
    """
    d = domain.lower()
    name = f"{d}_mapping_spec_approved.json" if approved else f"{d}_mapping_spec.json"
    path = SPECS_DIR / name
    if not path.exists():
        return f"Spec not found: {path}"

    raw_text = path.read_text(encoding="utf-8")

    if view == "full":
        return raw_text

    # Parse the spec JSON
    try:
        spec = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return f"Error parsing spec JSON: {e}"

    variables = spec.get("variables", [])
    study_id = spec.get("study_id", "")
    domain_name = spec.get("domain", domain.upper())

    if view == "summary":
        lines = [
            f"# Spec Summary: {domain_name} (Study: {study_id})",
            f"Spec version: {spec.get('spec_version', 'N/A')}",
            "",
            "| Variable | Source | Type | Function | Codelist | Decision? |",
            "|----------|--------|------|----------|----------|-----------|",
        ]
        for var in variables:
            target = var.get("target_variable", "")
            source = var.get("source_variable", "")
            dtype = var.get("data_type", "")
            func = var.get("macro_used", "") or "--"
            codelist = var.get("codelist_code", "") or "--"
            decision = "YES" if var.get("human_decision_required", False) else "--"
            lines.append(f"| {target} | {source} | {dtype} | {func} | {codelist} | {decision} |")
        lines.append("")
        lines.append(f"Total variables: {len(variables)}")
        decision_count = sum(1 for v in variables if v.get("human_decision_required", False))
        ct_count = sum(1 for v in variables if v.get("codelist_code"))
        lines.append(f"Requiring human decision: {decision_count}")
        lines.append(f"CT-controlled: {ct_count}")
        return "\n".join(lines)

    elif view == "decisions":
        decision_vars = [v for v in variables if v.get("human_decision_required", False)]
        if not decision_vars:
            return f"No variables in {domain_name} spec require human decisions."

        lines = [
            f"# Human Decisions Required: {domain_name} (Study: {study_id})",
            "",
        ]
        for var in decision_vars:
            target = var.get("target_variable", "")
            lines.append(f"## {target}")
            lines.append(f"- **Source:** {var.get('source_variable', 'N/A')}")
            lines.append(f"- **Mapping logic:** {var.get('mapping_logic', 'N/A')}")

            options = var.get("decision_options", [])
            if options:
                lines.append("- **Options:**")
                for opt in options:
                    opt_id = opt.get("id", "?")
                    desc = opt.get("description", "")
                    ig_ref = opt.get("ig_reference", "")
                    pros = ", ".join(opt.get("pros", []))
                    cons = ", ".join(opt.get("cons", []))
                    lines.append(f"  - **{opt_id}**: {desc}")
                    if ig_ref:
                        lines.append(f"    - IG Reference: {ig_ref}")
                    if pros:
                        lines.append(f"    - Pros: {pros}")
                    if cons:
                        lines.append(f"    - Cons: {cons}")

            chosen = var.get("chosen_option", "")
            if chosen:
                lines.append(f"- **Chosen:** {chosen}")
            lines.append("")

        return "\n".join(lines)

    elif view == "ct_variables":
        ct_vars = [v for v in variables if v.get("codelist_code")]
        if not ct_vars:
            return f"No CT-controlled variables found in {domain_name} spec."

        # Load CT lookup to show permitted values
        ct_rows = _load_ct_lookup_rows()
        codelist_values = {}  # codelist_code -> set of CT_VALUEs
        for row in ct_rows:
            cl = row.get("CODELIST", "")
            ct_val = row.get("CT_VALUE", "")
            if cl not in codelist_values:
                codelist_values[cl] = set()
            codelist_values[cl].add(ct_val)

        lines = [
            f"# CT-Controlled Variables: {domain_name} (Study: {study_id})",
            "",
            "| Variable | Codelist Code | Codelist Name | Permitted Values |",
            "|----------|---------------|---------------|------------------|",
        ]
        for var in ct_vars:
            target = var.get("target_variable", "")
            cl_code = var.get("codelist_code", "")
            cl_name = var.get("codelist_name", "")
            permitted = sorted(codelist_values.get(cl_code, set()))
            perm_str = ", ".join(permitted) if permitted else "(none in ct_lookup.csv)"
            lines.append(f"| {target} | {cl_code} | {cl_name} | {perm_str} |")
        return "\n".join(lines)

    return f"Unknown view '{view}'. Valid views: full, summary, decisions, ct_variables."


# ---------------------------------------------------------------------------
# New tool helpers (Part 1)
# ---------------------------------------------------------------------------

def _get_pipeline_status(domain: str = "DM", study: str = "") -> str:
    """Show pipeline stage progress and artifact inventory."""
    output_dir = _resolve_output_dir(domain, study)
    d = domain.lower()

    # --- Load pipeline state ---
    state_path = output_dir / "pipeline_state.json"
    # Also check if study mode stores state at a different location (studies/{study}/sdtm/)
    if study and not state_path.exists():
        alt_state_path = PROJECT_ROOT / "studies" / study / "sdtm" / "pipeline_state.json"
        if alt_state_path.exists():
            state_path = alt_state_path

    state = None
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            state = None

    # --- Define expected artifacts ---
    artifact_checks = [
        ("Draft Spec", output_dir / "specs" / f"{d}_mapping_spec.json"),
        ("Approved Spec", output_dir / "specs" / f"{d}_mapping_spec_approved.json"),
        ("Production Script", output_dir / "programs" / f"{d}_production.R"),
        ("Production Dataset", output_dir / "datasets" / f"{d}.parquet"),
        ("QC Script", output_dir / "qc" / f"{d}_qc.R"),
        ("QC Dataset", output_dir / "qc" / f"{d}_qc.parquet"),
        ("Compare Report", output_dir / "qc" / f"{d}_compare_report.txt"),
        ("P21 Report", output_dir / "validation" / "p21_report.txt"),
        ("Define Metadata", output_dir / "validation" / "define_metadata.json"),
        ("P21 Spec Sheet", output_dir / "validation" / "p21_spec_sheet.xlsx"),
        ("XPT File", output_dir / "validation" / f"{d}.xpt"),
    ]

    # Also check study-mode alternate paths
    if study:
        alt_base = PROJECT_ROOT / "studies" / study / "sdtm"
        alt_artifact_checks = [
            ("Draft Spec", alt_base / "specs" / f"{d}_mapping_spec.json"),
            ("Approved Spec", alt_base / "specs" / f"{d}_mapping_spec_approved.json"),
            ("Production Script", alt_base / "programs" / f"{d}_production.R"),
            ("Production Dataset", alt_base / "datasets" / f"{d}.parquet"),
            ("QC Script", alt_base / "qc" / f"{d}_qc.R"),
            ("QC Dataset", alt_base / "qc" / f"{d}_qc.parquet"),
            ("Compare Report", alt_base / "qc" / f"{d}_compare_report.txt"),
            ("P21 Report", alt_base / "validation" / "p21_report.txt"),
            ("Define Metadata", alt_base / "validation" / "define_metadata.json"),
            ("P21 Spec Sheet", alt_base / "validation" / "p21_spec_sheet.xlsx"),
            ("XPT File", alt_base / "validation" / f"{d}.xpt"),
        ]
        # Merge: prefer primary path if exists, else check alt
        merged = []
        for (name, primary), (_, alt) in zip(artifact_checks, alt_artifact_checks):
            if primary.exists():
                merged.append((name, primary))
            else:
                merged.append((name, alt))
        artifact_checks = merged

    # --- Build output ---
    lines = []
    study_label = study if study else "(legacy single-study mode)"
    lines.append(f"# Pipeline Status: {domain.upper()} — {study_label}")
    lines.append("")

    # Stage checklist
    phases = [
        ("spec_building", "Spec Building", "spec_status"),
        ("spec_review", "Spec Review", "spec_status"),
        ("human_review", "Human Review", "spec_status"),
        ("production", "Production Programming", "production_status"),
        ("qc", "QC Programming", "qc_status"),
        ("comparison", "Comparison", "comparison_result"),
        ("validation", "Validation", "validation_status"),
    ]

    lines.append("## Stage Checklist")
    lines.append("")

    if state:
        current_phase = state.get("current_phase", "unknown")
        for phase_key, phase_label, status_field in phases:
            status_val = state.get(status_field, "pending")
            # Determine display status
            if phase_key == "spec_building":
                if status_val in ("draft", "reviewed", "approved", "finalized"):
                    display = "DONE" if status_val != "draft" or current_phase != "spec_building" else "DONE (draft)"
                else:
                    display = "PENDING"
                # Check if spec file exists
                draft_exists = any(name == "Draft Spec" and p.exists() for name, p in artifact_checks)
                if draft_exists and current_phase != "spec_building":
                    display = "DONE"
                elif not draft_exists:
                    display = "PENDING"
            elif phase_key == "spec_review":
                if status_val in ("reviewed", "approved", "finalized"):
                    display = "DONE"
                elif current_phase == "spec_review":
                    display = "IN PROGRESS"
                else:
                    display = "PENDING"
            elif phase_key == "human_review":
                if status_val in ("approved", "finalized"):
                    display = "DONE"
                elif current_phase == "human_review":
                    display = "IN PROGRESS"
                else:
                    display = "PENDING"
            elif phase_key == "comparison":
                if status_val == "match":
                    display = "DONE (MATCH)"
                elif status_val == "mismatch":
                    display = "FAILED (MISMATCH)"
                elif current_phase == "comparison":
                    display = "IN PROGRESS"
                else:
                    display = "PENDING"
            else:
                if status_val == "done" or status_val == "complete" or status_val == "passed":
                    display = "DONE"
                elif status_val == "failed" or status_val == "error":
                    display = "FAILED"
                elif current_phase == phase_key:
                    display = "IN PROGRESS"
                elif status_val == "pending":
                    display = "PENDING"
                else:
                    display = status_val.upper()

            icon = "[x]" if "DONE" in display else ("[ ]" if display == "PENDING" else "[~]")
            lines.append(f"- {icon} **{phase_label}**: {display}")

        lines.append("")
        lines.append(f"**Current phase:** {current_phase}")
        lines.append(f"**Comparison iteration:** {state.get('comparison_iteration', 0)}")
    else:
        lines.append("_No pipeline_state.json found. Pipeline may not have been started._")

    # Artifact inventory
    lines.append("")
    lines.append("## Artifact Inventory")
    lines.append("")
    lines.append("| Artifact | Path | Status |")
    lines.append("|----------|------|--------|")
    for name, artifact_path in artifact_checks:
        status = "EXISTS" if artifact_path.exists() else "MISSING"
        display_path = str(artifact_path)
        lines.append(f"| {name} | {display_path} | {status} |")

    # Error log
    if state:
        errors = state.get("error_log", [])
        if errors:
            lines.append("")
            lines.append("## Error Log")
            lines.append("")
            for i, err in enumerate(errors, 1):
                lines.append(f"{i}. {err}")

    return "\n".join(lines)


def _get_comparison_summary(domain: str = "DM", study: str = "") -> str:
    """Summarize production vs QC comparison results."""
    output_dir = _resolve_output_dir(domain, study)
    d = domain.lower()

    # Also check study-mode alternate paths
    alt_base = PROJECT_ROOT / "studies" / study / "sdtm" if study else None

    # Find compare report
    report_path = output_dir / "qc" / f"{d}_compare_report.txt"
    if not report_path.exists() and alt_base:
        report_path = alt_base / "qc" / f"{d}_compare_report.txt"
    if not report_path.exists():
        return f"Compare report not found at {report_path}. Run the comparison stage first."

    report_text = report_path.read_text(encoding="utf-8").strip()

    lines = [f"# Comparison Summary: {domain.upper()}", ""]

    # Determine match vs mismatch
    is_match = "MATCH" in report_text.upper() and "MISMATCH" not in report_text.upper()

    if is_match:
        lines.append("**Status: MATCH** -- Production and QC datasets are identical.")
        lines.append("")

        # Try to read parquet files for row/column counts
        prod_parquet = output_dir / "datasets" / f"{d}.parquet"
        qc_parquet = output_dir / "qc" / f"{d}_qc.parquet"
        if not prod_parquet.exists() and alt_base:
            prod_parquet = alt_base / "datasets" / f"{d}.parquet"
        if not qc_parquet.exists() and alt_base:
            qc_parquet = alt_base / "qc" / f"{d}_qc.parquet"

        try:
            import pandas as pd
            if prod_parquet.exists():
                prod_df = pd.read_parquet(prod_parquet)
                lines.append(f"- Production dataset: {len(prod_df)} rows, {len(prod_df.columns)} columns")
            if qc_parquet.exists():
                qc_df = pd.read_parquet(qc_parquet)
                lines.append(f"- QC dataset: {len(qc_df)} rows, {len(qc_df.columns)} columns")
        except ImportError:
            lines.append("_(pandas not available for dataset dimension reporting)_")
        except Exception as e:
            lines.append(f"_(Could not read parquet files: {e})_")

    else:
        lines.append("**Status: MISMATCH** -- Differences found between production and QC datasets.")
        lines.append("")
        lines.append("### Compare Report Content")
        lines.append("```")
        lines.append(report_text)
        lines.append("```")
        lines.append("")

        # Parse differing columns from report text
        # Common patterns: "Column X differs", "Differences in: X, Y, Z", etc.
        differing_cols = set()
        for match in re.finditer(r"(?:Column|Variable)\s+['\"]?(\w+)['\"]?\s+(?:differs|mismatch|different)", report_text, re.IGNORECASE):
            differing_cols.add(match.group(1))
        # Also try "Differences in:" pattern
        diff_in_match = re.search(r"Differences\s+in:\s*(.+)", report_text, re.IGNORECASE)
        if diff_in_match:
            for col in diff_in_match.group(1).split(","):
                differing_cols.add(col.strip())

        # Try to load datasets and spec for detailed analysis
        prod_parquet = output_dir / "datasets" / f"{d}.parquet"
        qc_parquet = output_dir / "qc" / f"{d}_qc.parquet"
        if not prod_parquet.exists() and alt_base:
            prod_parquet = alt_base / "datasets" / f"{d}.parquet"
        if not qc_parquet.exists() and alt_base:
            qc_parquet = alt_base / "qc" / f"{d}_qc.parquet"

        # Load spec for codelist info
        spec_data = None
        spec_path = output_dir / "specs" / f"{d}_mapping_spec_approved.json"
        if not spec_path.exists() and alt_base:
            spec_path = alt_base / "specs" / f"{d}_mapping_spec_approved.json"
        if not spec_path.exists():
            spec_path = output_dir / "specs" / f"{d}_mapping_spec.json"
            if not spec_path.exists() and alt_base:
                spec_path = alt_base / "specs" / f"{d}_mapping_spec.json"
        if spec_path.exists():
            try:
                with open(spec_path, encoding="utf-8") as f:
                    spec_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                spec_data = None

        # Build codelist map from spec
        col_codelist = {}
        if spec_data:
            for var in spec_data.get("variables", []):
                cl = var.get("codelist_code", "")
                if cl:
                    col_codelist[var.get("target_variable", "")] = cl

        try:
            import pandas as pd
            if prod_parquet.exists() and qc_parquet.exists():
                prod_df = pd.read_parquet(prod_parquet)
                qc_df = pd.read_parquet(qc_parquet)

                lines.append(f"- Production: {len(prod_df)} rows, {len(prod_df.columns)} columns")
                lines.append(f"- QC: {len(qc_df)} rows, {len(qc_df.columns)} columns")
                lines.append("")

                # If no differing cols parsed from report, find them by comparing
                if not differing_cols:
                    common_cols = set(prod_df.columns) & set(qc_df.columns)
                    for col in common_cols:
                        try:
                            if not prod_df[col].equals(qc_df[col]):
                                differing_cols.add(col)
                        except Exception:
                            pass

                if differing_cols:
                    lines.append("### Column Differences")
                    lines.append("")
                    lines.append("| Column | Cause | USUBJID | Production Value | QC Value |")
                    lines.append("|--------|-------|---------|------------------|----------|")

                    for col in sorted(differing_cols):
                        # Classify the mismatch
                        if col in col_codelist:
                            cause = f"CT mapping difference ({col_codelist[col]})"
                        elif col.upper().endswith("DTC") or col.upper().endswith("DT"):
                            cause = "Date format difference"
                        else:
                            cause = "Derivation difference"

                        # Show up to 3 sample rows with differences
                        if col in prod_df.columns and col in qc_df.columns:
                            usubjid_col = "USUBJID" if "USUBJID" in prod_df.columns else None
                            diff_mask = prod_df[col].astype(str) != qc_df[col].astype(str)
                            diff_indices = diff_mask[diff_mask].index[:3]
                            for idx in diff_indices:
                                usubjid_val = str(prod_df.loc[idx, usubjid_col]) if usubjid_col else str(idx)
                                prod_val = str(prod_df.loc[idx, col])
                                qc_val = str(qc_df.loc[idx, col])
                                lines.append(f"| {col} | {cause} | {usubjid_val} | {prod_val} | {qc_val} |")
                            if len(diff_indices) == 0:
                                lines.append(f"| {col} | {cause} | -- | -- | -- |")
                        else:
                            lines.append(f"| {col} | {cause} | -- | (column missing) | (column missing) |")
                else:
                    lines.append("_Could not identify specific differing columns from the report._")
        except ImportError:
            lines.append("_(pandas not available for detailed mismatch analysis)_")
        except Exception as e:
            lines.append(f"_(Error during mismatch analysis: {e})_")

    return "\n".join(lines)


def _get_validation_summary(domain: str = "DM", study: str = "") -> str:
    """Summarize P21 validation results and fix suggestions."""
    output_dir = _resolve_output_dir(domain, study)
    d = domain.lower()

    alt_base = PROJECT_ROOT / "studies" / study / "sdtm" if study else None

    # --- Read p21_report.txt ---
    report_path = output_dir / "validation" / "p21_report.txt"
    if not report_path.exists() and alt_base:
        report_path = alt_base / "validation" / "p21_report.txt"

    # --- Try reading p21_report.json for richer data ---
    json_report_path = output_dir / "validation" / "p21_report.json"
    if not json_report_path.exists() and alt_base:
        json_report_path = alt_base / "validation" / "p21_report.json"

    if not report_path.exists() and not json_report_path.exists():
        return f"Validation report not found. Run the validation stage first.\nLooked in: {report_path}"

    lines = [f"# Validation Summary: {domain.upper()}", ""]

    # Parse text report
    report_text = ""
    overall_pass = None
    issues_list = []
    checks = []

    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8").strip()

        # Parse "Validation pass: True/False"
        pass_match = re.search(r"Validation\s+pass:\s*(True|False)", report_text, re.IGNORECASE)
        if pass_match:
            overall_pass = pass_match.group(1).strip().lower() == "true"

        # Parse issues list: "Issues: [...]"
        issues_match = re.search(r"Issues:\s*\[([^\]]*)\]", report_text)
        if issues_match:
            issues_raw = issues_match.group(1).strip()
            if issues_raw:
                issues_list = [i.strip().strip("'\"") for i in issues_raw.split(",")]

        # Parse individual checks: look for lines with PASS/FAIL
        for line in report_text.split("\n"):
            check_match = re.match(r"[-*]\s*([\w_]+).*?(PASS|FAIL)", line, re.IGNORECASE)
            if check_match:
                checks.append((check_match.group(1), check_match.group(2).upper()))

    # Parse JSON report if available
    json_report = None
    if json_report_path.exists():
        try:
            with open(json_report_path, encoding="utf-8") as f:
                json_report = json.load(f)
        except (json.JSONDecodeError, IOError):
            json_report = None

    if json_report:
        if overall_pass is None:
            overall_pass = json_report.get("validation_pass", json_report.get("pass", None))
        if not issues_list:
            issues_list = json_report.get("issues", [])
        if not checks:
            for check in json_report.get("checks", []):
                check_name = check.get("name", check.get("check", "unknown"))
                check_result = check.get("result", check.get("status", "UNKNOWN"))
                checks.append((check_name, check_result.upper()))

    # --- Overall status ---
    if overall_pass is True:
        lines.append("**Overall: PASS**")
    elif overall_pass is False:
        lines.append("**Overall: FAIL**")
    else:
        lines.append("**Overall: UNKNOWN** (could not parse pass/fail status)")
    lines.append("")

    # --- Issues ---
    if issues_list:
        lines.append(f"**Issues found:** {len(issues_list)}")
        for issue in issues_list:
            lines.append(f"- {issue}")
        lines.append("")
    else:
        lines.append("**Issues found:** 0")
        lines.append("")

    # --- Check-by-check table ---
    if checks:
        lines.append("## Check Results")
        lines.append("")
        lines.append("| Check | Result |")
        lines.append("|-------|--------|")
        pass_count = 0
        fail_count = 0
        for check_name, check_result in checks:
            lines.append(f"| {check_name} | {check_result} |")
            if check_result == "PASS":
                pass_count += 1
            elif check_result == "FAIL":
                fail_count += 1
        lines.append("")
        lines.append(f"**Severity summary:** {pass_count} PASS, {fail_count} FAIL, {len(checks) - pass_count - fail_count} OTHER")
        lines.append("")

    # --- Raw report content ---
    if report_text:
        lines.append("## Raw Report")
        lines.append("```")
        lines.append(report_text)
        lines.append("```")
        lines.append("")

    # --- Artifact existence ---
    lines.append("## Validation Artifacts")
    lines.append("")
    artifacts = [
        ("XPT File", output_dir / "validation" / f"{d}.xpt"),
        ("Define Metadata", output_dir / "validation" / "define_metadata.json"),
        ("P21 Spec Sheet", output_dir / "validation" / "p21_spec_sheet.xlsx"),
        ("P21 Report (text)", report_path),
        ("P21 Report (JSON)", json_report_path),
    ]
    # Check alt paths for study mode
    if alt_base:
        alt_artifacts = [
            ("XPT File", alt_base / "validation" / f"{d}.xpt"),
            ("Define Metadata", alt_base / "validation" / "define_metadata.json"),
            ("P21 Spec Sheet", alt_base / "validation" / "p21_spec_sheet.xlsx"),
            ("P21 Report (text)", alt_base / "validation" / "p21_report.txt"),
            ("P21 Report (JSON)", alt_base / "validation" / "p21_report.json"),
        ]
        merged = []
        for (name, primary), (_, alt) in zip(artifacts, alt_artifacts):
            if primary.exists():
                merged.append((name, primary))
            else:
                merged.append((name, alt))
        artifacts = merged

    lines.append("| Artifact | Status |")
    lines.append("|----------|--------|")
    for name, apath in artifacts:
        status = "EXISTS" if apath.exists() else "MISSING"
        lines.append(f"| {name} | {status} |")
    lines.append("")

    # --- Fix suggestions for failures ---
    failed_checks = [c for c, r in checks if r == "FAIL"]
    if failed_checks or (overall_pass is False and not checks):
        lines.append("## Fix Suggestions")
        lines.append("")
        if not failed_checks and overall_pass is False:
            lines.append("- Review the raw report above for details on what failed.")
            lines.append("- Ensure all R functions ran successfully (check error_log in pipeline_state.json).")
        for check_name in failed_checks:
            cn_lower = check_name.lower()
            if cn_lower.startswith("ct_") or "ct" in cn_lower or "codelist" in cn_lower:
                lines.append(f"- **{check_name}**: Review `assign_ct()` codelist parameter and verify raw values are in ct_lookup.csv")
            elif cn_lower.startswith("iso_") or "date" in cn_lower or "dtc" in cn_lower:
                lines.append(f"- **{check_name}**: Check `iso_date()` format parameter; verify date column formats with `profile_raw_data`")
            elif "required" in cn_lower or "missing" in cn_lower:
                lines.append(f"- **{check_name}**: Ensure all required SDTM variables are populated; check spec for variables with source 'N/A'")
            elif "length" in cn_lower or "type" in cn_lower:
                lines.append(f"- **{check_name}**: Verify variable data types and lengths match the spec and IG definitions")
            elif "domain" in cn_lower:
                lines.append(f"- **{check_name}**: Check DOMAIN variable is set correctly (should be '{domain.upper()}')")
            elif "usubjid" in cn_lower:
                lines.append(f"- **{check_name}**: Verify USUBJID construction: STUDYID + '-' + SUBJID")
            else:
                lines.append(f"- **{check_name}**: Review the check logic and compare against SDTM IG requirements for {domain.upper()} domain")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server."""
    if not _MCP_AVAILABLE:
        print("MCP package not installed. Install with: pip install mcp", file=sys.stderr)
        print("Falling back to CLI mode for testing.", file=sys.stderr)
        print()

        # Simple CLI test mode
        print("=== SDTM Tools (CLI Test Mode) ===")
        print()
        print("1. IG Variable Lookup (DM, SEX):")
        print(_read_ig_variable("DM", "SEX")[:500])
        print()
        print("2. CT Lookup (C66731):")
        print(_lookup_ct("C66731"))
        print()
        print("3. CT Lookup with check_values (C66731, ['M', 'FEMALE', 'X']):")
        print(_lookup_ct("C66731", check_values=["M", "FEMALE", "X"]))
        print()
        print("4. Function Registry:")
        print(_query_registry(""))
        print()
        print("5. Pipeline Status (DM):")
        print(_get_pipeline_status("DM"))
        print()
        print("6. Comparison Summary (DM):")
        print(_get_comparison_summary("DM"))
        print()
        print("7. Validation Summary (DM):")
        print(_get_validation_summary("DM"))
        print()
        print("8. Read Spec - summary view (DM):")
        print(_read_spec("DM", False, view="summary"))
        print()
        print("9. Profile Raw Data (with annotations):")
        print(_profile_data("", annotate=True))
        return

    app = Server("sdtm-tools")

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="sdtm_variable_lookup",
                description="Look up SDTM IG variable definitions. Pass domain (e.g. 'DM') and optionally a variable name (e.g. 'SEX'). Without variable, returns domain summary table.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "SDTM domain (e.g. DM, AE, VS)"},
                        "variable": {"type": "string", "description": "Variable name (optional, e.g. SEX, RACE)"},
                    },
                    "required": ["domain"],
                },
            ),
            Tool(
                name="ct_lookup",
                description="Look up CDISC Controlled Terminology mappings. Returns all raw->CT value mappings for a codelist. Optionally check specific values against the codelist.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "codelist_code": {"type": "string", "description": "Codelist code (e.g. C66731 for SEX, C74457 for RACE)"},
                        "check_values": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of values to check against the codelist. Reports MAPPED/UNMAPPED status for each.",
                        },
                    },
                    "required": ["codelist_code"],
                },
            ),
            Tool(
                name="profile_raw_data",
                description="Profile a raw clinical dataset. Returns column types, distinct values, missing counts. With annotations: suggests R functions, detects date formats, flags mixed case, cross-references CT lookup.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "csv_path": {"type": "string", "description": "Path to CSV file (defaults to study_data/raw_dm.csv)"},
                        "annotate": {
                            "type": "boolean",
                            "description": "Add function suggestions, CT cross-references, date format detection, and mixed-case flags (default true)",
                        },
                    },
                },
            ),
            Tool(
                name="query_function_registry",
                description="Query the R function registry. Returns function details including parameters and usage examples.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "function_name": {"type": "string", "description": "Function name (e.g. 'iso_date'). Empty for all functions."},
                    },
                },
            ),
            Tool(
                name="read_spec",
                description="Read the SDTM mapping specification for a domain. Supports multiple view modes: full (raw JSON), summary (compact table), decisions (human decisions only), ct_variables (CT-controlled only).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "SDTM domain (e.g. DM)"},
                        "approved": {"type": "boolean", "description": "Read approved spec (true) or draft (false)"},
                        "view": {
                            "type": "string",
                            "enum": ["full", "summary", "decisions", "ct_variables"],
                            "description": "View mode: 'full' (raw JSON, default), 'summary' (compact table), 'decisions' (human decisions only), 'ct_variables' (CT-controlled variables only)",
                        },
                    },
                    "required": ["domain"],
                },
            ),
            Tool(
                name="get_pipeline_status",
                description="Show pipeline stage progress and artifact inventory for a domain. Shows stage checklist (DONE/PENDING/FAILED), artifact existence, and error log.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "SDTM domain (default: DM)"},
                        "study": {"type": "string", "description": "Study ID for multi-study mode (e.g. XYZ_2026_001). Omit for legacy single-study mode."},
                    },
                },
            ),
            Tool(
                name="get_comparison_summary",
                description="Summarize production vs QC comparison results. For matches: shows dataset dimensions. For mismatches: shows column-by-column diff with sample values and cause classification.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "SDTM domain (default: DM)"},
                        "study": {"type": "string", "description": "Study ID for multi-study mode (e.g. XYZ_2026_001). Omit for legacy single-study mode."},
                    },
                },
            ),
            Tool(
                name="get_validation_summary",
                description="Summarize P21 validation results. Shows overall pass/fail, check-by-check table, artifact status, and fix suggestions for failures.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "SDTM domain (default: DM)"},
                        "study": {"type": "string", "description": "Study ID for multi-study mode (e.g. XYZ_2026_001). Omit for legacy single-study mode."},
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "sdtm_variable_lookup":
            domain = arguments.get("domain", "DM")
            variable = arguments.get("variable", "")
            if variable:
                result = _read_ig_variable(domain, variable)
            else:
                result = _read_ig_domain_summary(domain)
            return [TextContent(type="text", text=result)]

        elif name == "ct_lookup":
            result = _lookup_ct(
                arguments.get("codelist_code", ""),
                check_values=arguments.get("check_values", None),
            )
            return [TextContent(type="text", text=result)]

        elif name == "profile_raw_data":
            result = _profile_data(
                arguments.get("csv_path", ""),
                annotate=arguments.get("annotate", True),
            )
            return [TextContent(type="text", text=result)]

        elif name == "query_function_registry":
            result = _query_registry(arguments.get("function_name", ""))
            return [TextContent(type="text", text=result)]

        elif name == "read_spec":
            result = _read_spec(
                arguments.get("domain", "DM"),
                arguments.get("approved", False),
                view=arguments.get("view", "full"),
            )
            return [TextContent(type="text", text=result)]

        elif name == "get_pipeline_status":
            result = _get_pipeline_status(
                domain=arguments.get("domain", "DM"),
                study=arguments.get("study", ""),
            )
            return [TextContent(type="text", text=result)]

        elif name == "get_comparison_summary":
            result = _get_comparison_summary(
                domain=arguments.get("domain", "DM"),
                study=arguments.get("study", ""),
            )
            return [TextContent(type="text", text=result)]

        elif name == "get_validation_summary":
            result = _get_validation_summary(
                domain=arguments.get("domain", "DM"),
                study=arguments.get("study", ""),
            )
            return [TextContent(type="text", text=result)]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    import asyncio
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()
