from __future__ import annotations

import json
import threading
from pathlib import Path

from anki_audio_quick_editor import runtime_manager
from tests.runtime_manager_fixtures import _write_manifest, _write_runtime_pack


def test_ensure_runtime_downloads_verifies_and_persists_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")
    progress: list[dict[str, object]] = []

    status = runtime_manager.ensure_runtime(addon_dir, progress=progress.append)

    assert status["phase"] == "ready"
    assert [entry.get("step") for entry in progress] == [
        "Select runtime package",
        "Check existing runtime",
        "Download zip",
        "Download zip",
        "Verify zip",
        "Unpack zip",
        "Verify files",
        "Promote runtime",
        "Cleanup",
    ]
    root = addon_dir / "user_files" / "runtime" / "runtime-test"
    assert (root / "macos-arm64" / "ffmpeg").read_bytes() == b"ffmpeg"
    assert (root / "macos-arm64" / "rnnoise-cli").read_bytes() == b"rnnoise"
    assert runtime_manager.managed_tool_path(addon_dir, "ffmpeg") == root / "macos-arm64" / "ffmpeg"
    state = json.loads((addon_dir / "user_files" / "runtime_state.json").read_text(encoding="utf-8"))
    assert state["runtime_manifest_id"] == "runtime-test"
    assert state["platform"] == "macos-arm64"


def test_ensure_runtime_rejects_checksum_mismatch(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha="0" * 64, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert status["error"].startswith("AQE-RUNTIME-003:")
    assert "checksum mismatch" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_rejects_zip_size_mismatch(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        archive_size=archive.stat().st_size + 1,
        file_payloads=payloads,
    )
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert status["error"].startswith("AQE-RUNTIME-003:")
    assert "size mismatch" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_rejects_corrupt_zip(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive.write_bytes(b"not a zip")
    archive_sha = runtime_manager.sha256_file(archive)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert "not a valid zip archive" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_rejects_unexpected_archive_file(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
        "unexpected.bin": b"extra",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    expected_payloads = {key: value for key, value in payloads.items() if key != "unexpected.bin"}
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=expected_payloads,
    )
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert status["error"].startswith("AQE-RUNTIME-003:")
    assert "unexpected file" in status["error"]


def test_ensure_runtime_rejects_missing_archive_file(tmp_path: Path, monkeypatch) -> None:
    expected_payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive_payloads = {
        key: value
        for key, value in expected_payloads.items()
        if key != "macos-arm64/rnnoise-cli"
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, archive_payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=expected_payloads,
    )
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert "missing file" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_rejects_extracted_size_mismatch(tmp_path: Path, monkeypatch) -> None:
    expected_payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive_payloads = {
        **expected_payloads,
        "macos-arm64/rnnoise-cli": b"rnnoise-too-large",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, archive_payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=expected_payloads,
    )
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert "wrong size" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_rejects_extracted_sha_mismatch(tmp_path: Path, monkeypatch) -> None:
    expected_payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive_payloads = {
        **expected_payloads,
        "macos-arm64/rnnoise-cli": b"RNNOISE",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, archive_payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=expected_payloads,
    )
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert "checksum mismatch" in status["error"]
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()


def test_ensure_runtime_can_be_cancelled_before_download(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")
    cancel_event = threading.Event()
    cancel_event.set()

    status = runtime_manager.ensure_runtime(addon_dir, cancel_event=cancel_event)

    assert status["phase"] == "missing"
    assert status["message"] == "Runtime installation cancelled."
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()
    assert not (addon_dir / "user_files" / "runtime" / "runtime-test").exists()


def test_ensure_runtime_cancels_after_downloaded_bytes_arrive(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")
    cancel_event = threading.Event()
    observed_download = threading.Event()

    def progress(payload: dict[str, object]) -> None:
        if "Downloaded " in str(payload.get("detail", "")):
            observed_download.set()
            cancel_event.set()

    status = runtime_manager.ensure_runtime(addon_dir, progress=progress, cancel_event=cancel_event)

    assert observed_download.is_set(), "test did not rendezvous after downloaded data arrived"
    assert status["phase"] == "missing"
    assert not (addon_dir / "user_files" / "runtime" / "runtime-test").exists()
    assert not list((addon_dir / "user_files" / "runtime").glob("*.extracting-*"))
    assert not list((addon_dir / "user_files" / "runtime" / "downloads").glob("*.download"))


def test_ensure_runtime_cancels_during_extracted_file_verification(tmp_path: Path, monkeypatch) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")
    cancel_event = threading.Event()
    verification_started = threading.Event()

    def progress(payload: dict[str, object]) -> None:
        if payload.get("step") == "Verify files":
            verification_started.set()
            cancel_event.set()

    status = runtime_manager.ensure_runtime(addon_dir, progress=progress, cancel_event=cancel_event)

    assert verification_started.is_set(), "test did not rendezvous at extracted-file verification"
    assert status["phase"] == "missing"
    assert not (addon_dir / "user_files" / "runtime" / "runtime-test").exists()
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()
