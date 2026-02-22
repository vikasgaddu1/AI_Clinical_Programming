# Exercise 4.3: Match Raw Data to Controlled Terminology

## Objective
Use the codelist fetcher from Exercise 4.2 to match actual raw data values from `study_data/raw_dm.csv` against CDISC controlled terminology. Identify exact matches, synonym matches, and unmatched values.

## Time: 30 minutes

---

## Steps

### Step 1: Load the Raw Data

```python
import csv

# Read raw_dm.csv and get distinct values for SEX, RACE, ETHNIC
raw_data = {}
with open("study_data/raw_dm.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for col in ["SEX", "RACE", "ETHNIC"]:
    values = set()
    for row in rows:
        val = row.get(col, "").strip()
        if val:
            values.add(val)
    raw_data[col] = sorted(values)
    print(f"\n{col} distinct values ({len(values)}):")
    for v in sorted(values):
        print(f"  '{v}'")
```

> How many distinct SEX values? ___________
> How many distinct RACE values? ___________
> How many distinct ETHNIC values? ___________
>
> Do you see any messy data (mixed case, abbreviations, non-standard terms)?
> _________________________________________________________________

### Step 2: Define the Variable-to-Codelist Mapping

The SDTM IG tells us which codelist each variable uses:

```python
# This is what the IG (and the mapping spec) tells us
variable_codelists = {
    "SEX": "C66731",
    "RACE": "C74457",
    "ETHNIC": "C66790",
}
```

In the real pipeline, this mapping comes from the approved spec or the IG client. Here we hardcode it for clarity.

### Step 3: Build the Matching Function

Using `build_synonym_map()` from Exercise 4.2:

```python
def match_raw_to_ct(raw_values, codelist_code):
    """Match raw data values against a CDISC codelist via NCI EVS API.

    Returns:
        matched: dict of {raw_value: ct_submission_value}
        unmatched: list of raw values with no match
    """
    synonym_map = build_synonym_map(codelist_code)
    matched = {}
    unmatched = []

    for raw in raw_values:
        upper = raw.strip().upper()
        if upper in synonym_map:
            matched[raw] = synonym_map[upper]
        else:
            unmatched.append(raw)

    return matched, unmatched
```

### Step 4: Run the Matching for SEX

```python
matched, unmatched = match_raw_to_ct(raw_data["SEX"], "C66731")

print("=== SEX Matching Results ===")
print(f"\nMatched ({len(matched)}):")
for raw, ct in sorted(matched.items()):
    marker = " ✓" if raw.upper() == ct.upper() else " (synonym)"
    print(f"  '{raw}' → '{ct}'{marker}")

print(f"\nUnmatched ({len(unmatched)}):")
for raw in unmatched:
    print(f"  '{raw}' → ???")
```

> How many SEX values matched? ___________
> How many were unmatched? ___________
>
> Did any raw values match via synonym (not exact match)?
> Examples: ___________

### Step 5: Run the Matching for RACE

```python
matched, unmatched = match_raw_to_ct(raw_data["RACE"], "C74457")

print("=== RACE Matching Results ===")
print(f"\nMatched ({len(matched)}):")
for raw, ct in sorted(matched.items()):
    print(f"  '{raw}' → '{ct}'")

print(f"\nUnmatched ({len(unmatched)}):")
for raw in unmatched:
    print(f"  '{raw}' → ???")
```

> How many RACE values matched? ___________
> How many were unmatched? ___________
>
> List the unmatched values:
> _________________________________________________________________
>
> These are the "Other Specify" free-text values from the CRF.
> This is exactly the RACE decision point the Spec Builder agent flags!

### Step 6: Run the Matching for ETHNIC

```python
matched, unmatched = match_raw_to_ct(raw_data["ETHNIC"], "C66790")

print("=== ETHNICITY Matching Results ===")
print(f"\nMatched ({len(matched)}):")
for raw, ct in sorted(matched.items()):
    print(f"  '{raw}' → '{ct}'")

print(f"\nUnmatched ({len(unmatched)}):")
for raw in unmatched:
    print(f"  '{raw}' → ???")
```

> How many ETHNIC values matched? ___________

### Step 7: Generate a Complete Matching Report

```python
print("\n" + "="*70)
print("CT MATCHING REPORT")
print("="*70)
print(f"Study: XYZ-2026-001")
print(f"Data source: study_data/raw_dm.csv ({len(rows)} subjects)")
print(f"CT source: NCI EVS REST API")
print()

for var, cl_code in variable_codelists.items():
    codelist = fetch_codelist_safe(cl_code)
    matched, unmatched = match_raw_to_ct(raw_data[var], cl_code)

    status = "PASS" if len(unmatched) == 0 else "REVIEW"
    ext_label = "extensible" if codelist and codelist["extensible"] else "non-extensible"

    print(f"--- {var} (codelist {cl_code}, {ext_label}) --- [{status}]")
    print(f"    Raw distinct values: {len(raw_data[var])}")
    print(f"    Matched to CT: {len(matched)}")
    print(f"    Unmatched: {len(unmatched)}")
    if unmatched:
        print(f"    Unmatched values: {unmatched}")
        if not codelist["extensible"]:
            print(f"    ACTION: Non-extensible codelist — unmatched values MUST be")
            print(f"            mapped to a CT term or flagged for human review")
    print()
```

> Copy or screenshot your complete matching report:
>
> ```
>
>
>
>
> ```

### Step 8: Compare with the Static ct_lookup.csv

The existing `macros/ct_lookup.csv` does the same matching, but with manually curated mappings.

```python
# Load the static CSV
ct_static = {}
with open("macros/ct_lookup.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cl = row["CODELIST"]
        raw = row["RAW_VALUE"].upper()
        ct = row["CT_VALUE"]
        ct_static.setdefault(cl, {})[raw] = ct

# Compare: which raw values does the CSV match that the API didn't?
for var, cl_code in variable_codelists.items():
    csv_map = ct_static.get(cl_code, {})
    _, api_unmatched = match_raw_to_ct(raw_data[var], cl_code)

    print(f"\n{var} ({cl_code}):")
    for raw in api_unmatched:
        csv_match = csv_map.get(raw.upper())
        if csv_match:
            print(f"  '{raw}' — API: unmatched, CSV: → '{csv_match}'")
        else:
            print(f"  '{raw}' — API: unmatched, CSV: also unmatched")
```

> Does the static CSV match anything the API missed? ___________
>
> Why? What's in the CSV that the API synonyms don't cover?
> _________________________________________________________________
>
> Key insight: The CSV has _study-specific_ abbreviation mappings (like "1"→"M" for SEX)
> that NCI EVS doesn't know about. The API provides standard synonyms; the CSV adds local ones.

---

## What You Should Have at the End

- [ ] Loaded distinct raw values for SEX, RACE, ETHNIC from raw_dm.csv
- [ ] Built matching function using API synonym maps
- [ ] Generated matching reports for all three variables
- [ ] Identified unmatched RACE values (Other Specify free text)
- [ ] Compared API matching vs static ct_lookup.csv matching
- [ ] Understood that API synonyms + local mappings together provide full coverage
