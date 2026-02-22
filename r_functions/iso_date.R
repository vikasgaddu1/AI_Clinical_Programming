################################################################################
# Function: iso_date
# Purpose: Convert non-standard date values to ISO 8601 format (YYYY-MM-DD)
#
# Parameters:
#   data    - Data frame containing the raw date variable
#   invar   - Name of input variable (character) containing the date string
#   outvar  - Name of output variable for the ISO date (character, YYYY-MM-DD)
#   infmt   - (Optional) Specific input format hint: "DD-MON-YYYY", "MM/DD/YYYY",
#             "DD/MM/YYYY", "YYYY-MM-DD", or NULL for auto-detect
#
# AMBIGUITY WARNING:
#   When infmt is NULL (auto-detect) and a slash-separated date has both parts
#   <= 12 (e.g. "03/04/2020"), the function DEFAULTS TO MM/DD/YYYY (US format).
#   If your data uses DD/MM/YYYY, you MUST set infmt = "DD/MM/YYYY" to avoid
#   silent mis-parsing (e.g. 03/04/2020 → 2020-03-04 instead of 2020-04-03).
#
# Returns: Data frame with new column outvar added (character, YYYY-MM-DD).
#          Missing or invalid input produces NA in output.
#
# Usage:
#   dm <- iso_date(dm, invar = "BRTHDT", outvar = "BRTHDTC")
#   dm <- iso_date(dm, invar = "RFSTDTC", outvar = "RFSTDTC", infmt = "DD/MM/YYYY")
################################################################################

iso_date <- function(data, invar, outvar, infmt = NULL) {
  if (missing(data) || is.null(data)) stop("data is required")
  if (missing(invar) || is.null(invar) || !invar %in% names(data))
    stop("invar is required and must be a column name in data")
  if (missing(outvar) || is.null(outvar)) stop("outvar is required")

  x <- trimws(as.character(data[[invar]]))
  out <- character(length(x))
  out[] <- NA_character_

  for (i in seq_along(x)) {
    if (is.na(x[i]) || x[i] == "") next
    val <- x[i]
    parsed <- NULL

    if (!is.null(infmt)) {
      parsed <- try_parse_with_format(val, infmt)
    } else {
      parsed <- try_parse_auto(val)
    }

    if (!is.null(parsed)) {
      out[i] <- format(parsed, "%Y-%m-%d")
    }
  }

  data[[outvar]] <- out
  data
}


# Try parsing with a specific format hint
try_parse_with_format <- function(val, infmt) {
  val <- trimws(val)
  if (infmt == "DD-MON-YYYY" || infmt == "DDMONYYYY") {
    return(parse_dd_mon_yyyy(val))
  }
  if (infmt == "MM/DD/YYYY") {
    return(parse_mm_dd_yyyy(val))
  }
  if (infmt == "DD/MM/YYYY") {
    return(parse_dd_mm_yyyy(val))
  }
  if (infmt == "YYYY-MM-DD") {
    return(parse_iso(val))
  }
  try_parse_auto(val)
}


# Auto-detect format and parse
try_parse_auto <- function(val) {
  val <- trimws(val)
  val_upper <- toupper(val)

  # Already ISO (YYYY-MM-DD)
  if (grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", val)) {
    return(parse_iso(val))
  }

  # DD-MON-YYYY (e.g. 01-JAN-2020, 4-Sep-1954)
  if (grepl("^[0-9]{1,2}-[A-Z]{3}-[0-9]{4}$", val_upper)) {
    return(parse_dd_mon_yyyy(val))
  }

  # DDMONYYYY (e.g. 01JAN2020)
  if (grepl("^[0-9]{2}[A-Z]{3}[0-9]{4}$", val_upper)) {
    return(parse_dd_mon_yyyy(val))
  }

  # Slash-separated (MM/DD/YYYY or DD/MM/YYYY)
  if (grepl("^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$", val)) {
    parts <- strsplit(val, "/")[[1]]
    d <- as.integer(parts[1])
    m <- as.integer(parts[2])
    y <- as.integer(parts[3])
    if (d > 12) {
      return(parse_dd_mm_yyyy(val))
    }
    if (m > 12) {
      return(parse_mm_dd_yyyy(val))
    }
    # Both parts <= 12: ambiguous — default to MM/DD/YYYY with warning
    if (d <= 12 && m <= 12 && d != m) {
      warning("iso_date: ambiguous date '", val,
              "' — defaulting to MM/DD/YYYY. Use infmt to override.",
              call. = FALSE)
    }
    return(parse_mm_dd_yyyy(val))
  }

  NULL
}


parse_iso <- function(val) {
  tryCatch(
    as.Date(val, format = "%Y-%m-%d"),
    error = function(e) NULL
  )
}


parse_dd_mon_yyyy <- function(val) {
  val_upper <- toupper(trimws(val))
  # With hyphen: 01-JAN-2020 or 4-SEP-1954
  val_spaced <- gsub("-", " ", val_upper)
  out <- tryCatch(
    as.Date(val_spaced, format = "%d %b %Y"),
    error = function(e) NULL
  )
  if (!is.null(out)) return(out)
  out <- tryCatch(
    as.Date(val_spaced, format = "%e %b %Y"),
    error = function(e) NULL
  )
  if (!is.null(out)) return(out)
  # No separator: 01JAN2020
  if (grepl("^[0-9]{2}[A-Z]{3}[0-9]{4}$", val_upper)) {
    return(tryCatch(as.Date(val_upper, format = "%d%b%Y"), error = function(e) NULL))
  }
  NULL
}


parse_mm_dd_yyyy <- function(val) {
  tryCatch(
    as.Date(val, format = "%m/%d/%Y"),
    error = function(e) NULL
  )
}


parse_dd_mm_yyyy <- function(val) {
  tryCatch(
    as.Date(val, format = "%d/%m/%Y"),
    error = function(e) NULL
  )
}
