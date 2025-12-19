"""
High-level search API for XSIAM patterns.

Provides specialized search functions for different content types
and can optionally fetch full content from source files.
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .store import PatternStore, get_default_db_path


class PatternSearch:
    """High-level search interface for XSIAM patterns."""

    def __init__(
        self,
        store: PatternStore | None = None,
        content_root: Path | str | None = None,
    ):
        """
        Initialize pattern search.

        Args:
            store: PatternStore instance (creates default if not provided)
            content_root: Path to content repo for fetching full files
        """
        self.store = store or PatternStore()

        # Resolve content root for fetching full files
        if content_root:
            self.content_root = Path(content_root)
        elif content_path := os.getenv("DEMISTO_SDK_CONTENT_PATH"):
            self.content_root = Path(content_path)
        else:
            self.content_root = None

    def search_patterns(
        self,
        query: str,
        n_results: int = 5,
        content_types: list[str] | None = None,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Search for patterns matching a natural language query.

        Args:
            query: Natural language description of what you're looking for
            n_results: Maximum number of results
            content_types: Filter by types (playbook, script, integration, etc.)
            include_content: Include full file content in results

        Returns:
            Search results with metadata and optionally content
        """
        results = []

        # Search each requested type
        types_to_search = content_types or ["playbook", "script", "integration"]

        for item_type in types_to_search:
            matches = self.store.search(
                query=query,
                n_results=n_results,
                item_type=item_type,
            )
            results.extend(matches)

        # Sort by similarity and take top n
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        results = results[:n_results]

        # Optionally fetch full content
        if include_content and self.content_root:
            for result in results:
                if content := self._fetch_content(result.get("path", "")):
                    result["content"] = content

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    def find_similar_playbooks(
        self,
        description: str,
        n_results: int = 5,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Find playbooks similar to a description.

        Args:
            description: Description of the playbook you want to create
            n_results: Maximum number of results
            include_content: Include full YAML content

        Returns:
            Similar playbooks with metadata
        """
        matches = self.store.search(
            query=description,
            n_results=n_results,
            item_type="playbook",
        )

        if include_content and self.content_root:
            for match in matches:
                if content := self._fetch_content(match.get("path", "")):
                    match["content"] = content

        return {
            "query": description,
            "result_count": len(matches),
            "playbooks": matches,
        }

    def find_similar_scripts(
        self,
        description: str,
        n_results: int = 5,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Find scripts similar to a description.

        Args:
            description: Description of the script functionality
            n_results: Maximum number of results
            include_content: Include full Python/YAML content

        Returns:
            Similar scripts with metadata
        """
        matches = self.store.search(
            query=description,
            n_results=n_results,
            item_type="script",
        )

        if include_content and self.content_root:
            for match in matches:
                if content := self._fetch_content(match.get("path", "")):
                    match["content"] = content

        return {
            "query": description,
            "result_count": len(matches),
            "scripts": matches,
        }

    def find_integration_patterns(
        self,
        description: str,
        n_results: int = 5,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Find integration patterns matching a description.

        Args:
            description: Description of the integration type
            n_results: Maximum number of results
            include_content: Include full content

        Returns:
            Matching integrations with metadata
        """
        matches = self.store.search(
            query=description,
            n_results=n_results,
            item_type="integration",
        )

        if include_content and self.content_root:
            for match in matches:
                if content := self._fetch_content(match.get("path", "")):
                    match["content"] = content

        return {
            "query": description,
            "result_count": len(matches),
            "integrations": matches,
        }

    def find_xql_examples(
        self,
        description: str,
        rule_type: str | None = None,
        n_results: int = 5,
        include_content: bool = True,  # Usually want full XQL
    ) -> dict[str, Any]:
        """
        Find XQL parsing/modeling rule examples.

        Args:
            description: Description of what the XQL should do
            rule_type: "parsing" or "modeling" (or None for both)
            n_results: Maximum number of results
            include_content: Include full XQL content

        Returns:
            Matching XQL rules with content
        """
        results = []

        if rule_type in (None, "parsing"):
            parsing = self.store.search(
                query=description,
                n_results=n_results,
                item_type="parsing_rule",
            )
            results.extend(parsing)

        if rule_type in (None, "modeling"):
            modeling = self.store.search(
                query=description,
                n_results=n_results,
                item_type="modeling_rule",
            )
            results.extend(modeling)

        # Sort by similarity
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        results = results[:n_results]

        # Fetch full XQL content
        if include_content and self.content_root:
            for result in results:
                if content := self._fetch_content(result.get("path", "")):
                    result["content"] = content

        return {
            "query": description,
            "rule_type": rule_type,
            "result_count": len(results),
            "rules": results,
        }

    def find_classifier_examples(
        self,
        description: str,
        n_results: int = 5,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Find classifier examples.

        Args:
            description: Description of classification needs
            n_results: Maximum number of results
            include_content: Include full JSON content

        Returns:
            Matching classifiers
        """
        matches = self.store.search(
            query=description,
            n_results=n_results,
            item_type="classifier",
        )

        if include_content and self.content_root:
            for match in matches:
                if content := self._fetch_content(match.get("path", "")):
                    match["content"] = content

        return {
            "query": description,
            "result_count": len(matches),
            "classifiers": matches,
        }

    def find_mapper_examples(
        self,
        description: str,
        direction: str | None = None,
        n_results: int = 5,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """
        Find mapper examples.

        Args:
            description: Description of mapping needs
            direction: "incoming" or "outgoing" (or None for both)
            n_results: Maximum number of results
            include_content: Include full JSON content

        Returns:
            Matching mappers
        """
        matches = self.store.search(
            query=description,
            n_results=n_results,
            item_type="mapper",
        )

        # Filter by direction if specified
        if direction:
            matches = [m for m in matches if m.get("direction") == direction]

        if include_content and self.content_root:
            for match in matches:
                if content := self._fetch_content(match.get("path", "")):
                    match["content"] = content

        return {
            "query": description,
            "direction": direction,
            "result_count": len(matches),
            "mappers": matches,
        }

    def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the pattern index."""
        return self.store.get_stats()

    def _fetch_content(self, path: str) -> str | None:
        """Fetch full content from a file path."""
        if not path or not self.content_root:
            return None

        # Handle both absolute and relative paths
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.content_root / path

        if not file_path.exists():
            return None

        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return None


# Convenience function for quick searches
def search(query: str, n_results: int = 5) -> dict[str, Any]:
    """
    Quick search across all content types.

    Args:
        query: Natural language query
        n_results: Maximum results

    Returns:
        Search results
    """
    searcher = PatternSearch()
    return searcher.search_patterns(query, n_results=n_results)
