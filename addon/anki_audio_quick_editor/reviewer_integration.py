"""Reviewer integration for reusing inline editor audio controls."""

from __future__ import annotations

import logging
from typing import Any

from aqt import mw
from aqt.qt import qconnect

from .editor_actions import BRIDGE_COMMANDS, CMD_COMMAND_PAYLOAD
from .editor_callbacks import _handle_bridge_command
from .editor_media import audio_field_sources
from .editor_runtime import SESSIONS
from .editor_session import EditorSession, reset_for_note_load
from .editor_webview_injection import editor_injection_script
from .media_paths import media_filenames_match
from .reviewer_audio_targets import (
    explicit_target_field_indices,
    target_html,
)
from .sound_refs import find_sound_references, safe_media_basename

logger = logging.getLogger(__name__)

_ADAPTERS: dict[int, ReviewerEditorAdapter] = {}
_BRIDGE_WRAPPED_ATTR = "_aqe_reviewer_bridge_wrapped"
_ORIGINAL_BRIDGE_ATTR = "_aqe_original_bridge_command"
_WRAPPER_BRIDGE_ATTR = "_aqe_reviewer_bridge_command"
_SHOW_REVIEWER_EDITOR_LABEL = "Show audio editor"
_HIDE_REVIEWER_EDITOR_LABEL = "Hide audio editor"
_reviewer_editor_visible = True
_reviewer_editor_manual_override = False
_EXPLICIT_PANEL_CARD_KEYS: set[object] = set()


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


def refresh_reviewer_editor_toggle_action(action: Any, reviewer: Any | None = None) -> None:
    """Refresh a Reviewer audio-editor toggle action for the current state."""
    if hasattr(action, "setText"):
        action.setText(reviewer_editor_menu_label(reviewer))
    if hasattr(action, "setEnabled"):
        action.setEnabled(_reviewer_editor_action_enabled(reviewer))


def add_reviewer_editor_toggle_action(menu: Any, reviewer: Any | None = None) -> Any:
    """Add a Show/Hide audio editor action to an Anki menu."""
    action = menu.addAction(reviewer_editor_menu_label(reviewer))
    assert action is not None
    refresh_reviewer_editor_toggle_action(action, reviewer)
    qconnect(action.triggered, toggle_reviewer_editor_visibility)
    return action


def toggle_reviewer_editor_visibility() -> bool:
    """Toggle reviewer audio controls without changing the persistent setting."""
    global _reviewer_editor_manual_override
    global _reviewer_editor_visible
    reviewer = getattr(mw, "reviewer", None)
    if _reviewer_editor_currently_shown(reviewer):
        _reviewer_editor_visible = False
        _reviewer_editor_manual_override = False
        _dispose_reviewer_frontend()
        return False
    _reviewer_editor_visible = True
    _reviewer_editor_manual_override = not _reviewer_editor_enabled()
    if _reviewer_showing_answer(reviewer):
        _render_current_reviewer_side(reviewer)
    return False


def _on_card_review_webview_did_init(webview: Any, kind: Any) -> None:
    if _is_main_review_webview_kind(kind):
        _ensure_reviewer_bridge_wrapped(webview)


def _on_card_will_show(text: str, card: Any, kind: str) -> str:
    if kind != "reviewAnswer":
        return text
    existing_targets = explicit_target_field_indices(text)
    if existing_targets:
        _EXPLICIT_PANEL_CARD_KEYS.add(_card_key(card))
    if not _reviewer_editor_requested():
        return text
    note = _card_note(card)
    if note is None:
        return text
    targets = _review_audio_targets(text, note, card=card, kind=kind)
    if not targets:
        return text
    return text + "".join(
        target_html(field_index, filename)
        for field_index, filename in targets
        if field_index not in existing_targets
    )


def _on_reviewer_did_show_card_side(card: Any) -> None:
    reviewer = getattr(mw, "reviewer", None)
    if reviewer is None or getattr(reviewer, "card", None) is not card:
        return
    if not _reviewer_showing_answer(reviewer):
        _dispose_reviewer_frontend()
        return
    if not _reviewer_editor_requested() and not _card_has_explicit_panel_target(card):
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
    _EXPLICIT_PANEL_CARD_KEYS.discard(_card_key(card))
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
    rendered_filenames = {safe_media_basename(ref.filename) for ref in find_sound_references(text)}
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
    if _contains_media_filename(matched_filenames, filename):
        return False
    if side_filenames:
        return _contains_media_filename(side_filenames, filename)
    if rendered_filenames:
        return _contains_media_filename(rendered_filenames, filename)
    return filename in text


def _contains_media_filename(candidates: set[str], filename: str) -> bool:
    return any(media_filenames_match(candidate, filename) for candidate in candidates)


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


def _card_note(card: Any) -> Any | None:
    if not hasattr(card, "note"):
        return None
    try:
        return card.note()
    except TypeError:
        return card.note


def _card_key(card: Any) -> object:
    key = getattr(card, "id", None)
    return key if key is not None else id(card)


def _card_has_explicit_panel_target(card: Any) -> bool:
    return _card_key(card) in _EXPLICIT_PANEL_CARD_KEYS


def _reviewer_editor_enabled() -> bool:
    config = mw.addonManager.getConfig(mw.addonManager.addonFromModule(__name__)) or {}
    return bool(config.get("enable_reviewer_editor", True))


def _reviewer_editor_action_enabled(reviewer: Any | None) -> bool:
    reviewer = reviewer if reviewer is not None else getattr(mw, "reviewer", None)
    return reviewer is not None and getattr(reviewer, "card", None) is not None


def _reviewer_editor_requested() -> bool:
    return _reviewer_editor_visible and (_reviewer_editor_enabled() or _reviewer_editor_manual_override)


def _reviewer_showing_answer(reviewer: Any | None) -> bool:
    return getattr(reviewer, "state", None) == "answer"


def _reviewer_editor_currently_shown(reviewer: Any | None) -> bool:
    return _reviewer_editor_requested() and _reviewer_showing_answer(reviewer)


def _dispose_reviewer_frontend() -> None:
    reviewer = getattr(mw, "reviewer", None)
    web = getattr(reviewer, "web", None)
    if web is not None:
        web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def _is_main_review_webview_kind(kind: Any) -> bool:
    return getattr(kind, "name", "") == "MAIN" or getattr(kind, "value", "") == "main"


def _is_aqe_reviewer_command(command: str) -> bool:
    return command.startswith("focus:") or command in BRIDGE_COMMANDS or command.lstrip().startswith("{")
