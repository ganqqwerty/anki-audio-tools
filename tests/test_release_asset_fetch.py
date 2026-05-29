"""Release asset fetch and download helper tests."""

from __future__ import annotations

import copy
import hashlib
import io
import stat
import urllib.request
import zipfile
from pathlib import Path

import pytest
import scripts.release_asset_common as release_asset_common
import scripts.release_assets as release_assets
import scripts.release_sherpa_assets as release_sherpa_assets
import scripts.release_silero_assets as release_silero_assets

from tests.release_assets_helpers import write_tar_bz2


def test_fetch_deepfilter_marks_macos_binary_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = copy.deepcopy(release_assets.load_lock())

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"deep-filter")
        destination.chmod(0o644)

    monkeypatch.setattr(release_assets, "_download_verified", fake_download)
    fetched = release_assets.fetch_deepfilter(lock, target_keys=["macos-arm64"], cache_dir=tmp_path)
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
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_assets, "_download_verified", fake_download)
    monkeypatch.setattr("scripts.release_assets_runtime_ops.verify_ffmpeg_binary", lambda _path: None)
    fetched = release_assets.fetch_ffmpeg(
        lock,
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
        cache_dir=tmp_path / "cache",
    )
    assert fetched == [tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"]
    assert fetched[0].read_bytes() == b"ffmpeg-binary"
    assert fetched[0].stat().st_mode & stat.S_IXUSR


def test_fetch_sherpa_spleeter_extracts_executable_and_runtime_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    archive = tmp_path / "download" / "sherpa.tar.bz2"
    archive.parent.mkdir()
    executable_member = "sherpa/bin/sherpa-onnx-offline-source-separation"
    runtime_member = "sherpa/lib/libonnxruntime.1.24.4.dylib"
    write_tar_bz2(archive, {executable_member: b"sherpa-executable", runtime_member: b"onnxruntime"})
    entry = lock["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]
    entry["core_archive_url"] = "https://example.invalid/sherpa.tar.bz2"
    entry["core_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    entry["archive_member"] = executable_member
    entry["sha256"] = hashlib.sha256(b"sherpa-executable").hexdigest()
    entry["runtime_files"] = [{"archive_member": runtime_member, "path": "libonnxruntime.1.24.4.dylib", "sha256": hashlib.sha256(b"onnxruntime").hexdigest()}]

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_sherpa_assets, "_download_verified", fake_download)
    fetched = release_assets.fetch_sherpa_spleeter(lock, target_keys=["macos-arm64"], cache_dir=tmp_path / "cache")
    executable = tmp_path / "cache" / "bin" / "macos-arm64" / "sherpa-spleeter"
    runtime = tmp_path / "cache" / "bin" / "macos-arm64" / "libonnxruntime.1.24.4.dylib"
    assert fetched == [executable, runtime]
    assert executable.read_bytes() == b"sherpa-executable"
    assert executable.stat().st_mode & stat.S_IXUSR
    assert runtime.read_bytes() == b"onnxruntime"


def test_fetch_spleeter_models_extracts_shared_model_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    archive = tmp_path / "download" / "models.tar.bz2"
    archive.parent.mkdir()
    write_tar_bz2(archive, {"models/vocals.onnx": b"vocals", "models/accompaniment.onnx": b"accompaniment"})
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    for file_name, archive_member, payload in (
        ("spleeter-vocals", "models/vocals.onnx", b"vocals"),
        ("spleeter-accompaniment", "models/accompaniment.onnx", b"accompaniment"),
    ):
        entry = lock["shared_files"][file_name]
        entry["download_url"] = "https://example.invalid/models.tar.bz2"
        entry["download_sha256"] = archive_sha
        entry["archive_member"] = archive_member
        entry["sha256"] = hashlib.sha256(payload).hexdigest()

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_sherpa_assets, "_download_verified", fake_download)
    fetched = release_assets.fetch_spleeter_models(lock, cache_dir=tmp_path / "cache")
    vocals = tmp_path / "cache" / "shared" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    accompaniment = vocals.parent / "accompaniment.fp16.onnx"
    assert fetched == [vocals, accompaniment]
    assert vocals.read_bytes() == b"vocals"
    assert accompaniment.read_bytes() == b"accompaniment"


def test_fetch_silero_vad_extracts_executable_and_runtime_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    archive = tmp_path / "download" / "sherpa-vad.tar.bz2"
    archive.parent.mkdir()
    executable_member = "sherpa/bin/sherpa-onnx-vad"
    runtime_member = "sherpa/lib/libonnxruntime.1.24.4.dylib"
    write_tar_bz2(archive, {executable_member: b"silero-executable", runtime_member: b"onnxruntime"})
    entry = lock["targets"]["macos-arm64"]["tools"]["silero-vad"]
    entry["core_archive_url"] = "https://example.invalid/sherpa-vad.tar.bz2"
    entry["core_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    entry["archive_member"] = executable_member
    entry["sha256"] = hashlib.sha256(b"silero-executable").hexdigest()
    entry["runtime_files"] = [{"archive_member": runtime_member, "path": "libonnxruntime.1.24.4.dylib", "sha256": hashlib.sha256(b"onnxruntime").hexdigest()}]

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_silero_assets, "_download_verified", fake_download)
    fetched = release_assets.fetch_silero_vad(
        lock,
        target_keys=["macos-arm64"],
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
    )
    executable = tmp_path / "addon-bin" / "macos-arm64" / "silero-vad"
    runtime = tmp_path / "addon-bin" / "macos-arm64" / "libonnxruntime.1.24.4.dylib"
    assert fetched == [executable, runtime]
    assert executable.read_bytes() == b"silero-executable"
    assert executable.stat().st_mode & stat.S_IXUSR
    assert runtime.read_bytes() == b"onnxruntime"


def test_fetch_silero_vad_model_downloads_shared_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    entry = lock["shared_files"]["silero-vad-model"]
    entry["download_url"] = "https://example.invalid/silero_vad.onnx"
    entry["download_sha256"] = hashlib.sha256(b"silero-model").hexdigest()
    entry["sha256"] = hashlib.sha256(b"silero-model").hexdigest()

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"silero-model")

    monkeypatch.setattr(release_silero_assets, "_download_verified", fake_download)
    fetched = release_assets.fetch_silero_vad_model(
        lock,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
    )
    model = tmp_path / "addon-bin" / "models" / "silero-vad" / "silero_vad.onnx"
    assert fetched == [model]
    assert model.read_bytes() == b"silero-model"


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

    monkeypatch.setattr(release_asset_common.urllib.request, "urlopen", fake_urlopen)
    release_assets._download_verified(
        "https://example.invalid/tool.zip",
        tmp_path / "tool.zip",
        hashlib.sha256(payload).hexdigest(),
    )
    assert seen_headers["User-agent"].startswith("anki-audio-tools-release-assets/")
