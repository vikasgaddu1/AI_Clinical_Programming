"""
SDTM Implementation Guide RAG System Configuration

This configuration module centralizes all settings for the SDTM IG database setup,
content loading, and query operations. It supports environment variable overrides
for flexible deployment across development, testing, and production environments.

RAG Architecture Context:
- The AI orchestrator uses this configuration to:
  1. Connect to the PostgreSQL database containing chunked IG content
  2. Generate embeddings for semantic search queries
  3. Retrieve relevant context for SDTM mapping decisions
  4. Apply controlled terminology and mapping assumptions
"""

import os
from typing import Optional


class DatabaseConfig:
    """PostgreSQL and pgvector configuration."""
    
    # Connection parameters - override via environment variables
    HOST: str = os.getenv("PGHOST", "localhost")
    PORT: int = int(os.getenv("PGPORT", "5432"))
    DATABASE: str = os.getenv("PGDATABASE", "sdtm_ig_rag")
    USER: str = os.getenv("PGUSER", "sdtm_user")
    PASSWORD: str = os.getenv("PGPASSWORD", "sdtm_password")
    
    # Connection pool settings
    MIN_POOL_SIZE: int = int(os.getenv("DB_MIN_POOL_SIZE", "2"))
    MAX_POOL_SIZE: int = int(os.getenv("DB_MAX_POOL_SIZE", "10"))
    
    # Table names
    CHUNKS_TABLE: str = "sdtm_ig_chunks"
    CT_TABLE: str = "controlled_terminology"
    ASSUMPTIONS_TABLE: str = "mapping_assumptions"
    
    @classmethod
    def get_connection_string(cls) -> str:
        """
        Generate PostgreSQL connection string.
        
        Returns:
            str: PostgreSQL connection URI
        """
        return (
            f"postgresql://{cls.USER}:{cls.PASSWORD}@"
            f"{cls.HOST}:{cls.PORT}/{cls.DATABASE}"
        )


class EmbeddingConfig:
    """Embedding model configuration for semantic search."""
    
    # Embedding model settings
    # In production, this would use OpenAI API or Claude API
    # For this training exercise, we'll use placeholder with 1536 dimensions (OpenAI standard)
    MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    
    # Provider selection: "openai" or "claude" or "mock"
    PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mock")
    
    # API keys (should be in .env or environment)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Batch processing for efficiency
    BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))


class ChunkingConfig:
    """Settings for text chunking and segmentation."""
    
    # Chunk size in tokens (approximate)
    # 500 tokens ≈ 2000 characters for English text
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    
    # Overlap between chunks for context preservation
    # Higher overlap = more semantic continuity but more processing
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # Maximum chunk size in characters (safety limit)
    MAX_CHUNK_CHARS: int = int(os.getenv("MAX_CHUNK_CHARS", "3000"))
    
    # Minimum chunk size to avoid fragments
    MIN_CHUNK_CHARS: int = int(os.getenv("MIN_CHUNK_CHARS", "100"))


class QueryConfig:
    """Settings for semantic search and retrieval."""
    
    # Number of similar chunks to retrieve for context
    # For SDTM mapping: retrieve 3-5 most relevant chunks
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "5"))
    
    # Similarity threshold (0-1 scale)
    # Higher = stricter matching, lower = more permissive
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))
    
    # Controlled terminology lookup settings
    CT_TOP_K: int = int(os.getenv("CT_TOP_K", "10"))
    
    # Assumption lookup settings (typically 1-3 relevant assumptions per variable)
    ASSUMPTION_TOP_K: int = int(os.getenv("ASSUMPTION_TOP_K", "3"))


class RAGConfig:
    """Configuration specific to RAG orchestration."""
    
    # Maximum context length for AI model (in tokens)
    # Context = retrieved chunks + mapping rules + query
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    
    # Whether to include controlled terminology in context
    INCLUDE_CT_IN_CONTEXT: bool = os.getenv("INCLUDE_CT_IN_CONTEXT", "true").lower() == "true"
    
    # Whether to include mapping assumptions in context
    INCLUDE_ASSUMPTIONS_IN_CONTEXT: bool = (
        os.getenv("INCLUDE_ASSUMPTIONS_IN_CONTEXT", "true").lower() == "true"
    )
    
    # Domain-specific context (enable specialized handling for specific domains)
    DOMAIN_SPECIFIC_CONTEXT: bool = os.getenv("DOMAIN_SPECIFIC_CONTEXT", "true").lower() == "true"


class LoggingConfig:
    """Logging configuration."""
    
    # Log level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Log file path
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")


class Config:
    """
    Unified configuration class aggregating all subsystems.
    
    Usage:
        from config import Config
        
        # Access database settings
        db_host = Config.db.HOST
        
        # Access embedding settings
        embedding_model = Config.embeddings.MODEL
    """
    
    db = DatabaseConfig
    embeddings = EmbeddingConfig
    chunking = ChunkingConfig
    query = QueryConfig
    rag = RAGConfig
    logging = LoggingConfig


# Environment validation
def validate_config() -> bool:
    """
    Validate configuration for required values.
    
    Returns:
        bool: True if configuration is valid, raises error otherwise
    """
    # For production, you'd want stricter validation
    # For training, we're more lenient with defaults
    
    if Config.chunking.CHUNK_SIZE < Config.chunking.CHUNK_OVERLAP:
        raise ValueError("CHUNK_SIZE must be greater than CHUNK_OVERLAP")
    
    if Config.query.SIMILARITY_THRESHOLD < 0 or Config.query.SIMILARITY_THRESHOLD > 1:
        raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1")
    
    return True


if __name__ == "__main__":
    # Test configuration loading
    validate_config()
    print("Configuration loaded successfully")
    print(f"Database: {Config.db.DATABASE}")
    print(f"Embedding Model: {Config.embeddings.MODEL}")
    print(f"Chunk Size: {Config.chunking.CHUNK_SIZE} tokens")
