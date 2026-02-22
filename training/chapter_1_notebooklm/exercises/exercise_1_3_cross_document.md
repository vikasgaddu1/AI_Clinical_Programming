# Exercise 1.3: Cross-Document Analysis

## Objective
Use NotebookLM with multiple sources (protocol, SAP, SDTM IG) simultaneously to answer questions that span documents. Identify alignments and gaps between study-specific plans and SDTM requirements.

## Time: 15 minutes

## Prerequisites
- NotebookLM notebook with all 3 sources uploaded:
  - Protocol excerpt (`protocol_excerpt_dm.pdf`)
  - SAP excerpt (`sap_excerpt_dm.pdf`)
  - SDTM IG (`SDTMIG_v3.4.pdf`)

If you don't have all three in one notebook, add the missing sources now.

---

## Steps

### Step 1: Treatment Arm Mapping

Ask NotebookLM to bridge the protocol and the SDTM IG:

**Question:** "Based on the protocol's treatment arms and the SDTM IG's DM domain requirements, what values should ARMCD and ARM contain in the DM dataset?"

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Which sources did it cite? (protocol, IG, or both?)
> _________________________________________________________________

### Step 2: Demographics Coverage Check

Ask NotebookLM to compare the SAP's analysis plan against IG requirements:

**Question:** "Are there any demographics variables required by the SDTM IG for the DM domain that are NOT mentioned in the SAP's demographics analysis plan?"

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Were any gaps identified? List them:
> _________________________________________________________________

### Step 3: Race and Ethnicity Alignment

Ask about a specific mapping challenge that spans all three documents:

**Question:** "The protocol mentions race and ethnicity data collection. The SDTM IG defines RACE and ETHNIC variables with controlled terminology. What are the valid RACE values according to the IG, and does the protocol's race categories align with them?"

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Are there any categories in the protocol that do not directly map to IG-defined values?
> _________________________________________________________________

### Step 4: Identify a Programming Decision

Ask a question that requires judgment -- something NotebookLM can inform but cannot decide:

**Question:** "The SDTM IG shows multiple valid approaches for handling 'Other Specify' race values. What are these approaches, and which one does the protocol or SAP recommend?"

> Record the answer:
> _________________________________________________________________
> _________________________________________________________________
>
> Does the answer identify a clear recommendation, or is this a decision the programmer must make?
> _________________________________________________________________

### Step 5: Document Your Findings

Create a summary note in NotebookLM:

1. Save the most useful cross-document answer as a Note
2. Title it: **"DM Programming -- Cross-Document Findings"**

---

## Reflection Questions

1. When NotebookLM cites multiple sources in a single answer, how confident are you in the synthesis? Did it correctly integrate information across documents?
2. Did the cross-document analysis reveal anything you wouldn't have noticed reading each document separately?
3. For Question 4 (programming decision), did NotebookLM appropriately flag that this requires human judgment, or did it try to make the decision for you?

---

## What You Should Have at the End

- [ ] 4 cross-document questions asked with cited answers from multiple sources
- [ ] At least 1 gap or alignment issue identified between protocol/SAP and SDTM IG
- [ ] Understanding of where NotebookLM informs decisions vs. where human judgment is needed
- [ ] 1 summary note saved
