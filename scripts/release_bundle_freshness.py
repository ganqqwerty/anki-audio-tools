"""Bundle freshness helpers for release packaging."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_dev_command(root: Path, *command: str) -> None:
    result = subprocess.run([sys.executable, "scripts/dev.py", *command], cwd=root, text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def run_checks(root: Path, *, full: bool) -> None:
    run_dev_command(root, "check")
    if full:
        run_dev_command(root, "test-e2e")
        run_dev_command(root, "sonar")


def build_required_artifacts(root: Path, addon_dir: Path) -> None:
    run_dev_command(root, "contracts-generate")
    run_dev_command(root, "build-ui")
    verify_bundle_fresh(root, addon_dir)


def verify_bundle_fresh(root: Path, addon_dir: Path) -> None:
    src_dir = root / "settings_ui" / "src"
    if not src_dir.is_dir():
        return
    bundle_specs = [
        ("settings", [src_dir / "App.svelte", src_dir / "main.ts", src_dir / "lib"], [addon_dir / "templates" / "settings" / "settings_bundle.js", addon_dir / "templates" / "settings" / "settings_bundle.css"]),
        ("editor", [src_dir / "editor-inline", src_dir / "lib"], [addon_dir / "templates" / "editor" / "editor_bundle.js", addon_dir / "templates" / "editor" / "editor_bundle.css"]),
        ("batch", [src_dir / "batch", src_dir / "lib"], [addon_dir / "templates" / "batch" / "batch_bundle.js", addon_dir / "templates" / "batch" / "batch_bundle.css"]),
    ]
    for label, source_paths, bundles in bundle_specs:
        missing = [bundle for bundle in bundles if not bundle.exists()]
        if missing:
            missing_paths = ", ".join(str(path.relative_to(root)) for path in missing)
            print(f"ERROR: {label} bundle missing files: {missing_paths}. Run: python3 scripts/dev.py build")
            sys.exit(1)
        newest_source = source_mtime(source_paths)
        stale = [bundle for bundle in bundles if newest_source > bundle.stat().st_mtime]
        if stale:
            stale_paths = ", ".join(str(path.relative_to(root)) for path in stale)
            print(f"ERROR: {label} bundle is stale: {stale_paths}. Run: python3 scripts/dev.py build")
            sys.exit(1)


def source_mtime(paths: list[Path]) -> float:
    newest = 0.0
    for path in paths:
        if path.is_file() and path.suffix in {".svelte", ".ts"}:
            newest = max(newest, path.stat().st_mtime)
        elif path.is_dir():
            newest = max(newest, max((child.stat().st_mtime for child in path.rglob("*") if child.suffix in {".svelte", ".ts"}), default=0.0))
    return newest
