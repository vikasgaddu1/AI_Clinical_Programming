################################################################################
# Function: derive_age
# Purpose: Calculate age in completed years from birth date and reference date
#
# Parameters:
#   data      - Data frame containing birth and reference date variables
#   brthdt    - Name of birth date variable (character, ISO YYYY-MM-DD)
#   refdt     - Name of reference date variable (character, ISO YYYY-MM-DD)
#   agevar    - Name of output age variable (default: "AGE")
#   ageuvar   - Name of output age unit variable (default: "AGEU")
#   create_ageu - Create AGEU column with value "YEARS"? (default: TRUE)
#
# Returns: Data frame with age (numeric) and optionally AGEU (character) added.
#          Missing dates produce NA for age. Birth date after reference date
#          produces NA and is treated as invalid.
#
# Usage:
#   dm <- derive_age(dm, brthdt = "BRTHDTC", refdt = "RFSTDTC")
#   dm <- derive_age(dm, brthdt = "BRTHDTC", refdt = "RFSTDTC", create_ageu = TRUE)
################################################################################

derive_age <- function(data, brthdt, refdt, agevar = "AGE", ageuvar = "AGEU",
                       create_ageu = TRUE) {
  if (missing(data) || is.null(data)) stop("data is required")
  if (missing(brthdt) || is.null(brthdt) || !brthdt %in% names(data))
    stop("brthdt is required and must be a column name in data")
  if (missing(refdt) || is.null(refdt) || !refdt %in% names(data))
    stop("refdt is required and must be a column name in data")

  b <- as.Date(data[[brthdt]], format = "%Y-%m-%d")
  r <- as.Date(data[[refdt]], format = "%Y-%m-%d")

  age_years <- integer(length(b))
  age_years[] <- NA_integer_

  for (i in seq_along(b)) {
    if (is.na(b[i]) || is.na(r[i])) next
    if (b[i] > r[i]) next  # invalid: birth after reference
    age_years[i] <- as.integer(floor(as.numeric(difftime(r[i], b[i], units = "days")) / 365.25))
  }

  data[[agevar]] <- age_years

  if (create_ageu) {
    data[[ageuvar]] <- ifelse(!is.na(data[[agevar]]), "YEARS", NA_character_)
  }

  data
}
