# SDTM General Assumptions and Rules

## Overview

This document contains cross-domain assumptions, rules, and guidelines that apply across all SDTM domains. These foundational principles guide mapping decisions when domain-specific rules don't fully address a scenario.

---

## ISO 8601 Date and Time Format Requirements

### Standard Format Specification

All date and datetime variables in SDTM follow ISO 8601 standard format:

**Date Format:** `YYYY-MM-DD`
- Year: 4-digit calendar year (e.g., 2023)
- Month: 2-digit month (01-12)
- Day: 2-digit day (01-31)

**Datetime Format:** `YYYY-MM-DDTHH:MM:SS`
- "T" is literal separator between date and time
- Hours: 00-23 (24-hour format, no AM/PM)
- Minutes: 00-59
- Seconds: 00-59

**Examples:**
- Date: 2023-06-15 (June 15, 2023)
- Datetime: 2023-06-15T14:30:45 (June 15, 2023 at 2:30:45 PM)
- Partial Date: 2023-06 (Month/Year only, day unknown)
- Year Only: 2023 (Day and month unknown)

### Requirements for SDTM

1. **Always Use Hyphens for Dates:** `2023-06-15`, not `20230615` or `2023/06/15`
2. **24-Hour Format for Times:** `14:30:45`, not `2:30:45 PM` or `14:30:45 PM`
3. **Zero-Pad All Components:** `2023-01-05`, not `2023-1-5`
4. **No Timezone Specification:** Use local time where study conducted
5. **No Fractional Seconds:** Use whole seconds only

### Handling Partial/Incomplete Dates

When only partial date information is available:

**Partial Date - Format Specification:**
```
Complete Date: 2023-06-15
Month/Year Known: 2023-06 (day unknown)
Year Only Known: 2023 (month and day unknown)
```

**Imputation Rules for Analysis:**
- Document imputation approach in Analysis Dataset Specifications
- Record actual vs. imputed in separate flags/SUPP domain when critical
- Common imputation rules (choose one, apply consistently):

**Option 1: Mid-Point Imputation**
- Day Unknown: Impute day = 15
- Month Unknown: Impute month = 06 (June, middle of year)
- Example: Death in January 2023, day unknown → 2023-01-15

**Option 2: Last Day of Period**
- Day Unknown: Impute day = last day of month (28, 29, 30, or 31)
- Month Unknown: Impute month = 12 (December, last month)
- Example: Death sometime in 2023, unknown → 2023-12-31

**Option 3: First Day of Period**
- Day Unknown: Impute day = 01
- Month Unknown: Impute month = 01 (January, first month)
- Example: Surgery in March 2023, day unknown → 2023-03-01

### Study Day Calculation (DMDY, AEDY, LVDY, etc.)

For all domains tracking study day:

**Formula:** `Study Day = (Event Date - Reference Start Date) + 1`

**Key Points:**
- RFSTDTC (Reference Start Date) is the baseline for Study Day 1
- Study Day 1 = RFSTDTC date
- Study Day 0 = Day before RFSTDTC (does not occur unless event before enrollment)
- Negative study days possible: Events before RFSTDTC (screening visits)
- Always round down to integer (no fractional days)

**Example:**
```
RFSTDTC = 2023-06-15 → Study Day 1
Event Date = 2023-06-16 → Study Day 2
Event Date = 2023-06-15 → Study Day 1
Event Date = 2023-06-14 (screening) → Study Day 0 or negative
```

---

## Character vs. Numeric Variable Rules

### Character Variables

Variables stored as character (text) strings:

**When to Use Character Format:**
- Categorical values (SEX = "M" or "F")
- Coded values (ARMCD = "ARM1")
- Identifiers (USUBJID, SITEID)
- Free-text entries (comments, descriptions)
- Variables that might have leading zeros (SITEID = "001")
- Values from controlled terminology

**Formatting Rules:**
- Left-aligned in database
- Trailing spaces should be trimmed
- Case sensitivity: Follow controlled terminology
  - Most CDISC CT: All UPPERCASE
  - Some CT (e.g., NCI codes): Mixed case or specific format
- Empty vs. NULL: Prefer NULL (empty string) for missing

**Example Variables:**
- DOMAIN = "DM" (character)
- SEX = "M" (character, not numeric)
- SITEID = "001" (character to preserve leading zero)

### Numeric Variables

Variables stored as numbers:

**When to Use Numeric Format:**
- Continuous measurements (AGE, LBSTRESN)
- Counts (number of events)
- Dosing amounts (EXDOSE)
- Laboratory values (LBSTRESN)
- Study day variables (DMDY, AEDY)

**Formatting Rules:**
- No special characters or text
- Use decimal point (.) for fractional values, not comma
- Negative numbers allowed for derived values
- NULL for missing values
- Scientific notation: Only if needed for very large/small values

**Example Variables:**
- AGE = 45 (numeric)
- LBSTRESN = 7.4 (numeric)
- EXDOSE = 100.5 (numeric)
- DMDY = -5 (numeric, negative for pre-enrollment event)

### Differences in Analysis vs. SDTM

Note: Some variables have different storage formats in SDTM vs. analysis datasets:
- SDTM: VISITNUM = 1, 2, 3 (numeric) → Analysis: VISIT = "Week 1", "Week 2" (character)
- SDTM: ARMCD = "ARM1" (character) → Analysis: Treatment = 1 (numeric for modeling)

Always follow SDTM specifications for Study Data Tabulation, then transform as needed for analysis.

---

## USUBJID (Unique Subject Identifier) Construction Rules

The USUBJID must be globally unique across the entire study and remain constant throughout subject's participation.

### Rule 1: Global Uniqueness

**Requirement:** No two subjects, across all sites and all study periods, can have the same USUBJID.

**Validation:**
```
SELECT USUBJID, COUNT(*)
FROM DM
GROUP BY USUBJID
HAVING COUNT(*) > 1;
-- Should return 0 rows (no duplicates)
```

### Rule 2: Consistency Over Time

**Requirement:** USUBJID assigned to a subject never changes.

**Scenario:** Subject transfers to different site mid-study
- Original USUBJID assigned at Site 1: "STUDY123-001-0045"
- After transfer to Site 2: Keep original USUBJID "STUDY123-001-0045"
- Do NOT reassign: "STUDY123-002-0045" (would break data integrity)

### Rule 3: Construction Approaches

**Approach A: Site-Based (Most Common)**
```
Format: STUDYID-SITEID-SUBJID
Example: ABC123-001-0015

Advantages:
- Preserves site origin information
- Human-readable
- Maintains hierarchical structure

Components:
- STUDYID: Fixed study identifier (e.g., "ABC123")
- SITEID: Site code (e.g., "001")
- SUBJID: Subject number at site (e.g., "0015")
```

**Approach B: Sequential (Most Robust)**
```
Format: STUDYID-SEQUENTIAL
Example: ABC123-0215

Advantages:
- Guaranteed globally unique
- No dependency on site assignment
- Simplest validation logic

Components:
- STUDYID: Fixed study identifier
- Sequence: Continuous number across all sites (00001 to 99999)
```

**Approach C: Derived from Separate Components**
```
Format: STUDYID+SITEID+SUBJID combined
Example: Concatenate values without delimiters

Advantages:
- Compact, alphanumeric
- Encodes multiple pieces of information

Note: Ensure no collision risk if using variable-length components
```

### Rule 4: Uniqueness Check Examples

**Scenario 1: Duplicate Subject Numbers Across Sites**
```
Site 001: SUBJID = 0001
Site 002: SUBJID = 0001
↓ Using Approach A (Site-Based):
Site 001: USUBJID = "STUDY-001-0001"
Site 002: USUBJID = "STUDY-002-0001"
✓ Globally unique (different SITEID component)
```

**Scenario 2: Subject Reassignment**
```
Subject enrolled at Site 001 → USUBJID = "STUDY-001-0050"
If transferred to Site 002 → USUBJID = "STUDY-001-0050" (unchanged)
Do NOT change to "STUDY-002-0050"
```

### Rule 5: Validation in EDC/Database

**At Data Entry:**
- EDC system should auto-generate USUBJID based on STUDYID + SITEID + SUBJID
- Prevent manual entry to avoid typos/duplicates

**At Data Review:**
- Check for duplicate USUBJIDs before locking database
- Flag any changes to USUBJID post-enrollment
- Audit trail should capture USUBJID assignment timestamp

---

## Controlled Terminology Application Rules

### Rule 1: Always Use CDISC Codelist When Available

**Hierarchy of Controlled Terminology Sources:**

1. **CDISC Codelists** (First Choice)
   - Published by Clinical Data Interchange Standards Consortium
   - Officially supported codelists
   - Include NCI codes for reference
   - Examples: SEX, RACE, ETHNIC, DTHFL

2. **Study-Specific Codelists** (When CDISC insufficient)
   - Study-designed values for study-specific categories
   - Must be documented in Study Data Reviewer's Guide
   - Examples: ARMCD, VISITCD, QNAM (in SUPP domains)

3. **Other Standards** (If neither CDISC nor study-specific apply)
   - ISO standards (e.g., ISO 3166 for country codes)
   - Standard medical coding (ICD-10, SNOMED CT, MedDRA)
   - Used for narrative fields (diagnoses, adverse events)

### Rule 2: Case Sensitivity

**CDISC Codelists:**
- Almost always UPPERCASE
- Example: SEX values are "M", "F", "U" (not "m", "f", "u")
- Exception: Some NCI codes use mixed case (e.g., "Millimeters of mercury")

**Study-Specific:**
- Follow study-specific documentation
- If not specified, recommend UPPERCASE for consistency

**Database/System Considerations:**
- PostgreSQL default: Case-sensitive
- Some systems: Case-insensitive matching
- Always store and validate with exact case from codelist

### Rule 3: Missing Data Representation

**Rule:** Do NOT use codelist value to represent missing data
- Do NOT use "UNKNOWN" or "U" for missing numeric age
- Do NOT use "NULL" as a codelist string value
- Use actual NULL/missing value in database

**Example:**
```
✗ WRONG: AGE = "UNKNOWN", AGEU = "YEARS"
✓ CORRECT: AGE = NULL, AGEU = NULL

✗ WRONG: SEX = "U" (unless "U" = "Unknown" is valid codelist value)
✓ CORRECT: SEX = NULL (if not known)
```

### Rule 4: Codelist Validation at Data Entry

**Process:**
1. At data entry (EDC): Dropdown list enforces valid codelists
2. At data review: Compare against published codelist
3. At final validation: Flag any values not in codelist

**Out-of-Range Values:**
- Medical review needed if free-text entry created new value
- Map to appropriate codelist value if possible
- Document exceptions in data review comments

### Rule 5: Codelist Version Control

**Requirement:** Document codelist version used for study

**Example:**
```
SEX Codelist (CDISC C66742):
- Version 2023-06-15: "M", "F", "U"
- Version 2024-01-20: "M", "F", "U", "Other" (added)
```

**For Studies:**
- Reference specific CDISC IG version in protocol (e.g., "CDISC IG v3.4")
- Clarify if using older/newer codelists than IG version
- Lock codelists before study enrollment (no mid-study changes)

---

## Handling of Missing Data

### Rule 1: NULL vs. Empty String vs. Special Codes

**SDTM Standard:**
- Use NULL (database NULL value) for missing data
- Do NOT use empty string ""
- Do NOT use "-" or "." or "N/A" as missing indicators

**Example:**
```
✓ CORRECT: BRTHDTC = NULL (missing birth date)
✗ WRONG: BRTHDTC = "" (empty string)
✗ WRONG: BRTHDTC = "-" or "." (special character)
```

### Rule 2: Partial vs. Missing

**Partial Date (Not Missing):**
- Known component: Store with precision available
- DTHDTC = "2023-06" (month/year known, day unknown)
- DTHDTC = "2023" (year known only)

**Missing Date (Completely Unknown):**
- DTHDTC = NULL (no date information known)

### Rule 3: Not Applicable vs. Missing

**Not Applicable (--FL = "N" for flag variables):**
- Used when condition does not apply to subject
- Example: DTHFL = "N" → Subject did not die (not missing, just not applicable)

**Missing (--FL = NULL):**
- Used when applicability unknown
- Example: DTHFL = NULL → Whether subject died is unknown

### Rule 4: Variable-Level Missing Indicators (SUPP Domain)

For critical variables where you need to track reason for missing:

**Use SUPP Domain with QNAM:**
```
SUPPDM Record:
QNAM = "BRTHDTC_IND"  -- Missing indicator qualifier
QVAL = "UNKNOWN"      -- Reason: Age/DOB unknown
```

**Common Missing Reasons:**
- "UNKNOWN" - Information never provided
- "NOT_COLLECTED" - Not collected per protocol
- "REFUSED" - Subject refused to provide
- "WITHDRAWN" - Data withdrawn at subject request

### Rule 5: Numeric Missing Data

**For Numeric Variables:**
- Use NULL, do NOT use 0 or 999
- NULL is the only representation

**Example:**
```
✓ AGE = NULL (age not collected)
✗ AGE = 0 (age is not zero, it's missing!)
✗ AGE = 999 (placeholder; not standard SDTM)
```

---

## Cross-Domain Linking and Referential Integrity

### Rule 1: Parent-Child Domain Relationship

**DM Domain (Parent):**
- One record per subject
- Contains subject identifiers and demographics

**Other Domains (Children):**
- Multiple records per subject possible
- Must link to exactly one DM record via USUBJID

**Validation:**
```
SELECT DISTINCT USUBJID
FROM AE
WHERE USUBJID NOT IN (SELECT USUBJID FROM DM);
-- Should return 0 rows (all AE subjects in DM)
```

### Rule 2: Domain Key Variables

Each domain has a unique key (combination of variables that uniquely identifies each record):

**DM Domain Key:** STUDYID + USUBJID
- Must be unique combination

**AE Domain Key:** STUDYID + USUBJID + AESEQ
- Multiple AE records per subject, each with unique sequence number

**LB Domain Key:** STUDYID + USUBJID + LBSEQ
- Multiple test records per subject

### Rule 3: Sequence Numbers

**Rule:** Each domain with multiple records per subject must have --SEQ variable

**Requirements:**
- Numeric values: 1, 2, 3, ... (contiguous, no gaps)
- Sequential order: Usually chronological order of events
- Unique within subject per domain

**Example:**
```
Subject ABC-001:
  AESEQ 1: First adverse event
  AESEQ 2: Second adverse event
  AESEQ 3: Third adverse event
(No AESEQ = 5 without 4)
```

---

## Reference Variables (RF--) Rules

All RF-- variables (RFSTDTC, RFENDTC, RFXSTDTC, etc.) follow consistent rules:

### Rule 1: Study Reference Concept

The "Reference Period" (RP) is defined once per subject in DM domain:
- Starts: RFSTDTC (study start date)
- Ends: RFENDTC (study end date)
- All other domains' temporal relationships reference this period

### Rule 2: Consistency Within Subject

**Requirement:** All RF-- variables for same subject must use same reference concept

**Example:**
```
Subject ABC-001:
RFSTDTC = 2023-06-15 (informed consent)
RFXSTDTC = 2023-06-16 (first dose) ✓ Consistent reference frame
RFENDTC = 2023-12-01 (last dose)

If you used informed consent as RFSTDTC reference, 
DO NOT switch to screening date for RFXSTDTC
```

### Rule 3: Relationship Between RF-- Variables

Expected relationships (logical constraints):

```
RFICDTC ≤ RFSTDTC (IC before or on study start)
RFSTDTC ≤ RFXSTDTC (Study start before or on first dose)
RFXSTDTC ≤ RFXENDTC (First dose before or on last dose)
RFXENDTC ≤ RFENDTC (Last dose before or on study end)
RFENDTC ≤ RFPENDTC (Study end before or on end of participation)
```

**Exceptions documented:** Clearly identify and explain if relationships violated

---

## Assumptions vs. Derived Variables

### Rule 1: Assumptions in SDTM

**SDTM assumes facts about source data:**
- Example: "RACE is reported by subject, not derived"
- These assumptions are documented in IG

**Do NOT:**
- Derive values that should come from source data
- Assume values when data not available

**Do:**
- Follow documentation exactly as stated in IG
- Apply rules consistently across study

### Rule 2: Derived vs. Source Variables

**Source Variables:** Come directly from source documents
- No transformation beyond format conversion
- Example: SEX (from informed consent form)

**Derived Variables:** Calculated/transformed from source
- Example: DMDY = (DMDTC - RFSTDTC) + 1 (calculated)
- Example: AGE = INT((RFSTDTC - BRTHDTC) / 365.25) (calculated)

**Documentation:** Always document derivation logic
- Formula for numeric derived values
- Decision rules for categorical derivations

---

## Domain-Specific Exceptions to General Rules

While these general rules apply across SDTM, some domains have exceptions:

| Rule | Typical Application | Domain Exceptions |
|------|------------------|-------------------|
| ISO 8601 dates | All domains | None (universal) |
| Character codelists | All categorical | None (universal) |
| USUBJID linking | All domains | None (required everywhere) |
| Sequence numbers | Multi-record domains | QS (can have multiple per visit) |
| RF-- variables | All domains | Some use VISIT instead of dates |

---

## IG Cross-References and Further Reading

- CDISC IG: Section 1.0 Introduction (defines SDTM scope)
- CDISC IG: Section 2.1 General Assumptions
- CDISC IG: Section 2.2 General Variable Rules
- CDISC IG: Section 2.3 Reference Variables
- CDISC IG: Appendix C (Controlled Terminology)
- CDISC SDTM v1.7: Section 4.0 General Assumptions
- CDISC Glossary: https://www.cdisc.org/standards/foundational/glossary

