from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor import runtime_manager
from tests.test_runtime_manager import _write_manifest, _write_runtime_pack


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

