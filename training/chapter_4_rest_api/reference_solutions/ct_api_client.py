"""
Reference Solution: NCI EVS REST API Client for CDISC Controlled Terminology

This module provides functions to:
1. Fetch codelist metadata (name, extensibility) from NCI EVS
2. Fetch codelist members (allowed values) with CDISC submission values
3. Build synonym maps for matching raw data to CT
4. Match raw data values against CT with extensibility-aware routing

Usage:
    python ct_api_client.py              # Run demo with DM codelists
    python ct_api_client.py C66731       # Fetch a specific codelist
"""

import urllib.request
import json
import csv
import sys

BASE_URL = "https://api-evsrest.nci.nih.gov/api/v1"


# ---------------------------------------------------------------------------
# Core API Functions
# ---------------------------------------------------------------------------

def fetch_codelist_metadata(code):
    """Fetch codelist name and extensibility from NCI EVS.

    Args:
        code: NCI concept code (e.g., "C66731")

    Returns:
        dict with keys: code, name, extensible
    """
    url = f"{BASE_URL}/concept/ncit/{code}?include=summary"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    name = data.get("name", "")
    properties = data.get("properties", [])
    extensible = any(
        p["type"] == "Extensible_List" and p["value"] == "Yes"
        for p in properties
    )

    return {"code": code, "name": name, "extensible": extensible}


def fetch_codelist_members(code):
    """Fetch all CDISC submission values for a codelist.

    Args:
        code: NCI concept code (e.g., "C66731")

    Returns:
        list of submission value strings
    """
    url = f"{BASE_URL}/subset/ncit/{code}/members?include=summary"
    response = urllib.request.urlopen(url)
    members = json.loads(response.read())

    submission_values = []
    for member in members:
        cdisc_value = _extract_cdisc_submission_value(member)
        submission_values.append(cdisc_value)

    return submission_values


def fetch_codelist(code):
    """Fetch complete codelist info: metadata + submission values.

    Args:
        code: NCI concept code (e.g., "C66731")

    Returns:
        dict with keys: code, name, extensible, submission_values
    """
    meta = fetch_codelist_metadata(code)
    values = fetch_codelist_members(code)
    meta["submission_values"] = sorted(values)
    return meta


def fetch_codelist_safe(code):
    """Fetch codelist with error handling for network/HTTP failures."""
    try:
        return fetch_codelist(code)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  [WARN] Codelist {code} not found in NCI EVS")
        else:
            print(f"  [WARN] HTTP error {e.code} for codelist {code}")
        return None
    except urllib.error.URLError as e:
        print(f"  [WARN] Network error: {e.reason}")
        return None


# ---------------------------------------------------------------------------
# Synonym Map & Matching
# ---------------------------------------------------------------------------

def build_synonym_map(code):
    """Build a map of ALL known names -> CDISC submission value.

    Includes concept names and all synonyms from any source (CDISC, NCI, FDA, etc.)
    """
    url = f"{BASE_URL}/subset/ncit/{code}/members?include=summary"
    response = urllib.request.urlopen(url)
    members = json.loads(response.read())

    synonym_map = {}
    for member in members:
        submission_val = _extract_cdisc_submission_value(member)

        # Map the concept name
        synonym_map[member["name"].upper()] = submission_val

        # Map ALL synonyms
        for syn in member.get("synonyms", []):
            synonym_map[syn["name"].upper()] = submission_val

    return synonym_map


def match_raw_to_ct(raw_values, codelist_code):
    """Match raw data values against a CDISC codelist via NCI EVS API.

    Args:
        raw_values: list of raw data strings
        codelist_code: NCI concept code

    Returns:
        (matched, unmatched) where matched is {raw: ct_value} and
        unmatched is a list of raw values with no match
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


def build_hybrid_lookup(codelist_code, csv_path="macros/ct_lookup.csv"):
    """Merge API synonyms with local CSV mappings.

    API synonyms take precedence; CSV fills study-specific gaps.
    """
    api_map = build_synonym_map(codelist_code)

    csv_map = {}
    try:
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["CODELIST"] == codelist_code:
                    csv_map[row["RAW_VALUE"].upper()] = row["CT_VALUE"]
    except FileNotFoundError:
        pass

    merged = dict(api_map)
    for raw_upper, ct_val in csv_map.items():
        if raw_upper not in merged:
            merged[raw_upper] = ct_val

    return merged


# ---------------------------------------------------------------------------
# Extensibility Routing
# ---------------------------------------------------------------------------

def route_unmatched_values(unmatched_values, codelist_code):
    """Route unmatched values based on codelist extensibility.

    Returns:
        list of decision dicts
    """
    meta = fetch_codelist_metadata(codelist_code)
    decisions = []

    for raw_value in unmatched_values:
        if meta["extensible"]:
            decisions.append({
                "raw_value": raw_value,
                "action": "ACCEPT_AS_EXTENSION",
                "reason": f"Codelist {codelist_code} is extensible.",
                "human_review": False,
            })
        else:
            decisions.append({
                "raw_value": raw_value,
                "action": "REQUIRES_HUMAN_DECISION",
                "reason": f"Codelist {codelist_code} is non-extensible.",
                "human_review": True,
                "suggested_mappings": _suggest_closest_ct(raw_value, codelist_code),
            })

    return decisions


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _extract_cdisc_submission_value(member):
    """Extract the CDISC preferred term from a concept's synonyms."""
    for syn in member.get("synonyms", []):
        if syn.get("source") == "CDISC" and syn.get("termType") == "PT":
            return syn["name"]
    return member["name"].upper()


def _suggest_closest_ct(raw_value, codelist_code):
    """Suggest closest CT values using substring matching."""
    url = f"{BASE_URL}/subset/ncit/{codelist_code}/members?include=minimal"
    response = urllib.request.urlopen(url)
    members = json.loads(response.read())

    suggestions = []
    raw_upper = raw_value.upper()

    for member in members:
        name_upper = member["name"].upper()
        if raw_upper in name_upper or name_upper in raw_upper:
            suggestions.append(member["name"])

    other_members = [m for m in members if m["name"].upper() == "OTHER"]
    if other_members and "OTHER" not in [s.upper() for s in suggestions]:
        suggestions.append("Other")

    return suggestions if suggestions else ["No close match -- manual review required"]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo(codelist_code=None):
    """Run a demo showing the full CT matching workflow."""
    if codelist_code:
        result = fetch_codelist_safe(codelist_code)
        if result:
            ext_str = "EXTENSIBLE" if result["extensible"] else "NON-EXTENSIBLE"
            print(f"\n{result['code']} - {result['name']} [{ext_str}]")
            print(f"Values ({len(result['submission_values'])}):")
            for v in result["submission_values"]:
                print(f"  {v}")
        return

    print("=" * 70)
    print("NCI EVS REST API — CDISC CT Matching Demo")
    print("=" * 70)

    variable_codelists = {
        "SEX": "C66731",
        "RACE": "C74457",
        "ETHNIC": "C66790",
    }

    # Load raw data
    raw_data = {}
    try:
        with open("study_data/raw_dm.csv", "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        for col in variable_codelists:
            values = set()
            for row in rows:
                val = row.get(col, "").strip()
                if val:
                    values.add(val)
            raw_data[col] = sorted(values)
        print(f"\nLoaded {len(rows)} subjects from raw_dm.csv")
    except FileNotFoundError:
        print("\nraw_dm.csv not found -- using sample data")
        raw_data = {
            "SEX": ["Male", "Female", "M", "F", "MALE"],
            "RACE": ["White", "Black", "Asian", "Filipino", "Caucasian"],
            "ETHNIC": ["Hispanic", "Not Hispanic", "Unknown"],
        }

    for var, cl_code in variable_codelists.items():
        codelist = fetch_codelist_safe(cl_code)
        if not codelist:
            continue

        matched, unmatched = match_raw_to_ct(raw_data[var], cl_code)
        ext_label = "extensible" if codelist["extensible"] else "non-extensible"
        status = "PASS" if not unmatched else "REVIEW"

        print(f"\n--- {var} ({cl_code}, {ext_label}) [{status}] ---")
        print(f"  Raw distinct values: {len(raw_data[var])}")
        print(f"  Matched: {len(matched)}")
        print(f"  Unmatched: {len(unmatched)}")

        if unmatched:
            decisions = route_unmatched_values(unmatched, cl_code)
            for d in decisions:
                print(f"  -> '{d['raw_value']}': {d['action']}")
                if d.get("suggested_mappings"):
                    print(f"    Suggestions: {d['suggested_mappings']}")


if __name__ == "__main__":
    code_arg = sys.argv[1] if len(sys.argv) > 1 else None
    demo(code_arg)
