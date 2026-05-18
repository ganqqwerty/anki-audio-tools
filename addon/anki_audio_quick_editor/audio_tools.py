"""Executable and bundled audio tool discovery."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

from .errors import MissingDeepFilterError, MissingFfmpegError, MissingRnnoiseError

BUNDLED_DEEP_FILTER_VERSION = "0.5.6"
BUNDLED_RNNOISE_VERSION = "0.2"
FFMPEG_AUDIO_CODEC_ARG = "-codec:a"
WAV_MIME_TYPE = "audio/wav"
_PACKAGE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = _PACKAGE_DIR
_BUNDLED_DEEP_FILTER_BY_PLATFORM = {
    ("Darwin", "arm64"): _PACKAGE_DIR
    / "bin"
    / f"deep-filter-{BUNDLED_DEEP_FILTER_VERSION}-aarch64-apple-darwin",
}
_BUNDLED_RNNOISE_DIR_BY_PLATFORM = {
    ("Darwin", "arm64"): _PACKAGE_DIR / "bin" / "rnnoise-cli-macos-arm64",
}



def find_ffmpeg(configured_path: str = "") -> Path:  # pragma: no mutate
    """Return an ffmpeg executable path, honoring an optional config override."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is "
        "available in PATH, or configure its path in the add-on settings."
    )


def find_ffprobe(ffmpeg_path: Path) -> Path:
    """Return ffprobe next to ffmpeg or from PATH."""
    sibling = ffmpeg_path.with_name("ffprobe" + ffmpeg_path.suffix)
    if sibling.is_file():
        return sibling
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
    binary = _BUNDLED_DEEP_FILTER_BY_PLATFORM.get((platform.system(), platform.machine()))
    if binary is not None and binary.is_file():
        return binary
    return None


def expected_bundled_rnnoise_dir() -> Path | None:
    """Return the expected bundled RNNoise directory for the current platform."""
    return _BUNDLED_RNNOISE_DIR_BY_PLATFORM.get((platform.system(), platform.machine()))


def find_rnnoise_bundle() -> Path:
    """Return the bundled RNNoise executable path."""
    bundled_dir = expected_bundled_rnnoise_dir()
    if bundled_dir is None:
        raise MissingRnnoiseError("RNNoise is only bundled for macOS arm64 right now.")

    rnnoise_path = bundled_dir / "bin" / "rnnoise-cli"
    if not rnnoise_path.is_file():
        raise MissingRnnoiseError(
            "RNNoise requires the bundled rnnoise-cli executable. Reinstall the add-on to restore it."
        )
    return rnnoise_path
