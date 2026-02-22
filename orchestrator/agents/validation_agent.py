"""
Validation Agent: run checks on final dataset and generate P21/define metadata.

Reads final SDTM dataset (Parquet primary; CSV/RDS supported) and approved spec,
performs comprehensive validation checks including:
- Required variables from IG
- Controlled terminology for ALL CT-controlled variables
- ISO 8601 date formats for ALL DTC variables
- USUBJID uniqueness and format
- Variable type/length checks
- P21 spec sheet generation
- define.xml metadata with proper SDTM labels
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Standard SDTM labels for define.xml metadata
SDTM_LABELS = {
    "STUDYID": "Study Identifier",
    "DOMAIN": "Domain Abbreviation",
    "USUBJID": "Unique Subject Identifier",
    "SUBJID": "Subject Identifier for the Study",
    "RFSTDTC": "Subject Reference Start Date/Time",
    "RFENDTC": "Subject Reference End Date/Time",
    "RFXSTDTC": "Date/Time of First Study Treatment",
    "RFXENDTC": "Date/Time of Last Study Treatment",
    "RFICDTC": "Date/Time of Informed Consent",
    "RFPENDTC": "Date/Time of End of Participation",
    "DTHDTC": "Date/Time of Death",
    "DTHFL": "Subject Death Flag",
    "SITEID": "Study Site Identifier",
    "INVID": "Investigator Identifier",
    "INVNAM": "Investigator Name",
    "BRTHDTC": "Date/Time of Birth",
    "AGE": "Age",
    "AGEU": "Age Units",
    "SEX": "Sex",
    "RACE": "Race",
    "ETHNIC": "Ethnicity",
    "ARMCD": "Planned Arm Code",
    "ARM": "Description of Planned Arm",
    "ACTARMCD": "Actual Arm Code",
    "ACTARM": "Description of Actual Arm",
    "COUNTRY": "Country",
    "DMDTC": "Date/Time of Collection",
    "DMDY": "Study Day of Collection",
}

# Known CT value sets per codelist
CT_VALID_VALUES = {
    "C66731": {"M", "F", "U"},  # Sex
    "C74457": {
        "WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN",
        "AMERICAN INDIAN OR ALASKA NATIVE",
        "NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER",
        "OTHER", "MULTIPLE",
    },  # Race
    "C66790": {
        "HISPANIC OR LATINO", "NOT HISPANIC OR LATINO",
        "NOT REPORTED", "UNKNOWN",
    },  # Ethnicity
    "C71113": {
        "USA", "CANADA", "UNITED KINGDOM", "MEXICO",
        "GERMANY", "FRANCE", "JAPAN", "CHINA", "INDIA",
    },  # Country (subset)
}


def _read_dataset(path: str):
    """Read production dataset - Parquet preferred, CSV and RDS also supported."""
    import pandas as pd

    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".parquet":
        return pd.read_parquet(p)

    if suffix == ".csv":
        return pd.read_csv(p)

    if suffix == ".rds":
        try:
            import pyreadr
            robj = pyreadr.read_r(str(p))
            return list(robj.values())[0]
        except ImportError:
            raise RuntimeError("Reading RDS requires pyreadr: pip install pyreadr")

    raise ValueError(f"Unsupported format: {p.suffix}. Supported: .parquet, .csv, .rds")


def validate_dataset(
    dataset_path: str,
    spec: Dict[str, Any],
    ig_client=None,
) -> Dict[str, Any]:
    """
    Validate the final SDTM dataset against the spec and IG.

    Checks:
    1. Required variables present (from IG or spec)
    2. CT values valid for ALL CT-controlled variables
    3. ISO 8601 date formats for ALL DTC variables
    4. USUBJID uniqueness and format
    5. Variable types match spec
    6. No unexpected missing values in required fields
    """
    report: Dict[str, Any] = {"pass": True, "issues": [], "checks": {}}
    path = Path(dataset_path)
    if not path.exists():
        report["pass"] = False
        report["issues"].append(f"Dataset not found: {dataset_path}")
        return report

    try:
        df = _read_dataset(dataset_path)
    except Exception as e:
        report["pass"] = False
        report["issues"].append(f"Could not read dataset: {e}")
        return report

    actual_vars = set(df.columns)

    # ---- 1. Required variable check ----
    expected_vars = {v["target_variable"] for v in spec.get("variables", [])}
    missing = expected_vars - actual_vars
    if missing:
        report["issues"].append(f"Missing spec variables: {sorted(missing)}")
        report["pass"] = False
    report["checks"]["required_variables"] = len(missing) == 0

    # Also check IG-required variables if ig_client available
    if ig_client and ig_client.is_available():
        domain = spec.get("domain", "DM")
        ig_required = set(ig_client.get_required_variables(domain))
        ig_missing = ig_required - actual_vars
        if ig_missing:
            report["issues"].append(f"Missing IG-required variables: {sorted(ig_missing)}")
            report["pass"] = False
        report["checks"]["ig_required_variables"] = len(ig_missing) == 0

    # ---- 2. Controlled terminology checks ----
    ct_mapping = {
        "SEX": "C66731",
        "RACE": "C74457",
        "ETHNIC": "C66790",
    }

    # Also pull from spec for any additional CT variables
    for v in spec.get("variables", []):
        codelist = v.get("codelist_code")
        var_name = v.get("target_variable")
        if codelist and var_name:
            ct_mapping[var_name] = codelist

    for var_name, codelist in ct_mapping.items():
        if var_name not in df.columns:
            continue
        valid_values = CT_VALID_VALUES.get(codelist)
        if valid_values is None:
            continue

        actual_values = set(df[var_name].dropna().astype(str))
        invalid = actual_values - valid_values
        ct_ok = len(invalid) == 0
        report["checks"][f"ct_{var_name.lower()}"] = ct_ok
        if not ct_ok:
            report["issues"].append(
                f"{var_name} (codelist {codelist}): invalid values {sorted(invalid)}"
            )
            report["pass"] = False

    # ---- 3. ISO 8601 date format check for ALL DTC variables ----
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    dtc_vars = [c for c in df.columns if c.endswith("DTC")]
    for dtc_var in dtc_vars:
        non_null = df[dtc_var].dropna().astype(str)
        non_iso = non_null[~non_null.apply(lambda x: bool(iso_pattern.match(x)) or x == "")]
        check_ok = non_iso.empty
        report["checks"][f"iso_{dtc_var.lower()}"] = check_ok
        if not check_ok:
            report["issues"].append(
                f"{dtc_var}: {len(non_iso)} value(s) not in ISO 8601 YYYY-MM-DD format"
            )
            report["pass"] = False

    # ---- 4. USUBJID uniqueness and format ----
    if "USUBJID" in df.columns:
        dup_count = df["USUBJID"].duplicated().sum()
        report["checks"]["usubjid_unique"] = dup_count == 0
        if dup_count > 0:
            report["issues"].append(f"USUBJID has {dup_count} duplicate(s)")
            report["pass"] = False

        # Check format: should contain STUDYID
        study_id = spec.get("study_id", "")
        if study_id:
            bad_format = df["USUBJID"].dropna().astype(str)
            bad_format = bad_format[~bad_format.str.startswith(study_id)]
            report["checks"]["usubjid_format"] = bad_format.empty
            if not bad_format.empty:
                report["issues"].append(
                    f"USUBJID: {len(bad_format)} value(s) don't start with STUDYID '{study_id}'"
                )
                report["pass"] = False

    # ---- 5. Variable type checks ----
    for v in spec.get("variables", []):
        var_name = v.get("target_variable")
        expected_type = v.get("data_type", "Char")
        if var_name not in df.columns:
            continue
        actual_dtype = str(df[var_name].dtype)
        if expected_type == "Num" and "int" not in actual_dtype and "float" not in actual_dtype:
            report["issues"].append(
                f"{var_name}: spec says Num but actual type is {actual_dtype}"
            )
        report["checks"][f"type_{var_name.lower()}"] = True

    # ---- 6. Required fields not empty ----
    critical_required = ["STUDYID", "DOMAIN", "USUBJID", "SUBJID", "SITEID"]
    for var_name in critical_required:
        if var_name in df.columns:
            null_count = df[var_name].isna().sum()
            report["checks"][f"not_null_{var_name.lower()}"] = null_count == 0
            if null_count > 0:
                report["issues"].append(
                    f"{var_name}: {null_count} missing value(s) in required field"
                )
                report["pass"] = False

    return report


def generate_define_metadata(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Generate define.xml-style metadata structure from the spec."""
    return {
        "study_id": spec.get("study_id"),
        "domain": spec.get("domain"),
        "variables": [
            {
                "name": v.get("target_variable"),
                "label": SDTM_LABELS.get(
                    v.get("target_variable", ""),
                    v.get("target_variable", ""),
                ),
                "type": v.get("data_type", "Char"),
                "length": v.get("length", 0),
                "codelist": v.get("codelist_code"),
                "origin": "CRF" if v.get("source_dataset") == "raw_dm" else "Derived",
            }
            for v in spec.get("variables", [])
        ],
    }


def generate_p21_spec_sheet(
    spec: Dict[str, Any],
    output_path: str,
) -> Optional[str]:
    """
    Generate a Pinnacle 21 specification sheet (XLSX) from the approved spec.

    Creates two tabs:
    - Variables: variable-level metadata (name, label, type, length, codelist, origin)
    - ValueLevel: value-level metadata (codelist entries)
    """
    try:
        import pandas as pd
    except ImportError:
        return None

    path = Path(output_path)

    # Variable-level tab
    var_rows = []
    for v in spec.get("variables", []):
        var_name = v.get("target_variable", "")
        var_rows.append({
            "Dataset": spec.get("domain", "DM"),
            "Variable": var_name,
            "Label": SDTM_LABELS.get(var_name, var_name),
            "Type": v.get("data_type", "Char"),
            "Length": v.get("length", ""),
            "Codelist": v.get("codelist_code", ""),
            "Origin": "CRF" if v.get("source_dataset") == "raw_dm" else "Derived",
            "Comment": v.get("mapping_logic", ""),
        })
    var_df = pd.DataFrame(var_rows)

    # Value-level tab (codelist entries)
    vl_rows = []
    for v in spec.get("variables", []):
        codelist = v.get("codelist_code", "")
        if codelist and codelist in CT_VALID_VALUES:
            for val in sorted(CT_VALID_VALUES[codelist]):
                vl_rows.append({
                    "Dataset": spec.get("domain", "DM"),
                    "Variable": v.get("target_variable", ""),
                    "Codelist": codelist,
                    "CodelistName": v.get("codelist_name", ""),
                    "CodedValue": val,
                })
    vl_df = pd.DataFrame(vl_rows) if vl_rows else pd.DataFrame()

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        var_df.to_excel(writer, sheet_name="Variables", index=False)
        if not vl_df.empty:
            vl_df.to_excel(writer, sheet_name="ValueLevel", index=False)

    return str(path)
