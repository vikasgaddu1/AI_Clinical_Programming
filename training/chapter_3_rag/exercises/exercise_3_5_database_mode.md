# Exercise 3.5: Database Mode (Optional)

## Objective
Set up PostgreSQL + pgvector for production-grade semantic search over SDTM IG content. Compare database query results with file-based results.

## Time: 30 minutes

## Prerequisites
- PostgreSQL 14+ installed and running
- pgvector extension available
- Python packages: `psycopg2-binary`

**If you don't have PostgreSQL installed, follow along with the instructor demo or skip to the reflection questions.**

---

## Steps

### Step 1: Create the Database Schema

```bash
cd sdtm_ig_db
python setup_db.py
```

This creates:
- Database `sdtm_ig_rag` (or uses existing)
- Table `sdtm_ig_chunks` with vector column for embeddings
- Table `controlled_terminology` for codelist values
- Table `mapping_assumptions` for domain rules
- pgvector IVFFlat index for fast similarity search

> Schema creation: Success / Failed
> Error (if any): _____________________________________________

### Step 2: Load IG Content

```bash
python load_sdtm_ig.py
```

This reads the markdown files, chunks them, generates embeddings (mock mode by default), and loads into PostgreSQL.

> Chunks loaded: ___________
> CT entries loaded: ___________
> Assumptions loaded: ___________

### Step 3: Run Example Queries

```bash
python query_ig.py --examples
```

Or run manually:
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# Variable documentation
doc = q.get_variable_documentation("DM", "RACE")
print(f"RACE docs: {len(doc)} characters")

# Codelist values
cl = q.get_codelist_values("C74457")
print(f"C74457 values: {cl}")

# Mapping assumptions
assumptions = q.get_mapping_assumptions("DM", "RACE")
print(f"RACE assumptions: {assumptions}")
```

> Did the queries return results? Yes / No

### Step 4: Compare with File-Based Mode

Run the same query via both methods:

```python
# File-based (from Exercise 3.2)
import sys; sys.path.insert(0, 'orchestrator')
from core.ig_client import IGClient
ig = IGClient()
file_result = ig.get_variable_detail("DM", "RACE")

# Database-based
from query_ig import SDTMIGQuery
from config import Config
q = SDTMIGQuery(Config.db.get_connection_string())
db_result = q.get_variable_documentation("DM", "RACE")

print(f"File-based result: {len(file_result)} chars")
print(f"Database result: {len(db_result)} chars")
```

> Which returned more content? ___________
> Were the answers consistent? ___________

### Step 5: When to Use Each Mode

| Aspect | File-Based | Database |
|--------|-----------|----------|
| Setup effort | None (files exist) | PostgreSQL + pgvector |
| Query speed | Fast (file parse) | Fast (indexed) |
| Semantic search | No (keyword-like) | Yes (vector similarity) |
| Scale | Works for ~5 domain files | Scales to thousands of chunks |
| Offline | Yes | Yes (local DB) |
| Best for | Training, small IG subset | Production, multi-domain, full IG |

---

## Reflection Questions (for everyone, even without PostgreSQL)

1. When would a clinical programming team need database-mode RAG vs file-based?
2. What's the cost of maintaining a PostgreSQL database vs maintaining markdown files?
3. Could you use a cloud vector database (Pinecone, Weaviate) instead? What would change?

---

## Stretch Goal: Choosing a Vector Database for Production

Your team is tasked with building a production RAG system that covers all 30+ SDTM domains across multiple SDTM IG versions (3.3, 3.4, 4.0). Consider these options:

| Option | Technology | Setup | Ongoing Cost |
|--------|-----------|-------|-------------|
| A | PostgreSQL + pgvector (what we used) | Add extension to existing DB | DBA time |
| B | ChromaDB (embedded, in-process) | `pip install chromadb` | None (runs in your Python process) |
| C | Pinecone (managed cloud) | API key from pinecone.io | ~$70/mo for 1M vectors |

> **Question 1:** For a single-study, single-domain project (like our DM example), which option has the best effort-to-value ratio?
> Answer: _________________________________________________________________

> **Question 2:** For a 50-domain production system that 20 programmers query daily, which option would you recommend and why?
> Answer: _________________________________________________________________

> **Question 3:** ChromaDB stores everything in-process (no separate database server). What is the advantage? What is the risk if two pipeline runs query simultaneously?
> Answer: _________________________________________________________________

> **Question 4:** Your company's IT policy requires all data to remain on-premises. Which options are still available?
> Answer: _________________________________________________________________

---

## What You Should Have at the End

- [ ] (If PostgreSQL available) Database created with IG content loaded
- [ ] (If PostgreSQL available) Successful queries returning variable docs
- [ ] Understanding of when file-based vs database mode is appropriate
- [ ] (Stretch) Informed opinion on vector database selection for different scenarios
