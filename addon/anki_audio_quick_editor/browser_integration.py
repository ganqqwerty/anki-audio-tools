"""Browser menu integration for batch audio operations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .audio_processing_presets import presets_from_raw
from .audio_state import AudioProcessingConfig
from .batch_operations import (
    BatchNoteSnapshot,
    FieldGroup,
    field_groups_for_notes,
    unique_note_ids,
)
from .browser_audio_export_dialog import AudioExportDialog
from .browser_batch_runner import run_batch_in_background, snapshot_from_note
from .browser_dialog import BatchOperationsDialog
from .diagnostics_runtime import capture_exception
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)

ACTION_LABEL = "Run Audio Batch Operation..."
EXPORT_ACTION_LABEL = "Export Audio..."


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
    qconnect(
        action.triggered,
        lambda _checked=False, b=browser: _open_after_current_editor_saved(b, _open_batch_dialog),
    )
    export_action = browser.form.menu_Cards.addAction(_tr("audio_export.action"))
    assert export_action is not None
    qconnect(
        export_action.triggered,
        lambda _checked=False, b=browser: _open_after_current_editor_saved(b, _open_audio_export_dialog),
    )


def _open_after_current_editor_saved(
    browser: Any,
    opener: Callable[[Any], None],
    *,
    remaining_readiness_checks: int = 100,
) -> None:
    editor = getattr(browser, "editor", None)
    save_current_note = getattr(editor, "call_after_note_saved", None)
    if not callable(save_current_note):
        opener(browser)
        return

    web = getattr(editor, "web", None)
    eval_with_callback = getattr(web, "evalWithCallback", None)
    if callable(eval_with_callback):

        def _save_when_ready(save_now_available: bool) -> None:
            if save_now_available:
                save_current_note(lambda: opener(browser))
                return
            if remaining_readiness_checks <= 0:
                opener(browser)
                return
            _retry_after_editor_readiness_delay(
                browser,
                opener,
                remaining_readiness_checks=remaining_readiness_checks - 1,
            )

        eval_with_callback("typeof saveNow === 'function'", _save_when_ready)
        return

    save_current_note(lambda: opener(browser))


def _retry_after_editor_readiness_delay(
    browser: Any,
    opener: Callable[[Any], None],
    *,
    remaining_readiness_checks: int,
) -> None:
    from aqt.qt import QTimer

    QTimer.singleShot(
        50,
        lambda: _open_after_current_editor_saved(
            browser,
            opener,
            remaining_readiness_checks=remaining_readiness_checks,
        ),
    )


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

    raw_config = browser.mw.addonManager.getConfig(browser.mw.addonManager.addonFromModule(__name__)) or {}
    config = AudioProcessingConfig.from_config(raw_config)
    try:
        processing_presets = presets_from_raw(raw_config.get("audio_processing_presets"))
    except ValueError as exc:
        logger.warning("browser batch: ignoring invalid processing presets: %s", exc)
        processing_presets = ()
    dialog = _create_dialog(browser, note_ids, groups, config, processing_presets)
    dialog.exec()


def _open_audio_export_dialog(browser: Any) -> None:
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

    dialog = _create_export_dialog(browser, note_ids, groups, tuple(snapshots))
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
    processing_presets: tuple[Any, ...] = (),
) -> Any:
    return BatchOperationsDialog(
        browser,
        note_ids,
        groups,
        config,
        run_batch_in_background,
        processing_presets=processing_presets,
    )


def _create_export_dialog(
    browser: Any,
    note_ids: list[int],
    groups: tuple[FieldGroup, ...],
    snapshots: tuple[BatchNoteSnapshot, ...],
) -> Any:
    return AudioExportDialog(browser, note_ids, groups, snapshots)


def _tr(key: str, values: dict[str, object] | None = None) -> str:
    return format_message(dict(active_context()["messages"]), key, values)
