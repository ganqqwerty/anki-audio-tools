"""Editor bridge pending web payload command tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import _handle_bridge_command
from tests.editor_bridge_command_fixtures import attach_clip_session, make_editor


def test_bridge_defers_pending_payload_from_web_callback(tmp_path: Path, monkeypatch) -> None:
    class Web:
        def __init__(self) -> None:
            self.eval_calls: list[str] = []
            self.callback_expression = ""

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, expression: str, callback: Callable[[object], None]) -> None:
            self.callback_expression = expression
            callback({"command": "aqe:volume-up", "fieldOrd": 0, "overrides": {"volumeStepDb": 6}})

    editor = make_editor(web=Web())
    session, source = attach_clip_session(editor, tmp_path)
    rendered: dict[str, AudioEditState] = {}
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.session_and_source", lambda _editor: (session, source))
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {})
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    _handle_bridge_command(editor, "aqe:command-payload")

    assert "window.__aqePendingCommandPayload" in editor.web.callback_expression
    assert rendered["state"] == AudioEditState("clip.mp3", volume_db=6)


def test_pending_payload_missing_clears_busy_state() -> None:
    class Web:
        def __init__(self) -> None:
            self.eval_calls: list[str] = []

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback(None)

    editor = make_editor(current_field=3, web=Web())

    _handle_bridge_command(editor, "aqe:command-payload")

    assert any("window.__aqeSetBusy" in call and "(3, false" in call for call in editor.web.eval_calls)


def test_bridge_saves_split_button_defaults_from_pending_payload() -> None:
    class Web:
        def __init__(self) -> None:
            self.callback_expression = ""
            self.eval_calls: list[str] = []

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, expression: str, callback: Callable[[object], None]) -> None:
            self.callback_expression = expression
            callback(
                {
                    "defaults": {
                        "denoiseAlgorithm": "dpdfnet",
                        "dpdfnetAttnLimitDb": 17.4,
                        "graphConnectShortDropoutsMs": 999,
                        "graphRecordingCondition": "studio",
                        "graphSmoothness": "smooth",
                        "graphVoiceLock": "stable",
                        "graphVoiceRange": "child",
                        "pauseAggressiveness": "aggressive",
                        "pitchHumMode": "pitch_tier",
                        "repeatPauseSeconds": 20,
                        "repeatPlaybackByDefault": True,
                        "shareTarget": "catbox",
                        "speedStep": 9,
                        "voiceRecordingCountdownSeconds": 20,
                        "volumeStepDb": 99,
                    },
                    "fieldOrd": 0,
                }
            )

    addon_manager = MagicMock()
    addon_manager.addonFromModule.return_value = "anki_audio_quick_editor"
    addon_manager.getConfig.return_value = {
        "denoise_algorithm": "standard",
        "graph_voice_range": "general",
        "speed_step": 1.5,
    }
    editor = make_editor(web=Web())
    editor.mw = MagicMock(addonManager=addon_manager)

    _handle_bridge_command(editor, "aqe:save-split-defaults")

    assert "__aqePopPendingSplitDefaultSaveRequest" in editor.web.callback_expression
    addon_manager.writeConfig.assert_called_once()
    addon_id, saved_config = addon_manager.writeConfig.call_args.args
    assert addon_id == "anki_audio_quick_editor"
    assert saved_config == {
        "denoise_algorithm": "dpdfnet",
        "dpdfnet_attn_limit_db": 18.0,
        "graph_connect_short_dropouts_ms": 500,
        "graph_recording_condition": "studio",
        "graph_smoothness": "smooth",
        "graph_voice_lock": "stable",
        "graph_voice_range": "child",
        "pause_aggressiveness": "aggressive",
        "pitch_hum_mode": "pitch_tier",
        "repeat_pause_seconds": 10.0,
        "repeat_playback_by_default": True,
        "share_target": "catbox",
        "speed_step": 5.0,
        "voice_recording_countdown_seconds": 10,
        "volume_step_db": 40.0,
    }
    assert any("Saved quick settings as defaults." in call for call in editor.web.eval_calls)
