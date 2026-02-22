# Chapter 3 Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Exercise 3.1: Explore IG Content Files

- [ ] Read dm_domain.md and identified the structure (overview -> variables -> summary)
- [ ] Counted the number of variable sections
- [ ] Identified natural chunk boundaries (`### VARNAME`)
- [ ] Searched for "partial date" and understood keyword search limitations

## Exercise 3.2: Use the File-Based IG Client

- [ ] Successfully ran IGClient to get all DM variables
- [ ] Retrieved required variables and CT-controlled variables
- [ ] Got detailed RACE variable information
- [ ] Compared results with Chapter 1 (NotebookLM) findings
- [ ] Observed the AE domain gap (empty result)

## Exercise 3.3: Experiment with Chunking

- [ ] Chunked dm_domain.md at 3 different sizes (small, default, large)
- [ ] Compared RACE retrieval quality across chunk sizes
- [ ] Compared section-based vs overlap-based chunking
- [ ] Formed an opinion on the best strategy for SDTM IG content

## Exercise 3.4: Build an AE Domain Content File

- [ ] Created `sdtm_ig_db/sdtm_ig_content/ae_domain.md`
- [ ] Included at least 8 variables with proper structure
- [ ] Added a summary table at the end
- [ ] Tested with IGClient: `get_domain_variables("AE")` returns results
- [ ] Tested: `get_required_variables("AE")` and `get_variable_detail("AE", "AETERM")`

## Exercise 3.5: Database Mode (Optional)

- [ ] Set up PostgreSQL with pgvector schema
- [ ] Loaded IG content into the database
- [ ] Ran example queries successfully
- [ ] Compared database results with file-based results

---

## Final Deliverables

### Keyword vs Semantic Search Comparison

When is keyword search sufficient?
_________________________________________________________________

When do you need semantic search?
_________________________________________________________________

### Chunking Strategy Recommendation

For SDTM IG content, which chunking strategy is best and why?
_________________________________________________________________
_________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Explaining what RAG is and why it matters | [ ] | [ ] | [ ] |
| Differentiating keyword vs semantic search | [ ] | [ ] | [ ] |
| Understanding how chunking affects retrieval | [ ] | [ ] | [ ] |
| Using the IGClient Python API | [ ] | [ ] | [ ] |
| Extending the system to a new domain (markdown file) | [ ] | [ ] | [ ] |
| Understanding embeddings and cosine similarity | [ ] | [ ] | [ ] |
