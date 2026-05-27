"""Filesystem paths for managed runtime assets."""

from __future__ import annotations

from pathlib import Path

from .runtime_manifest import RUNTIME_MANIFEST_PATH

USER_FILES_DIRNAME = "user_files"
RUNTIME_DIRNAME = "runtime"
RUNTIME_STATE_FILENAME = "runtime_state.json"
DOWNLOADS_DIRNAME = ".downloads"


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
