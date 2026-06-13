#!/usr/bin/env python3
"""Headless managed-runtime provisioning for development commands."""

from __future__ import annotations

import argparse
import importlib
import importlib.machinery
import json
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
HEADLESS_PACKAGE = "_aqe_runtime_headless"
RUNTIME_INSTALL_HINT = "Run: python scripts/dev.py runtime-install"
RUNTIME_PHASE_READY = "ready"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import (
    release_assets,
    release_runtime,
    release_runtime_metadata,
)


def stage_runtime_manifest(addon_dir: Path = ADDON_DIR) -> dict[str, Any]:
    """Write the ignored thin runtime manifest used by local development."""
    lock = release_assets.load_lock()
    metadata = release_runtime_metadata.load_runtime_release_lock()
    release_runtime_metadata.validate_runtime_release_metadata(metadata, lock)
    pack_metadata = release_runtime_metadata.runtime_pack_metadata_from_release(metadata)
    release_runtime.write_runtime_manifest(
        addon_dir / "bin",
        lock,
        runtime_pack_metadata=pack_metadata,
        runtime_file_metadata=release_runtime_metadata.file_metadata_by_path(pack_metadata),
    )
    manifest_path = addon_dir / "bin" / "runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_id = metadata.get("runtime_manifest_id")
    if manifest.get("runtime_manifest_id") != expected_manifest_id:
        raise release_assets.ReleaseAssetError(
            "generated runtime_manifest_id does not match runtime_release.lock.json"
        )
    return manifest


def load_runtime_manager(
    *,
    addon_dir: Path = ADDON_DIR,
    package_name: str = HEADLESS_PACKAGE,
) -> Any:
    """Load runtime_manager without executing the add-on package bootstrap."""
    _clear_headless_package(package_name)
    package = types.ModuleType(package_name)
    package.__file__ = str(addon_dir / "__init__.py")
    package.__package__ = package_name
    package.__path__ = [str(addon_dir)]  # type: ignore[attr-defined]
    package.__spec__ = importlib.machinery.ModuleSpec(
        package_name,
        loader=None,
        is_package=True,
    )
    sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.runtime_manager")


def install_runtime(addon_dir: Path = ADDON_DIR) -> int:
    """Install or repair the managed runtime through the shared runtime core."""
    try:
        stage_runtime_manifest(addon_dir)
        runtime_manager = load_runtime_manager(addon_dir=addon_dir)
        final_status = runtime_manager.ensure_runtime(
            addon_dir,
            progress=_print_progress,
            force_verify=True,
        )
    except Exception as exc:
        print(f"[runtime] ERROR: {exc}", file=sys.stderr)
        return 1
    return _finish_status(final_status)


def require_ready(addon_dir: Path = ADDON_DIR) -> int:
    """Return success only when the managed runtime is already ready."""
    try:
        stage_runtime_manifest(addon_dir)
        runtime_manager = load_runtime_manager(addon_dir=addon_dir)
        current_status = runtime_manager.runtime_status(addon_dir)
    except Exception as exc:
        print(f"[runtime] ERROR: {exc}", file=sys.stderr)
        print(f"[runtime] {RUNTIME_INSTALL_HINT}", file=sys.stderr)
        return 1
    if current_status.get("phase") != RUNTIME_PHASE_READY:
        _print_status(current_status, stream=sys.stderr)
        print(f"[runtime] Managed runtime is not ready. {RUNTIME_INSTALL_HINT}", file=sys.stderr)
        return 1
    _print_status(current_status)
    return 0


def _clear_headless_package(package_name: str) -> None:
    for module_name in list(sys.modules):
        if module_name == package_name or module_name.startswith(f"{package_name}."):
            del sys.modules[module_name]


def _print_progress(status: dict[str, Any]) -> None:
    progress = int(status.get("progress") or 0)
    step = str(status.get("step") or status.get("message") or "Runtime install")
    detail = str(status.get("detail") or "")
    suffix = f": {detail}" if detail else ""
    print(f"[runtime] {progress:3d}% {step}{suffix}", flush=True)


def _finish_status(status: dict[str, Any]) -> int:
    _print_status(status)
    if status.get("phase") == RUNTIME_PHASE_READY:
        return 0
    print(f"[runtime] Managed runtime install did not finish ready. {RUNTIME_INSTALL_HINT}", file=sys.stderr)
    return 1


def _print_status(status: dict[str, Any], *, stream: Any | None = None) -> None:
    stream = stream or sys.stdout
    phase = status.get("phase", "")
    platform = status.get("platform", "")
    manifest_id = status.get("runtime_manifest_id", "")
    root = status.get("runtime_root", "")
    message = status.get("error") or status.get("message") or ""
    print(
        f"[runtime] status phase={phase} platform={platform} "
        f"manifest={manifest_id} root={root}",
        file=stream,
    )
    if message:
        print(f"[runtime] {message}", file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install or check the managed development runtime.")
    parser.add_argument("action", choices=("install", "require-ready"))
    parser.add_argument(
        "--addon-dir",
        type=Path,
        default=ADDON_DIR,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    addon_dir = args.addon_dir.resolve()
    if args.action == "install":
        return install_runtime(addon_dir)
    return require_ready(addon_dir)


if __name__ == "__main__":
    raise SystemExit(main())
