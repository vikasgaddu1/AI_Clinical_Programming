# SDTM IG: Demographics (DM) Domain

## DM Domain Overview and Purpose

The Demographics (DM) domain contains information identifying the study, the subject, and significant dates in the subject's participation in the study. The Demographics domain contains one record per subject with characteristics that are constant for the entire study. All subjects in the SDTM dataset must have at least one Demographics record.

The Demographics domain serves as the parent domain for all findings and events domains. Each record in other domains must be linkable to a Demographics record via the USUBJID variable.

Key characteristics of the DM domain:
- One record per subject (flat structure)
- Contains subject identifiers, demographics, and study timing information
- Required for linking all other domains
- ISO 8601 date format for all date variables
- No repeating measures (unlike other domains)

---

## Core DM Variables

### STUDYID - Study Identifier
**Format:** Character
**Controlled Terminology:** No (study-specific identifier)
**Requirement:** Required

The study identifier, which uniquely identifies the study. This is used to link all records within a study and across datasets.

**Assumptions:**
- Must match the STUDYID value in other domains
- Usually a fixed value for all subjects in a single study
- Case-sensitive in most systems
- Should be alphanumeric (no special characters recommended)

---

### DOMAIN - Domain Abbreviation
**Format:** Character
**Controlled Terminology:** Yes (fixed value: "DM")
**Requirement:** Required

The two-character domain abbreviation for Demographics.

**Value:** Always "DM" for Demographics records

---

### USUBJID - Unique Subject Identifier
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

A unique identifier for the subject that remains constant across the entire study, even if the subject is transferred between sites.

**Construction Rules:**
The USUBJID should be constructed to ensure uniqueness across the entire study. Common approaches:

1. **Site-Based Construction:** [STUDYID]-[SITE]-[SUBJECT NUMBER]
   - Example: ABC123-001-0001
   - Advantages: Human readable, easy to trace origins
   - Used when sites are responsible for subject numbering

2. **Sequential Construction:** [STUDYID]-[SEQUENTIAL NUMBER]
   - Example: ABC123-0001
   - Advantages: Global uniqueness guaranteed, simpler
   - Used for centrally-assigned subject numbers

3. **Derived Construction:** USUBJID derived from SITEID and SUBJID
   - Example: Concatenate STUDYID, SITEID, and SUBJID
   - Advantages: Maintains site information in identifier
   - Used when both site and local subject numbers are available

**Assumption:** Once a USUBJID is assigned, it should never change. If a subject changes sites, they retain the same USUBJID.

---

### SUBJID - Subject Identifier for Study
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

The subject number or identifier specific to the study site.

**Assumptions:**
- Must be unique within a site
- May be the same value at different sites (hence the need for USUBJID)
- Often used as the "local" identifier that subjects know
- When combined with SITEID, must be unique across the study

---

### RFSTDTC - Study Reference Start Date/Time
**Format:** ISO 8601 datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
**Controlled Terminology:** No
**Requirement:** Required (usually)

The date and time marking the beginning of the reference period for the subject, typically the date of informed consent or first dose, whichever is applicable.

**Multiple Valid Approaches for RFSTDTC Derivation:**

**Approach 1: Informed Consent Date (Preferred in many sponsors)**
- RFSTDTC = Date of written informed consent
- Applies when: Study requires informed consent before any study procedures
- Advantages: 
  - Most conservative definition of study start
  - Subjects enrolled before doses given
  - Protects subject rights
- Used for: Clinical trials with strict informed consent requirements

**Approach 2: First Dose Date (Alternate in some trials)**
- RFSTDTC = Date of first administration of study drug
- Applies when: First dose effectively marks study participation start
- Advantages:
  - Aligns with dosing timeline
  - Simpler for dose-tracking logic
  - Used in some oncology/early phase studies
- Used for: Studies where first dose is the critical enrollment event

**Approach 3: Earlier of Both Dates**
- RFSTDTC = MIN(Informed Consent Date, First Dose Date)
- Applies when: Wanting to capture earliest enrollment event
- Advantages:
  - Captures all study activities
  - Comprehensive reference period
- Used for: Studies with complex enrollment procedures

**IG Reference:** CDISC IG Section 2.3.1.1
**Recommendation:** Sponsors should document which approach is used and apply consistently for all subjects.

---

### RFENDTC - Study Reference End Date/Time
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Required (usually)

The date and time marking the end of the reference period for the subject. Usually the date of last dose or final visit.

**Multiple Valid Approaches for RFENDTC Derivation:**

**Approach 1: Last Dose Date**
- RFENDTC = Date of last study drug administration
- Most common approach in Phase II-IV trials

**Approach 2: Last Visit/Assessment Date**
- RFENDTC = Date of final study visit
- Used when: Last assessment marks study participation end

**Approach 3: Termination Date**
- RFENDTC = Date subject terminated from study
- Used for: Early termination scenarios

---

### RFXSTDTC - Date/Time of First Study Drug Administration
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Required (conditionally)

The date and time of first receipt of study medication/drug.

**Assumptions:**
- If subject never received study drug, this should be blank (not imputed)
- Should match the earliest date in the EX domain
- For studies with no drug intervention, may be missing for all subjects

---

### RFXENDTC - Date/Time of Last Study Drug Administration
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Required (conditionally)

The date and time of last receipt of study medication/drug.

**Assumptions:**
- If subject never received study drug, this should be blank
- Should match the latest date in the EX domain
- May differ from RFENDTC if post-treatment assessments occur

---

### RFICDTC - Date/Time of Informed Consent
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Required (usually)

The date and time the subject provided written informed consent.

**Assumptions:**
- Must precede or equal RFSTDTC in most studies
- Should match protocol-specified screening visit
- If multiple consent forms signed, typically the initial written IC

---

### RFPENDTC - Date/Time of End of Participation
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Conditional (required if different from RFENDTC)

The date and time the subject ended participation in the study.

**Assumptions:**
- Used to capture end of followup activities
- May be after RFENDTC if post-treatment followup occurs
- For discontinued subjects, may be early termination date

---

### DTHDTC - Date/Time of Death
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Conditional (only if subject died)

The date and time of subject death, if applicable.

**Assumptions:**
- Only populated if DTHFL = "Y"
- May be partial date (only month/year known) - use date imputation rules
- For ongoing studies, should not be populated for living subjects

**Date Imputation Rules for Partial Dates:**

When only partial death date information is available, the following imputation approaches are acceptable:

1. **Day Unknown, Month/Year Known**
   - Impute Day = 15 (middle of month)
   - DTHDTC = YYYY-MM-15
   - Example: Death in January 2020 → 2020-01-15
   - Rationale: Centers on month without being arbitrary

2. **Only Year Known, Month/Day Unknown**
   - Impute Month = 06, Day = 15 (middle of year)
   - DTHDTC = YYYY-06-15
   - Example: Death sometime in 2020 → 2020-06-15
   - Rationale: Represents middle of year
   - Alternative: Use protocol-specified imputation date

3. **Report Imputation Flag in SUPPDM**
   - When any imputation occurs, record in SUPPDM
   - QNAM = "DTHIMP" (or study-specific name)
   - QVAL = "D" (day), "DM" (day/month), or "Y" (year)
   - Allows post-hoc adjustment if needed

4. **Do Not Impute - Use Partial Format**
   - Some systems accept incomplete ISO 8601
   - DTHDTC = "2020-01" (month unknown)
   - DTHDTC = "2020" (day and month unknown)
   - Check system compatibility before using

**Recommendation:** Document imputation approach in analysis dataset specifications and Analysis Data Review.

---

### DTHFL - Subject Death Flag
**Format:** Character
**Controlled Terminology:** Yes (C66742 - Yes/No Flag)
**Requirement:** Required

Flag indicating whether the subject died during or after the study.

**Controlled Terminology Values:**
- "Y" = Subject died
- "N" = Subject did not die (or missing if unknown)

**Assumptions:**
- If DTHFL = "Y", DTHDTC should be populated (unless date unknown)
- If DTHDTC is populated, DTHFL must = "Y"
- Should reflect deaths up to data cut-off date
- Deaths after study end should still be captured if known

---

### SITEID - Study Site Identifier
**Format:** Character
**Controlled Terminology:** No (site-specific)
**Requirement:** Required

Unique identifier for the investigator site at which the subject was enrolled.

**Assumptions:**
- Must be unique identifier within the study
- Often numeric (001, 002, etc.) or alphanumeric
- Used with SUBJID to create unique subject identifiers
- Should match site list in trial master file

---

### INVID - Investigator Identifier
**Format:** Character
**Controlled Terminology:** No (site-specific)
**Requirement:** Conditional (if multiple investigators per site)

Identifier of the principal investigator at the site.

**Assumptions:**
- Only required if multiple investigators at same site
- Unique within a site
- Usually numeric code or initials
- Should match investigator list in trial master file

---

### INVNAM - Investigator Name
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Conditional

Name of the principal investigator.

**Assumptions:**
- Include as required by sponsor
- May be removed for regulatory submissions (privacy)
- Last name, First name format
- Should match protocol and site initiation documents

---

### BRTHDTC - Date/Time of Birth
**Format:** ISO 8601 date (YYYY-MM-DD) or partial
**Controlled Terminology:** No
**Requirement:** Conditional (usually required)

Subject's date of birth.

**Assumptions:**
- Often partial date (only YYYY-MM or YYYY)
- Should not appear on regulatory submissions for blinded trials
- Used to calculate AGE
- Day often imputed to 15 when unknown

---

### AGE - Age
**Format:** Numeric
**Controlled Terminology:** No
**Requirement:** Required (usually)

Age of the subject at RFSTDTC (reference start date).

**Derivation Rules:**
- Derived from BRTHDTC and RFSTDTC when possible
- Calculate as: INT((RFSTDTC - BRTHDTC) / 365.25)
- Or for partial dates: Use available precision
- Units should be specified in AGEU

**Assumptions:**
- Always reported in the units specified in AGEU (usually Years)
- Should be consistent with protocol eligibility criteria
- If BRTHDTC is partial, AGE may be approximate
- For subjects enrolled on/after 18th birthday, AGE typically >= 18

---

### AGEU - Age Units
**Format:** Character
**Controlled Terminology:** Yes (Common: YEARS, MONTHS, DAYS)
**Requirement:** Required (if AGE present)

Units of age measurement.

**Typical Values:**
- "YEARS" - Most common in clinical trials
- "MONTHS" - For pediatric studies
- "DAYS" - For neonatal/very young pediatric

**Assumption:** When AGE is present, AGEU must be specified.

---

### SEX - Sex
**Format:** Character
**Controlled Terminology:** Yes (CDISC C66742)
**Requirement:** Required (usually)

Biological sex of the subject.

**Controlled Terminology - CDISC C66742:**
- "M" = Male
- "F" = Female
- "U" = Unknown (if not determined)

**Multiple Valid Approaches for Sex Determination:**

**Approach 1: Direct Self-Report (Most Common)**
- Source: Subject self-identification at screening
- Used when: Standard demographic question asked
- Advantages: Respectful of subject's identification
- Timing: Usually captured at screening visit

**Approach 2: Source Document Review**
- Source: Medical record, inclusion/exclusion criteria
- Used when: Self-report not available or not asked
- Advantages: Objective source documentation
- Timing: During data review/source data verification

**Approach 3: Medical History**
- Source: Pregnancy test results, medical history
- Used when: Needed for reproductive toxicology context
- Advantages: Objective clinical indicator
- Note: May differ from self-identified sex

**IG Reference:** CDISC IG Section on DM Variables
**Recommendation:** Document sex determination method in Data Management Plan.

**Assumptions:**
- If only sex-specific procedures listed (e.g., hysterectomy), infer SEX appropriately
- Cannot be left blank unless truly unknown
- Should match protocol eligibility (e.g., "females of childbearing potential" implies F)
- Regulatory expectation: All enrolled subjects have documented SEX

---

### RACE - Race
**Format:** Character
**Controlled Terminology:** Yes (CDISC C74456 or similar)
**Requirement:** Conditional (as per protocol/region)

Racial or ethnic background of the subject.

**Controlled Terminology - Common Values:**
- "AMERICAN INDIAN OR ALASKA NATIVE"
- "ASIAN"
- "BLACK OR AFRICAN AMERICAN"
- "NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER"
- "WHITE"
- "MULTIPLE"

**Multiple Valid Approaches for Race Mapping:**

**Approach 1: Single Race Selection (Standard, When Subject Selects One)**
- RACE = Subject-selected single race value from controlled terminology
- Used when: Standard check-box selection, one race per subject
- Advantages: Clean data, easy analysis
- Assumptions: Subject willing to choose one race

**Approach 2: Multiple Races Collapsed to "MULTIPLE"**
- RACE = "MULTIPLE" when subject reports more than one race
- Supplemental Detail: Individual race values recorded in SUPPDM
  - Create multiple SUPPDM records with QNAM = "RACE1", "RACE2", etc.
  - Each QVAL = individual race reported
  - Example:
    ```
    SUPPDM Record 1: QNAM = "RACE1", QVAL = "WHITE"
    SUPPDM Record 2: QNAM = "RACE2", QVAL = "ASIAN"
    ```
- Used when: Study collects granular race data but needs single DM value
- Advantages: Preserves individual race information, maintains SDTM structure
- IG Reference: CDISC IG guidance on use of SUPPDM

**Approach 3: "Other Specify" with Reclassification**
- When source documents: "Other (Please Specify)" with text entry
- Reclassification Process:
  1. Review free-text entry
  2. Map to closest CDISC controlled terminology if possible
  3. If no good match, use "OTHER"
  4. Record original text in SUPPDM with QNAM = "RACESPEC"
  - Example: Subject entered "Hawaiian" → Map to "NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER"
  - Record "Hawaiian" in SUPPDM for audit trail
- Used when: CRF allows text-based race entry
- Advantages: Captures detailed information while using standard CT

**Recommendation:** For studies collecting detailed ethnicity (multiple races, specific ethnicities), use Approach 2 with SUPPDM supplemental qualifiers to preserve data richness while maintaining SDTM compliance.

---

### ETHNIC - Ethnicity
**Format:** Character
**Controlled Terminology:** Yes (CDISC C74457 or similar)
**Requirement:** Conditional (as per protocol/region)

Ethnic background of the subject.

**Controlled Terminology - Common Values:**
- "HISPANIC OR LATINO"
- "NOT HISPANIC OR LATINO"
- "UNKNOWN"

**Assumptions:**
- Independent of RACE variable
- Typically captures Hispanic/Latino status specifically
- May have different requirements by region (more required in US studies)
- Not required in some regions/studies

---

### ARMCD - Planned Arm Code
**Format:** Character
**Controlled Terminology:** Yes (Study-specific)
**Requirement:** Required

Coded values for the planned arm (treatment group) to which the subject was randomized or assigned per protocol.

**Assumptions:**
- Reflects protocol-specified treatment assignment
- Should not change even if subject has deviations
- Typically alphanumeric codes (e.g., "ARM1", "TRT1", "CTRL")
- All subjects should have same set of possible values
- Links to TA domain via ARMCD

---

### ARM - Planned Arm
**Format:** Character
**Controlled Terminology:** No (study-specific description)
**Requirement:** Required

Descriptive text for ARMCD (the planned arm description).

**Examples:**
- ARMCD = "TRT01" → ARM = "Placebo"
- ARMCD = "TRT02" → ARM = "Study Drug 50 mg QD"
- ARMCD = "CTRL" → ARM = "Active Control 10 mg BID"

**Assumptions:**
- Should be descriptive enough for report readability
- Usually includes dose, frequency, and duration information
- Multiple subjects can have same ARM value
- Should exactly match Treatment Assignment (TA) domain descriptions

---

### ACTARMCD - Actual Arm Code
**Format:** Character
**Controlled Terminology:** Yes (Study-specific)
**Requirement:** Conditional (if subject treatment deviates from plan)

The actual arm code for the treatment that the subject received (may differ from planned).

**Use Cases (When ACTARMCD ≠ ARMCD):**

1. **Cross-Over Study with Deviation**
   - Planned: ARMCD = "PER1", ARM = "Sequence A→B"
   - Actual: ACTARMCD = "PER2", ACTARM = "Sequence B→A"
   - Reason: Subject enrolled in wrong sequence due to enrollment error

2. **Dose Adjustment**
   - Planned: ARMCD = "HIGH", ARM = "High Dose 200 mg"
   - Actual: ACTARMCD = "LOW", ACTARM = "Low Dose 100 mg"
   - Reason: Toxicity requiring dose reduction

3. **Unblinded Treatment Switch**
   - Planned: ARMCD = "ARM1", ARM = "Placebo"
   - Actual: ACTARMCD = "ARM2", ACTARM = "Study Drug"
   - Reason: Emergency unblinding for safety

4. **Protocol Deviation (Non-Enrollment)**
   - Planned: ARMCD = "TRT1"
   - Actual: ACTARMCD = Blank (never received treatment)
   - Reason: Screen failure, never dosed

**Assumptions:**
- If subject never deviates, ACTARMCD can equal ARMCD
- Or, if no deviations exist, ACTARMCD may be missing for all subjects
- Document deviations in Medical Review or flag in dataset

---

### ACTARM - Actual Arm
**Format:** Character
**Controlled Terminology:** No (study-specific description)
**Requirement:** Conditional (with ACTARMCD)

Descriptive text for the actual arm (actual treatment received).

**Assumptions:**
- Required when ACTARMCD is populated
- Otherwise can be missing
- Corresponds to ACTARMCD the same way ARM corresponds to ARMCD

---

### COUNTRY - Country
**Format:** Character
**Controlled Terminology:** Yes (ISO 3166 two-letter country codes)
**Requirement:** Required (usually)

Country in which the subject was enrolled.

**Controlled Terminology - ISO 3166-1 Alpha-2 Codes:**
- "US" = United States
- "GB" = United Kingdom
- "DE" = Germany
- "JP" = Japan
- (etc. for all countries)

**Assumptions:**
- Use ISO 3166-1 Alpha-2 standard (two-letter codes)
- One country per subject
- If subject moves during study, use enrollment country
- Required for multi-country regulatory submissions

---

### DMDTC - Date/Time of Demographics Assessment
**Format:** ISO 8601 datetime
**Controlled Terminology:** No
**Requirement:** Conditional

Date and time demographics data was collected/assessed.

**Assumptions:**
- Usually screening or baseline date
- If missing, typically inferred from RFSTDTC
- Useful for auditing data collection timing

---

### DMDY - Study Day of Demographics Assessment
**Format:** Numeric
**Controlled Terminology:** No
**Requirement:** Conditional

Relative study day of the demographics assessment.

**Derivation:**
- Calculated as: (DMDTC - RFSTDTC) + 1
- Study Day 1 = RFSTDTC (reference start date)
- Can be negative if assessment before study start (e.g., screening)

**Assumptions:**
- Should be consistent with other Study Day variables
- Used for temporal analysis
- Numeric value, positive or negative

---

## Summary Table: DM Domain Variables

| Variable | Type | Format | Required | Controlled Terminology | Notes |
|----------|------|--------|----------|----------------------|-------|
| STUDYID | Char | Text | Req | No | Fixed for study |
| DOMAIN | Char | Text | Req | Yes | Always "DM" |
| USUBJID | Char | Text | Req | No | Unique per subject |
| SUBJID | Char | Text | Req | No | Site-specific |
| RFSTDTC | Date | ISO 8601 | Req | No | Multiple approaches |
| RFENDTC | Date | ISO 8601 | Req | No | Multiple approaches |
| RFXSTDTC | Date | ISO 8601 | Cond | No | Conditional |
| RFXENDTC | Date | ISO 8601 | Cond | No | Conditional |
| RFICDTC | Date | ISO 8601 | Req | No | IC date |
| RFPENDTC | Date | ISO 8601 | Cond | No | End of participation |
| DTHDTC | Date | ISO 8601 | Cond | No | Partial dates allowed |
| DTHFL | Char | Y/N | Req | Yes | Yes/No flag |
| SITEID | Char | Text | Req | No | Study site ID |
| INVID | Char | Text | Cond | No | Investigator ID |
| INVNAM | Char | Text | Cond | No | Investigator name |
| BRTHDTC | Date | ISO 8601 | Cond | No | Often partial |
| AGE | Num | Integer | Req | No | Derived from DOB |
| AGEU | Char | Text | Req | Yes | Usually YEARS |
| SEX | Char | Text | Req | Yes | M/F/U |
| RACE | Char | Text | Cond | Yes | Multiple approaches |
| ETHNIC | Char | Text | Cond | Yes | Hispanic/Latino |
| ARMCD | Char | Text | Req | Yes | Planned arm |
| ARM | Char | Text | Req | No | Arm description |
| ACTARMCD | Char | Text | Cond | Yes | Actual arm code |
| ACTARM | Char | Text | Cond | No | Actual arm desc |
| COUNTRY | Char | Text | Req | Yes | ISO 3166 code |
| DMDTC | Date | ISO 8601 | Cond | No | Assessment date |
| DMDY | Num | Integer | Cond | No | Study day |

---

## IG Cross-References

- CDISC IG: IG.G.2.1 Demographics (DM) Domain
- CDISC IG: IG.G.2.1.1 Demographics (DM) Variables
- CDISC IG: Section 2.3 Reference Variables
- CDISC SDTM: Section 4.0 Assumption

