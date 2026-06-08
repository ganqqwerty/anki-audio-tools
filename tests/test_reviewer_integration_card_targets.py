"""Reviewer integration tests focused on card target behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.reviewer_integration import (
    _on_card_review_webview_did_init,
    _on_card_will_show,
    _on_reviewer_did_answer_card,
    _on_reviewer_did_show_card_side,
    _on_reviewer_will_show_context_menu,
    register_reviewer_hooks,
)
from tests.reviewer_integration_fixtures import (
    FakeCard,
    FakeNote,
    FakeRenderedAudioCard,
    FakeWeb,
)


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
    assert hooks.card_review_webview_did_init.append.call_args.args == (_on_card_review_webview_did_init,)
    assert hooks.card_will_show.append.call_args.args == (_on_card_will_show,)
    assert hooks.reviewer_did_show_question.append.call_args.args == (_on_reviewer_did_show_card_side,)
    assert hooks.reviewer_did_show_answer.append.call_args.args == (_on_reviewer_did_show_card_side,)
    assert hooks.reviewer_did_answer_card.append.call_args.args == (_on_reviewer_did_answer_card,)
    assert hooks.reviewer_will_show_context_menu.append.call_args.args == (_on_reviewer_will_show_context_menu,)


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
