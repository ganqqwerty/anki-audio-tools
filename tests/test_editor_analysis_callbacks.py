"""Editor prosody analysis callback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_callbacks import (
    _analysis_failed,
    _analysis_finished,
    handle_bridge_command,
)
from anki_audio_quick_editor.editor_note_load_hooks import (
    reset_editor_session_for_note_load,
)
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import AnalysisState, EditorSession
from anki_audio_quick_editor.prosody_types import (
    FFMPEG_PCM_ANALYSIS_WARNING,
    FFMPEG_PCM_ANALYZER,
    ProsodyPoint,
    ProsodyTrack,
)
from tests.thread_fakes import ImmediateThread


def test_stale_analysis_completion_is_ignored_after_note_load_reset() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    session = EditorSession(
        note_id=10,
        field_index=0,
        analysis=AnalysisState(busy=True, busy_fields={0}, generation=2, generations_by_field={0: 2}),
    )
    SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )

    reset_editor_session_for_note_load(editor, 11)
    _analysis_finished(editor, 2, 0, track)

    assert session.analysis.generation == 3
    assert session.graph.visualized_duration_ms is None
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert len(evals) == 1
    assert "__aqeSetHistoryAvailability" in evals[0]
    assert "__aqeSetVisualizer(0," not in evals[0]


def test_analysis_completion_after_web_teardown_clears_state_without_publication() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.web = None
    session = EditorSession(
        field_index=0,
        analysis=AnalysisState(busy=True, busy_fields={0}, generation=2, generations_by_field={0: 2}),
    )
    SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )

    _analysis_finished(editor, 2, 0, track)

    assert session.analysis.busy is False
    assert session.analysis.generations_by_field == {}
    assert session.graph.filenames_by_field == {}
    assert session.graph.durations_by_field == {}


def test_analysis_failure_after_web_teardown_clears_state_without_publication() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.web = None
    session = EditorSession(
        field_index=0,
        analysis=AnalysisState(busy=True, busy_fields={0}, generation=2, generations_by_field={0: 2}),
    )
    SESSIONS[editor] = session

    _analysis_failed(editor, 2, 0, "analysis failed")

    assert session.analysis.busy is False
    assert session.analysis.generations_by_field == {}


def test_analysis_completion_renders_requested_field_when_session_tracks_another_field() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.web = MagicMock()
    session = EditorSession(
        backend_media_generation=7,
        field_index=0,
        current_filename="field-one.mp3",
        analysis=AnalysisState(busy=True, busy_fields={1}, generation=2, generations_by_field={1: 2}),
    )
    SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )

    _analysis_finished(editor, 2, 1, track)

    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()
    assert session.field_index == 0
    assert session.graph.durations_by_field[1] == 900
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetVisualizer(1," in call for call in evals)
    assert any(call.rstrip().endswith(", 7)") for call in evals)


def test_analysis_completion_warns_when_graph_uses_ffmpeg_pcm_fallback() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    session = EditorSession(
        field_index=0,
        analysis=AnalysisState(busy=True, busy_fields={0}, generation=2, generations_by_field={0: 2}),
    )
    SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-one.mp3",
        analyzer_name=FFMPEG_PCM_ANALYZER,
    )

    _analysis_finished(editor, 2, 0, track)

    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any('"analysisWarning":' in call and FFMPEG_PCM_ANALYSIS_WARNING in call for call in evals)
    assert not any("__aqeSetVisualizerStatus" in call and '"warning"' in call for call in evals)


def test_field_addressed_analysis_preserves_edit_session_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "field-one.mp3").write_bytes(b"one")
    field_two = media_dir / "field-two.mp3"
    field_two.write_bytes(b"two")
    track = ProsodyTrack(
        duration_ms=1200,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )
    analyzed: list[tuple[Path, AudioProcessingConfig]] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:field-one.mp3]", "[sound:field-two.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("field-one.mp3", speed=1.1),
        field_index=0,
        current_filename="field-one.mp3",
    )
    session.undo_history.push(AudioEditState("field-one.mp3"), "field-one.mp3")
    session.redo_history.push(AudioEditState("field-one.mp3", speed=1.1), "field-one__redo.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {
                "ord": 1,
                "sourceFilename": "field-two.mp3",
                "graphSettings": {
                    "voiceRange": "bass",
                    "recordingCondition": "noisy",
                    "smoothness": "smooth",
                    "connectShortDropoutsMs": 60,
                    "voiceLock": "stable",
                },
            }
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda path, config: analyzed.append((path, config)) or track,
    )

    handle_bridge_command(editor, "aqe:analyze-field")

    assert [path for path, _config in analyzed] == [field_two]
    assert [config.graph_voice_range for _path, config in analyzed] == ["bass"]
    assert [config.graph_recording_condition for _path, config in analyzed] == ["noisy"]
    assert [config.graph_smoothness for _path, config in analyzed] == ["smooth"]
    assert [config.graph_connect_short_dropouts_ms for _path, config in analyzed] == [60]
    assert [config.graph_voice_lock for _path, config in analyzed] == ["stable"]
    assert session.state == AudioEditState("field-one.mp3", speed=1.1)
    assert session.field_index == 0
    assert session.current_filename == "field-one.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["field-one.mp3"]
    assert [entry.filename for entry in session.redo_history.entries] == ["field-one__redo.mp3"]
    assert session.graph.durations_by_field[1] == 1200
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetVisualizer(1," in call for call in evals)


def test_manual_analysis_uses_read_only_field_path(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "field-one.mp3").write_bytes(b"one")
    field_two = media_dir / "field-two.mp3"
    field_two.write_bytes(b"two")
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )
    analyzed: list[Path] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 1
    editor.note = SimpleNamespace(fields=["[sound:field-one.mp3]", "[sound:field-two.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("field-one.mp3", volume_db=3.0),
        field_index=0,
        current_filename="field-one.mp3",
    )
    session.undo_history.push(AudioEditState("field-one.mp3"), "field-one.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda path, _config: analyzed.append(path) or track,
    )

    handle_bridge_command(editor, "aqe:analyze")

    assert analyzed == [field_two]
    assert session.state == AudioEditState("field-one.mp3", volume_db=3.0)
    assert session.field_index == 0
    assert session.current_filename == "field-one.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["field-one.mp3"]
    assert session.graph.durations_by_field[1] == 900


def test_manual_analysis_payload_applies_graph_settings(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "field-one.mp3").write_bytes(b"one")
    field_two = media_dir / "field-two.mp3"
    field_two.write_bytes(b"two")
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )
    analyzed: list[tuple[Path, AudioProcessingConfig]] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:field-one.mp3]", "[sound:field-two.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("field-one.mp3", volume_db=3.0),
        field_index=0,
        current_filename="field-one.mp3",
    )
    session.undo_history.push(AudioEditState("field-one.mp3"), "field-one.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda path, config: analyzed.append((path, config)) or track,
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:analyze","fieldOrd":1,'
        '"graphSettings":{"voiceRange":"child","recordingCondition":"studio",'
        '"smoothness":"very_smooth","connectShortDropoutsMs":90,"voiceLock":"stable"}}',
    )

    assert [path for path, _config in analyzed] == [field_two]
    assert [config.graph_voice_range for _path, config in analyzed] == ["child"]
    assert [config.graph_recording_condition for _path, config in analyzed] == ["studio"]
    assert [config.graph_smoothness for _path, config in analyzed] == ["very_smooth"]
    assert [config.graph_connect_short_dropouts_ms for _path, config in analyzed] == [90]
    assert [config.graph_voice_lock for _path, config in analyzed] == ["stable"]
    assert editor.currentField == 1
    assert session.state == AudioEditState("field-one.mp3", volume_db=3.0)


def test_stale_field_addressed_analysis_request_is_ignored(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "new.mp3").write_bytes(b"new")
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:new.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("new.mp3"),
        field_index=0,
        current_filename="new.mp3",
    )
    session.undo_history.push(AudioEditState("new.mp3"), "new.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback({"ord": 0, "sourceFilename": "old.mp3"}),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda *_args, **_kwargs: pytest.fail("stale graph requests should not analyze audio"),
    )

    handle_bridge_command(editor, "aqe:analyze-field")

    assert session.state == AudioEditState("new.mp3")
    assert [entry.filename for entry in session.undo_history.entries] == ["new.mp3"]
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetBusy && window.__aqeSetBusy(0, false" in call for call in evals)
    assert any("window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus(0" in call for call in evals)
