"""Managed runtime installation and status orchestration."""

from __future__ import annotations

import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import runtime_install_io
from .error_codes import AQE_RUNTIME_ASSET_MISSING, format_coded_message
from .runtime_archive import verify_extracted_files
from .runtime_lookup import is_runtime_ready
from .runtime_manifest import (
    RuntimeFile,
    RuntimeInstallError,
    RuntimeManifest,
    expected_files,
    load_manifest,
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
    clear_state,
    status,
)
from .runtime_state import (
    notify as notify_runtime_status,
)

DOWNLOAD_TIMEOUT_SECONDS = runtime_install_io.DOWNLOAD_TIMEOUT_SECONDS
USER_AGENT = runtime_install_io.USER_AGENT
RuntimeInstallCancelledError = runtime_install_io.RuntimeInstallCancelledError
download_extract_promote = runtime_install_io.download_extract_promote

_STATE_LOCK = threading.RLock()
_INSTALL_THREAD: threading.Thread | None = None
_LAST_STATUS: dict[str, Any] = {}
_INSTALL_LISTENERS: list[Callable[[dict[str, Any]], None]] = []


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
            current = dict(_LAST_STATUS)
            if notify is not None and notify not in _INSTALL_LISTENERS:
                _INSTALL_LISTENERS.append(notify)
                notify_runtime_status(notify, current)
            return current
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
            args=(addon_dir,),
            daemon=True,
            name="aqe-runtime-install",
        )
        downloading = dict(current_status)
        downloading["phase"] = RUNTIME_PHASE_DOWNLOADING
        downloading["message"] = "Downloading Audio Quick Editor runtime assets..."
        _remember_status(downloading)
        _INSTALL_LISTENERS.clear()
        if notify is not None:
            _INSTALL_LISTENERS.append(notify)
        _notify_install_listeners(downloading)
        _INSTALL_THREAD = thread
    thread.start()
    return downloading


def ensure_runtime(
    addon_dir: Path,
    *,
    progress: Callable[[dict[str, Any]], None] | None = None,
    cancel_event: threading.Event | None = None,
    force_verify: bool = False,
) -> dict[str, Any]:
    """Synchronously install or repair the managed runtime."""
    platform_key = current_platform_key()
    if platform_key is None:
        return status(RUNTIME_PHASE_UNSUPPORTED, platform_key="", message="Unsupported platform.")
    manifest = load_manifest(addon_dir)
    if manifest is None:
        return status(RUNTIME_PHASE_ERROR, platform_key=platform_key, error="Runtime manifest is not packaged.")
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

    _emit_progress(
        progress,
        manifest,
        platform_key,
        1,
        "Select runtime package",
        f"Manifest {manifest.manifest_id}; archive {pack.name}; URL {pack.url}",
    )
    if is_runtime_ready(addon_dir, manifest=manifest, platform_key=platform_key):
        ready_status = _handle_ready_runtime(
            addon_dir,
            manifest,
            platform_key,
            files,
            progress,
            cancel_event,
            force_verify=force_verify,
        )
        if ready_status is not None:
            return ready_status
    else:
        _emit_progress(
            progress,
            manifest,
            platform_key,
            8,
            "Check existing runtime",
            "Runtime assets are not installed or the ready state is missing.",
        )

    try:
        _check_cancel(cancel_event)
        download_extract_promote(
            addon_dir,
            manifest,
            platform_key,
            pack,
            files,
            lambda pct, step, detail: _emit_progress(
                progress,
                manifest,
                platform_key,
                pct,
                step,
                detail,
            ),
            lambda: _check_cancel(cancel_event),
        )
        _cleanup_old_runtimes(addon_dir, keep_manifest_id=manifest.manifest_id)
    except RuntimeInstallCancelledError:
        _emit_progress(
            progress,
            manifest,
            platform_key,
            0,
            "Cancelled",
            "Runtime installation was cancelled before completion.",
            phase=RUNTIME_PHASE_MISSING,
        )
        return status(
            RUNTIME_PHASE_MISSING,
            manifest=manifest,
            platform_key=platform_key,
            message="Runtime installation cancelled.",
        )
    except (OSError, RuntimeInstallError) as exc:
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


def _notify_install_listeners(payload: dict[str, Any]) -> None:
    with _STATE_LOCK:
        listeners = tuple(_INSTALL_LISTENERS)
    for listener in listeners:
        notify_runtime_status(listener, payload)


def _install_thread_main(addon_dir: Path) -> None:
    def progress(progress_status: dict[str, Any]) -> None:
        with _STATE_LOCK:
            _remember_status(progress_status)
        _notify_install_listeners(progress_status)

    final_status = ensure_runtime(addon_dir, progress=progress)
    with _STATE_LOCK:
        _remember_status(final_status)
    _notify_install_listeners(final_status)
    with _STATE_LOCK:
        _INSTALL_LISTENERS.clear()


def _handle_ready_runtime(
    addon_dir: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    files: list[RuntimeFile],
    progress: Callable[[dict[str, Any]], None] | None,
    cancel_event: threading.Event | None,
    *,
    force_verify: bool,
) -> dict[str, Any] | None:
    runtime_root = managed_runtime_root(addon_dir, manifest.manifest_id)
    _emit_progress(
        progress,
        manifest,
        platform_key,
        8,
        "Check existing runtime",
        f"Runtime state is ready at {runtime_root}.",
    )
    if not force_verify:
        return runtime_status(addon_dir)
    try:
        _check_cancel(cancel_event)
        _emit_progress(
            progress,
            manifest,
            platform_key,
            20,
            "Verify files",
            f"Checking size and SHA-256 for {len(files)} installed runtime files.",
        )
        verify_extracted_files(runtime_root, files)
    except RuntimeInstallCancelledError:
        return status(
            RUNTIME_PHASE_READY,
            manifest=manifest,
            platform_key=platform_key,
            runtime_root=str(runtime_root),
            message="Runtime verification cancelled; existing runtime was left unchanged.",
        )
    except (OSError, RuntimeInstallError) as exc:
        clear_state(addon_dir)
        _emit_progress(
            progress,
            manifest,
            platform_key,
            25,
            "Check existing runtime",
            f"Installed runtime failed verification and will be repaired: {exc}",
        )
        return None
    _emit_progress(
        progress,
        manifest,
        platform_key,
        100,
        "Ready",
        f"Runtime files are verified at {runtime_root}.",
        phase=RUNTIME_PHASE_READY,
    )
    return runtime_status(addon_dir)


def _emit_progress(
    progress: Callable[[dict[str, Any]], None] | None,
    manifest: RuntimeManifest,
    platform_key: str,
    pct: int,
    step: str,
    detail: str,
    *,
    phase: str = RUNTIME_PHASE_DOWNLOADING,
) -> None:
    if progress is None:
        return
    payload = status(
        phase,
        manifest=manifest,
        platform_key=platform_key,
        progress=max(0, min(100, pct)),
        message=step,
    )
    payload["step"] = step
    payload["detail"] = detail
    progress(payload)


def _check_cancel(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeInstallCancelledError("Runtime installation cancelled.")


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
    return _runtime_asset_error(runtime_install_io.friendly_download_error(exc))


def _runtime_asset_error(message: str) -> str:
    return format_coded_message(AQE_RUNTIME_ASSET_MISSING, message)
