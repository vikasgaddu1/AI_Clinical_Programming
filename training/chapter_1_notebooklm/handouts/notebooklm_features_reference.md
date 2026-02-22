# NotebookLM Quick Reference for Clinical Programmers

## What It Is

Google NotebookLM is a source-grounded AI tool. It answers questions ONLY from documents you upload -- it does not draw from general internet training data. This makes it reliable for querying regulatory documents like protocols, SAPs, and the SDTM IG.

**URL:** https://notebooklm.google.com
**Cost:** Free with a Google account
**Model:** Google Gemini

---

## Features at a Glance

| Feature | What It Does | Clinical Programming Use |
|---------|-------------|------------------------|
| **Sources** | Upload PDFs, Docs, URLs, text | Protocol, SAP, SDTM IG, FDA guidance |
| **Audio Overview** | AI-generated podcast discussion | Get oriented on a new study or IG version |
| **Chat** | Ask questions, get cited answers | Look up specific IG rules, protocol details |
| **Citations** | Links each answer to source passages | Verify accuracy, trace back to original text |
| **Notes** | Save AI answers for later | Build a study summary or programming checklist |
| **Source Guide** | Auto-generated FAQ + outline per source | Quick overview of uploaded documents |
| **Sharing** | Share notebooks with team | Collaborative study onboarding |

---

## Source Limits

- Up to **50 sources** per notebook
- Up to **500,000 words** per source
- Supported formats: PDF, Google Docs, Google Slides, website URLs, YouTube, pasted text
- NOT supported as structured data: CSV, Excel data files, SAS datasets

---

## Useful Questions for Clinical Programming

### Protocol Review
- "What is the study design, phase, and indication?"
- "Describe the treatment arms and dosing schedule"
- "What are the inclusion and exclusion criteria?"
- "What demographics data is collected at screening?"

### SAP Review
- "What demographics variables are in the primary summary table?"
- "What subgroup analyses are planned?"
- "How is the analysis population defined?"

### SDTM IG Lookup
- "What are the required variables for the [domain] domain?"
- "What controlled terminology applies to [variable]?"
- "How should [variable] be derived?"
- "What are the valid values for RACE according to the IG?"

### Cross-Document
- "Does the SAP cover all IG-required DM variables?"
- "What ARM values should I use based on the protocol?"
- "Are there discrepancies between the protocol CRF and IG requirements?"

---

## Limitations

| Cannot Do | Use Instead |
|-----------|-------------|
| Process CSV/SAS data files | R, Python, Claude Code |
| Count subjects or compute frequencies | `/profile-data` skill (Chapter 2) |
| Write or execute R/SAS/Python code | Claude Code, Cursor (Chapter 2) |
| Connect to databases or APIs | RAG system (Chapter 3) |
| Search the live internet | Web search tools |
| Provide GxP-compliant audit trail | Validated systems |
| Make programming judgment calls | Human review (Capstone) |

---

## Tips

1. **One notebook per study** keeps sources organized and questions contextual
2. **Customize Audio Overviews** with a topic prompt (e.g., "Focus on the DM domain") for more relevant summaries
3. **Verify citations** -- always click the citation number to confirm the AI pulled from the right passage
4. **Save useful answers as Notes** to build a study reference document over time
5. **Check your company's data governance policy** before uploading proprietary documents to Google
