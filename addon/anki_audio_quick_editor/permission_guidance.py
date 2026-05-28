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


def launch_error_message(prefix: str, exc: BaseException) -> str:
    """Return a launch failure message, adding repair guidance when useful."""
    return message_with_permission_guidance(f"{prefix} {exc}", exc)


def external_tool_error_message(message: str, *, tool_name: str = "external tool") -> str:
    """Return a user-facing external tool error with targeted recovery guidance."""
    rendered = message.strip()
    if not rendered:
        return rendered
    guidance = _external_tool_guidance(rendered, tool_name=tool_name)
    if not guidance or guidance in rendered:
        return rendered
    return f"{rendered}\n\n{guidance}"


def _external_tool_guidance(message: str, *, tool_name: str) -> str:
    lowered = message.lower()
    if _looks_like_permission_failure(lowered):
        return (
            f"{tool_name} could not read, write, or execute one of the files it needs. "
            "Check the file permissions and whether Windows Security, antivirus, macOS "
            "privacy prompts, or an organization policy blocked Anki or the audio tool."
        )
    if _looks_like_corrupt_runtime_failure(lowered):
        return (
            f"{tool_name} reported a corrupted or incompatible executable/model file. "
            "Open Settings > Diagnostics and repair the managed runtime. If you configured "
            "a custom tool path, replace it with a working build for this computer."
        )
    if _looks_like_unsupported_ffmpeg_feature(lowered):
        return (
            "This ffmpeg/ffprobe build does not include the codec, encoder, decoder, "
            "filter, protocol, or muxer required for this operation. Use Settings > "
            "Diagnostics to install or repair the managed runtime, or configure a full "
            "ffmpeg build with the missing feature enabled."
        )
    if _looks_like_ffmpeg_media_failure(lowered):
        return (
            "ffmpeg/ffprobe could not read or write this audio with the requested settings. "
            "The source may be damaged or unsupported, the output format may be unavailable, "
            "or the destination file may be locked. Try converting the source first or choose "
            "a different output format."
        )
    return ""


def _looks_like_permission_failure(lowered: str) -> bool:
    return any(
        marker in lowered
        for marker in (
            "permission denied",
            "access is denied",
            "operation not permitted",
            "not permitted",
            "eacces",
            "unauthorized",
        )
    )


def _looks_like_corrupt_runtime_failure(lowered: str) -> bool:
    return any(
        marker in lowered
        for marker in (
            "bad cpu type in executable",
            "exec format error",
            "not a valid win32 application",
            "invalid win32 application",
            "bad executable",
            "damaged",
            "corrupt",
            "corrupted",
            "invalid protobuf",
            "invalid onnx",
            "onnxruntime",
            "failed to load model",
            "model file",
        )
    )


def _looks_like_unsupported_ffmpeg_feature(lowered: str) -> bool:
    return any(
        marker in lowered
        for marker in (
            "unknown encoder",
            "unknown decoder",
            "unknown filter",
            "no such filter",
            "unknown protocol",
            "requested output format",
            "is not a suitable output format",
            "encoder not found",
            "decoder not found",
            "muxer not found",
            "demuxer not found",
            "not compiled",
            "disabled",
            "library configuration mismatch",
        )
    )


def _looks_like_ffmpeg_media_failure(lowered: str) -> bool:
    return any(
        marker in lowered
        for marker in (
            "invalid data found when processing input",
            "error while decoding",
            "could not find codec parameters",
            "moov atom not found",
            "failed to open",
            "no such file or directory",
            "input/output error",
            "i/o error",
            "resource temporarily unavailable",
            "device or resource busy",
            "file exists",
            "end of file",
        )
    )
