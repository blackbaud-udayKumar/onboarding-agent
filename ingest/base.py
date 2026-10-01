"""
Shared interface every ingestion source implements.

A "source" is anything that can hand back a list of Documents: repo files,
wiki pages, Confluence pages, Slack threads, etc. Keeping this interface
the same for local and remote sources means build_index.py doesn't need to
know or care where a document actually came from.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    text: str
    # A human-readable origin used in citations, e.g. "src/auth/login.py"
    # or "Confluence: Deployment Runbook".
    source: str
    # Stable id for the source system, if it has one (file path, page id...).
    source_id: str
    # Free-form extra info (repo name, url, last_modified, etc.) that gets
    # carried through to chunk metadata and can be surfaced in citations.
    metadata: dict = field(default_factory=dict)
    # Optional direct link (ADO file URL, Confluence page URL, ...).
    url: Optional[str] = None


class BaseSource:
    """Every source class implements fetch() -> list[Document]."""

    name = "base"

    def __init__(self, settings: dict):
        self.settings = settings

    def is_configured(self) -> bool:
        """Cheap check used before fetch() to give a clear error early."""
        return True

    def fetch(self) -> list[Document]:
        raise NotImplementedError
