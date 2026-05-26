"""Tests for prosody analysis cache keys and reuse."""

from __future__ import annotations

import threading
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


def test_analyze_prosody_cached_serializes_same_key_analysis(tmp_path: Path, monkeypatch) -> None:
    from anki_audio_quick_editor import prosody_cache

    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"audio")
    first_miss = threading.Event()
    allow_first_miss_return = threading.Event()
    second_miss = threading.Event()
    call_lock = threading.Lock()
    calls = 0

    class RaceCache(dict):
        misses = 0

        def get(self, key, default=None):  # type: ignore[no-untyped-def]
            if key in self:
                return super().get(key, default)
            self.misses += 1
            if self.misses == 1:
                first_miss.set()
                assert allow_first_miss_return.wait(3.0)
            elif self.misses == 2:
                second_miss.set()
            return default

    def fake_analyze_prosody(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        nonlocal calls
        with call_lock:
            calls += 1
        return ProsodyTrack(
            duration_ms=1000,
            points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
            pitch_min_hz=220.0,
            pitch_max_hz=220.0,
            source_filename=path.name,
            analyzer_name="race-test",
        )

    race_cache = RaceCache()
    monkeypatch.setattr(prosody_cache, "_ANALYSIS_CACHE", race_cache)
    monkeypatch.setattr(prosody_cache, "analyze_prosody", fake_analyze_prosody)

    results: list[ProsodyTrack] = []

    def worker() -> None:
        results.append(analyze_prosody_cached(audio, AudioProcessingConfig()))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    assert first_miss.wait(2)
    second_miss.wait(0.2)
    allow_first_miss_return.set()
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()

    assert len(results) == 2
    assert results[0] == results[1]
    assert calls == 1
