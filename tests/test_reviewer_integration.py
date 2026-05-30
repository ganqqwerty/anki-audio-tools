"""Reviewer integration tests for reused inline editor controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor import reviewer_integration
from anki_audio_quick_editor.reviewer_integration import (
    ReviewerEditorAdapter,
    _handle_reviewer_bridge_command,
    _on_card_review_webview_did_init,
    _on_card_will_show,
    _on_reviewer_did_show_card_side,
    register_reviewer_hooks,
)


class FakeNote:
    def __init__(self, fields: list[str], note_id: int = 123) -> None:
        self.fields = fields
        self.id = note_id


class FakeCard:
    def __init__(self, note: FakeNote) -> None:
        self._note = note
        self.loaded = False

    def note(self, reload: bool = False) -> FakeNote:
        del reload
        return self._note

    def load(self) -> None:
        self.loaded = True

    def question_av_tags(self) -> list[object]:
        return [SimpleNamespace(filename="first.mp3")]

    def answer_av_tags(self) -> list[object]:
        return [SimpleNamespace(filename="second.wav")]


class FakeWeb:
    def __init__(self) -> None:
        self.onBridgeCmd = MagicMock(return_value="delegated")
        self.bridge_command = None
        self.evals: list[str] = []

    def set_bridge_command(self, func, context) -> None:
        del context
        self.bridge_command = func
        self.onBridgeCmd = func

    def eval(self, js: str) -> None:
        self.evals.append(js)


def test_register_reviewer_hooks() -> None:
    hooks = SimpleNamespace(
        card_review_webview_did_init=MagicMock(),
        card_will_show=MagicMock(),
        reviewer_did_show_question=MagicMock(),
        reviewer_did_show_answer=MagicMock(),
        reviewer_did_answer_card=MagicMock(),
    )

    register_reviewer_hooks(hooks)

    hooks.card_review_webview_did_init.append.assert_called_once()
    hooks.card_will_show.append.assert_called_once()
    hooks.reviewer_did_show_question.append.assert_called_once()
    hooks.reviewer_did_show_answer.append.assert_called_once()
    hooks.reviewer_did_answer_card.append.assert_called_once()


def test_card_will_show_adds_review_targets_for_rendered_audio() -> None:
    note = FakeNote(["[sound:first.mp3]", "[sound:second.wav]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _on_card_will_show("<div>play icon without filename</div>", card, "reviewAnswer")

    assert 'class="aqe-review-audio-target"' in html
    assert 'data-field-ord="1"' in html
    assert 'data-aqe-source-filename="second.wav"' in html
    assert 'data-field-ord="0"' not in html


def test_card_will_show_respects_reviewer_setting() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}

    html = _on_card_will_show("<div>[sound:first.mp3]</div>", card, "reviewQuestion")

    assert "aqe-review-audio-target" not in html


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
        "_handle_bridge_command",
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
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=card)
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    _on_reviewer_did_show_card_side(card)

    assert any("window.__AQE_EDITOR_CONFIG__" in script for script in web.evals)
