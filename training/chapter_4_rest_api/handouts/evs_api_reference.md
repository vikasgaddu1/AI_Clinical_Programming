# NCI EVS REST API Quick Reference

## Base URL

```
https://api-evsrest.nci.nih.gov/api/v1/
```

No authentication required. Free and public.

---

## Key Endpoints for CDISC CT

### 1. Get Codelist Metadata

```
GET /concept/ncit/{code}?include=summary
```

**Example:** `GET /concept/ncit/C66731?include=summary`

**Response (key fields):**
```json
{
  "code": "C66731",
  "name": "CDISC SDTM Sex of Individual Terminology",
  "properties": [
    {"type": "Extensible_List", "value": "No"},
    {"type": "Contributing_Source", "value": "CDISC"}
  ]
}
```

### 2. Get Codelist Members (Allowed Values)

```
GET /subset/ncit/{code}/members?include=summary
```

**Example:** `GET /subset/ncit/C66731/members?include=summary`

**Response (array of members):**
```json
[
  {
    "code": "C16576",
    "name": "Female",
    "synonyms": [
      {"name": "F", "termType": "PT", "source": "CDISC", "code": "SDTM-SEX"},
      {"name": "FEMALE", "termType": "PT", "source": "FDA", "subSource": "SPL"}
    ]
  }
]
```

### 3. Search Concepts by Term

```
GET /concept/ncit/search?term={search_term}&include=minimal
```

**Example:** `GET /concept/ncit/search?term=sex+codelist&include=minimal`

---

## The `include` Parameter

| Value | Returns | Use When |
|-------|---------|----------|
| `minimal` | code, name | Quick lookups, listing |
| `summary` | + synonyms, definitions, properties | CT work (need synonyms + extensibility) |
| `full` | + parents, children, associations | Deep exploration |

---

## Extracting the CDISC Submission Value

The submission value for SDTM is in the `synonyms` array. Filter by:
- `source == "CDISC"`
- `termType == "PT"` (Preferred Term)
- `code` matches the SDTM codelist abbreviation (e.g., `"SDTM-SEX"`)

```python
def get_submission_value(member):
    for syn in member.get("synonyms", []):
        if syn.get("source") == "CDISC" and syn.get("termType") == "PT":
            return syn["name"]
    return member["name"].upper()  # fallback
```

---

## Common CDISC Codelist Codes

| Code | Name | Variables | Extensible |
|------|------|-----------|-----------|
| C66731 | Sex | SEX | No |
| C74457 | Race | RACE | No |
| C66790 | Ethnicity | ETHNIC | No |
| C71113 | Country | COUNTRY | Yes |
| C66726 | Dosage Form | -- | Yes |
| C66769 | Severity/Intensity | AESEV | No |
| C66767 | Outcome of Event | AEOUT | No |
| C66742 | Relationship to Intervention | AEREL | No |
| C66728 | Position | VSPOS | No |
| C71620 | Unit | various | Yes |
| C66741 | Lab Test | LBTESTCD | Yes |
| C66770 | Specimen Type | LBSPEC | Yes |

---

## Extensible vs Non-Extensible

| | Non-Extensible | Extensible |
|--|---------------|-----------|
| **Rule** | Only codelist values allowed | Standard values + sponsor additions |
| **Unmatched values** | Must map to CT term or flag error | Can accept as sponsor extension |
| **Check** | `Extensible_List: No` | `Extensible_List: Yes` |
| **Examples** | SEX, RACE, ETHNIC | COUNTRY, Units, Lab Tests |

---

## Python Minimal Example

```python
import urllib.request
import json

BASE_URL = "https://api-evsrest.nci.nih.gov/api/v1"

def fetch_ct_values(codelist_code):
    """Fetch CDISC submission values for a codelist."""
    # Get metadata
    url = f"{BASE_URL}/concept/ncit/{codelist_code}?include=summary"
    resp = urllib.request.urlopen(url)
    meta = json.loads(resp.read())

    extensible = any(
        p["type"] == "Extensible_List" and p["value"] == "Yes"
        for p in meta.get("properties", [])
    )

    # Get members
    url = f"{BASE_URL}/subset/ncit/{codelist_code}/members?include=summary"
    resp = urllib.request.urlopen(url)
    members = json.loads(resp.read())

    values = []
    for m in members:
        for syn in m.get("synonyms", []):
            if syn.get("source") == "CDISC" and syn.get("termType") == "PT":
                values.append(syn["name"])
                break
        else:
            values.append(m["name"].upper())

    return {
        "code": codelist_code,
        "name": meta["name"],
        "extensible": extensible,
        "values": sorted(values),
    }

# Usage
result = fetch_ct_values("C66731")
print(f"{result['name']} (Extensible: {result['extensible']})")
print(f"Values: {result['values']}")
```

---

## Resources

- **Swagger UI:** https://api-evsrest.nci.nih.gov/swagger-ui/index.html
- **Client SDK (Python, Java, curl):** https://github.com/NCIEVS/evsrestapi-client-SDK
- **NCI EVS Homepage:** https://evs.nci.nih.gov/
- **CDISC CT Downloads (Excel/XML):** https://evs.nci.nih.gov/ftp1/CDISC/SDTM/
