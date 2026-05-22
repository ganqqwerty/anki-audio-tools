from __future__ import annotations

import copy
import hashlib
import io
import json
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import release_asset_common, release_assets, release_sherpa_assets


def test_lock_contains_supported_target_and_tool_matrix() -> None:
    lock = release_assets.load_lock()

    assert release_assets.lock_targets(lock) == [
        "macos-arm64",
        "macos-x86_64",
        "windows-x86_64",
    ]
    assert release_assets.lock_tools(lock, "macos-arm64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    assert release_assets.lock_tools(lock, "macos-x86_64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    assert release_assets.lock_tools(lock, "windows-x86_64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    for target in release_assets.lock_targets(lock):
        sherpa_files = release_assets.tool_runtime_files(lock, target, "sherpa-spleeter")
        assert sherpa_files
    assert release_assets.lock_shared_files(lock) == [
        "spleeter-vocals",
        "spleeter-accompaniment",
    ]
    assert any("DPDFNet Lite CLI" in notice for notice in lock["notices"])


def test_release_ready_lock_requires_every_binary_checksum() -> None:
    lock = release_assets.load_lock()
    release_ready_lock = copy.deepcopy(lock)
    release_ready_lock["release_ready"] = True
    release_ready_lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("sha256", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="macos-arm64/ffmpeg.*sha256"):
        release_assets.validate_lock(release_ready_lock)


def test_release_ready_lock_requires_runtime_file_checksums() -> None:
    lock = release_assets.load_lock()
    release_ready_lock = copy.deepcopy(lock)
    release_ready_lock["release_ready"] = True
    runtime_file = release_ready_lock["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]["runtime_files"][0]
    runtime_file.pop("sha256", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="macos-arm64/sherpa-spleeter.*sha256"):
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


def test_verify_runs_current_sherpa_spleeter_smoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    current_target = "macos-arm64"
    _write_verified_target_cache(lock, tmp_path, current_target)
    monkeypatch.setattr(release_assets, "current_target_key", lambda: current_target)
    monkeypatch.setattr(release_assets, "_append_diagnostic_report", lambda *_args: None)
    commands: list[tuple[str, ...]] = []

    def fake_run(
        command: list[str],
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> SimpleNamespace:
        commands.append(tuple(command))
        if command[0].endswith("ffmpeg"):
            Path(command[-1]).write_bytes(b"input wav")
        elif command[0].endswith("sherpa-spleeter"):
            _write_spleeter_smoke_outputs(command)
        else:  # pragma: no cover - protects the test if a new command is added
            raise AssertionError(command)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(release_sherpa_assets.subprocess, "run", fake_run)

    result = release_assets.verify_assets(
        lock,
        cache_dir=tmp_path,
        target_keys=[current_target],
        run_diagnostics=True,
    )

    assert result.ok is True
    assert commands[1][-1] == "--num-threads=1"
    assert any("sherpa-spleeter: smoke ok" in report for report in result.reports)


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


def test_stage_copies_shared_model_files_when_staging_full_runtime(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    vocals = tmp_path / "cache" / "shared" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    accompaniment = vocals.parent / "accompaniment.fp16.onnx"
    binary.parent.mkdir(parents=True)
    vocals.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    vocals.write_bytes(b"vocals")
    accompaniment.write_bytes(b"accompaniment")
    locked["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] = hashlib.sha256(b"ffmpeg").hexdigest()
    locked["shared_files"]["spleeter-vocals"]["sha256"] = hashlib.sha256(b"vocals").hexdigest()
    locked["shared_files"]["spleeter-accompaniment"]["sha256"] = hashlib.sha256(b"accompaniment").hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        destination=tmp_path / "stage",
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
        include_shared=True,
    )

    assert tmp_path / "stage" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx" in staged
    assert tmp_path / "stage" / "models" / "spleeter-2stems-fp16" / "accompaniment.fp16.onnx" in staged


def test_lock_checksums_writes_present_binary_hashes(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_assets.lock.json"
    lock = release_assets.load_lock()
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    dpdfnet_binary = tmp_path / "cache" / "bin" / "macos-arm64" / "dpdfnet"
    runtime_file = tmp_path / "cache" / "bin" / "macos-arm64" / "libonnxruntime.1.24.4.dylib"
    vocals = tmp_path / "cache" / "shared" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    binary.parent.mkdir(parents=True)
    vocals.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    dpdfnet_binary.write_bytes(b"dpdfnet")
    runtime_file.write_bytes(b"onnxruntime")
    vocals.write_bytes(b"vocals")

    release_assets.lock_checksums(lock_path=lock_path, cache_dir=tmp_path / "cache")

    updated = json.loads(lock_path.read_text(encoding="utf-8"))
    assert updated["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] == hashlib.sha256(
        b"ffmpeg"
    ).hexdigest()
    assert updated["targets"]["macos-arm64"]["tools"]["dpdfnet"]["sha256"] == hashlib.sha256(
        b"dpdfnet"
    ).hexdigest()
    sherpa_files = updated["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]["runtime_files"]
    assert sherpa_files[0]["sha256"] == hashlib.sha256(b"onnxruntime").hexdigest()
    assert updated["shared_files"]["spleeter-vocals"]["sha256"] == hashlib.sha256(b"vocals").hexdigest()


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
        destination.parent.mkdir(parents=True, exist_ok=True)
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


def test_fetch_sherpa_spleeter_extracts_executable_and_runtime_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    archive = tmp_path / "download" / "sherpa.tar.bz2"
    archive.parent.mkdir()
    executable_member = "sherpa/bin/sherpa-onnx-offline-source-separation"
    runtime_member = "sherpa/lib/libonnxruntime.1.24.4.dylib"
    _write_tar_bz2(
        archive,
        {
            executable_member: b"sherpa-executable",
            runtime_member: b"onnxruntime",
        },
    )
    entry = lock["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]
    entry["core_archive_url"] = "https://example.invalid/sherpa.tar.bz2"
    entry["core_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    entry["archive_member"] = executable_member
    entry["sha256"] = hashlib.sha256(b"sherpa-executable").hexdigest()
    entry["runtime_files"] = [
        {
            "archive_member": runtime_member,
            "path": "libonnxruntime.1.24.4.dylib",
            "sha256": hashlib.sha256(b"onnxruntime").hexdigest(),
        }
    ]

    def fake_download(_url: str, destination: Path, _expected_sha: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(release_sherpa_assets, "_download_verified", fake_download)

    fetched = release_assets.fetch_sherpa_spleeter(
        lock,
        target_keys=["macos-arm64"],
        cache_dir=tmp_path / "cache",
    )

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
    _write_tar_bz2(
        archive,
        {
            "models/vocals.onnx": b"vocals",
            "models/accompaniment.onnx": b"accompaniment",
        },
    )
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


def _write_tar_bz2(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:bz2") as tf:
        for name, payload in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tf.addfile(info, io.BytesIO(payload))


def _write_verified_target_cache(lock: dict, cache_dir: Path, target: str) -> None:
    for tool_name in release_assets.lock_tools(lock, target):
        entry = lock["targets"][target]["tools"][tool_name]
        payload = f"{target}/{tool_name}".encode()
        _write_locked_file(release_assets.asset_binary_path(cache_dir, target, entry), payload, entry)
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            runtime_payload = f"{target}/{tool_name}/{file_entry['path']}".encode()
            _write_locked_file(
                release_assets.runtime_file_path(cache_dir, target, file_entry),
                runtime_payload,
                file_entry,
            )
    for file_name in release_assets.SHARED_FILE_NAMES:
        entry = lock["shared_files"][file_name]
        payload = f"shared/{file_name}".encode()
        _write_locked_file(release_assets.shared_asset_path(cache_dir, entry), payload, entry)


def _write_locked_file(path: Path, payload: bytes, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()


def _write_spleeter_smoke_outputs(command: list[str]) -> None:
    for arg in command:
        if arg.startswith("--output-vocals-wav=") or arg.startswith("--output-accompaniment-wav="):
            Path(arg.split("=", 1)[1]).write_bytes(b"stem wav")
