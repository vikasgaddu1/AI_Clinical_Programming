# AI Orchestrator Implementation Guide

## Executive Summary

This guide explains how to implement an AI Orchestrator that uses the SAS Macro Library registry to automatically generate and execute SDTM transformation code.

The key insight: **The macro_registry.json file is a machine-readable specification** that enables AI systems to understand what macros are available, what they do, what parameters they need, and how they depend on each other.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     AI ORCHESTRATOR                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Registry Loader       (Parses JSON)                     │
│  2. Input Analyzer        (Examines dataset structure)      │
│  3. Macro Selector        (Matches patterns to macros)      │
│  4. Dependency Resolver   (Sorts by dependencies)           │
│  5. Code Generator        (Creates SAS code)                │
│  6. SAS Executor          (Runs the code)                   │
│  7. Result Validator      (Checks outputs)                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────────┐
│        macro_registry.json (Machine-Readable Spec)           │
├──────────────────────────────────────────────────────────────┤
│  - Macro metadata (name, purpose, category)                 │
│  - Parameter specifications (type, required, default)       │
│  - When-to-use criteria (decision logic hints)              │
│  - Dependencies (sequencing rules)                          │
│  - Usage examples (reference implementations)               │
│  - Orchestrator integration guidelines                      │
└──────────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────────┐
│           SAS Macro Library (Executable Code)                │
├──────────────────────────────────────────────────────────────┤
│  - iso_date.sas         (Date conversion macro)             │
│  - derive_age.sas       (Age calculation macro)             │
│  - assign_ct.sas        (CT mapping macro)                  │
│  - ct_lookup.csv        (Reference data)                    │
└──────────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────────┐
│                    SAS System (Execution)                    │
├──────────────────────────────────────────────────────────────┤
│  Input Dataset → [Macro Calls] → Output Dataset             │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Load and Parse the Registry

### What to Load

Load `macro_registry.json` into a data structure. This file contains:

```json
{
  "registry_version": "1.0",
  "macros": [
    {
      "name": "%iso_date",
      "purpose": "Convert dates to ISO 8601",
      "parameters": [...],
      "dependencies": [...],
      ...
    }
  ]
}
```

### Python Example

```python
import json

with open('macro_registry.json') as f:
    registry = json.load(f)

# Access macros
for macro in registry['macros']:
    print(f"{macro['name']}: {macro['purpose']}")
```

### JavaScript Example

```javascript
fetch('macro_registry.json')
  .then(response => response.json())
  .then(registry => {
    registry.macros.forEach(macro => {
      console.log(`${macro.name}: ${macro.purpose}`);
    });
  });
```

---

## Step 2: Analyze Input Dataset

Examine the input dataset to understand what needs to be done.

### Detection Patterns

Create pattern-matching rules based on variable names:

```python
def analyze_input(variable_names):
    needs = {
        'date_conversions': [],
        'age_derivations': False,
        'ct_mappings': {},
        'other': []
    }
    
    # Pattern 1: Date conversion needed
    date_patterns = ['BRTHDT', 'RFSTDTC', 'DATE', 'DTND']
    for var in variable_names:
        if 'RAW_' in var and any(p in var for p in date_patterns):
            needs['date_conversions'].append(var)
    
    # Pattern 2: Age derivation
    if ('RAW_BRTHDT' in variable_names and 
        'RAW_RFSTDTC' in variable_names):
        needs['age_derivations'] = True
    
    # Pattern 3: CT mappings
    ct_map = {
        'RAW_SEX': 'C66731',
        'RAW_RACE': 'C74457',
        'RAW_ETHNIC': 'C66790'
    }
    for var, code in ct_map.items():
        if var in variable_names:
            needs['ct_mappings'][var] = code
    
    return needs
```

---

## Step 3: Select Applicable Macros

Match detected needs to macros from the registry.

### Selection Logic

```python
def select_macros(analysis, registry):
    selected = []
    macro_map = {m['name']: m for m in registry['macros']}
    
    if analysis['date_conversions']:
        selected.append(macro_map['%iso_date'])
    
    if analysis['age_derivations']:
        selected.append(macro_map['%derive_age'])
    
    if analysis['ct_mappings']:
        selected.append(macro_map['%assign_ct'])
    
    return selected
```

### When-to-Use Criteria

The registry includes "when_to_use" guidance:

```json
"when_to_use": [
  "Whenever a raw date variable needs to be converted to SDTM-compliant ISO 8601 format (YYYY-MM-DD)",
  "Use this instead of writing custom date conversion code",
  "Apply to birth dates, event dates, and any SDTM date variables requiring standardization"
]
```

Use these as hints for your selection logic.

---

## Step 4: Resolve Dependencies

Order macros correctly by respecting dependencies.

### Dependency Information

From the registry, each macro lists its dependencies:

```json
"dependencies": [
  "Requires birth date to be in ISO format or numeric SAS date",
  "Requires reference date to be in ISO format or numeric SAS date"
]
```

### Topological Sort Implementation

```python
def topological_sort(macros):
    """Sort macros by dependencies using DFS"""
    graph = {}
    for macro in macros:
        graph[macro['name']] = macro.get('dependencies', [])
    
    sorted_list = []
    visited = set()
    
    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                dfs(dep)
        sorted_list.append(node)
    
    for macro in macros:
        dfs(macro['name'])
    
    return sorted_list
```

### Example Sequence

For raw DM domain transformation:

```
1. %iso_date (RAW_BRTHDT → BRTHDTC)          [No dependencies]
2. %iso_date (RAW_RFSTDTC → RFSTDTC)         [No dependencies]
3. %derive_age (BRTHDTC, RFSTDTC → AGE)      [Depends on 1-2]
4. %assign_ct (RAW_SEX → SEX)                [No dependencies]
5. %assign_ct (RAW_RACE → RACE)              [No dependencies]
```

---

## Step 5: Parametrize Each Macro Call

Extract parameter specifications from the registry and fill in actual values.

### Parameter Specification Format

```json
"parameters": [
  {
    "name": "inds",
    "type": "dataset name",
    "required": true,
    "description": "Input dataset name",
    "example": "raw.dm"
  },
  {
    "name": "outds",
    "type": "dataset name",
    "required": true,
    "description": "Output dataset name",
    "example": "work.dm_iso"
  },
  {
    "name": "infmt",
    "type": "SAS format",
    "required": false,
    "default": "(auto-detect)",
    "description": "Input format for parsing"
  }
]
```

### Parametrization Logic

```python
def parametrize_macro(macro, inputs, chain_number):
    """Generate parameter values for a macro call"""
    params = {}
    
    for param in macro['parameters']:
        if param['required']:
            # Required parameters - must be provided
            if param['name'] == 'inds':
                if chain_number == 1:
                    params['inds'] = 'raw.dm'
                else:
                    params['inds'] = f'work.dm_step{chain_number-1}'
            elif param['name'] == 'outds':
                params['outds'] = f'work.dm_step{chain_number}'
            elif param['name'] == 'invar':
                params['invar'] = inputs[0]  # From analysis
            elif param['name'] == 'outvar':
                params['outvar'] = inputs[0].replace('RAW_', '')
        else:
            # Optional parameters - use defaults or skip
            if 'default' in param and param['default'] != '(auto-detect)':
                params[param['name']] = param['default']
    
    return params
```

---

## Step 6: Generate SAS Code

Combine selected macros with parametrized calls.

### Code Generation Template

```python
def generate_sas_code(ordered_macros, parametrizations):
    """Generate executable SAS code"""
    code = [
        "/* AUTO-GENERATED SAS CODE FROM AI ORCHESTRATOR */",
        "/* Generated from macro_registry.json */",
        ""
    ]
    
    for i, (macro, params) in enumerate(zip(ordered_macros, parametrizations), 1):
        code.append(f"/* Step {i}: {macro['purpose']} */")
        
        # Build macro call
        macro_name = macro['name']
        param_list = []
        for key, value in params.items():
            if isinstance(value, str) and not value.startswith('work.'):
                param_list.append(f"{key}={value}")
            else:
                param_list.append(f"{key}={value}")
        
        macro_call = f"%{macro_name.replace('%', '')}({', '.join(param_list)});"
        code.append(macro_call)
        code.append("")
    
    return "\n".join(code)
```

### Example Generated Code

```sas
/* AUTO-GENERATED SAS CODE FROM AI ORCHESTRATOR */

/* Step 1: Convert RAW_BRTHDT to ISO 8601 */
%iso_date(inds=raw.dm, outds=work.dm_step1, invar=RAW_BRTHDT, outvar=BRTHDTC);

/* Step 2: Convert RAW_RFSTDTC to ISO 8601 */
%iso_date(inds=work.dm_step1, outds=work.dm_step2, invar=RAW_RFSTDTC, outvar=RFSTDTC);

/* Step 3: Derive AGE from BRTHDTC and RFSTDTC */
%derive_age(inds=work.dm_step2, outds=work.dm_step3, brthdt=BRTHDTC, 
            refdt=RFSTDTC, agevar=AGE);

/* Step 4: Map RAW_SEX to CDISC CT */
%assign_ct(inds=work.dm_step3, outds=work.dm_step4, invar=RAW_SEX, 
           outvar=SEX, codelist=C66731);

/* Step 5: Map RAW_RACE to CDISC CT */
%assign_ct(inds=work.dm_step4, outds=work.dm_final, invar=RAW_RACE, 
           outvar=RACE, codelist=C74457);
```

---

## Step 7: Execute SAS Code

Submit the generated code to SAS for execution.

### SAS Execution Methods

#### Method 1: Using Python (sasctl)

```python
import subprocess

def execute_sas_code(sas_code, macro_library_path):
    """Execute SAS code via subprocess"""
    
    # Create a SAS program file
    with open('temp_program.sas', 'w') as f:
        f.write(f"%include '{macro_library_path}/iso_date.sas';\n")
        f.write(f"%include '{macro_library_path}/derive_age.sas';\n")
        f.write(f"%include '{macro_library_path}/assign_ct.sas';\n")
        f.write("\n")
        f.write(sas_code)
    
    # Execute SAS
    result = subprocess.run(
        ['sas', '-sysin', 'temp_program.sas'],
        capture_output=True,
        text=True
    )
    
    return result
```

#### Method 2: Using SAS Viya (REST API)

```python
import requests

def execute_via_viya(sas_code, viya_url, session_token):
    """Execute via SAS Viya REST API"""
    
    headers = {
        'Authorization': f'Bearer {session_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'source': sas_code,
        'packages': ['SAS.Programming']
    }
    
    response = requests.post(
        f'{viya_url}/compute/sessions/{{session_id}}/code',
        json=payload,
        headers=headers
    )
    
    return response.json()
```

#### Method 3: Include in SAS Studio

```python
# Generate .sas file
with open('orchestrated_transformation.sas', 'w') as f:
    f.write(sas_code)

# User opens in SAS Studio and runs
print("Generated program: orchestrated_transformation.sas")
print("Open in SAS Studio and execute")
```

---

## Step 8: Validate Results

Check that the output is correct.

### Validation Checks

```python
def validate_results(output_dataset_name):
    """Validate macro execution results"""
    
    checks = {
        'dataset_exists': False,
        'expected_variables': [],
        'data_quality': {},
        'warnings': []
    }
    
    # Check 1: Dataset exists
    # (Would need SAS code or connection to check)
    
    # Check 2: Variables created
    # Verify BRTHDTC, RFSTDTC, AGE, SEX, RACE exist
    
    # Check 3: Data quality
    # - No unexpected nulls
    # - Dates in correct format (YYYY-MM-DD)
    # - CT values are valid
    # - Ages are reasonable (0-120)
    
    return checks
```

---

## Complete Implementation Example

See `orchestrator_example.py` in the macro library directory for a complete working implementation.

Run it:
```bash
python3 orchestrator_example.py
```

This demonstrates:
1. Loading the registry
2. Analyzing input variables
3. Selecting macros
4. Sequencing by dependencies
5. Generating SAS code
6. Output

---

## Integration Points

### For AI Orchestrators

1. **Read the registry** to discover macros
2. **Use when_to_use** to guide macro selection
3. **Check dependencies** to order macro calls
4. **Extract parameters** to understand what inputs are needed
5. **Use usage_examples** for reference implementations

### For SAS Programmers

1. **Include the macro files** in your SAS program
2. **Call macros in sequence** respecting dependencies
3. **Check the registry** for parameter specifications
4. **Consult the examples** for usage guidance
5. **Monitor SAS logs** for errors and warnings

---

## Error Handling

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Macro not found | Macro file not %included | Include macro files before calling |
| Parameter error | Wrong parameter name | Check registry for exact parameter names |
| Date parsing fails | Unsupported date format | Specify `infmt` parameter explicitly |
| CT mapping fails | Lookup file not found | Provide correct `ctpath` parameter |
| Age calculation wrong | Dates not in ISO format | Run %iso_date first |

### Logging and Debugging

```python
def log_orchestration_decision(decision, reason):
    """Log orchestration decisions for debugging"""
    import datetime
    
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'decision': decision,
        'reason': reason
    }
    
    # Save to log file
    with open('orchestration.log', 'a') as f:
        json.dump(log_entry, f)
        f.write('\n')
```

---

## Best Practices

1. **Always use the registry** - Don't hardcode macro knowledge
2. **Validate inputs** - Check that input datasets exist and have required variables
3. **Check for errors** - Parse SAS logs for ERROR and WARNING messages
4. **Chain datasets carefully** - Track intermediate datasets through the pipeline
5. **Document assumptions** - Log what patterns matched for macro selection
6. **Test on small samples** - Validate the transformation works before running on full data
7. **Version your registry** - Update when new macros or patterns are added
8. **Cache decisions** - Remember what worked for similar transformations

---

## Extending the Library

To add a new macro to the orchestrator's knowledge:

1. **Create the SAS macro file** with proper documentation
2. **Add entry to macro_registry.json** with complete metadata
3. **Test the orchestrator** with the new macro
4. **Document usage patterns** in when_to_use section
5. **Provide examples** in usage_examples array

New entry template:

```json
{
  "name": "%new_macro",
  "file": "new_macro.sas",
  "category": "Category Name",
  "purpose": "What this macro does",
  "when_to_use": ["Use case 1", "Use case 2"],
  "parameters": [
    {
      "name": "param1",
      "type": "dataset name",
      "required": true,
      "description": "Description",
      "example": "example_value"
    }
  ],
  "dependencies": ["Any dependencies"],
  "output_type": "Description of output",
  "usage_examples": [
    {
      "description": "Example scenario",
      "code": "%new_macro(param1=value);"
    }
  ]
}
```

---

## Registry Specification (Complete)

See `macro_registry.json` for the authoritative specification of:
- All available macros
- Complete parameter definitions
- Supported input/output types
- Orchestrator integration guidelines
- Example orchestration scenarios

---

## Support and Resources

- **Macro Library Path:** `/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/`
- **Registry File:** `macro_registry.json`
- **Documentation:** `README.md`
- **Example Implementation:** `orchestrator_example.py`
- **Macro Files:** `iso_date.sas`, `derive_age.sas`, `assign_ct.sas`
- **Lookup Data:** `ct_lookup.csv`

---

**This architecture enables AI systems to autonomously understand, select, and execute clinical programming transformations while maintaining full traceability and human oversight.**
