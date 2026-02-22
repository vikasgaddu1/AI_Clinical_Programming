# Exercise 4.1: Explore the NCI EVS REST API

## Objective
Understand the NCI EVS REST API structure by making manual queries and reading the JSON responses. Learn the two-endpoint pattern: `/concept` for codelist metadata, `/subset/.../members` for allowed values.

## Time: 20 minutes

---

## Background

The NCI EVS (Enterprise Vocabulary Services) REST API provides free, public access to all CDISC controlled terminology. No API key or authentication is required.

- **Base URL:** `https://api-evsrest.nci.nih.gov/api/v1/`
- **Documentation:** https://api-evsrest.nci.nih.gov/swagger-ui/index.html
- **GitHub SDK:** https://github.com/NCIEVS/evsrestapi-client-SDK

---

## Steps

### Step 1: Query a Codelist in Your Browser

Open this URL in your browser:

```
https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C66731?include=summary
```

This retrieves the **codelist metadata** for C66731 (Sex).

> What is the `name` field? ___________
>
> Find the `properties` array. What is the value of `Extensible_List`? ___________
>
> What does `Contributing_Source: CDISC` tell you? ___________

### Step 2: Get the Codelist Members

Now open:

```
https://api-evsrest.nci.nih.gov/api/v1/subset/ncit/C66731/members?include=summary
```

This returns the **allowed values** (members) of the Sex codelist.

> How many members are returned? ___________
>
> List each member's `code` and `name`:
>
> | Code | Name |
> |------|------|
> | | |
> | | |
> | | |
> | | |

### Step 3: Find the CDISC Submission Value

For each member, look at the `synonyms` array. The CDISC submission value for SDTM is the synonym where:
- `"source": "CDISC"`
- `"termType": "PT"`
- `"code": "SDTM-SEX"` (matches the codelist short name)

For the **Female** member (C16576), find the SDTM submission value.

> CDISC submission value for Female: ___________
>
> Why is this different from the `name` field ("Female" vs the submission value)?
> _________________________________________________________________

### Step 4: Query with Python

In Claude Code or a Python terminal, run:

```python
import urllib.request
import json

url = "https://api-evsrest.nci.nih.gov/api/v1/subset/ncit/C66731/members?include=minimal"
response = urllib.request.urlopen(url)
data = json.loads(response.read())

print(f"Codelist C66731 has {len(data)} members:")
for member in data:
    print(f"  {member['code']:10} {member['name']}")
```

> Output:
> ```
>
>
>
> ```

### Step 5: Try the Race Codelist (C74457)

Modify the Python code to query codelist **C74457** (Race):

```python
url = "https://api-evsrest.nci.nih.gov/api/v1/subset/ncit/C74457/members?include=minimal"
response = urllib.request.urlopen(url)
data = json.loads(response.read())

print(f"Codelist C74457 has {len(data)} members:")
for member in data:
    print(f"  {member['code']:10} {member['name']}")
```

> How many Race values are in the codelist? ___________
>
> Compare with the static `macros/ct_lookup.csv`. Open the CSV and count the C74457 entries.
> How many entries does the CSV have for C74457? ___________
>
> What's the difference? Why might the CSV have MORE entries?
> _________________________________________________________________
> (Hint: the CSV includes abbreviation mappings like W→WHITE, B→BLACK OR AFRICAN AMERICAN)

### Step 6: Query a Codelist That Doesn't Exist

Try an invalid code:

```python
try:
    url = "https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C99999?include=summary"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    print(data)
except Exception as e:
    print(f"Error: {e}")
```

> What HTTP error code do you get? ___________
>
> Why is error handling important when building API-dependent code?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] Queried a codelist in the browser and read the JSON response
- [ ] Identified the Extensible_List property in the response
- [ ] Found the CDISC submission value in the synonyms array
- [ ] Made API calls from Python using `urllib`
- [ ] Compared REST API results with the static ct_lookup.csv
- [ ] Handled an API error for an invalid codelist code
