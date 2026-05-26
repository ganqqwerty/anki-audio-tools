"""Runtime archive extraction and verification helpers."""

from __future__ import annotations

import shutil
import stat
import zipfile
from pathlib import Path

from .runtime_manifest import (
    RuntimeFile,
    RuntimeInstallError,
    sha256_file,
    unsafe_relative_path,
)


def extract_expected_files(archive_path: Path, destination: Path, files: list[RuntimeFile]) -> None:
    """Extract exactly the files listed in the runtime manifest."""
    expected = {file_entry.path for file_entry in files}
    try:
        with zipfile.ZipFile(archive_path) as zf:
            _validate_archive_members(
                {name for name in zf.namelist() if not name.endswith("/")},
                expected,
            )
            for file_entry in files:
                _extract_runtime_file(zf, destination, file_entry)
    except zipfile.BadZipFile as exc:
        raise RuntimeInstallError("Runtime pack is not a valid zip archive.") from exc


def verify_extracted_files(root: Path, files: list[RuntimeFile]) -> None:
    """Verify extracted runtime files before promotion."""
    for file_entry in files:
        path = root / file_entry.path
        if not path.is_file():
            raise RuntimeInstallError(f"Extracted runtime file is missing: {file_entry.path}")
        if file_entry.size is not None and path.stat().st_size != file_entry.size:
            raise RuntimeInstallError(f"Extracted runtime file has wrong size: {file_entry.path}")
        actual_sha = sha256_file(path)
        if actual_sha != file_entry.sha256:
            raise RuntimeInstallError(f"Extracted runtime file checksum mismatch: {file_entry.path}")


def _validate_archive_members(actual: set[str], expected: set[str]) -> None:
    unsafe = [name for name in actual if unsafe_relative_path(name)]
    if unsafe:
        raise RuntimeInstallError(f"Runtime pack contains unsafe path: {unsafe[0]}")
    unknown = actual - expected
    if unknown:
        raise RuntimeInstallError(f"Runtime pack contains unexpected file: {sorted(unknown)[0]}")
    missing = expected - actual
    if missing:
        raise RuntimeInstallError(f"Runtime pack is missing file: {sorted(missing)[0]}")


def _extract_runtime_file(zf: zipfile.ZipFile, destination: Path, file_entry: RuntimeFile) -> None:
    target = destination / file_entry.path
    target.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(file_entry.path) as source, target.open("wb") as handle:
        shutil.copyfileobj(source, handle)
    if file_entry.executable:
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
