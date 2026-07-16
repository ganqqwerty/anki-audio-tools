"""Executable and bundled audio tool discovery."""

from __future__ import annotations

import platform
import shutil
from collections.abc import Callable
from pathlib import Path

from . import runtime_manager
from .error_codes import AQE_RUNTIME_ASSET_MISSING, format_coded_message
from .errors import (
    MissingDeepFilterError,
    MissingDpdfnetError,
    MissingFfmpegError,
    MissingRnnoiseError,
    MissingSileroVadError,
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
    "silero-vad": {
        "macos-arm64": "silero-vad",
        "macos-x86_64": "silero-vad",
        "windows-x86_64": "silero-vad.exe",
    },
}


def _runtime_repair_message(message: str) -> str:
    return format_coded_message(
        AQE_RUNTIME_ASSET_MISSING,
        f"{message} Open Settings > Diagnostics and click Install/Repair Runtime.",
    )


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
        _runtime_repair_message(
            "Audio Quick Editor requires ffmpeg. Configure an ffmpeg path, make ffmpeg "
            "available in PATH, or repair the managed runtime."
        )
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
        _runtime_repair_message(
            "DeepFilterNet's deep-filter executable is required for Standard denoise. "
            "Make deep-filter available in PATH or repair the managed runtime."
        )
    )


def _bundled_deep_filter_path() -> Path | None:
    return bundled_tool_path("deep-filter")


def expected_bundled_rnnoise_dir() -> Path | None:
    """Return the expected bundled RNNoise directory for the current platform."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    return _PACKAGE_DIR / "bin" / platform_key


def find_rnnoise_bundle(
    *,
    get_expected_bundled_tool_path: Callable[..., Path | None] | None = None,
) -> Path:
    """Return the bundled RNNoise executable path."""
    get_expected_bundled_tool_path = (
        get_expected_bundled_tool_path or expected_bundled_tool_path
    )
    managed = managed_tool_path("rnnoise-cli")
    if managed is not None:
        return managed
    managed_expected = expected_managed_tool_path("rnnoise-cli")
    bundled_expected = get_expected_bundled_tool_path("rnnoise-cli")
    if bundled_expected is not None and bundled_expected.is_file():
        return bundled_expected
    rnnoise_path = managed_expected or bundled_expected
    if rnnoise_path is None:
        raise MissingRnnoiseError(f"RNNoise is not bundled for {platform_description()}.")
    bundled = bundled_tool_path("rnnoise-cli")
    if bundled is not None:
        return bundled
    raise MissingRnnoiseError(
        _runtime_repair_message(
            f"RNNoise requires the managed or bundled rnnoise-cli executable at {rnnoise_path}."
        )
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
        _runtime_repair_message(
            f"DPDFNet requires the managed or bundled dpdfnet executable at {dpdfnet_path}."
        )
    )


def expected_bundled_spleeter_model_path(model_name: str) -> Path | None:
    """Return the expected bundled Sherpa Spleeter model path."""
    if current_platform_key() is None:
        return None
    return _PACKAGE_DIR / "bin" / "models" / "spleeter-2stems-fp16" / model_name


def _managed_spleeter_bundle() -> tuple[Path, Path, Path] | None:
    managed_executable = managed_tool_path("sherpa-spleeter")
    managed_vocals = runtime_manager.managed_spleeter_model_path(_PACKAGE_DIR, "vocals.fp16.onnx")
    managed_accompaniment = runtime_manager.managed_spleeter_model_path(_PACKAGE_DIR, "accompaniment.fp16.onnx")
    if managed_executable is not None and managed_vocals is not None and managed_accompaniment is not None:
        return managed_executable, managed_vocals, managed_accompaniment
    return None


def find_spleeter_bundle(
    *,
    get_expected_bundled_tool_path: Callable[..., Path | None] | None = None,
    get_expected_bundled_spleeter_model_path: Callable[..., Path | None] | None = None,
) -> tuple[Path, Path, Path]:
    """Return bundled Sherpa Spleeter executable and model paths."""
    managed = _managed_spleeter_bundle()
    if managed is not None:
        return managed
    get_tool = get_expected_bundled_tool_path or expected_bundled_tool_path
    get_model = (
        get_expected_bundled_spleeter_model_path
        or expected_bundled_spleeter_model_path
    )
    managed_expected = expected_managed_tool_path("sherpa-spleeter")
    bundled_expected = get_tool("sherpa-spleeter")
    if bundled_expected is not None and bundled_expected.is_file():
        return (
            bundled_expected,
            _required_spleeter_model("vocals.fp16.onnx", locate_model=get_model),
            _required_spleeter_model("accompaniment.fp16.onnx", locate_model=get_model),
        )
    executable_path = managed_expected or bundled_expected
    if executable_path is None:
        raise MissingSpleeterError(f"Sherpa Spleeter is not bundled for {platform_description()}.")
    bundled = bundled_tool_path("sherpa-spleeter")
    if bundled is None:
        raise MissingSpleeterError(
            _runtime_repair_message(
                f"Voice Only requires the managed or bundled sherpa-spleeter executable at {executable_path}."
            )
        )
    spleeter_path = bundled

    return (
        spleeter_path,
        _required_spleeter_model("vocals.fp16.onnx", locate_model=get_model),
        _required_spleeter_model("accompaniment.fp16.onnx", locate_model=get_model),
    )


def expected_bundled_silero_vad_model_path() -> Path | None:
    """Return the expected bundled Silero VAD model path."""
    if current_platform_key() is None:
        return None
    return _PACKAGE_DIR / "bin" / "models" / "silero-vad" / "silero_vad.onnx"


def find_silero_vad_bundle(
    *,
    get_expected_bundled_tool_path: Callable[..., Path | None] | None = None,
    get_expected_bundled_silero_vad_model_path: Callable[..., Path | None] | None = None,
) -> tuple[Path, Path]:
    """Return bundled Sherpa ONNX Silero VAD executable and model paths."""
    get_tool = get_expected_bundled_tool_path or expected_bundled_tool_path
    get_model = (
        get_expected_bundled_silero_vad_model_path
        or expected_bundled_silero_vad_model_path
    )
    managed_executable = managed_tool_path("silero-vad")
    managed_model = runtime_manager.managed_silero_vad_model_path(_PACKAGE_DIR)
    if managed_executable is not None and managed_model is not None:
        return managed_executable, managed_model
    if managed_executable is not None:
        expected_model = runtime_manager.expected_managed_silero_vad_model_path(_PACKAGE_DIR)
        raise MissingSileroVadError(
            _runtime_repair_message(f"Silero VAD requires the managed model at {expected_model}.")
        )

    managed_expected = expected_managed_tool_path("silero-vad")
    bundled_expected = get_tool("silero-vad")
    if bundled_expected is not None and bundled_expected.is_file():
        return bundled_expected, _required_silero_vad_model(
            locate_model=get_model
        )
    executable_path = managed_expected or bundled_expected
    if executable_path is None:
        raise MissingSileroVadError(f"Silero VAD is not bundled for {platform_description()}.")
    raise MissingSileroVadError(
        _runtime_repair_message(
            f"Silero VAD requires the managed or bundled silero-vad executable at {executable_path}."
        )
    )


def _required_spleeter_model(
    model_name: str,
    *,
    locate_model: Callable[..., Path | None] | None = None,
) -> Path:
    locate_model = locate_model or expected_bundled_spleeter_model_path
    model_path = locate_model(model_name)
    if model_path is None:
        raise MissingSpleeterError(f"Sherpa Spleeter models are not bundled for {platform_description()}.")
    if not model_path.is_file():
        raise MissingSpleeterError(
            _runtime_repair_message(
                f"Voice Only requires the managed or bundled Sherpa Spleeter model at {model_path}."
            )
        )
    return model_path


def _required_silero_vad_model(
    *,
    locate_model: Callable[..., Path | None] | None = None,
) -> Path:
    locate_model = locate_model or expected_bundled_silero_vad_model_path
    model_path = locate_model()
    if model_path is None:
        raise MissingSileroVadError(f"Silero VAD model is not bundled for {platform_description()}.")
    if not model_path.is_file():
        raise MissingSileroVadError(
            _runtime_repair_message(f"Silero VAD requires the managed or bundled model at {model_path}.")
        )
    return model_path
