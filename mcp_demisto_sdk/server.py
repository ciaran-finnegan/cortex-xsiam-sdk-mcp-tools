"""
MCP Server for demisto-sdk commands.

Provides LLM coding assistants with direct access to demisto-sdk operations
for XSIAM/XSOAR content development.

⚠️ ALPHA: Not suitable for production use.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any

# Note: mcp package import - adjust based on actual MCP SDK implementation
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)


server = Server("demisto-sdk")


def run_sdk_command(args: list[str], cwd: str | None = None) -> dict[str, Any]:
    """Execute a demisto-sdk command and return results."""
    try:
        result = subprocess.run(
            ["demisto-sdk"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300  # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 300 seconds",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
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
        description="Run code quality checks (pylint, mypy, pytest)",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to content file or directory"},
                "docker": {"type": "boolean", "description": "Run in Docker container"},
                "test": {"type": "boolean", "description": "Run unit tests"}
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
                "insecure": {"type": "boolean", "description": "Skip SSL verification"}
            },
            "required": ["input_path"]
        }
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


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool and return results."""
    
    handlers = {
        "init_pack": handle_init_pack,
        "init_integration": handle_init_integration,
        "init_script": handle_init_script,
        "format_content": handle_format_content,
        "validate_content": handle_validate_content,
        "lint_content": handle_lint_content,
        "generate_docs": handle_generate_docs,
        "upload_content": handle_upload_content,
        "download_content": handle_download_content,
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
    
    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    result = await handler(arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_init_pack(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_pack command."""
    cmd = ["init", "--pack", "-n", args["name"]]
    if output_dir := args.get("output_dir"):
        cmd.extend(["-o", output_dir])
    return run_sdk_command(cmd)


async def handle_init_integration(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_integration command."""
    cmd = ["init", "--integration", "-n", args["name"], "-p", args["pack"]]
    if template := args.get("template"):
        cmd.extend(["--template", template])
    return run_sdk_command(cmd)


async def handle_init_script(args: dict[str, Any]) -> dict[str, Any]:
    """Handle init_script command."""
    cmd = ["init", "--script", "-n", args["name"], "-p", args["pack"]]
    return run_sdk_command(cmd)


async def handle_format_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle format_content command."""
    cmd = ["format", "-i", args["input_path"]]
    if args.get("assume_yes", True):
        cmd.append("-y")
    return run_sdk_command(cmd)


async def handle_validate_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle validate_content command."""
    cmd = ["validate", "-i", args["input_path"]]
    if args.get("use_git"):
        cmd.append("-g")
    return run_sdk_command(cmd)


async def handle_lint_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle lint_content command."""
    cmd = ["lint", "-i", args["input_path"]]
    if args.get("docker"):
        cmd.append("-d")
    if args.get("test"):
        cmd.append("-t")
    return run_sdk_command(cmd)


async def handle_generate_docs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_docs command."""
    cmd = ["generate-docs", "-i", args["input_path"]]
    if output_path := args.get("output_path"):
        cmd.extend(["-o", output_path])
    if args.get("force"):
        cmd.append("-f")
    return run_sdk_command(cmd)


async def handle_upload_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle upload_content command."""
    cmd = ["upload", "-i", args["input_path"]]
    if args.get("insecure"):
        cmd.append("--insecure")
    return run_sdk_command(cmd)


async def handle_download_content(args: dict[str, Any]) -> dict[str, Any]:
    """Handle download_content command."""
    cmd = ["download", "-o", args["output_path"]]
    if input_path := args.get("input_path"):
        cmd.extend(["-i", input_path])
    if args.get("all_content"):
        cmd.append("-a")
    return run_sdk_command(cmd)


async def handle_find_dependencies(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_dependencies command."""
    cmd = ["find-dependencies", "-i", args["input_path"]]
    if args.get("update_pack_metadata"):
        cmd.append("--update-pack-metadata")
    return run_sdk_command(cmd)


async def handle_update_release_notes(args: dict[str, Any]) -> dict[str, Any]:
    """Handle update_release_notes command."""
    cmd = ["update-release-notes", "-i", args["input_path"]]
    if version := args.get("version"):
        cmd.extend(["-v", version])
    if text := args.get("text"):
        cmd.extend(["--text", text])
    return run_sdk_command(cmd)


async def handle_zip_packs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle zip_packs command."""
    cmd = ["zip-packs", "-i", args["input_path"], "-o", args["output_path"]]
    return run_sdk_command(cmd)


async def handle_generate_unit_tests(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_unit_tests command."""
    cmd = ["generate-unit-tests", "-i", args["input_path"]]
    if output_path := args.get("output_path"):
        cmd.extend(["-o", output_path])
    return run_sdk_command(cmd)


async def handle_generate_test_playbook(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_test_playbook command."""
    cmd = ["generate-test-playbook", "-i", args["input_path"]]
    if output_path := args.get("output_path"):
        cmd.extend(["-o", output_path])
    return run_sdk_command(cmd)


async def handle_generate_outputs(args: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_outputs command."""
    cmd = ["generate-outputs", "-i", args["input_path"], "-c", args["command"]]
    if json_path := args.get("json_path"):
        cmd.extend(["-j", json_path])
    return run_sdk_command(cmd)


async def handle_run_command(args: dict[str, Any]) -> dict[str, Any]:
    """Handle run_command command."""
    cmd = ["run", "-q", args["command"]]
    if cmd_args := args.get("args"):
        cmd.extend(["--args", cmd_args])
    return run_sdk_command(cmd)


async def handle_run_playbook(args: dict[str, Any]) -> dict[str, Any]:
    """Handle run_playbook command."""
    cmd = ["run-playbook", "-p", args["playbook_id"]]
    if args.get("wait"):
        cmd.append("--wait")
    return run_sdk_command(cmd)


async def handle_openapi_codegen(args: dict[str, Any]) -> dict[str, Any]:
    """Handle openapi_codegen command."""
    cmd = ["openapi-codegen", "-i", args["input_path"]]
    if output_path := args.get("output_path"):
        cmd.extend(["-o", output_path])
    if name := args.get("name"):
        cmd.extend(["-n", name])
    return run_sdk_command(cmd)


async def handle_postman_codegen(args: dict[str, Any]) -> dict[str, Any]:
    """Handle postman_codegen command."""
    cmd = ["postman-codegen", "-i", args["input_path"]]
    if output_path := args.get("output_path"):
        cmd.extend(["-o", output_path])
    if name := args.get("name"):
        cmd.extend(["-n", name])
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

