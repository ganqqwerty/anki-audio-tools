from __future__ import annotations

import hashlib
import json
import urllib.error
import zipfile
from pathlib import Path

from anki_audio_quick_editor import runtime_manager
from anki_audio_quick_editor.runtime_install import _friendly_download_error


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_manifest(
    addon_dir: Path,
    *,
    archive: Path,
    archive_sha: str,
    file_payloads: dict[str, bytes],
    manifest_id: str = "runtime-test",
) -> None:
    (addon_dir / "bin").mkdir(parents=True, exist_ok=True)
    files = {
        rel: {
            "path": rel,
            "sha256": _sha(payload),
            "size": len(payload),
            "executable_bit": rel.endswith("ffmpeg") or rel.endswith("rnnoise-cli"),
        }
        for rel, payload in file_payloads.items()
    }
    shared_files = {
        "spleeter-vocals": files["models/spleeter-2stems-fp16/vocals.fp16.onnx"],
    }
    if "models/silero-vad/silero_vad.onnx" in files:
        shared_files["silero-vad-model"] = files["models/silero-vad/silero_vad.onnx"]
    manifest = {
        "schema_version": 2,
        "runtime_manifest_id": manifest_id,
        "targets": {
            "macos-arm64": {
                "runtime_pack": {
                    "name": archive.name,
                    "url": archive.as_uri(),
                    "sha256": archive_sha,
                    "size": archive.stat().st_size,
                },
                "tools": {
                    "ffmpeg": {
                        "path": "macos-arm64/ffmpeg",
                        "executable": "ffmpeg",
                        **files["macos-arm64/ffmpeg"],
                    },
                    "rnnoise-cli": {
                        "path": "macos-arm64/rnnoise-cli",
                        "executable": "rnnoise-cli",
                        **files["macos-arm64/rnnoise-cli"],
                    },
                },
                "shared_files": shared_files,
            }
        },
    }
    (addon_dir / "bin" / "runtime_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def _write_runtime_pack(path: Path, payloads: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in payloads.items():
            zf.writestr(name, payload)
    return runtime_manager.sha256_file(path)


def test_friendly_download_error_mentions_firewall_for_timeouts() -> None:
    message = _friendly_download_error(urllib.error.URLError(TimeoutError("timed out")))

    assert message.startswith("AQE-RUNTIME-003:")
    assert "Runtime download timed out" in message
    assert "/errors/AQE-RUNTIME-003/" in message
    assert "firewall, proxy, VPN, antivirus" in message


def test_friendly_download_error_mentions_permissions_for_write_errors() -> None:
    message = _friendly_download_error(PermissionError(13, "Permission denied"))

    assert message.startswith("AQE-RUNTIME-003:")
    assert "could not write files" in message
    assert "security software" in message


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

    status = runtime_manager.ensure_runtime(addon_dir)

    assert status["phase"] == "ready"
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


def test_managed_silero_vad_model_path_uses_installed_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payloads = {
        "macos-arm64/ffmpeg": b"ffmpeg",
        "macos-arm64/rnnoise-cli": b"rnnoise",
        "models/spleeter-2stems-fp16/vocals.fp16.onnx": b"vocals",
        "models/silero-vad/silero_vad.onnx": b"silero",
    }
    archive = tmp_path / "runtime.zip"
    archive_sha = _write_runtime_pack(archive, payloads)
    addon_dir = tmp_path / "addon"
    _write_manifest(addon_dir, archive=archive, archive_sha=archive_sha, file_payloads=payloads)
    monkeypatch.setattr(runtime_manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_manager.platform, "machine", lambda: "arm64")

    assert runtime_manager.ensure_runtime(addon_dir)["phase"] == "ready"

    root = addon_dir / "user_files" / "runtime" / "runtime-test"
    assert runtime_manager.managed_silero_vad_model_path(addon_dir) == (
        root / "models" / "silero-vad" / "silero_vad.onnx"
    )


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
