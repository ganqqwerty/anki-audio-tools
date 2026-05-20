"""Tests for analyzer selection and optional Praat adapter behavior."""

from __future__ import annotations

import sys
import types
from pathlib import Path

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_analyzer import analyze_prosody
from anki_audio_quick_editor.prosody_praat import analyze_with_praat
from anki_audio_quick_editor.prosody_types import ProsodyPoint, build_prosody_track


def test_analyzer_selection_falls_back_when_praat_fails(monkeypatch, tmp_path: Path) -> None:
    fallback_track = build_prosody_track(
        duration_ms=100,
        points=[ProsodyPoint(0, 220, -20, 0.0, True)],
        source_filename="clip.wav",
        analyzer_name="fallback",
    )
    monkeypatch.setattr("anki_audio_quick_editor.prosody_analyzer.is_praat_available", lambda: True)
    monkeypatch.setattr(
        "anki_audio_quick_editor.prosody_analyzer.analyze_with_praat",
        lambda _path, _config: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.prosody_analyzer.analyze_with_fallback",
        lambda _path, _config: fallback_track,
    )

    track = analyze_prosody(tmp_path / "clip.wav", AudioProcessingConfig())

    assert track is fallback_track


def test_praat_adapter_converts_voiced_unvoiced_and_intensity(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"fake")

    class FakePitch:
        selected_array = {"frequency": [0.0, 220.25]}

        def xs(self):
            return [0.0, 0.01]

    class FakeIntensity:
        values = [[35.0, 55.0]]

        def xs(self):
            return [0.0, 0.01]

    class FakeSound:
        def __init__(self, path: str) -> None:
            self.path = path

        def to_pitch(self, **_kwargs):
            return FakePitch()

        def to_intensity(self, **_kwargs):
            return FakeIntensity()

    fake_module = types.SimpleNamespace(Sound=FakeSound)
    monkeypatch.setitem(sys.modules, "parselmouth", fake_module)
    monkeypatch.setattr("anki_audio_quick_editor.prosody_praat.probe_duration_ms", lambda *_args: 20)

    track = analyze_with_praat(source, AudioProcessingConfig())

    assert track.analyzer_name == "praat-parselmouth"
    assert track.duration_ms == 20
    assert track.points[0].pitch_hz is None
    assert track.points[1].pitch_hz == 220.25
    assert track.points[1].intensity_db == 55.0


def test_praat_adapter_uses_nearest_intensity_frame(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "nearest.wav"
    source.write_bytes(b"fake")
    _install_fake_parselmouth(
        monkeypatch,
        pitch_times=[0.002, 0.018, 0.031],
        frequencies=[180.0, 220.0, 260.0],
        intensity_times=[0.0, 0.02, 0.04],
        intensity_values=[30.0, 60.0, 45.0],
    )
    monkeypatch.setattr("anki_audio_quick_editor.prosody_praat.probe_duration_ms", lambda *_args: 40)

    track = analyze_with_praat(source, AudioProcessingConfig())

    assert [point.intensity_db for point in track.points] == [30.0, 60.0, 45.0]


def test_praat_adapter_derives_pitch_bounds_from_voiced_frames_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "bounds.wav"
    source.write_bytes(b"fake")
    _install_fake_parselmouth(
        monkeypatch,
        pitch_times=[0.0, 0.01, 0.02, 0.03, 0.04],
        frequencies=[0.0, 240.0, 120.0, 0.0, 300.0],
        intensity_times=[0.0, 0.02, 0.04],
        intensity_values=[35.0, 45.0, 55.0],
    )
    monkeypatch.setattr("anki_audio_quick_editor.prosody_praat.probe_duration_ms", lambda *_args: 50)

    track = analyze_with_praat(
        source,
        AudioProcessingConfig(graph_connect_short_dropouts_ms=0, graph_smoothness="raw"),
    )

    assert [point.voiced for point in track.points] == [False, True, True, False, True]
    assert track.pitch_min_hz == 120.0
    assert track.pitch_max_hz == 300.0


def test_praat_adapter_tolerates_mismatched_pitch_and_intensity_lengths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "mismatched.wav"
    source.write_bytes(b"fake")
    _install_fake_parselmouth(
        monkeypatch,
        pitch_times=[0.0, 0.01, 0.02, 0.03],
        frequencies=[190.0, 210.0, 230.0],
        intensity_times=[0.0, 0.01, 0.02, 0.03],
        intensity_values=[40.0, 42.0],
    )
    monkeypatch.setattr("anki_audio_quick_editor.prosody_praat.probe_duration_ms", lambda *_args: 40)

    track = analyze_with_praat(source, AudioProcessingConfig())

    assert len(track.points) == 3
    assert track.points[0].intensity_db == 40.0
    assert track.points[1].intensity_db == 42.0
    assert track.points[2].intensity_db is None


def _install_fake_parselmouth(
    monkeypatch,
    *,
    pitch_times: list[float],
    frequencies: list[float],
    intensity_times: list[float],
    intensity_values: list[float],
) -> None:
    class FakePitch:
        selected_array = {"frequency": frequencies}

        def xs(self):
            return pitch_times

    class FakeIntensity:
        values = [intensity_values]

        def xs(self):
            return intensity_times

    class FakeSound:
        def __init__(self, path: str) -> None:
            self.path = path

        def to_pitch(self, **_kwargs):
            return FakePitch()

        def to_intensity(self, **_kwargs):
            return FakeIntensity()

    monkeypatch.setitem(sys.modules, "parselmouth", types.SimpleNamespace(Sound=FakeSound))
