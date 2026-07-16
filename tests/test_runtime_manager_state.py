from __future__ import annotations

import threading
from pathlib import Path

import pytest

from anki_audio_quick_editor import runtime_install, runtime_install_io, runtime_manager
from tests.runtime_manager_fixtures import _write_manifest, _write_runtime_pack


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


def test_state_write_failure_rolls_back_promoted_runtime_and_preserves_ready_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    state_path = addon_dir / "user_files" / "runtime_state.json"
    old_state = state_path.read_bytes()

    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=payloads,
        manifest_id="runtime-test-2",
    )
    new_root = addon_dir / "user_files" / "runtime" / "runtime-test-2"

    def fail_state_write(*_args: object, **_kwargs: object) -> None:
        assert old_root.is_dir(), "old runtime was removed before replacement committed"
        assert new_root.is_dir(), "new runtime was not promoted before state write"
        raise OSError("injected state write failure")

    monkeypatch.setattr(runtime_install_io, "write_ready_state", fail_state_write)

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert old_root.is_dir()
    assert not new_root.exists()
    assert state_path.read_bytes() == old_state


def test_same_manifest_repair_restores_existing_root_when_state_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    marker = root / "preexisting-marker"
    marker.write_text("preserve me", encoding="utf-8")
    (addon_dir / "user_files" / "runtime_state.json").unlink()

    def fail_state_write(*_args: object, **_kwargs: object) -> None:
        assert root.is_dir()
        assert not marker.exists(), "new runtime was not promoted before state write"
        raise OSError("injected state write failure")

    monkeypatch.setattr(runtime_install_io, "write_ready_state", fail_state_write)

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert marker.read_text(encoding="utf-8") == "preserve me"
    assert not list((addon_dir / "user_files" / "runtime").glob("*.rollback-*"))


def test_ensure_runtime_async_is_single_flight_and_notifies_both_callers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = threading.Event()
    release = threading.Event()
    calls: list[Path] = []
    first_notifications: list[str] = []
    second_notifications: list[str] = []
    manifest_status = {
        "phase": "missing",
        "runtime_manifest_id": "runtime-test",
        "platform": "macos-arm64",
        "runtime_root": "",
        "progress": 0,
        "message": "missing",
        "error": "",
    }

    def fake_status(_addon_dir: Path) -> dict[str, object]:
        return dict(manifest_status)

    def fake_ensure(
        addon_dir: Path,
        *,
        progress=None,
        cancel_event=None,
        force_verify: bool = False,
    ) -> dict[str, object]:
        del cancel_event, force_verify
        calls.append(addon_dir)
        started.set()
        assert release.wait(5.0), "single-flight worker was not released"
        ready = {**manifest_status, "phase": "ready", "message": "ready"}
        if progress is not None:
            progress({**manifest_status, "phase": "downloading", "progress": 75})
        return ready

    monkeypatch.setattr(runtime_install, "_INSTALL_THREAD", None)
    monkeypatch.setattr(runtime_install, "_LAST_STATUS", {})
    monkeypatch.setattr(runtime_install, "_INSTALL_LISTENERS", [])
    monkeypatch.setattr(runtime_install, "runtime_status", fake_status)
    monkeypatch.setattr(runtime_install, "ensure_runtime", fake_ensure)

    first = runtime_install.ensure_runtime_async(
        tmp_path,
        notify=lambda value: first_notifications.append(str(value["phase"])),
    )
    assert started.wait(5.0), "runtime worker did not start"
    second = runtime_install.ensure_runtime_async(
        tmp_path,
        notify=lambda value: second_notifications.append(str(value["phase"])),
    )
    release.set()
    thread = runtime_install._INSTALL_THREAD
    assert thread is not None
    thread.join(5.0)

    assert first["phase"] == second["phase"] == "downloading"
    assert calls == [tmp_path]
    assert first_notifications == ["downloading", "downloading", "ready"]
    assert second_notifications == ["downloading", "downloading", "ready"]


@pytest.mark.parametrize("phase", ["extract", "verify"])
def test_pre_promotion_failure_preserves_previous_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
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
    old_state = (addon_dir / "user_files" / "runtime_state.json").read_bytes()
    _write_manifest(
        addon_dir,
        archive=archive,
        archive_sha=archive_sha,
        file_payloads=payloads,
        manifest_id="runtime-test-2",
    )

    def fail(*_args: object, **_kwargs: object) -> None:
        assert old_root.is_dir()
        raise OSError(f"injected {phase} failure")

    target = "extract_expected_files" if phase == "extract" else "verify_extracted_files"
    monkeypatch.setattr(runtime_install_io, target, fail)

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "error"
    assert old_root.is_dir()
    assert not (addon_dir / "user_files" / "runtime" / "runtime-test-2").exists()
    assert (addon_dir / "user_files" / "runtime_state.json").read_bytes() == old_state
