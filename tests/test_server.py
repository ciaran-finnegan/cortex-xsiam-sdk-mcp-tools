"""Tests for MCP server."""

import subprocess

import pytest
from mcp_demisto_sdk.server import run_sdk_command, TOOLS, server


def demisto_sdk_available() -> bool:
    """Check if demisto-sdk is installed and functional."""
    try:
        result = subprocess.run(
            ["demisto-sdk", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


class TestServer:
    """Tests for MCP server setup."""

    def test_server_name(self) -> None:
        """Test server has correct name."""
        assert server.name == "demisto-sdk"

    def test_tools_defined(self) -> None:
        """Test tools are defined."""
        assert len(TOOLS) >= 19


class TestRunSdkCommand:
    """Tests for SDK command execution."""

    @pytest.mark.skipif(
        not demisto_sdk_available(),
        reason="demisto-sdk not installed or not functional"
    )
    def test_run_sdk_command_help(self) -> None:
        """Test running demisto-sdk --help."""
        result = run_sdk_command(["--help"])
        assert result["returncode"] == 0
        assert "demisto-sdk" in result["stdout"].lower()

    def test_run_sdk_command_missing_binary(self) -> None:
        """Test handling of missing binary."""
        # This tests the error handling when the command fails
        result = run_sdk_command(["invalid-command-xyz"])
        assert result["success"] is False


class TestToolHandlers:
    """Tests for tool handler functions."""

    # Add more specific tests as the implementation matures
    pass

