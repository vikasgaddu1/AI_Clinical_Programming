# Chapter 4 Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

## Exercise 4.1: Explore the EVS REST API

- [ ] Queried C66731 (Sex) in the browser and read the JSON response
- [ ] Identified the `Extensible_List` property value
- [ ] Found the CDISC submission value ("F") in the synonyms array
- [ ] Made API calls from Python using `urllib`
- [ ] Queried C74457 (Race) and listed all member values
- [ ] Compared REST API results with static ct_lookup.csv
- [ ] Handled an API error for an invalid codelist code

## Exercise 4.2: Build a Codelist Fetcher

- [ ] `fetch_codelist_metadata()` -- returns codelist name and extensibility
- [ ] `fetch_codelist_members()` -- returns CDISC submission values
- [ ] `fetch_codelist()` -- combined metadata + values function
- [ ] `fetch_codelist_safe()` -- with HTTP and network error handling
- [ ] `build_synonym_map()` -- maps all known synonyms to submission values
- [ ] Tested with C66731 (Sex), C74457 (Race), and C66790 (Ethnicity)

## Exercise 4.3: Match Raw Data to CT

- [ ] Loaded distinct values from raw_dm.csv for SEX, RACE, ETHNIC
- [ ] Matched SEX values and identified synonym-based matches
- [ ] Matched RACE values and identified unmatched "Other Specify" values
- [ ] Matched ETHNIC values
- [ ] Generated a complete CT matching report
- [ ] Compared API matching vs static ct_lookup.csv matching

## Exercise 4.4: Handle Extensible vs Non-Extensible

- [ ] Checked extensibility for all DM codelists (SEX, RACE, ETHNIC, COUNTRY)
- [ ] Examined an extensible codelist (C66726 Dosage Form)
- [ ] Built routing function: ACCEPT_AS_EXTENSION vs REQUIRES_HUMAN_DECISION
- [ ] Built suggestion function for non-extensible unmatched values
- [ ] Connected extensibility to the Spec Builder decision workflow

## Exercise 4.5: Integrate with the Pipeline

- [ ] Read codelist references from the mapping spec
- [ ] Built hybrid lookup merging API synonyms + local CSV mappings
- [ ] Understood the value of both sources (authoritative + study-specific)
- [ ] Identified pipeline integration points

---

## Final Deliverables

### CT Matching Results Summary

| Variable | Codelist | Extensible | Raw Values | Matched | Unmatched |
|----------|----------|-----------|------------|---------|-----------|
| SEX | C66731 | | | | |
| RACE | C74457 | | | | |
| ETHNIC | C66790 | | | | |
| COUNTRY | C71113 | | | | |

### Key Insight: Static vs Live CT

When is the static ct_lookup.csv sufficient?
_________________________________________________________________

When do you need the REST API?
_________________________________________________________________

What's the best approach for a production pipeline?
_________________________________________________________________

### Extensibility Decision

If a raw value doesn't match a non-extensible codelist, what are your options?
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

---

## Self-Assessment

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
| Explaining what a REST API is and how to call one | [ ] | [ ] | [ ] |
| Querying the NCI EVS API for codelist metadata | [ ] | [ ] | [ ] |
| Extracting CDISC submission values from API responses | [ ] | [ ] | [ ] |
| Matching raw data values against CT using synonym maps | [ ] | [ ] | [ ] |
| Distinguishing extensible vs non-extensible codelists | [ ] | [ ] | [ ] |
| Routing unmatched values based on extensibility | [ ] | [ ] | [ ] |
| Building a hybrid lookup (API + local CSV) | [ ] | [ ] | [ ] |
