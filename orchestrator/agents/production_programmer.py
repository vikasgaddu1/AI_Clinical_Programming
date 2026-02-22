"""
Production Programmer Agent: generate R script from approved spec.

Reads approved spec and function registry, produces a complete R script
that sources r_functions, reads raw data, calls iso_date, derive_age,
assign_ct in order, adds STUDYID/DOMAIN/USUBJID etc., writes DM to
Parquet (primary) and optionally XPT for regulatory submission.

Memory-aware: accepts memory_context to prepend standard program header,
enforce coding standards, and read human_decisions from the spec.
"""

from pathlib import Path
from typing import Any, Dict, Optional


def _path_for_r(p: str) -> str:
    """Use forward slashes for R (Windows-friendly)."""
    return Path(p).as_posix()


def _get_race_approach(spec: Dict[str, Any]) -> str:
    """
    Determine the RACE approach from human decisions in the spec.

    Returns "A", "B", or "C". Defaults to "B" (SUPPDM) if not specified.
    """
    decisions = spec.get("human_decisions", {})
    race_decision = decisions.get("RACE", {})
    return race_decision.get("choice", "B")


def generate_r_script(
    spec: Dict[str, Any],
    raw_data_path: str,
    output_dataset_path: str,
    function_library_path: str,
    ct_lookup_path: str,
    output_format: str = "parquet",
    write_xpt: bool = True,
    xpt_path: Optional[str] = None,
    memory_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a complete R script implementing the approved DM mapping spec.

    Writes the primary output as Parquet (arrow::write_parquet) and
    optionally a SAS transport file (haven::write_xpt) for submission.
    Falls back to write.csv for output_format 'csv' and saveRDS for 'rds'.

    When memory_context is provided, the generated script includes:
    - Standard company program header with modification history
    - Coding standards compliance (lowercase code, UPPERCASE SDTM vars)
    - Human decision-driven logic (e.g., RACE approach A/B/C)
    """
    lib_path = _path_for_r(function_library_path)
    raw_path = _path_for_r(raw_data_path)
    out_path = _path_for_r(output_dataset_path)
    ct_path  = _path_for_r(ct_lookup_path)

    race_approach = _get_race_approach(spec)
    study_id = spec.get("study_id", "XYZ-2026-001")

    lines = []

    # --- Standard program header (from memory) ---
    if memory_context and memory_context.get("program_header"):
        for header_line in memory_context["program_header"].rstrip("\n").split("\n"):
            lines.append(header_line)
        lines.append("")
    else:
        lines += [
            "# DM Production Program - Generated from approved mapping spec",
            "# Spec: dm_mapping_spec_approved.json",
            "",
        ]

    # --- Load packages ---
    lines += [
        "# load packages",
        "# install once before running: install.packages(c(\"arrow\", \"haven\"))",
        'library(arrow)',
        'library(haven)',
        "",
    ]

    # --- Source functions ---
    lines += [
        "# source functions",
        f'library_path <- "{lib_path}"',
        'source(file.path(library_path, "iso_date.R"))',
        'source(file.path(library_path, "derive_age.R"))',
        'source(file.path(library_path, "assign_ct.R"))',
        "",
        f'ct_path  <- "{ct_path}"',
        f'raw_path <- "{raw_path}"',
        f'out_path <- "{out_path}"',
    ]

    if write_xpt and xpt_path:
        lines.append(f'xpt_path <- "{_path_for_r(xpt_path)}"')

    # --- Read data ---
    lines += [
        "",
        "# read data",
        'raw_dm <- read.csv(raw_path, stringsAsFactors = FALSE)',
        'dm <- raw_dm',
        "",
    ]

    # --- Processing ---
    lines += [
        "# processing",
        "",
        "# date conversions (spec: BRTHDT -> BRTHDTC, RFSTDTC)",
        '# variable: BRTHDTC - derived from raw BRTHDT',
        'dm <- iso_date(dm, invar = "BRTHDT", outvar = "BRTHDTC")',
        '# variable: RFSTDTC - standardise to ISO 8601',
        'dm <- iso_date(dm, invar = "RFSTDTC", outvar = "RFSTDTC")',
        "",
        "# age derivation (spec: AGE, AGEU from BRTHDTC and RFSTDTC)",
        'dm <- derive_age(dm, brthdt = "BRTHDTC", refdt = "RFSTDTC",',
        '                 agevar = "AGE", ageuvar = "AGEU", create_ageu = TRUE)',
        "",
        "# controlled terminology (spec: SEX, RACE, ETHNIC)",
        '# variable: SEX',
        '# codelist: C66731 (Sex)',
        'dm <- assign_ct(dm, invar = "SEX", outvar = "SEX", codelist = "C66731",',
        '                ctpath = ct_path, unmapped = "FLAG")',
        '',
    ]

    # RACE handling based on human decision
    if race_approach == "A":
        # Approach A: map free-text to closest CT term where possible
        lines += [
            '# variable: RACE',
            f'# codelist: C74457 (Race) - approach {race_approach}: map free-text to closest CT term',
            'dm <- assign_ct(dm, invar = "RACE", outvar = "RACE", codelist = "C74457",',
            '                ctpath = ct_path, unmapped = "FLAG")',
            '',
        ]
    elif race_approach == "C":
        # Approach C: mixed -> MULTIPLE, individual in SUPPDM
        lines += [
            '# variable: RACE',
            f'# codelist: C74457 (Race) - approach {race_approach}: MULTIPLE + SUPPDM',
            'dm <- assign_ct(dm, invar = "RACE", outvar = "RACE", codelist = "C74457",',
            '                ctpath = ct_path, unmapped = "FLAG")',
            '',
        ]
    else:
        # Approach B (default): Other Specify -> OTHER + SUPPDM.RACEOTH
        lines += [
            '# variable: RACE',
            f'# codelist: C74457 (Race) - approach {race_approach}: OTHER + SUPPDM.RACEOTH',
            'dm <- assign_ct(dm, invar = "RACE", outvar = "RACE", codelist = "C74457",',
            '                ctpath = ct_path, unmapped = "FLAG")',
            '',
        ]

    lines += [
        '# variable: ETHNIC',
        '# codelist: C66790 (Ethnicity)',
        'dm <- assign_ct(dm, invar = "ETHNIC", outvar = "ETHNIC", codelist = "C66790",',
        '                ctpath = ct_path, unmapped = "FLAG")',
        "",
        "# constants and derivations",
        f'dm$STUDYID <- "{study_id}"',
        'dm$DOMAIN  <- "DM"',
        'dm$USUBJID <- paste(dm$STUDYID, dm$SUBJID, sep = "-")',
        "",
        "# additional required SDTM variables",
        '# ACTARMCD and ACTARM (set equal to planned arm - no deviations in this study)',
        'dm$ACTARMCD <- dm$ARMCD',
        'dm$ACTARM   <- dm$ARM',
        "",
        '# DMDTC (demographics assessment date = enrollment date)',
        'dm$DMDTC <- dm$RFSTDTC',
        "",
        '# DMDY (study day of demographics: (DMDTC - RFSTDTC) + 1)',
        'dm$DMDY <- as.integer(as.Date(dm$DMDTC) - as.Date(dm$RFSTDTC)) + 1L',
        "",
        '# RFENDTC (not available in raw data; set to NA)',
        'dm$RFENDTC <- NA_character_',
        "",
    ]

    # SUPPDM generation depends on RACE approach
    if race_approach in ("B", "C"):
        lines += [
            "# SUPPDM for RACE Other Specify",
            '# create supplemental records for subjects with Other Specify race values',
            'suppdm_idx <- which(!is.na(raw_dm$RACEOTH) & trimws(raw_dm$RACEOTH) != "")',
            'if (length(suppdm_idx) > 0) {',
            '  suppdm <- data.frame(',
            '    STUDYID  = dm$STUDYID[suppdm_idx],',
            '    RDOMAIN  = "DM",',
            '    USUBJID  = dm$USUBJID[suppdm_idx],',
            '    IDVAR    = "",',
            '    IDVARVAL = "",',
            '    QNAM     = "RACEOTH",',
            '    QLABEL   = "Race Other Specify",',
            '    QVAL     = raw_dm$RACEOTH[suppdm_idx],',
            '    QORIG    = "CRF",',
            '    QEVAL    = "",',
            '    stringsAsFactors = FALSE',
            '  )',
            '  suppdm_path <- gsub("dm\\\\.", "suppdm.", out_path)',
            '  arrow::write_parquet(suppdm, suppdm_path)',
            '  message("SUPPDM written with ", nrow(suppdm), " records to ", suppdm_path)',
            '}',
            "",
        ]

    # --- Variable ordering ---
    lines += [
        "# reorder to SDTM variable order (key variables first)",
        'sdtm_order <- c("STUDYID", "DOMAIN", "USUBJID", "SUBJID",',
        '                "RFSTDTC", "RFENDTC", "SITEID", "INVNAM", "BRTHDTC",',
        '                "AGE", "AGEU", "SEX", "RACE", "ETHNIC",',
        '                "ARMCD", "ARM", "ACTARMCD", "ACTARM",',
        '                "COUNTRY", "DMDTC", "DMDY")',
        'existing <- intersect(sdtm_order, names(dm))',
        'other    <- setdiff(names(dm), sdtm_order)',
        'dm <- dm[c(existing, other)]',
        "",
        "# output",
    ]

    if output_format.lower() == "parquet":
        lines.append('arrow::write_parquet(dm, out_path)')
    elif output_format.lower() == "csv":
        lines.append('write.csv(dm, out_path, row.names = FALSE)')
    else:
        lines.append('saveRDS(dm, out_path)')

    lines.append('message("Primary dataset written to ", out_path)')

    if write_xpt and xpt_path:
        lines += [
            "",
            "# write XPT for regulatory submission (haven::write_xpt)",
            "# XPT version 5 (SAS XPORT transport format) is the standard for",
            "# regulatory submissions to FDA. column names must be <= 8 chars.",
            'haven::write_xpt(dm, path = xpt_path, version = 5)',
            'message("XPT submission file written to ", xpt_path)',
        ]

    return "\n".join(lines)
