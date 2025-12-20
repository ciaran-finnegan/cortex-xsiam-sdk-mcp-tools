"""
Indexer for XSIAM content patterns.

Processes the content repository or playbook_index.json to build
embeddings for semantic search.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .store import PatternStore, get_default_db_path

logger = logging.getLogger(__name__)


# Intent detection rules (from content repo's index_playbooks.py)
INTENT_RULES = [
    ("enrich", "enrichment"),
    ("enrichment", "enrichment"),
    ("block", "blocking"),
    ("isolate", "containment"),
    ("quarantine", "containment"),
    ("remediate", "remediation"),
    ("notify", "notification"),
    ("alert", "alerting"),
    ("ticket", "ticketing"),
    ("phishing", "phishing"),
    ("malware", "malware"),
    ("ransomware", "ransomware"),
    ("hunt", "hunting"),
    ("investigate", "investigation"),
    ("triage", "triage"),
    ("detonate", "detonation"),
    ("sandbox", "detonation"),
    ("poll", "polling"),
    ("mirror", "mirroring"),
    ("xql", "xql"),
    ("query", "query"),
    ("parse", "parsing"),
    ("classify", "classification"),
    ("map", "mapping"),
]


def infer_intents(text: str) -> list[str]:
    """Infer intents from name/description text."""
    intents = set()
    lowered = text.lower()
    for needle, label in INTENT_RULES:
        if needle in lowered:
            intents.add(label)
    return sorted(intents)


def load_yaml_file(
    path: Path, follow_symlinks: bool = False
) -> dict[str, Any] | None:
    """Load a YAML file safely with error logging.

    Args:
        path: Path to the YAML file
        follow_symlinks: If False, reject symlinked files

    Returns:
        Parsed YAML data as dict, or None on error
    """
    if not YAML_AVAILABLE:
        logger.debug("YAML library not available")
        return None

    # Check for symlinks if not allowed
    if not follow_symlinks and path.is_symlink():
        logger.warning(f"Symlink rejected: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            logger.debug(f"YAML file did not contain a dict: {path}")
            return None
        return data
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error in {path}: {e}")
        return None
    except PermissionError:
        logger.warning(f"Permission denied reading: {path}")
        return None
    except FileNotFoundError:
        logger.debug(f"File not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {path}: {type(e).__name__}: {e}")
        return None


def load_json_file(
    path: Path, follow_symlinks: bool = False
) -> dict[str, Any] | None:
    """Load a JSON file safely with error logging.

    Args:
        path: Path to the JSON file
        follow_symlinks: If False, reject symlinked files

    Returns:
        Parsed JSON data as dict, or None on error
    """
    # Check for symlinks if not allowed
    if not follow_symlinks and path.is_symlink():
        logger.warning(f"Symlink rejected: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error in {path}: {e}")
        return None
    except PermissionError:
        logger.warning(f"Permission denied reading: {path}")
        return None
    except FileNotFoundError:
        logger.debug(f"File not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {path}: {type(e).__name__}: {e}")
        return None


def parse_playbook(path: Path, pack_name: str) -> dict[str, Any] | None:
    """Parse a playbook YAML file."""
    data = load_yaml_file(path)
    if not data:
        return None

    name = data.get("name", "")
    description = data.get("description", "")

    # Extract commands used
    commands = []
    tasks = data.get("tasks", {})
    if isinstance(tasks, dict):
        for task in tasks.values():
            if isinstance(task, dict):
                task_def = task.get("task", {})
                script = task_def.get("script", "")
                if "|||" in str(script):
                    brand, cmd = script.split("|||", 1)
                    commands.append({"brand": brand.strip(), "command": cmd.strip()})

    # Extract subplaybooks
    subplaybooks = []
    if isinstance(tasks, dict):
        for task in tasks.values():
            if isinstance(task, dict):
                task_def = task.get("task", {})
                if pb_name := task_def.get("playbookName"):
                    subplaybooks.append({"name": pb_name})

    # Count task types
    task_counts = {}
    if isinstance(tasks, dict):
        for task in tasks.values():
            if isinstance(task, dict):
                task_type = task.get("type", "unknown")
                task_counts[task_type] = task_counts.get(task_type, 0) + 1

    return {
        "id": data.get("id", path.stem),
        "name": name,
        "description": description,
        "path": str(path),
        "pack": pack_name,
        "fromversion": data.get("fromversion", ""),
        "deprecated": bool(data.get("deprecated")),
        "intents": infer_intents(f"{name} {description}"),
        "commands": commands[:20],
        "subplaybooks": subplaybooks[:10],
        "task_counts": task_counts,
        "inputs": data.get("inputs", []),
        "outputs": data.get("outputs", []),
        "score": 10,  # Base score, can be enhanced
    }


def parse_script(path: Path, pack_name: str) -> dict[str, Any] | None:
    """Parse a script YAML file."""
    data = load_yaml_file(path)
    if not data:
        return None

    commonfields = data.get("commonfields", {})

    return {
        "id": commonfields.get("id") or data.get("name", path.stem),
        "name": data.get("name", ""),
        "description": data.get("comment", "") or data.get("description", ""),
        "path": str(path),
        "pack": pack_name,
        "fromversion": data.get("fromversion", ""),
        "deprecated": bool(data.get("deprecated")),
        "tags": data.get("tags", []),
        "args": data.get("args", []),
        "outputs": data.get("outputs", []),
        "type": data.get("type", ""),
        "subtype": data.get("subtype", ""),
        "intents": infer_intents(data.get("name", "") + " " + (data.get("comment", "") or "")),
        "score": 10,
    }


def parse_integration(path: Path, pack_name: str) -> dict[str, Any] | None:
    """Parse an integration YAML file."""
    data = load_yaml_file(path)
    if not data:
        return None

    commonfields = data.get("commonfields", {})
    config = data.get("configuration", [])
    script = data.get("script", {})
    commands = script.get("commands", []) if isinstance(script, dict) else []

    # Extract command names
    command_list = []
    for cmd in commands:
        if isinstance(cmd, dict):
            command_list.append({
                "name": cmd.get("name", ""),
                "description": cmd.get("description", ""),
            })

    return {
        "id": commonfields.get("id") or data.get("name", path.stem),
        "name": data.get("name", "") or data.get("display", ""),
        "description": data.get("description", ""),
        "path": str(path),
        "pack": pack_name,
        "fromversion": data.get("fromversion", ""),
        "deprecated": bool(data.get("deprecated")),
        "category": data.get("category", ""),
        "commands": command_list[:30],
        "configuration": [c.get("name", "") for c in config if isinstance(c, dict)][:20],
        "intents": infer_intents(data.get("name", "") + " " + data.get("description", "")),
        "score": 10,
    }


def parse_classifier(path: Path, pack_name: str) -> dict[str, Any] | None:
    """Parse a classifier JSON file."""
    data = load_json_file(path)
    if not data:
        return None

    return {
        "id": data.get("id", path.stem),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "path": str(path),
        "pack": pack_name,
        "type": data.get("type", ""),
        "brand": data.get("brandName", ""),
        "intents": ["classification"],
        "score": 10,
    }


def parse_mapper(path: Path, pack_name: str) -> dict[str, Any] | None:
    """Parse a mapper JSON file."""
    data = load_json_file(path)
    if not data:
        return None

    # Extract mapped fields
    mapping = data.get("mapping", {})
    fields = []
    if isinstance(mapping, dict):
        for incident_type, field_mapping in mapping.items():
            if isinstance(field_mapping, dict):
                internal_mapping = field_mapping.get("internalMapping", {})
                if isinstance(internal_mapping, dict):
                    fields.extend(list(internal_mapping.keys())[:10])

    return {
        "id": data.get("id", path.stem),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "path": str(path),
        "pack": pack_name,
        "type": data.get("type", ""),
        "direction": "incoming" if "incoming" in path.stem.lower() else "outgoing",
        "brand": data.get("brandName", ""),
        "fields": fields[:20],
        "intents": ["mapping"],
        "score": 10,
    }


def parse_xql_rule(
    path: Path, pack_name: str, rule_type: str, follow_symlinks: bool = False
) -> dict[str, Any] | None:
    """Parse an XQL parsing or modeling rule (.xif file).

    Args:
        path: Path to the XQL file
        pack_name: Name of the containing pack
        rule_type: Type of rule (parsing or modeling)
        follow_symlinks: If False, reject symlinked files

    Returns:
        Parsed rule data, or None on error
    """
    # Check for symlinks if not allowed
    if not follow_symlinks and path.is_symlink():
        logger.warning(f"Symlink rejected: {path}")
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except PermissionError:
        logger.warning(f"Permission denied reading: {path}")
        return None
    except FileNotFoundError:
        logger.debug(f"File not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {path}: {type(e).__name__}: {e}")
        return None

    # Extract rule name from content or filename
    name_match = re.search(r'\[RULE:\s*(\w+)\]', content)
    name = name_match.group(1) if name_match else path.stem

    # Extract filter/alter statements
    filters = re.findall(r'filter\s+(.+?)(?:\n|$)', content, re.IGNORECASE)
    alters = re.findall(r'alter\s+(.+?)(?:\n|$)', content, re.IGNORECASE)

    return {
        "id": f"{rule_type}:{path.stem}",
        "name": name,
        "description": f"XQL {rule_type} rule",
        "path": str(path),
        "pack": pack_name,
        "rule_type": rule_type,
        "content_preview": content[:500],
        "filters": filters[:5],
        "alters": alters[:5],
        "intents": ["xql", rule_type],
        "score": 15,  # Higher score for XQL examples
    }


def index_from_content_repo(
    content_root: Path,
    store: PatternStore,
    include_deprecated: bool = False,
    max_items: int = 0,
    follow_symlinks: bool = False,
) -> dict[str, int]:
    """
    Index content directly from a content repository.

    Args:
        content_root: Path to content repo root (contains Packs/)
        store: PatternStore instance
        include_deprecated: Include deprecated content
        max_items: Max items per type (0 = unlimited)
        follow_symlinks: If False, skip symlinked files and directories

    Returns:
        Counts by content type
    """
    packs_root = content_root / "Packs"
    if not packs_root.exists():
        raise ValueError(f"Packs directory not found at {packs_root}")

    counts = {
        "playbooks": 0,
        "scripts": 0,
        "integrations": 0,
        "classifiers": 0,
        "mappers": 0,
        "parsing_rules": 0,
        "modeling_rules": 0,
    }

    # Collect all items by type
    playbooks = []
    scripts = []
    integrations = []
    classifiers = []
    mappers = []
    xql_rules = []

    for pack_dir in packs_root.iterdir():
        if not pack_dir.is_dir():
            continue

        # Skip symlinked pack directories unless allowed
        if not follow_symlinks and pack_dir.is_symlink():
            logger.warning(f"Skipping symlinked pack directory: {pack_dir}")
            continue

        pack_name = pack_dir.name

        # Skip deprecated packs unless requested
        if not include_deprecated and "deprecated" in pack_name.lower():
            continue

        # Playbooks
        playbooks_dir = pack_dir / "Playbooks"
        if playbooks_dir.exists():
            for yml_path in playbooks_dir.glob("*.yml"):
                if max_items and len(playbooks) >= max_items:
                    break
                if item := parse_playbook(yml_path, pack_name):
                    if include_deprecated or not item.get("deprecated"):
                        playbooks.append(item)

        # Scripts
        scripts_dir = pack_dir / "Scripts"
        if scripts_dir.exists():
            for script_dir in scripts_dir.iterdir():
                if max_items and len(scripts) >= max_items:
                    break
                if script_dir.is_dir():
                    # Skip symlinked script directories
                    if not follow_symlinks and script_dir.is_symlink():
                        logger.debug(f"Skipping symlinked script directory: {script_dir}")
                        continue
                    yml_files = list(script_dir.glob("*.yml"))
                    for yml_path in yml_files:
                        if item := parse_script(yml_path, pack_name):
                            if include_deprecated or not item.get("deprecated"):
                                scripts.append(item)
                                break

        # Integrations
        integrations_dir = pack_dir / "Integrations"
        if integrations_dir.exists():
            for int_dir in integrations_dir.iterdir():
                if max_items and len(integrations) >= max_items:
                    break
                if int_dir.is_dir():
                    # Skip symlinked integration directories
                    if not follow_symlinks and int_dir.is_symlink():
                        logger.debug(f"Skipping symlinked integration directory: {int_dir}")
                        continue
                    yml_files = list(int_dir.glob("*.yml"))
                    for yml_path in yml_files:
                        if item := parse_integration(yml_path, pack_name):
                            if include_deprecated or not item.get("deprecated"):
                                integrations.append(item)
                                break

        # Classifiers
        classifiers_dir = pack_dir / "Classifiers"
        if classifiers_dir.exists():
            for json_path in classifiers_dir.glob("classifier-*.json"):
                if max_items and len(classifiers) >= max_items:
                    break
                if item := parse_classifier(json_path, pack_name):
                    classifiers.append(item)

            # Mappers (also in Classifiers dir)
            for json_path in classifiers_dir.glob("*mapper*.json"):
                if max_items and len(mappers) >= max_items:
                    break
                if item := parse_mapper(json_path, pack_name):
                    mappers.append(item)

        # Parsing Rules (XQL)
        parsing_dir = pack_dir / "ParsingRules"
        if parsing_dir.exists():
            for xif_path in parsing_dir.rglob("*.xif"):
                if max_items and len(xql_rules) >= max_items:
                    break
                if item := parse_xql_rule(
                    xif_path, pack_name, "parsing", follow_symlinks=follow_symlinks
                ):
                    xql_rules.append(item)

        # Modeling Rules (XQL)
        modeling_dir = pack_dir / "ModelingRules"
        if modeling_dir.exists():
            for xif_path in modeling_dir.rglob("*.xif"):
                if max_items and len(xql_rules) >= max_items:
                    break
                if item := parse_xql_rule(
                    xif_path, pack_name, "modeling", follow_symlinks=follow_symlinks
                ):
                    xql_rules.append(item)

    # Add items to store (pass content_root to store relative paths)
    counts["playbooks"] = store.add_items(playbooks, "playbook", content_root=content_root)
    counts["scripts"] = store.add_items(scripts, "script", content_root=content_root)
    counts["integrations"] = store.add_items(
        integrations, "integration", content_root=content_root
    )
    counts["classifiers"] = store.add_items(
        classifiers, "classifier", content_root=content_root
    )
    counts["mappers"] = store.add_items(mappers, "mapper", content_root=content_root)

    # XQL rules get special type
    parsing_rules = [r for r in xql_rules if r.get("rule_type") == "parsing"]
    modeling_rules = [r for r in xql_rules if r.get("rule_type") == "modeling"]
    counts["parsing_rules"] = store.add_items(
        parsing_rules, "parsing_rule", content_root=content_root
    )
    counts["modeling_rules"] = store.add_items(
        modeling_rules, "modeling_rule", content_root=content_root
    )

    return counts


def index_from_json(
    index_path: Path,
    store: PatternStore,
    include_deprecated: bool = False,
    min_score: int = 0,
) -> dict[str, int]:
    """
    Index content from a pre-built playbook_index.json file.

    Args:
        index_path: Path to playbook_index.json
        store: PatternStore instance
        include_deprecated: Include deprecated content
        min_score: Minimum quality score to include

    Returns:
        Counts by content type
    """
    with index_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    counts = {"playbooks": 0, "scripts": 0}

    # Filter and add playbooks
    playbooks = data.get("playbooks", [])
    if not include_deprecated:
        playbooks = [p for p in playbooks if not p.get("deprecated")]
    if min_score:
        playbooks = [p for p in playbooks if p.get("score", 0) >= min_score]

    counts["playbooks"] = store.add_items(playbooks, "playbook")

    # Filter and add scripts
    scripts = data.get("scripts", [])
    if not include_deprecated:
        scripts = [s for s in scripts if not s.get("deprecated")]

    counts["scripts"] = store.add_items(scripts, "script")

    return counts


def main() -> None:
    """CLI entry point for building the index."""
    parser = argparse.ArgumentParser(
        description="Build XSIAM pattern index for semantic search"
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to content repo root OR playbook_index.json",
        required=True,
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=f"Path to ChromaDB storage (default: {get_default_db_path()})",
    )
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        help="Include deprecated content",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum quality score (only for JSON index)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Max items per type (0 = unlimited)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing index before building",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symlinks when indexing (disabled by default for security)",
    )

    args = parser.parse_args()

    # Initialize store
    store = PatternStore(db_path=args.db_path)

    if args.clear:
        print("Clearing existing index...")
        store.clear()

    # Determine source type
    source = args.source.expanduser().resolve()

    if source.suffix == ".json":
        # Index from JSON file
        print(f"Indexing from JSON: {source}")
        counts = index_from_json(
            source,
            store,
            include_deprecated=args.include_deprecated,
            min_score=args.min_score,
        )
    elif (source / "Packs").exists():
        # Index from content repo
        print(f"Indexing from content repo: {source}")
        if args.follow_symlinks:
            print("WARNING: Following symlinks is enabled. This may pose security risks.")
        counts = index_from_content_repo(
            source,
            store,
            include_deprecated=args.include_deprecated,
            max_items=args.max_items,
            follow_symlinks=args.follow_symlinks,
        )
    else:
        print(f"Error: {source} is not a valid content repo or JSON index", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print("\nIndexing complete:")
    for content_type, count in counts.items():
        if count > 0:
            print(f"  {content_type}: {count}")

    stats = store.get_stats()
    print(f"\nTotal items in store: {stats['total_items']}")
    print(f"Database path: {stats['db_path']}")


if __name__ == "__main__":
    main()
