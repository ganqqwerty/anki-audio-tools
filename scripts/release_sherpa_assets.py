"""Sherpa source-separation release asset preparation."""

from __future__ import annotations

import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.release_asset_common import (
    SHARED_FILE_NAMES,
    ReleaseAssetError,
    _download_verified,
    _is_sha256,
    _required_https_url,
    _required_sha256,
    _required_string,
    _safe_archive_member,
    _safe_relative_executable,
    _shared_file_entry,
    _tool_entry,
    _validate_target,
    runtime_file_path,
    sha256_file,
    shared_asset_path,
    tracked_shared_asset_path,
    tracked_tool_binary_path,
    tool_runtime_files,
    validate_lock,
)

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".release-assets"
SMOKE_INPUT_SECONDS = "0.5"
SMOKE_TIMEOUT_SECONDS = 60


def fetch_sherpa_spleeter(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    cache_dir: Path = CACHE_DIR,
) -> list[Path]:
    """Fetch Sherpa source-separation executable assets and runtime libraries."""

    validate_lock(lock)
    fetched: list[Path] = []
    for target in target_keys:
        _validate_target(target)
        entry = _tool_entry(lock, target, "sherpa-spleeter")
        archive_url = _required_https_url(entry, "core_archive_url", target, "sherpa-spleeter")
        archive_sha = _required_sha256(entry, "core_archive_sha256", target, "sherpa-spleeter")
        archive_path = _sherpa_archive_path(cache_dir, target, archive_url)
        _download_verified(archive_url, archive_path, archive_sha)
        destination = _asset_binary_path(cache_dir, target, entry)
        executable_member = _safe_archive_member(_required_string(entry, "archive_member", target, "sherpa-spleeter"))
        _extract_tar_member(archive_path, executable_member, destination)
        if not target.startswith("windows-"):
            destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _verify_optional_extracted_sha(destination, entry.get("sha256"), f"{target}/sherpa-spleeter")
        fetched.append(destination)
        fetched.extend(_fetch_sherpa_runtime_files(lock, cache_dir, archive_path, target))
    return fetched


def fetch_spleeter_models(lock: dict[str, Any], *, cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch shared Sherpa Spleeter model files."""

    validate_lock(lock)
    fetched: list[Path] = []
    for file_name in SHARED_FILE_NAMES:
        entry = _shared_file_entry(lock, file_name)
        archive_url = _required_shared_https_url(entry, "download_url", file_name)
        archive_sha = _required_shared_sha256(entry, "download_sha256", file_name)
        archive_member = _safe_archive_member(_required_shared_string(entry, "archive_member", file_name))
        archive_path = _shared_archive_path(cache_dir, "spleeter", archive_url)
        _download_verified(archive_url, archive_path, archive_sha)
        destination = shared_asset_path(cache_dir, entry)
        _extract_tar_member(archive_path, archive_member, destination)
        _verify_optional_extracted_sha(destination, entry.get("sha256"), f"shared/{file_name}")
        fetched.append(destination)
    return fetched


def append_sherpa_spleeter_smoke_report(
    lock: dict[str, Any],
    *,
    cache_dir: Path,
    addon_bin_dir: Path,
    target_keys: list[str],
    current_target: str,
    reports: list[str],
    errors: list[str],
) -> None:
    """Run a tiny current-target Spleeter inference smoke check."""

    if current_target not in target_keys:
        return
    paths = _spleeter_smoke_paths(lock, cache_dir, addon_bin_dir, current_target)
    missing = [label for label, path in paths.items() if not path.is_file()]
    if missing:
        return
    try:
        _run_spleeter_smoke(paths)
    except ReleaseAssetError as exc:
        message = exc.args[0] if exc.args and isinstance(exc.args[0], str) else exc.__class__.__name__
        errors.append(f"{current_target}/sherpa-spleeter: smoke failed: {message}")
        return
    reports.append(f"{current_target}/sherpa-spleeter: smoke ok: wrote vocals.wav")


def _fetch_sherpa_runtime_files(
    lock: dict[str, Any],
    cache_dir: Path,
    archive_path: Path,
    target: str,
) -> list[Path]:
    fetched: list[Path] = []
    for file_entry in tool_runtime_files(lock, target, "sherpa-spleeter"):
        archive_member = _safe_archive_member(
            _required_runtime_string(file_entry, "archive_member", target, "sherpa-spleeter")
        )
        destination = runtime_file_path(cache_dir, target, file_entry)
        _extract_tar_member(archive_path, archive_member, destination)
        label = f"{target}/sherpa-spleeter/{file_entry['path']}"
        _verify_optional_extracted_sha(destination, file_entry.get("sha256"), label)
        fetched.append(destination)
    return fetched


def _spleeter_smoke_paths(lock: dict[str, Any], cache_dir: Path, addon_bin_dir: Path, target: str) -> dict[str, Path]:
    return {
        "ffmpeg": _asset_binary_path(cache_dir, target, _tool_entry(lock, target, "ffmpeg")),
        "sherpa-spleeter": tracked_tool_binary_path(addon_bin_dir, target, _tool_entry(lock, target, "sherpa-spleeter")),
        "vocals-model": tracked_shared_asset_path(addon_bin_dir, _shared_file_entry(lock, "spleeter-vocals")),
        "accompaniment-model": tracked_shared_asset_path(addon_bin_dir, _shared_file_entry(lock, "spleeter-accompaniment")),
    }


def _run_spleeter_smoke(paths: dict[str, Path]) -> None:
    with tempfile.TemporaryDirectory(prefix="aqe_spleeter_smoke_") as work_dir_raw:
        work_dir = Path(work_dir_raw)
        input_wav = work_dir / "input.wav"
        vocals_wav = work_dir / "vocals.wav"
        accompaniment_wav = work_dir / "accompaniment.wav"
        _run_smoke_command(
            (
                str(paths["ffmpeg"]),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={SMOKE_INPUT_SECONDS}",
                "-ac",
                "2",
                "-ar",
                "44100",
                "-codec:a",
                "pcm_s16le",
                str(input_wav),
            ),
            "ffmpeg sine input generation failed",
        )
        _run_smoke_command(
            (
                str(paths["sherpa-spleeter"]),
                f"--spleeter-vocals={paths['vocals-model']}",
                f"--spleeter-accompaniment={paths['accompaniment-model']}",
                f"--input-wav={input_wav}",
                f"--output-vocals-wav={vocals_wav}",
                f"--output-accompaniment-wav={accompaniment_wav}",
                "--num-threads=1",
            ),
            "Sherpa Spleeter inference failed",
        )
        if not vocals_wav.is_file():
            raise ReleaseAssetError("Sherpa Spleeter did not write vocals.wav")
        if not accompaniment_wav.is_file():
            raise ReleaseAssetError("Sherpa Spleeter did not write accompaniment.wav")


def _run_smoke_command(command: tuple[str, ...], failure_label: str) -> None:
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=SMOKE_TIMEOUT_SECONDS,
            check=False,
        )  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseAssetError(f"{failure_label}: {exc}") from exc
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        raise ReleaseAssetError(f"{failure_label}: {output or f'exited {result.returncode}'}")


def _asset_binary_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    executable = _safe_relative_executable(entry["executable"])
    return cache_dir / "bin" / target / executable


def _sherpa_archive_path(cache_dir: Path, target: str, url: str) -> Path:
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"Sherpa archive URL has no filename: {url}")
    return cache_dir / "sources" / "sherpa" / f"{target}-{name}"


def _shared_archive_path(cache_dir: Path, category: str, url: str) -> Path:
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"shared archive URL has no filename: {url}")
    return cache_dir / "sources" / category / name


def _extract_tar_member(archive_path: Path, archive_member: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".extract")
    try:
        with tarfile.open(archive_path, mode="r:*") as tf:
            member = tf.getmember(archive_member)
            if not member.isfile():
                raise ReleaseAssetError(f"{archive_path.name}:{archive_member} is not a regular file")
            source = tf.extractfile(member)
            if source is None:
                raise ReleaseAssetError(f"{archive_path.name}:{archive_member} could not be extracted")
            with source, tmp_path.open("wb") as target:
                shutil.copyfileobj(source, target)
    except KeyError as exc:
        tmp_path.unlink(missing_ok=True)
        raise ReleaseAssetError(f"{archive_path.name} is missing {archive_member}") from exc
    except tarfile.TarError as exc:
        tmp_path.unlink(missing_ok=True)
        raise ReleaseAssetError(f"{archive_path.name} is not a valid tar archive") from exc
    tmp_path.replace(destination)


def _verify_optional_extracted_sha(path: Path, expected_sha: object, label: str) -> None:
    if not expected_sha:
        return
    actual_sha = sha256_file(path)
    if actual_sha != expected_sha:
        raise ReleaseAssetError(f"{label}: extracted checksum mismatch (expected {expected_sha}, got {actual_sha})")


def _required_shared_string(entry: dict[str, Any], key: str, file_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ReleaseAssetError(f"shared/{file_name} must define {key}")
    return value


def _required_shared_https_url(entry: dict[str, Any], key: str, file_name: str) -> str:
    value = _required_shared_string(entry, key, file_name)
    if not value.startswith("https://"):
        raise ReleaseAssetError(f"shared/{file_name} must define an https {key}")
    return value


def _required_shared_sha256(entry: dict[str, Any], key: str, file_name: str) -> str:
    value = entry.get(key)
    if not _is_sha256(value):
        raise ReleaseAssetError(f"shared/{file_name} must define {key}")
    return value


def _required_runtime_string(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ReleaseAssetError(f"{target}/{tool_name} runtime file must define {key}")
    return value
