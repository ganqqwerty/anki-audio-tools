"""Reviewer integration tests for reused inline editor controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt
import pytest

from anki_audio_quick_editor import reviewer_integration
from anki_audio_quick_editor.reviewer_integration import (
    ReviewerEditorAdapter,
    _handle_reviewer_bridge_command,
    _on_card_review_webview_did_init,
    _on_card_will_show,
    _on_reviewer_did_show_card_side,
    _on_reviewer_will_show_context_menu,
    register_reviewer_hooks,
    reviewer_editor_menu_label,
    toggle_reviewer_editor_visibility,
)


class FakeNote:
    def __init__(self, fields: list[str], note_id: int = 123) -> None:
        self.fields = fields
        self.id = note_id
        self.field_names = ["Front", "Back"][: len(fields)]

    def keys(self) -> list[str]:
        return self.field_names


@pytest.fixture(autouse=True)
def _reset_reviewer_visibility(monkeypatch) -> None:
    monkeypatch.setattr(reviewer_integration, "_reviewer_editor_visible", True)
    reviewer_integration._EXPLICIT_PANEL_CARD_KEYS.clear()


class FakeCard:
    def __init__(self, note: FakeNote) -> None:
        self._note = note
        self.id = note.id + 1000
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


class FakeRenderedAudioCard(FakeCard):
    def question_av_tags(self) -> list[object]:
        return []

    def answer_av_tags(self) -> list[object]:
        return []


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


class FakeAction:
    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled = True
        self.triggered = object()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt API
        self.enabled = enabled

    def setText(self, label: str) -> None:  # noqa: N802 - Qt API
        self.label = label


class FakeMenu:
    def __init__(self) -> None:
        self.actions: list[FakeAction] = []
        self.separator_count = 0

    def addAction(self, label: str) -> FakeAction:  # noqa: N802 - Qt API
        action = FakeAction(label)
        self.actions.append(action)
        return action

    def addSeparator(self) -> None:  # noqa: N802 - Qt API
        self.separator_count += 1


def test_register_reviewer_hooks() -> None:
    hooks = SimpleNamespace(
        card_review_webview_did_init=MagicMock(),
        card_will_show=MagicMock(),
        reviewer_did_show_question=MagicMock(),
        reviewer_did_show_answer=MagicMock(),
        reviewer_did_answer_card=MagicMock(),
        reviewer_will_show_context_menu=MagicMock(),
    )

    register_reviewer_hooks(hooks)

    hooks.card_review_webview_did_init.append.assert_called_once()
    hooks.card_will_show.append.assert_called_once()
    hooks.reviewer_did_show_question.append.assert_called_once()
    hooks.reviewer_did_show_answer.append.assert_called_once()
    hooks.reviewer_did_answer_card.append.assert_called_once()
    hooks.reviewer_will_show_context_menu.append.assert_called_once()


def test_card_will_show_adds_review_targets_for_rendered_audio() -> None:
    note = FakeNote(["[sound:first.mp3]", "[sound:second.wav]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _on_card_will_show("<div>play icon without filename</div>", card, "reviewAnswer")

    assert 'class="aqe-review-audio-target"' in html
    assert 'data-field-ord="1"' in html
    assert 'data-aqe-source-filename="second.wav"' in html
    assert 'data-field-ord="0"' not in html


def test_card_will_show_matches_rendered_escaped_bracket_audio_without_av_tags() -> None:
    note = FakeNote(["[sound:amp&amp;bracket]name.opus]", "[sound:second.wav]"])
    card = FakeRenderedAudioCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _on_card_will_show(
        "<div>[sound:amp&amp;bracket]name.opus]</div>",
        card,
        "reviewAnswer",
    )

    assert 'class="aqe-review-audio-target"' in html
    assert 'data-field-ord="0"' in html
    assert 'data-aqe-source-filename="amp&amp;bracket]name.opus"' in html
    assert 'data-field-ord="1"' not in html


def test_card_will_show_deduplicates_windows_case_variant_targets(monkeypatch) -> None:
    note = FakeNote(["[sound:Clip.MP3]", "[sound:clip.mp3]"])
    card = FakeRenderedAudioCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    html = _on_card_will_show("<div>[sound:clip.mp3]</div>", card, "reviewAnswer")

    assert html.count('class="aqe-review-audio-target"') == 1
    assert 'data-field-ord="0"' in html
    assert 'data-field-ord="1"' not in html


def test_card_will_show_does_not_duplicate_explicit_template_target() -> None:
    note = FakeNote(["[sound:first.mp3]", "[sound:second.wav]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}
    existing = (
        '<button class="aqe-review-audio-panel-trigger" data-field-ord="1"></button>'
        '<div class="aqe-review-audio-target" data-field-ord="1" '
        'data-aqe-source-filename="second.wav"></div>'
    )

    html = _on_card_will_show(existing, card, "reviewAnswer")

    assert html.count('class="aqe-review-audio-target"') == 1


def test_card_will_show_respects_reviewer_setting() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}

    html = _on_card_will_show("<div>[sound:first.mp3]</div>", card, "reviewQuestion")

    assert "aqe-review-audio-target" not in html


def test_card_will_show_leaves_pre_rendered_html_when_reviewer_setting_disabled() -> None:
    note = FakeNote(["front", "[sound:second.wav]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}
    text = (
        '<button class="aqe-review-audio-panel-trigger" data-field-ord="1"></button>'
        '<div class="aqe-review-audio-target" data-field-ord="1" '
        'data-aqe-source-filename="second.wav"></div>'
    )

    html = _on_card_will_show(text, card, "reviewAnswer")

    assert html == text


def test_card_will_show_skips_question_side() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    card = FakeCard(note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _on_card_will_show("<div>[sound:first.mp3]</div>", card, "reviewQuestion")

    assert "aqe-review-audio-target" not in html


def test_reviewer_did_show_injects_explicit_template_panel_when_setting_disabled() -> None:
    note = FakeNote(["front", "[sound:second.wav]"])
    card = FakeCard(note)
    web = FakeWeb()
    reviewer = SimpleNamespace(mw=aqt.mw, web=web, card=card, state="answer")
    aqt.mw.reviewer = reviewer
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}
    explicit = (
        '<button class="aqe-review-audio-panel-trigger" data-field-ord="1"></button>'
        '<div class="aqe-review-audio-target" data-field-ord="1" '
        'data-aqe-source-filename="second.wav" '
        'data-aqe-panel-trigger-target="true" data-aqe-panel-open="false"></div>'
    )

    assert _on_card_will_show(explicit, card, "reviewAnswer") == explicit
    _on_reviewer_did_show_card_side(card)

    assert any("window.__AQE_EDITOR_CONFIG__" in script for script in web.evals)


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


def test_reviewer_more_menu_adds_audio_editor_toggle(monkeypatch) -> None:
    menu = FakeMenu()
    reviewer = SimpleNamespace(state="question")
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
    assert menu.actions[0].triggered in connections
