# Cortex XSIAM SDK MCP Tools

[![Demisto SDK](https://img.shields.io/badge/demisto--sdk-1.38+-blue)](https://github.com/demisto/demisto-sdk)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools)

> ⚠️ **Alpha Release**: This MCP server is in early development and not suitable for production use. APIs and tool schemas may change without notice.

Model Context Protocol (MCP) server providing demisto-sdk commands as tools for LLM coding assistants.

## Overview

This MCP server wraps [demisto-sdk](https://github.com/demisto/demisto-sdk) commands, enabling LLM assistants (Cursor, Cline, Claude Code) to directly invoke SDK operations for XSIAM/XSOAR content development.

## Installation

```bash
# Clone the repository
git clone https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools.git
cd cortex-xsiam-sdk-mcp-tools

# Install dependencies
pip install -e .
```

## Configuration

### Cursor

Add to your `.cursor/mcp.json`:

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

Add to your Cline MCP settings:

```json
{
  "demisto-sdk": {
    "command": "python",
    "args": ["-m", "mcp_demisto_sdk"]
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `init_pack` | Create new content pack structure |
| `init_integration` | Scaffold new integration |
| `init_script` | Scaffold new script |
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
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy mcp_demisto_sdk
```

## Related Repositories

- [demisto-sdk](https://github.com/demisto/demisto-sdk) - Official Palo Alto Networks SDK
- [demisto/content](https://github.com/demisto/content) - Official XSIAM/XSOAR content library
- [cortex-xsiam-content-development-template](https://github.com/ciaran-finnegan/cortex-xsiam-content-development-template) - Development template with LLM configurations
- [MCP Specification](https://modelcontextprotocol.io/) - Model Context Protocol documentation

## Licence

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

---

**Disclaimer**: This is a community project and is not officially supported by Palo Alto Networks.

