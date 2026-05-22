"""Editor pitch-hum callback tests."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)


class ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


def _setup_editor(
    tmp_path: Path,
    *,
    config: dict[str, object] | None = None,
) -> tuple[object, Path, Path]:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value=config or {}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )
    return editor, media_dir, source


def _patch_common(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.threading.Thread",
        ImmediateThread,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)


def test_pitch_hum_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    editor, _media_dir, source = _setup_editor(tmp_path)
    rendered: list[Path] = []

    def fake_render_pitch_hum_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        **_kwargs,
    ) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"hum")

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_pitch_hum_audio",
        fake_render_pitch_hum_audio,
    )

    _handle_bridge_command(editor, "aqe:pitch-hum")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


def test_pitch_hum_uses_current_graph_analysis_settings(tmp_path: Path, monkeypatch) -> None:
    editor, _media_dir, source = _setup_editor(
        tmp_path,
        config={
            "graph_voice_range": "general",
            "graph_recording_condition": "normal",
            "graph_smoothness": "balanced",
            "graph_connect_short_dropouts_ms": 240,
            "graph_voice_lock": "balanced",
        },
    )
    configs: list[AudioProcessingConfig] = []

    def fake_render_pitch_hum_audio(
        source_path: Path,
        config: AudioProcessingConfig,
        output_path: Path,
        **_kwargs,
    ) -> None:
        assert source_path == source
        configs.append(config)
        output_path.write_bytes(b"hum")

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_pitch_hum_audio",
        fake_render_pitch_hum_audio,
    )

    _handle_bridge_command(
        editor,
        json.dumps(
            {
                "command": "aqe:pitch-hum",
                "fieldOrd": 0,
                "graphSettings": {
                    "connectShortDropoutsMs": 60,
                    "recordingCondition": "studio",
                    "smoothness": "very_smooth",
                    "voiceLock": "stable",
                    "voiceRange": "child",
                },
            }
        ),
    )

    assert len(configs) == 1
    assert configs[0].graph_voice_range == "child"
    assert configs[0].graph_recording_condition == "studio"
    assert configs[0].graph_smoothness == "very_smooth"
    assert configs[0].graph_connect_short_dropouts_ms == 60
    assert configs[0].graph_voice_lock == "stable"


def _assert_pitch_tier_renderer_selection(
    tmp_path: Path,
    monkeypatch,
    *,
    command: str,
    config: dict[str, object] | None = None,
) -> None:
    editor, _media_dir, source = _setup_editor(tmp_path, config=config)
    direct_calls: list[Path] = []
    pitch_tier_calls: list[Path] = []

    def fake_renderer(calls: list[Path], content: bytes) -> Callable[..., None]:
        def _render(
            source_path: Path,
            _config: AudioProcessingConfig,
            output_path: Path,
            **_kwargs,
        ) -> None:
            calls.append(source_path)
            output_path.write_bytes(content)

        return _render

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_pitch_hum_audio",
        fake_renderer(direct_calls, b"direct"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_pitch_tier_hum_audio",
        fake_renderer(pitch_tier_calls, b"pitch-tier"),
    )

    _handle_bridge_command(editor, command)

    assert direct_calls == []
    assert pitch_tier_calls == [source]


def test_pitch_hum_pitch_tier_mode_uses_pitch_tier_renderer(tmp_path: Path, monkeypatch) -> None:
    _assert_pitch_tier_renderer_selection(
        tmp_path,
        monkeypatch,
        command=json.dumps(
            {
                "command": "aqe:pitch-hum",
                "fieldOrd": 0,
                "overrides": {"pitchHumMode": "pitch_tier"},
            }
        ),
    )


def test_pitch_hum_saved_pitch_tier_default_uses_pitch_tier_renderer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _assert_pitch_tier_renderer_selection(
        tmp_path,
        monkeypatch,
        command="aqe:pitch-hum",
        config={"pitch_hum_mode": "pitch_tier"},
    )
