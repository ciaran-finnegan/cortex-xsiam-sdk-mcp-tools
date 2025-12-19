# Cortex XSIAM SDK MCP Tools

**Alpha** - Not suitable for production use. APIs and tool schemas may change.

Model Context Protocol (MCP) server providing demisto-sdk commands as tools for LLM coding assistants.

## Overview

Wraps [demisto-sdk](https://github.com/demisto/demisto-sdk) commands, enabling LLM assistants (Cursor, Cline, Claude Code) to invoke SDK operations for XSIAM/XSOAR content development.

## Installation

```bash
git clone https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools.git
cd cortex-xsiam-sdk-mcp-tools
pip install -e .
```

## Configuration

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "demisto-sdk": {
      "command": "python",
      "args": ["-m", "mcp_demisto_sdk"],
      "cwd": "/path/to/cortex-xsiam-sdk-mcp-tools"
    }
  }
}
```

### Cline

Add to Cline MCP settings:

```json
{
  "demisto-sdk": {
    "command": "python",
    "args": ["-m", "mcp_demisto_sdk"]
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `init_pack` | Create content pack structure |
| `init_integration` | Scaffold integration |
| `init_script` | Scaffold script |
| `format_content` | Standardise YAML/Python formatting |
| `validate_content` | Check content validity |
| `lint_content` | Run code quality checks |
| `generate_docs` | Create README documentation |
| `generate_unit_tests` | Generate test scaffolds |
| `generate_test_playbook` | Create test playbook |
| `generate_outputs` | Generate context paths from JSON |
| `upload_content` | Deploy to XSIAM/XSOAR |
| `download_content` | Sync content from platform |
| `run_command` | Execute commands remotely |
| `run_playbook` | Run playbooks remotely |
| `find_dependencies` | Analyse pack dependencies |
| `update_release_notes` | Version management |
| `zip_packs` | Create distributable archives |
| `openapi_codegen` | Generate from OpenAPI spec |
| `postman_codegen` | Generate from Postman collection |

## Prerequisites

- Python 3.10+
- demisto-sdk 1.38+
- MCP-compatible LLM assistant

## Development

```bash
pip install -e ".[dev]"
pytest
mypy mcp_demisto_sdk
```

## Related Repositories

- [demisto-sdk](https://github.com/demisto/demisto-sdk) - Official SDK
- [demisto/content](https://github.com/demisto/content) - Official content library
- [cortex-xsiam-content-development-template](https://github.com/ciaran-finnegan/cortex-xsiam-content-development-template) - Development template
- [MCP Specification](https://modelcontextprotocol.io/)

## Licence

MIT - See [LICENSE](LICENSE).

---

Community project, not officially supported by Palo Alto Networks.
