"""Security utilities for path and input validation.

This module provides security primitives for:
- Path traversal prevention
- Binary execution validation
- Input sanitization for subprocess arguments
"""

import logging
import re
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Allowed SDK binary names (basename only)
ALLOWED_SDK_BINARIES = frozenset(["demisto-sdk"])

# Pattern for valid pack/content names (alphanumeric, underscore, hyphen)
SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")

# Pattern for valid file paths (no shell metacharacters)
# Allows alphanumeric, underscore, hyphen, dot, forward slash
SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9_\-./]+$")


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal is detected."""

    pass


class BinaryValidationError(SecurityError):
    """Raised when binary validation fails."""

    pass


def safe_resolve_path(
    path: str | Path,
    allowed_root: Path,
    follow_symlinks: bool = False,
) -> Optional[Path]:
    """
    Safely resolve a path ensuring it stays within allowed_root.

    This function prevents path traversal attacks by:
    1. Resolving the path to its canonical form
    2. Verifying the resolved path is within the allowed root directory
    3. Optionally rejecting symlinks for additional security

    Args:
        path: The path to resolve (absolute or relative to allowed_root)
        allowed_root: The root directory paths must be within
        follow_symlinks: If False (default), reject paths containing symlinks

    Returns:
        Resolved Path if valid, None if invalid or outside allowed_root
    """
    if not path or not allowed_root:
        return None

    try:
        path = Path(path)
        allowed_root = Path(allowed_root).resolve()

        # Handle relative paths by joining with allowed_root
        if not path.is_absolute():
            path = allowed_root / path

        # Resolve to canonical path (resolves .., symlinks, etc.)
        resolved = path.resolve()

        # Check for symlinks if not allowed
        if not follow_symlinks:
            # Check the original path for symlinks before resolution
            # We need to check each component that exists
            check_path = path
            while check_path != check_path.parent:
                if check_path.exists() and check_path.is_symlink():
                    logger.warning(f"Symlink detected in path: {check_path}")
                    return None
                check_path = check_path.parent

        # Verify resolved path is within allowed root
        try:
            resolved.relative_to(allowed_root)
        except ValueError:
            logger.warning(
                f"Path traversal blocked: {path} resolved to {resolved}, "
                f"outside of {allowed_root}"
            )
            return None

        return resolved

    except Exception as e:
        logger.warning(f"Path validation failed for {path}: {e}")
        return None


def validate_sdk_binary(binary_path: str) -> Optional[str]:
    """
    Validate that the SDK binary is a trusted demisto-sdk executable.

    This function prevents arbitrary code execution by ensuring only
    known SDK binary names are allowed.

    Args:
        binary_path: Path to the binary (can be basename or full path)

    Returns:
        Validated absolute path to the binary, or None if invalid
    """
    if not binary_path:
        return None

    path = Path(binary_path)

    # Check if it's just a basename (relies on PATH lookup)
    if path.name == binary_path:
        if path.name not in ALLOWED_SDK_BINARIES:
            logger.warning(f"Binary name not in allowlist: {binary_path}")
            return None
        # Use shutil.which to find in PATH
        found = shutil.which(binary_path)
        if not found:
            logger.warning(f"Binary not found in PATH: {binary_path}")
            return None
        return found

    # Full path provided - validate basename is allowed
    if path.name not in ALLOWED_SDK_BINARIES:
        logger.warning(f"Binary name not in allowlist: {path.name}")
        return None

    # Resolve to absolute path
    if not path.is_absolute():
        path = path.resolve()

    # Verify the file exists and is executable
    if not path.exists():
        logger.warning(f"Binary does not exist: {path}")
        return None

    if not path.is_file():
        logger.warning(f"Binary is not a file: {path}")
        return None

    return str(path.resolve())


def validate_name(name: str, max_length: int = 100) -> Optional[str]:
    """
    Validate a pack/integration/script name.

    Names must contain only alphanumeric characters, underscores, and hyphens.

    Args:
        name: The name to validate
        max_length: Maximum allowed length (default 100)

    Returns:
        The validated name if valid, None otherwise
    """
    if not name:
        return None

    if len(name) > max_length:
        logger.warning(f"Name exceeds max length ({max_length}): {name[:50]}...")
        return None

    if not SAFE_NAME_PATTERN.match(name):
        logger.warning(f"Name contains invalid characters: {name}")
        return None

    return name


def validate_path_argument(
    path: str,
    allowed_root: Optional[Path] = None,
    must_exist: bool = False,
    follow_symlinks: bool = False,
) -> Optional[str]:
    """
    Validate a path argument for subprocess use.

    This function ensures paths don't contain shell metacharacters
    that could be used for command injection.

    Args:
        path: The path to validate
        allowed_root: If provided, path must be within this directory
        must_exist: If True, path must exist
        follow_symlinks: If False, reject symlinks

    Returns:
        Validated path string, or None if invalid
    """
    if not path:
        return None

    # Reject shell metacharacters
    if not SAFE_PATH_PATTERN.match(path):
        logger.warning(f"Path contains invalid characters: {path}")
        return None

    # If allowed_root provided, use safe_resolve_path
    if allowed_root:
        resolved = safe_resolve_path(path, allowed_root, follow_symlinks=follow_symlinks)
        if resolved is None:
            return None
        if must_exist and not resolved.exists():
            logger.warning(f"Path does not exist: {resolved}")
            return None
        return str(resolved)

    # Basic validation without root restriction
    p = Path(path)
    if must_exist and not p.exists():
        logger.warning(f"Path does not exist: {path}")
        return None

    # Check for symlinks if not allowed
    if not follow_symlinks and p.exists() and p.is_symlink():
        logger.warning(f"Symlink rejected: {path}")
        return None

    return path


def check_insecure_flag(insecure: bool, acknowledged: bool) -> tuple[bool, Optional[str]]:
    """
    Check if the insecure flag can be used.

    The insecure flag disables SSL verification, which is dangerous.
    Users must explicitly acknowledge the risk.

    Args:
        insecure: Whether the insecure flag is requested
        acknowledged: Whether the user has acknowledged the risk

    Returns:
        Tuple of (can_proceed, error_message)
        - can_proceed: True if operation can proceed
        - error_message: Error message if can_proceed is False, None otherwise
    """
    if not insecure:
        return True, None

    if not acknowledged:
        return False, (
            "SECURITY WARNING: The 'insecure' option disables SSL certificate "
            "verification, exposing your API credentials to man-in-the-middle attacks. "
            "To proceed, you must set 'acknowledge_insecure_risk': true to confirm "
            "you understand and accept this security risk. "
            "Consider configuring proper SSL certificates instead."
        )

    logger.warning("SSL verification disabled - MITM attack risk")
    return True, None
