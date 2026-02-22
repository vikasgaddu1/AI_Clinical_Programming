# Exercise 3.3: Experiment with Chunking

## Objective
Use the `TextChunker` class to chunk the DM domain markdown and observe how chunk size and overlap affect the number and quality of chunks.

## Time: 30 minutes

---

## Steps

### Step 1: Load and Chunk the DM Domain File

```python
import sys
sys.path.insert(0, 'sdtm_ig_db')
from load_sdtm_ig import TextChunker

# Read the content
with open('sdtm_ig_db/sdtm_ig_content/dm_domain.md', 'r') as f:
    content = f.read()

print(f"Total document length: {len(content)} characters")

# Chunk by sections (markdown headings)
chunker = TextChunker()
section_chunks = chunker.chunk_by_sections(content)
print(f"\nSection-based chunks: {len(section_chunks)}")
for i, (text, meta) in enumerate(section_chunks[:5]):
    print(f"  Chunk {i+1}: {len(text)} chars | {meta}")
```

> Total document length: ___________ characters
> Number of section-based chunks: ___________

### Step 2: Try Different Chunk Sizes

Experiment with the overlap-based chunker at different settings:

```python
from config import Config

# Default: 500 tokens (~2000 chars)
default_chunks = chunker.chunk_with_overlap(content)
print(f"Default (500 tokens): {len(default_chunks)} chunks")

# Small chunks: 200 tokens (~800 chars)
Config.chunking.CHUNK_SIZE = 200
Config.chunking.CHUNK_OVERLAP = 50
small_chunks = chunker.chunk_with_overlap(content)
print(f"Small (200 tokens): {len(small_chunks)} chunks")

# Large chunks: 1000 tokens (~4000 chars)
Config.chunking.CHUNK_SIZE = 1000
Config.chunking.CHUNK_OVERLAP = 200
large_chunks = chunker.chunk_with_overlap(content)
print(f"Large (1000 tokens): {len(large_chunks)} chunks")

# Reset to default
Config.chunking.CHUNK_SIZE = 500
Config.chunking.CHUNK_OVERLAP = 100
```

> Default chunks: ___________
> Small chunks: ___________
> Large chunks: ___________

### Step 3: Examine Chunk Content

Look at what the RACE information looks like in different chunk sizes:

```python
# Find chunks containing "RACE" in each set
def find_race_chunks(chunks):
    race_chunks = [(i, text) for i, (text, _) in enumerate(chunks) if 'RACE' in text.upper()]
    return race_chunks

default_race = find_race_chunks(default_chunks)
small_race = find_race_chunks(small_chunks)
large_race = find_race_chunks(large_chunks)

print(f"RACE appears in {len(default_race)} default chunks")
print(f"RACE appears in {len(small_race)} small chunks")
print(f"RACE appears in {len(large_race)} large chunks")

# Show a small chunk that contains RACE
if small_race:
    idx, text = small_race[0]
    print(f"\nSmall chunk {idx} ({len(text)} chars):")
    print(text[:300])
```

> How many chunks contain RACE at each size?
> Default: ___________ | Small: ___________ | Large: ___________

### Step 4: Quality Assessment

Answer these questions for each chunk size:

**If someone searches for "How should RACE Other Specify be handled?"**

| Chunk Size | RACE chunk includes Other Specify approaches? | Chunk also includes irrelevant info? |
|-----------|-----------------------------------------------|--------------------------------------|
| Small (200) | | |
| Default (500) | | |
| Large (1000) | | |

> Which chunk size gives the best RACE retrieval? ___________
>
> Why? _________________________________________________________________

### Step 5: Compare Section-Based vs Overlap-Based

```python
# Find the RACE section in section-based chunks
section_race = [(i, text) for i, (text, meta) in enumerate(section_chunks)
                if 'RACE' in str(meta).upper() or '### RACE' in text]

if section_race:
    idx, text = section_race[0]
    print(f"Section-based RACE chunk: {len(text)} chars")
    print(f"Contains complete RACE section: {'Other Specify' in text}")
```

> Does the section-based chunk contain the complete RACE definition? ___________
>
> For SDTM IG content, which chunking strategy is better and why?
> _________________________________________________________________

---

## Key Insight

For structured documents like the SDTM IG where content is organized by variable (`### VARNAME`), **section-based chunking** preserves the natural boundaries and keeps each variable's information together. Overlap-based chunking is better for unstructured text (e.g., narrative protocol sections).

---

## What You Should Have at the End

- [ ] Chunked dm_domain.md at 3 different sizes
- [ ] Compared RACE retrieval quality across chunk sizes
- [ ] Compared section-based vs overlap-based chunking
- [ ] Formed an opinion on the best chunking strategy for SDTM IG content
