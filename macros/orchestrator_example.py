#!/usr/bin/env python3
"""
Example: AI Orchestrator Usage of SAS Macro Library Registry

This script demonstrates how an AI orchestrator would:
1. Load the macro registry
2. Analyze input dataset structure
3. Select appropriate macros
4. Sequence them by dependencies
5. Generate SAS code
6. Execute the code

This is a proof-of-concept example.
"""

import json
from typing import List, Dict, Set
from pathlib import Path


class SASMacroOrchestrator:
    """AI Orchestrator for SAS Macro Library"""
    
    def __init__(self, registry_path: str):
        """Load and parse the macro registry"""
        with open(registry_path) as f:
            self.registry = json.load(f)
        
        self.macros_by_name = {m['name']: m for m in self.registry['macros']}
        self.macros_by_file = {m['file']: m for m in self.registry['macros']}
        
        print(f"[ORCHESTRATOR] Loaded registry v{self.registry['registry_version']}")
        print(f"[ORCHESTRATOR] Available macros: {len(self.registry['macros'])}")
        for macro in self.registry['macros']:
            print(f"  - {macro['name']}: {macro['purpose']}")
    
    def analyze_input_dataset(self, variable_names: List[str]) -> Dict:
        """Analyze input dataset to understand what transformations are needed"""
        print(f"\n[ANALYSIS] Input dataset contains {len(variable_names)} variables:")
        for var in variable_names:
            print(f"  - {var}")
        
        analysis = {
            'needs_date_conversion': [],
            'needs_age_derivation': False,
            'needs_ct_mapping': {}
        }
        
        # Check for date variables that need conversion
        date_patterns = ['BRTHDT', 'RFSTDTC', 'DATE', 'DT', 'DTND', 'DTTM']
        for var in variable_names:
            if 'RAW_' in var and any(pattern in var for pattern in date_patterns):
                analysis['needs_date_conversion'].append(var)
        
        # Check if age derivation is needed
        if ('RAW_BRTHDT' in variable_names or 'BRTHDT' in variable_names) and \
           ('RAW_RFSTDTC' in variable_names or 'RFSTDTC' in variable_names):
            analysis['needs_age_derivation'] = True
        
        # Check for CT mappings needed
        ct_mappings = {
            'RAW_SEX': ('C66731', 'SEX'),
            'RAW_RACE': ('C74457', 'RACE'),
            'RAW_ETHNIC': ('C66790', 'ETHNIC'),
            'RAW_COUNTRY': ('C71113', 'COUNTRY')
        }
        
        for raw_var, (codelist, ct_var) in ct_mappings.items():
            if raw_var in variable_names:
                analysis['needs_ct_mapping'][raw_var] = {
                    'codelist': codelist,
                    'output_var': ct_var
                }
        
        return analysis
    
    def select_macros(self, analysis: Dict) -> List[Dict]:
        """Select macros based on analysis"""
        selected = []
        
        if analysis['needs_date_conversion']:
            selected.append(self.macros_by_name['%iso_date'])
            print(f"\n[SELECTION] Selected %iso_date for date conversion")
        
        if analysis['needs_age_derivation']:
            selected.append(self.macros_by_name['%derive_age'])
            print(f"[SELECTION] Selected %derive_age for age derivation")
        
        if analysis['needs_ct_mapping']:
            selected.append(self.macros_by_name['%assign_ct'])
            print(f"[SELECTION] Selected %assign_ct for CT mapping")
        
        return selected
    
    def topological_sort(self, macros: List[Dict]) -> List[Dict]:
        """Sort macros by dependencies (topological sort)"""
        macro_names = {m['name'] for m in macros}
        macro_dict = {m['name']: m for m in macros}
        
        sorted_macros = []
        visited = set()
        visiting = set()
        
        def visit(name):
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Circular dependency detected: {name}")
            
            visiting.add(name)
            macro = macro_dict[name]
            
            for dep in macro.get('dependencies', []):
                if dep in macro_names:
                    visit(dep)
            
            visiting.remove(name)
            visited.add(name)
            sorted_macros.append(macro)
        
        for macro in macros:
            visit(macro['name'])
        
        print(f"\n[SEQUENCING] Macros sorted by dependencies:")
        for i, macro in enumerate(sorted_macros, 1):
            deps = macro.get('dependencies', [])
            deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
            print(f"  {i}. {macro['name']}{deps_str}")
        
        return sorted_macros
    
    def generate_sas_code(self, analysis: Dict, selected_macros: List[Dict]) -> str:
        """Generate SAS code from selected macros"""
        code_lines = [
            "/* AUTO-GENERATED SAS CODE FROM AI ORCHESTRATOR */",
            "/* Generated from macro_registry.json */",
            "",
            "/* ========================================== */",
            "/* MACRO CALLS GENERATED BY ORCHESTRATOR     */",
            "/* ========================================== */",
            ""
        ]
        
        dataset_name = "raw.dm"  # Input dataset
        current_dataset = dataset_name
        output_dataset = dataset_name
        step_num = 1
        
        # Generate date conversion macros
        if analysis['needs_date_conversion']:
            for date_var in analysis['needs_date_conversion']:
                output_var = date_var.replace('RAW_', '')
                output_dataset = f"work.dm_step{step_num}"
                
                code_lines.append(f"/* Step {step_num}: Convert {date_var} to ISO 8601 */")
                code_lines.append(
                    f"%iso_date(inds={current_dataset}, outds={output_dataset}, "
                    f"invar={date_var}, outvar={output_var});"
                )
                code_lines.append("")
                
                current_dataset = output_dataset
                step_num += 1
        
        # Generate age derivation macro
        if analysis['needs_age_derivation']:
            output_dataset = f"work.dm_step{step_num}"
            
            code_lines.append(f"/* Step {step_num}: Derive AGE from BRTHDTC and RFSTDTC */")
            code_lines.append(
                f"%derive_age(inds={current_dataset}, outds={output_dataset}, "
                f"brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);"
            )
            code_lines.append("")
            
            current_dataset = output_dataset
            step_num += 1
        
        # Generate CT mapping macros
        if analysis['needs_ct_mapping']:
            for raw_var, mapping in analysis['needs_ct_mapping'].items():
                output_dataset = f"work.dm_step{step_num}"
                
                code_lines.append(
                    f"/* Step {step_num}: Map {raw_var} to CDISC CT "
                    f"({mapping['codelist']}) */"
                )
                code_lines.append(
                    f"%assign_ct(inds={current_dataset}, outds={output_dataset}, "
                    f"invar={raw_var}, outvar={mapping['output_var']}, "
                    f"codelist={mapping['codelist']});"
                )
                code_lines.append("")
                
                current_dataset = output_dataset
                step_num += 1
        
        # Final output
        code_lines.append(f"/* Final output: {current_dataset} */")
        code_lines.append(f"proc contents data={current_dataset}; run;")
        
        return "\n".join(code_lines)
    
    def orchestrate(self, variable_names: List[str], registry_path: str) -> str:
        """Main orchestration process"""
        print("=" * 70)
        print("SAS MACRO ORCHESTRATOR: AUTOMATED TRANSFORMATION PIPELINE")
        print("=" * 70)
        
        # Step 1: Analyze
        analysis = self.analyze_input_dataset(variable_names)
        
        # Step 2: Select
        selected_macros = self.select_macros(analysis)
        
        # Step 3: Sequence
        sorted_macros = self.topological_sort(selected_macros)
        
        # Step 4: Generate Code
        sas_code = self.generate_sas_code(analysis, sorted_macros)
        
        print("\n" + "=" * 70)
        print("GENERATED SAS CODE:")
        print("=" * 70)
        print(sas_code)
        
        return sas_code


def main():
    """Demonstrate the orchestrator"""
    
    # Path to registry
    registry_path = "/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/macros/macro_registry.json"
    
    # Create orchestrator
    orchestrator = SASMacroOrchestrator(registry_path)
    
    # Example input dataset with raw variables
    input_variables = [
        'STUDYID',
        'USUBJID',
        'RAW_BRTHDT',      # Needs date conversion
        'RAW_RFSTDTC',     # Needs date conversion
        'RAW_SEX',         # Needs CT mapping
        'RAW_RACE',        # Needs CT mapping
        'RAW_ETHNIC',      # Needs CT mapping
        'COUNTRY'          # Already standardized
    ]
    
    # Run orchestration
    sas_code = orchestrator.orchestrate(input_variables, registry_path)
    
    print("\n" + "=" * 70)
    print("ORCHESTRATION COMPLETE")
    print("=" * 70)
    print("\nThis SAS code would be executed against your input dataset to produce")
    print("an SDTM-compliant output with:")
    print("  - BRTHDTC: Converted birth date (ISO 8601)")
    print("  - RFSTDTC: Converted reference date (ISO 8601)")
    print("  - AGE: Derived age in years")
    print("  - SEX: CDISC CT-mapped value")
    print("  - RACE: CDISC CT-mapped value")
    print("  - ETHNIC: CDISC CT-mapped value")


if __name__ == '__main__':
    main()
