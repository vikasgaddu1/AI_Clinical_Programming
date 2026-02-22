"""
Spec Reviewer Agent: review draft spec for completeness and CDISC compliance.

Validates required variables (fetched from IG), CT references, derivation logic,
function selection, and CRF coverage.  Returns annotated spec with pass/fail
and comments.

Variable requirements are NOT hardcoded — they come from the SDTM IG content
via IGClient.get_required_variables(domain).  Permissible/supplemental variables
are checked against the annotated CRF.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from orchestrator.core.ig_client import IGClient


def _load_crf_variables(crf_path: str) -> Set[str]:
    """Load SDTM variable names from the annotated CRF CSV."""
    path = Path(crf_path)
    if not path.exists():
        return set()
    variables: Set[str] = set()
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            var = row.get("SDTM Variable", "").strip()
            if var:
                variables.add(var)
    return variables


def review_spec(
    spec: Dict[str, Any],
    ig_client: Optional[IGClient] = None,
    crf_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Review draft spec.  Adds review_comments and review_pass to the spec.

    Checks:
    1. Required variables (from IG) are present in the spec
    2. CRF-annotated variables are covered (permissible/supplemental)
    3. CT-controlled variables reference a codelist
    4. Derivation dependencies are correct (e.g. AGE needs BRTHDTC)
    5. Function parameters are valid

    Parameters:
        spec:       The draft mapping specification dict
        ig_client:  IGClient instance (provides required variable list from IG)
        crf_path:   Path to annotated_crf_dm.csv (provides CRF coverage check)
    """
    comments: List[str] = []
    variables = spec.get("variables", [])
    seen = {v.get("target_variable") for v in variables}
    domain = spec.get("domain", "DM")

    # ---- 1. Required variables from IG ----
    if ig_client and ig_client.is_available():
        required_vars = set(ig_client.get_required_variables(domain))
        missing_required = required_vars - seen
        if missing_required:
            comments.append(
                f"Missing IG-required {domain} variables: {sorted(missing_required)}"
            )

        # Also check CT-controlled variables are referencing a codelist
        ct_vars_from_ig = ig_client.get_ct_variables(domain)
        ct_var_names = {row["variable"] for row in ct_vars_from_ig}
        for var_name in ct_var_names & seen:
            spec_var = next((v for v in variables if v.get("target_variable") == var_name), None)
            if spec_var and not spec_var.get("codelist_code") and not spec_var.get("macro_used"):
                comments.append(
                    f"{var_name}: IG says CT-controlled but spec has no codelist_code or CT function"
                )
    else:
        # Fallback: minimal hardcoded check if IG not available
        _FALLBACK_REQUIRED = {
            "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC", "SITEID",
            "AGE", "AGEU", "SEX", "ARMCD", "ARM", "COUNTRY",
        }
        missing_required = _FALLBACK_REQUIRED - seen
        if missing_required:
            comments.append(
                f"Missing required {domain} variables (fallback check): {sorted(missing_required)}"
            )

    # ---- 2. CRF coverage check ----
    if crf_path:
        crf_vars = _load_crf_variables(crf_path)
        uncovered = crf_vars - seen
        if uncovered:
            comments.append(
                f"CRF-annotated variables not in spec: {sorted(uncovered)}"
            )

    # ---- 3. Derivation dependency checks ----
    for v in variables:
        tgt = v.get("target_variable", "")

        # AGE derivation requires BRTHDTC (from iso_date) and RFSTDTC
        if v.get("macro_used") == "derive_age" and tgt == "AGE":
            if not any(x.get("target_variable") == "BRTHDTC" for x in variables):
                comments.append("AGE derivation requires BRTHDTC (from iso_date)")
            if not any(x.get("target_variable") == "RFSTDTC" for x in variables):
                comments.append("AGE derivation requires RFSTDTC (reference date)")

        # DMDY derivation requires DMDTC and RFSTDTC
        if tgt == "DMDY":
            if "DMDTC" not in seen:
                comments.append("DMDY derivation requires DMDTC")
            if "RFSTDTC" not in seen:
                comments.append("DMDY derivation requires RFSTDTC")

        # USUBJID derivation requires STUDYID and SUBJID
        if tgt == "USUBJID":
            if "STUDYID" not in seen:
                comments.append("USUBJID derivation requires STUDYID")
            if "SUBJID" not in seen:
                comments.append("USUBJID derivation requires SUBJID")

    # ---- 4. Function parameter validation ----
    for v in variables:
        fn = v.get("macro_used", "")
        params = v.get("function_parameters", {})
        if fn == "iso_date" and not params.get("invar"):
            comments.append(f"{v.get('target_variable')}: iso_date missing 'invar' parameter")
        if fn == "assign_ct" and not params.get("codelist"):
            comments.append(f"{v.get('target_variable')}: assign_ct missing 'codelist' parameter")

    spec["review_comments"] = comments
    spec["review_pass"] = len(comments) == 0
    return spec
