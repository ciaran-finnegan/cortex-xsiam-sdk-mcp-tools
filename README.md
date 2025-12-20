# Cortex XSIAM SDK MCP Tools

[![CI](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/codeql.yml/badge.svg)](https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/actions/workflows/codeql.yml)
[![License](https://img.shields.io/github/license/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools)](LICENSE)
![Lifecycle: Alpha](https://img.shields.io/badge/lifecycle-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)

MCP server that helps LLM coding assistants develop Cortex XSIAM/XSOAR content by providing:

- **Pattern search**: Find relevant playbooks, scripts, integrations, and XQL rules from the official [demisto/content](https://github.com/demisto/content) library using natural language
- **SDK operations**: Scaffold, format, validate, and lint content using `demisto-sdk`
- **Remote operations**: List, download, and upload content to your XSIAM/XSOAR tenant

## Stability & Support

- **Alpha**: interfaces may change between releases
- **Remote write tools** are production-impacting: `upload_content`, `run_command`, `run_playbook`
- Community project — not officially supported by Palo Alto Networks

## Documentation

- [Sample prompts](docs/SAMPLE_PROMPTS.md) - Ready-to-use prompts for content development
- [Credentials](docs/CREDENTIALS.md) - Secure credential storage options
- [MCP client configuration](docs/MCP_CLIENTS.md) - Setup for Cursor, Claude Code, Cline, Amazon Q, Codex CLI
- [XQL syntax reference](docs/XQL_REFERENCE.md) - Quick reference for parsing and modeling rules

## Common Tasks

| Task | Tools | Prompt |
|------|-------|--------|
| Find enrichment patterns | `find_similar_playbooks` | Use `find_similar_playbooks` to find playbooks that enrich IP addresses from multiple threat intel sources. |
| Find XQL parsing examples | `find_xql_examples` | Use `find_xql_examples` to find parsing rules that extract authentication events from Windows Security logs. |
| Find integration patterns | `find_integration_patterns` | Use `find_integration_patterns` to find integrations that use OAuth2 with token refresh. |
| Find script examples | `find_similar_scripts` | Use `find_similar_scripts` to find scripts that parse email headers and extract sender information. |
| Create from patterns | `find_similar_playbooks`, `init_pack` | Use `find_similar_playbooks` to find phishing playbooks, then create a pack called `AcmePhishing` with a similar structure. |
| Scaffold + validate | `init_pack`, `format_content`, `validate_content` | Create a pack called `Acme_ServiceNow`, scaffold an integration, then run `format_content` and `validate_content`. |
| Pre-PR checks | `validate_content`, `lint_content` | Run `validate_content` and `lint_content` on `Packs/MyPack`. Summarise errors and propose fixes. |

See [docs/SAMPLE_PROMPTS.md](docs/SAMPLE_PROMPTS.md) for comprehensive examples.

## Installation

### 1. Install demisto-sdk

The `demisto-sdk` must be installed separately (conflicting pydantic requirements).

```bash
# Using pipx (recommended)
pipx install demisto-sdk

# Or using pip in a separate environment
python3.11 -m venv ~/.demisto-sdk-venv
~/.demisto-sdk-venv/bin/pip install demisto-sdk
export PATH="$HOME/.demisto-sdk-venv/bin:$PATH"  # Add to ~/.zshrc
```

### 2. Install the MCP Server

```bash
git clone https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools.git
cd cortex-xsiam-sdk-mcp-tools
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Install the Pattern Index

The pattern index enables semantic search over 4,700+ playbooks, scripts, integrations, and XQL rules.

**Option A: Download pre-built index (fastest)**

```bash
mkdir -p ~/.xsiam-patterns
curl -L https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools/releases/latest/download/pattern-index.tar.gz \
  | tar -xz -C ~/.xsiam-patterns/
```

**Option B: Build from source**

```bash
git clone --depth 1 https://github.com/demisto/content.git ~/content
xsiam-build-index --source ~/content
```

### 4. Configure Content Path (Recommended)

When you search for patterns, the tools return metadata (name, description, pack). To also fetch the **full source code** (YAML, Python, XQL), set the path to your local clone of the [demisto/content](https://github.com/demisto/content) repository:

```bash
# Clone the official content repo (if you haven't already)
git clone https://github.com/demisto/content.git ~/Documents/Dev/content

# Add to ~/.zshrc (or ~/.bashrc) - adjust path to your clone location
export DEMISTO_SDK_CONTENT_PATH="$HOME/Documents/Dev/content"
```

Keep your clone updated to get the latest patterns:

```bash
cd ~/Documents/Dev/content && git pull
```

This enables prompts like: *"Find playbooks that enrich IP addresses and show me the full YAML"*

Without this variable, pattern search still works but returns metadata only.

### 5. Configure Credentials

See [docs/CREDENTIALS.md](docs/CREDENTIALS.md) for secure credential storage (macOS Keychain, Windows Credential Manager, GitHub Actions secrets).

### 6. Configure Your MCP Client

See [docs/MCP_CLIENTS.md](docs/MCP_CLIENTS.md) for setup instructions.

## Tools

| Tool | Description |
|------|-------------|
| **Pattern Search** | |
| `search_patterns` | Search all content types with natural language |
| `find_similar_playbooks` | Find playbooks matching a description |
| `find_similar_scripts` | Find scripts with similar functionality |
| `find_integration_patterns` | Find integration patterns (REST API, OAuth2, etc.) |
| `find_xql_examples` | Find XQL parsing/modeling rule examples |
| `find_classifier_examples` | Find event classifier examples |
| `find_mapper_examples` | Find field mapper examples |
| `get_pattern_index_stats` | Show index statistics |
| **SDK Operations** | |
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
| `find_dependencies` | Analyse pack dependencies |
| `update_release_notes` | Version management |
| `zip_packs` | Create distributable archives |
| `openapi_codegen` | Generate from OpenAPI spec |
| `postman_codegen` | Generate from Postman collection |
| **Remote Operations** | |
| `list_files` | List custom content items (read-only) |
| `download_content` | Download content from tenant |
| `upload_content` | Deploy content to tenant ⚠️ |
| `run_command` | Execute command on tenant ⚠️ |
| `run_playbook` | Run playbook on tenant ⚠️ |

⚠️ = Production-impacting

### Content Types Indexed

| Type | Source |
|------|--------|
| Playbooks | `Packs/*/Playbooks/*.yml` |
| Scripts | `Packs/*/Scripts/**/*.yml` |
| Integrations | `Packs/*/Integrations/**/*.yml` |
| Classifiers | `Packs/*/Classifiers/classifier-*.json` |
| Mappers | `Packs/*/Classifiers/*mapper*.json` |
| Parsing Rules | `Packs/*/ParsingRules/**/*.xif` |
| Modeling Rules | `Packs/*/ModelingRules/**/*.xif` |

## Development

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
ruff check mcp_demisto_sdk tests
mypy mcp_demisto_sdk
pytest
```

## Related Resources

- [demisto-sdk](https://github.com/demisto/demisto-sdk) - Official SDK
- [demisto/content](https://github.com/demisto/content) - Official content library
- [MCP Specification](https://modelcontextprotocol.io/)

## Licence

MIT - See [LICENSE](LICENSE).

---

Community project, not officially supported by Palo Alto Networks.
