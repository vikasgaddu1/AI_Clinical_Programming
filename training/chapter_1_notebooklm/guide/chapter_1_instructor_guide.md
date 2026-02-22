# Chapter 1: Google NotebookLM for Clinical Programming -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 2-3 hours |
| Format | Instructor-led workshop (live demos + guided exercises) |
| Audience | Clinical programmers (SAS/R background, new to AI tools) |
| Prerequisites | Google account, Chrome browser |
| Materials | Protocol excerpt PDF, SAP excerpt PDF, SDTM IG PDF (all in `study_data/` and `docs/`) |

## Key Teaching Message

NotebookLM is the safest entry point for clinical programmers to start using AI. It only answers from documents you upload -- it will not hallucinate regulatory content from its training data. This "source grounding" is the same principle behind the RAG system we build in Chapter 3 and the orchestrator agents in the Capstone.

---

## Module 1.1: What is NotebookLM? (20 min)

### Talking Points

1. **Open with a relatable scenario:**
   "You've just been assigned to a new study. You have a 200-page protocol, a 50-page SAP, and the SDTM IG. Your first task is to understand the study design, the demographics CRF, and which SDTM variables you need. How long does that take you today?"

2. **Introduce NotebookLM:**
   - Google's AI notebook tool, free with a Google account
   - URL: https://notebooklm.google.com
   - Built on Google's Gemini model
   - Core concept: **source-grounded AI** -- the AI ONLY answers from documents you upload

3. **Why source grounding matters for pharma:**
   - Regulatory submissions require precision -- you cannot afford an AI making up codelist values
   - General ChatGPT/Claude chat sessions draw from training data that may include outdated IG versions, mixed guidance, or incorrect interpretations
   - NotebookLM constrains itself to YOUR documents -- if the answer isn't in the uploaded source, it says so

4. **What it is NOT:**
   - Not a data processing tool (cannot read CSV files or run code)
   - Not a replacement for clinical judgment
   - Not GxP-validated (no audit trail beyond saved notes)

### Live Demo (5 min)

1. Open https://notebooklm.google.com
2. Click "New Notebook"
3. Name it "Demo -- Protocol Review"
4. Upload `study_data/protocol_excerpt_dm.pdf`
5. Wait for processing (30-60 seconds)
6. Point out the auto-generated **Source Guide** (summary, FAQ, outline)
7. In the chat, ask: "What is the study design and what are the treatment arms?"
8. Show the **citation** -- click the citation number to see the exact source passage
9. Ask: "What is the primary endpoint?" -- show another cited answer

### Transition
"Now that you've seen the basics, let's look at all the features in detail."

---

## Module 1.2: Features Deep Dive (30 min)

### Talking Points

Walk through each feature with a live demo. Keep the protocol notebook open.

#### Sources
- Supported formats: PDF, Google Docs, Google Slides, website URLs, YouTube videos, copied text
- Limits: up to 50 sources per notebook, 500,000 words per source
- For clinical programming, PDFs are the primary format (protocols, SAPs, IG, FDA guidance)
- **Demo:** Show the source list in the left panel. Show how to add a second source (upload SAP).

#### Audio Overviews
- AI generates a podcast-style discussion of your documents (two AI "hosts" discuss the content)
- Takes 2-5 minutes to generate
- You can customize the topic: "Focus on the demographics section" or "Explain the treatment arms"
- Useful for: getting oriented on a new study, reviewing complex sections, accessibility
- **Demo:** Click "Generate" on the Audio Overview. While it generates, explain that it creates a ~10-minute discussion. Play the first 1-2 minutes when ready. Note: generation takes time, so you may want to have a pre-generated one ready.

#### Chat with Citations
- Every answer includes numbered citations linking to specific source passages
- You can click a citation to see the exact paragraph it came from
- This is the most useful feature for clinical programming: ask specific questions, get cited answers
- **Demo:** Ask several questions in sequence:
  - "How many sites are in this study?"
  - "What is the randomization ratio?"
  - "What concomitant medications are prohibited?"
  - Show that each answer has citations you can verify

#### Notes
- You can save any AI response as a Note
- Notes persist in the notebook for future reference
- Useful for building a "study summary" document
- **Demo:** Save one answer as a note. Show the Notes panel.

#### Source Guide
- Auto-generated when you upload a source
- Contains: summary, suggested questions (FAQ), table of contents
- Useful for getting oriented quickly
- **Demo:** Click on a source to show its guide. Show the suggested questions.

#### Sharing
- Notebooks can be shared with team members (view or edit access)
- Useful for collaborative study onboarding
- Note: sharing uses Google permissions -- check your company's data governance policy

### Transition
"Now let's see how these features apply specifically to clinical programming tasks."

---

## Module 1.3: Clinical Programming Use Cases (30 min)

### Talking Points

Walk through 5 scenarios using the project's study materials. For each, show the question, the answer, and the citation.

#### Scenario 1: Protocol Comprehension

**Setup:** Upload `study_data/protocol_excerpt_dm.pdf` (if not already uploaded)

**Questions to ask live:**
- "What is the study phase, indication, and study design?"
- "Describe the treatment arms including drug names and dosing"
- "What is the visit schedule for this study?"
- "What demographics data is collected at screening?"

**Teaching point:** "Before you start SDTM programming, you need to understand the study. NotebookLM gives you instant, cited answers instead of reading 200 pages."

#### Scenario 2: SAP Review

**Setup:** Upload `study_data/sap_excerpt_dm.pdf` to the same notebook

**Questions to ask live:**
- "What demographics variables are planned for the primary demographics table?"
- "Are there any subgroup analyses defined? If so, by which variables?"
- "How does the SAP define the analysis population?"

**Teaching point:** "The SAP tells you what analyses are planned. This helps you understand which SDTM variables matter most and how they'll be used downstream."

#### Scenario 3: SDTM IG Reference

**Setup:** Upload `docs/SDTMIG_v3.4.pdf` (this is a large file -- may take a minute to process)

**Questions to ask live:**
- "What are the required variables for the DM domain?"
- "How should RACE be handled when a subject selects 'Other Specify'?"
- "What is the definition of RFSTDTC and how should it be derived?"
- "What controlled terminology codelist applies to the SEX variable?"

**Teaching point:** "This is your SDTM IG reference assistant. Instead of searching a 400-page PDF, you ask a question and get the specific section with a citation. Notice it pulls from the exact IG text."

#### Scenario 4: Cross-Document Q&A

**Setup:** All three documents in the same notebook (protocol + SAP + IG)

**Questions to ask live:**
- "Based on the protocol's treatment arms and the SDTM IG, what values should ARMCD and ARM contain in the DM dataset?"
- "Does the SAP's demographics analysis plan cover all the DM variables required by the SDTM IG?"
- "Are there any discrepancies between the protocol's demographics CRF fields and the SDTM IG's DM domain requirements?"

**Teaching point:** "Cross-document analysis is where NotebookLM shines. You can ask questions that span multiple sources, and it will pull citations from each. This is something that would take you hours to do manually."

#### Scenario 5: FDA Guidance (Discussion Only)

**Discuss (do not demo unless you have FDA docs ready):**
- You could upload FDA guidance documents (E6 GCP, Study Data Standards Catalog, Technical Conformance Guide)
- Ask: "What does FDA require for race and ethnicity data collection in clinical trials?"
- Ask: "What validation checks does FDA expect for SDTM datasets?"
- This extends NotebookLM from "study-specific" to "regulatory reference"

**Teaching point:** "NotebookLM works with any PDF. Think about what documents you reference frequently -- SOPs, company standards, regulatory guidance -- and consider creating notebooks for them."

### Transition
"NotebookLM is powerful for document understanding. But it has clear limitations. Let's make sure you know what it cannot do."

---

## Module 1.4: Limitations & Guardrails (15 min)

### Talking Points

Be direct about limitations. Clinical programmers need to know exactly where the tool stops being useful.

1. **Cannot process data files:**
   - Cannot read CSV, SAS datasets, or Excel data files
   - Cannot count subjects, compute frequencies, or profile variables
   - "If you upload raw_dm.csv, it will try to parse it as text. It cannot tell you there are 300 subjects across 6 sites."

2. **Cannot execute code:**
   - Cannot write or run R, SAS, or Python code
   - Cannot generate SDTM datasets
   - "It can explain what iso_date() does if you upload the R source, but it cannot run it."

3. **Cannot connect to external systems:**
   - No API access, no database connections, no file system access
   - Everything happens in the browser with uploaded documents only

4. **No audit trail for GxP:**
   - Saved notes are not version-controlled
   - No user authentication log, no change tracking
   - "This is a productivity tool, not a validated system."

5. **Organizational data governance:**
   - Documents are uploaded to Google's servers
   - Check your company's policy on uploading proprietary/confidential documents
   - "Some companies restrict use of external AI tools with proprietary data. Know your policy."

6. **Accuracy depends on source quality:**
   - Answers are only as good as the uploaded documents
   - If the IG doesn't address your question, NotebookLM may say "not found" or give a partial answer
   - It will NOT go to the internet to fill gaps -- this is a feature, not a bug

### Key Contrast
"These limitations are exactly why we need the tools in the remaining chapters. Chapter 2 introduces AI coding assistants that CAN process data, write code, and execute scripts. Chapter 3 builds a RAG system that gives you control over how documents are stored and searched. The Capstone puts it all together."

### Transition
"Now it's your turn. Let's do the hands-on exercises."

---

## Module 1.5: Hands-On Exercises (45-60 min)

### Setup

Ensure all participants have:
- A Google account and are logged in
- Chrome browser open to https://notebooklm.google.com
- Access to the PDF files:
  - `study_data/protocol_excerpt_dm.pdf`
  - `study_data/sap_excerpt_dm.pdf`
  - `docs/SDTMIG_v3.4.pdf`
  - `study_data/raw_dm.csv` (for Exercise 1.4)

Distribute the exercise handouts (see `exercises/` directory).

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| 1.1: Study Materials Notebook | 15 min | Upload + ask questions + save notes |
| 1.2: SDTM IG Audio Overview | 15 min | Audio overview + follow-up questions |
| 1.3: Cross-Document Analysis | 15 min | Multi-source Q&A + finding discrepancies |
| 1.4: Limitations Discovery (optional) | 10 min | Try CSV upload + data processing request |

### Facilitation Tips

- **Walk the room** (or monitor screens on Zoom) during exercises
- **Common issue:** SDTM IG PDF may take 1-2 minutes to process due to size. Warn participants.
- **Common issue:** Audio Overview generation takes 2-5 minutes. Have participants start it and do other exercises while it generates.
- **Encourage exploration:** After completing required questions, participants should ask their own questions relevant to their real work
- **Group discussion after each exercise:** Ask 2-3 participants to share what they found. Were citations accurate? Did any answer surprise them?

### Wrap-Up (10 min)

1. **Poll the room:** "What's the most useful thing you discovered?"
2. **Review deliverables:** Ensure everyone has:
   - A notebook with study materials
   - Saved notes
   - Their "3 good / 3 bad" list
3. **Preview Chapter 2:** "Next, we move from understanding documents to actually doing the work -- reading data, writing code, and automating clinical programming tasks with AI coding assistants."

---

## Slide Deck Outline (for `slides/chapter_1_slides.pptx`)

| Slide # | Title | Content |
|---------|-------|---------|
| 1 | Title slide | "Chapter 1: Google NotebookLM for Clinical Programming" |
| 2 | Learning Objectives | 5 objectives from the plan |
| 3 | The Problem | "You have a 200-page protocol. Where do you start?" |
| 4 | What is NotebookLM? | Source-grounded AI, built on Gemini, free |
| 5 | Source Grounding | Diagram: documents -> NotebookLM -> cited answers (vs. general LLM -> uncited, possibly wrong answers) |
| 6 | Features Overview | Sources, Audio, Chat, Notes, Sharing |
| 7 | Sources | Supported formats, limits, clinical use |
| 8 | Audio Overviews | What they are, how to customize, when useful |
| 9 | Chat with Citations | Demo screenshot, citation verification |
| 10 | Clinical Use Case: Protocol | Questions + cited answers |
| 11 | Clinical Use Case: SAP | Questions + cited answers |
| 12 | Clinical Use Case: SDTM IG | Questions + cited answers |
| 13 | Cross-Document Analysis | Multi-source questions, finding discrepancies |
| 14 | Limitations | 6 limitations listed clearly |
| 15 | Limitations vs. What's Coming | Table: NotebookLM can / cannot vs. Ch.2-3-Capstone can |
| 16 | Exercise 1.1 Instructions | Study Materials Notebook |
| 17 | Exercise 1.2 Instructions | IG Audio Overview |
| 18 | Exercise 1.3 Instructions | Cross-Document Analysis |
| 19 | Exercise 1.4 Instructions | Limitations Discovery |
| 20 | Deliverables Checklist | What to submit/complete |
| 21 | Key Takeaways | 3 bullets: source grounding, clinical use cases, know the limits |
| 22 | What's Next | Preview of Chapter 2: AI Coding Assistants |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 1.1: What is NotebookLM? | 20 min | 0:20 |
| 1.2: Features Deep Dive | 30 min | 0:50 |
| 1.3: Clinical Use Cases | 30 min | 1:20 |
| 1.4: Limitations | 15 min | 1:35 |
| -- Break -- | 10 min | 1:45 |
| 1.5: Exercises | 45-60 min | 2:30-2:45 |
| Wrap-up + Q&A | 15 min | 2:45-3:00 |
