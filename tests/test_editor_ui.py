"""Tests for injected editor controls bundle wiring."""

from __future__ import annotations

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices_and_bundle() -> None:
    script = injection_script([1, 3])

    assert 'window.__AQE_EDITOR_CONFIG__ = {"audioFieldIndices": [1, 3]};' in script
    assert "window.__aqeEditorDispose" in script
    assert "aqe:frontend-log" in script
    assert "aqe:show-file" in script
    assert "aqe:volume-down" in script
    assert "aqe:volume-up" in script
    assert "aqe:sidon" in script
    assert "aqe:mp-senet" in script
    assert "aqe:save" not in script
    assert "aqe:cancel" not in script


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
