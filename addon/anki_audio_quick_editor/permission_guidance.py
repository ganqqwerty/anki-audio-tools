"""User-facing recovery guidance for bundled executable permission failures."""

from __future__ import annotations

import errno
import platform
import shlex
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def bin_folder_path() -> Path:
    """Return the bundled CLI tools folder for this add-on installation."""
    return _PACKAGE_DIR / "bin"


def chmod_bin_command() -> str:
    """Return the Terminal command that restores executable bits for bundled tools."""
    return f"chmod -R +x {shlex.quote(str(bin_folder_path()))}"


def macos_permission_guidance() -> str:
    """Return user-facing instructions for repairing bundled CLI permissions."""
    return (
        "On macOS, close Anki, open Terminal, paste this command, press Return, then reopen Anki:\n\n"
        f"{chmod_bin_command()}"
    )


def windows_permission_guidance() -> str:
    """Return user-facing instructions for repairing Windows bundled CLI blocking."""
    return (
        "On Windows, this usually means Windows Security, antivirus, or your organization blocked one of "
        "Audio Quick Editor's bundled tools. Close Anki, open Windows Security > Virus & threat protection "
        "> Protection history, restore or allow the blocked tool from this add-on folder, then reopen Anki:\n\n"
        f"{bin_folder_path()}"
    )


def is_macos_permission_error(exc: BaseException) -> bool:
    """Return whether ``exc`` is the macOS CLI permission failure users can repair."""
    return platform.system() == "Darwin" and (
        isinstance(exc, PermissionError) or getattr(exc, "errno", None) == errno.EACCES
    )


def is_windows_permission_error(exc: BaseException) -> bool:
    """Return whether ``exc`` is a Windows CLI permission failure users can repair."""
    return platform.system() == "Windows" and (
        isinstance(exc, PermissionError)
        or getattr(exc, "errno", None) == errno.EACCES
        or getattr(exc, "winerror", None) == 5
    )


def permission_guidance(exc: BaseException) -> str:
    """Return platform-specific guidance for repairable permission failures."""
    if is_macos_permission_error(exc):
        return macos_permission_guidance()
    if is_windows_permission_error(exc):
        return windows_permission_guidance()
    return ""


def message_with_permission_guidance(message: str, exc: BaseException) -> str:
    """Append platform-specific guidance to repairable permission-denied messages."""
    rendered = message or str(exc) or type(exc).__name__
    guidance = permission_guidance(exc)
    if not guidance:
        return rendered
    if guidance in rendered:
        return rendered
    return f"{rendered}\n\n{guidance}"


def message_with_macos_permission_guidance(message: str, exc: BaseException) -> str:
    """Backward-compatible wrapper for platform permission guidance."""
    return message_with_permission_guidance(message, exc)


def launch_error_message(prefix: str, exc: BaseException) -> str:
    """Return a launch failure message, adding repair guidance when useful."""
    return message_with_permission_guidance(f"{prefix} {exc}", exc)
