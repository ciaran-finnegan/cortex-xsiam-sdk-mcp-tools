"""
ChromaDB-based vector store for XSIAM patterns.

Stores embeddings of playbooks, scripts, and integrations for semantic search.
Uses sentence-transformers for local embedding generation (no API required).
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, cast

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
        """Create text for embedding from an item.

        Builds a rich text representation including all searchable fields
        to enable semantic search across the demisto/content repository.
        """
        parts = []

        # Name and description are always included
        if name := item.get("name"):
            parts.append(f"name: {name}")
        if desc := item.get("description"):
            parts.append(f"description: {desc}")
        if pack := item.get("pack"):
            parts.append(f"pack: {pack}")
        if intents := item.get("intents"):
            parts.append(f"intents: {', '.join(intents)}")

        # Type-specific fields
        if item_type == "playbook":
            # Commands with brand context
            if commands := item.get("commands"):
                cmd_strs = []
                for c in commands[:20]:
                    brand = c.get("brand", "")
                    cmd = c.get("command", "")
                    if brand and cmd:
                        cmd_strs.append(f"{brand}:{cmd}")
                    elif cmd:
                        cmd_strs.append(cmd)
                if cmd_strs:
                    parts.append(f"commands: {', '.join(cmd_strs)}")

            # Subplaybooks
            if subplaybooks := item.get("subplaybooks"):
                sub_names = [s.get("name", "") for s in subplaybooks[:10] if s.get("name")]
                if sub_names:
                    parts.append(f"subplaybooks: {', '.join(sub_names)}")

            # Task types
            if task_counts := item.get("task_counts"):
                parts.append(f"task_types: {', '.join(task_counts.keys())}")

            # Inputs with descriptions
            if inputs := item.get("inputs"):
                input_strs = []
                for inp in inputs[:10]:
                    if isinstance(inp, dict):
                        inp_name = inp.get("key", "") or inp.get("name", "")
                        inp_desc = inp.get("description", "")
                        if inp_name:
                            input_strs.append(f"{inp_name}: {inp_desc}" if inp_desc else inp_name)
                if input_strs:
                    parts.append(f"inputs: {'; '.join(input_strs)}")

            # Outputs with descriptions
            if outputs := item.get("outputs"):
                output_strs = []
                for out in outputs[:10]:
                    if isinstance(out, dict):
                        out_path = out.get("contextPath", "") or out.get("name", "")
                        out_desc = out.get("description", "")
                        if out_path:
                            output_strs.append(f"{out_path}: {out_desc}" if out_desc else out_path)
                if output_strs:
                    parts.append(f"outputs: {'; '.join(output_strs)}")

        elif item_type == "script":
            if script_type := item.get("type"):
                parts.append(f"type: {script_type}")
            if subtype := item.get("subtype"):
                parts.append(f"subtype: {subtype}")
            if tags := item.get("tags"):
                parts.append(f"tags: {', '.join(tags)}")

            # Arguments with descriptions
            if args := item.get("args"):
                arg_strs = []
                for arg in args[:15]:
                    if isinstance(arg, dict):
                        arg_name = arg.get("name", "")
                        arg_desc = arg.get("description", "")
                        if arg_name:
                            arg_strs.append(f"{arg_name}: {arg_desc}" if arg_desc else arg_name)
                if arg_strs:
                    parts.append(f"arguments: {'; '.join(arg_strs)}")

            # Outputs with descriptions
            if outputs := item.get("outputs"):
                output_strs = []
                for out in outputs[:10]:
                    if isinstance(out, dict):
                        out_path = out.get("contextPath", "") or out.get("name", "")
                        out_desc = out.get("description", "")
                        if out_path:
                            output_strs.append(f"{out_path}: {out_desc}" if out_desc else out_path)
                if output_strs:
                    parts.append(f"outputs: {'; '.join(output_strs)}")

        elif item_type == "integration":
            if category := item.get("category"):
                parts.append(f"category: {category}")
            if docker_image := item.get("docker_image"):
                parts.append(f"docker: {docker_image}")

            # Commands with descriptions, arguments, and outputs
            if commands := item.get("commands"):
                cmd_strs: list[str] = []
                all_args: list[str] = []
                all_outputs: list[str] = []

                for cmd in commands[:35]:
                    if isinstance(cmd, dict):
                        cmd_name = cmd.get("name", "")
                        cmd_desc = cmd.get("description", "")
                        if cmd_name:
                            cmd_strs.append(f"{cmd_name}: {cmd_desc}" if cmd_desc else cmd_name)

                        # Collect arguments
                        if args := cmd.get("arguments"):
                            for arg in args[:8]:
                                if isinstance(arg, dict):
                                    arg_name = arg.get("name", "")
                                    arg_desc = arg.get("description", "")
                                    if arg_name and len(all_args) < 50:
                                        arg_str = f"{cmd_name}.{arg_name}"
                                        if arg_desc:
                                            arg_str += f": {arg_desc[:80]}"
                                        all_args.append(arg_str)

                        # Collect outputs
                        if outputs := cmd.get("outputs"):
                            for out in outputs[:6]:
                                if isinstance(out, dict):
                                    ctx_path = out.get("contextPath", "")
                                    out_desc = out.get("description", "")
                                    if ctx_path and len(all_outputs) < 40:
                                        out_str = ctx_path
                                        if out_desc:
                                            out_str += f": {out_desc[:60]}"
                                        all_outputs.append(out_str)

                if cmd_strs:
                    parts.append(f"commands: {'; '.join(cmd_strs)}")
                if all_args:
                    parts.append(f"command_arguments: {'; '.join(all_args)}")
                if all_outputs:
                    parts.append(f"command_outputs: {'; '.join(all_outputs)}")

            # Configuration parameters with details
            if config := item.get("configuration"):
                if isinstance(config, list):
                    config_strs = []
                    for c in config[:15]:
                        if isinstance(c, dict):
                            cfg_name = c.get("name", "") or c.get("display", "")
                            if cfg_name:
                                config_strs.append(cfg_name)
                        elif isinstance(c, str) and c:
                            config_strs.append(c)
                    if config_strs:
                        parts.append(f"configuration: {', '.join(config_strs)}")

        elif item_type == "classifier":
            if clf_type := item.get("type"):
                parts.append(f"type: {clf_type}")
            if brand := item.get("brand"):
                parts.append(f"brand: {brand}")
            if default_type := item.get("default_type"):
                parts.append(f"default_incident_type: {default_type}")

            # Incident types this classifier can identify
            if incident_types := item.get("incident_types"):
                if isinstance(incident_types, list):
                    type_strs = [t for t in incident_types[:15] if t]
                    if type_strs:
                        parts.append(f"incident_types: {', '.join(type_strs)}")

            # Transformer keys (classification logic)
            if transformer_keys := item.get("transformer_keys"):
                if isinstance(transformer_keys, list):
                    key_strs = [k for k in transformer_keys[:10] if k]
                    if key_strs:
                        parts.append(f"classification_logic: {'; '.join(key_strs)}")

        elif item_type == "mapper":
            if mapper_type := item.get("type"):
                parts.append(f"type: {mapper_type}")
            if direction := item.get("direction"):
                parts.append(f"direction: {direction}")
            if brand := item.get("brand"):
                parts.append(f"brand: {brand}")

            # Incident types this mapper handles
            if incident_types := item.get("incident_types"):
                if isinstance(incident_types, list):
                    type_strs = [t for t in incident_types[:15] if t]
                    if type_strs:
                        parts.append(f"incident_types: {', '.join(type_strs)}")

            # Target fields being mapped
            if fields := item.get("fields"):
                if isinstance(fields, list):
                    field_names = [f for f in fields[:25] if f]
                    if field_names:
                        parts.append(f"target_fields: {', '.join(field_names)}")

            # Field mappings (source -> target)
            if field_mappings := item.get("field_mappings"):
                if isinstance(field_mappings, list):
                    mapping_strs = [m for m in field_mappings[:20] if m]
                    if mapping_strs:
                        parts.append(f"field_mappings: {'; '.join(mapping_strs)}")

        elif item_type in ("parsing_rule", "modeling_rule"):
            if rule_type := item.get("rule_type"):
                parts.append(f"rule_type: {rule_type}")

            # Include XQL content preview for searchability
            if content_preview := item.get("content_preview"):
                # Truncate but keep meaningful XQL syntax
                parts.append(f"xql: {content_preview[:400]}")

            # Filter statements
            if filters := item.get("filters"):
                if isinstance(filters, list):
                    filter_strs = [f for f in filters[:5] if f]
                    if filter_strs:
                        parts.append(f"filters: {'; '.join(filter_strs)}")

            # Alter statements
            if alters := item.get("alters"):
                if isinstance(alters, list):
                    alter_strs = [a for a in alters[:5] if a]
                    if alter_strs:
                        parts.append(f"alters: {'; '.join(alter_strs)}")

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
                embedding = [float(x) for x in self.model.encode(embed_text).tolist()]

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
                metadata: dict[str, str | int | float | bool | None] = {
                    "type": item_type,
                    "id": str(item_id),
                    "name": item.get("name", ""),
                    "path": stored_path,
                    "pack": item.get("pack", ""),
                    "score": int(item.get("score", 0)),
                    "deprecated": bool(item.get("deprecated", False)),
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
                cast(Any, self._collection).upsert(
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
        where_clauses: list[dict[str, dict[str, str | int | float | bool]]] = []

        if item_type:
            where_clauses.append({"type": {"$eq": item_type}})

        if not include_deprecated:
            where_clauses.append({"deprecated": {"$eq": False}})

        if min_score is not None:
            where_clauses.append({"score": {"$gte": min_score}})

        where: dict[str, Any] | None = None
        if len(where_clauses) == 1:
            where = where_clauses[0]
        elif len(where_clauses) > 1:
            where = {"$and": where_clauses}

        # Generate query embedding
        query_embedding = [float(x) for x in self.model.encode(query).tolist()]

        # Search
        results = cast(Any, self._collection).query(
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

                intents_raw = metadata.get("intents")
                intents = (
                    intents_raw.split(",")
                    if isinstance(intents_raw, str) and intents_raw
                    else []
                )

                items.append({
                    "id": doc_id,
                    "similarity": round(similarity, 4),
                    "type": metadata.get("type", ""),
                    "name": metadata.get("name", ""),
                    "path": metadata.get("path", ""),
                    "pack": metadata.get("pack", ""),
                    "score": metadata.get("score", 0),
                    "intents": intents,
                })

        return items

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the store."""
        count = self._collection.count()

        # Get type breakdown
        playbook_count = len(cast(Any, self._collection).get(
            where={"type": {"$eq": "playbook"}},
            include=[],
        )["ids"])

        script_count = len(cast(Any, self._collection).get(
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
