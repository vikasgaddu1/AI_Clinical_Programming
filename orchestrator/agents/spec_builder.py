"""
Spec Builder Agent: analyze raw data and study docs to produce draft mapping spec.

Uses function registry (R), optional IG client, and raw data to build
dm_mapping_spec.json with variables and decision points. In full implementation
would call Claude API; here provides structure and placeholder for LLM integration.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from orchestrator.core.function_loader import FunctionLoader
from orchestrator.core.ig_client import IGClient


def profile_raw_data(csv_path: str) -> Dict[str, Any]:
    """Profile raw DM CSV: variables, types, sample values, missing counts."""
    path = Path(csv_path)
    if not path.exists():
        return {"error": f"File not found: {csv_path}"}
    df = pd.read_csv(path, nrows=1000)
    profile = {
        "variables": list(df.columns),
        "nrows": len(df),
        "dtypes": {c: str(d) for c, d in df.dtypes.items()},
        "sample_values": {},
        "missing": {},
    }
    for col in df.columns:
        profile["sample_values"][col] = df[col].dropna().head(5).tolist()
        profile["missing"][col] = int(df[col].isna().sum())
    return profile


def build_draft_spec(
    study_id: str,
    domain: str,
    raw_data_path: str,
    function_loader: FunctionLoader,
    ig_client: Optional[IGClient] = None,
) -> Dict[str, Any]:
    """
    Build a draft DM mapping spec from raw data and registry.
    Does not call LLM; produces a minimal spec that can be refined by Spec Reviewer
    and Human Review. For full AI-driven spec, integrate Claude in this module.
    """
    profile = profile_raw_data(raw_data_path)
    if "error" in profile:
        return {"study_id": study_id, "domain": domain, "variables": [], "error": profile["error"]}

    # Map common raw columns to SDTM DM variables and functions from registry
    function_order = function_loader.get_dependency_order()
    var_mapping = [
        ("BRTHDT", "BRTHDTC", "iso_date", {"invar": "BRTHDT", "outvar": "BRTHDTC"}),
        ("RFSTDTC", "RFSTDTC", "iso_date", {"invar": "RFSTDTC", "outvar": "RFSTDTC"}),
        ("BRTHDTC", "AGE", "derive_age", {"brthdt": "BRTHDTC", "refdt": "RFSTDTC"}),
        ("SEX", "SEX", "assign_ct", {"invar": "SEX", "outvar": "SEX", "codelist": "C66731"}),
        ("RACE", "RACE", "assign_ct", {"invar": "RACE", "outvar": "RACE", "codelist": "C74457"}),
        ("ETHNIC", "ETHNIC", "assign_ct", {"invar": "ETHNIC", "outvar": "ETHNIC", "codelist": "C66790"}),
    ]

    variables: List[Dict[str, Any]] = []
    for src_var, tgt_var, fn_name, params in var_mapping:
        if src_var not in profile["variables"] and tgt_var != "AGE":
            continue
        var_spec = {
            "target_variable": tgt_var,
            "target_domain": domain,
            "source_variable": src_var,
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 60,
            "mapping_logic": f"Apply {fn_name}() with params {params}",
            "macro_used": fn_name,
            "function_parameters": params,
            "human_decision_required": tgt_var == "RACE",
        }
        if tgt_var == "AGE":
            var_spec["data_type"] = "Num"
            var_spec["length"] = 8
        if tgt_var == "SEX":
            var_spec["codelist_code"] = "C66731"
            var_spec["codelist_name"] = "Sex"
            var_spec["controlled_terms"] = ["M", "F", "U"]
        if tgt_var == "RACE":
            var_spec["codelist_code"] = "C74457"
            var_spec["codelist_name"] = "Race"
            var_spec["decision_options"] = [
                {"id": "A", "description": "Map free-text to closest CT term where possible.", "ig_reference": "SDTM IG 3.4", "pros": ["Maximizes CT"], "cons": ["Judgment calls"]},
                {"id": "B", "description": "All Other Specify → RACE='OTHER', free text in SUPPDM.", "ig_reference": "SDTM IG 3.4", "pros": ["Conservative"], "cons": ["Many SUPPDM"]},
                {"id": "C", "description": "Mixed → MULTIPLE, individual in SUPPDM.", "ig_reference": "SDTM IG 3.4", "pros": ["Complete"], "cons": ["Complex"]},
            ]
        variables.append(var_spec)

    # Add required SDTM variables that are constants or simple derivations
    for const_var, src in [("STUDYID", "study"), ("DOMAIN", "DM"), ("SUBJID", "SUBJID"), ("SITEID", "SITEID"), ("ARMCD", "ARMCD"), ("ARM", "ARM"), ("COUNTRY", "COUNTRY")]:
        if any(v["target_variable"] == const_var for v in variables):
            continue
        variables.insert(0, {
            "target_variable": const_var,
            "target_domain": domain,
            "source_variable": src,
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 20,
            "mapping_logic": "Constant or pass-through",
            "macro_used": "",
            "human_decision_required": False,
        })

    # USUBJID — derived from STUDYID + SUBJID
    if not any(v["target_variable"] == "USUBJID" for v in variables):
        variables.append({
            "target_variable": "USUBJID",
            "target_domain": domain,
            "source_variable": "SUBJID",
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 40,
            "mapping_logic": "Concatenate STUDYID + '-' + SUBJID",
            "macro_used": "",
            "human_decision_required": False,
        })

    # AGEU — derived by derive_age(), always 'YEARS'
    if not any(v["target_variable"] == "AGEU" for v in variables):
        variables.append({
            "target_variable": "AGEU",
            "target_domain": domain,
            "source_variable": "BRTHDTC",
            "source_dataset": "derived",
            "data_type": "Char",
            "length": 10,
            "mapping_logic": "Derived by derive_age(), always 'YEARS'",
            "macro_used": "derive_age",
            "human_decision_required": False,
        })

    # ACTARMCD — set equal to ARMCD (flag as decision point)
    if not any(v["target_variable"] == "ACTARMCD" for v in variables):
        variables.append({
            "target_variable": "ACTARMCD",
            "target_domain": domain,
            "source_variable": "ARMCD",
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 20,
            "mapping_logic": "Set equal to ARMCD (no treatment deviations in this study)",
            "macro_used": "",
            "human_decision_required": True,
            "decision_options": [
                {"id": "A", "description": "ACTARMCD = ARMCD for all subjects (no protocol deviations affecting treatment).", "ig_reference": "SDTM IG 3.4 — ACTARMCD", "pros": ["Simple", "Appropriate when no deviations"], "cons": ["Assumes no deviations exist"]},
                {"id": "B", "description": "Derive ACTARMCD from actual treatment received, compare against planned ARM.", "ig_reference": "SDTM IG 3.4 — ACTARMCD", "pros": ["Handles deviations correctly"], "cons": ["Requires deviation data not in raw_dm"]},
            ],
        })

    # ACTARM — set equal to ARM
    if not any(v["target_variable"] == "ACTARM" for v in variables):
        variables.append({
            "target_variable": "ACTARM",
            "target_domain": domain,
            "source_variable": "ARM",
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 200,
            "mapping_logic": "Set equal to ARM (no treatment deviations in this study)",
            "macro_used": "",
            "human_decision_required": False,
        })

    # DMDTC — demographics assessment date
    if not any(v["target_variable"] == "DMDTC" for v in variables):
        variables.append({
            "target_variable": "DMDTC",
            "target_domain": domain,
            "source_variable": "RFSTDTC",
            "source_dataset": "raw_dm",
            "data_type": "Char",
            "length": 10,
            "mapping_logic": "Set to RFSTDTC (demographics captured at enrollment visit)",
            "macro_used": "",
            "human_decision_required": False,
        })

    # DMDY — study day of demographics assessment
    if not any(v["target_variable"] == "DMDY" for v in variables):
        variables.append({
            "target_variable": "DMDY",
            "target_domain": domain,
            "source_variable": "derived",
            "source_dataset": "derived",
            "data_type": "Num",
            "length": 8,
            "mapping_logic": "(DMDTC - RFSTDTC) + 1; equals 1 when DMDTC = RFSTDTC",
            "macro_used": "",
            "human_decision_required": False,
        })

    # RFENDTC — no raw source available
    if not any(v["target_variable"] == "RFENDTC" for v in variables):
        variables.append({
            "target_variable": "RFENDTC",
            "target_domain": domain,
            "source_variable": "N/A",
            "source_dataset": "N/A",
            "data_type": "Char",
            "length": 10,
            "mapping_logic": "No raw source available in raw_dm; set to missing",
            "macro_used": "",
            "human_decision_required": True,
            "decision_options": [
                {"id": "A", "description": "Set RFENDTC to blank/missing (no end-of-participation date in raw data).", "ig_reference": "SDTM IG 3.4 — RFENDTC", "pros": ["Honest — data not available"], "cons": ["Missing required variable"]},
                {"id": "B", "description": "Derive from last visit date or last dose date if available in other domains.", "ig_reference": "SDTM IG 3.4 — RFENDTC", "pros": ["Populated field"], "cons": ["Source data not in DM domain"]},
            ],
        })

    # INVNAM — investigator name pass-through
    if not any(v["target_variable"] == "INVNAM" for v in variables):
        if "INVNAM" in profile.get("variables", []):
            variables.append({
                "target_variable": "INVNAM",
                "target_domain": domain,
                "source_variable": "INVNAM",
                "source_dataset": "raw_dm",
                "data_type": "Char",
                "length": 100,
                "mapping_logic": "Pass-through from raw data",
                "macro_used": "",
                "human_decision_required": False,
            })

    return {
        "study_id": study_id,
        "domain": domain,
        "spec_version": "1.0",
        "created_by": "Spec Builder Agent",
        "variables": variables,
    }
