from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_reload_status import (
    reload_editor_with_pending_status,
)
from anki_audio_quick_editor.editor_session import EditorSession, PendingEditorStatus


def test_reload_editor_with_pending_status_preserves_status_through_load() -> None:
    session = EditorSession()
    load_observed: list[PendingEditorStatus | None] = []

    editor = SimpleNamespace()
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: load_observed.append(session.pending_status))
    deps = SimpleNamespace(dispose_editor_frontend_controls=MagicMock())

    reload_editor_with_pending_status(
        editor,
        session,
        2,
        message="Closed settings.",
        kind="info",
        deps=deps,
    )

    expected = PendingEditorStatus(2, kind="info", message="Closed settings.")
    assert load_observed == [expected]
    assert session.pending_status == expected
    deps.dispose_editor_frontend_controls.assert_called_once_with(editor)
    editor.loadNote.assert_called_once_with(focusTo=2)


def test_reload_editor_with_pending_status_supports_missing_session() -> None:
    editor = SimpleNamespace(loadNote=MagicMock())
    deps = SimpleNamespace(dispose_editor_frontend_controls=MagicMock())

    reload_editor_with_pending_status(
        editor,
        None,
        1,
        message="Deleted selection 500-1250 ms.",
        deps=deps,
    )

    deps.dispose_editor_frontend_controls.assert_called_once_with(editor)
    editor.loadNote.assert_called_once_with(focusTo=1)


def test_reload_editor_with_pending_status_clears_stale_status_without_message() -> None:
    session = EditorSession(pending_status=PendingEditorStatus(3, message="Old status."))
    load_observed: list[PendingEditorStatus | None] = []

    editor = SimpleNamespace()
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: load_observed.append(session.pending_status))
    deps = SimpleNamespace(dispose_editor_frontend_controls=MagicMock())

    reload_editor_with_pending_status(
        editor,
        session,
        3,
        deps=deps,
    )

    assert load_observed == [None]
    assert session.pending_status is None
    deps.dispose_editor_frontend_controls.assert_called_once_with(editor)
    editor.loadNote.assert_called_once_with(focusTo=3)
