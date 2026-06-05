"""Tests for platform-scoped vendored Python wheel activation."""

from __future__ import annotations

import importlib
import sys
import zipfile
from pathlib import Path

import pytest

from anki_audio_quick_editor import vendor_runtime


def test_activate_vendor_extracts_platform_wheels(monkeypatch, tmp_path: Path) -> None:
    wheel_dir = tmp_path / "vendor" / "wheels" / "macos-arm64"
    wheel_dir.mkdir(parents=True)
    _write_wheel(
        wheel_dir / "sample_vendor-1.0-cp313-cp313-macosx_11_0_arm64.whl",
        {
            "sample_vendor/__init__.py": "VALUE = 42\n",
            "sample_vendor-1.0.dist-info/METADATA": "Name: sample-vendor\n",
        },
    )
    monkeypatch.setattr(vendor_runtime, "current_platform_key", lambda: "macos-arm64")
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "sample_vendor", raising=False)

    site_packages = vendor_runtime.activate_vendor(tmp_path)

    assert site_packages is not None
    assert sys.path[0] == str(site_packages)
    assert sys.path[1] == str(tmp_path / "vendor")
    assert (site_packages / "sample_vendor" / "__init__.py").is_file()
    assert not (site_packages / "sample_vendor-1.0.dist-info").exists()
    assert (site_packages / ".complete").read_text(encoding="utf-8").strip() == (
        "sample_vendor-1.0-cp313-cp313-macosx_11_0_arm64.whl"
    )
    imported = importlib.import_module("sample_vendor")
    assert imported.VALUE == 42


def test_activate_vendor_returns_none_without_platform_wheels(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vendor_runtime, "current_platform_key", lambda: "windows-x86_64")
    monkeypatch.setattr(sys, "path", list(sys.path))

    site_packages = vendor_runtime.activate_vendor(tmp_path)

    assert site_packages is None
    assert sys.path[0] == str(tmp_path / "vendor")


def test_activate_vendor_rejects_unsafe_wheel_member(monkeypatch, tmp_path: Path) -> None:
    wheel_dir = tmp_path / "vendor" / "wheels" / "macos-arm64"
    wheel_dir.mkdir(parents=True)
    _write_wheel(
        wheel_dir / "unsafe-1.0-cp313-cp313-macosx_11_0_arm64.whl",
        {"../unsafe.py": "VALUE = 1\n"},
    )
    monkeypatch.setattr(vendor_runtime, "current_platform_key", lambda: "macos-arm64")

    with pytest.raises(vendor_runtime.VendorActivationError, match="Unsafe vendored wheel member"):
        vendor_runtime.activate_vendor(tmp_path)


def _write_wheel(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as wheel:
        for name, content in files.items():
            wheel.writestr(name, content)
