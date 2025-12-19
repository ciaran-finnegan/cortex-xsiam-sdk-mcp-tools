# MCP Client Configuration

Configure your LLM coding assistant to use the demisto-sdk MCP server.

All examples use the virtual environment Python interpreter. Replace `/path/to/cortex-xsiam-sdk-mcp-tools` with your actual installation path.

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

Add to `~/.claude/claude_desktop_config.json`.

See [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

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

Verify credentials are available to the MCP server process. Some clients may not inherit shell environment variables — check your client's documentation for passing environment variables to MCP servers.

