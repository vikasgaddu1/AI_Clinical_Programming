---
description: Generate complete training chapter packages (exercises, instructor guide, handouts) for any SDTM domain and skill level.
user-invocable: true
argument-hint: "[chapter_num] [level] [domain] [topic]"
---

# Generate Training Materials

Generate a complete training chapter package with exercises, instructor guide, and handouts for clinical programming training.

## Usage
- `/generate-training` -- Generate a default chapter (next available number, operator level, DM domain, full_pipeline topic)
- `/generate-training 5 operator DM spec_building` -- Chapter 5, Operator level, DM domain, spec building topic
- `/generate-training 6 builder AE full_pipeline` -- Chapter 6, Builder level, AE domain, full pipeline
- `/generate-training 7 architect DM validation` -- Chapter 7, Architect level, DM domain, validation topic

## Instructions

1. **Parse arguments:**
   - Argument 1: Chapter number (integer, default: next available)
   - Argument 2: Skill level (`consumer`, `operator`, `builder`, `architect`, default: `operator`)
   - Argument 3: Domain (`DM`, `AE`, `VS`, `LB`, etc., default: `DM`)
   - Argument 4: Topic (see Valid Topics below, default: `full_pipeline`)

2. **Verify prerequisites:**
   - Check that `orchestrator/config.yaml` exists and is valid
   - Check that `r_functions/function_registry.json` exists
   - If the IG content file for the requested domain is missing (`sdtm_ig_db/sdtm_ig_content/{domain}_domain.md`), warn that exercises will be process-focused

3. **Determine next chapter number if not specified:**
   - Scan `training/` for existing `chapter_*` directories
   - Use the next available number

4. **Run the training generator:**
   ```bash
   python -c "
   import sys; sys.path.insert(0, '.')
   from orchestrator.agents.training_generator import generate_training_chapter
   from orchestrator.core.function_loader import FunctionLoader
   from orchestrator.core.ig_client import IGClient
   from orchestrator.core.spec_manager import SpecManager
   import json

   fl = FunctionLoader('r_functions/function_registry.json')
   ig = IGClient({})
   sm = SpecManager('orchestrator/outputs')

   # Read study_id from config
   import yaml
   with open('orchestrator/config.yaml') as _f:
       _cfg = yaml.safe_load(_f)
   _study_id = _cfg.get('study', {}).get('study_id', 'XYZ-2026-001')

   result = generate_training_chapter(
       chapter_number=CHAPTER,
       skill_level='LEVEL',
       domain='DOMAIN',
       topic='TOPIC',
       study_id=_study_id,
       output_dir='training',
       function_loader=fl,
       ig_client=ig,
       spec_manager=sm,
   )
   print(json.dumps(result, indent=2))
   "
   ```
   Replace CHAPTER, LEVEL, DOMAIN, TOPIC with the parsed arguments.

5. **Report results:**
   - Show the chapter title and skill level
   - List all generated files with their paths
   - Report any warnings (e.g., domain IG content not found)
   - If errors occurred, display them

## Valid Skill Levels
`consumer`, `operator`, `builder`, `architect`

## Valid Topics
`data_profiling`, `spec_building`, `production_programming`, `qc_and_comparison`, `validation`, `full_pipeline`, `human_review`

## Output Format
```
Training Chapter Generated
==========================
Chapter: 5 - SDTM DM Spec Building for Operators
Level: Operator
Domain: DM
Topic: spec_building

Generated files:
  training/chapter_5_dm_spec_building/metadata.json
  training/chapter_5_dm_spec_building/exercises/exercise_5_1_....md
  training/chapter_5_dm_spec_building/exercises/exercise_5_2_....md
  training/chapter_5_dm_spec_building/guide/chapter_5_instructor_guide.md
  training/chapter_5_dm_spec_building/handouts/deliverables_checklist.md
  training/chapter_5_dm_spec_building/handouts/dm_variable_reference.md

Warnings: (if any)
```
