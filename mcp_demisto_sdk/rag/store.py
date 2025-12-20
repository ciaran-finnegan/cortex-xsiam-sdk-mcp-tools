"""
ChromaDB-based vector store for XSIAM patterns.

Stores embeddings of playbooks, scripts, and integrations for semantic search.
Uses sentence-transformers for local embedding generation (no API required).
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_COLLECTION = "xsiam_patterns"


def get_default_db_path() -> Path:
    """Get default path for ChromaDB storage."""
    # Check environment variable first
    if db_path := os.getenv("XSIAM_PATTERN_DB"):
        return Path(db_path)

    # Default to ~/.xsiam-patterns/chroma
    return Path.home() / ".xsiam-patterns" / "chroma"


class PatternStore:
    """Vector store for XSIAM content patterns."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        model_name: str = DEFAULT_MODEL,
        collection_name: str = DEFAULT_COLLECTION,
    ):
        """
        Initialize the pattern store.

        Args:
            db_path: Path to ChromaDB storage directory
            model_name: Sentence transformer model for embeddings
            collection_name: Name of the ChromaDB collection
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb not installed. Install with: pip install chromadb"
            )
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.db_path = Path(db_path) if db_path else get_default_db_path()
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.model_name = model_name
        self.collection_name = collection_name

        # Initialize embedding model (lazy load on first use)
        self._model: SentenceTransformer | None = None

        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def model(self) -> "SentenceTransformer":
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _create_embedding_text(self, item: dict[str, Any], item_type: str) -> str:
        """Create text for embedding from an item."""
        parts = []

        # Name and description are always included
        if name := item.get("name"):
            parts.append(f"name: {name}")
        if desc := item.get("description"):
            parts.append(f"description: {desc}")

        # Type-specific fields
        if item_type == "playbook":
            if intents := item.get("intents"):
                parts.append(f"intents: {', '.join(intents)}")
            if commands := item.get("commands"):
                cmd_names = [c.get("command", "") for c in commands[:10]]
                parts.append(f"commands: {', '.join(cmd_names)}")
            if subplaybooks := item.get("subplaybooks"):
                sub_names = [s.get("name", "") for s in subplaybooks[:5]]
                parts.append(f"subplaybooks: {', '.join(sub_names)}")
            if task_counts := item.get("task_counts"):
                parts.append(f"task_types: {', '.join(task_counts.keys())}")

        elif item_type == "script":
            if tags := item.get("tags"):
                parts.append(f"tags: {', '.join(tags)}")
            if args := item.get("args"):
                arg_names = [a.get("name", "") for a in args[:10]]
                parts.append(f"arguments: {', '.join(arg_names)}")

        return " | ".join(parts)

    def add_items(
        self,
        items: list[dict[str, Any]],
        item_type: str = "playbook",
        batch_size: int = 100,
        content_root: Path | None = None,
    ) -> int:
        """
        Add items to the vector store.

        Args:
            items: List of playbook/script dictionaries from playbook_index.json
            item_type: Type of items ("playbook" or "script")
            batch_size: Number of items to process at once
            content_root: If provided, store paths relative to this root
                (prevents leaking absolute paths in metadata)

        Returns:
            Number of items added
        """
        added = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            ids = []
            documents = []
            metadatas = []
            embeddings = []

            for item in batch:
                # Use path for uniqueness, fall back to id/name
                item_path = item.get("path", "")
                item_id = item.get("id") or item.get("name", f"unknown_{i}")
                # Include path hash for uniqueness
                if item_path:
                    path_hash = hashlib.md5(item_path.encode()).hexdigest()[:8]
                    doc_id = f"{item_type}:{item_id}:{path_hash}"
                else:
                    doc_id = f"{item_type}:{item_id}"

                # Create embedding text
                embed_text = self._create_embedding_text(item, item_type)
                if not embed_text:
                    continue

                # Generate embedding
                embedding = self.model.encode(embed_text).tolist()

                # Convert absolute path to relative path if content_root provided
                stored_path = item_path
                if item_path and content_root:
                    try:
                        abs_path = Path(item_path)
                        if abs_path.is_absolute():
                            stored_path = str(abs_path.relative_to(content_root))
                    except ValueError:
                        # Path not relative to content_root, store as-is
                        logger.debug(f"Path not relative to content_root: {item_path}")

                # Prepare metadata (ChromaDB requires flat structure)
                metadata = {
                    "type": item_type,
                    "id": str(item_id),
                    "name": item.get("name", ""),
                    "path": stored_path,
                    "pack": item.get("pack", ""),
                    "score": item.get("score", 0),
                    "deprecated": item.get("deprecated", False),
                    "fromversion": item.get("fromversion", ""),
                }

                # Add intents as comma-separated string
                if intents := item.get("intents"):
                    metadata["intents"] = ",".join(intents)

                ids.append(doc_id)
                documents.append(embed_text)
                metadatas.append(metadata)
                embeddings.append(embedding)

            if ids:
                self._collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
                added += len(ids)

        return added

    def search(
        self,
        query: str,
        n_results: int = 5,
        item_type: str | None = None,
        min_score: int | None = None,
        include_deprecated: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Search for patterns matching a query.

        Args:
            query: Natural language query
            n_results: Maximum number of results
            item_type: Filter by type ("playbook" or "script")
            min_score: Minimum quality score filter
            include_deprecated: Include deprecated items

        Returns:
            List of matching items with similarity scores
        """
        # Build where clause for filtering
        where_clauses = []

        if item_type:
            where_clauses.append({"type": {"$eq": item_type}})

        if not include_deprecated:
            where_clauses.append({"deprecated": {"$eq": False}})

        if min_score is not None:
            where_clauses.append({"score": {"$gte": min_score}})

        where = None
        if len(where_clauses) == 1:
            where = where_clauses[0]
        elif len(where_clauses) > 1:
            where = {"$and": where_clauses}

        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()

        # Search
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        items = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Convert distance to similarity (cosine distance: 0 = identical)
                similarity = 1 - distance

                items.append({
                    "id": doc_id,
                    "similarity": round(similarity, 4),
                    "type": metadata.get("type", ""),
                    "name": metadata.get("name", ""),
                    "path": metadata.get("path", ""),
                    "pack": metadata.get("pack", ""),
                    "score": metadata.get("score", 0),
                    "intents": metadata.get("intents", "").split(",") if metadata.get("intents") else [],
                })

        return items

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the store."""
        count = self._collection.count()

        # Get type breakdown
        playbook_count = len(self._collection.get(
            where={"type": {"$eq": "playbook"}},
            include=[],
        )["ids"])

        script_count = len(self._collection.get(
            where={"type": {"$eq": "script"}},
            include=[],
        )["ids"])

        return {
            "total_items": count,
            "playbooks": playbook_count,
            "scripts": script_count,
            "db_path": str(self.db_path),
            "model": self.model_name,
            "collection": self.collection_name,
        }

    def clear(self) -> None:
        """Clear all items from the store."""
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
