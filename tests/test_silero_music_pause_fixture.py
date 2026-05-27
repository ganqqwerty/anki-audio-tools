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
def test_silero_aggressive_removes_music_filled_pause_chunks(
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
            internal_pause_threshold_ms=140,
            internal_pause_target_gap_ms=45,
        ),
        output_path=tmp_path / "shortened.mp3",
        artifact_root=tmp_path / "artifacts",
    )
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    pause_segments = [segment for segment in manifest["timeline"] if segment["kind"] == "pause"]

    assert _has_pause_near(pause_segments, start_ms=1800, end_ms=2200)
    assert _has_pause_near(pause_segments, start_ms=2820, end_ms=2970)


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
