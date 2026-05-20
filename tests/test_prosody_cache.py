"""Tests for prosody analysis cache keys and reuse."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_cache import (
    _ANALYSIS_CACHE,
    analyze_prosody_cached,
    prosody_cache_key,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


def test_prosody_cache_key_uses_path_size_and_mtime(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"one")
    first_key = prosody_cache_key(source, AudioProcessingConfig())
    source.write_bytes(b"one-two")
    second_key = prosody_cache_key(source, AudioProcessingConfig())

    assert first_key[0] == str(source)
    assert second_key[0] == str(source)
    assert first_key[1] != second_key[1]
    assert isinstance(first_key[2], int)
    assert first_key[3] == ("general", "auto", "very_smooth", 240, "balanced")


def test_prosody_cache_key_includes_graph_analysis_settings(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    default_key = prosody_cache_key(source, AudioProcessingConfig())
    bass_key = prosody_cache_key(source, AudioProcessingConfig(graph_voice_range="bass"))

    assert default_key[:3] == bass_key[:3]
    assert default_key[3] != bass_key[3]


def test_prosody_cache_reuses_matching_file_identity(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename=source.name,
        analyzer_name="test",
    )
    calls: list[Path] = []

    def fake_analyze(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        calls.append(path)
        return track

    monkeypatch.setattr("anki_audio_quick_editor.prosody_cache.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert calls == [source]


def test_prosody_cache_does_not_reuse_across_graph_settings(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename=source.name,
        analyzer_name="test",
    )
    calls: list[AudioProcessingConfig] = []

    def fake_analyze(_path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
        calls.append(config)
        return track

    monkeypatch.setattr("anki_audio_quick_editor.prosody_cache.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert analyze_prosody_cached(source, AudioProcessingConfig(graph_voice_range="bass")) is track
    assert [config.graph_voice_range for config in calls] == ["general", "bass"]
