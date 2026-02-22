# Chapter 3: Building a RAG System for SDTM IG -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 5-6 hours |
| Format | Instructor-led workshop (concepts + hands-on Python exercises) |
| Audience | Clinical programmers who completed Chapters 1-2 |
| Prerequisites | Python 3.11+, familiarity with Claude Code MCP (Ch.2) |
| Materials | `sdtm_ig_db/` directory, `orchestrator/core/ig_client.py` |

## Key Teaching Message

In Chapter 1 you used NotebookLM's source grounding. In Chapter 2 you connected it via MCP. Now you build the same capability from scratch -- understanding chunking, embeddings, and vector search -- so you can create domain-specific retrieval systems you fully own and control. This is the "under the hood" chapter.

---

## Module 3.1: Why RAG? The Clinical Programming Problem (30 min)

### Talking Points

1. **Start with the pain:**
   "The SDTM IG v3.4 is hundreds of pages. You need one specific answer: 'What are the valid RACE values?' General LLMs might hallucinate a value that doesn't exist in the codelist. In a regulatory submission, that's unacceptable."

2. **Define RAG:**
   - **R**etrieval-**A**ugmented **G**eneration
   - Step 1: Retrieve the exact relevant passage from your documents
   - Step 2: Feed that passage to the LLM as context
   - Step 3: LLM generates an answer grounded in the retrieved text
   - "NotebookLM does exactly this -- but Google controls the chunking, search, and model. With RAG, YOU control everything."

3. **Why build your own?**
   | Concern | NotebookLM | Custom RAG |
   |---------|-----------|-----------|
   | Data governance | Google-hosted | Self-hosted |
   | Chunking control | None | Full |
   | Offline capability | No | Yes |
   | Audit trail | Minimal | Complete |
   | GxP compliance | No | Possible |
   | Cost at scale | Free/Enterprise | Your infrastructure |

4. **Clinical RAG use cases:**
   - SDTM IG variable lookup (this project)
   - Controlled terminology search
   - Protocol/SAP cross-reference
   - FDA guidance retrieval
   - Company SOP search
   - Historical study data standards

### Transition
"Let's understand the three types of search that power RAG systems."

---

## Module 3.2: Search Fundamentals (45 min)

### Talking Points

#### Keyword Search (15 min)
- How: exact string matching (SQL LIKE, regex, grep)
- **Live demo:** Open `sdtm_ig_db/sdtm_ig_content/dm_domain.md` and Ctrl+F for "RACE"
- Strengths: simple, fast, deterministic, no special infrastructure
- Weaknesses: "race" doesn't match "ethnicity"; "date format" doesn't match "ISO 8601"
- The file-based IG client (`orchestrator/core/ig_client.py`) uses keyword-like parsing

#### Semantic Search (20 min)
- How: convert text to embeddings (vectors), find similar vectors
- **Explain embeddings:** Every text chunk becomes a list of numbers (e.g., 1536 floats). Semantically similar texts produce similar vectors.
- **Explain cosine similarity:** Measure the "angle" between two vectors. Closer angle = more similar meaning.
- Walk through `sdtm_ig_db/load_sdtm_ig.py` -- the `EmbeddingGenerator` class
- Walk through `sdtm_ig_db/query_ig.py` -- the `cosine_similarity` static method
- Strengths: finds related content with different words ("partial date" matches "incomplete date entry")
- Weaknesses: needs embedding model (API cost), vector database, more complex

#### Hybrid Search (10 min)
- Combine both: keyword for precision, semantic for recall
- Industry standard: BM25 (improved keyword) + vector similarity
- This project: file-based = keyword-like; database mode = semantic capable
- The best production systems use both

### Key Concept -- Draw on Whiteboard
```
Document: "RACE should be coded using codelist C74457..."

Keyword search for "RACE":     FOUND (exact match)
Keyword search for "ethnicity": NOT FOUND (different word)
Semantic search for "ethnicity": FOUND (similar meaning, close vector)
```

---

## Module 3.3: Chunking Strategies (30 min)

### Talking Points

1. **Why chunk?**
   - The full SDTM IG is too large for an LLM context window
   - We need to retrieve ONLY the relevant pieces
   - Chunks must be small enough to be specific but large enough to retain context

2. **Walk through the code:**
   Open `sdtm_ig_db/load_sdtm_ig.py` and show the `TextChunker` class:
   - `chunk_by_sections()`: splits on markdown headings (###, ##, #) -- natural boundaries
   - `chunk_with_overlap()`: fixed-size chunks with overlap for continuity
   - Config from `sdtm_ig_db/config.py`:
     - `CHUNK_SIZE = 500` tokens (~2000 characters)
     - `CHUNK_OVERLAP = 100` tokens
     - `MAX_CHUNK_CHARS = 3000` (safety limit)
     - `MIN_CHUNK_CHARS = 100` (avoid fragments)

3. **Clinical-specific considerations:**
   - SDTM variables are natural chunk boundaries (each `### VARNAME` section = one chunk)
   - Tables (codelist values, variable summaries) should NOT be split across chunks
   - Cross-references ("AGE is derived from BRTHDTC and RFSTDTC") need to be preserved
   - Show: `dm_domain.md` uses `### VARNAME` sections -- each is a natural chunk

4. **The trade-off:**
   - Too small: "C74457" is a chunk but has no context about RACE
   - Too large: the entire DM section is a chunk but includes irrelevant variables
   - Right size: the RACE section with its valid values, assumptions, and approaches

---

## Module 3.4: The RAG Architecture in This Project (45 min)

### File-Based Mode (20 min)

Walk through `orchestrator/core/ig_client.py`:

1. **`_parse_domain_summary_table()`** -- extracts the variable metadata table from the end of the markdown file
2. **`_parse_variable_sections()`** -- splits the markdown by `### VARNAME` headings
3. **Public API:**
   - `get_domain_variables("DM")` -- all variables with metadata
   - `get_required_variables("DM")` -- only "Req" variables
   - `get_conditional_variables("DM")` -- "Cond" or "Exp" variables
   - `get_ct_variables("DM")` -- variables with controlled terminology
   - `get_variable_detail("DM", "RACE")` -- full IG text for a variable

**Demo:** Run a quick Python snippet:
```python
import sys; sys.path.insert(0, 'orchestrator')
from core.ig_client import IGClient
ig = IGClient()
print(ig.get_required_variables("DM"))
```

### Database Mode (20 min)

Walk through `sdtm_ig_db/` components:

1. **Schema** (`setup_db.py`):
   - `sdtm_ig_chunks`: content text + embedding vector + domain/section metadata
   - `controlled_terminology`: codelist code + raw value + CT value
   - `mapping_assumptions`: domain + variable + assumption text

2. **Loading** (`load_sdtm_ig.py`):
   - `ContentProcessor`: reads markdown, extracts sections
   - `TextChunker`: splits into chunks with metadata
   - `EmbeddingGenerator`: converts chunks to vectors (mock mode for training)
   - `DatabaseLoader`: inserts chunks + embeddings into PostgreSQL

3. **Querying** (`query_ig.py`):
   - `semantic_search(query, domain, top_k)` -- vector similarity search
   - `get_variable_documentation(domain, variable)` -- full variable docs
   - `get_codelist_values(codelist_code)` -- CT lookup
   - `get_context_for_mapping(domain, variable, question)` -- bundled context for LLM

### How It Connects to Everything Else (5 min)

```
NotebookLM (Ch.1)     -->  NotebookLM MCP (Ch.2)    -->  Custom RAG (Ch.3)
Browser-based               Programmatic access            Full control
Google controls              Google still controls           YOU control
```

The IG client from this chapter is imported by:
- Spec Builder agent (builds the mapping spec)
- Spec Reviewer agent (verifies completeness)
- MCP tool `sdtm_variable_lookup` (serves IG content to Claude Code)

---

## Module 3.5: Hands-On Exercises (120 min)

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| 3.1: Explore IG Content Files | 20 min | Understand markdown structure, identify chunk boundaries |
| 3.2: Use the File-Based IG Client | 30 min | Python scripting with IGClient API |
| 3.3: Experiment with Chunking | 30 min | Vary chunk parameters, observe results |
| 3.4: Build an AE Domain Content File | 40 min | Extend the system with a new domain |
| 3.5: Database Mode (optional) | 30 min | PostgreSQL + pgvector setup and queries |

### Facilitation Tips

- **Exercise 3.2:** Participants write Python scripts. If some are uncomfortable with Python, pair them with someone who is. The scripts are short (<20 lines).
- **Exercise 3.3:** The key insight is that chunk_size 200 vs 500 vs 1000 produces very different retrieval quality. Let participants discover this.
- **Exercise 3.4:** This is the most creative exercise. Provide the AE domain template but encourage participants to research AE variables. The reference solution is in `reference_solutions/`.
- **Exercise 3.5:** Only for participants with PostgreSQL. If no one has it, do this as an instructor demo or skip.

---

## Wrap-Up (15 min)

### Discussion
1. "When would you use file-based RAG vs database RAG?"
2. "How does chunking strategy affect the quality of SDTM IG answers?"
3. "Could this RAG system replace NotebookLM for your team? What are the trade-offs?"

### Preview Capstone
"You now have all three skills: document understanding (Ch.1), AI tool operation (Ch.2), and knowledge retrieval infrastructure (Ch.3). In the Capstone, we integrate them all into the SDTM Agentic Orchestrator -- 5 AI agents that automate the full DM programming workflow from raw data to validated, submission-ready datasets."

---

## Slide Deck Outline (for `slides/chapter_3_slides.pptx`)

| Slide # | Title | Content |
|---------|-------|---------|
| 1 | Title | "Chapter 3: Building a RAG System for SDTM IG" |
| 2 | Learning Objectives | 6 objectives |
| 3 | The Problem | "SDTM IG is 400 pages. You need one specific answer." |
| 4 | What is RAG? | Retrieve -> Augment -> Generate diagram |
| 5 | RAG vs General LLM | Side-by-side: hallucinated vs grounded answer |
| 6 | Clinical RAG Use Cases | IG, CT, protocol, FDA guidance, SOPs |
| 7 | Search: Keyword | How it works, strengths, weaknesses |
| 8 | Search: Semantic | Embeddings diagram, cosine similarity |
| 9 | Search: Hybrid | BM25 + vector, industry standard |
| 10 | Keyword vs Semantic Demo | Same query, different results |
| 11 | Chunking: Why It Matters | Too small / too large / right size |
| 12 | Chunking Strategies | Section-based vs overlap-based |
| 13 | Chunking Config | CHUNK_SIZE, OVERLAP, MAX/MIN |
| 14 | Clinical Chunking | SDTM variables as natural boundaries |
| 15 | Architecture: File-Based | ig_client.py flow diagram |
| 16 | Architecture: Database | PostgreSQL + pgvector schema |
| 17 | IG Client API | get_domain_variables, get_required_variables, etc. |
| 18 | How It Connects | IG client -> Spec Builder -> MCP tool -> Claude Code |
| 19-23 | Exercise slides | One per exercise |
| 24 | Three Retrieval Strategies | NotebookLM vs Custom RAG vs Local MCP |
| 25 | Deliverables | Checklist |
| 26 | Key Takeaways | Chunk well, search smart, own your data |
| 27 | What's Next | Capstone: SDTM Agentic Orchestrator |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 3.1: Why RAG? | 30 min | 0:30 |
| 3.2: Search Fundamentals | 45 min | 1:15 |
| 3.3: Chunking Strategies | 30 min | 1:45 |
| -- Break -- | 15 min | 2:00 |
| 3.4: RAG Architecture | 45 min | 2:45 |
| -- Break -- | 15 min | 3:00 |
| 3.5: Exercises | 120 min | 5:00 |
| Wrap-up + Q&A | 15 min | 5:15 |
