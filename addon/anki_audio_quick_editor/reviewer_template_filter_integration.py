"""Anki template-filter hooks for the Reviewer audio panel trigger."""

from __future__ import annotations

from html import escape
from typing import Any

import anki.hooks as anki_hooks
from aqt.qt import QLabel, Qt, qconnect
from aqt.utils import openLink

from .error_codes import GITHUB_PAGES_BASE_URL
from .reviewer_audio_targets import AQE_AUDIO_PANEL_FILTER
from .reviewer_template_filter import audio_panel_filter_html

_SHOW_REVIEWER_EDITOR_LABEL = "Show audio editor"
AQE_TEMPLATE_AUDIO_PANEL_VIDEO_URL = f"{GITHUB_PAGES_BASE_URL}go/video-template-audio-panel/"
_CARD_LAYOUT_HINT_OBJECT_NAME = "aqeTemplateAudioPanelHint"


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
