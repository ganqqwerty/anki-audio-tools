"""Managed runtime asset installation and lookup."""

from __future__ import annotations

import json
import os
import platform
import shutil
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .runtime_archive import extract_expected_files, verify_extracted_files
from .runtime_manifest import (
    RUNTIME_MANIFEST_PATH,
    RuntimeFile,
    RuntimeInstallError,
    RuntimeManifest,
    RuntimePack,
    expected_files,
    load_manifest,
    sha256_file,
    target_pack,
)

USER_FILES_DIRNAME = "user_files"
RUNTIME_DIRNAME = "runtime"
RUNTIME_STATE_FILENAME = "runtime_state.json"
DOWNLOADS_DIRNAME = ".downloads"
DOWNLOAD_TIMEOUT_SECONDS = 60
USER_AGENT = "anki-audio-quick-editor-runtime/1.0"

RUNTIME_SOURCE_MANAGED = "managed"
RUNTIME_PHASE_READY = "ready"
RUNTIME_PHASE_MISSING = "missing"
RUNTIME_PHASE_DOWNLOADING = "downloading"
RUNTIME_PHASE_ERROR = "error"
RUNTIME_PHASE_UNSUPPORTED = "unsupported"

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

_STATE_LOCK = threading.RLock()
_INSTALL_THREAD: threading.Thread | None = None
_LAST_STATUS: dict[str, Any] = {}


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


def runtime_manifest_path(addon_dir: Path) -> Path:
    return addon_dir / RUNTIME_MANIFEST_PATH


def user_files_dir(addon_dir: Path) -> Path:
    return addon_dir / USER_FILES_DIRNAME


def runtime_base_dir(addon_dir: Path) -> Path:
    return user_files_dir(addon_dir) / RUNTIME_DIRNAME


def runtime_state_path(addon_dir: Path) -> Path:
    return user_files_dir(addon_dir) / RUNTIME_STATE_FILENAME


def managed_runtime_root(addon_dir: Path, manifest_id: str) -> Path:
    return runtime_base_dir(addon_dir) / manifest_id


def read_state(addon_dir: Path) -> dict[str, Any]:
    """Read persisted runtime state."""
    path = runtime_state_path(addon_dir)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def managed_tool_path(addon_dir: Path, tool_name: str) -> Path | None:
    """Return a verified managed runtime tool path when available."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    manifest = load_manifest(addon_dir)
    if manifest is None or not is_runtime_ready(addon_dir, manifest=manifest):
        return None
    executable = _TOOL_EXECUTABLES.get(tool_name, {}).get(platform_key)
    if executable is None:
        return None
    path = managed_runtime_root(addon_dir, manifest.manifest_id) / platform_key / executable
    return path if path.is_file() else None


def expected_managed_tool_path(addon_dir: Path, tool_name: str) -> Path | None:
    """Return the expected managed runtime tool path, even if missing."""
    platform_key = current_platform_key()
    manifest = load_manifest(addon_dir)
    executable = _TOOL_EXECUTABLES.get(tool_name, {}).get(platform_key or "")
    if manifest is None or platform_key is None or executable is None:
        return None
    return managed_runtime_root(addon_dir, manifest.manifest_id) / platform_key / executable


def managed_spleeter_model_path(addon_dir: Path, model_name: str) -> Path | None:
    """Return a verified managed Spleeter model path when available."""
    manifest = load_manifest(addon_dir)
    if manifest is None or not is_runtime_ready(addon_dir, manifest=manifest):
        return None
    path = managed_runtime_root(addon_dir, manifest.manifest_id) / "models" / "spleeter-2stems-fp16" / model_name
    return path if path.is_file() else None


def expected_managed_spleeter_model_path(addon_dir: Path, model_name: str) -> Path | None:
    """Return the expected managed Spleeter model path, even if missing."""
    manifest = load_manifest(addon_dir)
    if manifest is None or current_platform_key() is None:
        return None
    return managed_runtime_root(addon_dir, manifest.manifest_id) / "models" / "spleeter-2stems-fp16" / model_name


def runtime_status(addon_dir: Path) -> dict[str, Any]:
    """Return the current managed runtime status."""
    platform_key = current_platform_key()
    if platform_key is None:
        return _status(RUNTIME_PHASE_UNSUPPORTED, platform_key="", message="Unsupported platform.")
    try:
        manifest = load_manifest(addon_dir)
    except RuntimeInstallError as exc:
        return _status(RUNTIME_PHASE_ERROR, platform_key=platform_key, error=str(exc))
    if manifest is None:
        return _status(RUNTIME_PHASE_MISSING, platform_key=platform_key, message="Runtime manifest is not packaged.")
    with _STATE_LOCK:
        if _INSTALL_THREAD is not None and _INSTALL_THREAD.is_alive():
            return dict(_LAST_STATUS)
        if (
            _LAST_STATUS.get("phase") == RUNTIME_PHASE_ERROR
            and _LAST_STATUS.get("runtime_manifest_id") == manifest.manifest_id
            and _LAST_STATUS.get("platform") == platform_key
        ):
            return dict(_LAST_STATUS)
    if is_runtime_ready(addon_dir, manifest=manifest, platform_key=platform_key):
        return _status(
            RUNTIME_PHASE_READY,
            manifest=manifest,
            platform_key=platform_key,
            runtime_root=str(managed_runtime_root(addon_dir, manifest.manifest_id)),
            message="Runtime is ready.",
        )
    return _status(
        RUNTIME_PHASE_MISSING,
        manifest=manifest,
        platform_key=platform_key,
        message="Runtime assets are not installed.",
    )


def ensure_runtime_async(
    addon_dir: Path,
    *,
    notify: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Start a background runtime install when needed and return current status."""
    global _INSTALL_THREAD
    with _STATE_LOCK:
        if _INSTALL_THREAD is not None and _INSTALL_THREAD.is_alive():
            return dict(_LAST_STATUS)
        status = runtime_status(addon_dir)
        if status["phase"] == RUNTIME_PHASE_READY:
            _LAST_STATUS.clear()
            _LAST_STATUS.update(status)
            return status
        if status["phase"] in {RUNTIME_PHASE_UNSUPPORTED, RUNTIME_PHASE_ERROR}:
            _LAST_STATUS.clear()
            _LAST_STATUS.update(status)
            return status
        if not status.get("runtime_manifest_id"):
            _LAST_STATUS.clear()
            _LAST_STATUS.update(status)
            return status

        thread = threading.Thread(
            target=_install_thread_main,
            args=(addon_dir, notify),
            daemon=True,
            name="aqe-runtime-install",
        )
        downloading = dict(status)
        downloading["phase"] = RUNTIME_PHASE_DOWNLOADING
        downloading["message"] = "Downloading Audio Quick Editor runtime assets..."
        _LAST_STATUS.clear()
        _LAST_STATUS.update(downloading)
        _notify(notify, downloading)
        _INSTALL_THREAD = thread
    thread.start()
    return downloading


def ensure_runtime(addon_dir: Path, *, progress: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Synchronously install or repair the managed runtime."""
    platform_key = current_platform_key()
    if platform_key is None:
        return _status(RUNTIME_PHASE_UNSUPPORTED, platform_key="", message="Unsupported platform.")
    manifest = load_manifest(addon_dir)
    if manifest is None:
        return _status(RUNTIME_PHASE_ERROR, platform_key=platform_key, error="Runtime manifest is not packaged.")
    if is_runtime_ready(addon_dir, manifest=manifest, platform_key=platform_key):
        return runtime_status(addon_dir)
    pack = target_pack(manifest, platform_key)
    if pack is None:
        return _status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=f"Runtime manifest has no download pack for {platform_key}.",
        )
    files = expected_files(manifest, platform_key)
    if not files:
        return _status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=f"Runtime manifest has no files for {platform_key}.",
        )

    try:
        _download_extract_promote(addon_dir, manifest, platform_key, pack, files, progress)
        _cleanup_old_runtimes(addon_dir, keep_manifest_id=manifest.manifest_id)
    except Exception as exc:
        return _status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=_friendly_install_error(exc),
        )
    return runtime_status(addon_dir)


def is_runtime_ready(
    addon_dir: Path,
    *,
    manifest: RuntimeManifest | None = None,
    platform_key: str | None = None,
) -> bool:
    """Return whether all files for the current platform are present and quick-checked."""
    platform_key = platform_key or current_platform_key()
    if platform_key is None:
        return False
    manifest = manifest or load_manifest(addon_dir)
    if manifest is None:
        return False
    if not _runtime_state_matches(read_state(addon_dir), manifest, platform_key):
        return False
    root = managed_runtime_root(addon_dir, manifest.manifest_id)
    return all(_runtime_file_quick_check(root, file_entry) for file_entry in expected_files(manifest, platform_key))


def _runtime_state_matches(state: dict[str, Any], manifest: RuntimeManifest, platform_key: str) -> bool:
    return state.get("runtime_manifest_id") == manifest.manifest_id and state.get("platform") == platform_key


def _runtime_file_quick_check(root: Path, file_entry: RuntimeFile) -> bool:
    path = root / file_entry.path
    return path.is_file() and (file_entry.size is None or path.stat().st_size == file_entry.size)


def _install_thread_main(addon_dir: Path, notify: Callable[[dict[str, Any]], None] | None) -> None:
    def progress(progress_status: dict[str, Any]) -> None:
        with _STATE_LOCK:
            _LAST_STATUS.clear()
            _LAST_STATUS.update(progress_status)
        _notify(notify, progress_status)

    final_status = ensure_runtime(addon_dir, progress=progress)
    with _STATE_LOCK:
        _LAST_STATUS.clear()
        _LAST_STATUS.update(final_status)
    _notify(notify, final_status)


def _download_extract_promote(
    addon_dir: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    pack: RuntimePack,
    files: list[RuntimeFile],
    progress: Callable[[dict[str, Any]], None] | None,
) -> None:
    base_dir = runtime_base_dir(addon_dir)
    downloads_dir = base_dir / DOWNLOADS_DIRNAME
    downloads_dir.mkdir(parents=True, exist_ok=True)
    archive_path = downloads_dir / pack.name
    _download_pack(pack, archive_path, manifest, platform_key, progress)
    extract_root = base_dir / f"{manifest.manifest_id}.extracting-{os.getpid()}-{int(time.time())}"
    shutil.rmtree(extract_root, ignore_errors=True)
    try:
        extract_expected_files(archive_path, extract_root, files)
        verify_extracted_files(extract_root, files)
        target_root = managed_runtime_root(addon_dir, manifest.manifest_id)
        if target_root.exists():
            shutil.rmtree(target_root)
        extract_root.replace(target_root)
        _write_ready_state(addon_dir, manifest, platform_key, files)
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)
        archive_path.with_suffix(archive_path.suffix + ".download").unlink(missing_ok=True)


def _download_pack(
    pack: RuntimePack,
    destination: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    progress: Callable[[dict[str, Any]], None] | None,
) -> None:
    if destination.is_file() and sha256_file(destination) == pack.sha256:
        return
    tmp_path = destination.with_suffix(destination.suffix + ".download")
    tmp_path.unlink(missing_ok=True)
    request = urllib.request.Request(pack.url, headers={"User-Agent": USER_AGENT})
    downloaded = 0
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response, tmp_path.open("wb") as handle:  # nosec B310
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if progress is not None and pack.size:
                    progress(
                        _status(
                            RUNTIME_PHASE_DOWNLOADING,
                            manifest=manifest,
                            platform_key=platform_key,
                            progress=min(99, int(downloaded * 100 / pack.size)),
                            message=f"Downloaded {downloaded // 1024} KB of runtime assets...",
                        )
                    )
    except (OSError, urllib.error.URLError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeInstallError(f"Runtime download failed: {exc}") from exc
    actual_sha = sha256_file(tmp_path)
    if actual_sha != pack.sha256:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeInstallError(
            f"Runtime pack checksum mismatch: expected {pack.sha256}, got {actual_sha}."
        )
    tmp_path.replace(destination)


def _write_ready_state(
    addon_dir: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    files: list[RuntimeFile],
) -> None:
    state = {
        "schema_version": 1,
        "runtime_manifest_id": manifest.manifest_id,
        "platform": platform_key,
        "runtime_root": str(managed_runtime_root(addon_dir, manifest.manifest_id)),
        "installed_files": {file_entry.path: file_entry.sha256 for file_entry in files},
    }
    path = runtime_state_path(addon_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _cleanup_old_runtimes(addon_dir: Path, *, keep_manifest_id: str) -> None:
    base_dir = runtime_base_dir(addon_dir)
    if not base_dir.is_dir():
        return
    for child in base_dir.iterdir():
        if child.name in {keep_manifest_id, DOWNLOADS_DIRNAME} or not child.is_dir():
            continue
        try:
            shutil.rmtree(child)
        except OSError:
            continue


def _status(
    phase: str,
    *,
    manifest: RuntimeManifest | None = None,
    platform_key: str,
    runtime_root: str = "",
    message: str = "",
    error: str = "",
    progress: int = 0,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "runtime_manifest_id": manifest.manifest_id if manifest is not None else "",
        "platform": platform_key,
        "runtime_root": runtime_root,
        "progress": progress,
        "message": message,
        "error": error,
    }


def _notify(notify: Callable[[dict[str, Any]], None] | None, status: dict[str, Any]) -> None:
    if notify is not None:
        notify(dict(status))


def _friendly_install_error(exc: BaseException) -> str:
    if isinstance(exc, RuntimeInstallError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"
