#!/usr/bin/env python3
"""Download and verify locked runtime Python wheels."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
DEFAULT_LOCK_PATH = ADDON_DIR / "vendor" / "wheels.lock.json"
DEFAULT_WHEELS_DIR = ADDON_DIR / "vendor" / "wheels"
CHUNK_SIZE = 1024 * 1024


class VendorWheelError(Exception):
    """Raised when the vendored wheel set does not match its lock file."""

    def __str__(self) -> str:
        """Return the stored validation detail."""
        return "\n".join(str(argument) for argument in self.args)


@dataclass(frozen=True)
class LockedWheel:
    """A single wheel pinned by the vendored wheel lock file."""

    target: str
    package: str
    version: str
    filename: str
    url: str
    sha256: str
    size: int
    tag: str

    def path(self, wheels_dir: Path = DEFAULT_WHEELS_DIR) -> Path:
        """Return the expected source-tree path for this wheel."""
        return wheels_dir / self.target / self.filename

    def archive_name(self) -> str:
        """Return the expected release archive path for this wheel."""
        return f"vendor/wheels/{self.target}/{self.filename}"


def load_lock(lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    """Read and minimally validate the vendored wheel lock file."""
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VendorWheelError(f"missing wheel lock file {lock_path}") from exc
    except json.JSONDecodeError as exc:
        raise VendorWheelError(f"{lock_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise VendorWheelError(f"{lock_path} must contain a JSON object")
    return data


def locked_wheels(lock: dict[str, Any] | None = None) -> tuple[LockedWheel, ...]:
    """Return locked wheels in deterministic target/package order."""
    lock = lock or load_lock()
    targets = lock.get("targets")
    if lock.get("schema_version") != 1:
        raise VendorWheelError("vendor/wheels.lock.json must declare schema_version 1")
    if not isinstance(targets, dict) or not targets:
        raise VendorWheelError("vendor/wheels.lock.json must include targets")
    wheels: list[LockedWheel] = []
    for target in sorted(targets):
        target_wheels = targets[target]
        if not isinstance(target_wheels, list) or not target_wheels:
            raise VendorWheelError(f"target {target} must contain a non-empty list")
        for index, entry in enumerate(target_wheels):
            wheels.append(_locked_wheel_from_entry(target, index, entry))
    return tuple(wheels)


def verify_wheels(
    *,
    lock_path: Path = DEFAULT_LOCK_PATH,
    wheels_dir: Path = DEFAULT_WHEELS_DIR,
) -> list[str]:
    """Return validation errors for the source-tree vendored wheel directory."""
    errors: list[str] = []
    try:
        wheels = locked_wheels(load_lock(lock_path))
    except VendorWheelError as exc:
        return [str(exc)]

    expected_paths = {wheel.path(wheels_dir) for wheel in wheels}
    for wheel in wheels:
        errors.extend(_validate_wheel_file(wheel.path(wheels_dir), wheel))

    if wheels_dir.exists():
        extra_wheels = sorted(wheels_dir.glob("*/*.whl"))
        errors.extend(
            f"unexpected unlocked wheel {path.relative_to(wheels_dir)}"
            for path in extra_wheels
            if path not in expected_paths
        )
    else:
        errors.append(f"missing wheel directory {wheels_dir}")
    return errors


def assert_wheels_verified(
    *,
    lock_path: Path = DEFAULT_LOCK_PATH,
    wheels_dir: Path = DEFAULT_WHEELS_DIR,
) -> None:
    """Raise if the vendored wheel directory differs from the lock file."""
    errors = verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir)
    if errors:
        raise VendorWheelError("\n".join(errors))


def download_wheels(
    *,
    lock_path: Path = DEFAULT_LOCK_PATH,
    wheels_dir: Path = DEFAULT_WHEELS_DIR,
    prune: bool = False,
) -> list[str]:
    """Download exact locked wheels and return verification errors."""
    try:
        wheels = locked_wheels(load_lock(lock_path))
    except VendorWheelError as exc:
        return [str(exc)]

    for wheel in wheels:
        destination = wheel.path(wheels_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".download")
        _download_file(wheel.url, temporary)
        errors = _validate_wheel_file(temporary, wheel)
        if errors:
            temporary.unlink(missing_ok=True)
            return errors
        temporary.replace(destination)

    if prune and wheels_dir.exists():
        expected_paths = {wheel.path(wheels_dir) for wheel in wheels}
        for path in sorted(wheels_dir.glob("*/*.whl")):
            if path not in expected_paths:
                path.unlink()
    return verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir)


def archive_errors(
    zf: zipfile.ZipFile,
    *,
    lock_path: Path = DEFAULT_LOCK_PATH,
) -> list[str]:
    """Return validation errors for vendored wheels inside a release archive."""
    errors: list[str] = []
    try:
        wheels = locked_wheels(load_lock(lock_path))
    except VendorWheelError as exc:
        return [str(exc)]

    names = set(zf.namelist())
    expected_names = {wheel.archive_name() for wheel in wheels}
    for wheel in wheels:
        archive_name = wheel.archive_name()
        if archive_name not in names:
            errors.append(f"missing locked wheel {archive_name}")
            continue
        data = zf.read(archive_name)
        errors.extend(_validate_wheel_bytes(archive_name, data, wheel))

    for name in sorted(names):
        if name.startswith("vendor/wheels/") and name.endswith(".whl"):
            if name not in expected_names:
                errors.append(f"unexpected unlocked wheel {name}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Command-line entrypoint for vendored wheel maintenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="Verify locked wheels")
    _add_paths_args(verify_parser)

    download_parser = subparsers.add_parser(
        "download",
        help="Download the exact wheel files pinned in wheels.lock.json",
    )
    _add_paths_args(download_parser)
    download_parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete wheel files that are not listed in wheels.lock.json",
    )

    args = parser.parse_args(argv)
    lock_path = Path(args.lock)
    wheels_dir = Path(args.wheels_dir)

    if args.command == "verify":
        errors = verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir)
    else:
        errors = download_wheels(
            lock_path=lock_path,
            wheels_dir=wheels_dir,
            prune=args.prune,
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Vendored wheels match addon/anki_audio_quick_editor/vendor/wheels.lock.json")
    return 0


def _add_paths_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--lock",
        default=str(DEFAULT_LOCK_PATH),
        help="Path to wheels.lock.json",
    )
    parser.add_argument(
        "--wheels-dir",
        default=str(DEFAULT_WHEELS_DIR),
        help="Directory containing platform wheel subdirectories",
    )


def _locked_wheel_from_entry(
    target: str,
    index: int,
    entry: object,
) -> LockedWheel:
    if not isinstance(entry, dict):
        raise VendorWheelError(f"target {target} entry {index} must be an object")
    values: dict[str, str] = {}
    for key in ("package", "version", "filename", "url", "sha256", "tag"):
        value = entry.get(key)
        if not isinstance(value, str) or not value:
            raise VendorWheelError(f"target {target} entry {index} missing {key}")
        values[key] = value
    size = entry.get("size")
    if not isinstance(size, int) or size <= 0:
        raise VendorWheelError(f"target {target} entry {index} missing size")
    filename = values["filename"]
    if not filename.endswith(".whl") or "/" in filename or "\\" in filename:
        raise VendorWheelError(f"target {target} entry {index} has invalid filename")
    sha256 = values["sha256"]
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        raise VendorWheelError(f"target {target} entry {index} has invalid sha256")
    return LockedWheel(
        target=target,
        package=values["package"],
        version=values["version"],
        filename=filename,
        url=values["url"],
        sha256=sha256,
        size=size,
        tag=values["tag"],
    )


def _validate_wheel_file(path: Path, wheel: LockedWheel) -> list[str]:
    if not path.is_file():
        return [f"missing locked wheel {path}"]
    data = path.read_bytes()
    return _validate_wheel_bytes(str(path), data, wheel)


def _validate_wheel_bytes(label: str, data: bytes, wheel: LockedWheel) -> list[str]:
    errors: list[str] = []
    if len(data) != wheel.size:
        errors.append(f"{label} size mismatch: expected {wheel.size}, got {len(data)}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != wheel.sha256:
        errors.append(f"{label} checksum mismatch: expected {wheel.sha256}, got {digest}")
    try:
        if not _wheel_contains_tag(data, wheel.tag):
            errors.append(f"{label} WHEEL metadata missing tag {wheel.tag}")
    except zipfile.BadZipFile:
        errors.append(f"{label} is not a valid wheel zip")
    return errors


def _wheel_contains_tag(data: bytes, tag: str) -> bool:
    with zipfile.ZipFile(io.BytesIO(data), "r") as wheel_zip:
        for name in wheel_zip.namelist():
            if name.endswith(".dist-info/WHEEL"):
                metadata = wheel_zip.read(name).decode("utf-8", errors="replace")
                return f"Tag: {tag}\n" in metadata or metadata.rstrip().endswith(
                    f"Tag: {tag}"
                )
    return False


def _download_file(url: str, destination: Path) -> None:
    with (
        urllib.request.urlopen(url, timeout=120) as response,
        destination.open("wb") as output,
    ):
        while chunk := response.read(CHUNK_SIZE):
            output.write(chunk)


if __name__ == "__main__":
    raise SystemExit(main())
