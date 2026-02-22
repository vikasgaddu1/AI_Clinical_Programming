"""
HTML Report Generator for the SDTM Pipeline.
Generates a self-contained HTML report with pipeline status, spec details,
comparison results, validation checks, and dataset previews.

Usage:
    from orchestrator.core.report_generator import generate_report
    report_path = generate_report("orchestrator/outputs", domain="DM")

Can also be used standalone (no orchestrator imports required).
"""

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data Loaders -- each returns None on missing/unreadable file
# ---------------------------------------------------------------------------

def _load_state(output_dir: Path) -> Optional[dict]:
    """Load pipeline state from JSON."""
    state_path = output_dir / "pipeline_state.json"
    if not state_path.exists():
        return None
    try:
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _load_spec(output_dir: Path, domain: str) -> Optional[dict]:
    """Load approved spec; fall back to draft if approved not found."""
    specs_dir = output_dir / "specs"
    for suffix in ("_approved", ""):
        path = specs_dir / f"{domain.lower()}_mapping_spec{suffix}.json"
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _load_compare_report(output_dir: Path, domain: str) -> Optional[str]:
    """Load the plain-text comparison report."""
    path = output_dir / "qc" / f"{domain.lower()}_compare_report.txt"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _load_validation(output_dir: Path) -> Optional[dict]:
    """Load validation results -- tries JSON first, then parses text."""
    json_path = output_dir / "validation" / "p21_report.json"
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    txt_path = output_dir / "validation" / "p21_report.txt"
    if not txt_path.exists():
        return None
    try:
        text = txt_path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Parse simple text format: "Validation pass: True\nIssues: [...]"
    result: Dict[str, Any] = {"pass": False, "checks": []}
    if re.search(r"pass:\s*True", text, re.IGNORECASE):
        result["pass"] = True
    issues_match = re.search(r"Issues:\s*\[(.*)?\]", text, re.DOTALL)
    if issues_match:
        raw = issues_match.group(1).strip()
        if raw:
            for item in re.split(r",\s*", raw):
                item = item.strip().strip("'\"")
                if item:
                    result["checks"].append({"name": item, "status": "FAIL", "details": item})
    if result["pass"] and not result["checks"]:
        result["checks"].append({"name": "Overall Validation", "status": "PASS", "details": "All checks passed"})
    return result


def _load_dataset(output_dir: Path, domain: str, which: str = "production") -> Any:
    """Load a dataset as a pandas DataFrame. Returns None if unavailable."""
    try:
        import pandas as pd
    except ImportError:
        return None
    if which == "production":
        candidates = [
            output_dir / "datasets" / f"{domain.lower()}.parquet",
            output_dir / "datasets" / f"{domain.lower()}.csv",
        ]
    else:
        candidates = [
            output_dir / "qc" / f"{domain.lower()}_qc.parquet",
            output_dir / "qc" / f"{domain.lower()}_qc.csv",
        ]
    for path in candidates:
        if path.exists():
            try:
                if path.suffix == ".parquet":
                    return pd.read_parquet(path)
                return pd.read_csv(path, dtype=str)
            except Exception:
                continue
    return None


def _load_p21_spec_sheet(output_dir: Path) -> Optional[dict]:
    """Load P21 spec sheet XLSX into dict with 'variables' and 'valuelevel' DataFrames."""
    try:
        import pandas as pd
    except ImportError:
        return None
    path = output_dir / "validation" / "p21_spec_sheet.xlsx"
    if not path.exists():
        return None
    try:
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    except Exception:
        return None
    result = {}
    for name, df in sheets.items():
        key = name.lower().replace(" ", "")
        if "variable" in key:
            result["variables"] = df
        elif "value" in key:
            result["valuelevel"] = df
        else:
            result[key] = df
    if not result:
        first_key = list(sheets.keys())[0]
        result["variables"] = sheets[first_key]
    return result


def _load_errors(state_dict: Optional[dict]) -> Optional[List[str]]:
    """Extract error log from state dict."""
    if state_dict is None:
        return None
    errors = state_dict.get("error_log", [])
    return errors if errors else None


# ---------------------------------------------------------------------------
# Determine overall status
# ---------------------------------------------------------------------------

def _overall_status(state_dict: Optional[dict], validation: Optional[dict],
                    compare_text: Optional[str]) -> str:
    """Return 'PASSED', 'PARTIAL', or 'FAILED'."""
    v_pass = validation is not None and validation.get("pass", False)
    c_match = compare_text is not None and "MATCH" in compare_text and "MISMATCH" not in compare_text
    if v_pass and c_match:
        return "PASSED"
    if state_dict and state_dict.get("error_log"):
        return "FAILED"
    if v_pass or c_match:
        return "PARTIAL"
    if validation is not None or compare_text is not None:
        return "FAILED"
    return "PARTIAL"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def _render_css() -> str:
    return """<style>
/* ---------- Reset & Base ---------- */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #2c3e50; background: #f5f7fa; line-height: 1.6; padding: 0;
}
a { color: #2980b9; text-decoration: none; }
code, .mono { font-family: "Cascadia Code", "Fira Code", "Consolas", monospace; font-size: 0.92em; }

/* ---------- Header Banner ---------- */
.report-header {
    background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
    color: #fff; padding: 32px 40px; display: flex; justify-content: space-between;
    align-items: center; flex-wrap: wrap; gap: 12px;
}
.report-header h1 { font-size: 1.6em; font-weight: 700; }
.report-header .meta { font-size: 0.9em; opacity: 0.85; }
.status-badge {
    display: inline-block; padding: 4px 16px; border-radius: 20px;
    font-weight: 700; font-size: 0.85em; letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-passed  { background: #27ae60; color: #fff; }
.badge-partial { background: #f39c12; color: #fff; }
.badge-failed  { background: #e74c3c; color: #fff; }

/* ---------- Content Container ---------- */
.container { max-width: 1200px; margin: 0 auto; padding: 24px 20px; }

/* ---------- Dashboard ---------- */
.dashboard { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
.stat-box {
    flex: 1 1 200px; background: #fff; border-radius: 8px; padding: 18px 20px;
    border-left: 5px solid #95a5a6; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.stat-box h3 { font-size: 0.8em; text-transform: uppercase; color: #7f8c8d; margin-bottom: 4px; }
.stat-box .value { font-size: 1.35em; font-weight: 700; }
.stat-box.success { border-left-color: #27ae60; }
.stat-box.failure { border-left-color: #e74c3c; }
.stat-box.warning { border-left-color: #f39c12; }
.stat-box.pending { border-left-color: #95a5a6; }

/* ---------- Timeline ---------- */
.timeline { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 28px; align-items: center; }
.stage-box {
    flex: 1 1 110px; text-align: center; padding: 12px 8px; border-radius: 6px;
    font-size: 0.82em; font-weight: 600; color: #fff; position: relative;
    min-width: 100px;
}
.stage-box.completed { background: #27ae60; }
.stage-box.active    { background: #2980b9; }
.stage-box.pending   { background: #bdc3c7; color: #636e72; }
.stage-box.failed    { background: #e74c3c; }
.stage-arrow { font-size: 1.2em; color: #95a5a6; flex: 0 0 auto; }

/* ---------- Sections ---------- */
.section {
    background: #fff; border-radius: 8px; margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); overflow: hidden;
}
.section summary, .section-title {
    padding: 14px 20px; font-size: 1.05em; font-weight: 600; cursor: pointer;
    background: #fafbfc; border-bottom: 1px solid #ecf0f1; user-select: none;
    list-style: none; display: flex; align-items: center; gap: 8px;
}
.section summary::-webkit-details-marker { display: none; }
.section summary::before { content: "\\25B6"; font-size: 0.7em; transition: transform 0.2s; }
.section[open] summary::before { transform: rotate(90deg); }
.section-body { padding: 20px; }

/* ---------- Tables ---------- */
table { width: 100%; border-collapse: collapse; font-size: 0.88em; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
th {
    background: #f5f7fa; font-weight: 600; color: #2c3e50; position: sticky; top: 0;
    cursor: pointer; white-space: nowrap;
}
th:hover { background: #e8ecf1; }
tr:nth-child(even) { background: #fafbfc; }
tr:hover { background: #eef2f7; }
.decision-highlight { background: #fef9e7 !important; }
.decision-highlight:hover { background: #fdf2d0 !important; }

/* ---------- Callouts ---------- */
.callout { padding: 14px 18px; border-radius: 6px; margin-bottom: 16px; border-left: 4px solid; }
.callout-success { background: #eafaf1; border-color: #27ae60; color: #1e8449; }
.callout-error   { background: #fdedec; border-color: #e74c3c; color: #c0392b; }
.callout-warning { background: #fef9e7; border-color: #f39c12; color: #d68910; }
.callout-info    { background: #eaf2f8; border-color: #2980b9; color: #1a5276; }

/* ---------- Filter Buttons ---------- */
.filter-bar { margin-bottom: 12px; display: flex; gap: 8px; }
.filter-btn {
    padding: 5px 14px; border-radius: 4px; border: 1px solid #bdc3c7;
    background: #fff; cursor: pointer; font-size: 0.82em; font-weight: 600;
}
.filter-btn:hover { background: #ecf0f1; }
.filter-btn.active { background: #2980b9; color: #fff; border-color: #2980b9; }

/* ---------- Badge inline ---------- */
.check-pass { color: #27ae60; font-weight: 700; }
.check-fail { color: #e74c3c; font-weight: 700; }

/* ---------- Iteration badge ---------- */
.iter-badge {
    display: inline-block; background: #f39c12; color: #fff; font-size: 0.7em;
    padding: 1px 6px; border-radius: 10px; margin-left: 4px; vertical-align: middle;
}

/* ---------- Placeholder ---------- */
.placeholder { color: #95a5a6; font-style: italic; padding: 16px 0; }

/* ---------- Error Log ---------- */
.error-section { border: 2px solid #e74c3c; }
.error-section summary { background: #fdedec; color: #c0392b; }

/* ---------- Scrollable table wrapper ---------- */
.table-wrap { overflow-x: auto; max-height: 500px; overflow-y: auto; }

/* ---------- Print ---------- */
@media print {
    body { background: #fff; font-size: 10pt; }
    .report-header { background: #1a5276 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    details { display: block !important; }
    details > summary { display: none; }
    details > .section-body { display: block !important; }
    .filter-bar { display: none; }
    .stage-box, .stat-box, .status-badge, .callout {
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    .section { box-shadow: none; border: 1px solid #ddd; break-inside: avoid; }
    .table-wrap { max-height: none; overflow: visible; }
}
</style>"""


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

def _render_js() -> str:
    return """<script>
/* Filter validation checks by status */
function filterChecks(status) {
    var rows = document.querySelectorAll('#validation-table tbody tr');
    for (var i = 0; i < rows.length; i++) {
        var cell = rows[i].querySelector('td:nth-child(2)');
        if (!cell) continue;
        var text = cell.textContent.trim().toUpperCase();
        if (status === 'ALL' || text === status) {
            rows[i].style.display = '';
        } else {
            rows[i].style.display = 'none';
        }
    }
    var btns = document.querySelectorAll('.filter-btn');
    for (var j = 0; j < btns.length; j++) {
        btns[j].classList.remove('active');
        if (btns[j].getAttribute('data-filter') === status) {
            btns[j].classList.add('active');
        }
    }
}

/* Sort table by column */
function sortTable(tableId, colIdx) {
    var table = document.getElementById(tableId);
    if (!table) return;
    var tbody = table.querySelector('tbody');
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    var dir = table.getAttribute('data-sort-dir-' + colIdx) === 'asc' ? 'desc' : 'asc';
    table.setAttribute('data-sort-dir-' + colIdx, dir);
    rows.sort(function(a, b) {
        var aText = a.cells[colIdx] ? a.cells[colIdx].textContent.trim() : '';
        var bText = b.cells[colIdx] ? b.cells[colIdx].textContent.trim() : '';
        var aNum = parseFloat(aText);
        var bNum = parseFloat(bText);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return dir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        return dir === 'asc' ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    for (var i = 0; i < rows.length; i++) {
        tbody.appendChild(rows[i]);
    }
    /* Update header arrows */
    var headers = table.querySelectorAll('th');
    for (var h = 0; h < headers.length; h++) {
        var txt = headers[h].textContent.replace(/ [\\u25B2\\u25BC]/g, '');
        if (h === colIdx) {
            txt += dir === 'asc' ? ' \\u25B2' : ' \\u25BC';
        }
        headers[h].textContent = txt;
    }
}

/* Expand all sections (for print preview) */
function expandAll() {
    var details = document.querySelectorAll('details');
    for (var i = 0; i < details.length; i++) {
        details[i].setAttribute('open', '');
    }
}

/* Collapse all sections */
function collapseAll() {
    var details = document.querySelectorAll('details');
    for (var i = 0; i < details.length; i++) {
        details[i].removeAttribute('open');
    }
}
</script>"""


# ---------------------------------------------------------------------------
# Section Renderers
# ---------------------------------------------------------------------------

def _render_header(study_id: str, domain: str, status: str) -> str:
    badge_class = {
        "PASSED": "badge-passed",
        "PARTIAL": "badge-partial",
        "FAILED": "badge-failed",
    }.get(status, "badge-partial")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<div class="report-header">
  <div>
    <h1>SDTM Pipeline Report &mdash; {html.escape(domain)}</h1>
    <div class="meta">Study: {html.escape(study_id)} &nbsp;|&nbsp; Generated: {timestamp}</div>
  </div>
  <div>
    <span class="status-badge {badge_class}">{html.escape(status)}</span>
  </div>
</div>"""


def _render_dashboard(state_dict: Optional[dict], spec: Optional[dict],
                      validation: Optional[dict], compare_text: Optional[str]) -> str:
    # Spec status
    spec_status = "N/A"
    spec_class = "pending"
    if state_dict:
        spec_status = state_dict.get("spec_status", "pending").upper()
        if spec_status in ("APPROVED", "FINALIZED"):
            spec_class = "success"
        elif spec_status == "REVIEWED":
            spec_class = "warning"
    elif spec:
        spec_status = "LOADED"
        spec_class = "warning"

    # Comparison
    cmp_value = "Pending"
    cmp_class = "pending"
    if compare_text:
        if "MISMATCH" in compare_text:
            cmp_value = "MISMATCH"
            cmp_class = "failure"
        elif "MATCH" in compare_text:
            cmp_value = "MATCH"
            cmp_class = "success"

    # Validation
    val_value = "Pending"
    val_class = "pending"
    if validation is not None:
        if validation.get("pass", False):
            val_value = "PASS"
            val_class = "success"
        else:
            val_value = "FAIL"
            val_class = "failure"
        n_issues = sum(1 for c in validation.get("checks", []) if c.get("status", "").upper() == "FAIL")
        if n_issues:
            val_value += f" ({n_issues} issue{'s' if n_issues != 1 else ''})"

    # Review comments
    comments_value = "0"
    comments_class = "pending"
    if spec:
        n_comments = len(spec.get("review_comments", []))
        comments_value = str(n_comments)
        if n_comments > 0:
            comments_class = "warning"

    return f"""<div class="dashboard">
  <div class="stat-box {spec_class}">
    <h3>Spec Status</h3>
    <div class="value">{html.escape(spec_status)}</div>
  </div>
  <div class="stat-box {cmp_class}">
    <h3>Comparison</h3>
    <div class="value">{html.escape(cmp_value)}</div>
  </div>
  <div class="stat-box {val_class}">
    <h3>Validation</h3>
    <div class="value">{html.escape(val_value)}</div>
  </div>
  <div class="stat-box {comments_class}">
    <h3>Review Comments</h3>
    <div class="value">{html.escape(comments_value)}</div>
  </div>
</div>"""


def _render_timeline(state_dict: Optional[dict]) -> str:
    stages = [
        ("Spec Build", "spec_building"),
        ("Spec Review", "spec_review"),
        ("Human Review", "human_review"),
        ("Production", "production"),
        ("QC", "qc"),
        ("Compare", "comparison"),
        ("Validate", "validation"),
    ]
    phase_order = [s[1] for s in stages]
    current_phase = ""
    comparison_iter = 0
    errors = []
    if state_dict:
        current_phase = state_dict.get("current_phase", "")
        comparison_iter = state_dict.get("comparison_iteration", 0)
        errors = state_dict.get("error_log", [])

    # Determine the current phase index
    current_idx = -1
    if current_phase in phase_order:
        current_idx = phase_order.index(current_phase)

    # Check for terminal statuses that indicate completion
    all_done = False
    if state_dict:
        v_status = state_dict.get("validation_status", "pending")
        if v_status not in ("pending",):
            all_done = True

    boxes_html = []
    for i, (label, phase_key) in enumerate(stages):
        css_class = "pending"
        if all_done:
            css_class = "completed"
            # Check if any error relates to this stage
        elif i < current_idx:
            css_class = "completed"
        elif i == current_idx:
            css_class = "active"
        extra = ""
        if phase_key == "comparison" and comparison_iter > 0:
            extra = f' <span class="iter-badge">iter {comparison_iter}</span>'
        box = f'<div class="stage-box {css_class}">{html.escape(label)}{extra}</div>'
        boxes_html.append(box)
        if i < len(stages) - 1:
            boxes_html.append('<div class="stage-arrow">&rarr;</div>')

    return f'<div class="timeline">{"".join(boxes_html)}</div>'


def _render_spec_section(spec: Optional[dict]) -> str:
    if spec is None:
        return _collapsible_section("Mapping Specification", '<p class="placeholder">Specification not yet generated.</p>', open_default=True)

    variables = spec.get("variables", [])
    review_comments = spec.get("review_comments", [])
    human_decisions = spec.get("human_decisions", {})

    # Review comments callout
    comments_html = ""
    if review_comments:
        items = "".join(f"<li>{html.escape(str(c))}</li>" for c in review_comments)
        comments_html = f'<div class="callout callout-warning"><strong>Review Comments:</strong><ul style="margin:6px 0 0 18px;">{items}</ul></div>'

    # Human decisions callout
    decisions_html = ""
    if human_decisions:
        dec_items = []
        for var_name, dec in human_decisions.items():
            choice = dec.get("choice", "N/A") if isinstance(dec, dict) else str(dec)
            dec_items.append(f"<li><strong>{html.escape(str(var_name))}</strong>: Choice {html.escape(str(choice))}</li>")
        decisions_html = f'<div class="callout callout-info"><strong>Human Decisions:</strong><ul style="margin:6px 0 0 18px;">{"".join(dec_items)}</ul></div>'

    # Variables table
    if not variables:
        table_html = '<p class="placeholder">No variables in specification.</p>'
    else:
        headers = ["Variable", "Source", "Type", "Length", "Mapping Logic", "Codelist", "Decision?"]
        header_cells = "".join(
            f'<th onclick="sortTable(\'spec-table\', {i})">{h}</th>' for i, h in enumerate(headers)
        )
        rows = []
        for v in variables:
            decision_flag = v.get("human_decision_required", False)
            row_class = ' class="decision-highlight"' if decision_flag else ""
            codelist = v.get("codelist_code", v.get("codelist", "")) or ""
            if codelist and v.get("codelist_name"):
                codelist = f"{codelist} ({v['codelist_name']})"
            cells = [
                html.escape(str(v.get("target_variable", ""))),
                html.escape(str(v.get("source_variable", ""))),
                html.escape(str(v.get("data_type", ""))),
                html.escape(str(v.get("length", ""))),
                f'<span class="mono">{html.escape(str(v.get("mapping_logic", "")))}</span>',
                html.escape(str(codelist)),
                "Yes" if decision_flag else "No",
            ]
            rows.append(f'<tr{row_class}>{"".join(f"<td>{c}</td>" for c in cells)}</tr>')
        table_html = f"""<div class="table-wrap">
<table id="spec-table"><thead><tr>{header_cells}</tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>"""

    body = f"{comments_html}{decisions_html}{table_html}"
    return _collapsible_section("Mapping Specification", body, open_default=True)


def _render_comparison_section(compare_text: Optional[str], state_dict: Optional[dict]) -> str:
    if compare_text is None:
        return _collapsible_section("Production vs QC Comparison",
                                    '<p class="placeholder">Comparison not yet run.</p>', open_default=True)

    if "MISMATCH" in compare_text:
        callout = '<div class="callout callout-error"><strong>MISMATCH</strong> &mdash; Production and QC datasets differ.</div>'
        # Parse column diffs
        diff_lines = re.findall(r"Column '([^']+)':\s*(\d+)\s*row", compare_text)
        if diff_lines:
            rows = "".join(
                f"<tr><td>{html.escape(col)}</td><td>{html.escape(count)}</td></tr>"
                for col, count in diff_lines
            )
            table = f"""<div class="table-wrap"><table id="compare-table">
<thead><tr><th onclick="sortTable('compare-table', 0)">Column</th>
<th onclick="sortTable('compare-table', 1)"># Rows Different</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""
        else:
            table = f'<pre class="mono" style="padding:12px; background:#fafbfc; border-radius:4px;">{html.escape(compare_text)}</pre>'
        body = callout + table
    else:
        body = '<div class="callout callout-success"><strong>MATCH</strong> &mdash; Production and QC datasets match perfectly.</div>'

    iteration = 0
    if state_dict:
        iteration = state_dict.get("comparison_iteration", 0)
    if iteration > 0:
        body += f'<p style="margin-top:8px; font-size:0.88em; color:#7f8c8d;">Comparison iterations completed: {iteration}</p>'

    return _collapsible_section("Production vs QC Comparison", body, open_default=True)


def _render_validation_section(validation: Optional[dict]) -> str:
    if validation is None:
        return _collapsible_section("P21 Validation",
                                    '<p class="placeholder">Validation not yet run.</p>', open_default=True)

    checks = validation.get("checks", [])
    n_pass = sum(1 for c in checks if c.get("status", "").upper() == "PASS")
    n_fail = sum(1 for c in checks if c.get("status", "").upper() == "FAIL")

    # Severity grid
    grid = f"""<div class="dashboard" style="margin-bottom:16px;">
  <div class="stat-box success" style="flex: 0 1 150px;">
    <h3>Pass</h3><div class="value">{n_pass}</div>
  </div>
  <div class="stat-box {'failure' if n_fail > 0 else 'pending'}" style="flex: 0 1 150px;">
    <h3>Fail</h3><div class="value">{n_fail}</div>
  </div>
</div>"""

    # Filter buttons
    filters = """<div class="filter-bar">
  <button class="filter-btn active" data-filter="ALL" onclick="filterChecks('ALL')">All</button>
  <button class="filter-btn" data-filter="PASS" onclick="filterChecks('PASS')">Pass Only</button>
  <button class="filter-btn" data-filter="FAIL" onclick="filterChecks('FAIL')">Fail Only</button>
</div>"""

    # Checks table
    if checks:
        rows = []
        for c in checks:
            status = c.get("status", "UNKNOWN").upper()
            badge = f'<span class="check-pass">PASS</span>' if status == "PASS" else f'<span class="check-fail">FAIL</span>'
            rows.append(
                f'<tr><td>{html.escape(str(c.get("name", "")))}</td>'
                f'<td>{badge}</td>'
                f'<td>{html.escape(str(c.get("details", "")))}</td></tr>'
            )
        table = f"""<div class="table-wrap"><table id="validation-table">
<thead><tr><th onclick="sortTable('validation-table', 0)">Check Name</th>
<th onclick="sortTable('validation-table', 1)">Status</th>
<th onclick="sortTable('validation-table', 2)">Details</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>"""
    else:
        table = '<p class="placeholder">No individual checks recorded.</p>'

    body = grid + filters + table
    return _collapsible_section("P21 Validation", body, open_default=True)


def _render_dataset_preview(prod_df: Any, qc_df: Any, n_rows: int) -> str:
    body_parts = []

    for label, df in [("Production Dataset", prod_df), ("QC Dataset", qc_df)]:
        if df is None:
            body_parts.append(f'<h4 style="margin:12px 0 6px;">{html.escape(label)}</h4>')
            body_parts.append(f'<p class="placeholder">{html.escape(label)} not available.</p>')
            continue
        body_parts.append(f'<h4 style="margin:12px 0 6px;">{html.escape(label)} (first {n_rows} rows)</h4>')
        body_parts.append(_dataframe_to_html(df.head(n_rows), table_id=label.lower().replace(" ", "-")))

    body = "".join(body_parts)
    return _collapsible_section("Dataset Preview", body, open_default=False)


def _render_p21_sheet(p21_data: Optional[dict]) -> str:
    if p21_data is None:
        return _collapsible_section("P21 Spec Sheet",
                                    '<p class="placeholder">P21 spec sheet (p21_spec_sheet.xlsx) not available.</p>',
                                    open_default=False)

    body_parts = []
    if "variables" in p21_data:
        body_parts.append('<h4 style="margin:12px 0 6px;">Variables</h4>')
        body_parts.append(_dataframe_to_html(p21_data["variables"], table_id="p21-variables"))
    if "valuelevel" in p21_data:
        body_parts.append('<h4 style="margin:16px 0 6px;">Value Level</h4>')
        body_parts.append(_dataframe_to_html(p21_data["valuelevel"], table_id="p21-valuelevel"))
    if not body_parts:
        for key, df in p21_data.items():
            body_parts.append(f'<h4 style="margin:12px 0 6px;">{html.escape(str(key))}</h4>')
            body_parts.append(_dataframe_to_html(df, table_id=f"p21-{key}"))

    body = "".join(body_parts) if body_parts else '<p class="placeholder">No sheets found.</p>'
    return _collapsible_section("P21 Spec Sheet", body, open_default=False)


def _render_error_log(errors: Optional[List[str]]) -> str:
    if not errors:
        return ""
    items = "".join(f'<li style="margin-bottom:6px;">{html.escape(str(e))}</li>' for e in errors)
    body = f'<ul style="margin:0; padding-left:20px;">{items}</ul>'
    return f"""<details class="section error-section" open>
  <summary>Error Log ({len(errors)} error{"s" if len(errors) != 1 else ""})</summary>
  <div class="section-body">{body}</div>
</details>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collapsible_section(title: str, body_html: str, open_default: bool = True) -> str:
    open_attr = " open" if open_default else ""
    return f"""<details class="section"{open_attr}>
  <summary>{html.escape(title)}</summary>
  <div class="section-body">{body_html}</div>
</details>"""


def _dataframe_to_html(df: Any, table_id: str = "") -> str:
    """Convert a pandas DataFrame to an HTML table string."""
    if df is None:
        return '<p class="placeholder">No data available.</p>'
    try:
        columns = list(df.columns)
    except AttributeError:
        return '<p class="placeholder">Invalid data format.</p>'
    tid = f' id="{html.escape(table_id)}"' if table_id else ""
    header_cells = "".join(
        f'<th onclick="sortTable(\'{html.escape(table_id)}\', {i})">{html.escape(str(c))}</th>'
        for i, c in enumerate(columns)
    )
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{html.escape(str(v))}</td>" for v in row)
        rows.append(f"<tr>{cells}</tr>")
    return f"""<div class="table-wrap"><table{tid}>
<thead><tr>{header_cells}</tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>"""


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def generate_report(
    output_dir,
    state=None,
    domain: str = "DM",
    study_id: str = "XYZ-2026-001",
    report_path=None,
    n_preview_rows: int = 10,
) -> Path:
    """
    Generate a self-contained HTML pipeline report.

    Parameters
    ----------
    output_dir : str or Path
        Path to the pipeline output directory.
    state : PipelineState or None
        Optional PipelineState object. If None, loads from pipeline_state.json.
    domain : str
        SDTM domain code (default "DM").
    study_id : str
        Study identifier for the report header.
    report_path : str or Path or None
        Output HTML path. Defaults to {output_dir}/reports/{domain}_pipeline_report.html.
    n_preview_rows : int
        Number of rows to show in dataset preview tables.

    Returns
    -------
    Path
        Path to the generated HTML file.
    """
    output_dir = Path(output_dir)

    # Resolve state
    state_dict = None
    if state is not None:
        # Accept PipelineState dataclass or plain dict
        if hasattr(state, "__dataclass_fields__"):
            from dataclasses import asdict
            state_dict = asdict(state)
        elif isinstance(state, dict):
            state_dict = state
    if state_dict is None:
        state_dict = _load_state(output_dir)

    # Load all data sources
    spec = _load_spec(output_dir, domain)
    compare_text = _load_compare_report(output_dir, domain)
    validation = _load_validation(output_dir)
    prod_df = _load_dataset(output_dir, domain, "production")
    qc_df = _load_dataset(output_dir, domain, "qc")
    p21_data = _load_p21_spec_sheet(output_dir)
    errors = _load_errors(state_dict)

    # Determine overall status
    status = _overall_status(state_dict, validation, compare_text)

    # Build HTML
    sections = [
        _render_header(study_id, domain, status),
        '<div class="container">',
        _render_dashboard(state_dict, spec, validation, compare_text),
        _render_timeline(state_dict),
        _render_spec_section(spec),
        _render_comparison_section(compare_text, state_dict),
        _render_validation_section(validation),
        _render_dataset_preview(prod_df, qc_df, n_preview_rows),
        _render_p21_sheet(p21_data),
        _render_error_log(errors),
        '</div>',
    ]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SDTM Pipeline Report &mdash; {html.escape(domain)} | {html.escape(study_id)}</title>
{_render_css()}
{_render_js()}
</head>
<body>
{"".join(sections)}
</body>
</html>"""

    # Write report
    if report_path is None:
        report_path = output_dir / "reports" / f"{domain.lower()}_pipeline_report.html"
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html_content, encoding="utf-8")

    return report_path


# ---------------------------------------------------------------------------
# CLI entry point (allows standalone use: python report_generator.py <output_dir>)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    out_dir = sys.argv[1] if len(sys.argv) > 1 else "orchestrator/outputs"
    dom = sys.argv[2] if len(sys.argv) > 2 else "DM"
    sid = sys.argv[3] if len(sys.argv) > 3 else "XYZ-2026-001"

    path = generate_report(out_dir, domain=dom, study_id=sid)
    print(f"Report generated: {path}")
