"""Release archive manifest file selection."""

from __future__ import annotations

from pathlib import Path

from scripts import release_asset_common, release_assets

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
INCLUDE_EXTENSIONS = {".py", ".html", ".json", ".pyi", ".typed", ".js", ".css"}
SOURCE_BIN_FILES = {
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
}
EXCLUDE_DIRS = {"aqe_artifacts"}
BASE_REQUIRED_ARCHIVE_FILES = (
    "__init__.py",
    "manifest.json",
    "release_info.json",
    "config.json",
    "config.schema.json",
    "contracts_generated.py",
    "templates/settings/settings_bundle.js",
    "templates/settings/settings_bundle.css",
    "templates/editor/editor_bundle.js",
    "templates/editor/editor_bundle.css",
    "templates/batch/batch_bundle.js",
    "templates/batch/batch_bundle.css",
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
    "bin/runtime_manifest.json",
)


def should_include(path: Path) -> bool:
    """Return whether a source-tree path should be packaged."""
    if path.name == "meta.json" or "__pycache__" in path.parts:
        return False
    if path.name == ".DS_Store" or path.suffix in {".pyc", ".so", ".pyd", ".c"}:
        return False
    rel = path.relative_to(ADDON_DIR)
    if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
        return False
    if rel.parts and rel.parts[0] == "bin":
        return rel.as_posix() in SOURCE_BIN_FILES
    if rel.parts and rel.parts[0] == "vendor":
        return True
    return path.suffix in INCLUDE_EXTENSIONS


def release_runtime_executables(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
) -> list[str]:
    """Return required runtime executable archive paths from the asset lock."""
    lock = lock or release_assets.load_lock()
    names: list[str] = []
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_asset_common.bundled_tool_names(
            release_assets.lock_tools(lock, target),
            include_ffmpeg=include_ffmpeg,
        ):
            executable = lock["targets"][target]["tools"][tool_name]["executable"]
            names.append(f"bin/{target}/{executable}")
    return sorted(names)


def release_runtime_shared_files(lock: dict | None = None) -> list[str]:
    """Return required shared runtime asset archive paths from the asset lock."""
    return release_asset_common.release_runtime_shared_files(lock or release_assets.load_lock())


def release_runtime_support_files(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
) -> list[str]:
    """Return required target-specific runtime support file archive paths."""
    return release_asset_common.release_runtime_support_files(
        lock or release_assets.load_lock(),
        target_keys=target_keys,
    )


def release_manifest_files(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
) -> list[str]:
    """Return archive files required for a self-sufficient release."""
    required = set(BASE_REQUIRED_ARCHIVE_FILES)
    if embed_runtime:
        required.update(
            release_runtime_executables(
                lock,
                target_keys=target_keys,
                include_ffmpeg=include_ffmpeg,
            )
        )
        required.update(release_runtime_support_files(lock, target_keys=target_keys))
        required.update(release_runtime_shared_files(lock))
    for path in ADDON_DIR.rglob("*"):
        if path.is_file() and should_include(path):
            required.add(path.relative_to(ADDON_DIR).as_posix())
    return sorted(required)
