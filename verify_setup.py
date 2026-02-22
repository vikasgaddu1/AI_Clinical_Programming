"""
Verification script for the SDTM Orchestrator setup.

Checks that all critical fixes have been properly applied:
1. QC programmer is independent (does NOT import from production_programmer)
2. Spec includes all required DM variables
3. Config model IDs are current
4. .gitignore exists
5. LLM client module exists
6. State has save/load methods
7. Spec manager respects domain parameter
8. Validation agent checks RACE and ETHNIC CT
9. IG client can parse markdown files
10. Skills directory exists with 5 skills

Run from project root:
  python verify_setup.py
"""

import importlib
import inspect
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail:
        msg += f" — {detail}"
    results.append((condition, msg))
    print(msg)


# ---- 1. QC programmer independence ----
try:
    source = (PROJECT_ROOT / "orchestrator" / "agents" / "qc_programmer.py").read_text(encoding="utf-8")
    has_import = "from orchestrator.agents.production_programmer" in source
    check(
        "QC programmer independence",
        not has_import,
        "does NOT import from production_programmer" if not has_import else "STILL imports from production_programmer!"
    )
except Exception as e:
    check("QC programmer independence", False, str(e))

# ---- 2. Spec builder includes required variables ----
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from orchestrator.core.function_loader import FunctionLoader
    from orchestrator.agents.spec_builder import build_draft_spec

    fl = FunctionLoader(str(PROJECT_ROOT / "r_functions" / "function_registry.json"))
    spec = build_draft_spec("XYZ-2026-001", "DM", str(PROJECT_ROOT / "study_data" / "raw_dm.csv"), fl)
    var_names = {v["target_variable"] for v in spec.get("variables", [])}

    core_vars = {"STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC", "SITEID",
                 "BRTHDTC", "AGE", "AGEU", "SEX", "RACE", "ETHNIC",
                 "ARMCD", "ARM", "ACTARMCD", "ACTARM", "COUNTRY",
                 "DMDTC", "DMDY", "RFENDTC"}
    missing = core_vars - var_names
    check(
        "Spec builder covers required variables",
        len(missing) == 0,
        f"missing: {sorted(missing)}" if missing else f"all {len(core_vars)} required vars present"
    )
except Exception as e:
    check("Spec builder covers required variables", False, str(e))

# ---- 3. Config model IDs ----
try:
    import yaml
    cfg = yaml.safe_load(open(PROJECT_ROOT / "orchestrator" / "config.yaml", encoding="utf-8"))
    agents = cfg.get("agents", {})
    outdated = []
    for key, val in agents.items():
        if isinstance(val, dict):
            model = val.get("model", "")
            if "20250929" in model or "20251101" in model:
                outdated.append(f"{key}: {model}")
    check("Config model IDs current", len(outdated) == 0,
          f"outdated: {outdated}" if outdated else "all model IDs updated")
except Exception as e:
    check("Config model IDs current", False, str(e))

# ---- 4. .gitignore exists ----
check(".gitignore exists", (PROJECT_ROOT / ".gitignore").exists())

# ---- 5. LLM client module exists ----
llm_path = PROJECT_ROOT / "orchestrator" / "core" / "llm_client.py"
check("LLM client module exists", llm_path.exists())

# ---- 6. State has save/load ----
try:
    from orchestrator.core.state import PipelineState
    has_save = hasattr(PipelineState, "save")
    has_load = hasattr(PipelineState, "load")
    check("State has save/load", has_save and has_load,
          f"save={'yes' if has_save else 'no'}, load={'yes' if has_load else 'no'}")
except Exception as e:
    check("State has save/load", False, str(e))

# ---- 7. Spec manager respects domain ----
try:
    from orchestrator.core.spec_manager import SpecManager
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        sm = SpecManager(td)
        dm_path = sm.spec_path("DM")
        ae_path = sm.spec_path("AE")
        dm_ok = "dm_" in dm_path.name.lower()
        ae_ok = "ae_" in ae_path.name.lower()
    check("Spec manager uses domain parameter", dm_ok and ae_ok,
          f"DM={dm_path.name}, AE={ae_path.name}")
except Exception as e:
    check("Spec manager uses domain parameter", False, str(e))

# ---- 8. Validation agent checks RACE/ETHNIC ----
try:
    source = (PROJECT_ROOT / "orchestrator" / "agents" / "validation_agent.py").read_text(encoding="utf-8")
    checks_race = "C74457" in source
    checks_ethnic = "C66790" in source
    check("Validation checks RACE and ETHNIC CT",
          checks_race and checks_ethnic,
          f"RACE(C74457)={'yes' if checks_race else 'no'}, ETHNIC(C66790)={'yes' if checks_ethnic else 'no'}")
except Exception as e:
    check("Validation checks RACE and ETHNIC CT", False, str(e))

# ---- 9. IG client parses markdown ----
try:
    from orchestrator.core.ig_client import IGClient
    ig = IGClient()
    required = ig.get_required_variables("DM")
    check("IG client reads markdown", len(required) > 5,
          f"found {len(required)} required DM vars from IG: {required[:5]}...")
except Exception as e:
    check("IG client reads markdown", False, str(e))

# ---- 10. Skills directory with 5 skills ----
skills_dir = PROJECT_ROOT / ".claude" / "skills"
if skills_dir.exists():
    skill_files = list(skills_dir.glob("*.md"))
    check("Skills directory with 5 skills", len(skill_files) >= 5,
          f"found {len(skill_files)} skill(s): {[f.stem for f in skill_files]}")
else:
    check("Skills directory with 5 skills", False, "directory not found")

# ---- 11. MCP server exists ----
check("MCP server exists", (PROJECT_ROOT / "mcp_server.py").exists())

# ---- 12. MCP config exists ----
check("MCP config exists", (PROJECT_ROOT / ".claude" / "mcp.json").exists())

# ---- Summary ----
print()
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")

if failed > 0:
    print("\nFailed checks:")
    for ok, msg in results:
        if not ok:
            print(f"  {msg}")
    sys.exit(1)
else:
    print("\nAll verification checks passed!")
    sys.exit(0)
