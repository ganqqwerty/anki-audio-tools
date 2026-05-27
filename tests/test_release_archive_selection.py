"""Tests for release archive file selection."""

from __future__ import annotations

from pathlib import Path

from scripts import release, release_archive, release_assets


def test_release_excludes_retained_pause_pipeline_artifacts() -> None:
    artifact_manifest = (
        release.ADDON_DIR
        / "aqe_artifacts"
        / "clip__20260517_010203_123456_deadbeef"
        / "manifest.json"
    )

    assert release._should_include(artifact_manifest) is False


def test_release_keeps_committed_config_json() -> None:
    assert release._should_include(release.ADDON_DIR / "config.json") is True


def test_release_manifest_files_can_be_limited_to_single_runtime_target() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
        embed_runtime=True,
    )

    assert "bin/macos-arm64/ffmpeg" in names
    assert "bin/macos-arm64/silero-vad" in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" in names
    assert "bin/models/silero-vad/silero_vad.onnx" in names
    assert "bin/windows-x86_64/ffmpeg.exe" not in names
    assert "bin/windows-x86_64/onnxruntime.dll" not in names


def test_release_manifest_files_default_to_thin_archive() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
    )

    assert "bin/runtime_manifest.json" in names
    assert "bin/macos-arm64/ffmpeg" not in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" not in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" not in names
    assert "bin/models/silero-vad/silero_vad.onnx" not in names


def test_release_manifest_files_can_exclude_ffmpeg_tools() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
        include_ffmpeg=False,
        embed_runtime=True,
    )

    assert "bin/macos-arm64/ffmpeg" not in names
    assert "bin/macos-arm64/ffprobe" not in names
    assert "bin/macos-arm64/deep-filter" in names
    assert "bin/macos-arm64/silero-vad" in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" in names
    assert "bin/models/silero-vad/silero_vad.onnx" in names


def test_release_archive_name_marks_external_ffmpeg_variant(tmp_path: Path) -> None:
    original = release_archive.DIST_DIR
    release_archive.DIST_DIR = tmp_path / "dist"
    try:
        archive = release_archive.build_archive(
            "1.2.3",
            tmp_path,
            target_label="macos-arm64",
            include_ffmpeg=False,
        )
    finally:
        release_archive.DIST_DIR = original

    assert archive.name == "anki-audio-quick-editor-1.2.3-macos-arm64-external-ffmpeg.ankiaddon"
