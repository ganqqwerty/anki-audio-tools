from __future__ import annotations

from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/build-ffmpeg-runtime.yml")


def test_ffmpeg_runtime_workflow_defines_manual_inputs_and_targets() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "release_tag:" in text
    assert "ffmpeg_ref:" in text
    assert "force_custom_build:" in text
    for target in ("windows-x86_64", "macos-arm64", "macos-x86_64"):
        assert target in text


def test_ffmpeg_runtime_workflow_uses_expected_provider_and_build_paths() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "BtbN/FFmpeg-Builds" in text
    assert "scripts/ffmpeg_build/build_macos.sh" in text
    assert "ffmpeg.martin-riedl.de" in text
    assert "osxexperts.net" in text
    assert "Vargol/ffmpeg-apple-arm64-build" in text
    assert "scripts/ffmpeg_runtime/" not in text


def test_ffmpeg_runtime_workflow_verifies_capabilities_before_upload() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python3 scripts/ffmpeg_runtime_capabilities.py" in text
    assert "gh release upload" in text
    assert "aqe-ffmpeg-runtime-${{ inputs.ffmpeg_ref }}-${{ matrix.target }}.zip" in text
    assert "ffmpeg" in text
    assert "ffprobe" in text
