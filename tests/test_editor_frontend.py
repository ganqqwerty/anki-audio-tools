from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_frontend import (
    eval_status,
    eval_visualizer_status_for_field,
    graph_redraw_expression,
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


def test_eval_status_codes_plain_error_strings() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))

    eval_status(editor, "plain failure", kind="error")

    script = editor.web.eval.call_args.args[0]
    assert '"code": "AQE-AUDIO-001"' in script
    assert '"message": "plain failure"' in script


def test_eval_visualizer_status_codes_plain_error_strings() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))

    eval_visualizer_status_for_field(editor, 1, "graph failure", kind="error")

    script = editor.web.eval.call_args.args[0]
    assert '"code": "AQE-GRAPH-001"' in script
    assert '"message": "graph failure"' in script


def test_eval_status_logs_displayed_errors(caplog) -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_frontend.status")

    eval_status(editor, "plain failure", kind="error")

    assert "editor status displayed error: AQE-AUDIO-001: plain failure" in caplog.text


def test_eval_visualizer_status_logs_displayed_errors(caplog) -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_frontend.status")

    eval_visualizer_status_for_field(editor, 1, "graph failure", kind="error")

    assert "editor visualizer status field=1 displayed error: AQE-GRAPH-001: graph failure" in caplog.text


def test_eval_status_does_not_log_non_error_status(caplog) -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_frontend.status")

    eval_status(editor, "plain info")

    assert caplog.text == ""


def test_graph_redraw_expression_can_preserve_learner_overlay() -> None:
    script = graph_redraw_expression(2, "updated.mp3", preserve_learner_overlay=True)

    assert 'window.__aqeResetGraphAfterEdit(2, "updated.mp3", true)' in script
