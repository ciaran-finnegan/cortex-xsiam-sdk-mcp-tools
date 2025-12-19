"""Tests for MCP server."""

import pytest
from mcp_demisto_sdk.server import run_sdk_command


class TestRunSdkCommand:
    """Tests for SDK command execution."""

    def test_run_sdk_command_help(self) -> None:
        """Test running demisto-sdk --help."""
        result = run_sdk_command(["--help"])
        assert result["returncode"] == 0
        assert "demisto-sdk" in result["stdout"].lower()

    def test_run_sdk_command_invalid(self) -> None:
        """Test running invalid command."""
        result = run_sdk_command(["invalid-command-xyz"])
        assert result["success"] is False


class TestToolHandlers:
    """Tests for tool handler functions."""

    # Add more specific tests as the implementation matures
    pass

