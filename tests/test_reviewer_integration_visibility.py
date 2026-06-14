"""Reviewer integration tests focused on visibility controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor import reviewer_integration
from anki_audio_quick_editor.reviewer_integration import (
    _on_card_will_show,
    _on_reviewer_will_show_context_menu,
    reviewer_editor_menu_label,
    toggle_reviewer_editor_visibility,
)
from tests.reviewer_integration_fixtures import (
    FakeCard,
    FakeMenu,
    FakeNote,
    FakeRenderedAudioCard,
    FakeWeb,
)


def test_toggle_hides_visible_answer_editor() -> None:
    web = FakeWeb()
    reviewer = SimpleNamespace(
        mw=aqt.mw,
        web=web,
        card=FakeCard(FakeNote(["[sound:first.mp3]"])),
        state="answer",
        _showAnswer=MagicMock(),
    )
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    assert reviewer_editor_menu_label() == "Hide audio editor"

    toggle_reviewer_editor_visibility()

    assert reviewer_editor_menu_label() == "Show audio editor"
    assert web.evals == ["window.__aqeEditorDispose && window.__aqeEditorDispose()"]


def test_toggle_shows_answer_editor_by_rerendering_answer() -> None:
    web = FakeWeb()
    reviewer = SimpleNamespace(
        mw=aqt.mw,
        web=web,
        card=FakeCard(FakeNote(["[sound:first.mp3]"])),
        state="answer",
        _showAnswer=MagicMock(),
    )
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}
    toggle_reviewer_editor_visibility()

    toggle_reviewer_editor_visibility()

    reviewer._showAnswer.assert_called_once()


def test_toggle_shows_answer_editor_when_setting_disabled() -> None:
    web = FakeWeb()
    reviewer = SimpleNamespace(
        mw=aqt.mw,
        web=web,
        card=FakeRenderedAudioCard(FakeNote(["[sound:first.mp3]", "[sound:second.wav]"])),
        state="answer",
        _showAnswer=MagicMock(),
    )
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}

    assert reviewer_editor_menu_label() == "Show audio editor"

    toggle_reviewer_editor_visibility()

    reviewer._showAnswer.assert_called_once()


def test_reviewer_targets_not_added_when_setting_disabled() -> None:
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}

    html = _on_card_will_show(
        "<div>[sound:first.mp3] [sound:second.wav]</div>",
        FakeRenderedAudioCard(FakeNote(["[sound:first.mp3]", "[sound:second.wav]"])),
        "reviewAnswer",
    )

    assert "aqe-review-audio-target" not in html


def test_reviewer_more_menu_adds_audio_editor_toggle(monkeypatch) -> None:
    menu = FakeMenu()
    reviewer = SimpleNamespace(state="question", card=FakeCard(FakeNote(["[sound:first.mp3]"])))
    connections: dict[object, object] = {}
    monkeypatch.setattr(
        reviewer_integration,
        "qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    _on_reviewer_will_show_context_menu(reviewer, menu)

    assert menu.separator_count == 1
    assert menu.actions[0].label == "Show audio editor"
    assert menu.actions[0].enabled is True
    assert menu.actions[0].triggered in connections
