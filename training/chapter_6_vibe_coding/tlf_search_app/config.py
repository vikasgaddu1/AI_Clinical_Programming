"""
TLF Search Tool — Database Configuration.

Follows the same pattern as sdtm_ig_db/config.py.
All settings overridable via environment variables.
"""

import os


class Config:
    """Configuration for the TLF Search Tool."""

    class db:
        HOST = os.getenv("PGHOST", "localhost")
        PORT = int(os.getenv("PGPORT", "5432"))
        DATABASE = os.getenv("PGDATABASE", "tlf_search")
        USER = os.getenv("PGUSER", "sdtm_user")
        PASSWORD = os.getenv("PGPASSWORD", "")

        @classmethod
        def get_connection_string(cls) -> str:
            return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"

    class embeddings:
        MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        PROVIDER = os.getenv("EMBEDDING_PROVIDER", "mock")  # mock, openai

    class search:
        TOP_K = int(os.getenv("TLF_SEARCH_TOP_K", "5"))
        SIMILARITY_THRESHOLD = float(os.getenv("TLF_SIMILARITY_THRESHOLD", "0.3"))
