from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

from scripts import vendor_wheels


def test_verify_wheels_accepts_locked_file(tmp_path: Path) -> None:
    tag = "py3-none-any"
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes(tag)
    wheels_dir = tmp_path / "wheels"
    wheel_path = wheels_dir / "test-target" / filename
    wheel_path.parent.mkdir(parents=True)
    wheel_path.write_bytes(data)
    lock_path = _write_lock(tmp_path, filename=filename, data=data, tag=tag)

    assert vendor_wheels.verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir) == []


def test_verify_wheels_reports_missing_and_unlocked_wheels(tmp_path: Path) -> None:
    tag = "py3-none-any"
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes(tag)
    wheels_dir = tmp_path / "wheels"
    extra_path = wheels_dir / "test-target" / "extra-1.0-py3-none-any.whl"
    extra_path.parent.mkdir(parents=True)
    extra_path.write_bytes(data)
    lock_path = _write_lock(tmp_path, filename=filename, data=data, tag=tag)

    errors = vendor_wheels.verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir)

    assert any("missing locked wheel" in error for error in errors)
    assert any("unexpected unlocked wheel" in error for error in errors)


def test_verify_wheels_reports_tag_mismatch(tmp_path: Path) -> None:
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes("py3-none-any")
    wheels_dir = tmp_path / "wheels"
    wheel_path = wheels_dir / "test-target" / filename
    wheel_path.parent.mkdir(parents=True)
    wheel_path.write_bytes(data)
    lock_path = _write_lock(
        tmp_path,
        filename=filename,
        data=data,
        tag="cp313-cp313-win_amd64",
    )

    errors = vendor_wheels.verify_wheels(lock_path=lock_path, wheels_dir=wheels_dir)

    assert errors == [
        f"{wheel_path} WHEEL metadata missing tag cp313-cp313-win_amd64"
    ]


def test_download_wheels_recreates_locked_directory_and_prunes(
    tmp_path: Path,
) -> None:
    tag = "py3-none-any"
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes(tag)
    source = tmp_path / "source" / filename
    source.parent.mkdir()
    source.write_bytes(data)
    wheels_dir = tmp_path / "wheels"
    extra_path = wheels_dir / "test-target" / "old-1.0-py3-none-any.whl"
    extra_path.parent.mkdir(parents=True)
    extra_path.write_bytes(data)
    lock_path = _write_lock(
        tmp_path,
        filename=filename,
        data=data,
        tag=tag,
        url=source.as_uri(),
    )

    errors = vendor_wheels.download_wheels(
        lock_path=lock_path,
        wheels_dir=wheels_dir,
        prune=True,
    )

    assert errors == []
    assert (wheels_dir / "test-target" / filename).read_bytes() == data
    assert not extra_path.exists()


def test_archive_errors_validate_locked_wheels(tmp_path: Path) -> None:
    tag = "py3-none-any"
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes(tag)
    lock_path = _write_lock(tmp_path, filename=filename, data=data, tag=tag)
    archive = tmp_path / "addon.ankiaddon"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"vendor/wheels/test-target/{filename}", data)

    with zipfile.ZipFile(archive, "r") as zf:
        errors = vendor_wheels.archive_errors(zf, lock_path=lock_path)

    assert errors == []


def test_archive_errors_report_missing_and_unlocked_wheels(tmp_path: Path) -> None:
    tag = "py3-none-any"
    filename = "sample-1.0-py3-none-any.whl"
    data = _wheel_bytes(tag)
    lock_path = _write_lock(tmp_path, filename=filename, data=data, tag=tag)
    archive = tmp_path / "addon.ankiaddon"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("vendor/wheels/test-target/extra-1.0-py3-none-any.whl", data)

    with zipfile.ZipFile(archive, "r") as zf:
        errors = vendor_wheels.archive_errors(zf, lock_path=lock_path)

    assert any("missing locked wheel" in error for error in errors)
    assert any("unexpected unlocked wheel" in error for error in errors)


def _wheel_bytes(tag: str) -> bytes:
    wheel_buffer = io.BytesIO()
    with zipfile.ZipFile(wheel_buffer, "w", zipfile.ZIP_DEFLATED) as wheel_zip:
        wheel_zip.writestr(
            "sample-1.0.dist-info/WHEEL",
            f"Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: {tag}\n",
        )
    return wheel_buffer.getvalue()


def _write_lock(
    tmp_path: Path,
    *,
    filename: str,
    data: bytes,
    tag: str,
    url: str = "https://example.com/sample.whl",
) -> Path:
    lock_path = tmp_path / "wheels.lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "targets": {
                    "test-target": [
                        {
                            "package": "sample",
                            "version": "1.0",
                            "filename": filename,
                            "url": url,
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "size": len(data),
                            "tag": tag,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return lock_path
