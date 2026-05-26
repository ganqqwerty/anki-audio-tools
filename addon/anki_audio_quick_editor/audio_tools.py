"""Executable and bundled audio tool discovery."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

from . import runtime_manager
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
    return None


def managed_tool_path(tool_name: str) -> Path | None:
    """Return a managed downloaded tool path for the current platform when ready."""
    return runtime_manager.managed_tool_path(_PACKAGE_DIR, tool_name)


def expected_managed_tool_path(tool_name: str) -> Path | None:
    """Return the expected managed path for diagnostics, even when missing."""
    return runtime_manager.expected_managed_tool_path(_PACKAGE_DIR, tool_name)


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
        tool_path.relative_to(runtime_manager.runtime_base_dir(_PACKAGE_DIR))
    except ValueError:
        pass
    else:
        return runtime_manager.RUNTIME_SOURCE_MANAGED
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
    managed = managed_tool_path("ffmpeg")
    if managed is not None:
        return managed
    bundled = bundled_tool_path("ffmpeg")
    if bundled is not None:
        return bundled
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffmpeg. The managed runtime may still be downloading "
        "or missing; open Settings > Diagnostics to install or repair it, configure an "
        "ffmpeg path, or make ffmpeg available in PATH."
    )


def find_ffprobe(ffmpeg_path: Path) -> Path:
    """Return ffprobe next to ffmpeg, bundled for this platform, or from PATH."""
    sibling = ffmpeg_path.with_name("ffprobe" + ffmpeg_path.suffix)
    if sibling.is_file():
        return sibling
    managed = managed_tool_path("ffprobe")
    if managed is not None:
        return managed
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
    managed = managed_tool_path("deep-filter")
    if managed is not None:
        return managed
    bundled = _bundled_deep_filter_path()
    if bundled is not None:
        return bundled
    found = shutil.which("deep-filter")
    if found:
        return Path(found)
    raise MissingDeepFilterError(
        "DeepFilterNet's deep-filter executable is required for Standard denoise and Shorten Pauses. "
        "The managed runtime may still be downloading or missing; open Settings > Diagnostics "
        "to install or repair it, or make deep-filter available in PATH."
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
    managed = managed_tool_path("rnnoise-cli")
    if managed is not None:
        return managed
    managed_expected = expected_managed_tool_path("rnnoise-cli")
    bundled_expected = expected_bundled_tool_path("rnnoise-cli")
    if bundled_expected is not None and bundled_expected.is_file():
        return bundled_expected
    rnnoise_path = managed_expected or bundled_expected
    if rnnoise_path is None:
        raise MissingRnnoiseError(f"RNNoise is not bundled for {platform_description()}.")
    bundled = bundled_tool_path("rnnoise-cli")
    if bundled is not None:
        return bundled
    raise MissingRnnoiseError(
        f"RNNoise requires the managed or bundled rnnoise-cli executable at {rnnoise_path}. "
        "The runtime may still be downloading or missing; open Settings > Diagnostics to install or repair it."
    )


def find_dpdfnet_bundle() -> Path:
    """Return the bundled DPDFNet executable path."""
    managed = managed_tool_path("dpdfnet")
    if managed is not None:
        return managed
    managed_expected = expected_managed_tool_path("dpdfnet")
    bundled_expected = expected_bundled_tool_path("dpdfnet")
    if bundled_expected is not None and bundled_expected.is_file():
        return bundled_expected
    dpdfnet_path = managed_expected or bundled_expected
    if dpdfnet_path is None:
        raise MissingDpdfnetError(f"DPDFNet is not bundled for {platform_description()}.")
    raise MissingDpdfnetError(
        f"DPDFNet requires the managed or bundled dpdfnet executable at {dpdfnet_path}. "
        "The runtime may still be downloading or missing; open Settings > Diagnostics to install or repair it."
    )


def expected_bundled_spleeter_model_path(model_name: str) -> Path | None:
    """Return the expected bundled Sherpa Spleeter model path."""
    if current_platform_key() is None:
        return None
    return _PACKAGE_DIR / "bin" / "models" / "spleeter-2stems-fp16" / model_name


def find_spleeter_bundle() -> tuple[Path, Path, Path]:
    """Return bundled Sherpa Spleeter executable and model paths."""
    managed_executable = managed_tool_path("sherpa-spleeter")
    managed_vocals = runtime_manager.managed_spleeter_model_path(_PACKAGE_DIR, "vocals.fp16.onnx")
    managed_accompaniment = runtime_manager.managed_spleeter_model_path(_PACKAGE_DIR, "accompaniment.fp16.onnx")
    if managed_executable is not None and managed_vocals is not None and managed_accompaniment is not None:
        return managed_executable, managed_vocals, managed_accompaniment

    managed_expected = expected_managed_tool_path("sherpa-spleeter")
    bundled_expected = expected_bundled_tool_path("sherpa-spleeter")
    if bundled_expected is not None and bundled_expected.is_file():
        return (
            bundled_expected,
            _required_spleeter_model("vocals.fp16.onnx"),
            _required_spleeter_model("accompaniment.fp16.onnx"),
        )
    executable_path = managed_expected or bundled_expected
    if executable_path is None:
        raise MissingSpleeterError(f"Sherpa Spleeter is not bundled for {platform_description()}.")
    bundled = bundled_tool_path("sherpa-spleeter")
    if bundled is None:
        raise MissingSpleeterError(
            f"Voice Only requires the managed or bundled sherpa-spleeter executable at {executable_path}. "
            "The runtime may still be downloading or missing; open Settings > Diagnostics to install or repair it."
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
            f"Voice Only requires the managed or bundled Sherpa Spleeter model at {model_path}. "
            "The runtime may still be downloading or missing; open Settings > Diagnostics to install or repair it."
        )
    return model_path
