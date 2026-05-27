"""Browser menu integration for batch audio operations."""

from __future__ import annotations

import logging
from typing import Any

from .audio_state import AudioProcessingConfig
from .batch_operations import (
    BatchNoteSnapshot,
    FieldGroup,
    field_groups_for_notes,
    unique_note_ids,
)
from .browser_batch_runner import run_batch_in_background, snapshot_from_note
from .browser_dialog import BatchOperationsDialog
from .diagnostics_runtime import capture_exception
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)

ACTION_LABEL = "Run Audio Batch Operation..."


def register_browser_hooks(gui_hooks: Any) -> None:
    """Register Browser menu hooks."""
    gui_hooks.browser_menus_did_init.append(
        _browser_hook_boundary("browser_menus_did_init", _on_browser_menus_did_init)
    )


def _browser_hook_boundary(name: str, func: Any) -> Any:
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            capture_exception(f"browser.hook.{name}", exc, operation=f"browser.hook.{name}", log=logger)
            raise

    return _wrapped


def _on_browser_menus_did_init(browser: Any) -> None:
    from aqt.qt import qconnect

    action = browser.form.menu_Cards.addAction(_tr("batch.action"))
    assert action is not None
    qconnect(action.triggered, lambda _checked=False, b=browser: _open_batch_dialog(b))


def _open_batch_dialog(browser: Any) -> None:
    from aqt.utils import showWarning

    note_ids = unique_note_ids(browser.selected_notes())
    if not note_ids:
        showWarning(_tr("batch.no_cards_selected"), parent=browser)
        return

    snapshots = _snapshots_for_note_ids(browser.mw.col, note_ids)
    groups = field_groups_for_notes(snapshots)
    if not groups:
        showWarning(_tr("batch.no_fields"), parent=browser)
        return

    config = AudioProcessingConfig.from_config(
        browser.mw.addonManager.getConfig(browser.mw.addonManager.addonFromModule(__name__)) or {}
    )
    dialog = _create_dialog(browser, note_ids, groups, config)
    dialog.exec()


def _snapshots_for_note_ids(col: Any, note_ids: list[int]) -> list[BatchNoteSnapshot]:
    snapshots: list[BatchNoteSnapshot] = []
    for note_id in note_ids:
        snapshots.append(snapshot_from_note(col.get_note(note_id)))
    return snapshots


def _create_dialog(
    browser: Any,
    note_ids: list[int],
    groups: tuple[FieldGroup, ...],
    config: AudioProcessingConfig,
) -> Any:
    return BatchOperationsDialog(browser, note_ids, groups, config, run_batch_in_background)


def _tr(key: str, values: dict[str, object] | None = None) -> str:
    return format_message(dict(active_context()["messages"]), key, values)
