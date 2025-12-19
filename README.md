# Cortex XSIAM SDK MCP Tools

**Alpha** - Not suitable for production use. APIs and tool schemas may change.

Model Context Protocol (MCP) server providing demisto-sdk commands as tools for LLM coding assistants.

## Overview

Wraps [demisto-sdk](https://github.com/demisto/demisto-sdk) commands, enabling LLM assistants to invoke SDK operations for XSIAM/XSOAR content development.

## Installation

```bash
# Clone and set up the MCP server
git clone https://github.com/ciaran-finnegan/cortex-xsiam-sdk-mcp-tools.git
cd cortex-xsiam-sdk-mcp-tools

# Create virtual environment (Python 3.10+ required)
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the MCP server
pip install -e .

# Install demisto-sdk separately (has conflicting pydantic version)
pipx install demisto-sdk
# Or in a separate environment: pip install demisto-sdk
```

**Note:** `demisto-sdk` and `mcp` have incompatible pydantic requirements. Install `demisto-sdk` via [pipx](https://pipx.pypa.io/) or ensure it's available in your PATH.

## Credentials Configuration

The `demisto-sdk` requires credentials to interact with your XSIAM/XSOAR instance. **Avoid storing credentials directly in `.env` files** as these can be accidentally committed to version control.

### Recommended: Use a Secrets Manager

#### macOS Keychain

```bash
# Store credentials
security add-generic-password -a "$USER" -s "demisto-sdk-api-key" -w "your-api-key"
security add-generic-password -a "$USER" -s "demisto-sdk-url" -w "https://your-instance.xdr.us.paloaltonetworks.com"

# Retrieve in your shell profile (.zshrc / .bashrc)
export DEMISTO_BASE_URL=$(security find-generic-password -a "$USER" -s "demisto-sdk-url" -w)
export DEMISTO_API_KEY=$(security find-generic-password -a "$USER" -s "demisto-sdk-api-key" -w)
```

#### Windows Credential Manager

```powershell
# Store credentials (run in PowerShell)
cmdkey /generic:demisto-sdk-api-key /user:demisto /pass:your-api-key
cmdkey /generic:demisto-sdk-url /user:demisto /pass:https://your-instance.xdr.us.paloaltonetworks.com

# Retrieve using PowerShell (add to your profile)
$cred = cmdkey /list:demisto-sdk-api-key
# Or use the CredentialManager module
```

#### 1Password CLI

```bash
# Store as a secure note or API credential in 1Password, then:
export DEMISTO_BASE_URL=$(op read "op://Private/XSIAM/url")
export DEMISTO_API_KEY=$(op read "op://Private/XSIAM/api-key")
```

See [1Password CLI documentation](https://developer.1password.com/docs/cli/).

#### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret --name demisto-sdk/credentials \
  --secret-string '{"url":"https://your-instance.xdr.us.paloaltonetworks.com","api_key":"your-api-key"}'

# Retrieve
export DEMISTO_CREDS=$(aws secretsmanager get-secret-value --secret-id demisto-sdk/credentials --query SecretString --output text)
export DEMISTO_BASE_URL=$(echo $DEMISTO_CREDS | jq -r '.url')
export DEMISTO_API_KEY=$(echo $DEMISTO_CREDS | jq -r '.api_key')
```

See [AWS Secrets Manager documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).

#### GitHub Actions

Use [encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets):

```yaml
env:
  DEMISTO_BASE_URL: ${{ secrets.DEMISTO_BASE_URL }}
  DEMISTO_API_KEY: ${{ secrets.DEMISTO_API_KEY }}
```

### Environment Variables (Less Secure)

If you must use a `.env` file for local development:

1. **Never commit `.env` to version control** — ensure it's in `.gitignore`
2. Create `.env` with restricted permissions:

```bash
touch .env && chmod 600 .env
```

```bash
# .env (DO NOT COMMIT)
DEMISTO_BASE_URL=https://your-instance.xdr.us.paloaltonetworks.com
DEMISTO_API_KEY=your-api-key
```

Load with:
```bash
source .env  # Or use direnv, dotenv, etc.
```

## Client Configuration

All examples below use the virtual environment Python interpreter. Replace `/path/to/cortex-xsiam-sdk-mcp-tools` with your actual installation path.

### Cursor

Add to `.cursor/mcp.json`. See [Cursor MCP documentation](https://docs.cursor.com/context/model-context-protocol).

```json
{
  "mcpServers": {
    "demisto-sdk": {
      "command": "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
      "args": ["-m", "mcp_demisto_sdk"]
    }
  }
}
```

### Cline

Add to Cline MCP settings. See [Cline MCP documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers).

```json
{
  "demisto-sdk": {
    "command": "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
    "args": ["-m", "mcp_demisto_sdk"]
  }
}
```

### Claude Code

Add to `~/.claude/claude_desktop_config.json`. See [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

```json
{
  "mcpServers": {
    "demisto-sdk": {
      "command": "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
      "args": ["-m", "mcp_demisto_sdk"]
    }
  }
}
```

### Amazon Q Developer

Add to `~/.aws/amazonq/agents/default.json` (IDE) or `~/.aws/amazonq/cli-agents` (CLI). See [Amazon Q MCP documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html).

```json
{
  "mcpServers": {
    "demisto-sdk": {
      "command": "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
      "args": ["-m", "mcp_demisto_sdk"]
    }
  }
}
```

### OpenAI Codex CLI

Add to `~/.codex/config.toml`. See [Codex MCP documentation](https://developers.openai.com/codex/mcp/).

```toml
[mcp_servers.demisto-sdk]
command = "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python"
args = ["-m", "mcp_demisto_sdk"]
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
# Activate virtual environment
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check mcp_demisto_sdk
```

## Related Resources

- [demisto-sdk](https://github.com/demisto/demisto-sdk) - Official SDK
- [demisto/content](https://github.com/demisto/content) - Official content library
- [cortex-xsiam-content-development-template](https://github.com/ciaran-finnegan/cortex-xsiam-content-development-template) - Development template
- [MCP Specification](https://modelcontextprotocol.io/)

## Licence

MIT - See [LICENSE](LICENSE).

---

Community project, not officially supported by Palo Alto Networks.
