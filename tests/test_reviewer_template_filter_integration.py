"""Template-filter integration tests for the Reviewer audio panel trigger."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import anki.hooks as anki_hooks
import aqt

from anki_audio_quick_editor.reviewer_template_filter_integration import (
    AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL,
    _aqe_audio_panel_filter,
    _on_card_layout_will_show,
    register_reviewer_template_filter,
)


class FakeNote:
    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        self.field_names = ["Front", "Back"][: len(fields)]

    def keys(self) -> list[str]:
        return self.field_names


class FakeCardLayoutLabel:
    def __init__(self, text: str, parent: object | None = None) -> None:
        self.text = text
        self.parent = parent
        self.object_name = ""
        self.word_wrap = False
        self.open_external_links = True
        self.linkActivated = object()  # noqa: N815 - Qt signal attribute

    def setObjectName(self, object_name: str) -> None:  # noqa: N802 - Qt API
        self.object_name = object_name

    def setWordWrap(self, enabled: bool) -> None:  # noqa: N802 - Qt API
        self.word_wrap = enabled

    def setTextFormat(self, text_format: object) -> None:  # noqa: N802 - Qt API
        del text_format

    def setTextInteractionFlags(self, flags: object) -> None:  # noqa: N802 - Qt API
        del flags

    def setOpenExternalLinks(self, enabled: bool) -> None:  # noqa: N802 - Qt API
        self.open_external_links = enabled


class FakeCardLayoutWidgetList:
    def __init__(self, edit_area: object) -> None:
        self.edit_area = edit_area
        self.inserted: list[tuple[int, object]] = []
        self.added: list[object] = []

    def indexOf(self, widget: object) -> int:  # noqa: N802 - Qt API
        return 3 if widget is self.edit_area else -1

    def insertWidget(self, index: int, widget: object) -> None:  # noqa: N802 - Qt API
        self.inserted.append((index, widget))

    def addWidget(self, widget: object) -> None:  # noqa: N802 - Qt API
        self.added.append(widget)


def test_register_reviewer_template_filter() -> None:
    hooks = SimpleNamespace(card_layout_will_show=MagicMock())

    register_reviewer_template_filter(hooks)

    anki_hooks.field_filter.append.assert_called_once_with(_aqe_audio_panel_filter)
    hooks.card_layout_will_show.append.assert_called_once_with(_on_card_layout_will_show)


def test_card_layout_hint_is_inserted_before_template_edit_area(monkeypatch) -> None:
    parent = object()
    edit_area = object()
    layout = FakeCardLayoutWidgetList(edit_area)
    clayout = SimpleNamespace(
        tform=SimpleNamespace(
            edit_area=edit_area,
            template_box=parent,
            verticalLayout=layout,
        )
    )
    connections: dict[object, object] = {}
    opened: list[str] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.QLabel",
        FakeCardLayoutLabel,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.openLink",
        opened.append,
    )

    _on_card_layout_will_show(clayout)
    _on_card_layout_will_show(clayout)

    assert len(layout.inserted) == 1
    assert layout.added == []
    index, label = layout.inserted[0]
    assert index == 3
    assert isinstance(label, FakeCardLayoutLabel)
    assert label.parent is parent
    assert label.object_name == "aqeTemplateAudioPanelHint"
    assert label.word_wrap is True
    assert label.open_external_links is False
    assert "{{aqe-audio-panel:FieldName}}" in label.text
    assert AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL in label.text

    connections[label.linkActivated](AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL)

    assert opened == [AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL]


def test_aqe_audio_panel_filter_renders_trigger_for_audio_field() -> None:
    note = FakeNote(["front", "[sound:foo.mp3]"])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("[sound:foo.mp3]", "Back", "aqe-audio-panel", ctx)

    assert 'class="aqe-review-audio-panel-trigger"' in html
    assert 'data-testid="aqe-review-audio-panel-trigger-1"' in html
    assert 'class="aqe-review-audio-target"' in html
    assert 'data-field-ord="1"' in html
    assert 'data-aqe-source-filename="foo.mp3"' in html
    assert 'data-aqe-panel-open="false"' in html


def test_aqe_audio_panel_filter_reads_note_method_context() -> None:
    note = FakeNote(["front", "[sound:foo.mp3]"])
    ctx = SimpleNamespace(note=lambda: note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("[sound:foo.mp3]", "Back", "aqe-audio-panel", ctx)

    assert 'data-testid="aqe-review-audio-panel-trigger-1"' in html


def test_aqe_audio_panel_filter_is_idempotent_for_duplicate_registration() -> None:
    note = FakeNote(["front", "[sound:foo.mp3]"])
    ctx = SimpleNamespace(note=lambda: note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    first = _aqe_audio_panel_filter("[sound:foo.mp3]", "Back", "aqe-audio-panel", ctx)
    second = _aqe_audio_panel_filter(first, "Back", "aqe-audio-panel", ctx)

    assert second == first


def test_aqe_audio_panel_filter_returns_empty_without_audio() -> None:
    note = FakeNote(["front", "plain text"])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("plain text", "Back", "aqe-audio-panel", ctx)

    assert html == ""


def test_aqe_audio_panel_filter_returns_empty_for_unsupported_sound_reference() -> None:
    note = FakeNote(["front", "[sound:not-audio.txt]"])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("[sound:not-audio.txt]", "Back", "aqe-audio-panel", ctx)

    assert html == ""


def test_aqe_audio_panel_filter_escapes_filename() -> None:
    note = FakeNote(['[sound:bad"name.mp3]'])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter('[sound:bad"name.mp3]', "Front", "aqe-audio-panel", ctx)

    assert 'data-aqe-source-filename="bad&quot;name.mp3"' in html
    assert 'bad"name.mp3' not in html


def test_aqe_audio_panel_filter_handles_escaped_bracket_filename() -> None:
    note = FakeNote(["[sound:amp&amp;bracket]name.opus]"])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("[sound:amp&amp;bracket]name.opus]", "Front", "aqe-audio-panel", ctx)

    assert 'data-aqe-source-filename="amp&amp;bracket]name.opus"' in html


def test_aqe_audio_panel_filter_ignores_reviewer_setting() -> None:
    note = FakeNote(["[sound:first.mp3]"])
    ctx = SimpleNamespace(note=note)
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": False}

    html = _aqe_audio_panel_filter("[sound:first.mp3]", "Front", "aqe-audio-panel", ctx)

    assert 'class="aqe-review-audio-panel-trigger"' in html
    assert 'class="aqe-review-audio-target"' in html


def test_aqe_audio_panel_filter_ignores_other_filters() -> None:
    ctx = SimpleNamespace(note=FakeNote(["[sound:first.mp3]"]))
    aqt.mw.addonManager.getConfig.return_value = {"enable_reviewer_editor": True}

    html = _aqe_audio_panel_filter("[sound:first.mp3]", "Front", "text", ctx)

    assert html == "[sound:first.mp3]"
