from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_processing_preset_runner import (
    ProcessingPresetRunResult,
)
from anki_audio_quick_editor.editor_actions import EditorCommandPayload
from anki_audio_quick_editor.editor_presets import run_processing_preset_async
from anki_audio_quick_editor.editor_session import EditorSession
from tests.editor_bridge_command_fixtures import make_editor
from tests.thread_fakes import ImmediateThread


def _preset_config(*, graph_enabled: bool, steps: list[dict]) -> dict:
    return {
        "audio_processing_presets": [
            {
                "id": "clean_graph",
                "name": "Clean + graph",
                "steps": steps,
                "graph": {
                    "enabled": graph_enabled,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ]
    }


def _deps(editor, session: EditorSession, source: Path, config: dict) -> SimpleNamespace:
    return SimpleNamespace(
        analyze_current_async=MagicMock(),
        analyze_prosody_cached=MagicMock(),
        artifact_root=MagicMock(return_value=source.parent / "artifacts"),
        config=MagicMock(return_value=config),
        current_media_path=MagicMock(return_value=(session, source)),
        eval_playback_state=MagicMock(),
        eval_status=MagicMock(),
        main=lambda _editor, callback: callback(),
        make_output_filename=lambda filename, **_kwargs: filename,
        render_audio=MagicMock(),
        render_converted_audio=MagicMock(),
        render_dpdfnet_audio=MagicMock(),
        render_failed=MagicMock(),
        render_noise_reduced_audio=MagicMock(),
        render_rnnoise_audio=MagicMock(),
        render_voice_only_audio=MagicMock(),
        replace_current_field_after_special_transform=MagicMock(),
        request_graph_redraw=MagicMock(),
        sessions={editor: session},
        set_busy=MagicMock(),
        still_processing_message="Still processing. Please wait.",
        stop_session_playback=MagicMock(),
        temp_final_path=lambda filename: source.parent / "tmp" / filename,
        threading=SimpleNamespace(Thread=ImmediateThread),
    )


def test_editor_preset_graph_only_runs_graph_with_preset_settings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor = make_editor()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    session = EditorSession(field_index=0, current_filename="clip.mp3")
    deps = _deps(editor, session, source, _preset_config(graph_enabled=True, steps=[]))
    run_calls: list[dict[str, object]] = []

    def fake_run_processing_preset(*_args, **kwargs) -> ProcessingPresetRunResult:
        run_calls.append(kwargs)
        return ProcessingPresetRunResult(None, None, None, None, (), False)

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_presets.run_processing_preset",
        fake_run_processing_preset,
    )

    run_processing_preset_async(
        editor,
        EditorCommandPayload(command="aqe:preset", preset_id="clean_graph"),
        deps,
    )

    assert run_calls[0]["render_graph"] is False
    assert session.processing.active is False
    deps.analyze_current_async.assert_called_once_with(
        editor,
        graph_settings={
            "connectShortDropoutsMs": 240,
            "recordingCondition": "auto",
            "smoothness": "very_smooth",
            "voiceLock": "balanced",
            "voiceRange": "general",
        },
    )


def test_editor_preset_transform_replaces_audio_and_requests_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor = make_editor()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    final_audio = tmp_path / "tmp" / "clip__preset.mp3"
    final_audio.parent.mkdir()
    final_audio.write_bytes(b"preset audio")
    session = EditorSession(field_index=0, current_filename="clip.mp3")
    deps = _deps(
        editor,
        session,
        source,
        _preset_config(
            graph_enabled=True,
            steps=[
                {
                    "id": "denoise",
                    "operation": "denoise",
                    "parameters": {"denoise_algorithm": "standard"},
                }
            ],
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_presets.run_processing_preset",
        lambda *_args, **_kwargs: ProcessingPresetRunResult(
            final_audio,
            "clip__preset.mp3",
            b"",
            "clip__preset.mp3",
            (),
            True,
        ),
    )

    run_processing_preset_async(
        editor,
        EditorCommandPayload(command="aqe:preset", preset_id="clean_graph"),
        deps,
    )

    deps.replace_current_field_after_special_transform.assert_called_once()
    assert deps.replace_current_field_after_special_transform.call_args.kwargs["output_path"] == final_audio
    deps.request_graph_redraw.assert_called_once()
    assert deps.request_graph_redraw.call_args.args[2]["voiceRange"] == "general"
    assert not final_audio.parent.exists()
