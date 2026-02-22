"""
SDTM IG Content Loader - Chunks and Loads Content into PostgreSQL

This module reads SDTM IG content from markdown files, chunks them into
semantic segments, generates embeddings, and loads them into PostgreSQL.

RAG Architecture Role:
- Transforms raw SDTM IG documentation into retrieval-friendly chunks
- Creates embeddings for semantic search
- Populates the vector database for fast, relevant context retrieval
- Enables the AI orchestrator to find applicable rules for any SDTM mapping question

Chunking Strategy:
- Target: ~500 tokens per chunk (~2000 characters)
- Overlap: 100 tokens for context continuity
- Preserves semantic boundaries (sections, subsections)
- Tracks document structure (domain, section, subsection)
"""

import os
import re
import psycopg2
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import json

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextChunker:
    """
    Splits text into semantically-coherent chunks with configurable overlap.
    
    This chunker is "smart" - it tries to preserve section boundaries
    and semantic units rather than just splitting at token boundaries.
    """
    
    def __init__(
        self,
        chunk_size: int = Config.chunking.CHUNK_SIZE,
        overlap: int = Config.chunking.CHUNK_OVERLAP,
        max_chars: int = Config.chunking.MAX_CHUNK_CHARS,
        min_chars: int = Config.chunking.MIN_CHUNK_CHARS
    ):
        """
        Initialize chunker with token/character limits.
        
        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap in tokens between chunks
            max_chars: Maximum characters per chunk
            min_chars: Minimum characters per chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_chars = max_chars
        self.min_chars = min_chars
        
        # Token estimation: ~4 characters per token for English
        self.chars_per_token = 4
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is an approximation. Production systems would use
        the actual tokenizer from the embedding model (tiktoken for OpenAI, etc.)
        
        Args:
            text: Text to estimate
            
        Returns:
            Approximate token count
        """
        return len(text) // self.chars_per_token
    
    def chunk_by_sections(self, text: str, max_section_level: int = 3) -> List[Tuple[str, Dict]]:
        """
        Intelligently chunk text by preserving section structure.
        
        Identifies markdown headings (# ## ###) and tries to keep sections
        together while respecting size limits.
        
        Args:
            text: Full text to chunk
            max_section_level: Maximum heading level to treat as section boundary
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        chunks = []
        
        # Split by section headers
        # Pattern: # Header, ## Header, ### Header
        heading_pattern = r'^(#{1,%d})\s+(.+)$' % max_section_level
        
        lines = text.split('\n')
        current_section = ""
        current_level = 0
        current_subsection = ""
        section_start_line = 0
        
        for i, line in enumerate(lines):
            heading_match = re.match(heading_pattern, line, re.MULTILINE)
            
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # If we have accumulated content and hit a new section
                # at same or higher level (smaller number = higher), flush it
                if current_section and level <= current_level:
                    chunk_text = current_section.strip()
                    if len(chunk_text) >= self.min_chars:
                        chunks.append((chunk_text, {
                            'section': heading_text if level == 1 else current_section.split('\n')[0][:100],
                            'subsection': current_subsection,
                            'chunk_type': 'section_content'
                        }))
                    current_section = ""
                
                # Update section tracking
                if level == 1:
                    current_section = line + "\n"
                    current_subsection = ""
                elif level == 2:
                    current_subsection = heading_text
                    current_section = line + "\n"
                else:
                    current_section = line + "\n"
                
                current_level = level
            else:
                current_section += line + "\n"
            
            # Flush chunks if current section too large
            if len(current_section) > self.max_chars:
                # Split large section by paragraphs
                chunk_text = current_section.strip()
                if len(chunk_text) >= self.min_chars:
                    chunks.append((chunk_text, {
                        'subsection': current_subsection,
                        'chunk_type': 'section_content'
                    }))
                current_section = ""
        
        # Don't forget last section
        if current_section.strip():
            chunk_text = current_section.strip()
            if len(chunk_text) >= self.min_chars:
                chunks.append((chunk_text, {
                    'subsection': current_subsection,
                    'chunk_type': 'section_content'
                }))
        
        return chunks
    
    def chunk_with_overlap(self, text: str) -> List[str]:
        """
        Chunk text with overlap for semantic continuity.
        
        This is the fallback chunker if intelligent section-based chunking
        isn't used. It creates overlapping chunks of fixed character size.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunk strings
        """
        chunks = []
        char_size = self.chunk_size * self.chars_per_token
        overlap_chars = self.overlap * self.chars_per_token
        
        start = 0
        while start < len(text):
            end = start + char_size
            
            # Try to end at sentence boundary (period + space)
            if end < len(text):
                # Look back from end position for sentence boundary
                lookback = min(200, end - start // 2)
                for i in range(end, max(start, end - lookback), -1):
                    if text[i:i+2] in ['. ', '.\n', '?\n', '!\n']:
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start with overlap
            start = end - overlap_chars
            if start <= 0:
                break
        
        return chunks


class ContentProcessor:
    """Process markdown content and extract domain/section metadata."""
    
    @staticmethod
    def extract_domain(filename: str) -> str:
        """
        Extract SDTM domain from filename.
        
        Examples:
            'dm_domain.md' → 'DM'
            'ae_domain.md' → 'AE'
            'general_assumptions.md' → 'GENERAL'
        
        Args:
            filename: Markdown filename
            
        Returns:
            Domain code
        """
        if 'general' in filename.lower():
            return 'GENERAL'
        
        match = re.match(r'([a-z]+)_', filename.lower())
        if match:
            return match.group(1).upper()
        
        return 'UNKNOWN'
    
    @staticmethod
    def extract_sections(text: str) -> List[Tuple[str, str]]:
        """
        Extract all section headings from markdown.
        
        Args:
            text: Markdown text
            
        Returns:
            List of (heading_level, heading_text) tuples
        """
        sections = []
        for line in text.split('\n'):
            match = re.match(r'^(#+)\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text_content = match.group(2).strip()
                sections.append((level, text_content))
        
        return sections


class EmbeddingGenerator:
    """
    Generate embeddings for text chunks.
    
    In production, this would call OpenAI API, Claude API, or local model.
    For training, we provide a mock implementation that creates deterministic
    placeholder embeddings based on text hash.
    """
    
    def __init__(self, provider: str = Config.embeddings.PROVIDER):
        """
        Initialize embedding generator.
        
        Args:
            provider: "openai", "claude", or "mock"
        """
        self.provider = provider
        self.dimensions = Config.embeddings.DIMENSIONS
        logger.info(f"Initialized {provider} embedding generator (dim={self.dimensions})")
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing embedding vector
        """
        if self.provider == "mock":
            return self._mock_embedding(text)
        elif self.provider == "openai":
            return self._openai_embedding(text)
        elif self.provider == "claude":
            return self._claude_embedding(text)
        else:
            logger.warning(f"Unknown provider {self.provider}, using mock")
            return self._mock_embedding(text)
    
    def _mock_embedding(self, text: str) -> List[float]:
        """
        Generate mock embedding for training/testing.
        
        Uses text hash to create deterministic, repeatable embeddings.
        Chunks with similar text will have similar (but not identical) embeddings.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector of random floats in [-1, 1] range
        """
        import hashlib
        import random
        
        # Use text hash as seed for reproducibility
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % (2**31)
        rng = random.Random(seed)
        
        # Generate embedding as random unit vector
        # In real system, this would be semantic representation
        embedding = [rng.gauss(0, 0.3) for _ in range(self.dimensions)]
        
        # Normalize to unit vector for cosine similarity
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _openai_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.
        
        Requires OPENAI_API_KEY environment variable.
        Uses text-embedding-3-small model (1536 dimensions).
        
        Args:
            text: Text to embed
            
        Returns:
            OpenAI embedding vector
        """
        try:
            import openai
            
            if not Config.embeddings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY not set, falling back to mock")
                return self._mock_embedding(text)
            
            openai.api_key = Config.embeddings.OPENAI_API_KEY
            response = openai.Embedding.create(
                input=text,
                model=Config.embeddings.MODEL
            )
            return response['data'][0]['embedding']
        
        except ImportError:
            logger.error("openai library not installed, falling back to mock")
            return self._mock_embedding(text)
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}, falling back to mock")
            return self._mock_embedding(text)
    
    def _claude_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Claude API.
        
        Note: Claude API typically requires different endpoint.
        This is a placeholder for future implementation.
        
        Args:
            text: Text to embed
            
        Returns:
            Claude embedding vector (placeholder)
        """
        logger.warning("Claude embeddings not yet implemented, using mock")
        return self._mock_embedding(text)


class SDTMIGLoader:
    """Load SDTM IG content into PostgreSQL database."""
    
    def __init__(self, content_dir: str):
        """
        Initialize loader.
        
        Args:
            content_dir: Directory containing markdown files
        """
        self.content_dir = Path(content_dir)
        self.conn = None
        self.cur = None
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
    
    def connect(self, connection_string: str) -> bool:
        """
        Connect to PostgreSQL database.
        
        Args:
            connection_string: PostgreSQL URI
            
        Returns:
            True if successful
        """
        try:
            self.conn = psycopg2.connect(connection_string)
            self.cur = self.conn.cursor()
            logger.info("Connected to PostgreSQL")
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
    
    def load_content_files(self) -> List[Tuple[str, str]]:
        """
        Load all markdown files from content directory.
        
        Args:
            
        Returns:
            List of (filename, content) tuples
        """
        files = []
        
        if not self.content_dir.exists():
            logger.error(f"Content directory not found: {self.content_dir}")
            return files
        
        for md_file in self.content_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                files.append((md_file.name, content))
                logger.info(f"Loaded {md_file.name} ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Failed to load {md_file}: {e}")
        
        return files
    
    def chunk_content(self, filename: str, content: str) -> List[Tuple[str, Dict]]:
        """
        Chunk content into semantic segments.
        
        Args:
            filename: Source filename (for metadata)
            content: Text content
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        domain = ContentProcessor.extract_domain(filename)
        
        # Use intelligent section-based chunking
        chunks = self.chunker.chunk_by_sections(content)
        
        # Add domain and filename to metadata
        for i, (chunk_text, metadata) in enumerate(chunks):
            metadata['domain'] = domain
            metadata['filename'] = filename
            metadata['sequence'] = i + 1
        
        logger.info(f"Chunked {filename} into {len(chunks)} segments")
        return chunks
    
    def load_chunks_to_db(self, chunks: List[Tuple[str, Dict]]) -> int:
        """
        Load chunks into database with embeddings.
        
        Args:
            chunks: List of (chunk_text, metadata) tuples
            
        Returns:
            Number of chunks successfully loaded
        """
        loaded = 0
        
        for chunk_text, metadata in chunks:
            try:
                # Generate embedding
                embedding = self.embedder.generate(chunk_text)
                
                # Insert into database
                insert_query = f"""
                INSERT INTO {Config.db.CHUNKS_TABLE}
                (domain, section, subsection, content, chunk_type, sequence, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                self.cur.execute(insert_query, (
                    metadata.get('domain', 'UNKNOWN'),
                    metadata.get('section', 'General'),
                    metadata.get('subsection'),
                    chunk_text,
                    metadata.get('chunk_type', 'text'),
                    metadata.get('sequence'),
                    # pgvector expects array format [x, y, z, ...] as string
                    str(embedding).replace('[', '[').replace(']', ']')
                ))
                
                self.conn.commit()
                loaded += 1
                
                if loaded % 10 == 0:
                    logger.info(f"Loaded {loaded} chunks...")
            
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Failed to load chunk: {e}")
        
        logger.info(f"Successfully loaded {loaded} chunks to database")
        return loaded
    
    def load_controlled_terminology(self):
        """
        Load sample controlled terminology into database.
        
        This is hardcoded sample data for the training exercise.
        In production, this would load from NCI thesaurus or CDISC codelist.
        """
        logger.info("Loading controlled terminology...")
        
        ct_data = [
            # SEX Codelist (C66742)
            ('C66742', 'Sex', 'C16576', 'M', 'Male; MAN; MALE', 'Biological male'),
            ('C66742', 'Sex', 'C16575', 'F', 'Female; WOMAN; FEMALE', 'Biological female'),
            ('C66742', 'Sex', 'C17998', 'U', 'Unknown; UNKN', 'Sex unknown'),
            
            # RACE Codelist (C74456 - US OMB Race Categories)
            ('C74456', 'Race', 'C17177', 'AMERICAN INDIAN OR ALASKA NATIVE',
             'American Indian; Native American; Alaska Native', 'Indigenous people of Americas'),
            ('C74456', 'Race', 'C41260', 'ASIAN', 'Asian; SE Asian; Oriental',
             'People from Far East, Southeast Asia, Indian subcontinent'),
            ('C74456', 'Race', 'C16352', 'BLACK OR AFRICAN AMERICAN',
             'Black; African American; Negro', 'People of African origin'),
            ('C74456', 'Race', 'C41261', 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER',
             'Pacific Islander; Hawaiian', 'People of Hawaiian, Pacific islands, other territories'),
            ('C74456', 'Race', 'C41262', 'WHITE', 'Caucasian; White; European',
             'People of European origin'),
            ('C74456', 'Race', 'C29676', 'MULTIPLE', 'Multiple races; Mixed race',
             'Subject reports more than one race category'),
            
            # ETHNIC Codelist (C74457 - Hispanic/Latino)
            ('C74457', 'Ethnicity', 'C17459', 'HISPANIC OR LATINO',
             'Hispanic; Latino; Spanish origin', 'Person of Spanish or Latin American origin'),
            ('C74457', 'Ethnicity', 'C41258', 'NOT HISPANIC OR LATINO',
             'Non-Hispanic; Non-Latino', 'Person not of Spanish/Latin American origin'),
            ('C74457', 'Ethnicity', 'C17998', 'UNKNOWN', 'Unknown ethnicity',
             'Ethnicity not specified or known'),
            
            # DTHFL Codelist (C66742 - Yes/No Flag)
            ('C66742', 'Death Flag', 'C25441', 'Y', 'Yes; TRUE; 1', 'Event occurred'),
            ('C66742', 'Death Flag', 'C68709', 'N', 'No; FALSE; 0', 'Event did not occur'),
        ]
        
        try:
            for codelist_code, codelist_name, term_code, term_value, synonyms, definition in ct_data:
                insert_query = f"""
                INSERT INTO {Config.db.CT_TABLE}
                (codelist_code, codelist_name, term_code, term_value, synonyms, definition)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                self.cur.execute(insert_query, (
                    codelist_code,
                    codelist_name,
                    term_code,
                    term_value,
                    synonyms,
                    definition
                ))
            
            self.conn.commit()
            logger.info(f"Loaded {len(ct_data)} controlled terminology entries")
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load controlled terminology: {e}")
    
    def load_mapping_assumptions(self):
        """
        Load mapping assumptions into database.
        
        These are extracted/summarized from the IG content for quick lookup.
        """
        logger.info("Loading mapping assumptions...")
        
        assumptions = [
            # DM domain assumptions
            ('DM', 'RFSTDTC', 
             'RFSTDTC can be derived as informed consent date, first dose date, or '
             'the earlier of both dates. Must be applied consistently for all subjects.',
             'IG Section 2.3.1.1', 1, 1),
            
            ('DM', 'RFSTDTC',
             'Use informed consent date (Approach 1) for studies with strict IC requirements.',
             'IG Section 2.3.1.1', 2, 1),
            
            ('DM', 'RFSTDTC',
             'Use first dose date (Approach 2) for dose-tracking focused studies.',
             'IG Section 2.3.1.1', 2, 2),
            
            ('DM', 'RFENDTC',
             'RFENDTC typically represents date of last dose. Use termination date for '
             'early termination scenarios.',
             'IG Section 2.3.1.2', 2, None),
            
            ('DM', 'SEX',
             'SEX typically from subject self-report at screening. Use medical history only '
             'if self-report unavailable.',
             'IG DM Variables', 2, None),
            
            ('DM', 'RACE',
             'When subject reports multiple races, use RACE="MULTIPLE" and record individual '
             'races in SUPPDM with QNAM="RACE1", "RACE2", etc.',
             'IG DM Variables', 1, 2),
            
            ('DM', 'RACE',
             'For "Other Specify" responses, attempt to reclassify to CDISC codelist value. '
             'Record original text in SUPPDM with QNAM="RACESPEC".',
             'IG DM Variables', 2, 3),
            
            ('DM', 'BRTHDTC',
             'BRTHDTC often partial (MM-YYYY or YYYY only). Calculate AGE from complete date if available.',
             'IG DM Variables', 2, None),
            
            ('DM', 'DTHDTC',
             'For partial death dates, impute: Day Unknown→15, Month Unknown→06, Year Unknown→apply protocol rule. '
             'Record imputation flag in SUPPDM with QNAM="DTHIMP".',
             'IG DM Variables', 1, None),
            
            ('DM', 'USUBJID',
             'USUBJID must be globally unique and never change. Construct as STUDYID-SITEID-SUBJID or '
             'STUDYID-SEQUENTIAL depending on enrollment scheme.',
             'IG Section 2.2', 1, None),
            
            # General assumptions
            ('GENERAL', None,
             'All dates must use ISO 8601 format: YYYY-MM-DD. Datetime: YYYY-MM-DDTHH:MM:SS in 24-hour format.',
             'IG Section 2.1', 1, None),
            
            ('GENERAL', None,
             'Use NULL for missing data, never empty string or special characters like "-" or "."',
             'IG Section 2.2', 1, None),
            
            ('GENERAL', None,
             'Each domain with multiple records per subject must have unique --SEQ variable (1, 2, 3, ...)',
             'IG Section 2.2', 1, None),
        ]
        
        try:
            for domain, variable, assumption_text, ig_ref, priority, approach in assumptions:
                insert_query = f"""
                INSERT INTO {Config.db.ASSUMPTIONS_TABLE}
                (domain, variable, assumption_text, ig_reference, priority, approach_number)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                self.cur.execute(insert_query, (
                    domain,
                    variable,
                    assumption_text,
                    ig_ref,
                    priority,
                    approach
                ))
            
            self.conn.commit()
            logger.info(f"Loaded {len(assumptions)} mapping assumptions")
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load mapping assumptions: {e}")
    
    def load_all(self) -> bool:
        """
        Execute complete load process.
        
        Returns:
            True if all loads successful
        """
        logger.info("=" * 60)
        logger.info("Starting SDTM IG Content Load")
        logger.info("=" * 60)
        
        # Connect
        if not self.connect(Config.db.get_connection_string()):
            return False
        
        try:
            # Load markdown content files
            files = self.load_content_files()
            if not files:
                logger.warning("No content files found")
            
            # Process each file
            total_chunks = 0
            for filename, content in files:
                chunks = self.chunk_content(filename, content)
                loaded = self.load_chunks_to_db(chunks)
                total_chunks += loaded
            
            # Load controlled terminology
            self.load_controlled_terminology()
            
            # Load mapping assumptions
            self.load_mapping_assumptions()
            
            logger.info("=" * 60)
            logger.info(f"Load complete: {total_chunks} content chunks loaded")
            logger.info("=" * 60)
            
            return True
        
        finally:
            self.disconnect()


def main():
    """Main execution."""
    
    # Get content directory (relative to script)
    script_dir = Path(__file__).parent
    content_dir = script_dir / "sdtm_ig_content"
    
    loader = SDTMIGLoader(str(content_dir))
    success = loader.load_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
