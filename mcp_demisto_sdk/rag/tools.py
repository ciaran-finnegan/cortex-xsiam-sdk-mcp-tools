"""
MCP tool definitions and handlers for RAG pattern search.
"""

import json
from typing import Any

try:
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Tool = None
    TextContent = None

from .search import PatternSearch
from .store import PatternStore

# Lazy-initialized search instance
_search_instance: PatternSearch | None = None


def get_search() -> PatternSearch:
    """Get or create the pattern search instance."""
    global _search_instance
    if _search_instance is None:
        try:
            _search_instance = PatternSearch()
        except Exception as e:
            raise RuntimeError(
                f"Pattern search not available. "
                f"Run 'xsiam-build-index --source /path/to/content' first. "
                f"Error: {e}"
            )
    return _search_instance


# RAG Tool Definitions
RAG_TOOLS = [
    Tool(
        name="search_patterns",
        description=(
            "Search for XSIAM content patterns using natural language. "
            "Returns playbooks, scripts, integrations, XQL rules, classifiers, and mappers "
            "that match your description. Use this to find examples and patterns for content development."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of what you're looking for",
                },
                "content_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Filter by content types: playbook, script, integration, "
                        "classifier, mapper, parsing_rule, modeling_rule"
                    ),
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full file content in results",
                    "default": False,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="find_similar_playbooks",
        description=(
            "Find playbooks similar to a description. Use this when you need to create "
            "a new playbook and want to see how similar ones are structured. "
            "Returns matching playbooks with their task patterns, commands used, and structure."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the playbook you want to create",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full YAML content",
                    "default": False,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="find_similar_scripts",
        description=(
            "Find automation scripts similar to a description. Use this when you need "
            "to create a new script and want to see how similar functionality is implemented. "
            "Returns matching scripts with their arguments, outputs, and implementation patterns."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the script functionality you need",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full Python/YAML content",
                    "default": False,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="find_integration_patterns",
        description=(
            "Find integration patterns matching a description. Use this when building "
            "a new integration to see how similar APIs are handled. "
            "Returns matching integrations with their commands, configuration, and patterns."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the integration type (e.g., 'REST API with OAuth2')",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full integration content",
                    "default": False,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="find_xql_examples",
        description=(
            "Find XQL parsing and modeling rule examples. Use this when writing XQL queries "
            "to see correct syntax and patterns. Returns matching rules with their full XQL content."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of what the XQL should do",
                },
                "rule_type": {
                    "type": "string",
                    "enum": ["parsing", "modeling"],
                    "description": "Filter by rule type (omit for both)",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="find_classifier_examples",
        description=(
            "Find classifier examples for event classification. Use this when you need "
            "to classify incidents or events and want to see how similar classifiers work."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of classification needs",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full JSON content",
                    "default": False,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="find_mapper_examples",
        description=(
            "Find field mapper examples. Use this when you need to map fields "
            "between external systems and XSIAM incidents."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of mapping needs",
                },
                "direction": {
                    "type": "string",
                    "enum": ["incoming", "outgoing"],
                    "description": "Filter by mapper direction",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full JSON content",
                    "default": False,
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="get_pattern_index_stats",
        description=(
            "Get statistics about the pattern index. Shows how many playbooks, scripts, "
            "integrations, and other content types are indexed for search."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
] if MCP_AVAILABLE else []


# Tool Handlers
async def handle_search_patterns(args: dict[str, Any]) -> dict[str, Any]:
    """Handle search_patterns tool call."""
    try:
        search = get_search()
        return search.search_patterns(
            query=args["query"],
            n_results=args.get("n_results", 5),
            content_types=args.get("content_types"),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_similar_playbooks(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_similar_playbooks tool call."""
    try:
        search = get_search()
        return search.find_similar_playbooks(
            description=args["description"],
            n_results=args.get("n_results", 5),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_similar_scripts(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_similar_scripts tool call."""
    try:
        search = get_search()
        return search.find_similar_scripts(
            description=args["description"],
            n_results=args.get("n_results", 5),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_integration_patterns(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_integration_patterns tool call."""
    try:
        search = get_search()
        return search.find_integration_patterns(
            description=args["description"],
            n_results=args.get("n_results", 5),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_xql_examples(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_xql_examples tool call."""
    try:
        search = get_search()
        return search.find_xql_examples(
            description=args["description"],
            rule_type=args.get("rule_type"),
            n_results=args.get("n_results", 5),
            include_content=True,  # Always include XQL content
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_classifier_examples(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_classifier_examples tool call."""
    try:
        search = get_search()
        return search.find_classifier_examples(
            description=args["description"],
            n_results=args.get("n_results", 5),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_find_mapper_examples(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_mapper_examples tool call."""
    try:
        search = get_search()
        return search.find_mapper_examples(
            description=args["description"],
            direction=args.get("direction"),
            n_results=args.get("n_results", 5),
            include_content=args.get("include_content", False),
        )
    except Exception as e:
        return {"error": str(e)}


async def handle_get_pattern_index_stats(args: dict[str, Any]) -> dict[str, Any]:
    """Handle get_pattern_index_stats tool call."""
    try:
        search = get_search()
        return search.get_index_stats()
    except Exception as e:
        return {"error": str(e)}


# Handler registry
RAG_HANDLERS = {
    "search_patterns": handle_search_patterns,
    "find_similar_playbooks": handle_find_similar_playbooks,
    "find_similar_scripts": handle_find_similar_scripts,
    "find_integration_patterns": handle_find_integration_patterns,
    "find_xql_examples": handle_find_xql_examples,
    "find_classifier_examples": handle_find_classifier_examples,
    "find_mapper_examples": handle_find_mapper_examples,
    "get_pattern_index_stats": handle_get_pattern_index_stats,
}
