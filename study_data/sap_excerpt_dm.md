# Statistical Analysis Plan Excerpt - Demographics Domain (DM)

## Study Identification

| Field | Value |
|-------|-------|
| **Study ID** | XYZ-2026-001 |
| **Study Title** | A Phase III, Randomized, Double-Blind, Placebo-Controlled Study to Evaluate the Efficacy and Safety of Glucotrex 10mg in Patients with Type 2 Diabetes Mellitus |
| **SAP Version** | 1.0 |
| **SAP Date** | 15 JAN 2026 |
| **Sponsor** | Exemplar Pharmaceuticals, Inc. |
| **Analysis Planned for** | Efficacy and Safety |

---

## 1. Overview

This document outlines the statistical analysis plan for demographic and baseline characteristics data collected in Study XYZ-2026-001. Demographic data will be used to describe the enrolled population and assess balance between treatment groups. Demographic variables will also be used for subgroup analyses as specified in the primary SAP.

---

## 2. Analysis Populations

### 2.1 Randomized Population (RP)
**Definition**: All subjects who were randomized to study treatment, regardless of whether they received study medication.

**Use**: Analysis of demographic characteristics will be performed on the Randomized Population to characterize the enrolled study population and assess balance between treatment groups at baseline.

**Expected N**: Approximately 300 subjects
- Glucotrex 10mg: ~200 subjects
- Placebo: ~100 subjects

### 2.2 Safety Population (SP)
**Definition**: All subjects who received at least one dose of study medication.

**Use**: Safety analyses, including adverse event summaries stratified by baseline demographics, will be performed on the Safety Population.

### 2.3 Intent-to-Treat (ITT) Population
**Definition**: All randomized subjects regardless of protocol adherence or medication exposure.

**Use**: Primary efficacy analyses; demographic subgroup analyses will be performed within the ITT population.

### 2.4 Per Protocol (PP) Population
**Definition**: All randomized subjects who completed the study without major protocol deviations and had evaluable efficacy data.

**Use**: Sensitivity efficacy analyses; demographic subgroup analyses may be performed within the PP population as supplementary analyses.

---

## 3. Demographics and Baseline Characteristics Analysis Plan

### 3.1 Demographic Variables
The following demographic variables will be collected and analyzed:

| Variable | Definition | Unit/Categories | Assessment Timing |
|----------|-----------|-----------------|-------------------|
| **Age at Informed Consent** | Age calculated as (Date of Informed Consent - Date of Birth) in completed years | Years | Screening/Baseline |
| **Baseline Age** | Age at the time of randomization | Years | Baseline (Day 0) |
| **Sex** | Biological sex of the subject | Male, Female | Baseline |
| **Race** | Racial category as self-reported by subject | American Indian/Alaska Native, Asian, Black/African American, Native Hawaiian/Other Pacific Islander, White, Multiracial | Baseline |
| **Ethnicity** | Hispanic or Latino status | Hispanic/Latino, Not Hispanic/Latino, Unknown | Baseline |
| **Height** | Vertical body measurement | Centimeters | Baseline |
| **Weight** | Body mass | Kilograms | Baseline, Weeks 2, 6, 12, 18, 24, 28 |
| **Body Mass Index (BMI)** | Weight (kg) / Height (m)² | kg/m² | Calculated at Baseline and follow-up visits |

### 3.2 Derived Demographics Variables

The following variables will be derived from primary demographic data:

| Derived Variable | Definition | Categories |
|------------------|-----------|-----------|
| **Age Group** | Categorical age at baseline | 18-45 years, >45-65 years, >65-75 years |
| **Weight Category at Baseline** | Categorical baseline weight status | Overweight (BMI 20-29.9 kg/m²), Obese Class I (30.0-34.9), Obese Class II (35.0-39.9), Obese Class III (≥40) |
| **BMI Category at Baseline** | Categorical baseline BMI grouping | Normal/Overweight (<30 kg/m²), Obese (≥30 kg/m²) |
| **Baseline Weight Stratum** | Weight-based stratification variable | <80 kg, 80-100 kg, >100 kg |
| **Gender/Race Cross-tabulation** | Combination of sex and race for demographic description | All combinations of sex and race categories |

---

## 4. Summary Statistics for Demographic Variables

### 4.1 Continuous Demographic Variables

For continuous demographic variables (age, height, weight, BMI), the following summary statistics will be presented by treatment group and overall:

- **Count (N)**: Number of subjects with non-missing data
- **Missing (n, %)**: Number and percentage of subjects with missing data
- **Mean**: Arithmetic mean
- **Standard Deviation (SD)**: Sample standard deviation
- **Median**: 50th percentile
- **Minimum (Min)**: Minimum value
- **Maximum (Max)**: Maximum value
- **Range**: Max - Min
- **Quartiles**: 25th, 50th, and 75th percentiles
- **Interquartile Range (IQR)**: 75th percentile - 25th percentile

### 4.2 Categorical Demographic Variables

For categorical demographic variables (sex, race, ethnicity), the following summary statistics will be presented by treatment group and overall:

- **Count (N)**: Total number of subjects in the analysis group
- **n (%)**: Number and percentage of subjects in each category
- **Missing (n, %)**: Number and percentage of subjects with missing data

### 4.3 Statistical Comparisons Between Treatment Groups

Demographic characteristics will be compared between treatment groups to assess balance:

| Variable Type | Test Used | Purpose |
|---------------|-----------|---------|
| **Continuous** (Age, Height, Weight, BMI) | Two-sample t-test or Mann-Whitney U test* | Assess balance in baseline continuous variables |
| **Categorical** (Sex, Race, Ethnicity) | Chi-square test or Fisher's exact test** | Assess balance in baseline categorical variables |

*Mann-Whitney U test will be used if normality assumptions are violated.
**Fisher's exact test will be used if expected cell frequencies are <5.

**Note**: These comparisons are descriptive in nature and are intended to assess whether treatment groups are balanced. Formal hypothesis testing is not planned; p-values will be presented for descriptive purposes only. No adjustment for multiple comparisons will be made.

---

## 5. Handling of Missing Data

### 5.1 Missing Demographic Data

**Policy**: All demographic variables should have complete data for randomized subjects. Any missing demographic data will trigger a data query to the investigator site.

### 5.2 Missing Height Data

If baseline height is missing:
- A data query will be issued to the site
- If height remains unavailable after query resolution, BMI cannot be calculated for that subject
- The subject will be excluded from BMI-based analyses

### 5.3 Missing Weight Data

If baseline weight is missing:
- A data query will be issued to the site
- If baseline weight remains unavailable after query resolution, the subject will be excluded from analyses requiring baseline weight
- Missing follow-up weight measurements will not result in study discontinuation; subjects will be carried forward in other analyses

### 5.4 Missing Age Data

If date of birth or age is missing:
- A data query will be issued to the site
- Subjects without a valid age calculation cannot be included in the Randomized Population

### 5.5 Missing Sex, Race, Ethnicity

If sex, race, or ethnicity data are missing:
- A data query will be issued to the site
- Missing sex, race, or ethnicity will not exclude subjects from the analysis but will be included in summary tables as a separate category

### 5.6 Data Imputation

**No imputation** of missing demographic values will be performed. Analyses will be conducted using available data, with the number of subjects with non-missing data clearly displayed in all summary tables.

---

## 6. SDTM DM Domain Mapping Considerations

### 6.1 SDTM DM Domain Overview

The Demographics (DM) domain in the SDTM dataset will contain demographic characteristics collected for each subject. The DM domain is a special domain (single record per subject per visit category).

### 6.2 Key DM Variables

The following variables will be mapped to the SDTM DM domain:

| SDTM Variable | Description | Source | Data Type | Notes |
|---------------|-------------|--------|-----------|-------|
| **USUBJID** | Unique Subject Identifier | EDC/IWRS | Character | Format: [SITE]-[SUBJECT] |
| **SUBJID** | Subject Identifier | EDC/IWRS | Character | Site-specific ID assigned by site |
| **SITEID** | Site Identifier | EDC/IWRS | Character | Range: 101-106 |
| **AGE** | Age | Derived from DOB | Numeric | Calculated as (Visit Date - DOB) / 365.25, truncated to years |
| **AGEU** | Age Units | Constant | Character | Value: "YEARS" |
| **SEX** | Sex/Gender | EDC | Character | Values: "M" (Male), "F" (Female), "U" (Unknown) |
| **RACE** | Race | EDC | Character | Values per CDISC CT (C66731) |
| **ETHNIC** | Ethnicity | EDC | Character | Values: "HISPANIC OR LATINO", "NOT HISPANIC OR LATINO", "UNKNOWN" |
| **RFSTDTC** | Reference Start Date/Time | EDC | ISO 8601 datetime | Date of informed consent |
| **RFENDTC** | Reference End Date/Time | Derived | ISO 8601 datetime | Last known date subject was in study |
| **RFXSTDTC** | Study Drug Reference Start Date/Time | IWRS | ISO 8601 datetime | Date of first dose of study drug |
| **RFXENDTC** | Study Drug Reference End Date/Time | Derived | ISO 8601 datetime | Date of last dose of study drug or EOS visit |
| **RFICDTC** | Date Informed Consent Obtained | EDC | ISO 8601 date | Must be before RFXSTDTC |
| **DTHDTC** | Date of Death | EDC | ISO 8601 date | If applicable; otherwise null |
| **DTHFL** | Death Flag | Derived | Character | Values: "Y" (subject died during study), null (subject alive) |
| **VISIT** | Visit Name | EDC | Character | Examples: "Screening", "Baseline", "Week 2", "Week 6", etc. |
| **VISITNUM** | Visit Number | EDC | Numeric | Sequential numbering: 1=Screening, 2=Baseline, etc. |
| **VISITDY** | Planned Study Day of Visit | Derived | Numeric | Relative to baseline (Day 0) |
| **ARM** | Planned Arm/Cohort | IWRS | Character | Values: "Glucotrex 10mg QD", "Placebo" |
| **ARMCD** | Arm/Cohort Code | Derived | Character | Values: "GLUC10", "PLAC" |
| **ACTARM** | Actual Arm/Cohort | Derived | Character | Same as ARM (in double-blind study) |
| **ACTARMCD** | Actual Arm/Cohort Code | Derived | Character | Same as ARMCD (in double-blind study) |
| **COUNTRY** | Country | EDC | Character | Values: "USA" for all subjects |
| **REGION1** | Region 1 | EDC | Character | State abbreviations |
| **BRTHDTC** | Birth Date/Time | EDC | ISO 8601 date | Required for age calculation |
| **DMDY** | Study Day of Demographics Assessment | Derived | Numeric | Day relative to Baseline (Day 0) |

### 6.3 Vital Signs Related to DM

While vital signs (height, weight) are typically captured in the VS (Vital Signs) domain, baseline height and weight will also be referenced in DM domain analyses:

**Height** (from VS):
- Parameter code: "HEIGHT"
- Unit: "cm"
- Will be merged with DM for BMI calculation

**Weight** (from VS):
- Parameter code: "WEIGHT"
- Unit: "kg"
- Collected at Baseline and follow-up visits
- Will be merged with DM for BMI calculation and weight change analyses

### 6.4 DM Domain Quality Checks

The following quality checks will be performed on the DM domain data:

1. **Completeness**: All randomized subjects must have DM records
2. **Age Consistency**: AGE derived from BRTHDTC and reference date must be logical
3. **Sex Validity**: SEX must be "M", "F", or "U"
4. **Race Validity**: RACE must be a valid value per CDISC Controlled Terminology
5. **Ethnicity Validity**: ETHNIC must be a valid value
6. **Date Consistency**: RFICDTC ≤ RFXSTDTC ≤ RFENDTC
7. **Age Range**: AGE at baseline must be between 18 and 75 years (per inclusion criteria)
8. **Uniqueness**: One DM record per subject

---

## 7. Tables and Listings

### 7.1 Table 14.1.1: Demographics and Baseline Characteristics

**Title**: Demographic Characteristics and Baseline Characteristics - Randomized Population

**Description**: Summary of demographic and baseline characteristics by treatment group.

**Population**: Randomized Population (RP)

**Variables Displayed**:
- Age (years): n, mean, SD, median, min, max
- Age Group: n (%)
- Sex: n (%)
- Race: n (%) for each race category
- Ethnicity: n (%)
- Height (cm): n, mean, SD, median, min, max
- Weight (kg): n, mean, SD, median, min, max
- BMI (kg/m²): n, mean, SD, median, min, max
- BMI Category: n (%)

**Footnotes**:
- Age at informed consent, rounded to completed years
- P-value from t-test or Mann-Whitney U test for continuous variables (for reference only)
- P-value from chi-square or Fisher's exact test for categorical variables (for reference only)
- Missing data shown as n (%)

**Rows**: 
- Glucotrex 10mg Group
- Placebo Group
- Total

**Example Structure**:

```
                                    Glucotrex 10mg      Placebo        Total
                                      N=200             N=100          N=300
Age (years)
  N                                    200               100            300
  Mean (SD)                         54.2 (10.3)       53.8 (11.1)     54.1 (10.5)
  Median (Min, Max)                54 (23, 75)       53 (25, 74)     53 (23, 75)
  Missing, n (%)                       0                 0              0

Age Group, n (%)
  18-45 years                        42 (21.0)        24 (24.0)       66 (22.0)
  >45-65 years                       134 (67.0)       66 (66.0)       200 (66.7)
  >65-75 years                        24 (12.0)        10 (10.0)       34 (11.3)

Sex, n (%)
  Male                               112 (56.0)        58 (58.0)       170 (56.7)
  Female                              88 (44.0)        42 (42.0)       130 (43.3)

BMI (kg/m²)
  N                                    200               100            300
  Mean (SD)                         32.1 (4.8)        32.5 (4.9)      32.2 (4.8)
  Median (Min, Max)               31.8 (20.1, 44.9) 32.2 (20.4, 44.7) 31.9 (20.1, 44.9)
```

### 7.2 Table 14.1.2: Race and Ethnicity Distribution

**Title**: Race and Ethnicity Distribution by Treatment Group - Randomized Population

**Population**: Randomized Population (RP)

**Variables Displayed**:
- Race categories with counts and percentages
- Ethnicity categories with counts and percentages
- Combined race/ethnicity categories

**Rows**:
- American Indian/Alaska Native
- Asian
- Black or African American
- Native Hawaiian/Other Pacific Islander
- White
- Multiracial
- Unknown
- Ethnicity: Hispanic/Latino
- Ethnicity: Not Hispanic/Latino
- Ethnicity: Unknown

### 7.3 Table 14.1.3: Baseline Anthropometric Measurements

**Title**: Baseline Anthropometric Measurements by Treatment Group - Randomized Population

**Population**: Randomized Population (RP)

**Variables**:
- Height (cm)
- Weight (kg)
- BMI (kg/m²)

**Statistics by Group**: n, mean, SD, median, Q1, Q3, min, max

### 7.4 Listing 1: Subject Demographic Data

**Title**: Demographics Summary for All Randomized Subjects

**Population**: Randomized Population (RP)

**Columns**:
1. SUBJID
2. SITEID
3. Treatment Group
4. Date of Birth
5. Age at Informed Consent (years)
6. Sex
7. Race
8. Ethnicity
9. Baseline Height (cm)
10. Baseline Weight (kg)
11. Baseline BMI (kg/m²)
12. Age Group
13. BMI Category

**Sort Order**: By site, then by subject ID

---

## 8. Subgroup Analyses Based on Demographics

### 8.1 Subgroup Definitions

Demographic variables will be used to define subgroups for exploratory efficacy and safety analyses:

#### 8.1.1 Age-Based Subgroups
- **Subgroup A**: Ages 18-45 years (younger subjects)
- **Subgroup B**: Ages >45-65 years (middle-aged subjects)
- **Subgroup C**: Ages >65-75 years (older subjects)

**Rationale**: Age is a known factor affecting drug metabolism and efficacy in diabetes treatment.

#### 8.1.2 Sex-Based Subgroups
- **Subgroup M**: Male subjects
- **Subgroup F**: Female subjects

**Rationale**: Potential sex-based differences in metabolism, efficacy, and safety.

#### 8.1.3 BMI-Based Subgroups
- **Subgroup L**: BMI <30 kg/m² (non-obese)
- **Subgroup H**: BMI ≥30 kg/m² (obese)

**Alternative BMI categorization:
- **Subgroup L1**: BMI 20-29.9 kg/m² (normal/overweight)
- **Subgroup L2**: BMI 30.0-34.9 kg/m² (obese class I)
- **Subgroup L3**: BMI 35.0-39.9 kg/m² (obese class II)
- **Subgroup L4**: BMI ≥40 kg/m² (obese class III)

**Rationale**: BMI is a key factor in type 2 diabetes disease progression and treatment response.

#### 8.1.4 Race-Based Subgroups (if adequate sample sizes)
- Hispanic/Latino vs. Not Hispanic/Latino
- White vs. Non-White
- Individual race categories (if N ≥ 20 per treatment group)

**Rationale**: Potential differences in drug metabolism and efficacy across different racial/ethnic populations.

### 8.2 Subgroup Analysis Reporting

For each prespecified subgroup analysis:

1. **Primary Efficacy Outcome** (HbA1c change from baseline):
   - Mean change and SD by treatment group and subgroup
   - Treatment difference point estimate and 95% confidence interval
   - Number of subjects in each subgroup/treatment combination

2. **Safety Outcomes**:
   - Adverse event incidence by treatment group and subgroup
   - Serious adverse event incidence by treatment group and subgroup

3. **Interaction Testing**:
   - Formal statistical interaction tests between treatment and demographic variable will be noted if conducted
   - Emphasis will be on descriptive presentation of response by subgroup

### 8.3 Subgroup Analysis Presentation

Subgroup results will be presented in:
- Dedicated subgroup analysis tables
- Forest plots showing treatment effect across subgroups
- Appendix to the clinical study report

**Important Note**: Subgroup analyses are exploratory in nature and should be interpreted with caution. Statistical inference should not be drawn from small subgroups.

---

## 9. Data Modifications and Derivations

### 9.1 Age Derivation
```
AGE = INT((RFXSTDTC - BRTHDTC) / 365.25)

Where:
- AGE is rounded down to completed years
- RFXSTDTC is the date of first dose of study drug
- BRTHDTC is the date of birth
```

### 9.2 BMI Derivation
```
BMI = WEIGHT / (HEIGHT / 100)²

Where:
- WEIGHT is baseline weight in kilograms (from VS domain)
- HEIGHT is baseline height in centimeters (from VS domain)
- BMI is rounded to one decimal place (kg/m²)
```

### 9.3 Weight Change from Baseline
```
WT_CHG = WEIGHT_VISIT - WEIGHT_BASELINE
WT_PCT_CHG = ((WEIGHT_VISIT - WEIGHT_BASELINE) / WEIGHT_BASELINE) * 100

Where:
- WT_CHG is absolute weight change in kilograms
- WT_PCT_CHG is percent change from baseline
```

### 9.4 Age Groups
```
AGE_GRP = 
  '18-45'   if AGE >= 18 and AGE < 45
  '>45-65'  if AGE >= 45 and AGE <= 65
  '>65-75'  if AGE > 65 and AGE <= 75
```

### 9.5 BMI Categories
```
BMI_CAT =
  'Normal/Overweight' if BMI < 30.0
  'Obese Class I'     if BMI >= 30.0 and BMI < 35.0
  'Obese Class II'    if BMI >= 35.0 and BMI < 40.0
  'Obese Class III'   if BMI >= 40.0
```

---

## 10. Analysis Methods and Considerations

### 10.1 Descriptive Statistics
- Demographics will be summarized using descriptive statistics only
- No formal hypothesis testing is planned for demographic comparisons
- P-values will be provided for descriptive purposes only to assess baseline balance
- No adjustment for multiple comparisons will be made

### 10.2 Software and Tools
- Statistical analyses will be performed using SAS Version 9.4 or later
- SDTM datasets will be created in accordance with CDISC SDTM-IG v3.4 specifications
- Analysis datasets will be created from SDTM domains as specified in the ADaM specification

### 10.3 Rounding Rules
- Age: reported in completed years (integer)
- Height and Weight: reported to one decimal place
- BMI: reported to one decimal place
- Percentages: reported to one decimal place
- Standard Deviations and other statistics: reported to two decimal places

### 10.4 Consistency Checks
- Cross-validation of demographics data between EDC and IWRS systems
- Consistency of dates (DOB vs Age, visit dates vs study day calculations)
- Range checks for all numeric variables
- Valid value checks for all categorical variables

---

## 11. Documentation and QA/QC

### 11.1 SAS Programming Standards
All SAS programs for DM domain analysis will:
- Include detailed header comments with program purpose, author, date, and version
- Document all variable definitions and calculations
- Include validation checks and reasonableness tests
- Produce audit trails documenting data manipulation steps
- Conform to Good Programming Practice (GPP) standards

### 11.2 Quality Assurance
- All programs will be independently reviewed and tested
- Output tables will be compared to specifications and manual calculations
- SDTM DM datasets will be validated against source data
- Final SDTM datasets will be locked and archived per regulatory requirements

### 11.3 Change Control
- All changes to analysis methods or variable definitions will be documented
- Change logs will be maintained throughout the analysis phase
- Deviations from this SAP will be documented and justified

---

## 12. References

- FDA Guidance for Industry: Structure and Content of Clinical Study Reports (November 2018)
- ICH-GCP: Integrated Addendum to ICH E6(R1) (2015)
- CDISC: Study Data Tabulation Model Implementation Guide (SDTM-IG) v3.4
- CDISC: Analysis Data Model (ADaM) Implementation Guide v1.1
- 21 CFR Part 11: Electronic Records; Electronic Signatures

