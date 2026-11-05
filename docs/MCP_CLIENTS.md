# MCP Client Configuration

<!-- markdownlint-disable MD012 -->

Configure your LLM coding assistant to use the demisto-sdk MCP server.

All examples use the virtual environment Python interpreter. Replace `/path/to/cortex-xsiam-sdk-mcp-tools` with your actual installation path.

## Notes on environment and demisto-sdk

- **Credentials**: The MCP server expects `DEMISTO_BASE_URL`, `DEMISTO_API_KEY`, and `XSIAM_AUTH_ID` in its environment. Client config files are plaintext, so never put the key in an `env` block, start the server through `op run` or a Keychain / SecretStore launcher as in the Cursor example and [CREDENTIALS.md](CREDENTIALS.md). Examples that start Python directly need the credentials already in the client's environment.
- **demisto-sdk binary**: If you installed `demisto-sdk` in a non-default location (recommended), set:
  - `DEMISTO_SDK_BIN=/absolute/path/to/demisto-sdk`
- **Content repo layout**: `demisto-sdk` expects a `Packs/` directory. If your working directory is not a content repo, this MCP server will create and use `_tmp/demisto-sdk-content/Packs` automatically.

## Cursor

Add to `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global).

See [Cursor MCP documentation](https://docs.cursor.com/context/model-context-protocol).

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

Restart Cursor after updating the configuration.

### Cursor: ensure environment variables are available

Desktop clients do not inherit your shell environment. Resolve the credentials
at start with `op run`, which reads the `op://` references in `.env.op` and
prompts for Touch ID or Windows Hello if 1Password is locked (see
[CREDENTIALS.md](CREDENTIALS.md)):

```json
{
  "mcpServers": {
    "demisto-sdk": {
      "command": "/opt/homebrew/bin/op",
      "args": [
        "run",
        "--env-file=/path/to/cortex-xsiam-sdk-mcp-tools/.env.op",
        "--",
        "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
        "-m",
        "mcp_demisto_sdk"
      ],
      "env": {
        "DEMISTO_SDK_BIN": "/absolute/path/to/demisto-sdk"
      }
    }
  }
}
```

Desktop apps start with a short `PATH`, so use the full path to `op`
(`/opt/homebrew/bin/op`, `/usr/local/bin/op` or `C:\Program Files\1Password CLI\op.exe`).
For the macOS Keychain make the wrapper script from CREDENTIALS.md the
`command`, with no `args`. The same `command` and `args` work in every client
below.

## Kiro

Add to `.kiro/settings/mcp.json` in the workspace, or `~/.kiro/settings/mcp.json`
for every workspace. Same JSON as the Cursor example above, with `op` as the
command or the Keychain / SecretStore launcher script as the command.

## Cline

Add to Cline MCP settings via the extension settings UI or configuration file.

See [Cline MCP documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers).

```json
{
  "demisto-sdk": {
    "command": "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python",
    "args": ["-m", "mcp_demisto_sdk"]
  }
}
```

## Claude Code

Register the server from a terminal with `op run` as the command:

```bash
claude mcp add demisto-sdk -e DEMISTO_SDK_BIN=/absolute/path/to/demisto-sdk \
  -- op run --env-file=/path/to/cortex-xsiam-sdk-mcp-tools/.env.op \
  -- /path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python -m mcp_demisto_sdk
```

See [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp). Claude
Desktop reads `claude_desktop_config.json` and takes the same JSON as the Cursor
example above.

## Amazon Q Developer

Add to `~/.aws/amazonq/agents/default.json` (IDE) or `~/.aws/amazonq/cli-agents` (CLI).

See [Amazon Q MCP documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html).

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

## OpenAI Codex CLI

Add to `~/.codex/config.toml`.

See [Codex MCP documentation](https://developers.openai.com/codex/mcp/).

```toml
[mcp_servers.demisto-sdk]
command = "/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python"
args = ["-m", "mcp_demisto_sdk"]
```

## Verifying the Configuration

After configuring your client, verify the MCP server is working:

1. Restart your IDE/client
2. Check the MCP server status (client-specific)
3. Try invoking a tool, e.g., ask the assistant to "list demisto-sdk tools"

## Troubleshooting

### Server not starting

Check the Python path is correct:

```bash
/path/to/cortex-xsiam-sdk-mcp-tools/.venv/bin/python -c "import mcp_demisto_sdk; print('OK')"
```

### demisto-sdk not found

Ensure `demisto-sdk` is installed and in your PATH:

```bash
which demisto-sdk
demisto-sdk --version
```

### Environment variables not set

Desktop clients do not inherit shell environment variables. Start the server through `op run` or a credential-store wrapper as above, do not copy the key into the client's configuration.
