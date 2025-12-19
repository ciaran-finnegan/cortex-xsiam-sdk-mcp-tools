# Cortex XSIAM SDK MCP Tools

**Alpha** — APIs and tool schemas may change. Not suitable for production use.

An MCP server that exposes common `demisto-sdk` operations as tools, so an LLM (Cursor, Claude Code, Amazon Q, Codex CLI, etc.) can assist with Cortex XSIAM/XSOAR content development.

## Why this exists

- **Faster scaffolding**: create packs, integrations, and scripts in seconds
- **Higher quality**: run format/validate/lint as part of the conversation
- **Safer iteration**: favour local SDK workflows, and keep remote operations explicit

## Quickstart (local-first)

1) Install `demisto-sdk` (separate environment)  
2) Install this MCP server (venv)  
3) Configure credentials + your MCP client  
4) Ask your assistant to scaffold and validate content using the tools

See:
- Credentials: `docs/CREDENTIALS.md`
- MCP clients: `docs/MCP_CLIENTS.md`

## Example: typical XSIAM developer flows (LLM + MCP)

These are example prompts you can paste into your LLM chat after the MCP server is configured.

### Create a new pack and scaffold an integration

“Create a pack called `MyCompanyXSIAM` under `Packs/`, then scaffold an integration called `MyCompanyXSIAM` using the HelloWorld template. After that, run format + validate on the pack.”

### Validate and lint a pack before PR

“Run `validate_content` and `lint_content` on `Packs/MyCompanyXSIAM`. Summarise any failures and propose fixes.”

### Generate documentation for an integration

“Generate README documentation for `Packs/MyCompanyXSIAM/Integrations/MyCompanyXSIAM/MyCompanyXSIAM.yml` and write it next to the integration.”

### Read-only: discover and download one custom item from XSIAM

“Use `list_files` to list available custom content to download, then download a single small item into a temp pack for inspection (do not upload anything).”

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

See `docs/CREDENTIALS.md` for secure credential storage options including:

- 1Password CLI (recommended)
- macOS Keychain
- Windows Credential Manager
- AWS Secrets Manager
- GitHub Actions secrets

### 4. Configure Your MCP Client

See `docs/MCP_CLIENTS.md` for configuration instructions for:

- Cursor
- Cline
- Claude Code
- Amazon Q Developer
- OpenAI Codex CLI

## Security notes

- **Do not store credentials in git**. Prefer 1Password/Keychain/Secrets Manager and inject via environment variables.
- Treat **remote write operations** (`upload_content`, `run_command`, `run_playbook`) as production-impacting unless you are targeting a dedicated dev tenant.

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
| `list_files` | List custom content items available to download (read-only) |
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
