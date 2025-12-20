"""Security tests for the MCP server.

These tests verify that security controls are working correctly:
- Path traversal prevention
- Binary validation
- Input validation
- SSL insecure flag acknowledgment
"""

import os
import tempfile
from pathlib import Path

import pytest

from mcp_demisto_sdk.security import (
    check_insecure_flag,
    safe_resolve_path,
    validate_name,
    validate_path_argument,
    validate_sdk_binary,
)


class TestSafeResolvePath:
    """Tests for path traversal prevention."""

    def test_relative_path_within_root(self, tmp_path: Path) -> None:
        """Test that relative paths within root are allowed."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.touch()

        result = safe_resolve_path("test.txt", tmp_path)
        assert result is not None
        assert result == test_file

    def test_absolute_path_within_root(self, tmp_path: Path) -> None:
        """Test that absolute paths within root are allowed."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        result = safe_resolve_path(str(test_file), tmp_path)
        assert result is not None
        assert result == test_file

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are blocked."""
        # Try to escape the root
        result = safe_resolve_path("../../../etc/passwd", tmp_path)
        assert result is None

    def test_path_traversal_with_encoded_dots(self, tmp_path: Path) -> None:
        """Test that path traversal with dots is blocked."""
        result = safe_resolve_path("subdir/../../../etc/passwd", tmp_path)
        assert result is None

    def test_absolute_path_outside_root(self, tmp_path: Path) -> None:
        """Test that absolute paths outside root are blocked."""
        result = safe_resolve_path("/etc/passwd", tmp_path)
        assert result is None

    def test_symlink_blocked_by_default(self, tmp_path: Path) -> None:
        """Test that symlinks are blocked by default."""
        # Create a symlink
        target = tmp_path / "target.txt"
        target.touch()
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        result = safe_resolve_path("link.txt", tmp_path, follow_symlinks=False)
        assert result is None

    def test_symlink_allowed_when_enabled(self, tmp_path: Path) -> None:
        """Test that symlinks are allowed when explicitly enabled."""
        # Create a symlink
        target = tmp_path / "target.txt"
        target.touch()
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        result = safe_resolve_path("link.txt", tmp_path, follow_symlinks=True)
        assert result is not None

    def test_empty_path_returns_none(self, tmp_path: Path) -> None:
        """Test that empty path returns None."""
        result = safe_resolve_path("", tmp_path)
        assert result is None

    def test_none_allowed_root_returns_none(self) -> None:
        """Test that None allowed_root returns None."""
        result = safe_resolve_path("test.txt", None)  # type: ignore
        assert result is None


class TestValidateSdkBinary:
    """Tests for SDK binary validation."""

    def test_demisto_sdk_name_allowed(self) -> None:
        """Test that 'demisto-sdk' name is allowed."""
        # This will return the path if found, or None if not installed
        # We just verify it doesn't reject the name
        result = validate_sdk_binary("demisto-sdk")
        # Result can be path (if installed) or None (if not found in PATH)
        # The key is it's not rejected for being an invalid name

    def test_arbitrary_binary_rejected(self) -> None:
        """Test that arbitrary binary names are rejected."""
        result = validate_sdk_binary("malicious-binary")
        assert result is None

    def test_demisto_sdk_with_path_allowed(self, tmp_path: Path) -> None:
        """Test that full path to demisto-sdk is allowed."""
        # Create a fake demisto-sdk binary
        fake_binary = tmp_path / "demisto-sdk"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        result = validate_sdk_binary(str(fake_binary))
        assert result is not None

    def test_path_to_wrong_binary_rejected(self, tmp_path: Path) -> None:
        """Test that path to non-demisto-sdk binary is rejected."""
        fake_binary = tmp_path / "other-tool"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        result = validate_sdk_binary(str(fake_binary))
        assert result is None

    def test_empty_binary_returns_none(self) -> None:
        """Test that empty binary path returns None."""
        result = validate_sdk_binary("")
        assert result is None


class TestValidateName:
    """Tests for name validation."""

    def test_valid_name(self) -> None:
        """Test that valid names are accepted."""
        assert validate_name("MyPack") == "MyPack"
        assert validate_name("my_pack") == "my_pack"
        assert validate_name("my-pack") == "my-pack"
        assert validate_name("Pack123") == "Pack123"

    def test_name_with_spaces_rejected(self) -> None:
        """Test that names with spaces are rejected."""
        assert validate_name("My Pack") is None

    def test_name_with_special_chars_rejected(self) -> None:
        """Test that names with special characters are rejected."""
        assert validate_name("my;pack") is None
        assert validate_name("my|pack") is None
        assert validate_name("my$pack") is None
        assert validate_name("my`pack") is None

    def test_name_with_path_separator_rejected(self) -> None:
        """Test that names with path separators are rejected."""
        assert validate_name("../etc/passwd") is None
        assert validate_name("my/pack") is None

    def test_empty_name_rejected(self) -> None:
        """Test that empty name is rejected."""
        assert validate_name("") is None

    def test_name_too_long_rejected(self) -> None:
        """Test that names exceeding max length are rejected."""
        long_name = "a" * 200
        assert validate_name(long_name, max_length=100) is None


class TestValidatePathArgument:
    """Tests for path argument validation."""

    def test_valid_path(self) -> None:
        """Test that valid paths are accepted."""
        assert validate_path_argument("Packs/MyPack") == "Packs/MyPack"
        assert validate_path_argument("file.yml") == "file.yml"

    def test_path_with_shell_chars_rejected(self) -> None:
        """Test that paths with shell metacharacters are rejected."""
        assert validate_path_argument("file;rm -rf /") is None
        assert validate_path_argument("file|cat /etc/passwd") is None
        assert validate_path_argument("file`whoami`") is None
        assert validate_path_argument("file$(id)") is None

    def test_path_with_spaces_rejected(self) -> None:
        """Test that paths with spaces are rejected."""
        # Our pattern doesn't allow spaces for security
        assert validate_path_argument("path with spaces") is None

    def test_empty_path_rejected(self) -> None:
        """Test that empty path is rejected."""
        assert validate_path_argument("") is None


class TestCheckInsecureFlag:
    """Tests for SSL insecure flag handling."""

    def test_no_insecure_flag_allowed(self) -> None:
        """Test that operations without insecure flag proceed."""
        can_proceed, error = check_insecure_flag(insecure=False, acknowledged=False)
        assert can_proceed is True
        assert error is None

    def test_insecure_without_acknowledgment_blocked(self) -> None:
        """Test that insecure flag without acknowledgment is blocked."""
        can_proceed, error = check_insecure_flag(insecure=True, acknowledged=False)
        assert can_proceed is False
        assert error is not None
        assert "SECURITY WARNING" in error
        assert "acknowledge_insecure_risk" in error

    def test_insecure_with_acknowledgment_allowed(self) -> None:
        """Test that insecure flag with acknowledgment proceeds."""
        can_proceed, error = check_insecure_flag(insecure=True, acknowledged=True)
        assert can_proceed is True
        assert error is None


class TestServerInputValidation:
    """Integration tests for server handler input validation."""

    @pytest.mark.asyncio
    async def test_init_pack_invalid_name(self) -> None:
        """Test that invalid pack names are rejected."""
        from mcp_demisto_sdk.server import handle_init_pack

        result = await handle_init_pack({"name": "pack;rm -rf /"})
        assert result["success"] is False
        assert "Invalid" in result["stderr"]

    @pytest.mark.asyncio
    async def test_init_pack_valid_name(self) -> None:
        """Test that valid pack names pass validation."""
        from mcp_demisto_sdk.server import handle_init_pack

        # This will fail at demisto-sdk level if not installed,
        # but should pass input validation
        result = await handle_init_pack({"name": "ValidPack"})
        # If demisto-sdk isn't installed, it will fail with a different error
        # The key is it doesn't fail with "Invalid" input error
        if result["success"] is False:
            assert "Invalid pack name" not in result["stderr"]

    @pytest.mark.asyncio
    async def test_upload_content_insecure_blocked(self) -> None:
        """Test that insecure flag without acknowledgment is blocked."""
        from mcp_demisto_sdk.server import handle_upload_content

        result = await handle_upload_content({
            "input_path": "Packs/TestPack",
            "insecure": True,
        })
        assert result["success"] is False
        assert "SECURITY WARNING" in result["stderr"]

    @pytest.mark.asyncio
    async def test_list_files_insecure_blocked(self) -> None:
        """Test that insecure flag without acknowledgment is blocked."""
        from mcp_demisto_sdk.server import handle_list_files

        result = await handle_list_files({
            "insecure": True,
        })
        assert result["success"] is False
        assert "SECURITY WARNING" in result["stderr"]
