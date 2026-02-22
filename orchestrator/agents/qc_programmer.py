"""
QC Programmer Agent: generate an independent R script from the same approved spec.

Produces a second R script implementing the same mapping logic with genuinely
different structure (different variable names, different operation ordering,
different coding style) but identical final output.  The orchestrator then
runs both scripts and compares the outputs.

IMPORTANT: This module does NOT import from production_programmer.  The whole
point of double programming is that two *independent* implementations of the
same specification should produce identical results.

Memory-aware: accepts memory_context to prepend standard program header
and enforce coding standards.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


def _path_for_r(p: str) -> str:
    """Use forward slashes for R (Windows-friendly)."""
    return Path(p).as_posix()


def _get_spec_variables(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the variable list from the spec."""
    return spec.get("variables", [])


def _find_spec_var(variables: List[Dict[str, Any]], target: str) -> Optional[Dict[str, Any]]:
    """Find a variable entry by target_variable name."""
    for v in variables:
        if v.get("target_variable") == target:
            return v
    return None


def _get_race_approach(spec: Dict[str, Any]) -> str:
    """
    Determine the RACE approach from human decisions in the spec.

    Returns "A", "B", or "C". Defaults to "B" (SUPPDM) if not specified.
    """
    decisions = spec.get("human_decisions", {})
    race_decision = decisions.get("RACE", {})
    return race_decision.get("choice", "B")


def generate_qc_r_script(
    spec: Dict[str, Any],
    raw_data_path: str,
    output_dataset_path: str,
    function_library_path: str,
    ct_lookup_path: str,
    output_format: str = "parquet",
    write_xpt: bool = False,
    xpt_path: Optional[str] = None,
    memory_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate an independent QC R script from the approved mapping spec.

    This implementation is deliberately structured differently from the
    production programmer:
    - Uses 'qc_data' as the working data frame (not 'dm')
    - Sets constant/identifier variables FIRST
    - Applies CT mapping BEFORE date conversions where safe
    - Uses a different variable reordering approach
    - Different comment style and structure

    The final dataset must have identical variable names, types, and values
    to the production dataset.

    When memory_context is provided, the generated script includes:
    - Standard company program header with modification history
    - Coding standards compliance (lowercase code, UPPERCASE SDTM vars)
    - Human decision-driven logic (e.g., RACE approach A/B/C)
    """
    lib_path = _path_for_r(function_library_path)
    raw_path = _path_for_r(raw_data_path)
    out_path = _path_for_r(output_dataset_path)
    ct_path = _path_for_r(ct_lookup_path)

    variables = _get_spec_variables(spec)
    race_approach = _get_race_approach(spec)
    study_id = spec.get("study_id", "XYZ-2026-001")

    lines: List[str] = []

    # --- Standard program header (from memory) ---
    if memory_context and memory_context.get("program_header"):
        for header_line in memory_context["program_header"].rstrip("\n").split("\n"):
            lines.append(header_line)
        lines.append("")
    else:
        lines += [
            "###############################################################################",
            "# DM QC Program - Independent implementation from approved mapping spec",
            "# Spec: dm_mapping_spec_approved.json",
            "# This QC program is structurally independent from the production program.",
            "# It uses the same R functions and the same spec but different code structure.",
            "###############################################################################",
            "",
        ]

    # --- Load packages ---
    lines += [
        "## load packages ----",
        "library(arrow)",
        "library(haven)",
        "",
    ]

    # --- Source functions ---
    lines += [
        "## source functions ----",
        f'fn_dir <- "{lib_path}"',
        'source(file.path(fn_dir, "iso_date.R"))',
        'source(file.path(fn_dir, "derive_age.R"))',
        'source(file.path(fn_dir, "assign_ct.R"))',
        "",
        "## paths ----",
        f'ct_file   <- "{ct_path}"',
        f'raw_file  <- "{raw_path}"',
        f'out_file  <- "{out_path}"',
    ]

    if write_xpt and xpt_path:
        lines.append(f'xpt_file  <- "{_path_for_r(xpt_path)}"')

    # --- Read data ---
    lines += [
        "",
        "## ========== read data ==========",
        'qc_raw  <- read.csv(raw_file, stringsAsFactors = FALSE)',
        'qc_data <- qc_raw',
        "",
    ]

    # --- Step 1: Constants and identifiers (production does this AFTER transformations) ---
    lines += [
        "## ========== step 1: constants and identifiers ==========",
        '# qc approach: set identifiers first, then transform',
        '',
        '# STUDYID (constant)',
        f'qc_data$STUDYID <- "{study_id}"',
        '',
        '# DOMAIN (constant)',
        'qc_data$DOMAIN <- "DM"',
        '',
        '# USUBJID (derived: STUDYID-SUBJID)',
        'qc_data$USUBJID <- paste(qc_data$STUDYID, qc_data$SUBJID, sep = "-")',
        "",
    ]

    # --- Step 2: CT mapping (production does dates first, QC does CT first) ---
    lines += [
        "## ========== step 2: controlled terminology mapping ==========",
        '# qc approach: apply CT mappings before date conversions',
        '# (CT mapping does not depend on ISO dates)',
        "",
    ]

    # SEX
    if _find_spec_var(variables, "SEX"):
        lines += [
            '# SEX - codelist C66731',
            'qc_data <- assign_ct(qc_data, invar = "SEX", outvar = "SEX",',
            '                     codelist = "C66731", ctpath = ct_file, unmapped = "FLAG")',
            "",
        ]

    # RACE — approach-aware
    if _find_spec_var(variables, "RACE"):
        lines += [
            '# RACE - codelist C74457',
            f'# approach {race_approach} per human decision',
            'qc_data <- assign_ct(qc_data, invar = "RACE", outvar = "RACE",',
            '                     codelist = "C74457", ctpath = ct_file, unmapped = "FLAG")',
            "",
        ]

    # ETHNIC
    if _find_spec_var(variables, "ETHNIC"):
        lines += [
            '# ETHNIC - codelist C66790',
            'qc_data <- assign_ct(qc_data, invar = "ETHNIC", outvar = "ETHNIC",',
            '                     codelist = "C66790", ctpath = ct_file, unmapped = "FLAG")',
            "",
        ]

    # --- Step 3: Date conversions ---
    lines += [
        "## ========== step 3: date conversions ==========",
        "",
        '# BRTHDTC from raw BRTHDT (iso_date auto-detects format)',
        'qc_data <- iso_date(qc_data, invar = "BRTHDT", outvar = "BRTHDTC")',
        "",
        '# RFSTDTC standardised to ISO 8601',
        'qc_data <- iso_date(qc_data, invar = "RFSTDTC", outvar = "RFSTDTC")',
        "",
    ]

    # --- Step 4: Age derivation ---
    lines += [
        "## ========== step 4: age derivation ==========",
        '# AGE and AGEU from BRTHDTC + RFSTDTC',
        'qc_data <- derive_age(qc_data, brthdt = "BRTHDTC", refdt = "RFSTDTC",',
        '                      agevar = "AGE", ageuvar = "AGEU", create_ageu = TRUE)',
        "",
    ]

    # --- Step 5: Additional required variables ---
    lines += [
        "## ========== step 5: additional required SDTM variables ==========",
        "",
        '# ACTARMCD - set equal to ARMCD (no treatment deviations in this study)',
        'qc_data$ACTARMCD <- qc_data$ARMCD',
        "",
        '# ACTARM - set equal to ARM (no treatment deviations)',
        'qc_data$ACTARM <- qc_data$ARM',
        "",
        '# DMDTC - demographics assessment date (set to RFSTDTC = enrollment date)',
        'qc_data$DMDTC <- qc_data$RFSTDTC',
        "",
        '# DMDY - study day of demographics',
        '# when DMDTC = RFSTDTC, DMDY = 1 by convention',
        'qc_data$DMDY <- as.integer(as.Date(qc_data$DMDTC) - as.Date(qc_data$RFSTDTC)) + 1L',
        "",
        '# RFENDTC - no raw source available; set to missing',
        'qc_data$RFENDTC <- NA_character_',
        "",
    ]

    # --- Step 6: SUPPDM for RACE Other Specify (approach-dependent) ---
    if race_approach in ("B", "C"):
        lines += [
            "## ========== step 6: SUPPDM for RACE Other Specify ==========",
            '# create supplemental records for subjects with Other Specify race values',
            'suppdm_idx <- which(!is.na(qc_raw$RACEOTH) & trimws(qc_raw$RACEOTH) != "")',
            'if (length(suppdm_idx) > 0) {',
            '  suppdm <- data.frame(',
            '    STUDYID  = qc_data$STUDYID[suppdm_idx],',
            '    RDOMAIN  = "DM",',
            '    USUBJID  = qc_data$USUBJID[suppdm_idx],',
            '    IDVAR    = "",',
            '    IDVARVAL = "",',
            '    QNAM     = "RACEOTH",',
            '    QLABEL   = "Race Other Specify",',
            '    QVAL     = qc_raw$RACEOTH[suppdm_idx],',
            '    QORIG    = "CRF",',
            '    QEVAL    = "",',
            '    stringsAsFactors = FALSE',
            '  )',
            '  suppdm_path <- gsub("dm_qc\\\\.", "suppdm_qc.", out_file)',
            '  arrow::write_parquet(suppdm, suppdm_path)',
            '  message("QC SUPPDM written with ", nrow(suppdm), " records to ", suppdm_path)',
            '}',
            "",
        ]

    # --- Step 7: Select and reorder variables ---
    lines += [
        "## ========== step 7: variable selection and ordering ==========",
        '# qc approach: build the target column list from the SDTM standard,',
        '# then select only those columns that exist in our data frame',
        'target_vars <- c(',
        '  "STUDYID", "DOMAIN", "USUBJID", "SUBJID",',
        '  "RFSTDTC", "RFENDTC", "SITEID", "INVNAM", "BRTHDTC",',
        '  "AGE", "AGEU", "SEX", "RACE", "ETHNIC",',
        '  "ARMCD", "ARM", "ACTARMCD", "ACTARM",',
        '  "COUNTRY", "DMDTC", "DMDY"',
        ')',
        '',
        '# keep only target vars that exist, plus any extras from the raw data',
        'keep_target <- target_vars[target_vars %in% names(qc_data)]',
        'keep_extra  <- setdiff(names(qc_data), target_vars)',
        'qc_data <- qc_data[, c(keep_target, keep_extra)]',
        "",
    ]

    # --- Step 8: Write output ---
    lines.append("## ========== step 8: output ==========")

    if output_format.lower() == "parquet":
        lines.append('arrow::write_parquet(qc_data, out_file)')
    elif output_format.lower() == "csv":
        lines.append('write.csv(qc_data, out_file, row.names = FALSE)')
    else:
        lines.append('saveRDS(qc_data, out_file)')

    lines.append('message("QC dataset written to ", out_file)')

    if write_xpt and xpt_path:
        lines += [
            "",
            "## write XPT for regulatory comparison",
            'haven::write_xpt(qc_data, path = xpt_file, version = 5)',
            'message("QC XPT written to ", xpt_file)',
        ]

    lines.append("")
    lines.append("## === end of QC program ===")

    return "\n".join(lines)
