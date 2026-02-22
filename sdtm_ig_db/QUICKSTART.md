# SDTM IG RAG System - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- PostgreSQL 12+ installed and running
- Python 3.8+
- Basic terminal/command line familiarity

## Installation (5 minutes)

### 1. Install Python Dependencies
```bash
cd /path/to/sdtm_ig_db
pip install -r requirements.txt
```

### 2. Create Database User
```bash
sudo -u postgres psql
```

In psql:
```sql
CREATE USER sdtm_user WITH PASSWORD 'sdtm_password';
CREATE DATABASE sdtm_ig_rag OWNER sdtm_user;
\q
```

### 3. Setup Database Schema
```bash
python setup_db.py
```

Output:
```
Database setup completed successfully
Connect with: psql postgresql://sdtm_user@localhost/sdtm_ig_rag
```

### 4. Load SDTM IG Content
```bash
python load_sdtm_ig.py
```

Output:
```
Load complete: 27 content chunks loaded
Loaded 25 controlled terminology entries
Loaded 20 mapping assumptions
```

### 5. Verify Installation
```bash
python query_ig.py --examples
```

Should show 5 example queries with results.

---

## Basic Usage

### Example 1: Find IG Guidance for SEX Variable
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# Get complete documentation
doc = q.get_variable_documentation("DM", "SEX")

print("Assumptions:")
for assumption in doc['assumptions']:
    print(f"  - {assumption['text']}")

print("\nValid values:")
for ct in doc['controlled_terminology']:
    print(f"  - {ct['term_value']}: {ct['definition']}")

q.disconnect()
```

### Example 2: Search for Guidance on RACE
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# Semantic search
results = q.semantic_search(
    "What if subject reports multiple races?",
    domain="DM",
    top_k=3
)

for r in results:
    print(f"\n{r['section']}")
    print(f"Type: {r['chunk_type']}")
    print(f"Content: {r['content'][:200]}...")

q.disconnect()
```

### Example 3: Get Valid Codelist Values
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# Lookup SEX values
sex_values = q.get_codelist_values(variable="SEX")

print("Valid SEX values:")
for v in sex_values:
    print(f"  {v['term_value']}: {v['definition']}")

q.disconnect()
```

### Example 4: Get Complete Mapping Context (for AI)
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# Get all relevant context for an AI model
context = q.get_context_for_mapping(
    "DM",
    "RACE",
    question="How do I handle multiple races?"
)

# This includes:
# - Variable documentation
# - Valid codelists
# - Mapping assumptions and rules
# - Multiple valid approaches

print(f"Documentation chunks: {len(context['documentation']['documentation'])}")
print(f"Valid values: {len(context['controlled_terminology'])}")
print(f"Assumptions: {len(context['assumptions'])}")

q.disconnect()
```

### Example 5: Run the Demo Orchestrator
```bash
python orchestrator_example.py
```

Shows 3 realistic mapping scenarios:
1. Simple mapping (SEX)
2. Complex with alternatives (RACE)
3. Derivation with multiple approaches (RFSTDTC)

---

## Common Tasks

### Task 1: Search for Information on a Variable
```python
q = SDTMIGQuery(Config.db.get_connection_string())
q.semantic_search("RACE multiple values", domain="DM", top_k=5)
q.disconnect()
```

### Task 2: Get All Mapping Assumptions for a Domain
```python
q = SDTMIGQuery(Config.db.get_connection_string())
assumptions = q.get_mapping_assumptions(domain="DM")
for a in assumptions:
    print(f"{a['variable']}: {a['assumption']}")
q.disconnect()
```

### Task 3: Look Up Valid Values for Any Variable
```python
q = SDTMIGQuery(Config.db.get_connection_string())

# SEX valid values
sex = q.get_codelist_values(variable="SEX")

# RACE valid values
race = q.get_codelist_values(variable="RACE")

# By codelist code
c66742 = q.get_codelist_values(codelist_code="C66742")

q.disconnect()
```

### Task 4: Get All Guidance for a Single Variable
```python
q = SDTMIGQuery(Config.db.get_connection_string())

# Complete documentation
doc = q.get_variable_documentation("DM", "RACE")

# Now you have:
# - doc['documentation']: Full IG text about this variable
# - doc['assumptions']: Rules for mapping it
# - doc['controlled_terminology']: Valid values
```

### Task 5: Prepare Context for AI Model
```python
q = SDTMIGQuery(Config.db.get_connection_string())

context = q.get_context_for_mapping(
    "DM",
    "RACE",
    "Subject reports White and Asian ancestry"
)

# Format for your AI prompt
prompt = f"""
Based on SDTM IG:
{json.dumps(context, indent=2)}

Question: How should I map this race data?
"""
```

---

## Configuration

### Default Settings
The system works out of the box with defaults. Override via environment variables:

```bash
# .env file
PGHOST=localhost
PGPORT=5432
PGDATABASE=sdtm_ig_rag
PGUSER=sdtm_user
PGPASSWORD=sdtm_password
EMBEDDING_PROVIDER=mock
CHUNK_SIZE=500
TOP_K_CHUNKS=5
```

Or set individually:
```bash
export PGHOST=localhost
export PGPORT=5432
```

### Production Settings
```bash
# .env for production
PGHOST=prod-db.example.com
PGPORT=5432
PGDATABASE=sdtm_ig_rag
PGUSER=sdtm_user
PGPASSWORD=<secure_password>

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

LOG_LEVEL=INFO
MAX_CONTEXT_TOKENS=4000
```

---

## Troubleshooting

### Can't Connect to Database
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql postgresql://sdtm_user@localhost/sdtm_ig_rag

# If error, check:
# 1. PostgreSQL service running
# 2. User sdtm_user exists
# 3. Database sdtm_ig_rag exists
# 4. Credentials match
```

### No Results from Search
```python
# Try simpler query
q.semantic_search("RACE", top_k=10)

# Check what's in database
q.cur.execute("SELECT COUNT(*) FROM sdtm_ig_chunks")
# Should be > 20
```

### ImportError for psycopg2
```bash
# Reinstall PostgreSQL adapter
pip install --upgrade psycopg2-binary
```

### AttributeError in Query
```python
# Make sure context is properly returned
context = q.get_context_for_mapping("DM", "RACE")
if context and context['documentation']:
    print(context['documentation']['documentation'][0]['content'])
```

---

## Next Steps

1. **Explore the Code**
   - Read `config.py` for all available settings
   - Check `query_ig.py` for all query functions
   - Review `load_sdtm_ig.py` for chunking logic

2. **Add Your Own Content**
   - Create `sdtm_ig_content/ae_domain.md` for AE domain
   - Run `python load_sdtm_ig.py` to load it
   - Query as normal

3. **Integrate with AI**
   - Use `orchestrator_example.py` as a template
   - Connect to Claude API or OpenAI
   - Build your mapping decision system

4. **Deploy to Production**
   - Switch EMBEDDING_PROVIDER to "openai"
   - Set up proper PostgreSQL on cloud (AWS RDS, Google Cloud SQL, etc.)
   - Configure environment variables securely
   - Add monitoring/logging

---

## API Reference Quick Reference

### Main Query Functions
```python
from query_ig import SDTMIGQuery
from config import Config

q = SDTMIGQuery(Config.db.get_connection_string())

# 1. Semantic search
results = q.semantic_search("your question", domain="DM", top_k=5)

# 2. Variable documentation
doc = q.get_variable_documentation("DM", "RACE")

# 3. Codelist lookup
values = q.get_codelist_values(variable="SEX")

# 4. Assumptions
assumptions = q.get_mapping_assumptions(domain="DM", variable="RACE")

# 5. Complete context (best for AI)
context = q.get_context_for_mapping("DM", "RACE", question="...")

q.disconnect()
```

### Return Values
```python
# semantic_search returns:
[
    {
        'id': 1,
        'domain': 'DM',
        'section': 'Core DM Variables',
        'subsection': 'RACE',
        'content': 'Full text...',
        'chunk_type': 'variable_definition',
        'relevance': 0.85
    },
    ...
]

# get_variable_documentation returns:
{
    'domain': 'DM',
    'variable': 'RACE',
    'documentation': [{'id': 1, 'content': '...', ...}],
    'assumptions': [{'text': '...', 'priority': 1, ...}],
    'controlled_terminology': [{'term_value': 'WHITE', ...}]
}

# get_codelist_values returns:
[
    {
        'codelist_code': 'C74456',
        'codelist_name': 'Race',
        'term_value': 'WHITE',
        'term_code': 'C41262',
        'definition': 'People of European origin',
        'synonyms': 'Caucasian; European'
    },
    ...
]

# get_mapping_assumptions returns:
[
    {
        'id': 1,
        'domain': 'DM',
        'variable': 'RACE',
        'assumption': 'Multiple races use RACE="MULTIPLE" with SUPPDM...',
        'reference': 'IG Section 2.3',
        'priority': 1,
        'approach': 2
    },
    ...
]

# get_context_for_mapping returns:
{
    'domain': 'DM',
    'variable': 'RACE',
    'documentation': {...},
    'controlled_terminology': [...],
    'assumptions': [...],
    'related_questions': [...]
}
```

---

## Example Output

When you run the examples:

```
EXAMPLE 1: Simple Variable Mapping
Scenario: Map source SEX value to SDTM

======================================================================
SDTM MAPPING DECISION REPORT
======================================================================

VARIABLE: DM.SEX

SOURCE VALUE:        Male
MAPPED VALUE:        M
CONFIDENCE LEVEL:    HIGH

REASONING:
Single sex reported: Male → M. Per IG: SEX is typically from subject 
self-report at screening. Use medical history only if self-report 
unavailable.

IG REFERENCES:
  • CDISC IG: Section G.2.1 - Demographics Domain
  • CDISC IG: DM Variables - SEX Definition
  • CDISC Codelist C66742: Sex

VALIDATION RULES:
  • Must be one of: M, F, U
  • Required for all subjects
  • Case-sensitive (uppercase only)

======================================================================
```

---

## Where to Go From Here

- **ARCHITECTURE.md** - Deep dive into system design
- **README.md** - Complete documentation
- **config.py** - All configuration options
- **query_ig.py** - Query interface reference
- **orchestrator_example.py** - AI integration example

---

## Support

For questions or issues:

1. Check **README.md** troubleshooting section
2. Review **ARCHITECTURE.md** for design questions
3. Check inline comments in Python files
4. Run example queries to understand behavior

---

**You're ready to start!** 🚀

```bash
python query_ig.py --examples
```

