# RAG Concepts Quick Reference

## What is RAG?

**Retrieval-Augmented Generation** -- a technique that grounds LLM answers in specific documents by retrieving relevant passages before generating a response.

```
Step 1: RETRIEVE  -- Find relevant chunks from your document store
Step 2: AUGMENT   -- Add those chunks to the LLM's context
Step 3: GENERATE  -- LLM answers using the retrieved context (not just training data)
```

---

## Search Methods

| Method | How It Works | Finds "RACE" when searching for... | Best For |
|--------|-------------|-------------------------------------|----------|
| **Keyword** | Exact string match | "RACE" (exact match only) | Known terms, structured queries |
| **Semantic** | Vector similarity (embeddings) | "ethnicity", "racial category" (similar meaning) | Natural language questions |
| **Hybrid** | BM25 + vector | Both exact and similar | Production systems |

---

## Embeddings in 30 Seconds

- Every text chunk is converted to a list of numbers (e.g., 1536 floats)
- Semantically similar texts produce similar number patterns
- **Cosine similarity** measures how close two embeddings are (0 = unrelated, 1 = identical meaning)
- Common models: OpenAI `text-embedding-3-small`, Cohere `embed-v3`, open-source alternatives

---

## Chunking Strategies

| Strategy | How | Pros | Cons | Best For |
|----------|-----|------|------|----------|
| **Section-based** | Split on headings (###, ##) | Preserves natural structure | Chunk sizes vary | Structured docs (SDTM IG) |
| **Fixed-size with overlap** | Every N characters, overlap M | Consistent size | May split mid-sentence | Narrative text (protocols) |
| **Sentence-based** | Split on sentence boundaries | Natural boundaries | Small chunks | Dense, varied content |

**Key parameters:**
- `CHUNK_SIZE`: target chunk size (~500 tokens / ~2000 chars for SDTM)
- `CHUNK_OVERLAP`: characters shared between adjacent chunks (~100 tokens)
- `MIN_CHUNK_CHARS`: reject fragments shorter than this (100 chars)
- `MAX_CHUNK_CHARS`: safety limit (3000 chars)

---

## This Project's Architecture

### File-Based Mode (Default)
```
dm_domain.md  -->  IGClient parses markdown  -->  Returns variable metadata
                   (split by ### headings)        (name, type, CT, requirement)
```
- No database needed
- Works offline
- Keyword-like matching (exact section lookup)

### Database Mode (Optional)
```
Markdown files  -->  TextChunker  -->  EmbeddingGenerator  -->  PostgreSQL + pgvector
                     (chunk)          (vectorize)               (store + index)

Query  -->  Embed query  -->  Cosine similarity search  -->  Top-K chunks returned
```
- Requires PostgreSQL + pgvector
- Supports semantic search
- Scales to many domains

### Vector Database Options

Embeddings need to be stored somewhere for retrieval. Several vector databases exist, each with different trade-offs:

| Vector DB | Type | Setup | Scaling | Cost | Best For |
|-----------|------|-------|---------|------|----------|
| **PostgreSQL + pgvector** | SQL extension | Add to existing PG | Moderate | Free | Teams already using PostgreSQL |
| **ChromaDB** | Embedded | `pip install chromadb` | Limited | Free | Prototyping, local dev |
| **Pinecone** | Managed cloud | API key | High | Paid | Production, large-scale |
| **Weaviate** | Self-hosted or cloud | Docker or API | High | Free/Paid | Hybrid search (keyword+vector) |
| **Qdrant** | Self-hosted or cloud | Docker or API | High | Free/Paid | High-performance filtering |

**Why this project uses pgvector:** Our SDTM IG content is small (a few markdown files per domain). pgvector adds vector search to PostgreSQL with no new infrastructure -- one `CREATE EXTENSION` command. For a 50-domain production system with thousands of IG pages, you might graduate to a managed service like Pinecone (no database administration) or Weaviate (built-in hybrid search combining BM25 keyword matching with vector similarity).

---

### Beyond Vectors: Graph Databases for Regulatory Knowledge

Vector databases excel at "find me similar text" queries. But SDTM has inherent **graph structure** that vectors don't capture well:

- **Domains reference other domains:** DM provides USUBJID and RFSTDTC that AE, VS, and LB all depend on
- **Variables have dependency chains:** `iso_date()` must run before `derive_age()`, which must run before AGE is available
- **Codelists form hierarchies:** C74457 (Race) contains AMERICAN INDIAN OR ALASKA NATIVE, ASIAN, BLACK OR AFRICAN AMERICAN, etc.
- **Cross-domain constraints:** AESTDY in AE is derived from AESTDTC minus RFSTDTC (from DM)

A **graph database** like Neo4j models these relationships explicitly:

```
(DM)-[:HAS_VARIABLE]->(RACE)-[:USES_CODELIST]->(C74457)-[:CONTAINS]->(ASIAN)
(DM)-[:HAS_VARIABLE]->(RFSTDTC)-[:USED_BY]->(AE.AESTDY)
(iso_date)-[:MUST_RUN_BEFORE]->(derive_age)
```

| Approach | Answers | Example Query |
|----------|---------|---------------|
| **Vector DB (RAG)** | "What does the IG say about RACE?" | Semantic similarity search |
| **Graph DB** | "What variables depend on RFSTDTC?" | Traverse relationship edges |
| **Combined** | "Show me all variables that use extensible codelists and have derivation dependencies" | Graph traversal + semantic context |

This project does not implement a graph database, but the concept is important for architect-level thinking about multi-domain SDTM systems. When you have 20+ domains with complex cross-domain dependencies, a graph database can answer "what is the correct build order?" and "what downstream datasets break if I change this variable?" -- questions that vector search alone cannot handle.

---

### IGClient API
```python
ig = IGClient()
ig.get_domain_variables("DM")         # All variables with metadata
ig.get_required_variables("DM")       # Only "Req" variables
ig.get_conditional_variables("DM")    # "Cond" or "Exp" variables
ig.get_ct_variables("DM")             # Variables with controlled terminology
ig.get_variable_detail("DM", "RACE")  # Full IG text for a variable
ig.is_available()                     # True if IG content exists
```

---

## Three Grounding Strategies Compared

| Strategy | Setup | Control | Offline | Audit | Best For |
|----------|-------|---------|---------|-------|----------|
| **NotebookLM MCP** | 1 command | Low (Google controls) | No | Minimal | Quick grounding, any docs |
| **File-based RAG** | None (files exist) | High (you own files) | Yes | Full | Training, small scope |
| **Database RAG** | PostgreSQL setup | Full (you own everything) | Yes | Full | Production, multi-domain |

---

## Extending to New Domains

Adding a new SDTM domain (e.g., AE, VS, LB) requires:

1. Create `sdtm_ig_db/sdtm_ig_content/ae_domain.md` following the DM pattern
2. Include `### VARNAME` sections for each variable
3. Include a summary table at the end
4. The IGClient automatically discovers and parses the new file

No code changes needed -- just a markdown file.
