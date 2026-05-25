"""User-facing recovery guidance for macOS executable permission failures."""

from __future__ import annotations

import errno
import platform
import shlex
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def chmod_bin_command() -> str:
    """Return the Terminal command that restores executable bits for bundled tools."""
    return f"chmod -R +x {shlex.quote(str(_PACKAGE_DIR / 'bin'))}"


def macos_permission_guidance() -> str:
    """Return user-facing instructions for repairing bundled CLI permissions."""
    return (
        "On macOS, close Anki, open Terminal, paste this command, press Return, then reopen Anki:\n\n"
        f"{chmod_bin_command()}"
    )


def is_macos_permission_error(exc: BaseException) -> bool:
    """Return whether ``exc`` is the macOS CLI permission failure users can repair."""
    return platform.system() == "Darwin" and (
        isinstance(exc, PermissionError) or getattr(exc, "errno", None) == errno.EACCES
    )


def message_with_macos_permission_guidance(message: str, exc: BaseException) -> str:
    """Append chmod guidance to macOS permission-denied messages."""
    rendered = message or str(exc) or type(exc).__name__
    if not is_macos_permission_error(exc):
        return rendered
    command = chmod_bin_command()
    if command in rendered:
        return rendered
    return f"{rendered}\n\n{macos_permission_guidance()}"


def launch_error_message(prefix: str, exc: BaseException) -> str:
    """Return a launch failure message, adding macOS repair guidance when useful."""
    return message_with_macos_permission_guidance(f"{prefix} {exc}", exc)
