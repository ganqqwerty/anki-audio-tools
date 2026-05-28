from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_frontend import (
    eval_status,
    eval_visualizer_status_for_field,
)
from anki_audio_quick_editor.error_codes import (
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    coded_error,
)


def test_eval_status_accepts_user_facing_error_payload() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    payload = coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, "No [sound:...] reference found.")

    eval_status(editor, payload, kind="error")

    script = editor.web.eval.call_args.args[0]
    assert '"code": "AQE-MEDIA-001"' in script
    assert '"message": "No [sound:...] reference found."' in script
    assert '"error"' in script


def test_eval_visualizer_status_accepts_user_facing_error_payload() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    payload = coded_error("AQE-GRAPH-001", "Audio visualization failed.")

    eval_visualizer_status_for_field(editor, 3, payload, kind="error")

    script = editor.web.eval.call_args.args[0]
    assert "window.__aqeSetVisualizerStatus" in script
    assert '"code": "AQE-GRAPH-001"' in script
