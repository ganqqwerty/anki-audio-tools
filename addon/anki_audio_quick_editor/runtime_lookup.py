"""Managed runtime path lookup and readiness checks."""

from __future__ import annotations

from pathlib import Path

from .runtime_manifest import (
    RuntimeFile,
    RuntimeManifest,
    expected_files,
    load_manifest,
)
from .runtime_paths import managed_runtime_root
from .runtime_platform import current_platform_key, tool_executable_name
from .runtime_state import read_state


def managed_tool_path(addon_dir: Path, tool_name: str) -> Path | None:
    """Return a verified managed runtime tool path when available."""
    platform_key = current_platform_key()
    if platform_key is None:
        return None
    manifest = load_manifest(addon_dir)
    if manifest is None or not is_runtime_ready(addon_dir, manifest=manifest):
        return None
    executable = tool_executable_name(tool_name, platform_key)
    if executable is None:
        return None
    path = managed_runtime_root(addon_dir, manifest.manifest_id) / platform_key / executable
    return path if path.is_file() else None


def expected_managed_tool_path(addon_dir: Path, tool_name: str) -> Path | None:
    """Return the expected managed runtime tool path, even if missing."""
    platform_key = current_platform_key()
    manifest = load_manifest(addon_dir)
    executable = tool_executable_name(tool_name, platform_key)
    if manifest is None or platform_key is None or executable is None:
        return None
    return managed_runtime_root(addon_dir, manifest.manifest_id) / platform_key / executable


def managed_spleeter_model_path(addon_dir: Path, model_name: str) -> Path | None:
    """Return a verified managed Spleeter model path when available."""
    return managed_model_path(addon_dir, "spleeter-2stems-fp16", model_name)


def expected_managed_spleeter_model_path(addon_dir: Path, model_name: str) -> Path | None:
    """Return the expected managed Spleeter model path, even if missing."""
    return expected_managed_model_path(addon_dir, "spleeter-2stems-fp16", model_name)


def managed_silero_vad_model_path(addon_dir: Path) -> Path | None:
    """Return a verified managed Silero VAD model path when available."""
    return managed_model_path(addon_dir, "silero-vad", "silero_vad.onnx")


def expected_managed_silero_vad_model_path(addon_dir: Path) -> Path | None:
    """Return the expected managed Silero VAD model path, even if missing."""
    return expected_managed_model_path(addon_dir, "silero-vad", "silero_vad.onnx")


def managed_model_path(addon_dir: Path, model_dir: str, model_name: str) -> Path | None:
    """Return a verified managed shared model path when available."""
    manifest = load_manifest(addon_dir)
    if manifest is None or not is_runtime_ready(addon_dir, manifest=manifest):
        return None
    path = managed_runtime_root(addon_dir, manifest.manifest_id) / "models" / model_dir / model_name
    return path if path.is_file() else None


def expected_managed_model_path(addon_dir: Path, model_dir: str, model_name: str) -> Path | None:
    """Return the expected managed shared model path, even if missing."""
    manifest = load_manifest(addon_dir)
    if manifest is None or current_platform_key() is None:
        return None
    return managed_runtime_root(addon_dir, manifest.manifest_id) / "models" / model_dir / model_name


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


def _runtime_state_matches(state: dict[str, object], manifest: RuntimeManifest, platform_key: str) -> bool:
    return state.get("runtime_manifest_id") == manifest.manifest_id and state.get("platform") == platform_key


def _runtime_file_quick_check(root: Path, file_entry: RuntimeFile) -> bool:
    path = root / file_entry.path
    return path.is_file() and (file_entry.size is None or path.stat().st_size == file_entry.size)
