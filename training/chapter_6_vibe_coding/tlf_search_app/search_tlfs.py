"""
TLF Search Tool — Semantic Search Interface.

Takes a natural language query, embeds it, and finds the most similar
TLFs by cosine similarity in the tlf_outputs table.

Usage:
    python search_tlfs.py "demographics summary by treatment"
    python search_tlfs.py "adverse event severity" --domain AE
    python search_tlfs.py "Kaplan-Meier survival" --top_k 3

TODO: Implement during live demo using vibe coding.
      Follow the pattern in sdtm_ig_db/query_ig.py (SDTMIGQuery class).

Implementation steps:
    1. Parse CLI arguments (query string, optional domain filter, top_k)
    2. Generate embedding for the query using same mock method as load_tlfs.py
    3. Query PostgreSQL: ORDER BY embedding <=> query_embedding LIMIT top_k
    4. Display results: output_number, title, program_name, similarity_score
    5. If domain filter provided, add WHERE domain_source = filter

Reference files:
    - sdtm_ig_db/query_ig.py   (SDTMIGQuery.semantic_search for query pattern)
    - load_tlfs.py              (generate_mock_embedding for consistent embeddings)
    - config.py                  (connection settings, search defaults)
"""

# TODO: implement during live demo
# The instructor will use vibe coding (plan mode + iterative prompting)
# to fill in this file during Module 6.5.


def search(query: str, domain: str = None, top_k: int = 5) -> list:
    """Search for TLFs similar to the query.

    Args:
        query: Natural language description of the desired TLF.
        domain: Optional SDTM domain filter (e.g., "AE", "DM").
        top_k: Number of results to return.

    Returns:
        List of dicts with keys: output_number, title, program_name,
        domain_source, similarity_score.
    """
    # TODO: implement
    pass


def display_results(results: list) -> None:
    """Display search results in a formatted table.

    Args:
        results: List of result dicts from search().
    """
    # TODO: implement
    pass


if __name__ == "__main__":
    print("TLF Search Tool — Semantic Search")
    print("=" * 40)
    print()
    print("This file is a stub. Implement during the live demo using vibe coding.")
    print()
    print("Prompt suggestion for plan mode:")
    print('  "Implement search_tlfs.py. It should take a natural language query,')
    print('   embed it using the same mock method from load_tlfs.py, query the')
    print('   tlf_outputs table for the top 5 most similar TLFs by cosine')
    print('   similarity, and display: output number, title, program name,')
    print('   and similarity score. Follow the pattern in sdtm_ig_db/query_ig.py."')
