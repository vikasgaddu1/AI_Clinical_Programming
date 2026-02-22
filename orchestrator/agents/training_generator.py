"""
Training Generator Agent: produce complete training chapter packages.

Generates exercises, instructor guides, handouts, and metadata for clinical
programming training at any skill level and for any SDTM domain.  Uses IG
content, function registry, and raw data context dynamically -- no hardcoded
domain references.

In OFF mode (no LLM), produces complete template-based output.
In LIVE mode, enriches narratives with Claude-generated content.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.core.function_loader import FunctionLoader
from orchestrator.core.ig_client import IGClient
from orchestrator.core.spec_manager import SpecManager
from orchestrator.core.training_context import (
    DomainContext,
    ProjectContext,
    gather_domain_context,
    gather_project_context,
)

# ---------------------------------------------------------------------------
# Skill level configuration
# ---------------------------------------------------------------------------

SKILL_LEVEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "consumer": {
        "label": "Consumer",
        "depth": "introductory",
        "exercise_count": 3,
        "exercise_style": "guided_walkthrough",
        "code_complexity": "none",
        "focus": "understanding_outputs",
        "typical_duration": "2-3 hours",
        "prerequisite_level": "none",
        "exercises_use_skills": True,
        "exercises_write_code": False,
        "audience": "Clinical programmers new to AI tools",
        "prerequisites": ["Python environment with orchestrator installed"],
    },
    "operator": {
        "label": "Operator",
        "depth": "intermediate",
        "exercise_count": 4,
        "exercise_style": "directed_tasks",
        "code_complexity": "use_existing",
        "focus": "running_and_interpreting",
        "typical_duration": "3-4 hours",
        "prerequisite_level": "consumer",
        "exercises_use_skills": True,
        "exercises_write_code": False,
        "audience": "Clinical programmers who completed Consumer-level training",
        "prerequisites": [
            "Python 3.11+",
            "R 4.x with arrow and haven packages",
            "Completed Consumer-level training",
        ],
    },
    "builder": {
        "label": "Builder",
        "depth": "advanced",
        "exercise_count": 6,
        "exercise_style": "build_components",
        "code_complexity": "write_new",
        "focus": "building_and_extending",
        "typical_duration": "5-6 hours",
        "prerequisite_level": "operator",
        "exercises_use_skills": True,
        "exercises_write_code": True,
        "audience": "Clinical programmers who completed Operator-level training",
        "prerequisites": [
            "Python 3.11+",
            "R 4.x with arrow and haven packages",
            "Completed Operator-level training",
            "Familiarity with JSON and markdown",
        ],
    },
    "architect": {
        "label": "Architect",
        "depth": "expert",
        "exercise_count": 6,
        "exercise_style": "design_and_integrate",
        "code_complexity": "design_systems",
        "focus": "system_design",
        "typical_duration": "6-8 hours",
        "prerequisite_level": "builder",
        "exercises_use_skills": True,
        "exercises_write_code": True,
        "audience": "Clinical programmers who completed Builder-level training",
        "prerequisites": [
            "Python 3.11+",
            "R 4.x with arrow and haven packages",
            "Completed Builder-level training",
            "Understanding of orchestrator architecture",
        ],
    },
}

# ---------------------------------------------------------------------------
# Topic → exercise mapping
# ---------------------------------------------------------------------------

TOPIC_EXERCISE_MAP: Dict[str, Dict[str, Any]] = {
    "data_profiling": {
        "description": "Profile raw clinical data and identify quality issues",
        "skills_used": ["/profile-data", "/check-environment"],
        "agents_involved": ["spec_builder"],
        "pipeline_stages": [],
        "artifacts_produced": ["data profile report"],
    },
    "spec_building": {
        "description": "Build mapping specifications from raw data and IG",
        "skills_used": ["/run-pipeline spec_build", "/review-spec"],
        "agents_involved": ["spec_builder", "spec_reviewer"],
        "pipeline_stages": ["spec_build", "spec_review"],
        "artifacts_produced": [
            "dm_mapping_spec.json",
            "dm_mapping_spec.xlsx",
        ],
    },
    "production_programming": {
        "description": "Generate production R scripts from approved specs",
        "skills_used": ["/run-pipeline production"],
        "agents_involved": ["production_programmer"],
        "pipeline_stages": ["production"],
        "artifacts_produced": [
            "dm_production.R",
            "dm.parquet",
            "dm.xpt",
        ],
    },
    "qc_and_comparison": {
        "description": "Independent QC programming and dataset comparison",
        "skills_used": ["/run-pipeline qc", "/run-pipeline compare"],
        "agents_involved": ["qc_programmer"],
        "pipeline_stages": ["qc", "compare"],
        "artifacts_produced": [
            "dm_qc.R",
            "dm_qc.parquet",
            "dm_compare_report.txt",
        ],
    },
    "validation": {
        "description": "P21 validation, define.xml, and spec sheet generation",
        "skills_used": ["/validate-dataset", "/run-pipeline validate"],
        "agents_involved": ["validation_agent"],
        "pipeline_stages": ["validate"],
        "artifacts_produced": [
            "p21_report.txt",
            "p21_spec_sheet.xlsx",
            "define_metadata.json",
        ],
    },
    "full_pipeline": {
        "description": "End-to-end SDTM pipeline from raw data to validated submission",
        "skills_used": [
            "/run-pipeline",
            "/profile-data",
            "/review-spec",
            "/validate-dataset",
        ],
        "agents_involved": ["all"],
        "pipeline_stages": [
            "spec_build",
            "spec_review",
            "human_review",
            "production",
            "qc",
            "compare",
            "validate",
        ],
        "artifacts_produced": ["all pipeline artifacts"],
    },
    "human_review": {
        "description": "Human-in-the-loop spec review and decision making",
        "skills_used": ["/review-spec"],
        "agents_involved": ["human_review"],
        "pipeline_stages": ["human_review"],
        "artifacts_produced": ["dm_mapping_spec_approved.json"],
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    return text.lower().replace(" ", "_").replace("-", "_")


def _var_list_str(variables: List[str], limit: int = 8) -> str:
    """Format a variable list for display, truncating if long."""
    if len(variables) <= limit:
        return ", ".join(variables)
    return ", ".join(variables[:limit]) + f", ... ({len(variables)} total)"


def _fn_summary(functions: List[Dict[str, Any]]) -> str:
    """One-line summary per function for handouts."""
    lines = []
    for fn in functions:
        lines.append(f"- **{fn['name']}** -- {fn.get('purpose', 'N/A')}")
    return "\n".join(lines) if lines else "No R functions found in the registry."


def _ct_summary(ct_vars: List[Dict[str, str]]) -> str:
    """Summarise CT-controlled variables."""
    if not ct_vars:
        return "No controlled terminology variables identified."
    lines = []
    for v in ct_vars:
        lines.append(
            f"- **{v['variable']}** -- CT: {v.get('controlled_terminology', 'Yes')}"
        )
    return "\n".join(lines)


def _var_table(variables: List[Dict[str, str]]) -> str:
    """Markdown table of IG variables."""
    if not variables:
        return "No IG variable data available for this domain."
    header = "| Variable | Type | Required | CT | Notes |"
    sep = "|----------|------|----------|-----|-------|"
    rows = [header, sep]
    for v in variables:
        rows.append(
            f"| {v.get('variable', '')} "
            f"| {v.get('type', '')} "
            f"| {v.get('required', '')} "
            f"| {v.get('controlled_terminology', '')} "
            f"| {v.get('notes', '')} |"
        )
    return "\n".join(rows)


def _data_quality_summary(profile: Dict[str, Any]) -> str:
    """Summarise data quality from a raw data profile."""
    if "error" in profile:
        return f"Data profile unavailable: {profile['error']}"
    lines = [f"- **Rows:** {profile.get('nrows', 'N/A')}"]
    missing = profile.get("missing", {})
    cols_with_missing = [c for c, n in missing.items() if n > 0]
    if cols_with_missing:
        lines.append(
            f"- **Columns with missing values:** {', '.join(cols_with_missing[:6])}"
        )
    else:
        lines.append("- **Missing values:** none detected")
    lines.append(
        f"- **Variables:** {', '.join(profile.get('variables', [])[:10])}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Exercise generators per skill level
# ---------------------------------------------------------------------------


def _consumer_exercises(
    chapter: int,
    topic_cfg: Dict[str, Any],
    domain_ctx: DomainContext,
    project_ctx: ProjectContext,
) -> List[Dict[str, str]]:
    """Generate consumer-level exercises (guided walkthroughs, no code)."""
    domain = domain_ctx.domain
    exercises = []

    if not domain_ctx.ig_available:
        # Process-focused fallback
        exercises.append(_exercise_md(
            chapter, 1,
            f"Explore the {domain} Pipeline Environment",
            f"Use /check-environment to verify your setup is ready for {domain} domain processing.",
            15,
            ["Claude Code running in the project directory"],
            [
                f"### Step 1: Check Your Environment\n\nIn Claude Code, run:\n```\n/check-environment\n```\n\nRecord which checks pass and which fail.",
                f"### Step 2: Review the Configuration\n\nAsk Claude Code to show you the `orchestrator/config.yaml` file. "
                f"Identify the settings for:\n- Study ID\n- Domain\n- Output directory\n- R script path",
                f"### Step 3: Understand the Pipeline Stages\n\nAsk Claude Code: \"What are the 7 pipeline stages and what does each one do?\"\n\n"
                f"> Record the stages here:\n> _________________________________________________________________",
            ],
            [
                "How does each pipeline stage connect to the next?",
                "Which stages require human input?",
            ],
            [
                "Environment check output reviewed",
                "Config file settings identified",
                "7 pipeline stages listed",
            ],
        ))
        exercises.append(_exercise_md(
            chapter, 2,
            f"Understand {domain} Domain Outputs",
            f"Examine the output artifacts produced by the {domain} pipeline.",
            15,
            ["Completed Exercise 1"],
            [
                f"### Step 1: List Output Directories\n\nAsk Claude Code: \"What files are in orchestrator/outputs/?\"\n\nNote the subdirectories: specs, programs, datasets, qc, validation.",
                "### Step 2: Examine a Mapping Spec\n\nIf a spec exists, ask Claude Code to show you the spec JSON.\n\n"
                "Identify:\n- How many variables are mapped\n- Which variables require human decisions\n- What codelists are referenced",
                "### Step 3: Examine Validation Output\n\nIf validation output exists, ask Claude Code to read the P21 report.\n\n"
                "> What checks passed? What failed?\n> _________________________________________________________________",
            ],
            [
                "What is the difference between the draft spec and the approved spec?",
                "Why is the spec considered the 'single source of truth'?",
            ],
            [
                "Output directory structure documented",
                "Spec structure understood",
                "Validation report interpreted",
            ],
        ))
        exercises.append(_exercise_md(
            chapter, 3,
            f"Run and Observe the {domain} Pipeline",
            f"Watch the pipeline execute for the {domain} domain and observe each stage.",
            20,
            ["Completed Exercises 1-2", "R with arrow and haven packages"],
            [
                f"### Step 1: Run Spec Building\n\nIn Claude Code, run:\n```\n/run-pipeline spec_build\n```\n\nObserve what the spec builder does. What files were created?",
                "### Step 2: Review the Draft Spec\n\nRun:\n```\n/review-spec\n```\n\nLook at the variables that require human decisions.\n\n"
                "> How many decision points are there?\n> _________________________________________________________________",
                f"### Step 3: Observe Production Output\n\nRun:\n```\n/run-pipeline production\n```\n\nWhat R script was generated? What dataset format was used?",
            ],
            [
                "What would happen if the spec review failed?",
                "Why does the pipeline stop for human review?",
                f"How would this pipeline differ for a different domain (not {domain})?",
            ],
            [
                "Spec build stage completed and spec file created",
                "Draft spec reviewed with decision points noted",
                "Production stage run and output observed",
            ],
        ))
        return exercises

    # Domain-specific exercises using IG content
    req_vars = _var_list_str(domain_ctx.required_variables)
    ct_var_names = [v["variable"] for v in domain_ctx.ct_variables]

    exercises.append(_exercise_md(
        chapter, 1,
        f"Profile Raw {domain} Data",
        f"Use the /profile-data skill to analyse the raw {domain.lower()} data and identify data quality issues that will affect SDTM mapping.",
        15,
        ["Claude Code running in the project directory", "Environment check passing"],
        [
            f"### Step 1: Run the Data Profiling Skill\n\nIn Claude Code, type:\n```\n/profile-data\n```\n\n"
            f"This profiles the raw {domain} data ({domain_ctx.raw_data_profile.get('nrows', 'N/A')} rows).",
            _step_date_vars(domain_ctx),
            _step_ct_vars(domain_ctx),
            f"### Step 4: Identify Missing Data\n\n"
            f"> Which columns have missing values? What percentage?\n"
            f"> _________________________________________________________________\n>\n"
            f"> Are any required SDTM variables ({req_vars}) missing from the raw data?\n"
            f"> _________________________________________________________________",
        ],
        [
            "How would the data quality issues you found affect the mapping specification?",
            "Which R function from the registry would you use for each issue?",
            f"If you were profiling a different domain dataset, what different quality issues would you look for?",
        ],
        [
            "Data profile output showing all column statistics",
            "Identified data format inconsistencies",
            "Listed CT-controlled variables and their raw value distributions",
            "Noted missing data patterns",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 2,
        f"Run the {domain} Spec Builder",
        f"Execute the spec building stage and examine the draft mapping specification for the {domain} domain.",
        20,
        ["Completed Exercise 1"],
        [
            f"### Step 1: Run Spec Build\n\nIn Claude Code, run:\n```\n/run-pipeline spec_build\n```\n\n"
            f"The spec builder analyses the raw data and produces a draft mapping spec.",
            f"### Step 2: Open the Draft Spec\n\nAsk Claude Code to read the spec file at `orchestrator/outputs/specs/{domain.lower()}_mapping_spec.json`.\n\n"
            f"Identify:\n- How many variables are in the spec\n- Which variables reference controlled terminology\n- Which variables have `human_decision_required: true`\n\n"
            f"> Variables with decisions required:\n> _________________________________________________________________",
            f"### Step 3: Check Required Variables\n\nThe SDTM IG requires these variables for {domain}: {req_vars}.\n\n"
            f"Compare this list against the spec:\n\n"
            f"> Are all required variables present in the spec?\n> _________________________________________________________________\n>\n"
            f"> Are any extra variables included that are not required?\n> _________________________________________________________________",
        ],
        [
            "What is the difference between a 'Required' and 'Conditional' variable in the SDTM IG?",
            "Why does the spec builder flag certain variables for human decision?",
            "How does the function registry influence the mapping logic in the spec?",
        ],
        [
            "Spec build stage completed successfully",
            f"Draft spec with {domain} variables reviewed",
            "Decision points identified",
            "Required variables verified against IG",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 3,
        f"Review {domain} Spec Decision Points",
        f"Use /review-spec to interactively review the {domain} mapping specification and understand the decision points.",
        15,
        ["Completed Exercise 2", "Draft spec exists"],
        [
            f"### Step 1: Launch Spec Review\n\nIn Claude Code, run:\n```\n/review-spec\n```\n\n"
            f"The reviewer displays each variable and highlights those requiring decisions.",
            "### Step 2: Examine Decision Options\n\nFor each decision point, the reviewer shows:\n"
            "- Multiple approaches (A, B, C)\n- IG references for each approach\n- Pros and cons\n\n"
            "> Pick one decision point. What are the options and which would you choose?\n"
            "> _________________________________________________________________\n>\n"
            "> What IG reference supports your choice?\n"
            "> _________________________________________________________________",
            "### Step 3: Understand the Review Comments\n\nAfter the spec reviewer runs, check the review comments.\n\n"
            "> Were any issues flagged (missing variables, CT errors, derivation problems)?\n"
            "> _________________________________________________________________",
        ],
        [
            "Why can the AI not make these decisions autonomously?",
            "What company-specific standards might influence your choice?",
            "How would you document your decision rationale for regulatory submission?",
        ],
        [
            "Spec review completed",
            "Decision points examined with options listed",
            "Review comments understood",
        ],
    ))

    return exercises


def _operator_exercises(
    chapter: int,
    topic_cfg: Dict[str, Any],
    domain_ctx: DomainContext,
    project_ctx: ProjectContext,
) -> List[Dict[str, str]]:
    """Generate operator-level exercises (directed tasks, run tools)."""
    domain = domain_ctx.domain
    exercises = _consumer_exercises(chapter, topic_cfg, domain_ctx, project_ctx)

    # Add an operator-level exercise on top
    exercises.append(_exercise_md(
        chapter, len(exercises) + 1,
        f"Run Full {domain} Pipeline End-to-End",
        f"Execute the complete SDTM pipeline for {domain} and interpret all outputs.",
        30,
        ["Completed previous exercises", "R with arrow and haven packages"],
        [
            f"### Step 1: Run the Full Pipeline\n\nIn Claude Code, run:\n```\n/run-pipeline\n```\n\n"
            f"Watch each stage execute: spec_build -> spec_review -> human_review -> production -> qc -> compare -> validate.",
            "### Step 2: Make Human Review Decisions\n\nWhen the pipeline pauses for human review, you must make decisions.\n\n"
            "For each flagged variable:\n1. Read the options presented\n2. Consider the IG references and pros/cons\n3. Select your preferred approach\n4. Record your rationale\n\n"
            "> Decisions made:\n> _________________________________________________________________",
            "### Step 3: Interpret the Comparison Report\n\nAfter production and QC complete, read the comparison report.\n\n"
            f"Ask Claude Code: \"Read orchestrator/outputs/qc/{domain.lower()}_compare_report.txt\"\n\n"
            "> Did the comparison show a MATCH or MISMATCH?\n> _________________________________________________________________\n>\n"
            "> If MISMATCH: which variables differed?\n> _________________________________________________________________",
            "### Step 4: Review Validation Results\n\nRun:\n```\n/validate-dataset\n```\n\n"
            "> How many P21 checks passed? How many failed?\n> _________________________________________________________________\n>\n"
            "> What would you need to fix before regulatory submission?\n> _________________________________________________________________",
        ],
        [
            "What is the purpose of double programming (production + QC)?",
            "Why does the pipeline use different AI models for production vs QC?",
            "If validation fails, which agent should fix the issue?",
            f"How would you extend this pipeline to handle the {_other_domain(domain)} domain?",
        ],
        [
            "Full pipeline executed successfully",
            "Human review decisions recorded with rationale",
            "Comparison report interpreted",
            "Validation results reviewed and understood",
        ],
    ))

    return exercises


def _builder_exercises(
    chapter: int,
    topic_cfg: Dict[str, Any],
    domain_ctx: DomainContext,
    project_ctx: ProjectContext,
) -> List[Dict[str, str]]:
    """Generate builder-level exercises (write new components)."""
    domain = domain_ctx.domain
    exercises = []

    exercises.append(_exercise_md(
        chapter, 1,
        "Examine the Function Registry",
        "Read and understand the R function registry, then write a new entry for a custom function.",
        25,
        ["Python 3.11+", "Understanding of JSON format"],
        [
            "### Step 1: Read the Registry\n\nOpen `r_functions/function_registry.json` and examine the structure.\n\n"
            "For each function, note:\n- `name` and `purpose`\n- `when_to_use` conditions\n- `parameters` (required vs optional)\n- `dependencies`\n- `usage_examples`",
            "### Step 2: Understand Dependencies\n\nThe registry defines a dependency order:\n"
            f"**{' -> '.join(domain_ctx.function_dependency_order) if domain_ctx.function_dependency_order else 'iso_date -> derive_age -> assign_ct'}**\n\n"
            "> Why must iso_date run before derive_age?\n> _________________________________________________________________\n>\n"
            "> What would happen if functions ran in the wrong order?\n> _________________________________________________________________",
            "### Step 3: Write a New Registry Entry\n\nImagine you need an R function called `validate_length` that checks if a variable's "
            "values exceed a maximum character length.\n\nWrite a JSON registry entry for it with:\n- `name`, `file`, `purpose`\n- `when_to_use` (at least 2 conditions)\n- `parameters` (variable name, max length, action on failure)\n- `dependencies` (should run after assign_ct)\n- `usage_examples` (at least 1)\n\n"
            "Save your entry (do not add it to the real registry yet).\n\n"
            "> Your registry entry:\n> _________________________________________________________________",
        ],
        [
            "Why is the function registry JSON instead of parsing R source files?",
            "How do agents use the registry to generate correct R code?",
            "What would break if you added a function but forgot to register it?",
        ],
        [
            "Function registry structure understood",
            "Dependency order explained",
            "New registry entry written with correct format",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 2,
        f"Write a Custom R Function for {domain}",
        f"Create a new R function that validates {domain} domain-specific rules and register it.",
        35,
        ["R 4.x", "Completed Exercise 1"],
        [
            f"### Step 1: Identify a Validation Need\n\nReview the SDTM IG requirements for {domain}.\n\n"
            f"Required variables: {_var_list_str(domain_ctx.required_variables)}\n\n"
            "Choose a validation rule to implement. Examples:\n"
            "- USUBJID must follow the pattern STUDYID-SUBJID\n"
            "- AGE must be a positive integer\n"
            "- Date variables must be in ISO 8601 format\n\n"
            "> Validation rule chosen:\n> _________________________________________________________________",
            "### Step 2: Write the R Function\n\nCreate a new file `r_functions/validate_rule.R` containing:\n"
            "- A function that takes a data frame and the validation parameters\n- Returns a data frame with a flag column indicating pass/fail\n- Handles edge cases (NA values, unexpected types)\n\n"
            "```r\n# Template:\nvalidate_rule <- function(df, variable, rule, ...) {\n  # Your implementation here\n}\n```",
            "### Step 3: Register the Function\n\nAdd your function to `r_functions/function_registry.json` using the entry you designed in Exercise 1.\n\n"
            "Then verify the registry loads correctly:\n```bash\npython -c \"from orchestrator.core.function_loader import FunctionLoader; fl = FunctionLoader('r_functions/function_registry.json'); print(fl.get_function_by_name('validate_rule'))\"\n```",
        ],
        [
            "How would the production programmer agent use your new function?",
            "What tests would you write to verify your function works correctly?",
            "How does this pattern compare to writing SAS macros?",
        ],
        [
            "Validation rule identified and documented",
            "R function written and saved",
            "Function registered in function_registry.json",
            "Registry loads without errors",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 3,
        f"Create a Claude Code Skill for {domain}",
        f"Write a new slash command that checks {domain}-specific requirements.",
        30,
        ["Understanding of Claude Code skills", "Completed Exercises 1-2"],
        [
            f"### Step 1: Study Existing Skills\n\nRead the skills in `.claude/skills/`:\n"
            "- `run-pipeline.md`\n- `profile-data.md`\n- `validate-dataset.md`\n\n"
            "Note the common structure: frontmatter, Usage, Instructions, Valid Options, Output Format.",
            f"### Step 2: Design Your Skill\n\nCreate a skill file `.claude/skills/check-{domain.lower()}.md` that:\n"
            f"1. Reads the {domain} spec (draft or approved)\n"
            f"2. Checks that all required {domain} variables are present\n"
            "3. Verifies CT codelist references are valid\n"
            "4. Reports results in a formatted table\n\n"
            "Follow the exact frontmatter format of existing skills.",
            "### Step 3: Test Your Skill\n\nIn Claude Code, try running your new skill:\n```\n"
            f"/check-{domain.lower()}\n```\n\n"
            "> Did it work? What output did you see?\n> _________________________________________________________________",
        ],
        [
            "What makes a good skill vs something that should be a Python function?",
            "How do skills differ from MCP tools?",
            "What other skills would be useful for clinical programming?",
        ],
        [
            "Existing skills studied and structure understood",
            f"New /check-{domain.lower()} skill created",
            "Skill tested in Claude Code",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 4,
        "Modify the Spec Builder Agent",
        "Extend the spec builder to handle a new variable or mapping rule.",
        35,
        ["Python knowledge", "Completed Exercises 1-3"],
        [
            "### Step 1: Read the Spec Builder Source\n\nOpen `orchestrator/agents/spec_builder.py` and understand:\n"
            "- How `profile_raw_data()` works\n- How `build_draft_spec()` maps raw columns to SDTM variables\n- How the function registry is used\n- How decision points are flagged",
            "### Step 2: Add a New Variable Mapping\n\nChoose a variable not currently handled by the spec builder "
            "(e.g., a supplemental qualifier, or a derived variable like DMDY).\n\n"
            "Add the mapping entry to the `var_mapping` list in `build_draft_spec()`:\n"
            "```python\n(\"SOURCE_COL\", \"TARGET_VAR\", \"function_name\", {\"param\": \"value\"}),\n```\n\n"
            "> What variable did you add? What mapping logic did you use?\n> _________________________________________________________________",
            "### Step 3: Test Your Change\n\nRun the spec builder stage:\n```bash\npython orchestrator/main.py --domain DM --stage spec_build\n```\n\n"
            "Check that your new variable appears in the generated spec JSON.",
        ],
        [
            "How does the spec builder decide which function to use for each variable?",
            "What happens when a raw data column doesn't match any known mapping?",
            "How would you add support for an entirely new domain (e.g., AE)?",
        ],
        [
            "Spec builder source code understood",
            "New variable mapping added",
            "Spec builder runs successfully with the change",
            "New variable appears in generated spec",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 5,
        "Add an MCP Tool",
        "Create a new MCP tool that exposes training-relevant project information.",
        30,
        ["Python knowledge", "Understanding of MCP tools"],
        [
            "### Step 1: Study the MCP Server\n\nRead `mcp_server.py` and identify:\n"
            "- How tools are defined (name, description, inputSchema)\n- How tool handlers process requests\n- What data each tool returns",
            "### Step 2: Design a New Tool\n\nCreate a tool called `training_status` that:\n"
            "- Takes no parameters (or optional domain)\n- Returns: number of training chapters, list of chapter titles, coverage of skill levels\n\n"
            "Write the tool definition and handler function.",
            "### Step 3: Test the Tool\n\nRun the MCP server in CLI test mode:\n```bash\npython mcp_server.py\n```\n\n"
            "Call your new tool and verify the output.",
        ],
        [
            "When should functionality be an MCP tool vs a skill vs a Python function?",
            "How do MCP tools enable AI agents to access project data?",
            "What other MCP tools would be useful for this project?",
        ],
        [
            "MCP server structure understood",
            "New tool defined with schema",
            "Tool handler implemented",
            "Tool tested in CLI mode",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 6,
        f"Compare Our Approach with Industry: sdtm.oak",
        "Compare our R function registry pattern with the open-source sdtm.oak package used by Roche, Pfizer, Merck, GSK, and Vertex.",
        35,
        ["R 4.x", "Completed Exercises 1-5"],
        [
            "### Step 1: Research sdtm.oak\n\n"
            "The `sdtm.oak` R package (PHUSE EU 2023, PHUSE US 2024-2025) is an open-source,\n"
            "metadata-driven SDTM automation tool developed by Roche and the COSA collaboration\n"
            "(Pfizer, Merck, GSK, Vertex). It provides 22 reusable algorithms and achieves\n"
            "approximately 80% automation of SDTM domains.\n\n"
            "Read about sdtm.oak:\n"
            "- PHUSE EU 2023 paper: https://www.lexjansen.com/phuse/2023/si/PAP_SI02.pdf\n"
            "- PHUSE US 2025 poster: https://www.lexjansen.com/phuse-us/2025/pp/PAP_PP31.pdf\n"
            "- GitHub: https://github.com/pharmaverse/sdtm.oak\n\n"
            "> What are sdtm.oak's 'algorithms' and how do they compare to our R functions?\n"
            "> _________________________________________________________________",
            "### Step 2: Compare Architecture\n\nFill in this comparison table:\n\n"
            "| Feature | Our Project | sdtm.oak |\n"
            "|---------|-------------|----------|\n"
            "| Approach | Function registry + agent-generated R code | ? |\n"
            "| Metadata source | function_registry.json + IG markdown | ? |\n"
            "| CT mapping | assign_ct() with ct_lookup.csv | ? |\n"
            "| Date handling | iso_date() | ? |\n"
            "| Spec format | JSON + XLSX | ? |\n"
            "| Domain coverage | DM (extensible) | ? |\n"
            "| AI integration | LLM agents for code generation | ? |\n"
            "| QC approach | Independent double programming | ? |\n\n"
            "> Key differences:\n> _________________________________________________________________\n>\n"
            "> Key similarities:\n> _________________________________________________________________",
            "### Step 3: Design a Hybrid Approach\n\n"
            "Consider: could sdtm.oak's algorithms be integrated into our pipeline?\n\n"
            "Design a proposal that:\n- Uses sdtm.oak for standard transformations (the 80%)\n"
            "- Uses our LLM agents for non-standard mappings (the 20%)\n"
            "- Keeps the spec as the single source of truth\n- Maintains the human review gate\n\n"
            "> Your hybrid design:\n> _________________________________________________________________",
        ],
        [
            "What are the advantages of metadata-driven algorithms (sdtm.oak) vs LLM-generated code (our approach)?",
            "The industry achieves ~80% automation. What falls in the remaining 20%?",
            "How would you decide when to use a deterministic algorithm vs an LLM for a given transformation?",
            "What does the sdtm.oak collaboration (5 major pharma companies) tell you about industry direction?",
        ],
        [
            "sdtm.oak research completed and key features documented",
            "Architecture comparison table filled in",
            "Hybrid approach designed combining both patterns",
            "Trade-offs between deterministic and LLM approaches analysed",
        ],
    ))

    return exercises


def _architect_exercises(
    chapter: int,
    topic_cfg: Dict[str, Any],
    domain_ctx: DomainContext,
    project_ctx: ProjectContext,
) -> List[Dict[str, str]]:
    """Generate architect-level exercises (design systems)."""
    domain = domain_ctx.domain
    other = _other_domain(domain)
    exercises = []

    exercises.append(_exercise_md(
        chapter, 1,
        "Trace the Orchestrator Architecture",
        "Map the complete data flow from raw data through all agents to final validation.",
        30,
        ["Understanding of all pipeline stages"],
        [
            "### Step 1: Read main.py\n\nOpen `orchestrator/main.py` and trace the pipeline flow:\n"
            "1. Config loading and path setup\n2. State initialization\n3. Stage functions and error gates\n4. Comparison loop\n5. State persistence\n\n"
            "Draw a diagram showing the flow between stages, including error gates and loops.",
            "### Step 2: Map Agent Dependencies\n\nFor each agent, document:\n"
            "- Inputs (what files/data it reads)\n- Outputs (what files it produces)\n- Core modules used (function_loader, ig_client, spec_manager)\n- What happens on failure\n\n"
            "> Agent dependency map:\n> _________________________________________________________________",
            "### Step 3: Identify Architectural Decisions\n\nDocument 3 key design decisions in the orchestrator and explain why each was made:\n"
            "- Why spec-driven architecture?\n- Why different LLMs for production vs QC?\n- Why JSON persistence for state?\n\n"
            "> Your analysis:\n> _________________________________________________________________",
        ],
        [
            "What are the bottlenecks in the current pipeline?",
            "Which stages could run in parallel?",
            "How would you redesign the error handling for production use?",
        ],
        [
            "Pipeline flow diagram created",
            "Agent dependency map documented",
            "3 architectural decisions analysed",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 2,
        f"Design an Agent for the {other} Domain",
        f"Design a complete spec builder agent for the {other} domain, including IG content, function registry updates, and spec structure.",
        45,
        ["Completed Exercise 1", "Understanding of SDTM IG"],
        [
            f"### Step 1: Research {other} Domain Requirements\n\nUsing the SDTM IG (or `sdtm_ig_db/sdtm_ig_content/` as reference), identify:\n"
            f"- Required variables for {other}\n- Controlled terminology codelists\n- Key derivation rules\n- Variables that need human decisions\n\n"
            f"If no IG content exists for {other}, create `sdtm_ig_db/sdtm_ig_content/{other.lower()}_domain.md` following the format of `dm_domain.md`.",
            f"### Step 2: Design the Spec Builder Changes\n\nDocument what changes `spec_builder.py` needs for {other}:\n"
            f"- New variable mappings\n- New decision points\n- New function registry entries (if any)\n- New CT lookups\n\n"
            f"> Design document:\n> _________________________________________________________________",
            f"### Step 3: Design the Validation Rules\n\nDocument what P21 validation checks are specific to {other}:\n"
            "- Required variable checks\n- Domain-specific business rules\n- Cross-domain consistency checks\n\n"
            "> Validation rule list:\n> _________________________________________________________________",
        ],
        [
            f"What makes {other} domain processing different from {domain}?",
            "How does the IG-driven design make adding new domains easier?",
            "What shared infrastructure can be reused vs what needs new code?",
        ],
        [
            f"{other} domain requirements documented",
            "Spec builder changes designed",
            "Validation rules specified",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 3,
        "Design a Multi-Domain Orchestrator",
        "Extend the orchestrator to process multiple SDTM domains in a single run.",
        40,
        ["Completed Exercises 1-2"],
        [
            "### Step 1: Identify Cross-Domain Dependencies\n\nSome SDTM domains depend on others:\n"
            "- DM must be created before AE (RFSTDTC used for --DY derivations)\n- SUPPDM depends on DM decisions\n\n"
            "Map the dependency graph for at least 4 domains.",
            "### Step 2: Design the Multi-Domain Runner\n\nDesign changes to `main.py` that:\n"
            "- Accept `--domain DM,AE,VS` (comma-separated)\n- Resolve domain dependencies\n- Run domains in correct order (or in parallel where independent)\n- Track state per domain\n\n"
            "Write pseudocode for the multi-domain orchestration logic.",
            "### Step 3: Design Cross-Domain Validation\n\nDesign checks that verify consistency across domains:\n"
            "- Same subjects in DM and AE\n- Consistent RFSTDTC across domains\n- Consistent CT usage\n\nWrite the check specifications.",
        ],
        [
            "What parallelism opportunities exist in multi-domain processing?",
            "How would you handle partial failures (DM succeeds but AE fails)?",
            "What changes to the state manager are needed for multi-domain support?",
        ],
        [
            "Cross-domain dependencies mapped",
            "Multi-domain runner designed with pseudocode",
            "Cross-domain validation checks specified",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 4,
        "Design an LLM-Enhanced Pipeline",
        "Design how the orchestrator would work with live LLM calls (LIVE mode) vs template mode (OFF mode).",
        35,
        ["Understanding of LLM client architecture"],
        [
            "### Step 1: Compare OFF vs LIVE Mode\n\nRead `orchestrator/core/llm_client.py` and understand the three modes.\n\n"
            "For each agent, document:\n- What it does in OFF mode (template logic)\n- What it would do differently in LIVE mode (LLM-generated)\n- What guardrails are needed to ensure LLM output is safe\n\n"
            "> Mode comparison:\n> _________________________________________________________________",
            "### Step 2: Design Prompt Templates\n\nFor the spec builder agent, write the system prompt and user prompt that would be sent to Claude in LIVE mode.\n\n"
            "The prompts should:\n- Include function registry context\n- Include IG variable definitions\n- Include raw data profile\n- Request structured JSON output\n- Include safety guardrails",
            "### Step 3: Design Output Validation\n\nLLM output is not deterministic. Design a validation layer that:\n"
            "- Verifies the LLM-generated spec has all required fields\n- Checks that referenced codelists exist\n- Validates derivation logic is syntactically correct\n- Falls back to template mode on validation failure",
        ],
        [
            "What are the risks of using LLM-generated code in a regulatory context?",
            "How does the double-programming pattern (different LLMs) mitigate risk?",
            "What audit trail would regulators expect for AI-generated SDTM code?",
        ],
        [
            "OFF vs LIVE mode differences documented per agent",
            "Prompt templates written for spec builder",
            "Output validation layer designed",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 5,
        "Traceability-Driven QC vs Double Programming",
        "Analyse the emerging industry debate on whether traceability-driven validation can replace traditional double programming.",
        40,
        ["Completed Exercises 1-4", "Understanding of double programming"],
        [
            "### Step 1: Understand Double Programming\n\n"
            "Our pipeline uses two different LLMs (Sonnet for production, Opus for QC) to\n"
            "independently implement the same spec -- mirroring the traditional double-programming\n"
            "model where two different programmers write independent code.\n\n"
            "Read `orchestrator/agents/production_programmer.py` and `orchestrator/agents/qc_programmer.py`.\n\n"
            "> What makes the QC truly independent? What safeguards prevent the QC from\n"
            "> 'cheating' by seeing production code?\n"
            "> _________________________________________________________________\n>\n"
            "> What are the limitations of double programming? (Hint: what if the spec is wrong?)\n"
            "> _________________________________________________________________",
            "### Step 2: Research Traceability-Driven Validation\n\n"
            "The PharmaSUG 2025 paper AI-137 (\"Traceability and AI for QC of Clinical Trials\")\n"
            "argues that traceability-driven validation can replace double programming.\n\n"
            "The argument: if every transformation is traced from raw data through spec to\n"
            "final dataset with full provenance, you can validate correctness by tracing the\n"
            "chain rather than by rewriting everything from scratch.\n\n"
            "Consider our pipeline's traceability:\n"
            "- Spec maps raw variable -> SDTM variable with mapping logic\n"
            "- R code comments reference the spec\n"
            "- P21 validation checks the result against the spec\n"
            "- define.xml describes the transformation for regulators\n\n"
            "> Is our pipeline already 'traceability-driven'? What's missing?\n"
            "> _________________________________________________________________\n>\n"
            "> What would you add to make traceability strong enough to replace\n"
            "> independent QC?\n"
            "> _________________________________________________________________",
            "### Step 3: Design a Hybrid QC Strategy\n\n"
            "Design a risk-based QC approach for our pipeline that:\n"
            "- Uses **full double programming** for high-risk transformations (the 20%:\n"
            "  non-standard derivations, decision-dependent mappings)\n"
            "- Uses **traceability-driven validation** for standard transformations (the 80%:\n"
            "  assign_ct with known codelists, iso_date with ISO 8601)\n"
            "- Defines clear criteria for which category a transformation falls into\n\n"
            "Document:\n1. Risk classification criteria\n"
            "2. Which current pipeline variables would be 'standard' vs 'non-standard'\n"
            "3. What audit trail artifacts regulators would expect\n\n"
            "> Your hybrid QC design:\n> _________________________________________________________________",
        ],
        [
            "The FDA supports risk-based QC (PharmaSUG 2025 MM-227). How does this change the economics of double programming?",
            "If an AI-generated R script has full traceability back to the spec, is it 'higher quality' than a human-written script without traceability?",
            "What would it take to convince a regulatory agency to accept traceability-driven validation instead of double programming?",
            "How would you handle the case where the spec itself is wrong -- does traceability help or hurt?",
        ],
        [
            "Double programming model analysed with limitations identified",
            "Traceability-driven validation researched with gaps identified",
            "Hybrid QC strategy designed with risk classification criteria",
            "Regulatory implications documented",
        ],
    ))

    exercises.append(_exercise_md(
        chapter, 6,
        "Capstone: Build Your Own Agent",
        "Implement a new agent from scratch and integrate it into the orchestrator.",
        60,
        ["Completed all previous exercises"],
        [
            "### Step 1: Choose an Agent to Build\n\nPick one:\n"
            "- **Spec Diff Agent:** Compare two spec versions and report changes\n"
            "- **Data Quality Agent:** Profile raw data and auto-suggest mappings\n"
            "- **Documentation Agent:** Generate define.xml narrative from spec + data\n\n"
            "> Agent chosen: ____________________",
            "### Step 2: Implement the Agent\n\nCreate a new file in `orchestrator/agents/` following the pattern of existing agents:\n"
            "1. Module docstring\n2. Imports from core modules\n3. Main function with explicit parameters\n4. Return a dict with results\n\n"
            "Your agent should use at least 2 of: function_loader, ig_client, spec_manager.",
            "### Step 3: Integrate with main.py\n\nAdd your agent as a new pipeline stage:\n"
            "1. Import your agent function\n2. Create a `run_stage_youragent()` function\n3. Add it to the stages dict\n4. Test: `python orchestrator/main.py --domain DM --stage youragent`",
        ],
        [
            "How did you decide what core modules your agent needs?",
            "What error handling did you add?",
            "How would you test your agent in isolation vs as part of the pipeline?",
        ],
        [
            "Agent chosen and design documented",
            "Agent implemented in orchestrator/agents/",
            "Agent integrated into main.py as a new stage",
            "Agent runs successfully via --stage flag",
        ],
    ))

    return exercises


# ---------------------------------------------------------------------------
# Exercise markdown builder
# ---------------------------------------------------------------------------


def _exercise_md(
    chapter: int,
    num: int,
    title: str,
    objective: str,
    duration_minutes: int,
    prerequisites: List[str],
    steps: List[str],
    reflection: List[str],
    deliverables: List[str],
) -> Dict[str, str]:
    """Build an exercise markdown string and return {title, slug, content}."""
    prereqs = "\n".join(f"- {p}" for p in prerequisites)
    step_text = "\n\n".join(steps)
    refl_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(reflection))
    deliv_text = "\n".join(f"- [ ] {d}" for d in deliverables)

    content = f"""# Exercise {chapter}.{num}: {title}

## Objective
{objective}

## Time: {duration_minutes} minutes

## Prerequisites
{prereqs}

---

## Steps

{step_text}

---

## Reflection Questions

{refl_text}

---

## What You Should Have at the End

{deliv_text}
"""
    slug = _slugify(title)
    return {"title": title, "slug": slug, "content": content, "duration": duration_minutes}


def _step_date_vars(ctx: DomainContext) -> str:
    """Generate a step about examining date variables."""
    date_vars = [
        v["variable"]
        for v in ctx.ig_variables
        if v.get("variable", "").endswith(("DTC", "DT", "DTM"))
    ]
    if date_vars:
        var_names = ", ".join(date_vars[:4])
        return (
            f"### Step 2: Examine Date Variables\n\n"
            f"The {ctx.domain} domain requires ISO 8601 dates for: {var_names}.\n"
            f"Look at the profiling output for these columns:\n\n"
            f"> What date formats are present?\n"
            f"> _________________________________________________________________\n>\n"
            f"> Are there any partial dates?\n"
            f"> _________________________________________________________________\n\n"
            f"These will need conversion using the `iso_date()` R function."
        )
    return (
        "### Step 2: Examine Variable Formats\n\n"
        "Look at the data types reported by the profiler.\n\n"
        "> Are there any variables with inconsistent formats?\n"
        "> _________________________________________________________________"
    )


def _step_ct_vars(ctx: DomainContext) -> str:
    """Generate a step about examining CT-controlled variables."""
    if ctx.ct_variables:
        ct_names = ", ".join(v["variable"] for v in ctx.ct_variables[:4])
        return (
            f"### Step 3: Examine CT-Controlled Variables\n\n"
            f"The SDTM IG requires controlled terminology for: {ct_names}.\n"
            f"Look at the raw values:\n\n"
            f"> How many distinct values exist for each CT variable?\n"
            f"> _________________________________________________________________\n>\n"
            f"> Are there any 'Other Specify' entries?\n"
            f"> _________________________________________________________________\n\n"
            f"These will need mapping using the `assign_ct()` R function."
        )
    return (
        "### Step 3: Examine Variable Values\n\n"
        "Look at the distinct value counts for each variable.\n\n"
        "> Are there any variables with unexpected or inconsistent values?\n"
        "> _________________________________________________________________"
    )


def _other_domain(domain: str) -> str:
    """Return a different domain for cross-domain exercises."""
    others = {"DM": "AE", "AE": "VS", "VS": "LB", "LB": "DM"}
    return others.get(domain, "AE")


# ---------------------------------------------------------------------------
# Instructor guide generator
# ---------------------------------------------------------------------------


def _generate_instructor_guide(
    chapter: int,
    title: str,
    skill_level: str,
    exercises: List[Dict[str, str]],
    domain_ctx: DomainContext,
    project_ctx: ProjectContext,
) -> str:
    """Generate the instructor guide markdown."""
    level_cfg = SKILL_LEVEL_CONFIG[skill_level]
    domain = domain_ctx.domain

    prereqs = "\n".join(f"- {p}" for p in level_cfg["prerequisites"])
    total_minutes = sum(ex.get("duration", 20) for ex in exercises)

    # Exercise flow table
    ex_rows = ["| Exercise | Duration | Focus |", "|----------|----------|-------|"]
    for ex in exercises:
        ex_rows.append(f"| {ex['title']} | {ex.get('duration', 20)} min | Hands-on |")

    # Timing summary
    timing_rows = ["| Module | Duration | Running Total |", "|--------|----------|---------------|"]
    running = 0
    timing_rows.append(f"| Introduction + Setup | 15 min | 0:15 |")
    running = 15
    for ex in exercises:
        dur = ex.get("duration", 20)
        running += dur
        h, m = divmod(running, 60)
        timing_rows.append(f"| {ex['title']} | {dur} min | {h}:{m:02d} |")
    running += 15
    h, m = divmod(running, 60)
    timing_rows.append(f"| Wrap-up + Q&A | 15 min | {h}:{m:02d} |")

    skills_used = set()
    for ex in exercises:
        for line in ex.get("content", "").split("\n"):
            if "/run-pipeline" in line or "/profile-data" in line or "/review-spec" in line or "/validate-dataset" in line or "/check-environment" in line:
                for cmd in ["/run-pipeline", "/profile-data", "/review-spec", "/validate-dataset", "/check-environment"]:
                    if cmd in line:
                        skills_used.add(cmd)

    skills_list = ", ".join(sorted(skills_used)) if skills_used else "N/A"

    guide = f"""# Chapter {chapter}: {title} -- Instructor Guide

## Session Overview

| Item | Detail |
|------|--------|
| Duration | {level_cfg['typical_duration']} |
| Format | Instructor-led workshop (live demos + guided exercises) |
| Audience | {level_cfg['audience']} |
| Skill Level | {level_cfg['label']} |
| Domain | {domain} |
| Prerequisites | See below |
| Skills Used | {skills_list} |

### Prerequisites
{prereqs}

## Key Teaching Message

{"This session introduces learners to the SDTM pipeline as consumers -- observing what AI tools produce, understanding outputs, and learning where human judgment is essential." if skill_level == "consumer" else ""}{"This session puts learners in the operator seat -- running pipeline stages, making spec review decisions, and interpreting comparison and validation results." if skill_level == "operator" else ""}{"This session challenges learners to build new components -- R functions, Claude Code skills, agent modifications -- extending the orchestrator's capabilities." if skill_level == "builder" else ""}{"This session elevates learners to system designers -- architecting multi-domain pipelines, designing agents, and integrating LLM capabilities safely." if skill_level == "architect" else ""}

---

## Exercise Flow

{chr(10).join(ex_rows)}

### Facilitation Tips

- **Walk the room** (or monitor screens on Zoom) during exercises
- Allow extra time for setup issues (R packages, config.yaml paths)
- Encourage learners to explore beyond the prescribed steps
- Group discussion after each exercise: ask 2-3 participants to share findings
{"- For builder/architect exercises, pair up participants for code review" if skill_level in ("builder", "architect") else ""}

### Wrap-Up (15 min)

1. **Poll the room:** "What was the most useful thing you learned?"
2. **Review deliverables:** Ensure everyone completed the checklist
3. **Preview next level:** {"Move from understanding to directing -- the Operator level lets you run the pipeline yourself." if skill_level == "consumer" else ""}{"Move from directing to building -- the Builder level has you write new R functions and skills." if skill_level == "operator" else ""}{"Move from building to designing -- the Architect level challenges you to design multi-domain systems." if skill_level == "builder" else ""}{"This is the capstone level -- you now have the skills to design and build AI-assisted clinical programming systems." if skill_level == "architect" else ""}

---

## Timing Summary

{chr(10).join(timing_rows)}
"""
    return guide


# ---------------------------------------------------------------------------
# Deliverables checklist generator
# ---------------------------------------------------------------------------


def _generate_deliverables_checklist(
    chapter: int,
    title: str,
    exercises: List[Dict[str, str]],
    skill_level: str,
) -> str:
    """Generate the deliverables checklist markdown."""
    level_cfg = SKILL_LEVEL_CONFIG[skill_level]
    sections = []

    for ex in exercises:
        # Extract deliverables from exercise content
        content = ex.get("content", "")
        items = []
        in_deliverables = False
        for line in content.split("\n"):
            if "What You Should Have at the End" in line:
                in_deliverables = True
                continue
            if in_deliverables and line.strip().startswith("- [ ]"):
                items.append(line.strip()[6:].strip())
            elif in_deliverables and line.strip() == "":
                continue
            elif in_deliverables and not line.strip().startswith("-"):
                in_deliverables = False

        item_lines = "\n".join(f"- [ ] {item}" for item in items) if items else "- [ ] Exercise completed"
        sections.append(f"## {ex['title']}\n\n{item_lines}")

    sections_text = "\n\n".join(sections)

    # Self-assessment skills
    assessment_skills = {
        "consumer": [
            "Running environment checks and profiling data",
            "Reading and understanding mapping specifications",
            "Identifying where human judgment is needed",
            "Interpreting pipeline outputs and validation reports",
        ],
        "operator": [
            "Running the full SDTM pipeline end-to-end",
            "Making informed spec review decisions",
            "Interpreting comparison and validation results",
            "Troubleshooting pipeline failures",
        ],
        "builder": [
            "Writing and registering R functions",
            "Creating Claude Code skills",
            "Modifying agent source code",
            "Adding MCP tools",
            "Comparing our approach with industry tools (sdtm.oak)",
        ],
        "architect": [
            "Tracing orchestrator architecture and data flow",
            "Designing agents for new SDTM domains",
            "Designing multi-domain orchestration",
            "Evaluating LLM integration safety",
            "Analysing traceability-driven QC vs double programming",
        ],
    }

    skills = assessment_skills.get(skill_level, assessment_skills["consumer"])
    assessment_rows = "\n".join(
        f"| {skill} | [ ] | [ ] | [ ] |" for skill in skills
    )

    return f"""# Chapter {chapter} Deliverables Checklist

## Participant Name: ____________________
## Date: ____________________

---

{sections_text}

---

## Self-Assessment

After completing all exercises, rate your confidence:

| Skill | Not confident | Somewhat | Confident |
|-------|:---:|:---:|:---:|
{assessment_rows}
"""


# ---------------------------------------------------------------------------
# Reference handout generator
# ---------------------------------------------------------------------------


def _generate_reference_handout(
    domain_ctx: DomainContext,
) -> str:
    """Generate a domain variable reference handout."""
    domain = domain_ctx.domain

    return f"""# {domain} Domain Variable Reference

## Required Variables

{_var_list_str(domain_ctx.required_variables, limit=20)}

## Variable Summary

{_var_table(domain_ctx.ig_variables)}

## R Functions Available

{_fn_summary(domain_ctx.available_functions)}

## Function Dependency Order

{' -> '.join(domain_ctx.function_dependency_order) if domain_ctx.function_dependency_order else 'N/A'}

## CT-Controlled Variables

{_ct_summary(domain_ctx.ct_variables)}

## Raw Data Quality Summary

{_data_quality_summary(domain_ctx.raw_data_profile)}
"""


def _generate_industry_landscape_handout(
    skill_level: str,
    domain: str,
) -> str:
    """Generate an industry landscape handout based on recent conference papers."""

    # Papers curated from LexJansen.com research (PharmaSUG, PHUSE 2023-2025)
    core_references = """
## Key Industry Papers (2023-2025)

The architecture used in this training project mirrors patterns emerging across
the pharmaceutical industry. These papers validate the approach and provide
additional context.

### Spec-Driven AI Pipelines

| Paper | Conference | Key Finding |
|-------|-----------|-------------|
| Automating SDTM Programming with Generative AI (AI144) | PharmaSUG CN 2025 | End-to-end LLM pipeline: metadata -> prompt -> Python code -> iterative QC. Mirrors our orchestrator architecture. |
| Natural Language to Code: AI-Powered CDISC R Code (ML10) | PHUSE US 2025 (Best Presentation) | Translates natural language specs into CDISC-compliant R code. Validates our Production Programmer approach. |
| AI Application -- Spec Files to SAS (AI171) | PharmaSUG CN 2025 | AI-based spec recognition and code generation from specifications. |

### RAG for CDISC Standards

| Paper | Conference | Key Finding |
|-------|-----------|-------------|
| SDTM Spec Automation Using ML with RAG (ML20) | PHUSE US 2025 | Two-stage RAG + agentic flow for spec creation. Validates our `ig_client.py` + agent design. |
| From RAGS to Riches: CDISC Agent in R (ML11) | PHUSE US 2025 | RAG-based CDISC standards agent. Productized version of our IG query approach. |
| Everyday AI for Statistical Programmers (ML15) | PHUSE EU 2025 | Roche's global deployment uses RAG + MCP + LLM Agents -- same technologies as our project. |

### Human-in-the-Loop

| Paper | Conference | Key Finding |
|-------|-----------|-------------|
| SDTM Transformation with AI + HITL (SM10) | PHUSE US 2025 | Framework combining AI variable mapping with human validation. Validates our human review gate. |
| Safe Integration of AI in Clinical Programming (ET09) | PHUSE US 2024 | AI augments programmers, does not replace them. Key principle for responsible adoption. |
| ACIRA: Human-AI Collaboration for ADaM (AA172) | PharmaSUG CN 2025 | Intuitive interfaces for human-AI collaboration in code generation. |

### Validation Paradigm Shift

| Paper | Conference | Key Finding |
|-------|-----------|-------------|
| Traceability and AI for QC of Clinical Trials (AI-137) | PharmaSUG 2025 | Traceability-driven validation can replace double programming. 80% of SDTM is automatable; 20% needs human judgment. |
| AI-Enhanced CRO Deliverable Management (MM-227) | PharmaSUG 2025 | FDA supports risk-based QC and AI use in clinical development. |
| SDTM/ADaM Automation Challenges (SM03) | PHUSE US 2024 | Even validated code generators do not eliminate QC needs. |

### Open-Source SDTM Automation

| Paper | Conference | Key Finding |
|-------|-----------|-------------|
| sdtm.oak: Metadata-Driven SDTM in R (SI02) | PHUSE EU 2023 | Roche + COSA open-source R package. 22 reusable algorithms, 80% domain automation. |
| sdtm.oak Evolution (OS09, PP31) | PHUSE US 2024-2025 | Industry collaboration: Roche, Pfizer, Merck, GSK, Vertex. EDC-agnostic, CDASH-driven. |
| R-Based CT Mapping Automation (DS-338) | PharmaSUG 2025 | Automated CDISC controlled terminology mapping in R. |
"""

    landscape_summary = f"""# AI for SDTM Programming: Industry Landscape

## Where Our Project Fits

This training project implements patterns that the pharmaceutical industry is
independently converging on across multiple companies and conferences (2023-2025).
Understanding the industry landscape helps you see that these are not experimental
ideas -- they are becoming standard practice.

## Architecture Patterns Validated by Industry

Our orchestrator uses five key patterns. Each is validated by multiple industry papers:

### 1. Spec as Single Source of Truth
Nearly all successful SDTM automation systems treat the mapping specification as
the canonical document that drives code generation, validation, and define.xml.
Our pipeline enforces this: the spec drives the R code, the P21 checks, and the
metadata.

### 2. RAG for Regulatory Standards
Retrieval Augmented Generation (RAG) over SDTM IG content is becoming the
standard approach for grounding AI outputs in actual CDISC standards. Our
`ig_client.py` + `sdtm_ig_db/` implements this pattern. Eli Lilly, Saama, and
Roche all independently built similar systems.

### 3. Multi-Agent / Agentic Flows
Using multiple specialised agents (spec builder, reviewer, programmer, QC,
validator) rather than one monolithic system. Saama's PHUSE US 2025 paper
describes a near-identical "agentic flow" architecture.

### 4. Human-in-the-Loop at Decision Points
The SDTM IG is often ambiguous (RACE handling, RFSTDTC derivation, date
imputation). AI presents options with evidence; humans decide. Multiple papers
(SM10, ET09, AA172) confirm this is the right approach.

### 5. MCP (Model Context Protocol) for Tool Integration
Roche's PHUSE EU 2025 paper explicitly mentions MCP alongside RAG and LLM
Agents for clinical programming -- the same protocol our `mcp_server.py` uses.

## The 80/20 Rule

Industry consensus (PharmaSUG 2025 AI-137, PHUSE EU 2023 SI02):
- **80% of SDTM domains** can be automated with high confidence using
  metadata-driven approaches
- **20% of mappings** (non-standard derivations, ambiguous IG guidance,
  sponsor-specific conventions) still require expert human judgment

This is why our pipeline has both automated agents AND a human review gate.

## Technology Trends

| Technology | Industry Adoption | Our Project |
|-----------|------------------|-------------|
| R for SDTM | Growing fast (sdtm.oak, Eli Lilly, multiple papers) | Primary language |
| Python for orchestration | Standard for LLM APIs and pipeline coordination | Orchestrator + compare |
| RAG over CDISC docs | Emerging standard (Lilly, Saama, Roche) | `ig_client.py` + `sdtm_ig_content/` |
| Vector databases | pgvector, ChromaDB used in multiple RAG papers | `ig_client.py` database mode (pgvector) |
| Graph databases | Emerging for CDISC relationship modeling (domain dependencies, codelist hierarchies) | Not yet implemented (see Ch.3 discussion) |
| MCP protocol | Mentioned by Roche (PHUSE EU 2025) | `mcp_server.py` |
| Agentic AI flows | Multiple 2025 papers | 5-agent pipeline |
| Workflow orchestration (n8n, Zapier) | Used as trigger/notification layers around AI pipelines | Claude Code + hooks (pipeline orchestration) |
| Human-in-the-loop | Universal consensus | Human review gate |

{core_references}

## Key Conferences to Follow

- **PharmaSUG** (pharmasug.org) -- Annual, US + China editions. Largest clinical
  programming conference.
- **PHUSE** (phuse.global) -- US Connect + EU Connect. Strong ML/AI track since 2020.
- **CDISC** (cdisc.org) -- Standards body. Interchange conference.

Papers available at: https://www.lexjansen.com

## Discussion Questions

1. How does knowing the industry landscape change your perspective on AI-assisted
   clinical programming?
2. Which industry approach (RAG, agentic flows, traceability-driven QC) do you
   think has the most potential for your organisation?
3. The 80/20 rule suggests 80% automation is achievable. What falls in the 20%
   that still needs human judgment at your company?
"""
    return landscape_summary


# ---------------------------------------------------------------------------
# Metadata generator
# ---------------------------------------------------------------------------


def _generate_metadata(
    chapter: int,
    title: str,
    skill_level: str,
    domain: str,
    topic: str,
    study_id: str,
    exercises: List[Dict[str, str]],
    guide_path: str,
    handout_paths: List[str],
) -> Dict[str, Any]:
    """Generate chapter metadata JSON."""
    level_cfg = SKILL_LEVEL_CONFIG[skill_level]

    return {
        "chapter_number": chapter,
        "chapter_id": f"chapter_{chapter}_{domain.lower()}_{topic}",
        "title": title,
        "skill_level": skill_level,
        "skill_level_label": level_cfg["label"],
        "domain": domain,
        "topic": topic,
        "study_id": study_id,
        "duration": level_cfg["typical_duration"],
        "format": "Instructor-led workshop",
        "audience": level_cfg["audience"],
        "prerequisites": level_cfg["prerequisites"],
        "exercises": [
            {
                "id": f"{chapter}.{i+1}",
                "title": ex["title"],
                "duration_minutes": ex.get("duration", 20),
                "file": f"exercises/exercise_{chapter}_{i+1}_{ex['slug']}.md",
            }
            for i, ex in enumerate(exercises)
        ],
        "guide_file": guide_path,
        "handouts": handout_paths,
        "generated_by": "training_generator",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_training_chapter(
    chapter_number: int,
    skill_level: str,
    domain: str,
    topic: str,
    study_id: str,
    output_dir: str,
    function_loader: FunctionLoader,
    ig_client: IGClient,
    spec_manager: SpecManager,
    llm_client: Any = None,
) -> Dict[str, Any]:
    """
    Generate a complete training chapter package.

    Returns a dict with chapter_number, title, exercises, guide_path,
    handouts, metadata_path, and errors.
    """
    errors: List[str] = []

    # Validate skill level
    if skill_level not in SKILL_LEVEL_CONFIG:
        return {
            "chapter_number": chapter_number,
            "title": "",
            "errors": [f"Invalid skill level: {skill_level}. Use: {list(SKILL_LEVEL_CONFIG.keys())}"],
        }

    # Validate topic
    if topic not in TOPIC_EXERCISE_MAP:
        return {
            "chapter_number": chapter_number,
            "title": "",
            "errors": [f"Invalid topic: {topic}. Use: {list(TOPIC_EXERCISE_MAP.keys())}"],
        }

    level_cfg = SKILL_LEVEL_CONFIG[skill_level]
    topic_cfg = TOPIC_EXERCISE_MAP[topic]

    # Gather context
    raw_data_path = ""
    project_root = Path(output_dir).resolve().parent
    try:
        import yaml
        config_path = project_root / "orchestrator" / "config.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        raw_data_path = str(
            project_root / config.get("paths", {}).get("raw_data", f"study_data/raw_{domain.lower()}.csv").lstrip("./")
        )
    except Exception:
        config = {}
        raw_data_path = str(project_root / f"study_data/raw_{domain.lower()}.csv")

    domain_ctx = gather_domain_context(domain, ig_client, function_loader, raw_data_path)
    project_ctx = gather_project_context(config, spec_manager, domain, project_root)

    if not domain_ctx.ig_available:
        errors.append(
            f"IG content not available for {domain} domain. "
            f"Exercises are process-focused. "
            f"To add domain-specific exercises, create sdtm_ig_db/sdtm_ig_content/{domain.lower()}_domain.md"
        )

    # Build title
    topic_label = topic.replace("_", " ").title()
    title = f"SDTM {domain} {topic_label} for {level_cfg['label']}s"

    # Generate exercises based on skill level
    exercise_generators = {
        "consumer": _consumer_exercises,
        "operator": _operator_exercises,
        "builder": _builder_exercises,
        "architect": _architect_exercises,
    }
    exercises = exercise_generators[skill_level](
        chapter_number, topic_cfg, domain_ctx, project_ctx
    )

    # Create output directories
    dir_name = f"chapter_{chapter_number}_{domain.lower()}_{topic}"
    chapter_dir = Path(output_dir) / dir_name
    (chapter_dir / "exercises").mkdir(parents=True, exist_ok=True)
    (chapter_dir / "guide").mkdir(parents=True, exist_ok=True)
    (chapter_dir / "handouts").mkdir(parents=True, exist_ok=True)

    # Write exercises
    exercise_paths = []
    for i, ex in enumerate(exercises):
        filename = f"exercise_{chapter_number}_{i+1}_{ex['slug']}.md"
        path = chapter_dir / "exercises" / filename
        path.write_text(ex["content"], encoding="utf-8")
        exercise_paths.append(str(path))

    # Write instructor guide
    guide_content = _generate_instructor_guide(
        chapter_number, title, skill_level, exercises, domain_ctx, project_ctx
    )
    guide_rel = f"guide/chapter_{chapter_number}_instructor_guide.md"
    guide_path = chapter_dir / "guide" / f"chapter_{chapter_number}_instructor_guide.md"
    guide_path.write_text(guide_content, encoding="utf-8")

    # Write deliverables checklist
    checklist_content = _generate_deliverables_checklist(
        chapter_number, title, exercises, skill_level
    )
    checklist_path = chapter_dir / "handouts" / "deliverables_checklist.md"
    checklist_path.write_text(checklist_content, encoding="utf-8")

    # Write reference handout (only if IG data available)
    handout_paths_list = ["handouts/deliverables_checklist.md"]
    if domain_ctx.ig_available:
        ref_content = _generate_reference_handout(domain_ctx)
        ref_path = chapter_dir / "handouts" / f"{domain.lower()}_variable_reference.md"
        ref_path.write_text(ref_content, encoding="utf-8")
        handout_paths_list.append(f"handouts/{domain.lower()}_variable_reference.md")

    # Write industry landscape handout (builder and architect levels)
    if skill_level in ("builder", "architect"):
        landscape_content = _generate_industry_landscape_handout(skill_level, domain)
        landscape_path = chapter_dir / "handouts" / "industry_landscape.md"
        landscape_path.write_text(landscape_content, encoding="utf-8")
        handout_paths_list.append("handouts/industry_landscape.md")

    # Write metadata
    metadata = _generate_metadata(
        chapter_number, title, skill_level, domain, topic,
        study_id, exercises, guide_rel, handout_paths_list,
    )
    meta_path = chapter_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "chapter_number": chapter_number,
        "title": title,
        "skill_level": skill_level,
        "domain": domain,
        "topic": topic,
        "directory": str(chapter_dir),
        "metadata_path": str(meta_path),
        "exercises": [
            {"id": f"{chapter_number}.{i+1}", "title": ex["title"], "path": p}
            for i, (ex, p) in enumerate(zip(exercises, exercise_paths))
        ],
        "guide_path": str(guide_path),
        "handouts": [str(chapter_dir / h) for h in handout_paths_list],
        "errors": errors,
    }
