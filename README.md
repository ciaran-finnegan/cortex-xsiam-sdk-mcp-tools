# Cortex XSIAM SDK MCP Tools

**Alpha** — APIs and tool schemas may change. Not suitable for production use.

An MCP server that exposes common `demisto-sdk` operations as tools, so an LLM (Cursor, Claude Code, Amazon Q, Codex CLI, etc.) can assist with Cortex XSIAM/XSOAR content development.

## Why this exists

- **Faster scaffolding**: create packs, integrations, and scripts quickly using an LLM coding assistant
- **Higher quality**: run format/validate/lint using natural language

## Quickstart

1) Install `demisto-sdk` (separate environment)  
2) Install this MCP server (venv)  
3) Configure credentials + your MCP client  
4) Ask your assistant to scaffold and validate content using the tools

See:

- Credentials: [`docs/CREDENTIALS.md`](docs/CREDENTIALS.md)
- MCP clients: [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md)

## Example prompts: typical XSIAM developer flows (LLM + MCP)

These are example prompts you can paste into your LLM chat after the MCP server is configured.

### Scaffold a new pack and integration (local)

“Create a new pack called `Acme_ServiceNow` under `Packs/`. Scaffold an integration called `AcmeServiceNow` using the HelloWorld template. Then run `format_content`, `validate_content`, and `lint_content` on the pack.”

### Pre-PR checks for an existing pack (local)

“Run `validate_content` and `lint_content` on `Packs/Acme_ServiceNow`. Summarise errors with file paths and propose minimal fixes.”

### Generate integration README docs (local)

“Run `generate_docs` for `Packs/Acme_ServiceNow/Integrations/AcmeServiceNow/AcmeServiceNow.yml` and write the output README next to it.”

### Read-only: find what exists in the tenant (remote)

“Use `list_files` and show me all available content items related to **ServiceNow** (scripts, playbooks, mappers, classifiers, etc.).”

### Read-only: download a small, targeted subset (remote → local)

“From `list_files`, pick the **top 3 ServiceNow-related** items and use `download_content` to download only those into a temporary pack called `Remote_Inspect_ServiceNow` for review. Do not upload anything.”

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

See [`docs/CREDENTIALS.md`](docs/CREDENTIALS.md) for secure credential storage options including:

- 1Password CLI (recommended)
- macOS Keychain
- Windows Credential Manager
- AWS Secrets Manager
- GitHub Actions secrets

### 4. Configure Your MCP Client

See [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md) for configuration instructions for:

- Cursor
- Cline
- Claude Code
- Amazon Q Developer
- OpenAI Codex CLI

## Security notes

- **Do not store credentials in git**. Prefer 1Password/Keychain/Secrets Manager and inject via environment variables.
- Treat **remote write operations** (`upload_content`, `run_command`, `run_playbook`) as production-impacting unless you are targeting a dedicated dev tenant.

## Sample outputs

These are representative examples (truncated) of what you should see when the MCP tools run successfully.

### `list_files` (read-only)

This tool wraps `demisto-sdk download --list-files` and returns an inventory of custom content items available to download:

```text
Successfully parsed 617 custom content objects.
List of custom content files available to download (617):

Content Name                                      Content Type
BuildSimilarAlertSearchQuery                      script
CleanUpJiraAlerts                                 script
RLS - DSPM Correlation Alerts v1                  playbook
DSPM MS Forms Classifier                          classifier
DSPM Backlog Mapper                               mapper
Prisma Cloud Instance Name                        incidentfield
...
```

### `download_content` (single item)

Downloading a single item into a temporary pack for inspection (no upload):

```text
Fetching custom content bundle from server...
Successfully parsed 617 custom content objects.
Filtering process completed, 1/617 items remain.
Successful downloads: 1
Saved:
  Packs/RemoteSmokeTest/Scripts/JBTest/JBTest.yml
  Packs/RemoteSmokeTest/Scripts/JBTest/JBTest.py
  Packs/RemoteSmokeTest/Scripts/JBTest/README.md
```

### `validate_content`

Typical validation output (example):

```text
Running validation on: Packs/MyCompanyXSIAM
Validation finished: 0 errors, 2 warnings
- Warnings:
  - Some file(s) are missing optional documentation
  - pack_metadata.json could include more metadata (optional)
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
