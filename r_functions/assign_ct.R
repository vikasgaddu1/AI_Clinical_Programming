################################################################################
# Function: assign_ct
# Purpose: Map raw data values to CDISC Controlled Terminology
#
# Parameters:
#   data           - Data frame containing the raw categorical variable
#   invar          - Name of input variable with raw values (character or numeric)
#   outvar         - Name of output variable for CT-mapped values (character)
#   codelist       - CT codelist code (e.g. "C66731" for SEX, "C74457" for RACE)
#   ctpath         - Path to CT lookup CSV (default: ct_lookup.csv in same dir)
#   unmapped       - Action for unmapped values: "KEEP", "MISSING", or "FLAG" (default: "FLAG")
#   case_insensitive - Match raw values case-insensitively? (default: TRUE)
#
# Returns: Data frame with new column outvar (character) containing CT values.
#          Missing input yields missing output. Unmapped handled per unmapped.
#
# CT lookup file must have columns: CODELIST, RAW_VALUE, CT_VALUE
#
# Usage:
#   dm <- assign_ct(dm, invar = "SEX", outvar = "SEX", codelist = "C66731", ctpath = "ct_lookup.csv")
#   dm <- assign_ct(dm, invar = "RACE", outvar = "RACE", codelist = "C74457", unmapped = "MISSING")
################################################################################

assign_ct <- function(data, invar, outvar, codelist, ctpath = NULL,
                      unmapped = c("FLAG", "KEEP", "MISSING"),
                      case_insensitive = TRUE) {
  unmapped <- match.arg(unmapped)

  if (missing(data) || is.null(data)) stop("data is required")
  if (missing(invar) || !invar %in% names(data))
    stop("invar is required and must be a column name in data")
  if (missing(outvar)) stop("outvar is required")
  if (missing(codelist)) stop("codelist is required")

  if (is.null(ctpath)) {
    ctpath <- file.path(getOption("sdtm.ct_path", "."), "ct_lookup.csv")
  }
  if (!file.exists(ctpath)) {
    stop("CT lookup file does not exist: ", ctpath)
  }

  ct <- read.csv(ctpath, stringsAsFactors = FALSE)
  if (!all(c("CODELIST", "RAW_VALUE", "CT_VALUE") %in% names(ct))) {
    stop("CT lookup must have columns: CODELIST, RAW_VALUE, CT_VALUE")
  }

  sub <- ct[ct$CODELIST == codelist, c("RAW_VALUE", "CT_VALUE")]
  if (nrow(sub) == 0) {
    warning("Codelist ", codelist, " not found in CT lookup. All values treated as unmapped.")
  }

  raw_vals <- data[[invar]]
  raw_char <- trimws(as.character(raw_vals))
  out_vals <- character(length(raw_char))
  out_vals[] <- NA_character_

  for (i in seq_along(raw_char)) {
    if (is.na(raw_char[i]) || raw_char[i] == "") next

    key <- raw_char[i]
    key_compare <- if (case_insensitive) toupper(key) else key

    matched <- FALSE
    for (j in seq_len(nrow(sub))) {
      ref <- sub$RAW_VALUE[j]
      ref_compare <- if (case_insensitive) toupper(ref) else ref
      if (key_compare == ref_compare) {
        out_vals[i] <- sub$CT_VALUE[j]
        matched <- TRUE
        break
      }
    }

    if (!matched) {
      if (unmapped == "MISSING") {
        out_vals[i] <- NA_character_
      } else {
        out_vals[i] <- key
      }
      if (unmapped %in% c("FLAG", "KEEP")) {
        warning("Unmapped value in codelist ", codelist, ": ", key)
      }
    }
  }

  data[[outvar]] <- out_vals
  data
}
