# SDTM Implementation Guide RAG System

A Python-based Retrieval-Augmented Generation (RAG) system for semantic search and lookup of SDTM (Study Data Tabulation Model) Implementation Guide content, stored in PostgreSQL with pgvector for vector similarity search.

**Purpose:** Enable AI models to retrieve relevant SDTM guidance when making clinical data mapping decisions.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Setup and Installation](#setup-and-installation)
4. [Database Schema](#database-schema)
5. [Loading Content](#loading-content)
6. [Querying the System](#querying-the-system)
7. [Example Use Cases](#example-use-cases)
8. [How the AI Orchestrator Uses This System](#how-the-ai-orchestrator-uses-this-system)
9. [Development and Troubleshooting](#development-and-troubleshooting)

---

## Architecture Overview

### RAG Pattern

The Retrieval-Augmented Generation (RAG) pattern combines document retrieval with AI models:

```
Source Data (Raw SDTM IG)
         ↓
    [CHUNKING] - Split into semantic segments
         ↓
   [EMBEDDING] - Generate vector representations
         ↓
  [STORAGE] - PostgreSQL with pgvector
         ↓
    [QUERY] - Semantic similarity search
         ↓
  [CONTEXT] - Retrieved chunks + user question
         ↓
   [MODEL] - AI generates mapping decision using context
         ↓
  Output (Mapping recommendation + source citations)
```

### Why RAG for SDTM?

1. **Consistency:** AI references actual IG guidance, not training-based "hallucinations"
2. **Traceability:** Every recommendation cites source IG section
3. **Flexibility:** Easy to update with new IG versions
4. **Domain-Specific:** Captures detailed SDTM rules not in general training data
5. **Compliance:** Audit trail of what guidance was consulted

---

## System Components

### 1. **config.py** - Configuration Management
- Centralized settings for database, embeddings, chunking
- Environment variable overrides for different environments
- RAG-specific settings (context size, retrieval parameters)

### 2. **setup_db.py** - Database Schema Creation
- Creates PostgreSQL tables with proper indexes
- Installs pgvector extension for semantic search
- Three main tables:
  - `sdtm_ig_chunks` - Chunked IG content with embeddings
  - `controlled_terminology` - Valid values for coded variables
  - `mapping_assumptions` - Rules and operational guidance

### 3. **load_sdtm_ig.py** - Content Loading Pipeline
- Reads markdown IG files
- Intelligently chunks text preserving semantic boundaries
- Generates embeddings (uses mock embeddings for training)
- Loads chunks with metadata into PostgreSQL
- Populates controlled terminology and assumptions

### 4. **query_ig.py** - Query Interface
- Primary interface for retrieving guidance
- Semantic search for similarity-based retrieval
- Codelist lookup for valid values
- Variable documentation retrieval
- Mapping context assembly for AI models

### 5. **SDTM IG Content Files** (Markdown)
- `dm_domain.md` - Demographics domain with detailed variable documentation
- `general_assumptions.md` - Cross-domain rules and assumptions

---

## Setup and Installation

### Prerequisites

- PostgreSQL 12+
- Python 3.8+
- pgvector extension (optional, system gracefully degrades without it)

### Step 1: Install PostgreSQL

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**On macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**On Windows:**
Download installer from https://www.postgresql.org/download/windows/

### Step 2: Install pgvector Extension (Recommended)

```bash
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

Then in psql:
```sql
CREATE EXTENSION vector;
```

### Step 3: Create Database User and Database

```bash
# Connect as postgres user
sudo -u postgres psql

# In psql:
CREATE USER sdtm_user WITH PASSWORD 'sdtm_password';
CREATE DATABASE sdtm_ig_rag OWNER sdtm_user;
GRANT ALL PRIVILEGES ON DATABASE sdtm_ig_rag TO sdtm_user;
```

### Step 4: Install Python Dependencies

```bash
cd /path/to/sdtm_ig_db
pip install -r requirements.txt
```

### Step 5: Set Environment Variables (Optional)

Create `.env` file:
```bash
# Database
PGHOST=localhost
PGPORT=5432
PGDATABASE=sdtm_ig_rag
PGUSER=sdtm_user
PGPASSWORD=sdtm_password

# Embeddings
EMBEDDING_PROVIDER=mock           # or "openai" or "claude"
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-...             # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-...      # if using Claude

# Chunking
CHUNK_SIZE=500                    # tokens
CHUNK_OVERLAP=100                 # tokens

# Query
TOP_K_CHUNKS=5                    # retrieve top 5 chunks
SIMILARITY_THRESHOLD=0.6          # 0-1, higher = stricter
```

Load with: `python -m dotenv`

### Step 6: Initialize Database Schema

```bash
python setup_db.py
```

Output should show:
```
Starting SDTM IG Database Setup
Target database: sdtm_ig_rag
Host: localhost:5432
Created database 'sdtm_ig_rag'
Setting up PostgreSQL extensions...
Creating sdtm_ig_chunks table...
Creating controlled_terminology table...
Creating mapping_assumptions table...
Database schema successfully initialized
```

### Step 7: Load SDTM IG Content

```bash
python load_sdtm_ig.py
```

Output should show:
```
Starting SDTM IG Content Load
Loaded dm_domain.md (45000 chars)
Loaded general_assumptions.md (32000 chars)
Chunked dm_domain.md into 15 segments
Chunked general_assumptions.md into 12 segments
Successfully loaded 27 content chunks to database
Loaded 25 controlled terminology entries
Loaded 20 mapping assumptions
Load complete: 27 content chunks loaded
```

### Step 8: Run Example Queries (Verify Installation)

```bash
python query_ig.py --examples
```

Should display example queries and results.

---

## Database Schema

### sdtm_ig_chunks Table

Stores chunked SDTM IG content with embeddings.

| Column | Type | Purpose |
|--------|------|---------|
| id | SERIAL PRIMARY KEY | Unique chunk identifier |
| domain | VARCHAR(10) | SDTM domain (DM, AE, LB, etc.) |
| section | VARCHAR(255) | Major section (Domain Variables, Assumptions, etc.) |
| subsection | VARCHAR(255) | Subsection for hierarchy |
| content | TEXT | Actual chunk text |
| chunk_type | VARCHAR(50) | Type (overview, variable_def, assumption, etc.) |
| sequence | INT | Order within document |
| embedding | vector(1536) | Vector for semantic search (pgvector) |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Indexes:**
- `domain` - Filter by domain (DM, AE, etc.)
- `section` - Filter by content section
- `chunk_type` - Filter by content type
- `(domain, sequence)` - Order within domain
- `embedding` - Vector similarity search (IVFFlat)

### controlled_terminology Table

Valid values for SDTM coded variables.

| Column | Type | Purpose |
|--------|------|---------|
| id | SERIAL PRIMARY KEY | Unique entry identifier |
| codelist_code | VARCHAR(20) | CDISC codelist code (C66742, C74456, etc.) |
| codelist_name | VARCHAR(255) | Human name (Sex, Race, etc.) |
| term_code | VARCHAR(20) | NCI code for term |
| term_value | VARCHAR(255) | Actual codelist value (M, F, WHITE, etc.) |
| synonyms | TEXT | Alternate acceptable values |
| definition | TEXT | Definition from NCI thesaurus |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- `codelist_code` - Lookup by NCI code
- `codelist_name` - Lookup by friendly name
- `term_value` - Search for specific value

### mapping_assumptions Table

Domain and variable-specific mapping rules.

| Column | Type | Purpose |
|--------|------|---------|
| id | SERIAL PRIMARY KEY | Unique assumption identifier |
| domain | VARCHAR(10) | Domain (DM, AE, GENERAL) |
| variable | VARCHAR(50) | Variable name (NULL for domain-level) |
| assumption_text | TEXT | The assumption/rule text |
| ig_reference | VARCHAR(255) | Reference to IG section |
| priority | INT | 1=Critical, 2=Important, 3=Info |
| approach_number | INT | For multiple valid approaches (1, 2, 3) |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- `domain` - Filter by domain
- `(domain, variable)` - Lookup by domain+variable
- `priority` - Filter by importance

---

## Loading Content

### Content File Format

SDTM IG content is provided in Markdown format with specific structure:

```markdown
# Domain Name

## Overview Section
Introductory content...

## Variable Name - Description
Details about variable...

### Assumptions
Assumptions for this variable...

### Multiple Valid Approaches
**Approach 1: First approach**
Details...

**Approach 2: Second approach**
Details...
```

### Chunking Strategy

The loader uses intelligent section-based chunking:

1. **Identify sections** by heading level (# ## ###)
2. **Group content** within section boundaries
3. **Respect size limits** (~500 tokens / ~2000 characters)
4. **Preserve context** with overlaps between chunks
5. **Track metadata** (domain, section, subsection, type)

**Example chunk:**
```
Content: "The RACE variable captures subject's racial category. 
         Controlled Terminology includes AMERICAN INDIAN... WHITE, MULTIPLE.
         When subject reports multiple races, use RACE='MULTIPLE' and record 
         individual races in SUPPDM with QNAM='RACE1', 'RACE2'..."

Metadata:
  - domain: "DM"
  - section: "Core DM Variables"
  - subsection: "RACE - Race"
  - chunk_type: "variable_definition"
  - sequence: 12
  - embedding: [0.23, -0.15, 0.89, ...] (1536 dimensions)
```

### Custom Content Loading

To add your own SDTM IG content:

1. **Create markdown file** in `sdtm_ig_content/` directory
   - Name: `{domain}_domain.md` (e.g., `ae_domain.md`)
   - Follow markdown structure with clear headings

2. **Update load_sdtm_ig.py** if adding new tables/assumptions

3. **Run loader:**
   ```bash
   python load_sdtm_ig.py
   ```

4. **Verify loading:**
   ```bash
   python query_ig.py --examples
   ```

---

## Querying the System

### Basic Usage

```python
from query_ig import SDTMIGQuery
from config import Config

# Initialize query interface
q = SDTMIGQuery(Config.db.get_connection_string())

# Semantic search
results = q.semantic_search("How should I map RACE?", domain="DM", top_k=5)
for r in results:
    print(f"{r['section']}: {r['content'][:100]}...")

# Variable documentation
doc = q.get_variable_documentation("DM", "RACE")
print(f"Assumptions: {doc['assumptions']}")
print(f"Valid values: {doc['controlled_terminology']}")

# Mapping context
context = q.get_context_for_mapping("DM", "RACE")
# Use context to prompt AI model

q.disconnect()
```

### Query Functions

#### semantic_search()
Find chunks by keyword/semantic similarity.

```python
results = q.semantic_search(
    query="What if multiple races reported?",
    domain="DM",               # Optional filter
    top_k=5,                   # Number of results
    threshold=0.6              # Similarity threshold (0-1)
)
# Returns: List of chunks with content, section, relevance
```

#### get_variable_documentation()
Get complete variable documentation with assumptions and CT.

```python
doc = q.get_variable_documentation("DM", "RACE")
# Returns:
# {
#   'domain': 'DM',
#   'variable': 'RACE',
#   'documentation': [...chunks...],
#   'assumptions': [...rules...],
#   'controlled_terminology': [...values...]
# }
```

#### get_codelist_values()
Look up valid values for coded variable.

```python
sex_values = q.get_codelist_values(variable="SEX")
# Or with explicit codelist:
sex_values = q.get_codelist_values(codelist_code="C66742")

# Returns list of:
# {
#   'term_value': 'M',
#   'definition': 'Male',
#   'synonyms': 'MAN; MALE',
#   'term_code': 'C16576'
# }
```

#### get_mapping_assumptions()
Retrieve rules for domain/variable.

```python
assumptions = q.get_mapping_assumptions(
    domain="DM",
    variable="RFSTDTC",
    priority=2               # Filter by importance
)

# Returns list of:
# {
#   'domain': 'DM',
#   'variable': 'RFSTDTC',
#   'assumption': 'Can be derived as IC date, first dose, or earlier...',
#   'priority': 1,
#   'approach': 1
# }
```

#### get_context_for_mapping()
**Primary interface for AI orchestrator.** Returns complete context.

```python
context = q.get_context_for_mapping(
    domain="DM",
    variable="RACE",
    question="What if subject reports multiple races?"
)

# Returns:
# {
#   'domain': 'DM',
#   'variable': 'RACE',
#   'documentation': [...],
#   'controlled_terminology': [...],
#   'assumptions': [...],
#   'related_questions': [...]
# }
```

---

## Example Use Cases

### Use Case 1: Mapping DM.SEX

```python
# User question: "How do I determine SEX value?"

q = SDTMIGQuery(Config.db.get_connection_string())

# 1. Get variable documentation
doc = q.get_variable_documentation("DM", "SEX")

# 2. Get valid values
sex_values = q.get_codelist_values(variable="SEX")

# 3. Get assumptions
assumptions = q.get_mapping_assumptions("DM", "SEX")

# Present to user:
print("VARIABLE DOCUMENTATION:")
print(doc['documentation'][0]['content'])

print("\nVALID VALUES:")
for value in sex_values:
    print(f"  {value['term_value']}: {value['definition']}")

print("\nASSUMPTIONS:")
for assumption in assumptions:
    print(f"  - {assumption['assumption']}")

q.disconnect()
```

### Use Case 2: Handling Multiple Races in RACE

```python
# User question: "Subject reports multiple races. What should I do?"

context = q.get_context_for_mapping(
    "DM",
    "RACE",
    "What if subject reports multiple races?"
)

# Format for AI model:
prompt = f"""
Based on SDTM IG guidance:

VARIABLE: {context['variable']}

DOCUMENTATION:
{context['documentation']['documentation'][0]['content']}

VALID VALUES:
{context['controlled_terminology']}

RULES & ASSUMPTIONS:
{context['assumptions']}

QUESTION: How should I handle a subject reporting multiple races?

Provide a mapping decision with IG citations.
"""

# Send to AI model, get recommendation
# Model has full context to cite specific IG sections
```

### Use Case 3: RFSTDTC Derivation Decision

```python
# AI needs to decide: Should RFSTDTC = IC date or First Dose date?

context = q.get_context_for_mapping(
    "DM",
    "RFSTDTC",
    "Multiple approaches available"
)

# Context includes all three approaches from IG:
# Approach 1: IC date (Preferred in many sponsors)
# Approach 2: First dose date (Alternate in some trials)
# Approach 3: Earlier of both dates (Comprehensive)

# AI model can:
# 1. See all approaches in detail
# 2. Check which is more common (priority levels)
# 3. Check study-specific documented approach
# 4. Make informed decision with full context
```

---

## How the AI Orchestrator Uses This System

### Architecture

```
AI Orchestrator / Clinical Programming System
         ↓
   [Mapping Decision Task]
   "Map variable X in domain Y"
         ↓
[Query SDTM IG Database]
   get_context_for_mapping(domain, variable, question)
         ↓
[Retrieve from PostgreSQL]
- Documentation chunks
- Controlled terminology
- Mapping assumptions
- Multiple approaches (if applicable)
         ↓
[Format as Prompt Context]
   Max 4000 tokens of most relevant guidance
         ↓
[Send to AI Model]
   Claude / GPT-4 with full IG context
         ↓
[AI Generates Decision]
   - Mapping recommendation
   - IG citations (section references)
   - Reasoning from guidance
   - Confidence level
         ↓
[Document Decision]
   - Store in mapping table
   - Record source citations
   - Audit trail of IG consulted
         ↓
[Human Review]
   - Data manager reviews AI decision
   - Verifies against IG
   - Approves or overrides with feedback
```

### Integration Points

The AI orchestrator would call this system as follows:

```python
class SDTMMappingOrchestrator:
    """Main AI orchestration system."""
    
    def __init__(self, db_connection_string):
        self.ig_db = SDTMIGQuery(db_connection_string)
        self.ai_model = ClaudeAPI()  # or OpenAI, etc.
    
    def map_variable(self, domain: str, variable: str, 
                     source_data: Dict) -> MappingDecision:
        """
        Map a variable using SDTM IG guidance.
        
        1. Retrieve relevant IG context
        2. Prepare AI prompt with context
        3. Get mapping decision from AI
        4. Validate against IG
        5. Return decision with citations
        """
        
        # Step 1: Get IG context
        context = self.ig_db.get_context_for_mapping(
            domain, variable,
            question=f"How to map {variable} from {source_data}"
        )
        
        # Step 2: Build prompt
        prompt = self._format_mapping_prompt(context, source_data)
        
        # Step 3: Get AI decision
        decision_text = self.ai_model.generate(prompt)
        
        # Step 4: Parse decision
        decision = self._parse_decision(decision_text, context)
        
        # Step 5: Return
        return decision
    
    def _format_mapping_prompt(self, context: Dict, source_data: Dict) -> str:
        """Format complete mapping prompt with IG context."""
        
        prompt = f"""
Based on SDTM Implementation Guide:

VARIABLE: {context['domain']}.{context['variable']}

DOCUMENTATION:
{self._format_documentation(context['documentation'])}

VALID VALUES (Controlled Terminology):
{self._format_ct(context['controlled_terminology'])}

MAPPING RULES & ASSUMPTIONS:
{self._format_assumptions(context['assumptions'])}

RELATED GUIDANCE:
{self._format_related(context['related_questions'])}

---

SOURCE DATA:
{json.dumps(source_data, indent=2)}

TASK: Provide a mapping decision that:
1. Follows SDTM IG guidance exactly
2. Cites specific IG sections
3. Explains reasoning
4. Addresses edge cases
5. Includes validation logic

Decision:
"""
        return prompt
    
    def _parse_decision(self, decision_text: str, context: Dict):
        """Parse AI decision and extract mapping logic."""
        
        # Extract:
        # - Recommended value
        # - IG citations
        # - Reasoning
        # - Confidence
        # - Validation rules
        
        return MappingDecision(
            domain=context['domain'],
            variable=context['variable'],
            decision=decision_text,
            sources=context['documentation'],
            assumptions=context['assumptions']
        )
```

### Benefits

1. **Consistency:** Every decision references actual IG
2. **Traceability:** Know exactly which IG sections were consulted
3. **Compliance:** Audit trail for regulatory review
4. **Expertise:** IG is "in the loop" for every decision
5. **Validation:** Can check decisions against IG rules
6. **Updates:** New IG versions automatically improve decisions

---

## Development and Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Fails

```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in config.py or .env file
- Check database exists: `psql -l`
- Check user has permissions: `psql -c "\du"`

#### 2. pgvector Extension Not Found

```
ERROR: extension "vector" does not exist
```

**Solutions:**
- Install pgvector: See [Setup Step 2](#step-2-install-pgvector-extension)
- Gracefully degrades to keyword search without pgvector
- Most queries still work, just less semantic

#### 3. Embeddings Not Generated

For training, mock embeddings are used. For production:

**With OpenAI:**
```bash
export OPENAI_API_KEY=sk-...
python load_sdtm_ig.py
```

**With Claude:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export EMBEDDING_PROVIDER=claude
python load_sdtm_ig.py
```

#### 4. Large Content Files

If chunking seems slow or chunks seem off:

Adjust in `config.py`:
```python
CHUNK_SIZE = 250        # Smaller chunks
CHUNK_OVERLAP = 50      # Less overlap
```

Then reload: `python load_sdtm_ig.py`

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now logs will show detailed SQL, embeddings, etc.
```

### Testing

Run test queries:

```bash
python query_ig.py --examples
```

Check database directly:

```bash
# Connect
psql postgresql://sdtm_user@localhost/sdtm_ig_rag

# Check tables
\dt

# Count chunks
SELECT COUNT(*) FROM sdtm_ig_chunks;

# Check assumptions
SELECT domain, variable, COUNT(*) FROM mapping_assumptions 
GROUP BY domain, variable;

# Search for content
SELECT domain, section, LENGTH(content) 
FROM sdtm_ig_chunks 
WHERE LOWER(content) LIKE '%race%';
```

### Performance Optimization

For large content:

1. **Increase chunk batch size:**
   ```python
   Config.embeddings.BATCH_SIZE = 500
   ```

2. **Parallel embedding generation:**
   Implement with `concurrent.futures.ThreadPoolExecutor`

3. **Index optimization:**
   Add more aggressive indexes if queries slow

4. **Connection pooling:**
   Use psycopg2 connection pool for multiple threads

---

## Configuration Reference

See `config.py` for complete list of settings:

| Setting | Default | Description |
|---------|---------|-------------|
| PGHOST | localhost | Database hostname |
| PGPORT | 5432 | Database port |
| PGDATABASE | sdtm_ig_rag | Database name |
| CHUNK_SIZE | 500 | Chunk size in tokens |
| CHUNK_OVERLAP | 100 | Chunk overlap in tokens |
| TOP_K_CHUNKS | 5 | Chunks to retrieve |
| SIMILARITY_THRESHOLD | 0.6 | Min similarity (0-1) |
| EMBEDDING_PROVIDER | mock | "mock", "openai", or "claude" |
| EMBEDDING_DIMENSIONS | 1536 | Vector dimensions |

---

## License and Citation

This training exercise provides a realistic example of RAG architecture for clinical data standards (SDTM).

**For academic/research use, cite:**
- CDISC Study Data Tabulation Model (SDTM) Documentation
- IG - CDISC Implementation Guide
- pgvector: Open-source PostgreSQL vector extension

---

## Further Resources

- [CDISC Standards](https://www.cdisc.org/)
- [SDTM IG Official](https://www.cdisc.org/standards/foundational/sdtm)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Claude API Documentation](https://docs.anthropic.com/)

