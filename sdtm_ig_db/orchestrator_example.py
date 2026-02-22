"""
SDTM AI Orchestrator Example - Demonstrates RAG-Based Mapping Decisions

This module shows how an AI system would use the SDTM IG RAG database
to make clinical data mapping decisions with full IG guidance context.

This is a training/demonstration module showing:
1. How to retrieve context from the IG database
2. How to format context for an AI model
3. How to make decisions with full citations
4. How to validate decisions against rules

In production, this would integrate with Claude/GPT-4 API.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from query_ig import SDTMIGQuery
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MappingDecision:
    """Result of a mapping decision."""
    domain: str
    variable: str
    source_value: str
    mapped_value: str
    reasoning: str
    ig_references: List[str]
    confidence: str  # "high", "medium", "low"
    validation_rules: List[str]
    alternatives: Optional[List[Dict]] = None


class SDTMMappingOrchestrator:
    """
    Orchestrates SDTM mapping decisions using IG guidance.
    
    In production, this would call Claude/GPT-4 API to generate
    decisions. For demonstration, we use rule-based logic with
    full IG context shown.
    """
    
    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize orchestrator.
        
        Args:
            db_connection_string: PostgreSQL connection URI
        """
        self.db = SDTMIGQuery(
            db_connection_string or Config.db.get_connection_string()
        )
        self.decision_log = []
    
    def decide_sex_mapping(self, source_sex: str) -> MappingDecision:
        """
        Demonstrate SEX variable mapping with IG context.
        
        Args:
            source_sex: Source system value (M, F, Male, Female, Unknown, etc.)
            
        Returns:
            Mapping decision with IG citations
        """
        logger.info(f"Making SEX mapping decision for source value: {source_sex}")
        
        # Step 1: Get IG context
        context = self.db.get_context_for_mapping(
            "DM", "SEX",
            question=f"How to map source value: {source_sex}"
        )
        
        # Step 2: Get valid SEX values
        valid_values = self.db.get_codelist_values(variable="SEX")
        
        # Step 3: Apply simple mapping logic (in production, AI does this)
        normalized = source_sex.upper().strip()
        
        mapping_logic = {
            'M': ('M', 'Exact match to Male'),
            'F': ('F', 'Exact match to Female'),
            'MALE': ('M', 'Mapped from "Male" to codelist M'),
            'FEMALE': ('F', 'Mapped from "Female" to codelist F'),
            'UNKNOWN': ('U', 'Mapped from "Unknown" to U'),
            'U': ('U', 'Exact match to Unknown'),
        }
        
        if normalized in mapping_logic:
            mapped_value, reasoning = mapping_logic[normalized]
        else:
            # Default: unmapped
            mapped_value = ''
            reasoning = f'No mapping found for "{source_sex}"'
        
        # Step 4: Get documentation
        assumptions = context.get('assumptions', [])
        
        # Step 5: Assemble decision
        decision = MappingDecision(
            domain='DM',
            variable='SEX',
            source_value=source_sex,
            mapped_value=mapped_value,
            reasoning=reasoning,
            ig_references=[
                'CDISC IG: Section G.2.1 - Demographics Domain',
                'CDISC IG: DM Variables - SEX Definition',
                'CDISC Codelist C66742: Sex'
            ],
            confidence='high' if mapped_value else 'low',
            validation_rules=[
                'Must be one of: M, F, U',
                'Required for all subjects',
                'Case-sensitive (uppercase only)'
            ],
            alternatives=None
        )
        
        self.decision_log.append(decision)
        return decision
    
    def decide_race_mapping(self, source_races: List[str]) -> MappingDecision:
        """
        Demonstrate RACE mapping with multiple approaches from IG.
        
        Shows how to handle the "multiple races" scenario.
        
        Args:
            source_races: List of races (e.g., ["White", "Asian"])
            
        Returns:
            Mapping decision with available approaches
        """
        logger.info(f"Making RACE mapping decision for sources: {source_races}")
        
        # Step 1: Get IG context - this includes multiple approaches
        context = self.db.get_context_for_mapping(
            "DM", "RACE",
            question="What if subject reports multiple races?"
        )
        
        # Step 2: Get assumptions (includes all approaches)
        assumptions = context.get('assumptions', [])
        
        # Step 3: Check number of races
        if len(source_races) == 1:
            # Single race - straightforward mapping
            source_race = source_races[0].upper()
            race_mappings = {
                'WHITE': 'WHITE',
                'ASIAN': 'ASIAN',
                'BLACK': 'BLACK OR AFRICAN AMERICAN',
                'AFRICAN AMERICAN': 'BLACK OR AFRICAN AMERICAN',
                'AMERICAN INDIAN': 'AMERICAN INDIAN OR ALASKA NATIVE',
                'NATIVE AMERICAN': 'AMERICAN INDIAN OR ALASKA NATIVE',
                'HAWAIIAN': 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER',
                'OTHER': 'OTHER',
            }
            
            mapped_value = race_mappings.get(source_race, 'OTHER')
            reasoning = f'Single race reported: {source_race} → {mapped_value}'
            alternatives = None
        
        else:
            # Multiple races - show multiple approaches from IG
            mapped_value = 'MULTIPLE'
            reasoning = (
                f'Multiple races reported: {", ".join(source_races)}. '
                'Per IG Approach 2: Use RACE="MULTIPLE" and record individual '
                'races in SUPPDM with QNAM="RACE1", "RACE2", etc.'
            )
            
            # Show the alternatives from IG
            alternatives = [
                {
                    'approach': 1,
                    'description': 'Collapse to single race (Approach 1)',
                    'value': 'MULTIPLE',
                    'detail': 'Record first/primary race in DM.RACE, others in SUPPDM',
                    'priority': 'Standard approach'
                },
                {
                    'approach': 2,
                    'description': 'Use MULTIPLE flag (Approach 2 - Recommended)',
                    'value': 'MULTIPLE',
                    'detail': 'DM.RACE=MULTIPLE, then SUPPDM records each race',
                    'priority': 'Recommended by IG'
                },
                {
                    'approach': 3,
                    'description': 'Create multiple DM records',
                    'value': 'Multiple records',
                    'detail': 'Not standard SDTM - usually not recommended',
                    'priority': 'Not standard'
                }
            ]
        
        # Step 4: Get valid RACE values
        valid_races = self.db.get_codelist_values(variable="RACE")
        
        # Step 5: Assemble decision
        decision = MappingDecision(
            domain='DM',
            variable='RACE',
            source_value=str(source_races),
            mapped_value=mapped_value,
            reasoning=reasoning,
            ig_references=[
                'CDISC IG: DM Variables - RACE Definition',
                'CDISC IG: Section 2.x Multiple Race Handling',
                'CDISC Codelist C74456: Race Categories',
                'SUPPDM Qualifiers for Multiple Values'
            ],
            confidence='high',
            validation_rules=[
                'RACE must be from codelist C74456',
                'If RACE="MULTIPLE", require SUPPDM records',
                'Each individual race must be valid codelist value',
                'Maximum valid values defined by study'
            ],
            alternatives=alternatives
        )
        
        self.decision_log.append(decision)
        return decision
    
    def decide_rfstdtc_derivation(self, ic_date: str, first_dose_date: str) -> MappingDecision:
        """
        Demonstrate RFSTDTC derivation with multiple IG approaches.
        
        This is a key decision point - IG explicitly allows multiple approaches.
        
        Args:
            ic_date: Informed consent date (YYYY-MM-DD)
            first_dose_date: First dose date (YYYY-MM-DD)
            
        Returns:
            Mapping decision with all applicable approaches
        """
        logger.info(
            f"Making RFSTDTC decision: IC={ic_date}, FD={first_dose_date}"
        )
        
        # Step 1: Get IG context - includes all 3 approaches
        context = self.db.get_context_for_mapping(
            "DM", "RFSTDTC",
            question="Multiple valid approaches to RFSTDTC derivation"
        )
        
        # Step 2: Get assumptions (should list all approaches)
        assumptions = context.get('assumptions', [])
        
        # Step 3: Present all three IG-allowed approaches
        all_approaches = [
            {
                'approach': 1,
                'name': 'Informed Consent Date',
                'value': ic_date,
                'reasoning': (
                    'Uses written informed consent date as study start. '
                    'Preferred by many sponsors for subject protection. '
                    'IG Approach 1: Recommended when IC is critical enrollment event.'
                ),
                'priority': 'Preferred',
                'advantages': [
                    'Most conservative (IC before any study activity)',
                    'Protects subject rights',
                    'Standard in most trials',
                    'Clear enrollment point'
                ]
            },
            {
                'approach': 2,
                'name': 'First Dose Date',
                'value': first_dose_date,
                'reasoning': (
                    'Uses first study drug administration as reference period start. '
                    'IG Approach 2: Used in some oncology and early-phase studies. '
                    'Aligns study participation with dosing timeline.'
                ),
                'priority': 'Alternate',
                'advantages': [
                    'Aligns with dosing timeline',
                    'Simpler for dose-tracking logic',
                    'Used in phase I/II trials',
                    'Clear treatment start'
                ]
            },
            {
                'approach': 3,
                'name': 'Earlier of IC and First Dose',
                'value': min(ic_date, first_dose_date),
                'reasoning': (
                    'Uses whichever date is earlier. '
                    'IG Approach 3: Captures all study activities. '
                    'Most comprehensive definition of study participation.'
                ),
                'priority': 'Comprehensive',
                'advantages': [
                    'Captures all study activities',
                    'Comprehensive reference period',
                    'Includes pre-dose activities',
                    'Single clear earliest date'
                ]
            }
        ]
        
        # Step 4: For this example, recommend based on common practice
        # (In production, might query protocol or config)
        recommended_approach = all_approaches[0]  # IC date is most common
        
        # Step 5: Assemble decision
        decision = MappingDecision(
            domain='DM',
            variable='RFSTDTC',
            source_value=f'IC:{ic_date}, FD:{first_dose_date}',
            mapped_value=recommended_approach['value'],
            reasoning=(
                f"RFSTDTC derivation: Selected {recommended_approach['name']} "
                f"({recommended_approach['value']}). "
                f"{recommended_approach['reasoning']}"
            ),
            ig_references=[
                'CDISC IG Section 2.3.1.1: Reference Start Date (RFSTDTC)',
                'CDISC IG: DM Variables - RFSTDTC Definition',
                'Multiple Valid Approaches Document in IG'
            ],
            confidence='high',
            validation_rules=[
                'RFSTDTC must be ISO 8601 format (YYYY-MM-DD)',
                'RFSTDTC must be ≤ RFENDTC',
                'RFSTDTC must be ≤ RFICDTC (usually)',
                'Choose ONE approach and apply consistently',
                'Document approach in study documentation'
            ],
            alternatives=all_approaches  # Show all options
        )
        
        self.decision_log.append(decision)
        return decision
    
    def format_decision_report(self, decision: MappingDecision) -> str:
        """
        Format a decision as a human-readable report.
        
        This shows how the orchestrator would present decisions to data managers.
        
        Args:
            decision: Mapping decision
            
        Returns:
            Formatted report string
        """
        report = f"""
{'='*70}
SDTM MAPPING DECISION REPORT
{'='*70}

VARIABLE: {decision.domain}.{decision.variable}

SOURCE VALUE:        {decision.source_value}
MAPPED VALUE:        {decision.mapped_value}
CONFIDENCE LEVEL:    {decision.confidence.upper()}

REASONING:
{decision.reasoning}

IG REFERENCES:
{chr(10).join(f'  • {ref}' for ref in decision.ig_references)}

VALIDATION RULES:
{chr(10).join(f'  • {rule}' for rule in decision.validation_rules)}

{'='*70}
"""
        
        if decision.alternatives:
            report += "\nALTERNATIVE APPROACHES FROM IG:\n"
            report += "-" * 70 + "\n"
            
            for alt in decision.alternatives:
                if isinstance(alt, dict):
                    report += f"\nApproach {alt.get('approach', '?')}: {alt.get('name', alt.get('description', ''))}\n"
                    report += f"  Value: {alt.get('value', '')}\n"
                    report += f"  Priority: {alt.get('priority', '')}\n"
                    if alt.get('detail'):
                        report += f"  Detail: {alt.get('detail')}\n"
                    if alt.get('reasoning'):
                        report += f"  Reasoning: {alt.get('reasoning')}\n"
                    if alt.get('advantages'):
                        report += "  Advantages:\n"
                        for adv in alt['advantages']:
                            report += f"    - {adv}\n"
        
        report += f"\n{'='*70}\n"
        return report
    
    def demo_workflow(self):
        """
        Demonstrate complete mapping workflow.
        
        Shows examples of the orchestrator making decisions
        with full IG context.
        """
        logger.info("\n" + "="*70)
        logger.info("SDTM AI ORCHESTRATOR DEMO")
        logger.info("Demonstrating RAG-based mapping decisions with IG guidance")
        logger.info("="*70 + "\n")
        
        # Example 1: SEX mapping
        print("\n" + "="*70)
        print("EXAMPLE 1: Simple Variable Mapping")
        print("="*70)
        print("Scenario: Map source SEX value to SDTM")
        
        decision = self.decide_sex_mapping("Male")
        print(self.format_decision_report(decision))
        
        # Example 2: RACE with multiple values
        print("\n" + "="*70)
        print("EXAMPLE 2: Complex Variable Mapping")
        print("="*70)
        print("Scenario: Subject reports multiple races - which IG approach to use?")
        
        decision = self.decide_race_mapping(["White", "Asian"])
        print(self.format_decision_report(decision))
        
        # Example 3: RFSTDTC - multiple valid approaches
        print("\n" + "="*70)
        print("EXAMPLE 3: Derivation with Multiple Valid Approaches")
        print("="*70)
        print("Scenario: RFSTDTC can be derived multiple ways per IG")
        
        decision = self.decide_rfstdtc_derivation(
            ic_date="2024-01-15",
            first_dose_date="2024-01-16"
        )
        print(self.format_decision_report(decision))
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info(f"DEMO COMPLETE: Made {len(self.decision_log)} mapping decisions")
        logger.info("All decisions include:")
        logger.info("  ✓ Full IG guidance context")
        logger.info("  ✓ Specific IG citations")
        logger.info("  ✓ Multiple approaches when applicable")
        logger.info("  ✓ Validation rules")
        logger.info("  ✓ Confidence levels")
        logger.info("="*70 + "\n")


def main():
    """Run demonstration."""
    
    # Create orchestrator
    orchestrator = SDTMMappingOrchestrator()
    
    try:
        # Run demo workflow
        orchestrator.demo_workflow()
    
    finally:
        # Cleanup
        orchestrator.db.disconnect()


if __name__ == "__main__":
    main()
