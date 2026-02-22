# TLF Search Tool

A semantic search tool for clinical trial TLF (Tables, Figures, Listings) outputs. Stores TLF metadata (titles, footnotes, program paths) in PostgreSQL with vector embeddings, enabling stats programmers to find similar outputs across studies.

## The Problem

Every stats programmer faces this: you need to create Table 14.2.3 -- Summary of AEs by Severity. Has anyone at your company created a similar table before? Which study? Which program? You end up searching shared drives, asking colleagues, or starting from scratch.

## The Solution

This tool:
1. **Scans** TLF output metadata (titles, footnotes, program names)
2. **Embeds** each TLF's title + footnotes as a vector using an embedding model
3. **Stores** everything in PostgreSQL with pgvector for fast similarity search
4. **Searches** semantically: ask "adverse event severity summary" and find matching TLFs

## Architecture

```
TLF Catalog (CSV)
       |
       v
  load_tlfs.py          ← Reads CSV, generates embeddings, inserts to DB
       |
       v
  PostgreSQL + pgvector  ← Stores TLF metadata + embedding vectors
       |
       v
  search_tlfs.py         ← Embeds query, cosine similarity, returns top-K
       |
       v
  Results: Title, Footnotes, Program Path, Similarity Score
```

## Files

| File | Status | Purpose |
|------|--------|---------|
| `config.py` | Ready | Database connection settings |
| `setup_db.py` | Ready | Creates the `tlf_outputs` table + indexes |
| `load_tlfs.py` | Stub | Reads CSV, embeds, loads to DB (implement during demo) |
| `search_tlfs.py` | Stub | Semantic search interface (implement during demo) |
| `sample_data/tlf_catalog.csv` | Ready | 35 sample TLF entries from Study XYZ-2026-001 |

## Quick Start

```bash
# 1. Create the database table
python setup_db.py

# 2. Load sample TLF data (implement during demo)
python load_tlfs.py

# 3. Search for similar TLFs (implement during demo)
python search_tlfs.py "demographics summary by treatment"
python search_tlfs.py "adverse event severity"
```

## Database Schema

```sql
CREATE TABLE tlf_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    study_id VARCHAR(50) NOT NULL,
    output_type VARCHAR(10) NOT NULL,      -- Table, Figure, Listing
    output_number VARCHAR(20) NOT NULL,     -- 14.1.1, 16.2.1, etc.
    title TEXT NOT NULL,
    footnotes TEXT,
    program_name VARCHAR(100),
    program_path VARCHAR(500),
    domain_source VARCHAR(10),              -- DM, AE, VS, LB, etc.
    status VARCHAR(20) DEFAULT 'draft',     -- draft, validated, final
    created_date DATE,
    embedding vector(1536)                  -- pgvector embedding
);
```

## Reused Patterns

This app follows the same patterns as the project's SDTM IG RAG system:

| Pattern | IG RAG System | TLF Search Tool |
|---------|--------------|-----------------|
| Schema | `sdtm_ig_db/setup_db.py` | `setup_db.py` |
| Config | `sdtm_ig_db/config.py` | `config.py` |
| Embeddings | `EmbeddingGenerator` in `load_sdtm_ig.py` | Reuse same class |
| Search | `SDTMIGQuery` in `query_ig.py` | `search_tlfs.py` |

## Demo Instructions (for Instructor)

1. Show this README and explain the architecture
2. Run `setup_db.py` to create the table
3. Use vibe coding (plan mode) to implement `load_tlfs.py`
4. Use vibe coding to implement `search_tlfs.py`
5. Load the sample data and run test searches
6. Show how this connects to the RAG patterns from Chapter 3
