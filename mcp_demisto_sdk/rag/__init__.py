"""
RAG (Retrieval Augmented Generation) module for XSIAM pattern search.

Provides semantic search over playbooks, scripts, and integration patterns
from the Cortex XSIAM content library.
"""

from .store import PatternStore
from .search import PatternSearch

__all__ = ["PatternStore", "PatternSearch"]
