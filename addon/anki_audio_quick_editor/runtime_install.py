"""Managed runtime installation and status orchestration."""

from __future__ import annotations

import os
import shutil
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .error_codes import AQE_RUNTIME_ASSET_MISSING, format_coded_message
from .runtime_archive import extract_expected_files, verify_extracted_files
from .runtime_lookup import is_runtime_ready
from .runtime_manifest import (
    RuntimeFile,
    RuntimeInstallError,
    RuntimeManifest,
    RuntimePack,
    expected_files,
    load_manifest,
    sha256_file,
    target_pack,
)
from .runtime_paths import DOWNLOADS_DIRNAME, managed_runtime_root, runtime_base_dir
from .runtime_platform import current_platform_key
from .runtime_state import (
    RUNTIME_PHASE_DOWNLOADING,
    RUNTIME_PHASE_ERROR,
    RUNTIME_PHASE_MISSING,
    RUNTIME_PHASE_READY,
    RUNTIME_PHASE_UNSUPPORTED,
    status,
    write_ready_state,
)
from .runtime_state import (
    notify as notify_runtime_status,
)

DOWNLOAD_TIMEOUT_SECONDS = 60
USER_AGENT = "anki-audio-quick-editor-runtime/1.0"

_STATE_LOCK = threading.RLock()
_INSTALL_THREAD: threading.Thread | None = None
_LAST_STATUS: dict[str, Any] = {}


def runtime_status(addon_dir: Path) -> dict[str, Any]:
    """Return the current managed runtime status."""
    platform_key = current_platform_key()
    if platform_key is None:
        return status(RUNTIME_PHASE_UNSUPPORTED, platform_key="", message="Unsupported platform.")
    try:
        manifest = load_manifest(addon_dir)
    except RuntimeInstallError as exc:
        return status(RUNTIME_PHASE_ERROR, platform_key=platform_key, error=str(exc))
    if manifest is None:
        return status(RUNTIME_PHASE_MISSING, platform_key=platform_key, message="Runtime manifest is not packaged.")
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
        return status(
            RUNTIME_PHASE_READY,
            manifest=manifest,
            platform_key=platform_key,
            runtime_root=str(managed_runtime_root(addon_dir, manifest.manifest_id)),
            message="Runtime is ready.",
        )
    return status(
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
        current_status = runtime_status(addon_dir)
        if current_status["phase"] == RUNTIME_PHASE_READY:
            _remember_status(current_status)
            return current_status
        if current_status["phase"] in {RUNTIME_PHASE_UNSUPPORTED, RUNTIME_PHASE_ERROR}:
            _remember_status(current_status)
            return current_status
        if not current_status.get("runtime_manifest_id"):
            _remember_status(current_status)
            return current_status

        thread = threading.Thread(
            target=_install_thread_main,
            args=(addon_dir, notify),
            daemon=True,
            name="aqe-runtime-install",
        )
        downloading = dict(current_status)
        downloading["phase"] = RUNTIME_PHASE_DOWNLOADING
        downloading["message"] = "Downloading Audio Quick Editor runtime assets..."
        _remember_status(downloading)
        notify_runtime_status(notify, downloading)
        _INSTALL_THREAD = thread
    thread.start()
    return downloading


def ensure_runtime(addon_dir: Path, *, progress: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Synchronously install or repair the managed runtime."""
    platform_key = current_platform_key()
    if platform_key is None:
        return status(RUNTIME_PHASE_UNSUPPORTED, platform_key="", message="Unsupported platform.")
    manifest = load_manifest(addon_dir)
    if manifest is None:
        return status(RUNTIME_PHASE_ERROR, platform_key=platform_key, error="Runtime manifest is not packaged.")
    if is_runtime_ready(addon_dir, manifest=manifest, platform_key=platform_key):
        return runtime_status(addon_dir)
    pack = target_pack(manifest, platform_key)
    if pack is None:
        return status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=f"Runtime manifest has no download pack for {platform_key}.",
        )
    files = expected_files(manifest, platform_key)
    if not files:
        return status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=f"Runtime manifest has no files for {platform_key}.",
        )

    try:
        _download_extract_promote(addon_dir, manifest, platform_key, pack, files, progress)
        _cleanup_old_runtimes(addon_dir, keep_manifest_id=manifest.manifest_id)
    except Exception as exc:
        return status(
            RUNTIME_PHASE_ERROR,
            manifest=manifest,
            platform_key=platform_key,
            error=_friendly_install_error(exc),
        )
    return runtime_status(addon_dir)


def _remember_status(payload: dict[str, Any]) -> None:
    _LAST_STATUS.clear()
    _LAST_STATUS.update(payload)


def _install_thread_main(addon_dir: Path, notify_fn: Callable[[dict[str, Any]], None] | None) -> None:
    def progress(progress_status: dict[str, Any]) -> None:
        with _STATE_LOCK:
            _remember_status(progress_status)
        notify_runtime_status(notify_fn, progress_status)

    final_status = ensure_runtime(addon_dir, progress=progress)
    with _STATE_LOCK:
        _remember_status(final_status)
    notify_runtime_status(notify_fn, final_status)


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
        write_ready_state(addon_dir, manifest, platform_key, files)
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
        with (
            urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response,  # nosec B310
            tmp_path.open("wb") as handle,
        ):
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if progress is not None and pack.size:
                    progress(
                        status(
                            RUNTIME_PHASE_DOWNLOADING,
                            manifest=manifest,
                            platform_key=platform_key,
                            progress=min(99, int(downloaded * 100 / pack.size)),
                            message=f"Downloaded {downloaded // 1024} KB of runtime assets...",
                        )
                    )
    except (OSError, urllib.error.URLError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeInstallError(_friendly_download_error(exc)) from exc
    actual_sha = sha256_file(tmp_path)
    if actual_sha != pack.sha256:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeInstallError(
            f"Runtime pack checksum mismatch: expected {pack.sha256}, got {actual_sha}."
        )
    tmp_path.replace(destination)


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


def _friendly_install_error(exc: BaseException) -> str:
    if isinstance(exc, RuntimeInstallError):
        return _runtime_asset_error(str(exc))
    return f"{type(exc).__name__}: {exc}"


def _friendly_download_error(exc: BaseException) -> str:
    reason = getattr(exc, "reason", exc)
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return _runtime_asset_error(
            "Runtime download timed out. Check your internet connection and whether a "
            "firewall, proxy, VPN, antivirus, or organization network policy is blocking "
            "Audio Quick Editor from downloading its runtime assets."
        )
    if isinstance(exc, urllib.error.HTTPError):
        return _runtime_asset_error(
            f"Runtime download failed with HTTP {exc.code}. If this keeps happening, "
            "check whether a firewall, proxy, VPN, antivirus, or organization network "
            "policy is blocking the runtime asset URL."
        )
    if isinstance(reason, OSError) and getattr(reason, "errno", None) in {13, 30}:
        return _runtime_asset_error(
            f"Runtime download could not write files: {reason}. Check permissions for "
            "Anki's add-ons folder and whether security software is blocking the add-on."
        )
    return _runtime_asset_error(
        f"Runtime download failed: {exc}. Check your internet connection and whether a "
        "firewall, proxy, VPN, antivirus, or organization network policy is blocking "
        "Audio Quick Editor from downloading its runtime assets."
    )


def _runtime_asset_error(message: str) -> str:
    return format_coded_message(AQE_RUNTIME_ASSET_MISSING, message)
