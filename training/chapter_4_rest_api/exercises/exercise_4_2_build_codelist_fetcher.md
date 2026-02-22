# Exercise 4.2: Build a Codelist Fetcher

## Objective
Write a Python function that, given a CDISC codelist code (e.g., C66731), fetches the codelist metadata and all allowed submission values from the NCI EVS REST API.

## Time: 30 minutes

---

## Steps

### Step 1: Understand the Goal

You'll build a function `fetch_codelist(code)` that returns:
```python
{
    "code": "C66731",
    "name": "CDISC SDTM Sex of Individual Terminology",
    "extensible": False,
    "submission_values": ["F", "INTERSEX", "M", "U"]
}
```

This requires two API calls:
1. `/concept/ncit/{code}?include=summary` -- for metadata (name, extensibility)
2. `/subset/ncit/{code}/members?include=summary` -- for member values

### Step 2: Write the Metadata Fetcher

```python
import urllib.request
import json

BASE_URL = "https://api-evsrest.nci.nih.gov/api/v1"

def fetch_codelist_metadata(code):
    """Fetch codelist name and extensibility from NCI EVS."""
    url = f"{BASE_URL}/concept/ncit/{code}?include=summary"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    name = data.get("name", "")
    properties = data.get("properties", [])

    # Find the Extensible_List property
    extensible = False
    for prop in properties:
        if prop["type"] == "Extensible_List":
            extensible = (prop["value"] == "Yes")
            break

    return {"code": code, "name": name, "extensible": extensible}
```

Test it:
```python
meta = fetch_codelist_metadata("C66731")
print(f"Name: {meta['name']}")
print(f"Extensible: {meta['extensible']}")
```

> Name: ___________
> Extensible: ___________

### Step 3: Write the Members Fetcher

This is the harder part. The CDISC submission value is buried in the synonyms array. You need to:
1. Get all members of the subset
2. For each member, find the synonym where `source == "CDISC"` and `termType == "PT"`

```python
def fetch_codelist_members(code):
    """Fetch all submission values for a CDISC codelist."""
    url = f"{BASE_URL}/subset/ncit/{code}/members?include=summary"
    response = urllib.request.urlopen(url)
    members = json.loads(response.read())

    submission_values = []
    for member in members:
        synonyms = member.get("synonyms", [])
        # Find the CDISC preferred term
        cdisc_value = None
        for syn in synonyms:
            if syn.get("source") == "CDISC" and syn.get("termType") == "PT":
                cdisc_value = syn["name"]
                break
        # Fallback to concept name if no CDISC PT found
        if cdisc_value is None:
            cdisc_value = member["name"].upper()
        submission_values.append(cdisc_value)

    return submission_values
```

Test it:
```python
values = fetch_codelist_members("C66731")
print(f"Submission values: {values}")
```

> Submission values: ___________

### Step 4: Combine into a Single Function

```python
def fetch_codelist(code):
    """Fetch complete codelist info: metadata + submission values."""
    meta = fetch_codelist_metadata(code)
    values = fetch_codelist_members(code)
    meta["submission_values"] = sorted(values)
    return meta
```

Test with multiple codelists:
```python
for cl_code in ["C66731", "C74457", "C66790"]:
    result = fetch_codelist(cl_code)
    print(f"\n{result['code']} - {result['name']}")
    print(f"  Extensible: {result['extensible']}")
    print(f"  Values: {result['submission_values']}")
```

Fill in the results:

> **C66731 (Sex):**
> Values: ___________
>
> **C74457 (Race):**
> Values: ___________
>
> **C66790 (Ethnicity):**
> Values: ___________

### Step 5: Add Error Handling

Real-world API calls can fail. Add error handling:

```python
def fetch_codelist_safe(code):
    """Fetch codelist with error handling."""
    try:
        return fetch_codelist(code)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Codelist {code} not found in NCI EVS")
        else:
            print(f"HTTP error {e.code} for codelist {code}")
        return None
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}")
        print("Check your internet connection or try again later")
        return None

# Test with valid and invalid codes
print(fetch_codelist_safe("C66731"))   # Should work
print(fetch_codelist_safe("C99999"))   # Should fail gracefully
```

> What happens with C99999? ___________

### Step 6: Build a Synonym Lookup Table

The member synonyms include alternative names from multiple sources (CDISC, NCI, FDA, etc.). Build a more complete lookup:

```python
def build_synonym_map(code):
    """Build a map of ALL known names → CDISC submission value."""
    url = f"{BASE_URL}/subset/ncit/{code}/members?include=summary"
    response = urllib.request.urlopen(url)
    members = json.loads(response.read())

    synonym_map = {}
    for member in members:
        # Find the CDISC submission value
        submission_val = None
        for syn in member.get("synonyms", []):
            if syn.get("source") == "CDISC" and syn.get("termType") == "PT":
                submission_val = syn["name"]
                break
        if submission_val is None:
            submission_val = member["name"].upper()

        # Map the concept name
        synonym_map[member["name"].upper()] = submission_val

        # Map ALL synonyms (from any source)
        for syn in member.get("synonyms", []):
            synonym_map[syn["name"].upper()] = submission_val

    return synonym_map

syn_map = build_synonym_map("C66731")
print(f"Total synonym entries: {len(syn_map)}")
print(f"'MALE' → {syn_map.get('MALE', 'NOT FOUND')}")
print(f"'F' → {syn_map.get('F', 'NOT FOUND')}")
print(f"'FEMALE' → {syn_map.get('FEMALE', 'NOT FOUND')}")
```

> Total synonym entries: ___________
>
> Why are there more synonym entries than codelist members?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] `fetch_codelist_metadata()` -- returns name and extensibility
- [ ] `fetch_codelist_members()` -- returns CDISC submission values
- [ ] `fetch_codelist()` -- combined function
- [ ] `fetch_codelist_safe()` -- with error handling
- [ ] `build_synonym_map()` -- maps all known names to submission values
- [ ] Tested all functions with C66731, C74457, and C66790
