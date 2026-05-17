"""Tests for injected editor controls bundle wiring."""

from __future__ import annotations

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices_and_bundle() -> None:
    script = injection_script([1, 3])

    assert (
        'window.__AQE_EDITOR_CONFIG__ = {"audioFieldIndices": [1, 3], '
        '"audioFieldSources": {}, "repeatPlaybackByDefault": false, '
        '"showGraphByDefault": false};'
    ) in script
    assert "window.__aqeEditorDispose" in script
    assert "aqe:frontend-log" in script
    assert "aqe:show-file" in script
    assert "aqe:volume-down" in script
    assert "aqe:volume-up" in script
    assert "aqe:denoise-standard" in script
    assert "aqe:mp-senet" in script
    assert "aqe:redo" in script
    assert "aqe:settings" in script
    assert ("aqe:" + "remove" + "-noise") not in script
    assert "aqe:save" not in script
    assert "aqe:cancel" not in script


def test_injection_script_embeds_repeat_default() -> None:
    script = injection_script([0], repeat_playback_by_default=True)

    assert (
        'window.__AQE_EDITOR_CONFIG__ = {"audioFieldIndices": [0], '
        '"audioFieldSources": {}, "repeatPlaybackByDefault": true, '
        '"showGraphByDefault": false};'
    ) in script


def test_injection_script_embeds_show_graph_default() -> None:
    script = injection_script([0], show_graph_by_default=True)

    assert (
        'window.__AQE_EDITOR_CONFIG__ = {"audioFieldIndices": [0], '
        '"audioFieldSources": {}, "repeatPlaybackByDefault": false, '
        '"showGraphByDefault": true};'
    ) in script


def test_injection_script_embeds_audio_field_sources() -> None:
    script = injection_script([0, 2], audio_field_sources={0: "front.wav", 2: "back.mp3"})

    assert '"audioFieldSources": {"0": "front.wav", "2": "back.mp3"}' in script


def test_injection_script_keeps_python_window_contract() -> None:
    script = injection_script([0])

    assert "__aqeSetBusy" in script
    assert "__aqeSetStatus" in script
    assert "__aqeSetVisualizer" in script
    assert "__aqeSetVisualizerStatus" in script
    assert "__aqeGetPlaybackRequest" in script
    assert "__aqeGetCursorIntent" in script
    assert "__aqePopFrontendLog" in script
    assert "__aqeScan" in script
    assert "__aqeGraphStateForTest" in script


def test_injection_script_injects_editor_css() -> None:
    script = injection_script([0])

    assert "const styleId = \"aqe-inline-style\";" in script
    assert ".aqe-controls" in script
    assert ".aqe-button:disabled" in script
    assert "data-busy=true" in script
    assert "border-style:dashed" in script
    assert "aqe-spin" in script
