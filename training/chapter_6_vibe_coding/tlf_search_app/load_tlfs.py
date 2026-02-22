"""
TLF Search Tool — Load TLF Metadata into PostgreSQL.

Reads TLF catalog from CSV, generates vector embeddings for each TLF's
title + footnotes, and inserts into the tlf_outputs table.

Uses mock embeddings by default (deterministic, no API key needed).
Set EMBEDDING_PROVIDER=openai for real embeddings.

Usage:
    python load_tlfs.py
    python load_tlfs.py --csv path/to/tlf_catalog.csv

TODO: Implement during live demo using vibe coding.
      Follow the pattern in sdtm_ig_db/load_sdtm_ig.py (EmbeddingGenerator class).

Implementation steps:
    1. Read sample_data/tlf_catalog.csv with pandas
    2. For each row, combine title + footnotes into embedding text
    3. Generate embedding using mock mode (MD5 hash -> deterministic vector)
    4. Insert into tlf_outputs table via psycopg2
    5. Report: number of TLFs loaded, any errors

Reference files:
    - sdtm_ig_db/load_sdtm_ig.py  (EmbeddingGenerator for mock/openai embeddings)
    - sdtm_ig_db/config.py         (config pattern)
    - config.py                     (this app's config)
    - setup_db.py                   (table schema)
"""

# TODO: implement during live demo
# The instructor will use vibe coding (plan mode + iterative prompting)
# to fill in this file during Module 6.5.


def load_tlf_catalog(csv_path: str = "sample_data/tlf_catalog.csv") -> int:
    """Load TLF metadata from CSV into PostgreSQL.

    Args:
        csv_path: Path to the TLF catalog CSV file.

    Returns:
        Number of TLFs successfully loaded.
    """
    # TODO: implement
    pass


def generate_mock_embedding(text: str, dimensions: int = 1536) -> list:
    """Generate a deterministic mock embedding from text.

    Uses MD5 hash as seed for reproducible vectors.
    Same pattern as sdtm_ig_db/load_sdtm_ig.py EmbeddingGenerator.

    Args:
        text: The text to embed (title + footnotes).
        dimensions: Vector dimensions (default 1536).

    Returns:
        List of floats representing the embedding vector.
    """
    # TODO: implement
    pass


if __name__ == "__main__":
    print("TLF Search Tool — Load TLF Metadata")
    print("=" * 40)
    print()
    print("This file is a stub. Implement during the live demo using vibe coding.")
    print()
    print("Prompt suggestion for plan mode:")
    print('  "I want to implement load_tlfs.py. It should read tlf_catalog.csv,')
    print('   generate mock embeddings for each TLF title + footnotes, and insert')
    print('   into the tlf_outputs PostgreSQL table. Follow the pattern in')
    print('   sdtm_ig_db/load_sdtm_ig.py for the EmbeddingGenerator."')
