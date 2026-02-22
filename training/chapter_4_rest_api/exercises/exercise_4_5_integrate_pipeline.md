# Exercise 4.5: Integrate with the Pipeline

## Objective
Connect the REST API-based CT matching with the existing pipeline components: the mapping spec, the function registry, and the static ct_lookup.csv. Build a hybrid approach that uses the API as the authoritative source while retaining local study-specific mappings.

## Time: 15 minutes

---

## Steps

### Step 1: Read the Mapping Spec

Check what codelists the spec references:

```python
import json

# Try to load the approved spec; fall back to draft
spec_path = "orchestrator/outputs/specs/dm_mapping_spec_approved.json"
try:
    with open(spec_path) as f:
        spec = json.load(f)
except FileNotFoundError:
    spec_path = "orchestrator/outputs/specs/dm_mapping_spec.json"
    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except FileNotFoundError:
        print("No spec found -- run the pipeline first (spec_build stage)")
        spec = None

if spec:
    print(f"Spec: {spec.get('study_id')} / {spec.get('domain')}")
    print(f"\nVariables with controlled terminology:")
    for var in spec.get("variables", []):
        cl = var.get("codelist_code")
        if cl:
            print(f"  {var['target_variable']:15} codelist {cl} ({var.get('codelist_name', '')})")
```

> Which variables have codelist references?
> _________________________________________________________________

### Step 2: Build an API-Enhanced CT Lookup

Combine the REST API synonyms with the local ct_lookup.csv for maximum coverage:

```python
import csv

def build_hybrid_lookup(codelist_code, csv_path="macros/ct_lookup.csv"):
    """Build a CT lookup that merges API synonyms with local CSV mappings.

    Priority: API synonym match first, then CSV match, then unmatched.
    """
    # 1. Get API synonyms (authoritative)
    api_map = build_synonym_map(codelist_code)

    # 2. Get local CSV mappings (study-specific)
    csv_map = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["CODELIST"] == codelist_code:
                csv_map[row["RAW_VALUE"].upper()] = row["CT_VALUE"]

    # 3. Merge: API takes precedence, CSV fills gaps
    merged = dict(api_map)  # Start with API
    csv_only = 0
    for raw_upper, ct_val in csv_map.items():
        if raw_upper not in merged:
            merged[raw_upper] = ct_val
            csv_only += 1

    print(f"  API synonyms: {len(api_map)}")
    print(f"  CSV-only additions: {csv_only}")
    print(f"  Total merged entries: {len(merged)}")

    return merged

print("=== Hybrid Lookup for SEX (C66731) ===")
sex_lookup = build_hybrid_lookup("C66731")

print("\n=== Hybrid Lookup for RACE (C74457) ===")
race_lookup = build_hybrid_lookup("C74457")
```

> How many entries does the hybrid lookup have vs API-only vs CSV-only?
>
> | Source | SEX entries | RACE entries |
> |--------|-----------|-------------|
> | API synonyms | | |
> | CSV-only additions | | |
> | Merged total | | |

### Step 3: Re-Run Matching with the Hybrid Lookup

```python
def match_with_hybrid_lookup(raw_values, hybrid_map):
    """Match raw values using the merged synonym map."""
    matched = {}
    unmatched = []
    for raw in raw_values:
        upper = raw.strip().upper()
        if upper in hybrid_map:
            matched[raw] = hybrid_map[upper]
        else:
            unmatched.append(raw)
    return matched, unmatched

# Test with RACE
matched, unmatched = match_with_hybrid_lookup(raw_data["RACE"], race_lookup)
print(f"\nRACE hybrid matching: {len(matched)} matched, {len(unmatched)} unmatched")
if unmatched:
    print(f"Still unmatched: {unmatched}")
```

> Did the hybrid approach match more values than API alone? ___________
> What's still unmatched? ___________

### Step 4: See How This Fits in the Pipeline

```
Current pipeline (ct_lookup.csv):
  Spec Builder → reads ct_lookup.csv → maps raw values

Enhanced pipeline (hybrid):
  Spec Builder → queries NCI EVS API for codelist → builds synonym map
              → merges with ct_lookup.csv for study-specific mappings
              → checks extensibility for unmatched values
              → flags non-extensible unmatched for human review
```

> What are the advantages of the hybrid approach?
> _________________________________________________________________
>
> What are the risks? (Hint: think about network dependency)
> _________________________________________________________________
>
> How would you handle offline scenarios?
> _________________________________________________________________

### Step 5: Think Ahead

Consider how you would extend this for other domains:

> For the AE domain, the variable AESEV (severity) uses codelist C66769.
> Without modifying any static files, you can now:
>
> 1. Query `fetch_codelist("C66769")` to get the allowed severity values
> 2. Check if it's extensible
> 3. Match raw AE data against the codelist
>
> What manual work does this eliminate? ___________
>
> This is why the REST approach scales: you need ZERO domain-specific CSV
> files to handle new codelists. The API is the single source of truth.

---

## What You Should Have at the End

- [ ] Read codelist references from the mapping spec
- [ ] Built a hybrid lookup merging API synonyms + local CSV
- [ ] Understood why both sources are valuable (API = authoritative, CSV = study-specific)
- [ ] Identified how this integrates into the pipeline architecture
- [ ] Understood the scalability advantage for multi-domain work
