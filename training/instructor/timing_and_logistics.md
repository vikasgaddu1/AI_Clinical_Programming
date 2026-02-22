# Instructor Guide: Timing and Logistics

## Program Schedule Options

### Option A: 8-Day Workshop (Recommended)
| Day | Chapter | Duration | Format |
|-----|---------|----------|--------|
| Day 1 (Half) | Chapter 1: NotebookLM | 3 hrs | Morning session |
| Day 2 (Full) | Chapter 2: CLI Tools | 5 hrs | Full day |
| Day 3 (Half) | Chapter 2B: Function Library | 4 hrs | Morning + early afternoon |
| Day 4 (Full) | Chapter 3: RAG System | 5.5 hrs | Full day |
| Day 5 (Full) | Chapter 4: REST API + Chapter 5: Package Mgmt | 5 hrs + 4 hrs | Full day |
| Day 6 (Full) | Chapter 6: Vibe Coding | 6 hrs | Full day |
| Day 7 (Full) | Capstone (Part 1) | 4 hrs | Full day |
| Day 8 (Half) | Capstone (Part 2) | 3 hrs | Morning session |

### Option B: 6-Day Intensive
| Day | Content | Duration |
|-----|---------|----------|
| Day 1 | Ch.1 (full) + Ch.2 (through Module 2.3) | 6 hrs |
| Day 2 | Ch.2 (exercises) + Ch.2B (full) | 6 hrs |
| Day 3 | Ch.3 (full) + Ch.4 (modules only) | 6 hrs |
| Day 4 | Ch.4 (exercises) + Ch.5 (full) | 6 hrs |
| Day 5 | Ch.6: Vibe Coding (modules + demo + select exercises) | 6 hrs |
| Day 6 | Capstone (full) | 7 hrs |

### Option C: Weekly Sessions (10 weeks)
| Week | Content | Duration |
|------|---------|----------|
| Week 1 | Ch.1: NotebookLM | 2.5 hrs |
| Week 2 | Ch.2: Claude Code deep dive | 2.5 hrs |
| Week 3 | Ch.2: Cursor + exercises + Ch.2B: Function Library | 5 hrs (two sessions) |
| Week 4 | Ch.3: RAG System | 5 hrs (two sessions) |
| Week 5 | Ch.4: REST API for CDISC CT | 4.5 hrs |
| Week 6 | Ch.5: Enterprise Package Management | 4 hrs |
| Week 7-8 | Ch.6: Vibe Coding (modules, demo, exercises) | 6 hrs (two sessions) |
| Week 9-10 | Capstone | 7 hrs (two sessions) |

---

## Room / Zoom Setup

### In-Person
- Projector + screen for instructor demos
- Each participant: laptop with internet access, Chrome browser
- Whiteboard for architecture diagrams (Modules 2.2, 3.2, C.1)
- Power outlets for all laptops
- Printed handouts for each chapter (features reference, comparison tables, checklists)

### Virtual (Zoom/Teams)
- Screen sharing for instructor demos
- Breakout rooms for paired exercises (especially Ch.2 Exercise 2.4, Ch.3 Exercise 3.4)
- Chat for Q&A during exercises
- Pre-distribute: handouts as PDF, exercise files as markdown
- Backup plan for NotebookLM MCP demo (pre-recorded video)

---

## Pre-Workshop Preparation (1 week before)

### Participant Prerequisites Email

Send participants a checklist:

```
Subject: AI for Clinical Programming -- Pre-Workshop Setup

Please complete the following before the workshop:

Chapter 1 (Day 1):
- [ ] Create a Google account (if you don't have one)
- [ ] Verify you can access https://notebooklm.google.com

Chapter 2 (Day 2):
- [ ] Install Node.js 18+ (https://nodejs.org)
- [ ] Install Python 3.11+ (https://python.org)
- [ ] Install VS Code (https://code.visualstudio.com)
- [ ] Install Cursor free tier (https://cursor.com)
- [ ] Install Claude Code: npm install -g @anthropic-ai/claude-code
- [ ] (Optional) Get an Anthropic API key

Chapter 2B (Day 3):
- [ ] Same prerequisites as Chapter 2 (Node.js, Python, Claude Code)
- [ ] (Recommended) Install R 4.x (https://cran.r-project.org)
- [ ] Verify function_registry.json exists in project: ls r_functions/function_registry.json

Chapter 3 (Day 4):
- [ ] Verify Python works: python --version
- [ ] (Optional) Install PostgreSQL 14+

Chapter 5 (Day 5):
- [ ] Same prerequisites as Chapter 2 (Node.js, Python, Claude Code)
- [ ] Verify package_manager directory exists: ls package_manager/approved_packages.json

Chapter 6 (Day 6):
- [ ] Same prerequisites as Chapter 2 (Node.js, Python, Claude Code)
- [ ] (Recommended) Install PostgreSQL 14+ (for live TLF Search Tool demo)
- [ ] (Recommended) Install R 4.x (https://cran.r-project.org)
- [ ] (Optional) Get an Anthropic API key (for agent team experiments)

Capstone (Day 7-8):
- [ ] Install R 4.x (https://cran.r-project.org)
- [ ] Install R packages: Rscript -e "install.packages(c('arrow','haven'))"
- [ ] Clone/download the project directory (link will be provided)
```

### Instructor Setup
- Verify the full pipeline runs on your machine: `python orchestrator/main.py --domain DM`
- Pre-generate a NotebookLM notebook with protocol + SAP + IG uploaded (for Ch.1 demos)
- Pre-record a NotebookLM MCP demo video (backup for Ch.2 Exercise 2.2)
- Test all 5 skills in Claude Code (`/check-environment`, etc.)
- Ensure all exercise Python scripts work from a fresh terminal

---

## Materials Distribution

### Per Chapter
| Material | Format | Distribute When |
|----------|--------|----------------|
| Instructor slides | PPTX (screen) | N/A (instructor only) |
| Exercise handouts | PDF or Markdown | Start of exercise block |
| Reference handouts | PDF or Markdown | Start of chapter |
| Deliverables checklist | PDF | End of chapter |
| Reference solutions | PDF or Markdown | End of chapter (after exercises) |
