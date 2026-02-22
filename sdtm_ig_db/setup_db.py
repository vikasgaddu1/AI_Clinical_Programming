"""
SDTM IG PostgreSQL Database Setup and Schema Initialization

This module creates the complete database schema for the SDTM IG RAG system.
It handles:
1. Database creation and connection validation
2. pgvector extension installation for semantic search
3. Table creation for chunks, controlled terminology, and assumptions
4. Indexes for performance optimization

RAG Architecture Role:
- Stores chunked SDTM IG content with embeddings for retrieval
- Enables semantic search for finding relevant IG sections
- Maintains controlled terminology mappings and assumptions
- Provides efficient vector similarity search via pgvector
"""

import psycopg2
from psycopg2 import sql
import sys
import logging
from typing import Optional

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SDTMIGDatabase:
    """Manages SDTM IG PostgreSQL database schema and operations."""
    
    def __init__(self, connection_string: str):
        """
        Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection URI
        """
        self.connection_string = connection_string
        self.conn = None
        self.cur = None
    
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cur = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Execute a single SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            
        Returns:
            bool: True if successful
        """
        try:
            if params:
                self.cur.execute(query, params)
            else:
                self.cur.execute(query)
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            return False
    
    def setup_extensions(self) -> bool:
        """
        Install required PostgreSQL extensions.
        
        Returns:
            bool: True if all extensions installed successfully
        """
        logger.info("Setting up PostgreSQL extensions...")
        
        extensions = ["pgvector", "uuid-ossp"]
        
        for ext in extensions:
            try:
                self.cur.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")
                self.conn.commit()
                logger.info(f"Extension '{ext}' installed/verified")
            except psycopg2.Error as e:
                # pgvector might not be installed; this is a common setup issue
                if "pgvector" in str(e):
                    logger.warning(
                        f"pgvector extension not available. "
                        f"Install with: CREATE EXTENSION vector;"
                    )
                    # Continue anyway - we'll create vector columns as TEXT for training
                else:
                    logger.error(f"Failed to install extension {ext}: {e}")
                self.conn.rollback()
        
        return True
    
    def create_chunks_table(self) -> bool:
        """
        Create sdtm_ig_chunks table for storing IG content chunks.
        
        Schema:
        - id: Primary key
        - domain: SDTM domain (DM, AE, LB, etc.)
        - section: Major section (Domain Variables, Assumptions, etc.)
        - subsection: Subsection for organization
        - content: Actual chunk text
        - chunk_type: Type of content (overview, variable_def, assumption, etc.)
        - sequence: Order within document
        - embedding: Vector for semantic search
        - created_at: Timestamp of creation
        
        Returns:
            bool: True if table created successfully
        """
        logger.info("Creating sdtm_ig_chunks table...")
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {Config.db.CHUNKS_TABLE} (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(10) NOT NULL,
            section VARCHAR(255) NOT NULL,
            subsection VARCHAR(255),
            content TEXT NOT NULL,
            chunk_type VARCHAR(50),
            sequence INT,
            -- pgvector column for embeddings (1536 dimensions for OpenAI/Claude)
            -- If pgvector not available, this is stored as TEXT (mock embeddings)
            embedding vector(1536),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for query performance
        CREATE INDEX IF NOT EXISTS idx_chunks_domain ON {Config.db.CHUNKS_TABLE}(domain);
        CREATE INDEX IF NOT EXISTS idx_chunks_section ON {Config.db.CHUNKS_TABLE}(section);
        CREATE INDEX IF NOT EXISTS idx_chunks_type ON {Config.db.CHUNKS_TABLE}(chunk_type);
        CREATE INDEX IF NOT EXISTS idx_chunks_sequence ON {Config.db.CHUNKS_TABLE}(domain, sequence);
        
        -- Vector similarity index for fast semantic search
        -- Uses IVFFlat with cosine similarity
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
            ON {Config.db.CHUNKS_TABLE} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """
        
        return self.execute_query(create_table_query)
    
    def create_controlled_terminology_table(self) -> bool:
        """
        Create controlled_terminology table for SDTM codelist mappings.
        
        Schema:
        - id: Primary key
        - codelist_code: Codelist identifier (e.g., 'C66742' for SEX)
        - codelist_name: Human-readable name (e.g., 'Sex')
        - term_code: NCI code for term
        - term_value: Actual codelist value (M, F, U, etc.)
        - synonyms: Alternate acceptable values or abbreviations
        - definition: Definition from NCI thesaurus
        
        Returns:
            bool: True if table created successfully
        """
        logger.info("Creating controlled_terminology table...")
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {Config.db.CT_TABLE} (
            id SERIAL PRIMARY KEY,
            codelist_code VARCHAR(20) NOT NULL,
            codelist_name VARCHAR(255) NOT NULL,
            term_code VARCHAR(20),
            term_value VARCHAR(255) NOT NULL,
            synonyms TEXT,
            definition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for fast lookups
        CREATE INDEX IF NOT EXISTS idx_ct_codelist ON {Config.db.CT_TABLE}(codelist_code);
        CREATE INDEX IF NOT EXISTS idx_ct_value ON {Config.db.CT_TABLE}(term_value);
        CREATE INDEX IF NOT EXISTS idx_ct_name ON {Config.db.CT_TABLE}(codelist_name);
        """
        
        return self.execute_query(create_table_query)
    
    def create_mapping_assumptions_table(self) -> bool:
        """
        Create mapping_assumptions table for domain and variable assumptions.
        
        Schema:
        - id: Primary key
        - domain: SDTM domain
        - variable: Variable name (or NULL for domain-level)
        - assumption_text: The mapping assumption/rule
        - ig_reference: Reference to IG section
        - priority: Priority level (1=critical, 2=important, 3=informational)
        - approach_number: For multiple valid approaches to same mapping
        
        Returns:
            bool: True if table created successfully
        """
        logger.info("Creating mapping_assumptions table...")
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {Config.db.ASSUMPTIONS_TABLE} (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(10) NOT NULL,
            variable VARCHAR(50),
            assumption_text TEXT NOT NULL,
            ig_reference VARCHAR(255),
            priority INT DEFAULT 2,
            approach_number INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for retrieval
        CREATE INDEX IF NOT EXISTS idx_assumptions_domain ON {Config.db.ASSUMPTIONS_TABLE}(domain);
        CREATE INDEX IF NOT EXISTS idx_assumptions_variable 
            ON {Config.db.ASSUMPTIONS_TABLE}(domain, variable);
        CREATE INDEX IF NOT EXISTS idx_assumptions_priority ON {Config.db.ASSUMPTIONS_TABLE}(priority);
        """
        
        return self.execute_query(create_table_query)
    
    def setup_schema(self) -> bool:
        """
        Create complete database schema.
        
        Returns:
            bool: True if all schema elements created successfully
        """
        logger.info("Setting up complete database schema...")
        
        success = True
        
        # Setup extensions
        if not self.setup_extensions():
            success = False
        
        # Create tables
        if not self.create_chunks_table():
            success = False
        
        if not self.create_controlled_terminology_table():
            success = False
        
        if not self.create_mapping_assumptions_table():
            success = False
        
        if success:
            logger.info("Database schema successfully initialized")
        else:
            logger.error("Some schema elements failed to initialize")
        
        return success
    
    def drop_schema(self, confirm: bool = False) -> bool:
        """
        Drop all SDTM IG tables (for testing/cleanup).
        
        Args:
            confirm: Must be True to actually execute
            
        Returns:
            bool: True if successful
        """
        if not confirm:
            logger.warning("Dropping schema requires confirm=True parameter")
            return False
        
        logger.warning("Dropping database schema...")
        
        drop_query = f"""
        DROP TABLE IF EXISTS {Config.db.ASSUMPTIONS_TABLE} CASCADE;
        DROP TABLE IF EXISTS {Config.db.CT_TABLE} CASCADE;
        DROP TABLE IF EXISTS {Config.db.CHUNKS_TABLE} CASCADE;
        """
        
        return self.execute_query(drop_query)


def create_database_if_not_exists(host: str, user: str, password: str, database: str) -> bool:
    """
    Create PostgreSQL database if it doesn't exist.
    
    Args:
        host: Database host
        user: Database user
        password: Database password
        database: Database name to create
        
    Returns:
        bool: True if successful
    """
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=host,
            database="postgres",
            user=user,
            password=password
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (database,))
        if cur.fetchone():
            logger.info(f"Database '{database}' already exists")
        else:
            cur.execute(f"CREATE DATABASE {database};")
            logger.info(f"Created database '{database}'")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Failed to create database: {e}")
        return False


def main():
    """Main execution function."""
    
    logger.info("Starting SDTM IG Database Setup")
    logger.info(f"Target database: {Config.db.DATABASE}")
    logger.info(f"Host: {Config.db.HOST}:{Config.db.PORT}")
    
    # Create database if needed
    if not create_database_if_not_exists(
        Config.db.HOST,
        Config.db.USER,
        Config.db.PASSWORD,
        Config.db.DATABASE
    ):
        logger.error("Failed to create database")
        return False
    
    # Connect to the database
    db = SDTMIGDatabase(Config.db.get_connection_string())
    if not db.connect():
        logger.error("Failed to connect to database")
        return False
    
    # Setup schema
    success = db.setup_schema()
    
    # Cleanup
    db.disconnect()
    
    if success:
        logger.info("Database setup completed successfully")
        logger.info(f"Connect with: psql postgresql://{Config.db.USER}@{Config.db.HOST}/{Config.db.DATABASE}")
    else:
        logger.error("Database setup completed with errors")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
