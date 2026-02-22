"""
TLF Search Tool — Database Schema Setup.

Creates the PostgreSQL table for storing TLF metadata with vector embeddings.
Follows the same pattern as sdtm_ig_db/setup_db.py.

Usage:
    python setup_db.py
"""

import sys

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

from config import Config


def create_database():
    """Create the tlf_search database if it doesn't exist."""
    conn = psycopg2.connect(
        host=Config.db.HOST,
        port=Config.db.PORT,
        user=Config.db.USER,
        password=Config.db.PASSWORD,
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (Config.db.DATABASE,)
    )
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(Config.db.DATABASE)
        ))
        print(f"Created database: {Config.db.DATABASE}")
    else:
        print(f"Database already exists: {Config.db.DATABASE}")

    cur.close()
    conn.close()


def create_schema():
    """Create the tlf_outputs table with pgvector support."""
    conn = psycopg2.connect(Config.db.get_connection_string())
    conn.autocommit = True
    cur = conn.cursor()

    # Enable extensions
    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    cur.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    print("Extensions enabled: uuid-ossp, vector")

    # Create the TLF outputs table
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS tlf_outputs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            study_id VARCHAR(50) NOT NULL,
            output_type VARCHAR(10) NOT NULL,
            output_number VARCHAR(20) NOT NULL,
            title TEXT NOT NULL,
            footnotes TEXT,
            program_name VARCHAR(100),
            program_path VARCHAR(500),
            domain_source VARCHAR(10),
            status VARCHAR(20) DEFAULT 'draft',
            created_date DATE,
            embedding vector({Config.embeddings.DIMENSIONS}),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Table created: tlf_outputs")

    # Create indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tlf_study_id
        ON tlf_outputs(study_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tlf_output_type
        ON tlf_outputs(output_type)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tlf_domain_source
        ON tlf_outputs(domain_source)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tlf_status
        ON tlf_outputs(status)
    """)
    print("Indexes created: study_id, output_type, domain_source, status")

    # Create vector similarity index (IVFFlat)
    # Note: IVFFlat requires at least some data to build properly.
    # For small datasets, exact search (no index) is fine.
    # For production with thousands of TLFs, uncomment:
    # cur.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_tlf_embedding
    #     ON tlf_outputs USING ivfflat (embedding vector_cosine_ops)
    #     WITH (lists = 50)
    # """)

    cur.close()
    conn.close()
    print("\nSchema setup complete. Ready to load TLF data.")


if __name__ == "__main__":
    print("TLF Search Tool — Schema Setup")
    print("=" * 40)
    try:
        create_database()
        create_schema()
    except psycopg2.OperationalError as e:
        print(f"\nCould not connect to PostgreSQL: {e}")
        print("\nTo run without PostgreSQL, review the SQL above to understand the schema.")
        print("The schema creates a tlf_outputs table with:")
        print("  - UUID primary key")
        print("  - Study ID, output type, number, title, footnotes")
        print("  - Program name and path")
        print("  - Domain source (DM, AE, VS, LB, etc.)")
        print("  - Status (draft, validated, final)")
        print(f"  - Vector embedding ({Config.embeddings.DIMENSIONS} dimensions)")
