"""True modal-loop smoke coverage for the Browser batch shell."""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog

from e2e.conftest import import_runtime_addon_module


def test_browser_batch_dialog_runs_and_finishes_real_modal_loop(anki_mw) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    batch_operations = import_runtime_addon_module(".batch_operations")
    audio_state = import_runtime_addon_module(".audio_state")
    dialog = browser_dialog.BatchOperationsDialog(
        anki_mw,
        [],
        (batch_operations.FieldGroup("Basic", ("Front", "Back")),),
        audio_state.AudioProcessingConfig(),
        lambda *_args: None,
    )

    QTimer.singleShot(150, dialog._dialog.reject)
    result = dialog.exec()

    assert result == QDialog.DialogCode.Rejected
    assert dialog._cleaned_up is True
    assert dialog.cancel_event.is_set() is False
