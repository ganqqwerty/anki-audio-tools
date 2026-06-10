"""Template-filter integration tests for the Reviewer audio panel trigger."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import anki.hooks as anki_hooks
import aqt

from anki_audio_quick_editor.reviewer_template_filter_integration import (
    AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL,
    _append_audio_editor_tag,
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
        self.linkActivated = object()

    def setObjectName(self, object_name: str) -> None:
        self.object_name = object_name

    def setWordWrap(self, enabled: bool) -> None:
        self.word_wrap = enabled

    def setTextFormat(self, text_format: object) -> None:
        del text_format

    def setTextInteractionFlags(self, flags: object) -> None:
        del flags

    def setOpenExternalLinks(self, enabled: bool) -> None:
        self.open_external_links = enabled


class FakeCardLayoutButton:
    def __init__(self, text: str, parent: object | None = None) -> None:
        self.text = text
        self.parent = parent
        self.object_name = ""
        self.auto_default = True
        self.hidden = False
        self.clicked = object()

    def setObjectName(self, object_name: str) -> None:
        self.object_name = object_name

    def setAutoDefault(self, enabled: bool) -> None:
        self.auto_default = enabled

    def setHidden(self, hidden: bool) -> None:
        self.hidden = hidden


class FakeCardLayoutEditArea:
    def __init__(self, text: str = "") -> None:
        self.text = text

    def toPlainText(self) -> str:
        return self.text

    def setPlainText(self, text: str) -> None:
        self.text = text


class FakeCardLayoutWidgetList:
    def __init__(self, edit_area: object) -> None:
        self.edit_area = edit_area
        self.inserted: list[tuple[int, object]] = []
        self.added: list[object] = []

    def indexOf(self, widget: object) -> int:
        return 3 if widget is self.edit_area else -1

    def insertWidget(self, index: int, widget: object) -> None:
        self.inserted.append((index, widget))

    def addWidget(self, widget: object) -> None:
        self.added.append(widget)


class FakeCardLayoutButtonList:
    def __init__(self, add_field_button: object) -> None:
        self.add_field_button = add_field_button
        self.inserted: list[tuple[int, object]] = []
        self.added: list[object] = []

    def indexOf(self, widget: object) -> int:
        return 2 if widget is self.add_field_button else -1

    def insertWidget(self, index: int, widget: object) -> None:
        self.inserted.append((index, widget))

    def addWidget(self, widget: object) -> None:
        self.added.append(widget)


def test_register_reviewer_template_filter() -> None:
    hooks = SimpleNamespace(card_layout_will_show=MagicMock())

    register_reviewer_template_filter(hooks)

    anki_hooks.field_filter.append.assert_called_once_with(_aqe_audio_panel_filter)
    hooks.card_layout_will_show.append.assert_called_once_with(_on_card_layout_will_show)


def test_card_layout_hint_is_inserted_before_template_edit_area(monkeypatch) -> None:
    parent = object()
    edit_area = FakeCardLayoutEditArea("{{Front}}")
    layout = FakeCardLayoutWidgetList(edit_area)
    add_field_button = object()
    buttons = FakeCardLayoutButtonList(add_field_button)
    clayout = SimpleNamespace(
        model={"flds": [{"name": "Back"}]},
        change_tracker=SimpleNamespace(mark_basic=MagicMock()),
        current_editor_index=0,
        tform=SimpleNamespace(
            back_button=SimpleNamespace(clicked=object()),
            edit_area=edit_area,
            front_button=SimpleNamespace(clicked=object()),
            style_button=SimpleNamespace(clicked=object()),
            template_box=parent,
            verticalLayout=layout,
        ),
        add_field_button=add_field_button,
        buttons=buttons,
        write_edits_to_template_and_redraw=MagicMock(),
    )
    connections: dict[object, object] = {}
    opened: list[str] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.QLabel",
        FakeCardLayoutLabel,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.QPushButton",
        FakeCardLayoutButton,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.openLink",
        opened.append,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration._choose_audio_editor_field_name",
        lambda _clayout: "Back",
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
    assert len(buttons.inserted) == 1
    button_index, button = buttons.inserted[0]
    assert button_index == 3
    assert isinstance(button, FakeCardLayoutButton)
    assert button.object_name == "aqeTemplateAudioPanelAddButton"
    assert button.auto_default is False
    assert button.hidden is False

    connections[label.linkActivated](AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL)
    connections[button.clicked]()

    assert opened == [AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL]
    assert edit_area.text == "{{Front}}\n{{aqe-audio-panel:Back}}\n"
    clayout.change_tracker.mark_basic.assert_called_once_with()
    clayout.write_edits_to_template_and_redraw.assert_called_once_with()


def test_add_audio_editor_button_is_hidden_for_style_editor(monkeypatch) -> None:
    parent = object()
    edit_area = FakeCardLayoutEditArea()
    layout = FakeCardLayoutWidgetList(edit_area)
    add_field_button = object()
    buttons = FakeCardLayoutButtonList(add_field_button)
    clayout = SimpleNamespace(
        current_editor_index=2,
        tform=SimpleNamespace(
            back_button=SimpleNamespace(clicked=object()),
            edit_area=edit_area,
            front_button=SimpleNamespace(clicked=object()),
            style_button=SimpleNamespace(clicked=object()),
            template_box=parent,
            verticalLayout=layout,
        ),
        add_field_button=add_field_button,
        buttons=buttons,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.QLabel",
        FakeCardLayoutLabel,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.QPushButton",
        FakeCardLayoutButton,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.reviewer_template_filter_integration.qconnect",
        lambda _signal, _callback: None,
    )

    _on_card_layout_will_show(clayout)

    _, button = buttons.inserted[0]
    assert isinstance(button, FakeCardLayoutButton)
    assert button.hidden is True


def test_append_audio_editor_tag_adds_template_filter_tag() -> None:
    edit_area = FakeCardLayoutEditArea("{{Front}}")
    clayout = SimpleNamespace(
        change_tracker=SimpleNamespace(mark_basic=MagicMock()),
        tform=SimpleNamespace(edit_area=edit_area),
        write_edits_to_template_and_redraw=MagicMock(),
    )

    _append_audio_editor_tag(clayout, "Back")

    assert edit_area.text == "{{Front}}\n{{aqe-audio-panel:Back}}\n"
    clayout.change_tracker.mark_basic.assert_called_once_with()
    clayout.write_edits_to_template_and_redraw.assert_called_once_with()


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
