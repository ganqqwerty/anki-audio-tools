from __future__ import annotations

import json
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import render_audio
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.audio_tools import (
    expected_bundled_silero_vad_model_path,
    expected_bundled_tool_path,
)
from tests.audio_fixtures import FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON

MUSIC_PAUSE_FIXTURE = Path(__file__).parent / "fixtures" / "audio" / "13df7c3d3bc_music_pauses.mp3"


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_silero_aggressive_detects_music_filled_pauses_and_removes_min_duration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    silero_path = expected_bundled_tool_path("silero-vad")
    model_path = expected_bundled_silero_vad_model_path()
    if silero_path is None or model_path is None or not silero_path.is_file() or not model_path.is_file():
        pytest.skip("Bundled Silero VAD executable and model are not available for this platform.")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline.find_silero_vad_bundle",
        lambda: (silero_path, model_path),
    )

    result = render_audio(
        MUSIC_PAUSE_FIXTURE,
        AudioEditState(MUSIC_PAUSE_FIXTURE.name, remove_internal_pauses_enabled=True),
        AudioProcessingConfig(
            pause_aggressiveness="aggressive",
            pause_detection_algorithm="silero_vad",
            pause_silero_threshold=0.85,
            pause_silero_min_silence_seconds=0.15,
            pause_silero_min_speech_seconds=0.04,
        ),
        output_path=tmp_path / "shortened.mp3",
        artifact_root=tmp_path / "artifacts",
    )
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    detected_segments = manifest["detected_intervals"]
    removed_segments = manifest["removed_intervals"]

    assert manifest["operation"] == "silero_vad_pause_removal"
    assert manifest["pause_detection_parameters"] == {
        "aggressiveness": "aggressive",
        "algorithm": "silero_vad",
        "threshold": 0.85,
        "min_silence_seconds": 0.15,
        "min_speech_seconds": 0.04,
        "preprocess_denoise": False,
    }
    assert _has_pause_near(detected_segments, start_ms=1800, end_ms=2200)
    assert _has_pause_near(detected_segments, start_ms=2820, end_ms=2970)
    assert _has_pause_near(removed_segments, start_ms=1800, end_ms=2200)
    assert not _has_pause_near(removed_segments, start_ms=2820, end_ms=2970)
    assert all(segment["kind"] == "normal" for segment in manifest["timeline"])
    assert all(segment["speed_factor"] == 1.0 for segment in manifest["timeline"])


def _has_pause_near(
    pause_segments: list[dict[str, object]],
    *,
    start_ms: int,
    end_ms: int,
    tolerance_ms: int = 90,
) -> bool:
    return any(
        abs(int(segment["start_ms"]) - start_ms) <= tolerance_ms
        and abs(int(segment["end_ms"]) - end_ms) <= tolerance_ms
        for segment in pause_segments
    )
