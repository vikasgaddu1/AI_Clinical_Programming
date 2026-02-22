# Chapter 4: Querying CDISC Controlled Terminology via REST API -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | 4-5 hours |
| Format | Instructor-led workshop (concepts + hands-on Python exercises) |
| Audience | Clinical programmers who completed Chapters 1-3 |
| Prerequisites | Python 3.11+, familiarity with IGClient (Ch.3), internet access |
| Materials | `macros/ct_lookup.csv`, `r_functions/function_registry.json`, `study_data/raw_dm.csv` |

## Key Teaching Message

In Chapter 3 you built a RAG system that retrieves IG text. But the IG only says _which_ codelist a variable uses (e.g., "C66731"). It doesn't give you the authoritative, up-to-date list of allowed values -- NCI EVS does. This chapter teaches you to query the NCI EVS REST API to get the official CDISC controlled terminology values, match them against your raw data, and handle the extensible vs non-extensible distinction that determines whether you can add your own values.

---

## Module 4.1: Why Live CT Lookup? The Problem with Static Files (30 min)

### Talking Points

1. **Start with the current approach:**
   "Open `macros/ct_lookup.csv`. This is a hand-curated mapping file -- 55 entries across 4 codelists. It works for DM. But what happens when you need AE, VS, LB? That's 100+ codelists. Maintaining a static CSV becomes unsustainable."

2. **Show the gap:**
   - CDISC publishes new CT quarterly (March, June, September, December)
   - Your static file was created at a point in time -- it can drift
   - The IG says "SEX uses codelist C66731" but never lists the actual allowed values
   - The IG says "RACE uses codelist C74457" -- but are these values current?

3. **The solution: NCI EVS REST API**
   - NCI's Enterprise Vocabulary Services hosts ALL CDISC controlled terminology
   - Free, public REST API -- no API key required
   - Always current (updated with each CDISC CT publication)
   - Base URL: `https://api-evsrest.nci.nih.gov/api/v1/`

4. **What is a REST API?**
   - REST = **RE**presentational **S**tate **T**ransfer
   - A way to request data over HTTP -- the same protocol your browser uses
   - You send a URL (the "request"), the server sends back JSON (the "response")
   - No authentication, no SDK, no installation -- just a URL and Python's `urllib`

### Demo: Open in Browser

Open `https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C66731?include=summary` in a browser. Show the JSON response. Point out:
- `"name": "CDISC SDTM Sex of Individual Terminology"` -- this is the codelist name
- `"Extensible_List": "No"` -- SEX is non-extensible (only CT values allowed)
- The `synonyms` array -- shows "SEX" as the CDISC preferred term

### Transition
"Now let's understand the API structure and how to get the actual allowed values."

---

## Module 4.2: NCI EVS REST API Structure (45 min)

### Talking Points

1. **Two key endpoints for CT work:**

   | Endpoint | Purpose | Example |
   |----------|---------|---------|
   | `GET /concept/ncit/{code}?include=summary` | Get codelist metadata (name, extensibility, definition) | `/concept/ncit/C66731?include=summary` |
   | `GET /subset/ncit/{code}/members?include=summary` | Get all allowed values in a codelist | `/subset/ncit/C66731/members?include=summary` |

   **Critical distinction:** A codelist code (like C66731) is a _concept_ in NCIt. Its allowed values are the _subset members_.

2. **Understanding the response structure:**

   **Codelist metadata** (`/concept/ncit/C66731`):
   ```json
   {
     "code": "C66731",
     "name": "CDISC SDTM Sex of Individual Terminology",
     "properties": [
       {"type": "Extensible_List", "value": "No"},
       {"type": "Contributing_Source", "value": "CDISC"},
       {"type": "Publish_Value_Set", "value": "Yes"}
     ]
   }
   ```

   **Codelist members** (`/subset/ncit/C66731/members`):
   Each member is a concept with its own code, name, and synonyms. The CDISC submission value is in the `synonyms` array:
   ```json
   {
     "code": "C16576",
     "name": "Female",
     "synonyms": [
       {"name": "F", "termType": "PT", "source": "CDISC", "code": "SDTM-SEX"}
     ]
   }
   ```
   The submission value for SDTM is the synonym where `source == "CDISC"` and `termType == "PT"` and `code` matches the SDTM codelist short name (e.g., `"SDTM-SEX"`).

3. **The `include` parameter:**
   - `minimal` -- just code and name (fast, small response)
   - `summary` -- code, name, synonyms, definitions, properties
   - `full` -- everything including parents, children, associations

4. **Live demo -- walk through the three-step workflow:**
   ```
   Step 1: IG says RACE uses codelist C74457
   Step 2: Query /concept/ncit/C74457 → get metadata, check Extensible_List
   Step 3: Query /subset/ncit/C74457/members → get allowed values
   ```

### Key Concept -- Draw on Whiteboard

```
SDTM IG               NCI EVS REST API              Raw Data
┌──────────┐         ┌──────────────────┐          ┌──────────┐
│ RACE     │ ──C74457──> │ /concept/ncit/  │          │ White    │
│ CT: C74457│         │   C74457         │          │ Black    │
│           │         │ Extensible: No   │          │ Asian    │
└──────────┘         │                  │          │ Filipino │
                     │ /subset/ncit/    │          └──────────┘
                     │   C74457/members │
                     │ → WHITE          │     Match: White→WHITE ✓
                     │ → ASIAN          │     Match: Black→BLACK OR AFRICAN AMERICAN ✓
                     │ → BLACK OR...    │     Match: Asian→ASIAN ✓
                     │ → AMERICAN...    │     Match: Filipino→??? (no match)
                     │ → NATIVE HAW...  │
                     │ → OTHER          │     Non-extensible → must map to OTHER
                     │ → NOT REPORTED   │       or flag for review
                     │ → UNKNOWN        │
                     └──────────────────┘
```

---

## Module 4.3: Extensible vs Non-Extensible Codelists (30 min)

### Talking Points

1. **The regulatory significance:**
   - **Non-extensible** (e.g., SEX C66731, RACE C74457): ONLY the values defined in the codelist are allowed. Any value not in the codelist is a validation error.
   - **Extensible** (e.g., Dosage Form C66726): The codelist provides standard values, but sponsors CAN add their own values if needed. Additional values should still follow naming conventions.

2. **How to check programmatically:**
   ```python
   # In the concept response, look for the Extensible_List property
   props = concept_data.get("properties", [])
   extensible = any(
       p["type"] == "Extensible_List" and p["value"] == "Yes"
       for p in props
   )
   ```

3. **What this means for the CT matching workflow:**

   | Raw Value | CT Match? | Extensible? | Action |
   |-----------|-----------|-------------|--------|
   | "White" | Yes (WHITE) | N/A | Map to WHITE |
   | "Filipino" | No | No (C74457) | Must map to closest CT term (ASIAN) or OTHER -- requires human decision |
   | "Filipino" | No | Yes (hypothetical) | Can keep "FILIPINO" as a sponsor-defined extension |

4. **Real examples from this project:**
   - C66731 (SEX): Extensible = **No** -- only F, M, U, INTERSEX allowed
   - C74457 (RACE): Extensible = **No** -- only the 8 standard terms allowed
   - C66790 (ETHNICITY): Extensible = **No** -- only 4 terms allowed
   - C66726 (Dosage Form): Extensible = **Yes** -- sponsor can add custom forms

### Discussion Question
"Your raw data has `RACE = 'Filipino'`. The codelist C74457 is non-extensible. What do you do? This is exactly the decision the Spec Builder agent flags for human review (RACE approach A/B/C from Chapter 2)."

---

## Module 4.4: Building the CT Matching Pipeline (45 min)

### Talking Points

1. **The end-to-end workflow in Python:**

   ```
   1. Read the mapping spec → find variables with codelist codes
   2. For each codelist code:
      a. GET /concept/ncit/{code} → check extensibility
      b. GET /subset/ncit/{code}/members → get allowed values
      c. Extract CDISC submission values from synonyms
   3. Read raw data → get distinct values for that variable
   4. Match: for each raw value, find the closest CT value
      - Exact match (case-insensitive)
      - Known abbreviation match (from synonyms)
      - Fuzzy/manual match (flag for review)
   5. If no match found:
      - Extensible codelist → accept as sponsor extension
      - Non-extensible → flag for human decision
   ```

2. **Walk through the matching logic:**
   ```python
   def match_raw_to_ct(raw_values, ct_members):
       """Match raw data values to CDISC CT submission values."""
       matches = {}
       unmatched = []

       # Build lookup: all synonyms → submission value
       synonym_map = {}
       for member in ct_members:
           submission_val = get_cdisc_submission_value(member)
           # Add the concept name and all synonyms as keys
           synonym_map[member["name"].upper()] = submission_val
           for syn in member.get("synonyms", []):
               synonym_map[syn["name"].upper()] = submission_val

       for raw in raw_values:
           upper = raw.strip().upper()
           if upper in synonym_map:
               matches[raw] = synonym_map[upper]
           else:
               unmatched.append(raw)

       return matches, unmatched
   ```

3. **How this improves on the static ct_lookup.csv:**

   | Aspect | Static CSV | REST API approach |
   |--------|-----------|-------------------|
   | Maintenance | Manual updates quarterly | Always current |
   | Coverage | 4 codelists, 55 entries | 1,300+ CDISC codelists |
   | Synonym matching | Only hand-entered synonyms | All NCI-registered synonyms |
   | Extensibility check | Not captured | Programmatic |
   | Audit trail | None | API response logged |

4. **Integration with the orchestrator:**
   The CT matching function can be called by:
   - The Spec Builder agent (to pre-populate codelist mappings)
   - The Validation Agent (to verify final dataset values)
   - The MCP `ct_lookup` tool (to enhance beyond static CSV)

### Transition
"Now let's build this step by step in the exercises."

---

## Module 4.5: Hands-On Exercises (120 min)

### Exercise Flow

| Exercise | Duration | Focus |
|----------|----------|-------|
| 4.1: Explore the EVS REST API | 20 min | Manual API calls, understand response structure |
| 4.2: Build a Codelist Fetcher | 30 min | Python function to fetch CT values for any codelist |
| 4.3: Match Raw Data to CT | 30 min | Build matching logic, handle synonyms |
| 4.4: Handle Extensible vs Non-Extensible | 25 min | Check extensibility, route unmatched values |
| 4.5: Integrate with the Pipeline | 15 min | Connect to existing ct_lookup.csv and function registry |

### Facilitation Tips

- **Exercise 4.1:** If internet is slow, have pre-downloaded JSON responses as fallback. The key insight is understanding the two-endpoint pattern (concept for metadata, subset/members for values).
- **Exercise 4.2:** Participants write ~30 lines of Python. The tricky part is extracting the CDISC submission value from the synonyms array -- multiple synonyms exist, they need to filter by `source == "CDISC"` and `termType == "PT"`.
- **Exercise 4.3:** The matching exercise uses real raw_dm.csv data. Expect messy matches: "CAUCASIAN" should match WHITE, "AFRICAN AMERICAN" should match "BLACK OR AFRICAN AMERICAN". Some participants will want fuzzy matching -- acknowledge it but keep scope to exact + synonym matching.
- **Exercise 4.4:** The extensibility exercise is conceptual + code. The key teaching moment: "Filipino" with a non-extensible codelist MUST be mapped or flagged, never accepted as-is.
- **Exercise 4.5:** Brief integration exercise showing how the REST approach could replace or supplement the static ct_lookup.csv.

---

## Wrap-Up (15 min)

### Discussion
1. "When would you use the static ct_lookup.csv vs the live REST API?"
2. "How does knowing extensibility change your mapping decisions?"
3. "Could the Spec Builder agent call this API automatically? What would the workflow look like?"

### Connection to Other Chapters
- **Chapter 3 (RAG):** The IG told us WHICH codelist to use. The REST API tells us WHAT values are in it. They complement each other.
- **Capstone:** The Spec Builder agent currently uses ct_lookup.csv. This REST approach could replace or augment it, making the pipeline work for any domain without manual CSV maintenance.

---

## Slide Deck Outline (for `slides/chapter_4_slides.pptx`)

| Slide # | Title | Content |
|---------|-------|---------|
| 1 | Title | "Chapter 4: Querying CDISC CT via REST API" |
| 2 | Learning Objectives | 6 objectives |
| 3 | The Problem | "ct_lookup.csv has 55 entries. CDISC has 1,300+ codelists." |
| 4 | What is a REST API? | HTTP request → JSON response diagram |
| 5 | NCI EVS REST API | Base URL, no auth, free, always current |
| 6 | Two Key Endpoints | /concept for metadata, /subset/members for values |
| 7 | Live Demo: Browser | C66731 in browser → JSON response |
| 8 | Response Structure | Codelist metadata fields |
| 9 | Members Response | Concept code, name, synonyms with CDISC source |
| 10 | Extracting Submission Values | Filter synonyms by source=CDISC, termType=PT |
| 11 | Extensible vs Non-Extensible | Definition, examples, regulatory significance |
| 12 | How to Check Extensibility | Extensible_List property in API response |
| 13 | The Matching Workflow | 5-step diagram: IG → API → raw data → match → route |
| 14 | Matching Logic | Exact match → synonym match → unmatched → route |
| 15 | Static CSV vs REST API | Comparison table |
| 16 | Integration Points | Spec Builder, Validation Agent, MCP tool |
| 17-21 | Exercise slides | One per exercise |
| 22 | Key Takeaways | Live CT, extensibility, synonym matching |
| 23 | What's Next | Capstone: full pipeline integration |

---

## Timing Summary

| Module | Duration | Running Total |
|--------|----------|---------------|
| 4.1: Why Live CT Lookup? | 30 min | 0:30 |
| 4.2: API Structure | 45 min | 1:15 |
| 4.3: Extensible vs Non-Extensible | 30 min | 1:45 |
| -- Break -- | 15 min | 2:00 |
| 4.4: CT Matching Pipeline | 45 min | 2:45 |
| -- Break -- | 15 min | 3:00 |
| 4.5: Exercises | 120 min | 5:00 |
| Wrap-up + Q&A | 15 min | 5:15 |
