# SDTM IG RAG System - Architecture Document

## Executive Summary

This is a production-ready RAG (Retrieval-Augmented Generation) system for semantic search and lookup of SDTM (Study Data Tabulation Model) Implementation Guide content. It enables AI models to retrieve relevant clinical data mapping guidance when making SDTM decisions.

**Key Insight:** The system bridges the gap between raw SDTM IG documentation and AI decision-making, ensuring every mapping decision is grounded in official IG guidance with complete citation trails.

---

## Problem Statement

### Without RAG
- AI models hallucinate or invent SDTM rules
- No audit trail of which IG sections guided decisions
- Hard to update when IG changes
- Risk of non-compliance with IG requirements

### With RAG
- AI retrieves actual IG guidance for every question
- Complete citation trail for compliance review
- Easy to update with new IG versions
- Decisions provably based on official guidance

---

## System Architecture

### High-Level Flow

```
Raw SDTM IG (Markdown Files)
    ↓ [Load & Process]
    
Content Chunking
    • Split into ~500 token semantic segments
    • Preserve section structure
    • Overlap for context continuity
    
    ↓ [Transform]
    
Embedding Generation
    • Mock embeddings for training (deterministic hash-based)
    • OpenAI embeddings for production
    • Claude embeddings for production (future)
    
    ↓ [Store]
    
PostgreSQL + pgvector
    • Chunks table: content + embeddings + metadata
    • Controlled Terminology: valid values + definitions
    • Mapping Assumptions: rules + priorities + approaches
    
    ↓ [Query]
    
AI Orchestrator
    1. Receives mapping question
    2. Queries IG database
    3. Retrieves relevant chunks (semantic search)
    4. Gets valid values (controlled terminology)
    5. Gets applicable rules (assumptions)
    6. Assembles context prompt
    7. Calls AI model (Claude/GPT-4)
    8. AI returns decision with IG citations
    
    ↓
    
Human Review
    • Data manager reviews decision
    • Verifies against IG citations
    • Approves or overrides with feedback
    
    ↓
    
Mapping Result
    • Domain.Variable = mapped value
    • Source: IG section X.Y.Z
    • Reasoning: [from AI]
    • Confidence: [high/medium/low]
```

---

## Database Design

### Three-Table Schema

#### 1. sdtm_ig_chunks
Stores semantic segments of IG documentation with embeddings.

**Purpose:** Enable semantic search for relevant guidance

**Key Columns:**
- `embedding (vector[1536])` - Enables similarity search
- `domain` - Filter by SDTM domain (DM, AE, LB, etc.)
- `section` - Group by major section
- `chunk_type` - Distinguish overview vs. variable_def vs. assumption
- `sequence` - Maintain document order

**Example Chunk:**
```
domain: "DM"
section: "Core DM Variables"
subsection: "RACE - Race"
content: "RACE captures subject's racial category from CDISC C74456. 
         When multiple races reported, use RACE='MULTIPLE' and record 
         individual races in SUPPDM with QNAM='RACE1', 'RACE2'..."
embedding: [0.123, -0.456, 0.789, ...]  # 1536 dimensions
chunk_type: "variable_definition"
sequence: 12
```

#### 2. controlled_terminology
Stores valid codelist values with definitions and synonyms.

**Purpose:** Enable lookup of what values are allowed for each variable

**Key Columns:**
- `codelist_code` - NCI code (C66742, C74456, etc.)
- `codelist_name` - Friendly name (Sex, Race, Ethnicity)
- `term_value` - Actual SDTM value (M, F, U, WHITE, ASIAN, etc.)
- `definition` - What this value means
- `synonyms` - Alternate acceptable inputs

**Example Record:**
```
codelist_code: "C66742"
codelist_name: "Sex"
term_value: "M"
term_code: "C16576"
definition: "Biological male"
synonyms: "MALE; MAN; MALE"
```

#### 3. mapping_assumptions
Documents domain/variable-level rules and multiple valid approaches.

**Purpose:** Capture the "how to map this variable" rules from IG

**Key Columns:**
- `domain`, `variable` - What this rule applies to
- `assumption_text` - The rule itself
- `priority` - 1=Critical, 2=Important, 3=Informational
- `approach_number` - For multiple valid approaches (1, 2, 3, ...)
- `ig_reference` - Citation to IG section

**Example Records:**
```
domain: "DM"
variable: "RFSTDTC"
assumption: "RFSTDTC can be derived as IC date, first dose, or earlier. 
            Must apply consistently."
priority: 1  # Critical decision
approach: 1
ig_reference: "IG Section 2.3.1.1"

---

domain: "DM"
variable: "RFSTDTC"
assumption: "Use informed consent date (Approach 1) for studies with 
            strict IC requirements."
priority: 2
approach: 1
ig_reference: "IG Section 2.3.1.1"

---

domain: "DM"
variable: "RFSTDTC"
assumption: "Use first dose date (Approach 2) for dose-tracking studies."
priority: 2
approach: 2
ig_reference: "IG Section 2.3.1.1"
```

### Index Strategy

For performance:

```sql
-- Full-text search on content
CREATE INDEX idx_chunks_content ON sdtm_ig_chunks 
  USING GIN (to_tsvector('english', content));

-- Domain/variable filtering
CREATE INDEX idx_chunks_domain_section 
  ON sdtm_ig_chunks(domain, section);

-- Vector similarity search (pgvector)
CREATE INDEX idx_chunks_embedding 
  ON sdtm_ig_chunks USING ivfflat (embedding vector_cosine_ops);

-- Assumption lookup
CREATE INDEX idx_assumptions_domain_variable 
  ON mapping_assumptions(domain, variable);
```

---

## Content Chunking Strategy

### Why Chunking Matters

Raw documentation is too large for AI context windows. Smart chunking:
- Preserves semantic boundaries (don't split concepts)
- Maintains readability (not random word breaks)
- Enables relevance ranking (small units easier to score)
- Creates overlap (context continuity)

### Algorithm

1. **Identify Semantic Boundaries**
   - Split by markdown headings (# ## ###)
   - Preserve hierarchical structure
   - Track section/subsection context

2. **Respect Size Limits**
   - Target: ~500 tokens (~2000 characters)
   - Maximum: 3000 characters (safety limit)
   - Minimum: 100 characters (no fragments)

3. **Create Overlap**
   - 100 tokens overlap between chunks
   - Ensures context continuity
   - Helps with semantic boundaries

4. **Add Metadata**
   - domain: extracted from filename
   - section: first level heading
   - subsection: second level heading
   - chunk_type: auto-detected or manual
   - sequence: order in document

### Example: DM.RACE Variable

Source IG content:
```
### RACE - Race

The RACE variable captures subject's racial or ethnic background. 
[200 words of definition]

#### Controlled Terminology
RACE uses CDISC C74456. Valid values include:
- AMERICAN INDIAN OR ALASKA NATIVE
- ASIAN
- BLACK OR AFRICAN AMERICAN
[list of 8 values]

#### Multiple Valid Approaches for Race Mapping

**Approach 1: Single Race Selection (Standard)**
[250 words of explanation]

**Approach 2: Multiple Races Collapsed to "MULTIPLE"**
[300 words of explanation with SUPPDM example]

**Approach 3: "Other Specify" with Reclassification**
[250 words of explanation]
```

Chunked into:
```
Chunk 1: "RACE variable definition and overview"
  - domain: "DM"
  - subsection: "RACE - Race"
  - chunk_type: "variable_definition"
  - sequence: 1

Chunk 2: "RACE Controlled Terminology and valid values"
  - domain: "DM"
  - subsection: "RACE - Race"
  - chunk_type: "controlled_terminology"
  - sequence: 2

Chunk 3: "Approach 1 - Single Race Selection"
  - domain: "DM"
  - subsection: "RACE - Race"
  - chunk_type: "mapping_approach"
  - sequence: 3
  - approach_number: 1

Chunk 4: "Approach 2 - Multiple Races to MULTIPLE"
  - domain: "DM"
  - subsection: "RACE - Race"
  - chunk_type: "mapping_approach"
  - sequence: 4
  - approach_number: 2

Chunk 5: "Approach 3 - Other Specify Reclassification"
  - domain: "DM"
  - subsection: "RACE - Race"
  - chunk_type: "mapping_approach"
  - sequence: 5
  - approach_number: 3
```

---

## Embedding Strategy

### For Training (Current Implementation)

Uses **mock embeddings** - deterministic hash-based vectors:

```python
def mock_embedding(text):
    # Use text hash as seed
    hash_value = hash(text)
    random.seed(hash_value)
    
    # Generate consistent random vector
    embedding = [random.gauss(0, 0.3) for _ in range(1536)]
    
    # Normalize to unit vector
    return normalize(embedding)
```

**Characteristics:**
- Identical text → identical embedding (reproducible)
- Similar text → similar but not identical embeddings
- Fast (no API calls)
- No costs
- Good for development/testing

### For Production

#### Option 1: OpenAI text-embedding-3-small
```python
response = openai.Embedding.create(
    input=text,
    model="text-embedding-3-small"
)
embedding = response['data'][0]['embedding']  # 1536 dimensions
```

**Costs:** ~$0.02 per 1M tokens (~$50 for typical IG)

#### Option 2: Claude Embeddings API (Future)
```python
response = anthropic.Embeddings.embed(
    model="claude-embedding-text",
    input=text
)
embedding = response.embedding
```

**Advantages:** 
- Trained on more recent data
- Better context understanding
- Claude API consistency

### Similarity Search Mechanism

**With pgvector:**
```sql
SELECT * FROM sdtm_ig_chunks
ORDER BY embedding <-> query_embedding
LIMIT 5;
```

Uses **cosine similarity** (pgvector default):
- Values: 0.0 to 1.0
- 1.0 = identical
- 0.6-0.8 = semantically similar
- 0.3-0.6 = somewhat related
- <0.3 = unrelated

---

## Query Interface

### Core Query Functions

#### 1. Semantic Search
```python
q.semantic_search(
    query="How do I map RACE?",
    domain="DM",        # optional filter
    top_k=5,            # number of results
    threshold=0.6       # min similarity
)
```

Returns: Top-K most relevant chunks

#### 2. Variable Documentation
```python
q.get_variable_documentation("DM", "RACE")
```

Returns:
- Definition chunks
- All assumptions
- Controlled terminology
- All approaches (if multiple)

#### 3. Controlled Terminology Lookup
```python
q.get_codelist_values(variable="SEX")
```

Returns: List of valid values with definitions

#### 4. Mapping Assumptions
```python
q.get_mapping_assumptions(
    domain="DM",
    variable="RFSTDTC",
    priority=2  # Critical (1) or important (2)
)
```

Returns: Applicable rules in priority order

#### 5. Complete Mapping Context (Primary Interface)
```python
context = q.get_context_for_mapping(
    "DM",
    "RACE",
    "What if multiple races reported?"
)
```

Returns:
```python
{
    'domain': 'DM',
    'variable': 'RACE',
    'documentation': [chunks],
    'controlled_terminology': [values],
    'assumptions': [rules],
    'related_questions': [similar_queries]
}
```

---

## AI Orchestrator Integration

### How the AI Uses This System

```python
class SDTMMappingOrchestrator:
    def map_variable(self, domain, variable, source_data):
        # 1. Query IG database
        context = ig_db.get_context_for_mapping(domain, variable)
        
        # 2. Build prompt with context
        prompt = f"""
Based on SDTM IG Guidance:

VARIABLE: {domain}.{variable}

DOCUMENTATION:
{context['documentation']}

CONTROLLED TERMINOLOGY:
{context['controlled_terminology']}

MAPPING ASSUMPTIONS:
{context['assumptions']}

QUESTION: How should I map {source_data}?

Provide a mapping decision that:
- Cites specific IG sections
- Lists all valid approaches
- Explains your choice
- Includes validation rules
"""
        
        # 3. Call AI model
        decision = claude.generate(prompt)
        
        # 4. Return with citations
        return {
            'value': decision.extracted_value,
            'reasoning': decision.explanation,
            'citations': context['documentation'].references,
            'confidence': decision.confidence_level,
            'alternatives': decision.alternative_approaches
        }
```

### Why This Matters

1. **Consistency:** Every decision references actual IG
2. **Traceability:** Know exactly which IG sections were consulted
3. **Compliance:** Audit trail for regulatory review
4. **Flexibility:** Easy to update with new IG versions
5. **Quality:** AI reasoning grounded in official guidance

---

## Real-World Scenarios

### Scenario 1: Simple Mapping - SEX Variable

**Input:**
```
Source system value: "Male"
Target: SDTM DM.SEX
```

**Process:**
1. Query: `get_context_for_mapping("DM", "SEX")`
2. Retrieve:
   - SEX definition from DM documentation
   - C66742 codelist: {M, F, U}
   - Assumptions: "Required, self-reported or from medical history"
3. Build prompt with guidance
4. AI recommends: `M` (confidence: high)
5. Citation: CDISC IG Section 2.3 - DM Variables

---

### Scenario 2: Complex Decision - RACE with Multiple Values

**Input:**
```
Source: Subject reports ["White", "Asian"]
Target: SDTM DM.RACE
```

**Process:**
1. Query: `get_context_for_mapping("DM", "RACE")`
2. Retrieve:
   - RACE variable definition
   - All 9 codelist values
   - **THREE approaches from IG:**
     * Approach 1: Use RACE="MULTIPLE", record races in SUPPDM
     * Approach 2: Use first/primary race, others in SUPPDM
     * Approach 3: Create multiple DM records (not standard)
   - Assumptions indicating Approach 1 is recommended
3. Build prompt showing all approaches
4. AI recommends: Approach 1 with reasoning
5. Citations: Multiple IG sections + SUPPDM guidance

---

### Scenario 3: Derivation Rule - RFSTDTC

**Input:**
```
IC date: 2024-01-15
First dose: 2024-01-16
Target: SDTM DM.RFSTDTC
```

**Process:**
1. Query: `get_context_for_mapping("DM", "RFSTDTC")`
2. Retrieve:
   - RFSTDTC definition
   - **THREE approaches:**
     * Approach 1: IC date (Preferred, subject protection)
     * Approach 2: First dose (Early phase studies)
     * Approach 3: Earlier date (Comprehensive)
   - Assumptions with priorities:
     * Priority 1: "Must choose ONE and apply consistently"
     * Priority 2: IC date preferred for most studies
     * Priority 2: First dose for some early studies
3. Build prompt with approaches
4. AI checks protocol context
5. AI recommends: IC date = 2024-01-15 (most common)
6. Citations: IG Section 2.3.1.1 + approach documentation

---

## Configuration and Deployment

### Development Environment
```bash
EMBEDDING_PROVIDER=mock
PGHOST=localhost
LOG_LEVEL=DEBUG
```

### Production Environment
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
PGHOST=prod-database.example.com
LOG_LEVEL=INFO
MAX_CONTEXT_TOKENS=4000
```

### Scaling Considerations

1. **Content Scale:**
   - DM domain: ~40KB markdown → ~30 chunks
   - Full IG (all domains): ~500KB → ~500 chunks
   - Reasonable DB size for PostgreSQL

2. **Query Scale:**
   - Typical: 10-50 queries per study
   - Vector similarity search: <100ms per query
   - No performance issues expected

3. **Update Frequency:**
   - Typically annual (new IG versions)
   - Can re-load without downtime
   - Version control recommended

---

## Example: Complete Workflow

### Step 1: Setup (One-time)
```bash
python setup_db.py           # Create schema
python load_sdtm_ig.py       # Load content
python query_ig.py --examples # Verify
```

### Step 2: Orchestrator Makes Decision
```python
from orchestrator_example import SDTMMappingOrchestrator

orch = SDTMMappingOrchestrator()

# Decide how to map a RACE value
decision = orch.decide_race_mapping(["White", "Asian"])

print(orch.format_decision_report(decision))
# Output: Full report with IG citations, approaches, rules
```

### Step 3: Human Reviews
Data manager:
- Reads decision report
- Verifies IG citations
- Checks validation rules
- Approves or provides feedback

### Step 4: Result Stored
```python
{
    'domain': 'DM',
    'variable': 'RACE',
    'source_value': ['White', 'Asian'],
    'mapped_value': 'MULTIPLE',
    'approach': 'Approach 2 - SUPPDM supplement',
    'ig_citation': 'IG Section 2.3 - DM Variables',
    'confidence': 'high',
    'reviewed_by': 'john.doe@company.com',
    'timestamp': '2024-01-20T10:30:00'
}
```

---

## Files and Components Summary

| File | Purpose | Size |
|------|---------|------|
| `config.py` | Centralized configuration | 6KB |
| `setup_db.py` | Database schema creation | 13KB |
| `load_sdtm_ig.py` | Content loader with chunking | 26KB |
| `query_ig.py` | Query interface | 21KB |
| `orchestrator_example.py` | AI orchestration example | 17KB |
| `dm_domain.md` | DM domain documentation | 22KB |
| `general_assumptions.md` | Cross-domain rules | 17KB |
| **Total** | **Complete RAG system** | **~122KB** |

---

## Future Enhancements

1. **Multi-Domain Support**
   - Load AE, LB, EX domains
   - Cross-domain linkage (e.g., DM → AE)

2. **Version Control**
   - Track IG version changes
   - Diff between versions
   - Backwards compatibility

3. **Learning from Reviews**
   - Track which recommendations were approved
   - Retrain model or adjust prompts
   - Continuous improvement

4. **Advanced Search**
   - Faceted search by domain/variable
   - Full-text + semantic hybrid search
   - Query suggestion/autocomplete

5. **Governance**
   - Audit trail of all decisions
   - Compliance reporting
   - Decision approval workflows

---

## Conclusion

This RAG system solves a critical problem: keeping AI-generated SDTM mappings grounded in official guidance. By maintaining a queryable database of chunked IG content with semantic embeddings, the system enables:

- **Consistent mappings** across studies
- **Explainable decisions** with citations
- **Regulatory compliance** with audit trails
- **Easy updates** when IG changes
- **Domain expertise** directly in the mapping process

The modular design allows easy extension to other SDTM domains, other standards (e.g., ADaM, ADAM-IG), or completely different clinical programming domains.

