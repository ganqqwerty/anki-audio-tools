"""Silero VAD release asset preparation."""

from __future__ import annotations

import shutil
import stat
import tempfile
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.release_asset_common import (
    ReleaseAssetError,
    _download_verified,
    _required_https_url,
    _required_sha256,
    _required_string,
    _safe_archive_member,
    _shared_file_entry,
    _tool_entry,
    _validate_target,
    tracked_runtime_file_path,
    tracked_shared_asset_path,
    tracked_tool_binary_path,
    validate_lock,
)
from scripts.release_sherpa_assets import _extract_tar_member, _run_smoke_command

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".release-assets"
ADDON_BIN_DIR = ROOT / "addon" / "anki_audio_quick_editor" / "bin"
SMOKE_TIMEOUT_SECONDS = 60


def fetch_silero_vad(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch locked Sherpa ONNX VAD executables and shared runtime files."""

    validate_lock(lock)
    fetched: list[Path] = []
    for target in target_keys:
        _validate_target(target)
        entry = _tool_entry(lock, target, "silero-vad")
        archive_url = _required_https_url(entry, "core_archive_url", target, "silero-vad")
        archive_sha = _required_sha256(entry, "core_archive_sha256", target, "silero-vad")
        archive_path = _silero_archive_path(cache_dir, target, archive_url)
        _download_verified(archive_url, archive_path, archive_sha)

        executable_member = _safe_archive_member(_required_string(entry, "archive_member", target, "silero-vad"))
        destination = tracked_tool_binary_path(addon_bin_dir, target, entry)
        _extract_tar_member(archive_path, executable_member, destination)
        if not target.startswith("windows-"):
            destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _verify_extracted_sha(destination, entry.get("sha256"), f"{target}/silero-vad")
        fetched.append(destination)

        for file_entry in entry.get("runtime_files", []):
            archive_member = _safe_archive_member(
                _required_runtime_string(file_entry, "archive_member", target, "silero-vad")
            )
            runtime_destination = tracked_runtime_file_path(addon_bin_dir, target, file_entry)
            _extract_tar_member(archive_path, archive_member, runtime_destination)
            _verify_extracted_sha(
                runtime_destination,
                file_entry.get("sha256"),
                f"{target}/silero-vad/{file_entry['path']}",
            )
            fetched.append(runtime_destination)
    return fetched


def fetch_silero_vad_model(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch the locked shared Silero VAD ONNX model."""

    validate_lock(lock)
    entry = _shared_file_entry(lock, "silero-vad-model")
    download_url = _required_shared_https_url(entry, "download_url", "silero-vad-model")
    download_sha = _required_shared_sha256(entry, "download_sha256", "silero-vad-model")
    source_path = _model_download_path(cache_dir, download_url)
    _download_verified(download_url, source_path, download_sha)
    destination = tracked_shared_asset_path(addon_bin_dir, entry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    _verify_extracted_sha(destination, entry.get("sha256"), "shared/silero-vad-model")
    return [destination]


def append_silero_vad_smoke_report(
    lock: dict[str, Any],
    *,
    addon_bin_dir: Path,
    target_keys: list[str],
    current_target: str,
    reports: list[str],
    errors: list[str],
) -> None:
    """Run a tiny current-target Silero VAD smoke check."""

    if current_target not in target_keys:
        return
    paths = _silero_smoke_paths(lock, addon_bin_dir, current_target)
    missing = [label for label, path in paths.items() if not path.is_file()]
    if missing:
        return
    try:
        _run_silero_smoke(paths)
    except ReleaseAssetError as exc:
        message = exc.args[0] if exc.args and isinstance(exc.args[0], str) else exc.__class__.__name__
        errors.append(f"{current_target}/silero-vad: smoke failed: {message}")
        return
    reports.append(f"{current_target}/silero-vad: smoke ok: wrote vad.wav")


def _silero_smoke_paths(lock: dict[str, Any], addon_bin_dir: Path, target: str) -> dict[str, Path]:
    return {
        "silero-vad": tracked_tool_binary_path(addon_bin_dir, target, _tool_entry(lock, target, "silero-vad")),
        "model": tracked_shared_asset_path(addon_bin_dir, _shared_file_entry(lock, "silero-vad-model")),
    }


def _run_silero_smoke(paths: dict[str, Path]) -> None:
    with tempfile.TemporaryDirectory(prefix="aqe_silero_vad_smoke_") as work_dir_raw:
        work_dir = Path(work_dir_raw)
        input_wav = work_dir / "input.wav"
        output_wav = work_dir / "vad.wav"
        _write_silent_wav(input_wav)
        _run_smoke_command(
            (
                str(paths["silero-vad"]),
                f"--silero-vad-model={paths['model']}",
                "--silero-vad-threshold=0.5",
                "--silero-vad-min-silence-duration=0.3",
                "--silero-vad-min-speech-duration=0.1",
                "--vad-num-threads=1",
                "--print-args=false",
                str(input_wav),
                str(output_wav),
            ),
            "Silero VAD inference failed",
        )
        if not output_wav.is_file():
            raise ReleaseAssetError("Silero VAD did not write vad.wav")


def _write_silent_wav(path: Path) -> None:
    sample_rate = 16_000
    frame_count = sample_rate // 4
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frame_count)


def _silero_archive_path(cache_dir: Path, target: str, url: str) -> Path:
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"Silero VAD archive URL has no filename: {url}")
    return cache_dir / "sources" / "silero-vad" / f"{target}-{name}"


def _model_download_path(cache_dir: Path, url: str) -> Path:
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"Silero VAD model URL has no filename: {url}")
    return cache_dir / "sources" / "silero-vad" / name


def _verify_extracted_sha(path: Path, expected_sha: object, label: str) -> None:
    from scripts.release_asset_common import sha256_file

    if not expected_sha:
        return
    actual_sha = sha256_file(path)
    if actual_sha != expected_sha:
        raise ReleaseAssetError(f"{label}: extracted checksum mismatch (expected {expected_sha}, got {actual_sha})")


def _required_runtime_string(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ReleaseAssetError(f"{target}/{tool_name} runtime file must define {key}")
    return value


def _required_shared_https_url(entry: dict[str, Any], key: str, file_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.startswith("https://"):
        raise ReleaseAssetError(f"shared/{file_name} must define an https {key}")
    return value


def _required_shared_sha256(entry: dict[str, Any], key: str, file_name: str) -> str:
    value = entry.get(key)
    from scripts.release_asset_common import _is_sha256

    if not _is_sha256(value):
        raise ReleaseAssetError(f"shared/{file_name} must define {key}")
    return value
