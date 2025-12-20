"""
MCP Server for demisto-sdk commands with pattern search (RAG).

Provides LLM coding assistants with:
- Direct access to demisto-sdk operations for XSIAM/XSOAR content development
- Semantic search over playbooks, scripts, integrations, and XQL rules

⚠️ ALPHA: Not suitable for production use.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Note: mcp package import - adjust based on actual MCP SDK implementation
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from .security import (
    check_insecure_flag,
    validate_name,
    validate_path_argument,
    validate_sdk_binary,
)

logger = logging.getLogger(__name__)

# RAG tools (optional - requires chromadb and sentence-transformers)
RAG_AVAILABLE = False
RAG_TOOLS: list[Tool] = []
RAG_HANDLERS: dict[str, Any] = {}

try:
    from .rag.tools import RAG_TOOLS, RAG_HANDLERS
    RAG_AVAILABLE = True
except ImportError:
    pass  # RAG dependencies not installed


server = Server("demisto-sdk")


def _resolve_demisto_sdk_content_root(explicit_cwd: str | None) -> Path:
    """
    demisto-sdk expects to run within a 'content' repo layout (at minimum, a Packs/ dir).
    When the current working directory isn't such a repo, we use a safe temp content root.
    """
    # 1) Honour explicit cwd if it already looks like a content repo.
    if explicit_cwd:
        p = Path(explicit_cwd).expanduser().resolve()
        if (p / "Packs").exists():
            return p

    # 2) Honour DEMISTO_SDK_CONTENT_PATH if set.
    if content_path := os.getenv("DEMISTO_SDK_CONTENT_PATH"):
        p = Path(content_path).expanduser().resolve()
        (p / "Packs").mkdir(parents=True, exist_ok=True)
        return p

    # 3) If current cwd is a content repo, use it.
    cwd = Path.cwd()
    if (cwd / "Packs").exists():
        return cwd

    # 4) Fallback: create a minimal content root under _tmp.
    fallback = cwd / "_tmp" / "demisto-sdk-content"
    (fallback / "Packs").mkdir(parents=True, exist_ok=True)
    return fallback


def run_sdk_command(args: list[str], cwd: str | None = None) -> dict[str, Any]:
    """Execute a demisto-sdk command and return results.

    Security: The SDK binary is validated against an allowlist to prevent
    arbitrary code execution via the DEMISTO_SDK_BIN environment variable.
    """
    try:
        content_root = _resolve_demisto_sdk_content_root(cwd)
        env = os.environ.copy()
        env.setdefault("DEMISTO_SDK_CONTENT_PATH", str(content_root))

        # Validate the SDK binary
        sdk_bin_input = env.get("DEMISTO_SDK_BIN", "demisto-sdk")
        sdk_bin = validate_sdk_binary(sdk_bin_input)

        if sdk_bin is None:
            logger.warning(f"Invalid SDK binary rejected: {sdk_bin_input}")
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Invalid or untrusted SDK binary: {sdk_bin_input}. "
                "Only 'demisto-sdk' is allowed.",
                "returncode": -1,
            }

        result = subprocess.run(
            [sdk_bin] + args,
            capture_output=True,
            text=True,
            cwd=str(content_root),
            env=env,
            timeout=300,  # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 300 seconds",
            "returncode": -1,
        }
    except Exception as e:
        logger.error(f"SDK command failed: {type(e).__name__}: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


# Tool definitions
TOOLS = [
    Tool(
        name="init_pack",
        description="Create a new XSIAM content pack with proper structure",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the pack to create"},
                "output_dir": {"type": "string", "description": "Output directory (defaults to Packs/)"}
            },
            "required": ["name"]
        }
    ),
    Tool(
        name="init_integration",
        description="Scaffold a new integration within a pack",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the integration"},
                "pack": {"type": "string", "description": "Target pack name"},
                "template": {"type": "string", "description": "Template type: HelloWorld, FeedHelloWorld, HelloIAMWorld"}
            },
            "required": ["name", "pack"]
        }
    ),
    Tool(
        name="init_script",
        description="Scaffold a new script within a pack",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the script"},
                "pack": {"type": "string", "description": "Target pack name"}
            },
            "required": ["name", "pack"]
        }
    ),
    Tool(
        name="format_content",
        description="Standardise YAML and Python formatting for content",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content file or directory"},
                "assume_yes": {"type": "boolean", "description": "Auto-accept changes", "default": True}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="validate_content",
        description="Check content validity against XSIAM standards",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content file or directory"},
                "use_git": {"type": "boolean", "description": "Validate only changed files"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="lint_content",
        description="Run XSOAR linter code quality checks on content",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content file or directory"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="generate_docs",
        description="Generate README documentation for content",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content YML file"},
                "output_path": {"type": "string", "description": "Output path for README"},
                "force": {"type": "boolean", "description": "Overwrite existing documentation"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="upload_content",
        description="Deploy content to XSIAM/XSOAR instance",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content to upload"},
                "insecure": {
                    "type": "boolean",
                    "description": "Skip SSL verification (DANGEROUS: exposes credentials to MITM attacks)",
                },
                "acknowledge_insecure_risk": {
                    "type": "boolean",
                    "description": "Required if insecure=true. Confirms you accept the security risk.",
                },
            },
            "required": ["input_path"],
        },
    ),
    Tool(
        name="download_content",
        description="Download content from XSIAM/XSOAR instance",
        inputSchema={
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Output directory for downloaded content"},
                "input_path": {"type": "string", "description": "Specific content to download"},
                "all_content": {"type": "boolean", "description": "Download all custom content"}
            },
            "required": ["output_path"]
        }
    ),
    Tool(
        name="list_files",
        description="List all custom content items available to download (demisto-sdk download --list-files)",
        inputSchema={
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional output path (demisto-sdk -o). Listing does not write content.",
                },
                "insecure": {
                    "type": "boolean",
                    "description": "Skip SSL verification (DANGEROUS: exposes credentials to MITM attacks)",
                },
                "acknowledge_insecure_risk": {
                    "type": "boolean",
                    "description": "Required if insecure=true. Confirms you accept the security risk.",
                },
            },
        },
    ),
    Tool(
        name="find_dependencies",
        description="Analyse and list pack dependencies",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to pack"},
                "update_pack_metadata": {"type": "boolean", "description": "Update pack_metadata.json"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="update_release_notes",
        description="Update or create release notes for version changes",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to pack"},
                "version": {"type": "string", "description": "Version type: major, minor, revision"},
                "text": {"type": "string", "description": "Release notes text"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="zip_packs",
        description="Create distributable pack archives",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to pack(s) to zip"},
                "output_path": {"type": "string", "description": "Output directory for zip files"}
            },
            "required": ["input_path", "output_path"]
        }
    ),
    Tool(
        name="generate_unit_tests",
        description="Generate unit test scaffolds for integrations/scripts",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to integration/script"},
                "output_path": {"type": "string", "description": "Output path for test file"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="generate_test_playbook",
        description="Generate a test playbook for an integration",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to integration YML"},
                "output_path": {"type": "string", "description": "Output path for test playbook"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="generate_outputs",
        description="Generate context outputs from JSON response",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to integration YML"},
                "command": {"type": "string", "description": "Command name to generate outputs for"},
                "json_path": {"type": "string", "description": "Path to JSON response file"}
            },
            "required": ["input_path", "command"]
        }
    ),
    Tool(
        name="run_command",
        description="Execute a command on XSIAM/XSOAR instance",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "args": {"type": "string", "description": "Command arguments as JSON string"}
            },
            "required": ["command"]
        }
    ),
    Tool(
        name="run_playbook",
        description="Run a playbook on XSIAM/XSOAR instance",
        inputSchema={
            "type": "object",
            "properties": {
                "playbook_id": {"type": "string", "description": "ID of playbook to run"},
                "wait": {"type": "boolean", "description": "Wait for playbook completion"}
            },
            "required": ["playbook_id"]
        }
    ),
    Tool(
        name="openapi_codegen",
        description="Generate integration from OpenAPI specification",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to OpenAPI spec file"},
                "output_path": {"type": "string", "description": "Output directory"},
                "name": {"type": "string", "description": "Integration name"}
            },
            "required": ["input_path"]
        }
    ),
    Tool(
        name="postman_codegen",
        description="Generate integration from Postman collection",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to Postman collection JSON"},
                "output_path": {"type": "string", "description": "Output directory"},
                "name": {"type": "string", "description": "Integration name"}
            },
            "required": ["input_path"]
        }
    ),
]


@server.list_tools()  # type: ignore[misc]
async def list_tools() -> list[Tool]:
    """Return available tools."""
    all_tools = TOOLS.copy()
    if RAG_AVAILABLE and RAG_TOOLS:
        all_tools.extend(RAG_TOOLS)
    return all_tools


@server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool and return results."""

    # SDK tool handlers
    sdk_handlers = {
        "init_pack": handle_init_pack,
        "init_integration": handle_init_integration,
        "init_script": handle_init_script,
        "format_content": handle_format_content,
        "validate_content": handle_validate_content,
        "lint_content": handle_lint_content,
        "generate_docs": handle_generate_docs,
        "upload_content": handle_upload_content,
        "download_content": handle_download_content,
        "list_files": handle_list_files,
        "find_dependencies": handle_find_dependencies,
        "update_release_notes": handle_update_release_notes,
        "zip_packs": handle_zip_packs,
        "generate_unit_tests": handle_generate_unit_tests,
        "generate_test_playbook": handle_generate_test_playbook,
        "generate_outputs": handle_generate_outputs,
        "run_command": handle_run_command,
        "run_playbook": handle_run_playbook,
        "openapi_codegen": handle_openapi_codegen,
        "postman_codegen": handle_postman_codegen,
    }

    # Check SDK handlers first
    handler = sdk_handlers.get(name)

    # Check RAG handlers if not found
    if not handler and RAG_AVAILABLE:
        handler = RAG_HANDLERS.get(name)

    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    result = await handler(arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def _error_result(message: str) -> dict[str, Any]:
    """Create a standardized error result."""
    return {
        "success": False,
        "stdout": "",
        "stderr": message,
        "returncode": -1,
    }


async def handle_init_pack(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_pack command."""
    name = validate_name(args.get("name", ""))
    if not name:
        return _error_result(
            "Invalid pack name. Use only alphanumeric characters, underscores, and hyphens."
        )

    cmd = ["init", "--pack", "-n", name]
    if output_dir := args.get("output_dir"):
        validated_dir = validate_path_argument(output_dir)
        if not validated_dir:
            return _error_result("Invalid output directory path.")
        cmd.extend(["-o", validated_dir])
    return run_sdk_command(cmd)


async def handle_init_integration(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_integration command."""
    name = validate_name(args.get("name", ""))
    if not name:
        return _error_result(
            "Invalid integration name. Use only alphanumeric characters, underscores, and hyphens."
        )

    pack = validate_name(args.get("pack", ""))
    if not pack:
        return _error_result(
            "Invalid pack name. Use only alphanumeric characters, underscores, and hyphens."
        )

    cmd = ["init", "--integration", "-n", name, "-p", pack]
    if template := args.get("template"):
        validated_template = validate_name(template)
        if not validated_template:
            return _error_result("Invalid template name.")
        cmd.extend(["--template", validated_template])
    return run_sdk_command(cmd)


async def handle_init_script(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_script command."""
    name = validate_name(args.get("name", ""))
    if not name:
        return _error_result(
            "Invalid script name. Use only alphanumeric characters, underscores, and hyphens."
        )

    pack = validate_name(args.get("pack", ""))
    if not pack:
        return _error_result(
            "Invalid pack name. Use only alphanumeric characters, underscores, and hyphens."
        )

    cmd = ["init", "--script", "-n", name, "-p", pack]
    return run_sdk_command(cmd)


async def handle_format_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle format_content command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["format", "-i", input_path]
    if args.get("assume_yes", True):
        cmd.append("-y")
    return run_sdk_command(cmd)


async def handle_validate_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle validate_content command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["validate", "-i", input_path]
    if args.get("use_git"):
        cmd.append("-g")
    return run_sdk_command(cmd)


async def handle_lint_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle lint_content command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["xsoar-lint", input_path]
    return run_sdk_command(cmd)


async def handle_generate_docs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_docs command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["generate-docs", "-i", input_path]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    if args.get("force"):
        cmd.append("-f")
    return run_sdk_command(cmd)


async def handle_upload_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle upload_content command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    # Check insecure flag with acknowledgment requirement
    can_proceed, error_msg = check_insecure_flag(
        insecure=args.get("insecure", False),
        acknowledged=args.get("acknowledge_insecure_risk", False),
    )
    if not can_proceed:
        return _error_result(error_msg or "Insecure flag requires acknowledgment.")

    cmd = ["upload", "-i", input_path]
    if args.get("insecure"):
        cmd.append("--insecure")
    return run_sdk_command(cmd)


async def handle_download_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle download_content command."""
    output_path = validate_path_argument(args.get("output_path", ""))
    if not output_path:
        return _error_result("Invalid output path.")

    cmd = ["download", "-o", output_path]
    if input_path := args.get("input_path"):
        validated_input = validate_path_argument(input_path)
        if not validated_input:
            return _error_result("Invalid input path.")
        cmd.extend(["-i", validated_input])
    if args.get("all_content"):
        cmd.append("-a")
    return run_sdk_command(cmd)


async def handle_list_files(args: dict[str, Any]) -> dict[str, Any]:
    """Handle list_files command (read-only)."""
    # Check insecure flag with acknowledgment requirement
    can_proceed, error_msg = check_insecure_flag(
        insecure=args.get("insecure", False),
        acknowledged=args.get("acknowledge_insecure_risk", False),
    )
    if not can_proceed:
        return _error_result(error_msg or "Insecure flag requires acknowledgment.")

    cmd = ["download", "-lf"]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    if args.get("insecure"):
        cmd.append("--insecure")
    return run_sdk_command(cmd)


async def handle_find_dependencies(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_dependencies command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["find-dependencies", "-i", input_path]
    if args.get("update_pack_metadata"):
        cmd.append("--update-pack-metadata")
    return run_sdk_command(cmd)


async def handle_update_release_notes(args: dict[str, Any]) -> dict[str, Any]:
    """Handle update_release_notes command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["update-release-notes", "-i", input_path]
    if version := args.get("version"):
        # Validate version is a safe value
        if version not in ("major", "minor", "revision"):
            return _error_result("Invalid version. Must be: major, minor, or revision.")
        cmd.extend(["-v", version])
    if text := args.get("text"):
        # Text is passed as-is to demisto-sdk, which handles it safely
        cmd.extend(["--text", text])
    return run_sdk_command(cmd)


async def handle_zip_packs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle zip_packs command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    output_path = validate_path_argument(args.get("output_path", ""))
    if not output_path:
        return _error_result("Invalid output path.")

    cmd = ["zip-packs", "-i", input_path, "-o", output_path]
    return run_sdk_command(cmd)


async def handle_generate_unit_tests(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_unit_tests command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["generate-unit-tests", "-i", input_path]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    return run_sdk_command(cmd)


async def handle_generate_test_playbook(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_test_playbook command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["generate-test-playbook", "-i", input_path]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    return run_sdk_command(cmd)


async def handle_generate_outputs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_outputs command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    # Command name should be validated as a safe name
    command = validate_name(args.get("command", ""))
    if not command:
        return _error_result(
            "Invalid command name. Use only alphanumeric characters, underscores, and hyphens."
        )

    cmd = ["generate-outputs", "-i", input_path, "-c", command]
    if json_path := args.get("json_path"):
        validated_json = validate_path_argument(json_path)
        if not validated_json:
            return _error_result("Invalid JSON path.")
        cmd.extend(["-j", validated_json])
    return run_sdk_command(cmd)


async def handle_run_command(args: dict[str, Any]) -> dict[str, Any]:
    """Handle run_command command."""
    # Command is passed to demisto-sdk which handles it
    # We do basic validation to prevent obvious issues
    command = args.get("command", "")
    if not command:
        return _error_result("Command is required.")

    cmd = ["run", "-q", command]
    if cmd_args := args.get("args"):
        # Args are passed as JSON string to demisto-sdk
        cmd.extend(["--args", cmd_args])
    return run_sdk_command(cmd)


async def handle_run_playbook(args: dict[str, Any]) -> dict[str, Any]:
    """Handle run_playbook command."""
    playbook_id = args.get("playbook_id", "")
    if not playbook_id:
        return _error_result("Playbook ID is required.")

    cmd = ["run-playbook", "-p", playbook_id]
    if args.get("wait"):
        cmd.append("--wait")
    return run_sdk_command(cmd)


async def handle_openapi_codegen(args: dict[str, Any]) -> dict[str, Any]:
    """Handle openapi_codegen command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["openapi-codegen", "-i", input_path]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    if name := args.get("name"):
        validated_name = validate_name(name)
        if not validated_name:
            return _error_result(
                "Invalid name. Use only alphanumeric characters, underscores, and hyphens."
            )
        cmd.extend(["-n", validated_name])
    return run_sdk_command(cmd)


async def handle_postman_codegen(args: dict[str, Any]) -> dict[str, Any]:
    """Handle postman_codegen command."""
    input_path = validate_path_argument(args.get("input_path", ""))
    if not input_path:
        return _error_result("Invalid input path.")

    cmd = ["postman-codegen", "-i", input_path]
    if output_path := args.get("output_path"):
        validated_output = validate_path_argument(output_path)
        if not validated_output:
            return _error_result("Invalid output path.")
        cmd.extend(["-o", validated_output])
    if name := args.get("name"):
        validated_name = validate_name(name)
        if not validated_name:
            return _error_result(
                "Invalid name. Use only alphanumeric characters, underscores, and hyphens."
            )
        cmd.extend(["-n", validated_name])
    return run_sdk_command(cmd)


def main() -> None:
    """Run the MCP server."""
    async def run_stdio_async() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_stdio_async())


if __name__ == "__main__":
    main()
