# Cortex XSIAM SDK MCP Tools

**Alpha** - Not suitable for production use. APIs and tool schemas may change.

Model Context Protocol (MCP) server providing demisto-sdk commands as tools for LLM coding assistants.

## Overview

Wraps [demisto-sdk](https://github.com/demisto/demisto-sdk) commands, enabling LLM assistants to invoke SDK operations for XSIAM/XSOAR content development.

## Prerequisites

- Python 3.10+
- [demisto-sdk](https://github.com/demisto/demisto-sdk) 1.38+
- MCP-compatible LLM assistant

## Installation

### 1. Install demisto-sdk

The `demisto-sdk` must be installed separately (it has conflicting pydantic requirements with the MCP SDK).

**Using pipx (recommended):**

```bash
pipx install demisto-sdk
```

**Using pip in a separate environment:**

```bash
python3.11 -m venv ~/.demisto-sdk-venv
~/.demisto-sdk-venv/bin/pip install demisto-sdk
export PATH="$HOME/.demisto-sdk-venv/bin:$PATH"  # Add to ~/.zshrc
```

Verify installation:

```bash
demisto-sdk --version
```

### 2. Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools.git
cd cortex-xsiam-sdk-mcp-tools

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .
```

### 3. Configure Credentials

See [docs/CREDENTIALS.md](docs/CREDENTIALS.md) for secure credential storage options including:

- 1Password CLI (recommended)
- macOS Keychain
- Windows Credential Manager
- AWS Secrets Manager
- GitHub Actions secrets

### 4. Configure Your MCP Client

See [docs/MCP_CLIENTS.md](docs/MCP_CLIENTS.md) for configuration instructions for:

- Cursor
- Cline
- Claude Code
- Amazon Q Developer
- OpenAI Codex CLI

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

## Development

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check mcp_demisto_sdk
```

## Related Resources

- [demisto-sdk](https://github.com/demisto/demisto-sdk) - Official SDK
- [demisto/content](https://github.com/demisto/content) - Official content library
- [MCP Specification](https://modelcontextprotocol.io/)

## Licence

MIT - See [LICENSE](LICENSE).

---

Community project, not officially supported by Palo Alto Networks.
