"""Activation for vendored Python wheels with native extensions."""

from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

from .runtime_paths import user_files_dir
from .runtime_platform import current_platform_key

VENDOR_DIRNAME = "vendor"
VENDOR_WHEELS_DIRNAME = "wheels"
PYTHON_VENDOR_DIRNAME = "python_vendor"
SITE_PACKAGES_DIRNAME = "site-packages"
_COMPLETE_MARKER = ".complete"


class VendorActivationError(RuntimeError):
    """Raised when vendored wheel extraction cannot be completed safely."""


def activate_vendor(addon_dir: Path | None = None) -> Path | None:
    """Add vendored Python packages for this platform to ``sys.path``."""
    package_dir = addon_dir or Path(__file__).resolve().parent
    vendor_dir = package_dir / VENDOR_DIRNAME
    _prepend_sys_path(vendor_dir)

    platform_key = current_platform_key()
    if platform_key is None:
        return None
    wheel_paths = tuple(
        sorted((vendor_dir / VENDOR_WHEELS_DIRNAME / platform_key).glob("*.whl"))
    )
    if not wheel_paths:
        return None

    site_packages = (
        user_files_dir(package_dir)
        / PYTHON_VENDOR_DIRNAME
        / platform_key
        / _wheel_set_id(wheel_paths)
        / SITE_PACKAGES_DIRNAME
    )
    if not (site_packages / _COMPLETE_MARKER).is_file():
        _extract_wheels(wheel_paths, site_packages)
    _prepend_sys_path(site_packages)
    return site_packages


def _prepend_sys_path(path: Path) -> None:
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


def _wheel_set_id(wheel_paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in wheel_paths:
        stat = path.stat()
        digest.update(path.name.encode("utf-8"))
        digest.update(str(stat.st_size).encode("ascii"))
    return digest.hexdigest()[:16]


def _extract_wheels(wheel_paths: tuple[Path, ...], destination: Path) -> None:
    try:
        destination.mkdir(parents=True, exist_ok=True)
        for wheel_path in wheel_paths:
            _extract_wheel(wheel_path, destination)
        (destination / _COMPLETE_MARKER).write_text(
            "\n".join(path.name for path in wheel_paths) + "\n",
            encoding="utf-8",
        )
    except (OSError, zipfile.BadZipFile) as exc:
        raise VendorActivationError(f"Could not activate vendored Python wheels: {exc}") from exc


def _extract_wheel(wheel_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        for member in wheel.infolist():
            if member.is_dir() or _skip_wheel_member(member.filename):
                continue
            target = _safe_member_path(destination, member.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with wheel.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def _skip_wheel_member(name: str) -> bool:
    return any(part.endswith(".dist-info") for part in Path(name).parts)


def _safe_member_path(destination: Path, member_name: str) -> Path:
    target = destination / member_name
    try:
        target.resolve().relative_to(destination.resolve())
    except ValueError as exc:
        raise VendorActivationError(f"Unsafe vendored wheel member: {member_name}") from exc
    return target
