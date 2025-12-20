# Cortex XSIAM SDK MCP Tools

[![CI](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/codeql.yml/badge.svg)](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/codeql.yml)
[![License](https://img.shields.io/github/license/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools)](LICENSE)
![Lifecycle: Alpha](https://img.shields.io/badge/lifecycle-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)

Expose common `demisto-sdk` operations as MCP tools so an LLM can assist with Cortex XSIAM/XSOAR content development.

**New in v0.2.0**: Pattern search (RAG) - semantic search over playbooks, scripts, integrations, XQL rules, and more from the official content library.

## Stability & support

- This project is **alpha**: interfaces may change between releases.
- Treat **remote write tools** as production-impacting (`upload_content`, `run_command`, `run_playbook`).
- Community project — not officially supported by Palo Alto Networks.

## Documentation

- **Sample prompts**: [`docs/SAMPLE_PROMPTS.md`](docs/SAMPLE_PROMPTS.md) - Ready-to-use prompts for content development
- Credentials: [`docs/CREDENTIALS.md`](docs/CREDENTIALS.md)
- MCP client configuration: [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md)
- XQL syntax reference: [`docs/XQL_REFERENCE.md`](docs/XQL_REFERENCE.md)

## Why this exists

- **Faster scaffolding**: create packs, integrations, and scripts quickly using an LLM coding assistant
- **Higher quality**: run format/validate/lint using natural language
- **Pattern search**: find relevant examples from the official content library using natural language queries

## Quickstart

1) Install `demisto-sdk` (separate environment)  
2) Install this MCP server (venv)  
3) Configure credentials + your MCP client  
4) Ask your assistant to scaffold and validate content using the tools

See [`docs/CREDENTIALS.md`](docs/CREDENTIALS.md) and [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md) for setup details.

## Common tasks (copy/paste prompts)

| Task | Tools | Prompt |
|------|-------|--------|
| Find enrichment patterns | `find_similar_playbooks` | Use `find_similar_playbooks` to find playbooks that enrich IP addresses from multiple threat intel sources. Show the top 5 with their pack names. |
| Find XQL parsing examples | `find_xql_examples` | Use `find_xql_examples` to find parsing rules that extract authentication events from Windows Security logs. |
| Create playbook from patterns | `find_similar_playbooks`, `init_pack` | Use `find_similar_playbooks` to find phishing investigation playbooks, then create a new pack called `AcmePhishing` with a similar playbook structure. |
| Find integration patterns | `find_integration_patterns` | Use `find_integration_patterns` to find integrations that use OAuth2 with token refresh. Show me the authentication code patterns. |
| Find script examples | `find_similar_scripts` | Use `find_similar_scripts` to find scripts that parse email headers and extract sender information. |
| Scaffold + validate | `init_pack`, `format_content`, `validate_content` | Create a pack called `Acme_ServiceNow` under `Packs/`. Scaffold an integration using the HelloWorld template, then run `format_content` and `validate_content`. |
| Pre-PR checks | `validate_content`, `lint_content` | Run `validate_content` and `lint_content` on `Packs/Acme_ServiceNow`. Summarise errors and propose fixes. |
| Check index stats | `get_pattern_index_stats` | Use `get_pattern_index_stats` to show what content is available in the pattern index. |

See [`docs/SAMPLE_PROMPTS.md`](docs/SAMPLE_PROMPTS.md) for more comprehensive examples.

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

- macOS Keychain
- Windows Credential Manager
- GitHub Actions secrets

### 4. Configure Your MCP Client

See [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md) for configuration instructions for:

- Cursor
- Cline
- Claude Code
- Amazon Q Developer
- OpenAI Codex CLI

## Pattern Search (RAG)

Search for patterns from the official [demisto/content](https://github.com/demisto/content) library using natural language. The LLM can find relevant playbooks, scripts, integrations, XQL rules, classifiers, and mappers to use as examples.

### Setup

**Option A: Download pre-built index (fastest)**

```bash
# Download latest pre-built index from releases
curl -L https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/releases/latest/download/pattern-index.tar.gz \
  | tar -xz -C ~/.xsiam-patterns/
```

**Option B: Build from source**

```bash
# Clone content repo and build index
git clone --depth 1 https://github.com/demisto/content.git ~/content
xsiam-build-index --source ~/content
```

The index is stored at `~/.xsiam-patterns/chroma/` (configurable via `XSIAM_PATTERN_DB`).

**Optional: Set content path for fetching full files**

```bash
export DEMISTO_SDK_CONTENT_PATH="$HOME/content"
```

### Pattern Search Tools

| Tool | Description |
|------|-------------|
| `search_patterns` | Search all content types with natural language |
| `find_similar_playbooks` | Find playbooks similar to a description |
| `find_similar_scripts` | Find scripts with similar functionality |
| `find_integration_patterns` | Find integration patterns (REST API, OAuth2, etc.) |
| `find_xql_examples` | Find XQL parsing/modeling rule examples |
| `find_classifier_examples` | Find event classifier examples |
| `find_mapper_examples` | Find field mapper examples |
| `get_pattern_index_stats` | Show index statistics |

### Example Prompts

| Task | Prompt |
|------|--------|
| Find enrichment patterns | "Use `find_similar_playbooks` to find playbooks that enrich IP addresses from multiple threat intel sources" |
| Find XQL syntax | "Use `find_xql_examples` to find parsing rules that extract usernames from Windows event logs" |
| Find integration patterns | "Use `find_integration_patterns` to find integrations that use OAuth2 with refresh tokens" |
| Find script patterns | "Use `find_similar_scripts` to find scripts that parse email headers" |

### Content Types Indexed

| Type | Source |
|------|--------|
| Playbooks | `Packs/*/Playbooks/*.yml` |
| Scripts | `Packs/*/Scripts/**/*.yml` |
| Integrations | `Packs/*/Integrations/**/*.yml` |
| Classifiers | `Packs/*/Classifiers/classifier-*.json` |
| Mappers | `Packs/*/Classifiers/*mapper*.json` |
| Parsing Rules (XQL) | `Packs/*/ParsingRules/**/*.xif` |
| Modeling Rules (XQL) | `Packs/*/ModelingRules/**/*.xif` |

## CI & security scanning

- **CI**: runs `ruff` and `pytest` on PRs and main.
- **CodeQL**: performs static analysis security scanning on PRs and on a schedule.

## Sample outputs

<!-- markdownlint-disable MD033 -->
<details>
<summary><code>list_files</code> (read-only)</summary>

```text
Successfully parsed 617 custom content objects.
List of custom content files available to download (617):

Content Name                                      Content Type
Acme ServiceNow Ticket Sync                       playbook
AcmeServiceNow                                    integration
Acme ServiceNow Classifier                        classifier
Acme ServiceNow Mapper                            mapper
Acme Instance Name                                incidentfield
...
```

</details>

<details>
<summary><code>download_content</code> (single item)</summary>

```text
Fetching custom content bundle from server...
Successfully parsed 617 custom content objects.
Filtering process completed, 1/617 items remain.
Successful downloads: 1
Saved:
  Packs/Remote_Inspect_ServiceNow/Scripts/AcmeServiceNowHelper/AcmeServiceNowHelper.yml
  Packs/Remote_Inspect_ServiceNow/Scripts/AcmeServiceNowHelper/AcmeServiceNowHelper.py
  Packs/Remote_Inspect_ServiceNow/Scripts/AcmeServiceNowHelper/README.md
```

</details>

<details>
<summary><code>validate_content</code></summary>

```text
Running validation on: Packs/Acme_ServiceNow
Validation finished: 0 errors, 2 warnings
- Warnings:
  - Some file(s) are missing optional documentation
  - pack_metadata.json could include more metadata (optional)
```

</details>
<!-- markdownlint-enable MD033 -->

## Tools

### SDK Tools (demisto-sdk)

| Tool | Scope | Remote write | Description |
|------|-------|-------------:|-------------|
| `init_pack` | Local | No | Create content pack structure |
| `init_integration` | Local | No | Scaffold integration |
| `init_script` | Local | No | Scaffold script |
| `format_content` | Local | No | Standardise YAML/Python formatting |
| `validate_content` | Local | No | Check content validity |
| `lint_content` | Local | No | Run code quality checks |
| `generate_docs` | Local | No | Create README documentation |
| `generate_unit_tests` | Local | No | Generate test scaffolds |
| `generate_test_playbook` | Local | No | Create test playbook |
| `generate_outputs` | Local | No | Generate context paths from JSON |
| `find_dependencies` | Local | No | Analyse pack dependencies |
| `update_release_notes` | Local | No | Version management |
| `zip_packs` | Local | No | Create distributable archives |
| `openapi_codegen` | Local | No | Generate from OpenAPI spec |
| `postman_codegen` | Local | No | Generate from Postman collection |
| `list_files` | Remote | No | List custom content items available to download (read-only) |
| `download_content` | Remote | No | Download content from the tenant |
| `upload_content` | Remote | **Yes** | Deploy content to XSIAM/XSOAR |
| `run_command` | Remote | **Yes** | Execute a command on the tenant |
| `run_playbook` | Remote | **Yes** | Run a playbook on the tenant |

### Pattern Search Tools (RAG)

| Tool | Description |
|------|-------------|
| `search_patterns` | Search all content types with natural language |
| `find_similar_playbooks` | Find playbooks similar to a description |
| `find_similar_scripts` | Find scripts with similar functionality |
| `find_integration_patterns` | Find integration patterns |
| `find_xql_examples` | Find XQL parsing/modeling rule examples |
| `find_classifier_examples` | Find event classifier examples |
| `find_mapper_examples` | Find field mapper examples |
| `get_pattern_index_stats` | Show index statistics |

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
