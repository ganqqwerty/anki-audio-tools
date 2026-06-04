"""Anki template-filter hooks for the Reviewer audio panel trigger."""

from __future__ import annotations

from html import escape
from typing import Any

import anki.hooks as anki_hooks
from aqt.qt import QDialog, QLabel, QPushButton, Qt, qconnect
from aqt.utils import openLink

from .error_codes import GITHUB_PAGES_BASE_URL
from .reviewer_audio_targets import AQE_AUDIO_PANEL_FILTER
from .reviewer_template_filter import audio_panel_filter_html

_SHOW_REVIEWER_EDITOR_LABEL = "Show audio editor"
_ADD_AUDIO_EDITOR_BUTTON_LABEL = "Add audio Editor"
AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL = f"{GITHUB_PAGES_BASE_URL}go/video-template-audio-panel/"
_CARD_LAYOUT_HINT_OBJECT_NAME = "aqeTemplateAudioPanelHint"
_CARD_LAYOUT_BUTTON_OBJECT_NAME = "aqeTemplateAudioPanelAddButton"


def register_reviewer_template_filter(gui_hooks: Any | None = None) -> None:
    """Register the AQE Reviewer audio-panel template filter and Card Layout hint."""
    anki_hooks.field_filter.append(_aqe_audio_panel_filter)
    if gui_hooks is not None:
        gui_hooks.card_layout_will_show.append(_on_card_layout_will_show)


def _aqe_audio_panel_filter(field_text: str, field_name: str, filter_name: str, ctx: Any) -> str:
    """Render a Reviewer audio-panel trigger for an Anki card template field filter."""
    if filter_name != AQE_AUDIO_PANEL_FILTER:
        return field_text
    return audio_panel_filter_html(field_text, field_name, ctx, label=_SHOW_REVIEWER_EDITOR_LABEL)


def _template_audio_panel_hint_html() -> str:
    video_url = escape(AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL, quote=True)
    return (
        "Audio Quick Editor: add <code>{{aqe-audio-panel:FieldName}}</code> "
        "to this card template to place the audio editor exactly there. "
        f'<a href="{video_url}">Watch the setup video</a>.'
    )


def _audio_panel_template_tag(field_name: str) -> str:
    return f"{{{{{AQE_AUDIO_PANEL_FILTER}:{field_name}}}}}"


def _choose_audio_editor_field_name(clayout: Any) -> str | None:
    import aqt.forms as aqt_forms
    from aqt.utils import disable_help_button

    fields = [field["name"] for field in getattr(clayout, "model", {}).get("flds", []) if field.get("name")]
    if not fields:
        return None

    dialog = QDialog(clayout)
    form = aqt_forms.addfield.Ui_Dialog()
    form.setupUi(dialog)
    dialog.setWindowTitle(_ADD_AUDIO_EDITOR_BUTTON_LABEL)
    disable_help_button(dialog)
    form.fields.addItems(fields)
    form.fields.setCurrentRow(0)
    form.font.hide()
    form.label_2.hide()
    form.size.hide()
    form.label_3.hide()
    if not dialog.exec():
        return None
    row = form.fields.currentIndex().row()
    if row < 0:
        return None
    return fields[row]


def _append_audio_editor_tag(clayout: Any, field_name: str) -> None:
    edit_area = getattr(getattr(clayout, "tform", None), "edit_area", None)
    if edit_area is None:
        return

    text = edit_area.toPlainText()
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"{_audio_panel_template_tag(field_name)}\n"
    edit_area.setPlainText(text)

    change_tracker = getattr(clayout, "change_tracker", None)
    if change_tracker is not None:
        change_tracker.mark_basic()

    write_edits = getattr(clayout, "write_edits_to_template_and_redraw", None)
    if callable(write_edits):
        write_edits()


def _on_add_audio_editor(clayout: Any) -> None:
    field_name = _choose_audio_editor_field_name(clayout)
    if field_name is None:
        return
    _append_audio_editor_tag(clayout, field_name)


def _sync_add_audio_editor_button_visibility(clayout: Any, button: Any) -> None:
    button.setHidden(getattr(clayout, "current_editor_index", 0) == 2)


def _on_card_layout_will_show(clayout: Any) -> None:
    """Add a short AQE template-filter hint to Anki's Card Templates window."""
    if getattr(clayout, "_aqe_template_audio_panel_hint", None) is not None:
        return

    tform = getattr(clayout, "tform", None)
    layout = getattr(tform, "verticalLayout", None)
    edit_area = getattr(tform, "edit_area", None)
    parent = getattr(tform, "template_box", None)
    if layout is None or edit_area is None:
        return

    label = QLabel(_template_audio_panel_hint_html(), parent)
    label.setObjectName(_CARD_LAYOUT_HINT_OBJECT_NAME)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    label.setOpenExternalLinks(False)
    qconnect(label.linkActivated, lambda url: openLink(str(url)))

    index = layout.indexOf(edit_area)
    if index >= 0:
        layout.insertWidget(index, label)
    else:
        layout.addWidget(label)
    clayout._aqe_template_audio_panel_hint = label

    buttons = getattr(clayout, "buttons", None)
    add_field_button = getattr(clayout, "add_field_button", None)
    if buttons is None or add_field_button is None:
        return

    button = QPushButton(_ADD_AUDIO_EDITOR_BUTTON_LABEL)
    button.setObjectName(_CARD_LAYOUT_BUTTON_OBJECT_NAME)
    button.setAutoDefault(False)
    qconnect(button.clicked, lambda: _on_add_audio_editor(clayout))

    button_index = buttons.indexOf(add_field_button)
    if button_index >= 0:
        buttons.insertWidget(button_index + 1, button)
    else:
        buttons.addWidget(button)

    for toggle_name in ("front_button", "back_button", "style_button"):
        toggle = getattr(tform, toggle_name, None)
        if toggle is not None:
            qconnect(toggle.clicked, lambda *_args, clayout=clayout, button=button: _sync_add_audio_editor_button_visibility(clayout, button))
    _sync_add_audio_editor_button_visibility(clayout, button)
    clayout._aqe_template_audio_panel_button = button
