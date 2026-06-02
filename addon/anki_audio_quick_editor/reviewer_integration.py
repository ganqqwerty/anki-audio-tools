"""Reviewer integration for reusing inline editor audio controls."""

from __future__ import annotations

import html
import logging
import re
from typing import Any

import anki.hooks as anki_hooks
from aqt import mw
from aqt.qt import qconnect

from .editor_actions import BRIDGE_COMMANDS, CMD_COMMAND_PAYLOAD
from .editor_callbacks import _handle_bridge_command
from .editor_integration import editor_injection_script
from .editor_media import audio_field_sources
from .editor_runtime import SESSIONS
from .editor_session import EditorSession, reset_for_note_load
from .sound_refs import is_supported_audio_filename, safe_media_basename

logger = logging.getLogger(__name__)

_AQE_REVIEW_TARGET_CLASS = "aqe-review-audio-target"
_AQE_REVIEW_TRIGGER_CLASS = "aqe-review-audio-panel-trigger"
_AQE_AUDIO_PANEL_FILTER = "aqe-audio-panel"
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]", re.IGNORECASE)
_ADAPTERS: dict[int, ReviewerEditorAdapter] = {}
_BRIDGE_WRAPPED_ATTR = "_aqe_reviewer_bridge_wrapped"
_ORIGINAL_BRIDGE_ATTR = "_aqe_original_bridge_command"
_WRAPPER_BRIDGE_ATTR = "_aqe_reviewer_bridge_command"
_SHOW_REVIEWER_EDITOR_LABEL = "Show audio editor"
_HIDE_REVIEWER_EDITOR_LABEL = "Hide audio editor"
_reviewer_editor_visible = True


class ReviewerEditorAdapter:
    """Editor-shaped adapter backed by Anki's live Reviewer."""

    def __init__(self, reviewer: Any) -> None:
        self.reviewer = reviewer
        self.mw = reviewer.mw
        self.web = reviewer.web
        self.currentField: int | None = None
        self.last_field_index: int | None = None
        self.note = self.current_note()

    def loadNote(self, focusTo: int | None = None) -> None:  # noqa: N802, N803 - Anki editor API
        """Persist the current note and rerender the current Reviewer side."""
        if self.note is None:
            return
        self.mw.col.update_note(self.note)
        card = getattr(self.reviewer, "card", None)
        if card is not None and hasattr(card, "load"):
            card.load()
        self.note = self.current_note(reload=True)
        if focusTo is not None:
            self.currentField = self.last_field_index = int(focusTo)
        _render_current_reviewer_side(self.reviewer)

    def current_note(self, *, reload: bool = False) -> Any | None:
        card = getattr(self.reviewer, "card", None)
        if card is None or not hasattr(card, "note"):
            return None
        try:
            return card.note(reload=reload)
        except TypeError:
            return card.note()


def register_reviewer_hooks(gui_hooks: Any) -> None:
    """Register Reviewer hooks used by the add-on."""
    anki_hooks.field_filter.append(_aqe_audio_panel_filter)
    gui_hooks.card_review_webview_did_init.append(_on_card_review_webview_did_init)
    gui_hooks.card_will_show.append(_on_card_will_show)
    gui_hooks.reviewer_did_show_question.append(_on_reviewer_did_show_card_side)
    gui_hooks.reviewer_did_show_answer.append(_on_reviewer_did_show_card_side)
    gui_hooks.reviewer_did_answer_card.append(_on_reviewer_did_answer_card)
    gui_hooks.reviewer_will_show_context_menu.append(_on_reviewer_will_show_context_menu)


def reviewer_editor_menu_label(reviewer: Any | None = None) -> str:
    """Return the current Reviewer audio-editor toggle label."""
    reviewer = reviewer if reviewer is not None else getattr(mw, "reviewer", None)
    return (
        _HIDE_REVIEWER_EDITOR_LABEL
        if _reviewer_editor_currently_shown(reviewer)
        else _SHOW_REVIEWER_EDITOR_LABEL
    )


def add_reviewer_editor_toggle_action(menu: Any, reviewer: Any | None = None) -> Any:
    """Add a Show/Hide audio editor action to an Anki menu."""
    action = menu.addAction(reviewer_editor_menu_label(reviewer))
    assert action is not None
    if hasattr(action, "setEnabled"):
        action.setEnabled(_reviewer_editor_enabled())
    qconnect(action.triggered, toggle_reviewer_editor_visibility)
    return action


def toggle_reviewer_editor_visibility() -> bool:
    """Toggle reviewer audio controls without changing the persistent setting."""
    global _reviewer_editor_visible
    reviewer = getattr(mw, "reviewer", None)
    if _reviewer_editor_currently_shown(reviewer):
        _reviewer_editor_visible = False
        _dispose_reviewer_frontend()
        return False
    _reviewer_editor_visible = True
    if _reviewer_editor_enabled() and _reviewer_showing_answer(reviewer):
        _render_current_reviewer_side(reviewer)
    return False


def _on_card_review_webview_did_init(webview: Any, kind: Any) -> None:
    if _is_main_review_webview_kind(kind):
        _ensure_reviewer_bridge_wrapped(webview)


def _on_card_will_show(text: str, card: Any, kind: str) -> str:
    if kind != "reviewAnswer":
        return text
    if not _reviewer_editor_enabled() or not _reviewer_editor_visible:
        return text
    note = _card_note(card)
    if note is None:
        return text
    targets = _review_audio_targets(text, note, card=card, kind=kind)
    if not targets:
        return text
    existing_targets = _explicit_target_field_indices(text)
    return text + "".join(
        _target_html(field_index, filename)
        for field_index, filename in targets
        if field_index not in existing_targets
    )


def _aqe_audio_panel_filter(field_text: str, field_name: str, filter_name: str, ctx: Any) -> str:
    """Render a Reviewer audio-panel trigger for an Anki card template field filter."""
    if filter_name != _AQE_AUDIO_PANEL_FILTER:
        return field_text
    if not _reviewer_editor_enabled():
        return ""
    filename = _first_sound_filename(field_text)
    if filename is None:
        return ""
    field_index = _template_field_index(ctx, field_name)
    if field_index is None:
        return ""
    return _audio_panel_trigger_html(field_index, filename)


def _on_reviewer_did_show_card_side(card: Any) -> None:
    if not _reviewer_editor_enabled() or not _reviewer_editor_visible:
        _dispose_reviewer_frontend()
        return
    reviewer = getattr(mw, "reviewer", None)
    if reviewer is None or getattr(reviewer, "card", None) is not card:
        return
    if not _reviewer_showing_answer(reviewer):
        _dispose_reviewer_frontend()
        return
    adapter = _adapter_for_reviewer(reviewer)
    note = _card_note(card)
    if note is None:
        return
    _reset_adapter_for_note(adapter, note)
    _ensure_reviewer_bridge_wrapped(reviewer.web)
    reviewer.web.eval(editor_injection_script(adapter, note))


def _on_reviewer_did_answer_card(reviewer: Any, card: Any, ease: int) -> None:
    logger.debug("disposing reviewer editor state after card answer: card=%r ease=%s", card, ease)
    adapter = _ADAPTERS.get(id(reviewer))
    if adapter is None:
        return
    session = SESSIONS.get(adapter)
    if session is not None:
        reset_for_note_load(session, None)
    if hasattr(adapter, "web"):
        adapter.web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def _on_reviewer_will_show_context_menu(reviewer: Any, menu: Any) -> None:
    if hasattr(menu, "addSeparator"):
        menu.addSeparator()
    add_reviewer_editor_toggle_action(menu, reviewer)


def _ensure_reviewer_bridge_wrapped(webview: Any) -> None:
    if getattr(webview, _BRIDGE_WRAPPED_ATTR, False) and getattr(
        webview, "onBridgeCmd", None
    ) is getattr(webview, _WRAPPER_BRIDGE_ATTR, None):
        return
    original = getattr(webview, "onBridgeCmd", None)
    if original is None:
        original = getattr(webview, "_bridge_command", None)
    setattr(webview, _ORIGINAL_BRIDGE_ATTR, original)

    def _bridge(command: str) -> Any:
        reviewer = getattr(mw, "reviewer", None)
        if _is_aqe_reviewer_command(command) and reviewer is not None:
            _handle_reviewer_bridge_command(reviewer, command)
            return None
        original_bridge = getattr(webview, _ORIGINAL_BRIDGE_ATTR, None)
        if callable(original_bridge):
            return original_bridge(command)
        return None

    if hasattr(webview, "set_bridge_command"):
        webview.set_bridge_command(_bridge, getattr(mw, "reviewer", None))
    else:
        webview.onBridgeCmd = _bridge
    setattr(webview, _BRIDGE_WRAPPED_ATTR, True)
    setattr(webview, _WRAPPER_BRIDGE_ATTR, _bridge)


def _handle_reviewer_bridge_command(reviewer: Any, command: str) -> None:
    adapter = _adapter_for_reviewer(reviewer)
    if command.startswith("focus:"):
        _focus_adapter_field(adapter, command)
        return
    if command == CMD_COMMAND_PAYLOAD or command in BRIDGE_COMMANDS or command.lstrip().startswith("{"):
        _handle_bridge_command(adapter, command)


def _adapter_for_reviewer(reviewer: Any) -> ReviewerEditorAdapter:
    adapter = _ADAPTERS.get(id(reviewer))
    if adapter is None:
        adapter = ReviewerEditorAdapter(reviewer)
        _ADAPTERS[id(reviewer)] = adapter
    adapter.web = reviewer.web
    adapter.note = adapter.current_note()
    return adapter


def _reset_adapter_for_note(adapter: ReviewerEditorAdapter, note: Any) -> None:
    note_id = getattr(note, "id", None)
    session = SESSIONS.setdefault(adapter, EditorSession())
    reset_for_note_load(session, note_id)
    session.note_id = note_id
    adapter.note = note


def _focus_adapter_field(adapter: ReviewerEditorAdapter, command: str) -> None:
    try:
        _prefix, field_index = command.split(":", 1)
        adapter.currentField = adapter.last_field_index = int(field_index)
    except (TypeError, ValueError):
        logger.debug("ignored invalid reviewer focus command: %s", command)


def _render_current_reviewer_side(reviewer: Any) -> None:
    state = getattr(reviewer, "state", None)
    show_answer = getattr(reviewer, "_showAnswer", None)
    if state == "answer" and callable(show_answer):
        show_answer()
        return
    show_question = getattr(reviewer, "_showQuestion", None)
    if state == "question" and callable(show_question):
        show_question()


def _review_audio_targets(
    text: str,
    note: Any,
    *,
    card: Any | None = None,
    kind: str = "",
) -> list[tuple[int, str]]:
    sources = audio_field_sources(note)
    if not sources:
        return []
    side_filenames = _card_side_audio_filenames(card, kind)
    rendered_filenames = {safe_media_basename(match.group(1)) for match in _SOUND_RE.finditer(text)}
    targets: list[tuple[int, str]] = []
    matched_filenames: set[str] = set()
    for field_index, filename in sources.items():
        if _review_target_matches(filename, text, side_filenames, rendered_filenames, matched_filenames):
            matched_filenames.add(filename)
            targets.append((field_index, filename))
    return targets


def _review_target_matches(
    filename: str,
    text: str,
    side_filenames: set[str],
    rendered_filenames: set[str],
    matched_filenames: set[str],
) -> bool:
    if filename in matched_filenames:
        return False
    if side_filenames:
        return filename in side_filenames
    if rendered_filenames:
        return filename in rendered_filenames
    return filename in text


def _card_side_audio_filenames(card: Any | None, kind: str) -> set[str]:
    if card is None:
        return set()
    method_name = "question_av_tags" if kind == "reviewQuestion" else "answer_av_tags"
    method = getattr(card, method_name, None)
    if not callable(method):
        return set()
    return {
        safe_media_basename(filename)
        for tag in method()
        if isinstance((filename := getattr(tag, "filename", None)), str)
    }


def _target_html(field_index: int, filename: str) -> str:
    return _target_html_with_attrs(field_index, filename, "")


def _target_html_with_attrs(field_index: int, filename: str, extra_attrs: str) -> str:
    return (
        f'<div class="{_AQE_REVIEW_TARGET_CLASS}" '
        f'data-field-ord="{int(field_index)}" '
        f'data-aqe-source-filename="{html.escape(filename, quote=True)}"{extra_attrs}></div>'
    )


def _audio_panel_trigger_html(field_index: int, filename: str) -> str:
    target = _target_html_with_attrs(
        field_index,
        filename,
        ' data-aqe-panel-trigger-target="true" data-aqe-panel-open="false"',
    )
    escaped_filename = html.escape(filename, quote=True)
    return (
        f'<button type="button" class="{_AQE_REVIEW_TRIGGER_CLASS}" '
        f'data-testid="aqe-review-audio-panel-trigger-{int(field_index)}" '
        f'data-field-ord="{int(field_index)}" '
        f'data-aqe-source-filename="{escaped_filename}">{_SHOW_REVIEWER_EDITOR_LABEL}</button>'
        f"{target}"
    )


def _first_sound_filename(text: str) -> str | None:
    match = _SOUND_RE.search(text)
    if match is None:
        return None
    filename = safe_media_basename(match.group(1))
    return filename if is_supported_audio_filename(filename) else None


def _template_field_index(ctx: Any, field_name: str) -> int | None:
    note = _template_note(ctx)
    if isinstance(field_name, str):
        ordinal = _field_index_by_name(note, field_name)
        if ordinal is not None:
            return ordinal
    ordinal = getattr(ctx, "field_ordinal", None)
    if isinstance(ordinal, int):
        return ordinal
    return None


def _template_note(ctx: Any) -> Any | None:
    note = getattr(ctx, "note", None)
    if callable(note):
        try:
            return note()
        except TypeError:
            return None
    return note


def _field_index_by_name(note: Any, field_name: str) -> int | None:
    keys = getattr(note, "keys", None)
    if callable(keys):
        try:
            return list(keys()).index(field_name)
        except ValueError:
            return None
    fields = getattr(note, "fields", None)
    field_names = getattr(note, "field_names", None)
    if isinstance(fields, list) and isinstance(field_names, list):
        try:
            return field_names.index(field_name)
        except ValueError:
            return None
    return None


def _explicit_target_field_indices(text: str) -> set[int]:
    return {
        int(match)
        for match in re.findall(r'class="[^"]*\baqe-review-audio-target\b[^"]*"[^>]*data-field-ord="(\d+)"', text)
    }


def _card_note(card: Any) -> Any | None:
    if not hasattr(card, "note"):
        return None
    try:
        return card.note()
    except TypeError:
        return card.note


def _reviewer_editor_enabled() -> bool:
    config = mw.addonManager.getConfig(mw.addonManager.addonFromModule(__name__)) or {}
    return bool(config.get("enable_reviewer_editor", True))


def _reviewer_showing_answer(reviewer: Any | None) -> bool:
    return getattr(reviewer, "state", None) == "answer"


def _reviewer_editor_currently_shown(reviewer: Any | None) -> bool:
    return _reviewer_editor_enabled() and _reviewer_editor_visible and _reviewer_showing_answer(reviewer)


def _dispose_reviewer_frontend() -> None:
    reviewer = getattr(mw, "reviewer", None)
    web = getattr(reviewer, "web", None)
    if web is not None:
        web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def _is_main_review_webview_kind(kind: Any) -> bool:
    return getattr(kind, "name", "") == "MAIN" or getattr(kind, "value", "") == "main"


def _is_aqe_reviewer_command(command: str) -> bool:
    return command.startswith("focus:") or command in BRIDGE_COMMANDS or command.lstrip().startswith("{")
