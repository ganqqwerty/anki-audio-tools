"""Executable and bundled audio tool discovery."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

from .errors import (
    MissingDeepFilterError,
    MissingDpdfnetError,
    MissingFfmpegError,
    MissingRnnoiseError,
    MissingSpleeterError,
)

BUNDLED_DEEP_FILTER_VERSION = "0.5.6"
BUNDLED_RNNOISE_VERSION = "0.2"
BUNDLED_DPDFNET_VERSION = "0.1.0"
FFMPEG_AUDIO_CODEC_ARG = "-codec:a"
WAV_MIME_TYPE = "audio/wav"
_PACKAGE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = _PACKAGE_DIR
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
}
_LEGACY_TOOL_PATHS = {
    "deep-filter": {
        "macos-arm64": ("bin/deep-filter-0.5.6-aarch64-apple-darwin",),
        "macos-x86_64": ("bin/deep-filter-0.5.6-x86_64-apple-darwin",),
        "windows-x86_64": ("bin/deep-filter-0.5.6-x86_64-pc-windows-msvc.exe",),
    },
    "rnnoise-cli": {
        "macos-arm64": ("bin/rnnoise-cli-macos-arm64/bin/rnnoise-cli",),
        "macos-x86_64": ("bin/rnnoise-cli-macos-x86_64/bin/rnnoise-cli",),
        "windows-x86_64": ("bin/rnnoise-cli-windows-x86_64/rnnoise-cli.exe",),
    }
}


def current_platform_key() -> str | None:
    """Return the supported release target key for this runtime platform."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Darwin" and machine == "x86_64":
        return "macos-x86_64"
    if system == "Windows" and machine in {"amd64", "x86_64", "64bit"}:
        return "windows-x86_64"
    return None


def platform_description() -> str:
    """Return a diagnostic-friendly platform description."""
    return f"{platform.system()} {platform.machine()}".strip()


def bundled_tool_path(tool_name: str) -> Path | None:
    """Return a bundled tool path for the current platform when it exists."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    executable = _TOOL_EXECUTABLES.get(tool_name, {}).get(platform_key)
    if executable is None:
        return None
    path = _PACKAGE_DIR / "bin" / platform_key / executable
    if path.is_file():
        return path
    for legacy_path in _LEGACY_TOOL_PATHS.get(tool_name, {}).get(platform_key, ()):
        path = _PACKAGE_DIR / legacy_path
        if path.is_file():
            return path
    return None


def expected_bundled_tool_path(tool_name: str) -> Path | None:
    """Return the expected bundled path for diagnostics, even when missing."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    executable = _TOOL_EXECUTABLES.get(tool_name, {}).get(platform_key)
    if executable is None:
        return None
    return _PACKAGE_DIR / "bin" / platform_key / executable


def tool_source_label(tool_path: Path, *, configured_path: str = "") -> str:
    """Return whether a resolved tool came from config, bundle, or PATH."""
    if configured_path and Path(configured_path).expanduser() == tool_path:
        return "config"
    try:
        tool_path.relative_to(_PACKAGE_DIR / "bin")
    except ValueError:
        return "PATH"
    return "bundled"


def find_ffmpeg(configured_path: str = "") -> Path:  # pragma: no mutate
    """Return ffmpeg, honoring config, bundled binary, then PATH."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    bundled = bundled_tool_path("ffmpeg")
    if bundled is not None:
        return bundled
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffmpeg. Reinstall the add-on to restore the bundled "
        "runtime, configure an ffmpeg path, or make ffmpeg available in PATH."
    )


def find_ffprobe(ffmpeg_path: Path) -> Path:
    """Return ffprobe next to ffmpeg, bundled for this platform, or from PATH."""
    sibling = ffmpeg_path.with_name("ffprobe" + ffmpeg_path.suffix)
    if sibling.is_file():
        return sibling
    bundled = bundled_tool_path("ffprobe")
    if bundled is not None:
        return bundled
    found = shutil.which("ffprobe")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."
    )


def find_deep_filter(configured_path: str = "") -> Path:
    """Return a deep-filter executable path, honoring config, bundled binary, then PATH."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    bundled = _bundled_deep_filter_path()
    if bundled is not None:
        return bundled
    found = shutil.which("deep-filter")
    if found:
        return Path(found)
    raise MissingDeepFilterError(
        "DeepFilterNet's deep-filter executable is required for Standard denoise and Shorten Pauses. "
        "Install DeepFilterNet and make sure deep-filter is available in PATH, or configure its "
        "path in add-on settings."
    )


def _bundled_deep_filter_path() -> Path | None:
    return bundled_tool_path("deep-filter")


def expected_bundled_rnnoise_dir() -> Path | None:
    """Return the expected bundled RNNoise directory for the current platform."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    return _PACKAGE_DIR / "bin" / platform_key


def find_rnnoise_bundle() -> Path:
    """Return the bundled RNNoise executable path."""
    rnnoise_path = expected_bundled_tool_path("rnnoise-cli")
    if rnnoise_path is None:
        raise MissingRnnoiseError(f"RNNoise is not bundled for {platform_description()}.")
    if rnnoise_path.is_file():
        return rnnoise_path
    bundled = bundled_tool_path("rnnoise-cli")
    if bundled is not None:
        return bundled
    raise MissingRnnoiseError(
        f"RNNoise requires the bundled rnnoise-cli executable at {rnnoise_path}. "
        "Reinstall the add-on to restore it."
    )


def find_dpdfnet_bundle() -> Path:
    """Return the bundled DPDFNet executable path."""
    dpdfnet_path = expected_bundled_tool_path("dpdfnet")
    if dpdfnet_path is None:
        raise MissingDpdfnetError(f"DPDFNet is not bundled for {platform_description()}.")
    if dpdfnet_path.is_file():
        return dpdfnet_path
    raise MissingDpdfnetError(
        f"DPDFNet requires the bundled dpdfnet executable at {dpdfnet_path}. "
        "Reinstall the add-on to restore it."
    )


def expected_bundled_spleeter_model_path(model_name: str) -> Path | None:
    """Return the expected bundled Sherpa Spleeter model path."""
    if current_platform_key() is None:
        return None
    return _PACKAGE_DIR / "bin" / "models" / "spleeter-2stems-fp16" / model_name


def find_spleeter_bundle() -> tuple[Path, Path, Path]:
    """Return bundled Sherpa Spleeter executable and model paths."""
    executable_path = expected_bundled_tool_path("sherpa-spleeter")
    if executable_path is None:
        raise MissingSpleeterError(f"Sherpa Spleeter is not bundled for {platform_description()}.")
    if executable_path.is_file():
        spleeter_path = executable_path
    else:
        bundled = bundled_tool_path("sherpa-spleeter")
        if bundled is None:
            raise MissingSpleeterError(
                f"Voice Only requires the bundled sherpa-spleeter executable at {executable_path}. "
                "Reinstall the add-on to restore it."
            )
        spleeter_path = bundled

    return (
        spleeter_path,
        _required_spleeter_model("vocals.fp16.onnx"),
        _required_spleeter_model("accompaniment.fp16.onnx"),
    )


def _required_spleeter_model(model_name: str) -> Path:
    model_path = expected_bundled_spleeter_model_path(model_name)
    if model_path is None:
        raise MissingSpleeterError(f"Sherpa Spleeter models are not bundled for {platform_description()}.")
    if not model_path.is_file():
        raise MissingSpleeterError(
            f"Voice Only requires the bundled Sherpa Spleeter model at {model_path}. "
            "Reinstall the add-on to restore it."
        )
    return model_path
