"""Download, extraction, and promotion helpers for managed runtime installs."""

from __future__ import annotations

import os
import shutil
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from .runtime_archive import extract_expected_files, verify_extracted_files
from .runtime_manifest import (
    RuntimeFile,
    RuntimeInstallError,
    RuntimeManifest,
    RuntimePack,
    sha256_file,
)
from .runtime_paths import DOWNLOADS_DIRNAME, managed_runtime_root, runtime_base_dir
from .runtime_state import write_ready_state

DOWNLOAD_TIMEOUT_SECONDS = 60
USER_AGENT = "anki-audio-quick-editor-runtime/1.0"

ProgressEmitter = Callable[[int, str, str], None]
CancelChecker = Callable[[], None]


class RuntimeInstallCancelledError(RuntimeError):
    """Raised when the user cancels runtime installation."""


def download_extract_promote(
    addon_dir: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    pack: RuntimePack,
    files: list[RuntimeFile],
    progress: ProgressEmitter,
    check_cancel: CancelChecker,
) -> None:
    """Download, verify, extract, verify, and promote one runtime pack."""
    base_dir = runtime_base_dir(addon_dir)
    downloads_dir = base_dir / DOWNLOADS_DIRNAME
    downloads_dir.mkdir(parents=True, exist_ok=True)
    archive_path = downloads_dir / pack.name
    check_cancel()
    _download_pack(pack, archive_path, progress, check_cancel)
    progress(60, "Verify zip", f"Runtime archive size and SHA-256 verified at {archive_path}.")
    extract_root = base_dir / f"{manifest.manifest_id}.extracting-{os.getpid()}-{int(time.time())}"
    backup_root = base_dir / f"{manifest.manifest_id}.rollback-{os.getpid()}-{int(time.time())}"
    shutil.rmtree(extract_root, ignore_errors=True)
    shutil.rmtree(backup_root, ignore_errors=True)
    target_root = managed_runtime_root(addon_dir, manifest.manifest_id)
    promoted = False
    try:
        check_cancel()
        progress(68, "Unpack zip", f"Extracting {len(files)} expected files into {extract_root}.")
        extract_expected_files(archive_path, extract_root, files)
        check_cancel()
        progress(78, "Verify files", f"Checking size and SHA-256 for {len(files)} extracted runtime files.")
        verify_extracted_files(extract_root, files)
        check_cancel()
        progress(88, "Promote runtime", f"Promoting verified runtime into {target_root}.")
        if target_root.exists():
            target_root.replace(backup_root)
        extract_root.replace(target_root)
        promoted = True
        write_ready_state(addon_dir, manifest, platform_key, files)
        shutil.rmtree(backup_root, ignore_errors=True)
        progress(96, "Cleanup", "Runtime state written; cleaning temporary files.")
    except Exception:
        if promoted:
            shutil.rmtree(target_root, ignore_errors=True)
        if backup_root.exists():
            backup_root.replace(target_root)
        archive_path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)
        shutil.rmtree(backup_root, ignore_errors=True)
        archive_path.with_suffix(archive_path.suffix + ".download").unlink(missing_ok=True)


def _download_pack(
    pack: RuntimePack,
    destination: Path,
    progress: ProgressEmitter,
    check_cancel: CancelChecker,
) -> None:
    if destination.is_file():
        try:
            _verify_pack_file(pack, destination)
            progress(55, "Download zip", f"Reusing verified runtime archive at {destination}.")
            return
        except RuntimeInstallError:
            destination.unlink(missing_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".download")
    tmp_path.unlink(missing_ok=True)
    request = urllib.request.Request(pack.url, headers={"User-Agent": USER_AGENT})
    downloaded = 0
    progress(10, "Download zip", f"Downloading {pack.name} from {pack.url}.")
    try:
        with (
            urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response,  # nosec B310
            tmp_path.open("wb") as handle,
        ):
            while True:
                check_cancel()
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if pack.size:
                    progress(
                        min(55, max(10, int(downloaded * 55 / pack.size))),
                        "Download zip",
                        f"Downloaded {downloaded} of {pack.size} bytes.",
                    )
            check_cancel()
    except RuntimeInstallCancelledError:
        tmp_path.unlink(missing_ok=True)
        raise
    except (OSError, urllib.error.URLError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeInstallError(friendly_download_error(exc)) from exc
    try:
        _verify_pack_file(pack, tmp_path)
    except RuntimeInstallError:
        tmp_path.unlink(missing_ok=True)
        raise
    tmp_path.replace(destination)


def _verify_pack_file(pack: RuntimePack, path: Path) -> None:
    if pack.size is not None:
        actual_size = path.stat().st_size
        if actual_size != pack.size:
            raise RuntimeInstallError(
                f"Runtime pack size mismatch: expected {pack.size} bytes, got {actual_size} bytes."
            )
    actual_sha = sha256_file(path)
    if actual_sha != pack.sha256:
        raise RuntimeInstallError(
            f"Runtime pack checksum mismatch: expected {pack.sha256}, got {actual_sha}."
        )


def friendly_download_error(exc: BaseException) -> str:
    reason = getattr(exc, "reason", exc)
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return (
            "Runtime download timed out. Check your internet connection and whether a "
            "firewall, proxy, VPN, antivirus, or organization network policy is blocking "
            "Audio Quick Editor from downloading its runtime assets."
        )
    if isinstance(exc, urllib.error.HTTPError):
        return (
            f"Runtime download failed with HTTP {exc.code}. If this keeps happening, "
            "check whether a firewall, proxy, VPN, antivirus, or organization network "
            "policy is blocking the runtime asset URL."
        )
    if isinstance(reason, OSError) and getattr(reason, "errno", None) in {13, 30}:
        return (
            f"Runtime download could not write files: {reason}. Check permissions for "
            "Anki's add-ons folder and whether security software is blocking the add-on."
        )
    return (
        f"Runtime download failed: {exc}. Check your internet connection and whether a "
        "firewall, proxy, VPN, antivirus, or organization network policy is blocking "
        "Audio Quick Editor from downloading its runtime assets."
    )
