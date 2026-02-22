# SDTM IG: Adverse Events (AE) Domain

## AE Domain Overview and Purpose

The Adverse Events (AE) domain captures information about adverse events experienced by subjects during the course of a clinical study. Each record represents one adverse event occurrence for one subject. A subject may have multiple records if they experience multiple adverse events.

The AE domain is one of the most critical domains for safety analysis and regulatory review. It captures the reported adverse event term, the coded (dictionary-derived) term, dates of onset and resolution, severity, seriousness criteria, relationship to study treatment, and actions taken.

Key characteristics of the AE domain:
- Multiple records per subject (one per adverse event)
- Uses MedDRA for dictionary coding (AEDECOD = Preferred Term, AEBODSYS = System Organ Class)
- Date variables follow ISO 8601 format
- Controlled terminology for severity, seriousness, causality, outcome, and action taken
- Links to DM domain via USUBJID

---

## Core AE Variables

### STUDYID - Study Identifier
**Format:** Character
**Controlled Terminology:** No (study-specific identifier)
**Requirement:** Required

The study identifier, which uniquely identifies the study. Must match the STUDYID value in the DM domain and all other domains.

**Assumptions:**
- Same value for all records in the study
- Must be consistent across all domains

---

### DOMAIN - Domain Abbreviation
**Format:** Character
**Controlled Terminology:** Yes (fixed value: "AE")
**Requirement:** Required

The two-character domain abbreviation for Adverse Events.

**Value:** Always "AE" for Adverse Event records.

---

### USUBJID - Unique Subject Identifier
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

A unique identifier for the subject. Must match the USUBJID in the DM domain to enable linking between domains.

**Construction Rules:**
Same as DM domain: typically [STUDYID]-[SITEID]-[SUBJID] or as defined by the sponsor.

---

### AESEQ - Sequence Number
**Format:** Numeric
**Controlled Terminology:** No
**Requirement:** Required

A sequence number assigned to each adverse event record for a given subject. Used to ensure unique identification of each record within the domain for a subject.

**Assumptions:**
- Sequential starting from 1 for each subject
- Must be unique within USUBJID
- Typically assigned in chronological order by onset date (AESTDTC)
- If two events have the same onset date, ordering is at the sponsor's discretion

---

### AETERM - Reported Term for the Adverse Event
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

The verbatim term for the adverse event as reported by the investigator. This is the original, unmodified text from the CRF.

**Assumptions:**
- Captured as reported -- do not modify or correct the investigator's original text
- May include abbreviations, misspellings, or non-standard medical terminology
- The dictionary-coded version appears in AEDECOD
- Case should be preserved as entered

---

### AEDECOD - Dictionary-Derived Term
**Format:** Character
**Controlled Terminology:** Yes (MedDRA Preferred Term)
**Requirement:** Required

The dictionary-derived text description of the adverse event. Typically the MedDRA Preferred Term (PT) obtained by coding AETERM.

**Assumptions:**
- Coded using MedDRA (Medical Dictionary for Regulatory Activities)
- Represents the Preferred Term (PT) level of the MedDRA hierarchy
- The System Organ Class (SOC) is typically stored in AEBODSYS
- Coding should follow the sponsor's MedDRA coding conventions
- Version of MedDRA used should be documented in the define.xml

---

### AESTDTC - Start Date/Time of Adverse Event
**Format:** Character (ISO 8601)
**Controlled Terminology:** No
**Requirement:** Expected

The start date/time of the adverse event in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss).

**Assumptions:**
- May be partial (YYYY-MM or YYYY) if the exact start date is unknown
- Partial date imputation rules should be documented in the spec and define.xml
- For ongoing events that started before the study, the best available date should be used
- The date imputation method should be consistent with the approach used in other domains

**Multiple Valid Approaches for Partial Dates:**
1. **Approach A:** Impute missing day to 01 (first of month) -- conservative
2. **Approach B:** Impute missing day to 15 (midpoint) -- reduces bias
3. **Approach C:** Leave as partial (YYYY-MM) -- preserves original precision

---

### AEENDTC - End Date/Time of Adverse Event
**Format:** Character (ISO 8601)
**Controlled Terminology:** No
**Requirement:** Expected

The end date/time of the adverse event in ISO 8601 format.

**Assumptions:**
- Null/missing if the event is ongoing at the end of the study
- Same partial date handling rules as AESTDTC
- Must be >= AESTDTC when both are non-null
- For events that resolve and recur, each episode should be a separate record

---

### AESER - Serious Event
**Format:** Character
**Controlled Terminology:** Yes (C66742: No Yes Response)
**Requirement:** Expected

Indicates whether the adverse event met the criteria for a serious adverse event (SAE).

**Controlled Terms:** Y, N

**Seriousness Criteria (per ICH E2A):**
- Results in death
- Is life-threatening
- Requires inpatient hospitalization or prolongation of existing hospitalization
- Results in persistent or significant disability/incapacity
- Is a congenital anomaly/birth defect
- Is an important medical event

---

### AESEV - Severity/Intensity
**Format:** Character
**Controlled Terminology:** Yes (C66769: Severity/Intensity Scale for Adverse Events)
**Requirement:** Expected

The severity or intensity of the adverse event.

**Controlled Terms:** MILD, MODERATE, SEVERE

**Assumptions:**
- Severity is NOT the same as seriousness (a mild event can be serious)
- Some studies use toxicity grading (Grade 1-5) instead of or in addition to severity
- If toxicity grading is used, AETOXGR should be populated

---

### AEREL - Causality
**Format:** Character
**Controlled Terminology:** Yes (C66742: No Yes Response)
**Requirement:** Expected

The investigator's assessment of the causal relationship between the adverse event and the study treatment.

**Controlled Terms:** Y, N (Related, Not Related)

**Assumptions:**
- Represents the investigator's judgment, not a statistical determination
- Some protocols use a more granular scale (Unrelated, Unlikely, Possible, Probable, Definite) -- these should be mapped to Y/N per sponsor conventions
- If multiple treatments are given, causality may need to be assessed per treatment

---

### AEOUT - Outcome of Adverse Event
**Format:** Character
**Controlled Terminology:** Yes (C66768: Outcome of Event)
**Requirement:** Expected

The outcome or status of the adverse event at the last assessment.

**Controlled Terms:**
- RECOVERED/RESOLVED
- RECOVERING/RESOLVING
- NOT RECOVERED/NOT RESOLVED
- RECOVERED/RESOLVED WITH SEQUELAE
- FATAL
- UNKNOWN

---

## AE Domain Variable Summary Table

| Variable | Label | Type | CT | Requirement |
|----------|-------|------|-----|-------------|
| STUDYID | Study Identifier | Char | No | Req |
| DOMAIN | Domain Abbreviation | Char | Yes | Req |
| USUBJID | Unique Subject Identifier | Char | No | Req |
| AESEQ | Sequence Number | Num | No | Req |
| AETERM | Reported Term for the Adverse Event | Char | No | Req |
| AEDECOD | Dictionary-Derived Term | Char | Yes (MedDRA PT) | Req |
| AESTDTC | Start Date/Time of Adverse Event | Char | No | Exp |
| AEENDTC | End Date/Time of Adverse Event | Char | No | Exp |
| AESER | Serious Event | Char | Yes (C66742) | Exp |
| AESEV | Severity/Intensity | Char | Yes (C66769) | Exp |
| AEREL | Causality | Char | Yes (C66742) | Exp |
| AEOUT | Outcome of Adverse Event | Char | Yes (C66768) | Exp |
