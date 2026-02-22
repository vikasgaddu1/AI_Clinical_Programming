# Exercise 3.4: Build an AE Domain Content File

## Objective
Create a new SDTM IG content file for the Adverse Events (AE) domain, following the DM domain structure. This demonstrates that extending the RAG system = adding a markdown file.

## Time: 40 minutes

---

## Background

The IG client currently only knows about DM because only `dm_domain.md` exists in `sdtm_ig_db/sdtm_ig_content/`. In Exercise 3.2, you saw that `ig.get_domain_variables("AE")` returned nothing.

Your task: create `ae_domain.md` so the IG client can answer AE questions.

---

## Steps

### Step 1: Study the DM Domain Structure

Open `sdtm_ig_db/sdtm_ig_content/dm_domain.md` and note the pattern:

```markdown
# SDTM IG: Demographics (DM) Domain

## DM Domain Overview and Purpose
[High-level description]

## Core DM Variables

### STUDYID - Study Identifier
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required
[Description and assumptions]

---

### DOMAIN - Domain Abbreviation
[...]

## DM Domain Variable Summary Table
| Variable | Label | Type | CT | Requirement |
```

Your AE file must follow this same pattern.

### Step 2: Create the AE Domain File

Create `sdtm_ig_db/sdtm_ig_content/ae_domain.md` with at minimum these 8 variables:

**Required variables:** STUDYID, DOMAIN, USUBJID, AESEQ, AETERM, AEDECOD, AESTDTC, AEENDTC

**Use this starter content and fill in the details:**

```markdown
# SDTM IG: Adverse Events (AE) Domain

## AE Domain Overview and Purpose

The Adverse Events (AE) domain captures information about adverse events
experienced by subjects during the study. Each record represents one
adverse event occurrence for one subject.

[Add 3-4 more sentences about the AE domain purpose]

---

## Core AE Variables

### STUDYID - Study Identifier
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

[Same as DM -- study identifier]

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

[Same construction rules as DM]

---

### AESEQ - Sequence Number
**Format:** Numeric
**Controlled Terminology:** No
**Requirement:** Required

[Describe: sequential number for each AE per subject, starting from 1]

---

### AETERM - Reported Term for the Adverse Event
**Format:** Character
**Controlled Terminology:** No
**Requirement:** Required

[Describe: verbatim term as reported by the investigator]

---

### AEDECOD - Dictionary-Derived Term
**Format:** Character
**Controlled Terminology:** Yes (MedDRA Preferred Term)
**Requirement:** Required

[Describe: standardized term from MedDRA coding]

---

### AESTDTC - Start Date/Time of Adverse Event
**Format:** Character (ISO 8601)
**Controlled Terminology:** No
**Requirement:** Expected

[Describe: ISO 8601 date, may be partial]

---

### AEENDTC - End Date/Time of Adverse Event
**Format:** Character (ISO 8601)
**Controlled Terminology:** No
**Requirement:** Expected

[Describe: ISO 8601 date, may be partial or missing if ongoing]
```

**Add at least 2 more variables of your choice from:**
- AESER (Serious Event, CT: C66742 NY)
- AESEV (Severity/Intensity, CT: C66769)
- AEREL (Causality, CT: C66742 NY)
- AEACN (Action Taken with Study Treatment)
- AEOUT (Outcome of Adverse Event, CT: C66768)

### Step 3: Add the Summary Table

At the end of your file, add:

```markdown
## AE Domain Variable Summary Table

| Variable | Label | Type | CT | Requirement |
|----------|-------|------|-----|-------------|
| STUDYID | Study Identifier | Char | No | Req |
| DOMAIN | Domain Abbreviation | Char | Yes | Req |
| [... fill in all your variables ...]
```

### Step 4: Test with the IG Client

```python
import sys
sys.path.insert(0, 'orchestrator')
from core.ig_client import IGClient

ig = IGClient()
ae_vars = ig.get_domain_variables("AE")
print(f"AE variables found: {len(ae_vars)}")
for var in ae_vars:
    print(f"  {var['name']:15s} {var.get('requirement', 'N/A')}")

# Test required variables
req = ig.get_required_variables("AE")
print(f"\nRequired AE variables: {req}")

# Test variable detail
detail = ig.get_variable_detail("AE", "AETERM")
print(f"\nAETERM detail: {detail[:300]}")
```

> How many AE variables did the IG client find? ___________
> Did `get_required_variables("AE")` return the correct list? Yes / No
> Did `get_variable_detail("AE", "AETERM")` return content? Yes / No

### Step 5: Reflect

> How long did it take to add a new domain to the system? ___________
>
> What else would need to change in the orchestrator to support AE?
> _________________________________________________________________
> (Hint: the orchestrator code itself doesn't need to change -- just the IG content)

---

## What You Should Have at the End

- [ ] `sdtm_ig_db/sdtm_ig_content/ae_domain.md` with 8+ variables
- [ ] Summary table at the end of the file
- [ ] Successfully tested with IGClient: get_domain_variables, get_required_variables, get_variable_detail
- [ ] Understanding that extending the system = adding a markdown file
