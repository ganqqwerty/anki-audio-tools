"""Tests for injected editor controls."""

from __future__ import annotations

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices() -> None:
    script = injection_script([1, 3])

    assert "const audioFieldIndices = new Set([1, 3]);" in script
    assert '.field-container[data-index="' in script
    assert "button.dataset.aqeCommand = command;" in script
    assert '"aqe:undo"' in script
    assert '"aqe:save"' not in script
    assert '"aqe:cancel"' not in script
    assert "window.__aqeSetBusy = setControlsBusy;" in script
    assert "button.disabled = !!busy;" in script
    assert "status.title = command || \"\";" in script
    assert 'pycmd("focus:" + ord);' in script
