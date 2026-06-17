"""Reviewer integration tests focused on bridge and adapter command flow."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor import reviewer_integration
from anki_audio_quick_editor.reviewer_integration import (
    ReviewerEditorAdapter,
    _handle_reviewer_bridge_command,
    _on_card_review_webview_did_init,
    _on_reviewer_did_show_card_side,
)
from tests.reviewer_integration_fixtures import (
    FakeCard,
    FakeNote,
    FakeWeb,
)


def test_reviewer_bridge_delegates_non_aqe_commands(monkeypatch) -> None:
    web = FakeWeb()
    kind = SimpleNamespace(name="MAIN", value="main")
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=FakeCard(FakeNote(["[sound:first.mp3]"])))
    aqt.mw.reviewer = reviewer

    _on_card_review_webview_did_init(web, kind)

    assert web.bridge_command("ans") == "delegated"


def test_reviewer_bridge_dispatches_aqe_commands(monkeypatch) -> None:
    note = FakeNote(["[sound:first.mp3]"])
    web = FakeWeb()
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=FakeCard(note))
    calls: list[tuple[object, str]] = []
    monkeypatch.setattr(
        reviewer_integration,
        "handle_bridge_command",
        lambda editor, command: calls.append((editor, command)),
    )

    _handle_reviewer_bridge_command(reviewer, "focus:0")
    _handle_reviewer_bridge_command(reviewer, "aqe:play")

    adapter, command = calls[0]
    assert isinstance(adapter, ReviewerEditorAdapter)
    assert adapter.currentField == 0
    assert command == "aqe:play"


def test_reviewer_adapter_load_note_persists_and_rerenders_question() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    web = FakeWeb()
    reviewer = SimpleNamespace(
        mw=aqt.mw,
        web=web,
        card=card,
        state="question",
        _showQuestion=MagicMock(),
        _showAnswer=MagicMock(),
    )
    adapter = ReviewerEditorAdapter(reviewer)

    adapter.loadNote(focusTo=0)

    aqt.mw.col.update_note.assert_called_once_with(note)
    assert card.loaded is True
    reviewer._showQuestion.assert_called_once()
    reviewer._showAnswer.assert_not_called()
    assert adapter.currentField == 0


def test_reviewer_did_show_injects_shared_editor_script() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    web = FakeWeb()
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=card, state="answer")
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    _on_reviewer_did_show_card_side(card)

    assert any("window.__AQE_EDITOR_CONFIG__" in script for script in web.evals)


def test_reviewer_did_show_question_disposes_frontend() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    web = FakeWeb()
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=card, state="question")
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    _on_reviewer_did_show_card_side(card)

    assert web.evals == ["window.__aqeEditorDispose && window.__aqeEditorDispose()"]
