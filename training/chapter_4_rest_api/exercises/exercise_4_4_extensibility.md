# Exercise 4.4: Handle Extensible vs Non-Extensible Codelists

## Objective
Build logic that checks whether a codelist is extensible and routes unmatched values accordingly: non-extensible codelists require human decisions, while extensible codelists can accept sponsor-defined values.

## Time: 25 minutes

---

## Background

CDISC controlled terminology codelists come in two flavors:

| Type | Rule | Example |
|------|------|---------|
| **Non-extensible** | ONLY codelist values are allowed. Any other value is a validation error. | SEX (C66731), RACE (C74457), ETHNICITY (C66790) |
| **Extensible** | Codelist values are the standard, but sponsors CAN add their own if needed. | Dosage Form (C66726), Unit (C71620), Route of Administration (C66729) |

The `Extensible_List` property in the NCI EVS API response tells you which type a codelist is.

---

## Steps

### Step 1: Check Extensibility for DM Codelists

Using `fetch_codelist_metadata()` from Exercise 4.2:

```python
dm_codelists = {
    "SEX": "C66731",
    "RACE": "C74457",
    "ETHNIC": "C66790",
    "COUNTRY": "C71113",
}

print("=== DM Codelist Extensibility ===")
for var, code in dm_codelists.items():
    meta = fetch_codelist_metadata(code)
    ext_str = "EXTENSIBLE" if meta["extensible"] else "NON-EXTENSIBLE"
    print(f"  {var:10} {code}  {meta['name']:50}  [{ext_str}]")
```

> Which DM codelists are extensible? ___________
> Which are non-extensible? ___________

### Step 2: Check an Extensible Codelist

Let's look at C66726 (Dosage Form) -- a codelist used in other SDTM domains:

```python
dosage_form = fetch_codelist("C66726")
print(f"Name: {dosage_form['name']}")
print(f"Extensible: {dosage_form['extensible']}")
print(f"Values ({len(dosage_form['submission_values'])}):")
for v in dosage_form["submission_values"][:15]:
    print(f"  {v}")
if len(dosage_form["submission_values"]) > 15:
    print(f"  ... and {len(dosage_form['submission_values']) - 15} more")
```

> How many values does C66726 have? ___________
>
> If a clinical trial used a dosage form not in this list (e.g., "NASAL SPRAY"),
> what would happen?
>
> - With a non-extensible codelist: ___________
> - With this extensible codelist: ___________

### Step 3: Build the Routing Function

Now build the function that decides what to do with unmatched values:

```python
def route_unmatched_values(unmatched_values, codelist_code):
    """Decide how to handle values that don't match any CT term.

    Returns:
        decisions: list of dicts describing each routing decision
    """
    meta = fetch_codelist_metadata(codelist_code)
    decisions = []

    for raw_value in unmatched_values:
        if meta["extensible"]:
            decisions.append({
                "raw_value": raw_value,
                "action": "ACCEPT_AS_EXTENSION",
                "reason": f"Codelist {codelist_code} is extensible. "
                          f"'{raw_value}' accepted as sponsor-defined value.",
                "human_review": False,
            })
        else:
            decisions.append({
                "raw_value": raw_value,
                "action": "REQUIRES_HUMAN_DECISION",
                "reason": f"Codelist {codelist_code} is NON-extensible. "
                          f"'{raw_value}' must be mapped to a standard CT term.",
                "human_review": True,
                "suggested_mappings": suggest_closest_ct(raw_value, codelist_code),
            })

    return decisions
```

### Step 4: Build the Suggestion Helper

When a value can't be accepted as-is, suggest the closest CT terms:

```python
def suggest_closest_ct(raw_value, codelist_code):
    """Suggest closest CT values for an unmatched raw value.

    Uses simple substring matching -- not fuzzy matching.
    """
    members_url = f"{BASE_URL}/subset/ncit/{codelist_code}/members?include=minimal"
    response = urllib.request.urlopen(members_url)
    members = json.loads(response.read())

    suggestions = []
    raw_upper = raw_value.upper()

    for member in members:
        name_upper = member["name"].upper()
        # Check if the raw value is a substring of the CT term or vice versa
        if raw_upper in name_upper or name_upper in raw_upper:
            suggestions.append(member["name"])

    # Always include OTHER if it's in the codelist
    other_members = [m for m in members if m["name"].upper() == "OTHER"]
    if other_members and "OTHER" not in [s.upper() for s in suggestions]:
        suggestions.append("Other")

    return suggestions if suggestions else ["No close match found -- manual review required"]
```

### Step 5: Test with Real Unmatched Values

Use the unmatched RACE values from Exercise 4.3:

```python
# Get unmatched RACE values (from Exercise 4.3)
_, race_unmatched = match_raw_to_ct(raw_data["RACE"], "C74457")

print("=== Routing Unmatched RACE Values ===\n")
decisions = route_unmatched_values(race_unmatched, "C74457")
for d in decisions:
    print(f"  Raw value: '{d['raw_value']}'")
    print(f"  Action: {d['action']}")
    print(f"  Reason: {d['reason']}")
    if d.get("suggested_mappings"):
        print(f"  Suggestions: {d['suggested_mappings']}")
    print(f"  Needs human review: {d['human_review']}")
    print()
```

> For each unmatched RACE value, what action was taken?
>
> | Raw Value | Action | Suggestions |
> |-----------|--------|-------------|
> | | | |
> | | | |
> | | | |

### Step 6: Understand the Connection to the Spec Builder

In the Capstone orchestrator, the Spec Builder agent creates decision points like this:

```json
{
  "target_variable": "RACE",
  "human_decision_required": true,
  "decision_options": [
    {"id": "A", "description": "Map free-text to closest CT term..."},
    {"id": "B", "description": "All Other → RACE='OTHER' + SUPPDM..."},
    {"id": "C", "description": "Mixed → RACE='MULTIPLE' + SUPPDM..."}
  ]
}
```

> How does the extensibility check help the Spec Builder make this decision?
> _________________________________________________________________
>
> If RACE were extensible, would the Spec Builder still need to flag it
> for human review? Why or why not?
> _________________________________________________________________

---

## What You Should Have at the End

- [ ] Checked extensibility for all DM codelists
- [ ] Understood the difference between extensible and non-extensible codelists
- [ ] Built routing logic that handles unmatched values differently based on extensibility
- [ ] Built a suggestion function for non-extensible codelists
- [ ] Connected the extensibility check to the Spec Builder's decision workflow
