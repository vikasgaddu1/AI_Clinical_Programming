"""
SDTM IG Query Interface - Semantic Search and Lookup Functions

This module provides the query interface that the AI orchestrator uses to retrieve
relevant SDTM IG guidance for mapping decisions.

RAG Architecture Role:
- Semantic search: Given a mapping question, find relevant IG sections
- CT lookup: Find applicable codelists and allowed values
- Assumption lookup: Find variable-specific or domain-level rules
- Context retrieval: Format results for AI model consumption

The AI orchestrator would use these functions to:
1. Answer "How should I map SEX?" → retrieve DM/SEX documentation
2. Find valid values → "What are valid values for RACE?" → retrieve codelist
3. Handle edge cases → "What if multiple races reported?" → retrieve assumptions
4. Apply rules → Format context for model reasoning
"""

import psycopg2
from psycopg2 import sql
import logging
import json
from typing import List, Dict, Optional, Tuple
from math import sqrt

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SDTMIGQuery:
    """Query interface for SDTM IG database."""
    
    def __init__(self, connection_string: str):
        """
        Initialize query interface.
        
        Args:
            connection_string: PostgreSQL connection URI
        """
        self.connection_string = connection_string
        self.conn = None
        self.cur = None
        self._connect()
    
    def _connect(self) -> bool:
        """Connect to database."""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cur = self.conn.cursor()
            logger.info("Connected to SDTM IG database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from database")
    
    def close(self):
        """Alias for disconnect."""
        self.disconnect()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        This is used for semantic similarity when pgvector extension not available.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher = more similar)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sqrt(sum(a * a for a in vec1))
        mag2 = sqrt(sum(b * b for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    @staticmethod
    def parse_embedding(embedding_str: str) -> List[float]:
        """
        Parse embedding from database string format.
        
        Args:
            embedding_str: String representation of embedding
            
        Returns:
            List of floats
        """
        if not embedding_str:
            return []
        
        # Remove brackets and split
        cleaned = embedding_str.strip('[]')
        try:
            return [float(x.strip()) for x in cleaned.split(',')]
        except (ValueError, AttributeError):
            return []
    
    def semantic_search(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = Config.query.TOP_K_CHUNKS,
        threshold: float = Config.query.SIMILARITY_THRESHOLD
    ) -> List[Dict]:
        """
        Semantically search for relevant IG chunks.
        
        This simulates semantic search by:
        1. Finding exact keyword matches (fast)
        2. Optionally using embeddings if available
        3. Returning top-k most relevant chunks
        
        Args:
            query: Search query (e.g., "How do I map RACE?")
            domain: Optionally filter by domain (e.g., "DM")
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of relevant chunks with metadata
        """
        results = []
        
        # For training, use keyword matching instead of embedding search
        # In production, would:
        # 1. Generate embedding for query
        # 2. Use pgvector for similarity search: ORDER BY embedding <-> query_embedding
        
        logger.info(f"Searching for: {query}")
        
        # Build query
        search_terms = query.lower().split()
        
        # Create WHERE clause for keyword matching
        where_clauses = [f"LOWER(content) LIKE %s" for _ in search_terms]
        where_sql = " OR ".join(where_clauses)
        
        if domain:
            where_sql = f"domain = %s AND ({where_sql})"
        
        select_query = f"""
        SELECT 
            id, domain, section, subsection, content, chunk_type,
            similarity(content, %s) as relevance
        FROM {Config.db.CHUNKS_TABLE}
        WHERE {where_sql}
        ORDER BY relevance DESC
        LIMIT %s
        """
        
        try:
            # Prepare parameters
            params = []
            if domain:
                params.append(domain)
            params.append(query)
            params.extend([f"%{term}%" for term in search_terms])
            params.append(top_k)
            
            # Simple keyword search (since similarity() might not be available)
            simple_query = f"""
            SELECT 
                id, domain, section, subsection, content, chunk_type
            FROM {Config.db.CHUNKS_TABLE}
            WHERE {('domain = %s AND ' if domain else '')}
            LOWER(content) LIKE %s
            LIMIT %s
            """
            
            simple_params = []
            if domain:
                simple_params.append(domain)
            simple_params.append(f"%{query.lower()}%")
            simple_params.append(top_k)
            
            self.cur.execute(simple_query, simple_params)
            rows = self.cur.fetchall()
            
            for row in rows:
                results.append({
                    'id': row[0],
                    'domain': row[1],
                    'section': row[2],
                    'subsection': row[3],
                    'content': row[4],
                    'chunk_type': row[5],
                    'relevance': 0.8  # Mock relevance
                })
        
        except psycopg2.Error as e:
            logger.error(f"Search failed: {e}")
        
        return results[:top_k]
    
    def get_variable_documentation(
        self,
        domain: str,
        variable: str
    ) -> Optional[Dict]:
        """
        Get complete documentation for a specific variable.
        
        This retrieves all IG content related to a single variable,
        including definition, assumptions, controlled terminology.
        
        Args:
            domain: Domain code (e.g., "DM")
            variable: Variable name (e.g., "RACE")
            
        Returns:
            Dictionary with documentation and related info, or None
        """
        logger.info(f"Retrieving documentation for {domain}.{variable}")
        
        try:
            # Get chunks specific to this variable
            query = f"""
            SELECT id, content, section, subsection, chunk_type
            FROM {Config.db.CHUNKS_TABLE}
            WHERE domain = %s
            AND (
                LOWER(content) LIKE %s
                OR section ILIKE %s
            )
            ORDER BY sequence
            """
            
            self.cur.execute(query, (domain, f"%{variable}%", f"%{variable}%"))
            chunks = self.cur.fetchall()
            
            # Get assumptions for this variable
            self.cur.execute(
                f"""
                SELECT assumption_text, ig_reference, priority, approach_number
                FROM {Config.db.ASSUMPTIONS_TABLE}
                WHERE domain = %s AND variable = %s
                ORDER BY priority ASC
                """,
                (domain, variable)
            )
            assumptions = self.cur.fetchall()
            
            # Get controlled terminology if applicable
            ct_data = self.get_codelist_values(domain, variable)
            
            return {
                'domain': domain,
                'variable': variable,
                'documentation': [
                    {
                        'id': c[0],
                        'content': c[1],
                        'section': c[2],
                        'subsection': c[3],
                        'type': c[4]
                    }
                    for c in chunks
                ],
                'assumptions': [
                    {
                        'text': a[0],
                        'reference': a[1],
                        'priority': a[2],
                        'approach': a[3]
                    }
                    for a in assumptions
                ],
                'controlled_terminology': ct_data
            }
        
        except psycopg2.Error as e:
            logger.error(f"Failed to retrieve variable documentation: {e}")
            return None
    
    def get_codelist_values(
        self,
        domain: Optional[str] = None,
        variable: Optional[str] = None,
        codelist_name: Optional[str] = None,
        codelist_code: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve controlled terminology (codelist) values.
        
        This allows looking up valid values for any coded variable.
        Can be called with domain+variable (infer codelist) or explicit codelist name.
        
        Args:
            domain: Domain code (optional, for context)
            variable: Variable name (optional)
            codelist_name: Codelist name (e.g., "Sex", "Race")
            codelist_code: NCI codelist code (e.g., "C66742")
            
        Returns:
            List of codelist entries with definitions
        """
        # Map common variables to codelists
        var_to_codelist = {
            'SEX': 'Sex',
            'RACE': 'Race',
            'ETHNIC': 'Ethnicity',
            'DTHFL': 'Death Flag',
        }
        
        if not codelist_name and variable:
            codelist_name = var_to_codelist.get(variable.upper())
        
        if not codelist_name and not codelist_code:
            logger.warning("No codelist identifier provided")
            return []
        
        try:
            where_clauses = []
            params = []
            
            if codelist_name:
                where_clauses.append("codelist_name = %s")
                params.append(codelist_name)
            
            if codelist_code:
                where_clauses.append("codelist_code = %s")
                params.append(codelist_code)
            
            where_sql = " OR ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
            SELECT codelist_code, codelist_name, term_value, term_code,
                   synonyms, definition
            FROM {Config.db.CT_TABLE}
            WHERE {where_sql}
            ORDER BY codelist_name, term_value
            """
            
            self.cur.execute(query, params)
            rows = self.cur.fetchall()
            
            return [
                {
                    'codelist_code': r[0],
                    'codelist_name': r[1],
                    'term_value': r[2],
                    'term_code': r[3],
                    'synonyms': r[4],
                    'definition': r[5]
                }
                for r in rows
            ]
        
        except psycopg2.Error as e:
            logger.error(f"Codelist lookup failed: {e}")
            return []
    
    def get_domain_overview(self, domain: str) -> Optional[Dict]:
        """
        Get domain overview documentation.
        
        Args:
            domain: Domain code (e.g., "DM")
            
        Returns:
            Dictionary with overview and variable list
        """
        logger.info(f"Retrieving overview for domain {domain}")
        
        try:
            # Get overview content
            query = f"""
            SELECT id, content, section, subsection
            FROM {Config.db.CHUNKS_TABLE}
            WHERE domain = %s
            AND chunk_type IN ('overview', 'section_content')
            ORDER BY sequence
            LIMIT 1
            """
            
            self.cur.execute(query, (domain,))
            overview = self.cur.fetchone()
            
            # Get all variables in domain
            self.cur.execute(
                f"""
                SELECT DISTINCT section
                FROM {Config.db.CHUNKS_TABLE}
                WHERE domain = %s
                AND section LIKE '% - %'
                ORDER BY sequence
                """,
                (domain,)
            )
            variables = [row[0] for row in self.cur.fetchall()]
            
            return {
                'domain': domain,
                'overview': overview[1] if overview else None,
                'variables': variables
            }
        
        except psycopg2.Error as e:
            logger.error(f"Failed to retrieve domain overview: {e}")
            return None
    
    def get_mapping_assumptions(
        self,
        domain: Optional[str] = None,
        variable: Optional[str] = None,
        priority: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve mapping assumptions.
        
        Assumptions are the operational rules that guide mapping decisions.
        Can be domain-level or variable-specific.
        
        Args:
            domain: Filter by domain
            variable: Filter by variable
            priority: Filter by priority (1=critical, 2=important, 3=info)
            
        Returns:
            List of assumption records
        """
        where_clauses = []
        params = []
        
        if domain:
            where_clauses.append("domain = %s")
            params.append(domain)
        
        if variable:
            where_clauses.append("variable = %s")
            params.append(variable)
        
        if priority:
            where_clauses.append("priority <= %s")
            params.append(priority)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        try:
            query = f"""
            SELECT domain, variable, assumption_text, ig_reference,
                   priority, approach_number, id
            FROM {Config.db.ASSUMPTIONS_TABLE}
            WHERE {where_sql}
            ORDER BY priority ASC, approach_number ASC
            """
            
            self.cur.execute(query, params)
            rows = self.cur.fetchall()
            
            return [
                {
                    'id': r[6],
                    'domain': r[0],
                    'variable': r[1],
                    'assumption': r[2],
                    'reference': r[3],
                    'priority': r[4],
                    'approach': r[5]
                }
                for r in rows
            ]
        
        except psycopg2.Error as e:
            logger.error(f"Failed to retrieve assumptions: {e}")
            return []
    
    def get_context_for_mapping(
        self,
        domain: str,
        variable: str,
        question: Optional[str] = None
    ) -> Dict:
        """
        Retrieve complete context for an AI model to make mapping decision.
        
        This is the primary interface for the AI orchestrator.
        Returns all relevant IG guidance formatted for model consumption.
        
        Args:
            domain: Target domain
            variable: Target variable
            question: Optional specific question about mapping
            
        Returns:
            Complete context dictionary
        """
        logger.info(f"Building mapping context for {domain}.{variable}")
        
        context = {
            'domain': domain,
            'variable': variable,
            'documentation': self.get_variable_documentation(domain, variable),
            'controlled_terminology': self.get_codelist_values(domain, variable),
            'assumptions': self.get_mapping_assumptions(domain, variable, priority=2),
            'related_questions': []
        }
        
        # If specific question provided, search for related guidance
        if question:
            context['related_questions'] = self.semantic_search(question, domain=domain, top_k=3)
        
        return context


# Example usage and test queries
def example_queries():
    """Run example queries to demonstrate the system."""
    
    logger.info("\n" + "="*60)
    logger.info("SDTM IG Query System - Example Queries")
    logger.info("="*60 + "\n")
    
    # Initialize query interface
    query = SDTMIGQuery(Config.db.get_connection_string())
    
    try:
        # Example 1: Semantic search
        print("\n1. SEMANTIC SEARCH - 'How should I map RACE?'")
        print("-" * 60)
        results = query.semantic_search("How should I map RACE?", domain="DM", top_k=3)
        for result in results:
            print(f"\nFound in section: {result['section']}")
            print(f"Type: {result['chunk_type']}")
            print(f"Content preview: {result['content'][:200]}...")
        
        # Example 2: Variable documentation
        print("\n\n2. VARIABLE DOCUMENTATION - DM.RACE")
        print("-" * 60)
        doc = query.get_variable_documentation("DM", "RACE")
        if doc:
            print(f"Assumptions for RACE:")
            for assumption in doc['assumptions']:
                print(f"\n  Priority {assumption['priority']}: {assumption['text'][:100]}...")
            
            if doc['controlled_terminology']:
                print(f"\nControlled Terminology ({len(doc['controlled_terminology'])} values):")
                for ct in doc['controlled_terminology'][:5]:
                    print(f"  - {ct['term_value']}: {ct['definition']}")
        
        # Example 3: Codelist lookup
        print("\n\n3. CODELIST LOOKUP - SEX Values")
        print("-" * 60)
        sex_values = query.get_codelist_values(variable="SEX")
        for value in sex_values:
            print(f"\n{value['term_value']} (NCI: {value['term_code']})")
            print(f"  Definition: {value['definition']}")
            print(f"  Synonyms: {value['synonyms']}")
        
        # Example 4: Mapping assumptions
        print("\n\n4. MAPPING ASSUMPTIONS - DM Domain")
        print("-" * 60)
        assumptions = query.get_mapping_assumptions(domain="DM")
        print(f"Found {len(assumptions)} mapping assumptions:\n")
        for assumption in assumptions[:5]:
            var_str = f"{assumption['variable']}" if assumption['variable'] else "Domain-level"
            print(f"[{var_str}] Priority {assumption['priority']}: {assumption['assumption'][:80]}...")
        
        # Example 5: Complete mapping context
        print("\n\n5. COMPLETE MAPPING CONTEXT - DM.RACE")
        print("-" * 60)
        context = query.get_context_for_mapping(
            "DM",
            "RACE",
            "What if a subject reports multiple races?"
        )
        print(f"Domain: {context['domain']}")
        print(f"Variable: {context['variable']}")
        print(f"Documentation chunks: {len(context['documentation']['documentation']) if context['documentation'] else 0}")
        print(f"CT values: {len(context['controlled_terminology'])}")
        print(f"Assumptions: {len(context['assumptions'])}")
        print(f"Related guidance: {len(context['related_questions'])}")
        
        print("\n" + "="*60)
        logger.info("Example queries completed")
    
    finally:
        query.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        example_queries()
    else:
        print("SDTM IG Query Interface")
        print("Usage: python query_ig.py --examples    (run example queries)")
        print("\nFor programmatic use:")
        print("  from query_ig import SDTMIGQuery")
        print("  from config import Config")
        print("  q = SDTMIGQuery(Config.db.get_connection_string())")
        print("  results = q.semantic_search('question')")
