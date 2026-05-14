"""Tests for injected editor controls."""

from __future__ import annotations

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices() -> None:
    script = injection_script([1, 3])

    assert "const audioFieldIndices = new Set([1, 3]);" in script
    assert '.field-container[data-index="' in script
    assert "button.dataset.aqeCommand = command;" in script
    assert '"aqe:undo"' in script
    assert 'pycmd("aqe:analyze");' in script
    assert 'pycmd("aqe:set-cursor");' in script
    assert '"aqe:save"' not in script
    assert '"aqe:cancel"' not in script
    assert "window.__aqeSetBusy = setControlsBusy;" in script
    assert "window.__aqeSetVisualizer =" in script
    assert "class=\"aqe-visualizer-svg\"" in script
    assert "Hz`" in script
    assert "button.disabled = !!busy;" in script
    assert "status.title = command || \"\";" in script
    assert 'pycmd("focus:" + ord);' in script


def test_graph_is_user_requested_and_redraws_after_active_edits() -> None:
    script = injection_script([0])

    assert 'makeButton("Graph", "Analyze and show pitch/intensity graph", "aqe:analyze"' in script
    assert "requestGraph(ord, true);" in script
    assert "rememberGraphRedrawIfActive(ord);" in script
    assert "sessionStorage.setItem(redrawAfterEditKey(ord), \"true\");" in script
    assert "sessionStorage.removeItem(redrawAfterEditKey(ord));" in script
    assert "requestAnalysis" not in script


def test_visualizer_has_progress_axis_and_lock_test_hooks() -> None:
    script = injection_script([0])

    assert "durationMs < 2000" in script
    assert "return `${Math.round(ms)} ms`;" in script
    assert "setControlsBusy(ord, true, \"Analyzing...\", \"\");" in script
    assert "document.body.dataset.aqeBusy" in script
    assert "window.__aqeGraphStateForTest" in script
    assert "window.__aqeSetCursorByClientXForTest" in script
    assert "window.__aqeSetPlaybackState" in script
    assert "window.requestAnimationFrame(tick)" in script
