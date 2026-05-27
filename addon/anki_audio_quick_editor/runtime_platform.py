"""Platform detection and executable names for managed runtime assets."""

from __future__ import annotations

import platform

_TOOL_EXECUTABLES = {
    "ffmpeg": {
        "macos-arm64": "ffmpeg",
        "macos-x86_64": "ffmpeg",
        "windows-x86_64": "ffmpeg.exe",
    },
    "ffprobe": {
        "macos-arm64": "ffprobe",
        "macos-x86_64": "ffprobe",
        "windows-x86_64": "ffprobe.exe",
    },
    "deep-filter": {
        "macos-arm64": "deep-filter",
        "macos-x86_64": "deep-filter",
        "windows-x86_64": "deep-filter.exe",
    },
    "rnnoise-cli": {
        "macos-arm64": "rnnoise-cli",
        "macos-x86_64": "rnnoise-cli",
        "windows-x86_64": "rnnoise-cli.exe",
    },
    "dpdfnet": {
        "macos-arm64": "dpdfnet",
        "macos-x86_64": "dpdfnet",
        "windows-x86_64": "dpdfnet.exe",
    },
    "sherpa-spleeter": {
        "macos-arm64": "sherpa-spleeter",
        "macos-x86_64": "sherpa-spleeter",
        "windows-x86_64": "sherpa-spleeter.exe",
    },
    "silero-vad": {
        "macos-arm64": "silero-vad",
        "macos-x86_64": "silero-vad",
        "windows-x86_64": "silero-vad.exe",
    },
}

__all__ = ["_TOOL_EXECUTABLES", "current_platform_key", "platform", "tool_executable_name"]


def current_platform_key() -> str | None:
    """Return the managed runtime target key for this host."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Darwin" and machine == "x86_64":
        return "macos-x86_64"
    if system == "Windows" and machine in {"amd64", "x86_64", "64bit"}:
        return "windows-x86_64"
    return None


def tool_executable_name(tool_name: str, platform_key: str | None) -> str | None:
    """Return the managed executable filename for a tool/platform pair."""
    return _TOOL_EXECUTABLES.get(tool_name, {}).get(platform_key or "")
