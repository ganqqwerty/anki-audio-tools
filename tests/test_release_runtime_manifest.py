"""Tests for release runtime manifest generation."""

from __future__ import annotations

import json

from scripts import release, release_assets, release_runtime


def test_runtime_manifest_can_be_limited_to_single_runtime_target(tmp_path) -> None:
    lock = release_assets.load_lock()

    release_runtime.write_runtime_manifest(tmp_path, lock, target_keys=["windows-x86_64"])

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert list(manifest["targets"]) == ["windows-x86_64"]
    assert manifest["targets"]["windows-x86_64"]["tools"]["sherpa-spleeter"]["runtime_files"]
    assert manifest["targets"]["windows-x86_64"]["tools"]["silero-vad"]["runtime_files"]
    assert manifest["shared_files"]["spleeter-vocals"]["path"] == "models/spleeter-2stems-fp16/vocals.fp16.onnx"
    assert manifest["shared_files"]["silero-vad-model"]["path"] == "models/silero-vad/silero_vad.onnx"


def test_runtime_manifest_can_exclude_ffmpeg_tools(tmp_path) -> None:
    lock = release_assets.load_lock()

    release_runtime.write_runtime_manifest(tmp_path, lock, target_keys=["macos-arm64"], include_ffmpeg=False)

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert "ffmpeg" not in manifest["targets"]["macos-arm64"]["tools"]
    assert "ffprobe" not in manifest["targets"]["macos-arm64"]["tools"]
    assert "deep-filter" in manifest["targets"]["macos-arm64"]["tools"]


def test_runtime_manifest_includes_locked_diagnostic_args(tmp_path) -> None:
    lock = release_assets.load_lock()

    release_runtime.write_runtime_manifest(tmp_path, lock, target_keys=["macos-arm64"])

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert manifest["targets"]["macos-arm64"]["tools"]["ffmpeg"]["diagnostic_args"] == ["-version"]
    assert manifest["targets"]["macos-arm64"]["tools"]["silero-vad"]["diagnostic_args"] == ["--help"]


def test_runtime_pack_entries_deduplicate_shared_onnxruntime_support_files() -> None:
    lock = release_assets.load_lock()

    entries = release_runtime._runtime_pack_entries(
        lock,
        "macos-arm64",
        source_bin_dir=release.ADDON_DIR / "bin",
        include_ffmpeg=False,
    )
    paths = [entry["path"] for entry in entries]

    assert paths.count("macos-arm64/libonnxruntime.1.24.4.dylib") == 1
