#!/usr/bin/env python3
"""Native-platform release acceptance checks for a built archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import release_assets  # noqa: E402


class ReleaseAcceptanceError(RuntimeError):
    """Raised when a native release acceptance check fails."""


def _archive_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not find project version in pyproject.toml")
    return match.group(1)


def _run(command: list[str]) -> dict[str, object]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _extract_archive(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive, "r") as zf:
        for info in zf.infolist():
            extracted = Path(zf.extract(info, destination))
            mode = (info.external_attr >> 16) & 0o777
            if mode:
                extracted.chmod(mode)


def accept_archive(archive: Path, target: str) -> Path:
    if target == "current":
        target = release_assets.current_target_key()
    with tempfile.TemporaryDirectory(prefix="anki-audio-acceptance-") as tmp:
        extract_root = Path(tmp)
        _extract_archive(archive, extract_root)
        manifest = json.loads((extract_root / "bin" / "runtime_manifest.json").read_text(encoding="utf-8"))
        tool_reports = {}
        failures: list[str] = []
        for tool_name, entry in manifest["targets"][target]["tools"].items():
            tool_path = extract_root / "bin" / target / entry["executable"]
            args = entry.get("diagnostic_args", ["--version"])
            diagnostic = _run([str(tool_path), *args]) if tool_path.is_file() else None
            tool_reports[tool_name] = {
                "path": str(tool_path),
                "exists": tool_path.is_file(),
                "diagnostic": diagnostic,
            }
            if not tool_path.is_file():
                failures.append(f"{tool_name} missing at {tool_path}")
            elif diagnostic is None or diagnostic["returncode"] != 0:
                failures.append(f"{tool_name} diagnostic failed")
        report = {
            "archive": str(archive),
            "archive_sha256": _archive_sha256(archive),
            "target": target,
            "status": "failed" if failures else "passed",
            "failures": failures,
            "host": {
                "system": platform.system(),
                "machine": platform.machine(),
            },
            "tools": tool_reports,
        }
    output_dir = ROOT / "dist" / "release-acceptance" / _version()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{target}.json"
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise ReleaseAcceptanceError("; ".join(failures))
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run native release acceptance checks")
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--target", default="current")
    args = parser.parse_args()
    try:
        report = accept_archive(args.archive, args.target)
    except ReleaseAcceptanceError as exc:
        # noinspection PyStringConversionWithoutDunderMethod
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    else:
        print(report)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
