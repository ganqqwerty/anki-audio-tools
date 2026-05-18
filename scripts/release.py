#!/usr/bin/env python3
"""Build a validated .ankiaddon package for Anki Audio Quick Editor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
DIST_DIR = ROOT / "dist"
INCLUDE_EXTENSIONS = {".py", ".html", ".json", ".pyi", ".typed", ".js", ".css"}
SOURCE_BIN_FILES = {
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
}
EXCLUDE_DIRS = {"aqe_artifacts"}
BASE_REQUIRED_ARCHIVE_FILES = (
    "__init__.py",
    "manifest.json",
    "config.json",
    "config.schema.json",
    "contracts_generated.py",
    "templates/settings/settings_bundle.js",
    "templates/settings/settings_bundle.css",
    "templates/editor/editor_bundle.js",
    "templates/editor/editor_bundle.css",
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
    "bin/runtime_manifest.json",
)
WARN_ARCHIVE_BYTES = 125 * 1024 * 1024
FAIL_ARCHIVE_BYTES = 145 * 1024 * 1024

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_assets  # noqa: E402
from dev import _find_anki_python  # noqa: E402


def _read_pyproject_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    if match is None:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def _read_package_version() -> str:
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)"',
        (ADDON_DIR / "_version.py").read_text(),
        re.MULTILINE,
    )
    if match is None:
        print("ERROR: Could not find __version__ in _version.py")
        sys.exit(1)
    return match.group(1)


def _verify_versions(version: str) -> None:
    pyproject_ver = _read_pyproject_version()
    package_ver = _read_package_version()
    if pyproject_ver != version or package_ver != version:
        print(
            "ERROR: version mismatch "
            f"(pyproject={pyproject_ver!r}, package={package_ver!r}, requested={version!r})"
        )
        sys.exit(1)


def _run_dev_command(*command: str) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dev.py", *command],
        cwd=ROOT,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


def _run_checks(*, full: bool) -> None:
    _run_dev_command("check")
    if not full:
        return
    _run_dev_command("test-e2e")
    _run_dev_command("sonar")


def _source_mtime(paths: list[Path]) -> float:
    newest = 0.0
    for path in paths:
        if path.is_file() and path.suffix in {".svelte", ".ts"}:
            newest = max(newest, path.stat().st_mtime)
        elif path.is_dir():
            newest = max(
                newest,
                max(
                    (child.stat().st_mtime for child in path.rglob("*") if child.suffix in {".svelte", ".ts"}),
                    default=0.0,
                ),
            )
    return newest


def _verify_bundle_fresh() -> None:
    src_dir = ROOT / "settings_ui" / "src"
    if not src_dir.is_dir():
        return
    bundle_specs = [
        (
            "settings",
            [
                src_dir / "App.svelte",
                src_dir / "main.ts",
                src_dir / "lib",
            ],
            [
                ADDON_DIR / "templates" / "settings" / "settings_bundle.js",
                ADDON_DIR / "templates" / "settings" / "settings_bundle.css",
            ],
        ),
        (
            "editor",
            [
                src_dir / "editor-inline",
                src_dir / "lib",
            ],
            [
                ADDON_DIR / "templates" / "editor" / "editor_bundle.js",
                ADDON_DIR / "templates" / "editor" / "editor_bundle.css",
            ],
        ),
    ]
    for label, source_paths, bundles in bundle_specs:
        missing = [bundle for bundle in bundles if not bundle.exists()]
        if missing:
            missing_paths = ", ".join(str(path.relative_to(ROOT)) for path in missing)
            print(f"ERROR: {label} bundle missing files: {missing_paths}. Run: python3 scripts/dev.py build")
            sys.exit(1)
        newest_source = _source_mtime(source_paths)
        stale = [bundle for bundle in bundles if newest_source > bundle.stat().st_mtime]
        if stale:
            stale_paths = ", ".join(str(path.relative_to(ROOT)) for path in stale)
            print(f"ERROR: {label} bundle is stale: {stale_paths}. Run: python3 scripts/dev.py build")
            sys.exit(1)


def _build_required_artifacts() -> None:
    _run_dev_command("contracts-generate")
    _run_dev_command("build-ui")
    _verify_bundle_fresh()


def _should_include(path: Path) -> bool:
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
) -> list[str]:
    """Return required runtime executable archive paths from the asset lock."""
    lock = lock or release_assets.load_lock()
    names: list[str] = []
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            executable = lock["targets"][target]["tools"][tool_name]["executable"]
            names.append(f"bin/{target}/{executable}")
    return sorted(names)


def release_manifest_files(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
) -> list[str]:
    """Return archive files required for a self-sufficient release."""
    required = set(BASE_REQUIRED_ARCHIVE_FILES)
    required.update(release_runtime_executables(lock, target_keys=target_keys))
    for path in ADDON_DIR.rglob("*"):
        if path.is_file() and _should_include(path):
            required.add(path.relative_to(ADDON_DIR).as_posix())
    return sorted(required)


def _stage_source_tree(staging_dir: Path) -> None:
    for path in sorted(ADDON_DIR.rglob("*")):
        if path.is_file() and _should_include(path):
            target = staging_dir / path.relative_to(ADDON_DIR)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _write_runtime_manifest(
    staging_bin_dir: Path,
    lock: dict,
    *,
    target_keys: list[str] | None = None,
) -> None:
    selected_targets = target_keys or release_assets.lock_targets(lock)
    manifest = {
        "schema_version": lock["schema_version"],
        "release_ready": bool(lock.get("release_ready", False)),
        "targets": {
            target: {
                "tools": {
                    tool_name: {
                        "executable": lock["targets"][target]["tools"][tool_name]["executable"],
                        "sha256": lock["targets"][target]["tools"][tool_name].get("sha256"),
                        "diagnostic_args": lock["targets"][target]["tools"][tool_name].get("diagnostic_args"),
                    }
                    for tool_name in release_assets.lock_tools(lock, target)
                }
            }
            for target in selected_targets
        },
    }
    (staging_bin_dir / "runtime_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _stage_release_tree(
    staging_dir: Path,
    *,
    lock: dict,
    target_keys: list[str] | None = None,
) -> None:
    _stage_source_tree(staging_dir)
    staging_bin_dir = staging_dir / "bin"
    release_assets.stage_assets(lock, destination=staging_bin_dir, target_keys=target_keys)
    _write_runtime_manifest(staging_bin_dir, lock, target_keys=target_keys)


def _build_archive(version: str, staging_dir: Path, *, target_label: str = "all") -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    suffix = "" if target_label == "all" else f"-{target_label}"
    archive = DIST_DIR / f"anki-audio-quick-editor-{version}{suffix}.ankiaddon"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging_dir.rglob("*")):
            if path.is_file():
                zf.write(path, str(path.relative_to(staging_dir)))
    return archive


def _validate_archive(
    archive: Path,
    *,
    allow_large_archive: bool = False,
    lock: dict | None = None,
    target_keys: list[str] | None = None,
) -> None:
    lock = lock or release_assets.load_lock()
    with zipfile.ZipFile(archive, "r") as zf:
        infos = {info.filename: info for info in zf.infolist()}
        names = set(infos)
        for required in release_manifest_files(lock, target_keys=target_keys):
            if required not in names:
                _validation_error(f"missing required file {required}")
        for name in sorted(names):
            if _is_forbidden_archive_name(name):
                _validation_error(f"unexpected file {name}")
        _validate_runtime_matrix(zf, infos, lock, target_keys=target_keys)
        _validate_notices(zf, names)
    _validate_archive_size(archive, allow_large_archive=allow_large_archive)


def _validate_runtime_matrix(
    zf: zipfile.ZipFile,
    infos: dict[str, zipfile.ZipInfo],
    lock: dict,
    *,
    target_keys: list[str] | None = None,
) -> None:
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            entry = lock["targets"][target]["tools"][tool_name]
            executable = entry["executable"]
            name = f"bin/{target}/{executable}"
            if target.startswith("windows-") and not executable.endswith(".exe"):
                _validation_error(f"{name} must use a .exe filename for Windows")
            if target.startswith("macos-") and executable.endswith(".exe"):
                _validation_error(f"{name} must not use a .exe filename for macOS")
            if target.startswith("macos-") and not _zipinfo_has_executable_bit(infos[name]):
                _validation_error(f"{name} is missing executable mode bits")
            expected_sha = entry.get("sha256")
            if not expected_sha:
                _validation_error(f"{name} is missing sha256 in release_assets.lock.json")
            actual_sha = hashlib.sha256(zf.read(name)).hexdigest()
            if actual_sha != expected_sha:
                _validation_error(f"{name} checksum mismatch")


def _validate_notices(zf: zipfile.ZipFile, names: set[str]) -> None:
    notice_name = "bin/THIRD_PARTY_NOTICES.md"
    if notice_name not in names:
        _validation_error(f"missing required file {notice_name}")
    notice_text = zf.read(notice_name).decode("utf-8", errors="replace")
    for required in ("FFmpeg", "LAME", "DeepFilterNet", "RNNoise"):
        if required not in notice_text:
            _validation_error(f"{notice_name} is missing {required} notice")


def _validate_archive_size(archive: Path, *, allow_large_archive: bool) -> None:
    size = archive.stat().st_size
    if size > FAIL_ARCHIVE_BYTES and not allow_large_archive:
        _validation_error(
            f"archive is {size} bytes, above the {FAIL_ARCHIVE_BYTES} byte release gate"
        )
    if size > WARN_ARCHIVE_BYTES:
        print(f"WARNING: archive is {size} bytes, above the {WARN_ARCHIVE_BYTES} byte warning gate")


def _zipinfo_has_executable_bit(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o777
    return bool(mode & 0o111)


def _is_forbidden_archive_name(name: str) -> bool:
    parts = Path(name).parts
    if name == ".DS_Store" or name.endswith(".DS_Store"):
        return True
    if "node_modules" in parts or "__pycache__" in parts or "aqe_artifacts" in parts:
        return True
    if ".release-assets" in parts or name == "meta.json":
        return True
    return name.endswith((".pyc", ".so", ".pyd", ".tar", ".tar.gz", ".zip"))


def _validation_error(message: str) -> None:
    print(f"VALIDATION ERROR: {message}")
    sys.exit(1)


def _selected_release_targets(value: str, lock: dict) -> tuple[list[str] | None, str]:
    if value == "all":
        return None, "all"
    if value == "current":
        target = release_assets.current_target_key()
        return [target], target
    if value not in release_assets.lock_targets(lock):
        choices = ", ".join(["all", "current", *release_assets.lock_targets(lock)])
        print(f"ERROR: unknown release target {value!r}; expected one of {choices}")
        sys.exit(1)
    return [value], value


def main() -> None:
    parser = argparse.ArgumentParser(description="Build .ankiaddon package")
    parser.add_argument("--version", help="Override version")
    parser.add_argument(
        "--skip-quality-checks",
        action="store_true",
        help="Skip expensive QC, but still generate artifacts, stage assets, and validate the archive",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Deprecated alias for --skip-quality-checks",
    )
    parser.add_argument("--full", action="store_true", help="Run e2e tests and Sonar quality gate before packaging")
    parser.add_argument("--allow-large-archive", metavar="REASON", help="Allow archives above the hard size gate")
    parser.add_argument(
        "--target",
        default="all",
        help="Release target to package: all, current, macos-arm64, macos-x86_64, or windows-x86_64",
    )
    args = parser.parse_args()
    skip_quality_checks = args.skip_quality_checks or args.skip_checks
    if skip_quality_checks and args.full:
        parser.error("--full cannot be used with --skip-quality-checks")
    if args.allow_large_archive:
        print(f"Large archive override reason: {args.allow_large_archive}")

    version = args.version or _read_pyproject_version()
    _verify_versions(version)

    if not skip_quality_checks:
        _find_anki_python()
        _run_checks(full=args.full)
    _build_required_artifacts()
    lock = release_assets.load_lock()
    target_keys, target_label = _selected_release_targets(args.target, lock)

    with tempfile.TemporaryDirectory(prefix="anki-audio-release-") as tmp:
        staging_dir = Path(tmp) / "addon"
        try:
            _stage_release_tree(staging_dir, lock=lock, target_keys=target_keys)
        except release_assets.ReleaseAssetError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)
        archive = _build_archive(version, staging_dir, target_label=target_label)
    _validate_archive(
        archive,
        allow_large_archive=bool(args.allow_large_archive),
        lock=lock,
        target_keys=target_keys,
    )
    print(f"Done: {archive}")


if __name__ == "__main__":
    main()
