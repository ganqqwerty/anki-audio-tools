"""Tests for injected editor controls."""

from __future__ import annotations

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices() -> None:
    script = injection_script([1, 3])

    assert "const audioFieldIndices = new Set([1, 3]);" in script
    assert '.field-container[data-index="' in script
    assert "button.dataset.aqeCommand = command;" in script
    assert '"aqe:undo"' in script
    assert '"aqe:show-file"' in script
    assert 'pycmd("aqe:analyze");' in script
    assert 'pycmd("aqe:set-cursor");' in script
    assert '"aqe:save"' not in script
    assert '"aqe:cancel"' not in script
    assert '"aqe:untrim-left"' not in script
    assert '"aqe:untrim-right"' not in script
    assert 'makeButton("+L"' not in script
    assert 'makeButton("+R"' not in script
    assert "window.__aqeSetBusy = setControlsBusy;" in script
    assert "window.__aqeSetVisualizer =" in script
    assert "class=\"aqe-visualizer-svg\"" in script
    assert "Hz`" in script
    assert "button.disabled = !!busy;" in script
    assert "status.title = command || \"\";" in script
    assert 'pycmd("focus:" + ord);' in script
    assert 'makeButton("Folder", "Show current audio file in folder", "aqe:show-file"' in script


def test_graph_is_user_requested_and_redraws_after_active_edits() -> None:
    script = injection_script([0])

    assert 'makeButton("Graph", "Analyze and show pitch/intensity graph", "aqe:analyze"' in script
    assert "requestGraph(ord, true);" in script
    assert "rememberGraphRedrawIfActive" not in script
    assert "redrawAfterEditKey" not in script
    assert "sessionStorage" not in script
    assert "function audioSourceForNode(node)" in script
    assert "const existingControls = Array.from" in script
    assert "controls.dataset.aqeSourceFilename === sourceFilename" in script
    assert "existingControls.forEach((controls) => controls.remove());" in script
    assert "controls.dataset.aqeSourceFilename = sourceFilename;" in script
    assert 'document.querySelectorAll(".aqe-controls").forEach((node) => node.remove());' not in script
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
    assert 'setControlsBusy(ord, false, "", "");' in script


def test_disabled_button_styling_is_visible_without_color() -> None:
    script = injection_script([0])

    assert ".aqe-controls[data-busy=" in script
    assert "border-style: dashed;" in script
    assert ".aqe-button:disabled" in script
    assert "cursor: not-allowed;" in script
    assert "opacity: 0.45;" in script


def test_playback_finish_and_cursor_drag_intents_are_injected() -> None:
    script = injection_script([0])

    assert 'pycmd("aqe:play-ended");' in script
    assert 'clearStatus(ord);' in script
    assert 'setCursor(visualizer, anchorMs, false, { updateAnchor: false });' in script
    assert 'visualizer.dataset.resumeRequiresRestart = "true";' in script
    assert 'const restartPlayback = previousPlaybackState === "playing";' in script
    assert "window.__aqeGetCursorIntent" in script
    assert "anchorMs" in script
