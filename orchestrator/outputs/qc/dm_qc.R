# DM Production Program - Generated from approved mapping spec
# Spec: dm_mapping_spec_approved.json

# Load required packages
# Install once before running: install.packages(c("arrow", "haven"))
library(arrow)
library(haven)

# Source R function library
library_path <- "C:/Users/vikas/OneDrive/Documents/AI_Clinical_Programming/r_functions"
source(file.path(library_path, "iso_date.R"))
source(file.path(library_path, "derive_age.R"))
source(file.path(library_path, "assign_ct.R"))

ct_path  <- "C:/Users/vikas/OneDrive/Documents/AI_Clinical_Programming/macros/ct_lookup.csv"
raw_path <- "C:/Users/vikas/OneDrive/Documents/AI_Clinical_Programming/study_data/raw_dm.csv"
out_path <- "C:/Users/vikas/OneDrive/Documents/AI_Clinical_Programming/orchestrator/outputs/qc/dm_qc.parquet"

# Read raw data
raw_dm <- read.csv(raw_path, stringsAsFactors = FALSE)
dm <- raw_dm

# --- Date conversions (Spec: BRTHDT -> BRTHDTC, RFSTDTC) ---
# Variable: BRTHDTC - derived from raw BRTHDT
dm <- iso_date(dm, invar = "BRTHDT", outvar = "BRTHDTC")
# Variable: RFSTDTC - standardise to ISO 8601
dm <- iso_date(dm, invar = "RFSTDTC", outvar = "RFSTDTC")

# --- Age derivation (Spec: AGE, AGEU from BRTHDTC and RFSTDTC) ---
dm <- derive_age(dm, brthdt = "BRTHDTC", refdt = "RFSTDTC",
                  agevar = "AGE", ageuvar = "AGEU", create_ageu = TRUE)

# --- Controlled terminology (Spec: SEX, RACE, ETHNIC) ---
# Variable: SEX
# Spec Reference: dm_mapping_spec_approved, variable SEX
# Codelist: C66731 (Sex)
dm <- assign_ct(dm, invar = "SEX", outvar = "SEX", codelist = "C66731",
                ctpath = ct_path, unmapped = "FLAG")

# Variable: RACE
# Spec Reference: dm_mapping_spec_approved, variable RACE
# Codelist: C74457 (Race) - approach per human decision
dm <- assign_ct(dm, invar = "RACE", outvar = "RACE", codelist = "C74457",
                ctpath = ct_path, unmapped = "FLAG")

# Variable: ETHNIC
# Codelist: C66790 (Ethnicity)
dm <- assign_ct(dm, invar = "ETHNIC", outvar = "ETHNIC", codelist = "C66790",
                ctpath = ct_path, unmapped = "FLAG")

# --- Constants and derivations ---
dm$STUDYID <- "XYZ-2026-001"
dm$DOMAIN  <- "DM"
dm$USUBJID <- paste(dm$STUDYID, dm$SUBJID, sep = "-")

# Reorder to SDTM variable order (key variables first)
sdtm_order <- c("STUDYID", "DOMAIN", "USUBJID", "SUBJID",
                "RFSTDTC", "RFENDTC", "SITEID", "BRTHDTC",
                "AGE", "AGEU", "SEX", "RACE", "ETHNIC",
                "ARMCD", "ARM", "ACTARMCD", "ACTARM",
                "COUNTRY", "DMDTC", "DMDY")
existing <- intersect(sdtm_order, names(dm))
other    <- setdiff(names(dm), sdtm_order)
dm <- dm[c(existing, other)]

# --- Write primary output (Parquet) ---
arrow::write_parquet(dm, out_path)
message("Primary dataset written to ", out_path)