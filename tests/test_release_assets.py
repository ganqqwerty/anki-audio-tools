from __future__ import annotations

import copy
import hashlib
import io
import json
import stat
import urllib.request
import zipfile
from pathlib import Path

import pytest
from scripts import release_assets


def test_lock_contains_supported_target_and_tool_matrix() -> None:
    lock = release_assets.load_lock()

    assert release_assets.lock_targets(lock) == [
        "macos-arm64",
        "macos-x86_64",
        "windows-x86_64",
    ]
    for target in release_assets.lock_targets(lock):
        assert release_assets.lock_tools(lock, target) == [
            "deep-filter",
            "ffmpeg",
            "ffprobe",
            "rnnoise-cli",
        ]


def test_release_ready_lock_requires_every_binary_checksum() -> None:
    lock = release_assets.load_lock()
    release_ready_lock = copy.deepcopy(lock)
    release_ready_lock["release_ready"] = True
    release_ready_lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("sha256", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="macos-arm64/ffmpeg.*sha256"):
        release_assets.validate_lock(release_ready_lock)


def test_verify_target_reports_missing_runtime_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()

    result = release_assets.verify_assets(
        lock,
        cache_dir=tmp_path,
        target_keys=["macos-arm64"],
        run_diagnostics=False,
    )

    assert result.ok is False
    assert "macos-arm64/ffmpeg" in "\n".join(result.errors)


def test_verify_target_reports_checksum_mismatch(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    entry = locked["targets"]["macos-arm64"]["tools"]["ffmpeg"]
    entry["sha256"] = hashlib.sha256(b"expected").hexdigest()
    binary = tmp_path / "bin" / "macos-arm64" / "ffmpeg"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"actual")

    result = release_assets.verify_assets(
        locked,
        cache_dir=tmp_path,
        target_keys=["macos-arm64"],
        run_diagnostics=False,
    )

    assert result.ok is False
    assert "checksum mismatch" in "\n".join(result.errors)


def test_stage_rejects_path_traversal_from_lock(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    unsafe = copy.deepcopy(lock)
    unsafe["targets"]["macos-arm64"]["tools"]["ffmpeg"]["executable"] = "../ffmpeg"

    with pytest.raises(release_assets.ReleaseAssetError, match="unsafe executable path"):
        release_assets.stage_assets(
            unsafe,
            cache_dir=tmp_path,
            destination=tmp_path / "stage",
            target_keys=["macos-arm64"],
        )


def test_stage_copies_verified_runtime_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    locked["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] = hashlib.sha256(b"ffmpeg").hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        destination=tmp_path / "stage",
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
    )

    assert staged == [tmp_path / "stage" / "macos-arm64" / "ffmpeg"]
    assert staged[0].read_bytes() == b"ffmpeg"


def test_lock_checksums_writes_present_binary_hashes(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_assets.lock.json"
    lock = release_assets.load_lock()
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")

    release_assets.lock_checksums(lock_path=lock_path, cache_dir=tmp_path / "cache")

    updated = json.loads(lock_path.read_text(encoding="utf-8"))
    assert updated["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] == hashlib.sha256(
        b"ffmpeg"
    ).hexdigest()


def test_fetch_deepfilter_marks_macos_binary_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = copy.deepcopy(release_assets.load_lock())

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"deep-filter")
        destination.chmod(0o644)

    monkeypatch.setattr(release_assets, "_download_verified", fake_download)

    fetched = release_assets.fetch_deepfilter(
        lock,
        target_keys=["macos-arm64"],
        cache_dir=tmp_path,
    )

    assert fetched == [tmp_path / "bin" / "macos-arm64" / "deep-filter"]
    assert fetched[0].stat().st_mode & stat.S_IXUSR


def test_fetch_ffmpeg_extracts_verified_zip_member(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    archive = tmp_path / "download" / "ffmpeg.zip"
    archive.parent.mkdir()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("package/bin/ffmpeg", b"ffmpeg-binary")

    entry = lock["targets"]["macos-arm64"]["tools"]["ffmpeg"]
    entry["download_url"] = "https://example.invalid/ffmpeg.zip"
    entry["download_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    entry["archive_member"] = "package/bin/ffmpeg"
    entry["sha256"] = hashlib.sha256(b"ffmpeg-binary").hexdigest()

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_assets, "_download_verified", fake_download)

    fetched = release_assets.fetch_ffmpeg(
        lock,
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
        cache_dir=tmp_path / "cache",
    )

    assert fetched == [tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"]
    assert fetched[0].read_bytes() == b"ffmpeg-binary"
    assert fetched[0].stat().st_mode & stat.S_IXUSR


def test_download_verified_sends_release_asset_user_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"downloaded-binary"
    seen_headers: dict[str, str] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: int) -> io.BytesIO:
        assert timeout == 60
        seen_headers.update(dict(request.header_items()))
        return io.BytesIO(payload)

    monkeypatch.setattr(release_assets.urllib.request, "urlopen", fake_urlopen)

    release_assets._download_verified(
        "https://example.invalid/tool.zip",
        tmp_path / "tool.zip",
        hashlib.sha256(payload).hexdigest(),
    )

    assert seen_headers["User-agent"].startswith("anki-audio-tools-release-assets/")
