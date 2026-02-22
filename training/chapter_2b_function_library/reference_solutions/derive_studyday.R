################################################################################
# Function: derive_studyday
# Purpose:  Calculate study day from event date and reference date (RFSTDTC)
#
# Parameters:
#   data    - Data frame with event and reference dates (ISO YYYY-MM-DD)
#   evtdt   - Name of the event date variable (character, ISO format)
#   refdt   - Name of the reference date variable (character, ISO format)
#   outvar  - Name of the output study day variable (default: "STUDYDAY")
#
# Returns: Data frame with outvar added (numeric integer).
#
# SDTM Rules:
#   event_date >= reference_date:  study_day = (event - ref) + 1   (Day 1 onward)
#   event_date <  reference_date:  study_day = (event - ref)       (Day -1 backward)
#   There is NO Day 0 in SDTM.
#   Missing event or reference date:  study_day = NA
#
# Usage:
#   dm <- derive_studyday(dm, evtdt = "DMDTC", refdt = "RFSTDTC", outvar = "DMDY")
#   ae <- derive_studyday(ae, evtdt = "AESTDTC", refdt = "RFSTDTC", outvar = "AESTDY")
################################################################################

derive_studyday <- function(data, evtdt, refdt, outvar = "STUDYDAY") {
  if (missing(data) || is.null(data)) stop("data is required")
  if (missing(evtdt) || is.null(evtdt) || !evtdt %in% names(data))
    stop("evtdt is required and must be a column name in data")
  if (missing(refdt) || is.null(refdt) || !refdt %in% names(data))
    stop("refdt is required and must be a column name in data")
  if (missing(outvar) || is.null(outvar)) stop("outvar is required")

  evt_dates <- as.Date(data[[evtdt]], format = "%Y-%m-%d")
  ref_dates <- as.Date(data[[refdt]], format = "%Y-%m-%d")

  diff_days <- as.integer(difftime(evt_dates, ref_dates, units = "days"))

  # Apply the no-Day-0 rule:
  # If diff >= 0 (same day or after), add 1 (Day 1 is the reference date itself)
  # If diff < 0 (before reference), keep as-is (Day -1 is the day before reference)
  study_day <- ifelse(is.na(diff_days), NA_integer_,
                      ifelse(diff_days >= 0, diff_days + 1L, diff_days))

  data[[outvar]] <- study_day
  data
}
