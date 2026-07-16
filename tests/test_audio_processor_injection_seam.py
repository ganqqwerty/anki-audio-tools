"""Behavior tests for the public typed audio dependency seam."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from anki_audio_quick_editor import audio_processor as facade
from anki_audio_quick_editor import audio_rendering


def test_typed_dependency_installation_changes_leaf_resolution() -> None:
    expected = Path("/typed-deps/ffmpeg")
    deps = replace(
        facade.audio_module_dependencies(),
        find_ffmpeg=lambda _configured="": expected,
    )

    facade.install_audio_dependencies(deps)

    assert audio_rendering.find_ffmpeg("") == expected


def test_public_facade_routes_output_naming_to_rendering_leaf(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        audio_rendering,
        "make_output_filename",
        lambda source, _now, _token, *, output_format: calls.append((source, output_format))
        or "observable.mp3",
    )

    result = facade.make_output_filename("source.wav", output_format="mp3")

    assert result == "observable.mp3"
    assert calls == [("source.wav", "mp3")]
