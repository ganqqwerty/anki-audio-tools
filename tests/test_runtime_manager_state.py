from __future__ import annotations

import threading
from pathlib import Path

from anki_audio_quick_editor import runtime_manager
from tests.test_runtime_manager import _write_manifest, _write_runtime_pack


def test_runtime_status_reuses_existing_manifest_id_across_addon_versions(
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
    assert runtime_manager.ensure_runtime(addon_dir)["phase"] == "ready"

    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)

    assert runtime_manager.runtime_status(addon_dir)["phase"] == "ready"


def test_force_verify_clears_ready_state_before_cancelled_repair(
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
    assert runtime_manager.ensure_runtime(addon_dir)["phase"] == "ready"
    root = addon_dir / "user_files" / "runtime" / "runtime-test"
    (root / "macos-arm64" / "ffmpeg").write_bytes(b"FFMPEG")
    assert runtime_manager.runtime_status(addon_dir)["phase"] == "ready"
    cancel_event = threading.Event()

    def progress(payload: dict[str, object]) -> None:
        if "failed verification" in str(payload.get("detail", "")):
            cancel_event.set()

    status = runtime_manager.ensure_runtime(
        addon_dir,
        progress=progress,
        cancel_event=cancel_event,
        force_verify=True,
    )

    assert status["phase"] == "missing"
    assert not (addon_dir / "user_files" / "runtime_state.json").exists()
    assert runtime_manager.runtime_status(addon_dir)["phase"] == "missing"


def test_changed_manifest_id_installs_new_runtime_without_deleting_old_first(
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
    assert runtime_manager.ensure_runtime(addon_dir)["phase"] == "ready"
    old_root = addon_dir / "user_files" / "runtime" / "runtime-test"
    assert old_root.is_dir()

    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=payloads,
        manifest_id="runtime-test-2",
    )
    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "ready"
    assert (addon_dir / "user_files" / "runtime" / "runtime-test-2").is_dir()

