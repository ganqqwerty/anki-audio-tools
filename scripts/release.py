#!/usr/bin/env python3
"""Build a validated .ankiaddon package for Anki Audio Quick Editor."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
DIST_DIR = ROOT / "dist"
INCLUDE_EXTENSIONS = {".py", ".html", ".json", ".pyi", ".typed", ".js", ".css"}
INCLUDE_DIRS = {"bin"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
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


def _run_checks() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dev.py", "check"],
        cwd=ROOT,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


def _verify_bundle_fresh() -> None:
    src_dir = ROOT / "settings_ui" / "src"
    bundle = ADDON_DIR / "templates" / "settings" / "settings_bundle.js"
    if not src_dir.is_dir():
        return
    if not bundle.exists():
        print("ERROR: settings bundle missing. Run: python3 scripts/dev.py build")
        sys.exit(1)
    bundle_mtime = bundle.stat().st_mtime
    newest_source = max(
        (path.stat().st_mtime for path in src_dir.rglob("*") if path.suffix in {".svelte", ".ts"}),
        default=0.0,
    )
    if newest_source > bundle_mtime:
        print("ERROR: settings bundle is stale. Run: python3 scripts/dev.py build")
        sys.exit(1)


def _should_include(path: Path) -> bool:
    if path.name == "meta.json" or "__pycache__" in path.parts:
        return False
    if path.suffix in {".pyc", ".so", ".pyd", ".c"}:
        return False
    rel = path.relative_to(ADDON_DIR)
    if rel.parts and rel.parts[0] in INCLUDE_DIRS:
        return True
    if rel.parts and rel.parts[0] == "vendor":
        return True
    return path.suffix in INCLUDE_EXTENSIONS


def _build_archive(version: str) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    archive = DIST_DIR / f"anki-audio-quick-editor-{version}.ankiaddon"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ADDON_DIR.rglob("*")):
            if path.is_file() and _should_include(path):
                zf.write(path, str(path.relative_to(ADDON_DIR)))
    return archive


def _validate_archive(archive: Path) -> None:
    names = zipfile.ZipFile(archive, "r").namelist()
    for required in ("__init__.py", "config.json"):
        if required not in names:
            print(f"VALIDATION ERROR: missing required file {required}")
            sys.exit(1)
    for name in names:
        if "__pycache__" in name or name.endswith((".pyc", ".so", ".pyd")):
            print(f"VALIDATION ERROR: unexpected file {name}")
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build .ankiaddon package")
    parser.add_argument("--version", help="Override version")
    parser.add_argument("--skip-checks", action="store_true", help="Skip validation commands")
    args = parser.parse_args()

    version = args.version or _read_pyproject_version()
    _verify_versions(version)

    if not args.skip_checks:
        _find_anki_python()
        _run_checks()
        _verify_bundle_fresh()

    archive = _build_archive(version)
    _validate_archive(archive)
    print(f"Done: {archive}")


if __name__ == "__main__":
    main()
