"""
IG Client: wraps the SDTM IG knowledge base for agent use.

Provides domain variable definitions, required/conditional status, CT lookups,
and mapping assumptions.  Works in two modes:

1. Database mode: queries PostgreSQL + pgvector via sdtm_ig_db/query_ig.py
2. File-based mode (fallback): parses the markdown files in sdtm_ig_content/

The file-based mode is the default and requires NO database setup.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on path when running from orchestrator/
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from sdtm_ig_db.config import Config
    from sdtm_ig_db.query_ig import SDTMIGQuery
    _IG_DB_AVAILABLE = True
except ImportError:
    _IG_DB_AVAILABLE = False
    Config = None
    SDTMIGQuery = None

# Path to IG markdown content
_IG_CONTENT_DIR = _project_root / "sdtm_ig_db" / "sdtm_ig_content"


def _parse_domain_summary_table(md_path: Path) -> List[Dict[str, str]]:
    """
    Parse the summary table from a domain markdown file.

    Returns a list of dicts with keys:
      variable, type, format, required, controlled_terminology, notes
    """
    if not md_path.exists():
        return []

    text = md_path.read_text(encoding="utf-8")

    # Find the summary table (starts after "## Summary Table")
    table_match = re.search(
        r"## Summary Table.*?\n\|.*?\n\|[-\s|]+\n((?:\|.*?\n)+)",
        text,
        re.DOTALL,
    )
    if not table_match:
        return []

    rows = []
    for line in table_match.group(1).strip().split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6:
            rows.append({
                "variable": cells[0],
                "type": cells[1],
                "format": cells[2],
                "required": cells[3],
                "controlled_terminology": cells[4],
                "notes": cells[5] if len(cells) > 5 else "",
            })
    return rows


def _parse_variable_sections(md_path: Path) -> Dict[str, str]:
    """
    Parse variable sections from domain markdown.

    Returns a dict of variable_name -> section_text for detailed lookup.
    """
    if not md_path.exists():
        return {}

    text = md_path.read_text(encoding="utf-8")
    sections: Dict[str, str] = {}

    # Split on ### headings that match "### VARNAME - Description"
    parts = re.split(r"(?=^### [A-Z])", text, flags=re.MULTILINE)
    for part in parts:
        match = re.match(r"### ([A-Z]+)\s*-", part)
        if match:
            sections[match.group(1)] = part.strip()

    return sections


class IGClient:
    """
    Provides SDTM IG variable definitions, CT lookups, and mapping assumptions.

    Falls back to file-based parsing of sdtm_ig_content/ markdown when the
    database is not available.  The file-based fallback is fully functional for
    domain variable metadata, required/conditional status, and CT references.

    Supports multiple content directories (e.g., study-specific IG content that
    overrides or supplements the standard content).  Directories are searched in
    order; the first match wins.
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        content_dirs: Optional[List[str]] = None,
    ) -> None:
        self.db_config = db_config or {}
        self._client: Optional[Any] = None
        self._connected = False
        # Content directories: searched in order (study-specific first, standard last)
        self._content_dirs: List[Path] = (
            [Path(d) for d in content_dirs] if content_dirs else [_IG_CONTENT_DIR]
        )
        # File-based caches
        self._domain_tables: Dict[str, List[Dict[str, str]]] = {}
        self._domain_sections: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Database mode
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Connect to the SDTM IG database if available."""
        if not _IG_DB_AVAILABLE:
            return False
        try:
            conn_str = (
                f"postgresql://{self.db_config.get('user', getattr(Config.db, 'USER', 'sdtm_user'))}:"
                f"{self.db_config.get('password', getattr(Config.db, 'PASSWORD', 'sdtm_password'))}@"
                f"{self.db_config.get('host', getattr(Config.db, 'HOST', 'localhost'))}:"
                f"{self.db_config.get('port', getattr(Config.db, 'PORT', 5432))}/"
                f"{self.db_config.get('name', getattr(Config.db, 'DATABASE', 'sdtm_ig_rag'))}"
            )
            self._client = SDTMIGQuery(conn_str)
            self._connected = True
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        """Disconnect from the database."""
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
        self._connected = False

    # ------------------------------------------------------------------
    # File-based fallback (always available)
    # ------------------------------------------------------------------

    def _get_domain_md_path(self, domain: str) -> Path:
        """Return path to domain markdown file.

        Searches content directories in order (study-specific first, then
        standard).  Returns the first existing match, or falls back to the
        first directory if no match is found.
        """
        filename = f"{domain.lower()}_domain.md"
        for d in self._content_dirs:
            candidate = d / filename
            if candidate.exists():
                return candidate
        # Fallback: first dir (may not exist — handled by caller)
        return self._content_dirs[0] / filename

    def _load_domain_table(self, domain: str) -> List[Dict[str, str]]:
        """Load and cache the summary table for a domain."""
        if domain not in self._domain_tables:
            self._domain_tables[domain] = _parse_domain_summary_table(
                self._get_domain_md_path(domain)
            )
        return self._domain_tables[domain]

    def _load_domain_sections(self, domain: str) -> Dict[str, str]:
        """Load and cache the variable sections for a domain."""
        if domain not in self._domain_sections:
            self._domain_sections[domain] = _parse_variable_sections(
                self._get_domain_md_path(domain)
            )
        return self._domain_sections[domain]

    # ------------------------------------------------------------------
    # Public API — used by agents
    # ------------------------------------------------------------------

    def get_domain_variables(self, domain: str) -> List[Dict[str, str]]:
        """
        Return all variables defined for a domain with their metadata.

        Each dict has: variable, type, format, required, controlled_terminology, notes.
        Works without the database (parses markdown files).
        """
        return self._load_domain_table(domain)

    def get_required_variables(self, domain: str) -> List[str]:
        """Return variable names that are Required for this domain."""
        table = self._load_domain_table(domain)
        return [row["variable"] for row in table if row["required"].strip() == "Req"]

    def get_conditional_variables(self, domain: str) -> List[str]:
        """Return variable names that are Conditional for this domain."""
        table = self._load_domain_table(domain)
        return [row["variable"] for row in table if "Cond" in row["required"]]

    def get_ct_variables(self, domain: str) -> List[Dict[str, str]]:
        """Return variables that have controlled terminology, with their CT info."""
        table = self._load_domain_table(domain)
        return [row for row in table if row["controlled_terminology"].strip() == "Yes"]

    def get_variable_detail(self, domain: str, variable: str) -> str:
        """
        Return the full IG section text for a specific variable.

        Includes assumptions, derivation rules, multiple valid approaches, etc.
        """
        sections = self._load_domain_sections(domain)
        return sections.get(variable, "")

    def query_variable_guidance(self, domain: str, variable: str) -> List[Dict[str, Any]]:
        """
        Return relevant IG chunks for a domain/variable.

        Tries database first, falls back to markdown parsing.
        """
        # Try database
        if not self._connected and _IG_DB_AVAILABLE:
            self.connect()
        if self._client:
            try:
                results = self._client.semantic_search(
                    f"{domain} {variable} variable definition mapping"
                )
                if results:
                    return results
            except Exception:
                pass

        # Fallback: file-based
        detail = self.get_variable_detail(domain, variable)
        if detail:
            return [{"content": detail, "source": "file", "domain": domain, "variable": variable}]
        return []

    def get_ct_values(self, codelist_code: str) -> List[str]:
        """Return allowed CT values for a codelist (if available via DB)."""
        if not self._connected and _IG_DB_AVAILABLE:
            self.connect()
        if not self._client:
            return []
        try:
            return self._client.get_codelist_values(codelist_code) or []
        except Exception:
            return []

    def is_available(self) -> bool:
        """Return True if the IG content is available (file or database)."""
        # File-based is always available if any content directory exists
        for d in self._content_dirs:
            if d.exists():
                return True
        return _IG_DB_AVAILABLE and self._connected

    def has_database(self) -> bool:
        """Return True if the PostgreSQL database is connected."""
        return _IG_DB_AVAILABLE and self._connected
