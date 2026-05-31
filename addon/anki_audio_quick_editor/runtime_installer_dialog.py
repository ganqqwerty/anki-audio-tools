"""Qt dialog for managed runtime installation and repair."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from aqt import mw
from aqt.qt import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    qconnect,
)

from .i18n import t


class RuntimeInstallDialog(QDialog):
    """Small modal progress dialog for runtime install/repair."""

    def __init__(self, parent: object, addon_dir: Path, *, force_verify: bool) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._addon_dir = addon_dir
        self._force_verify = force_verify
        self._cancel_event = threading.Event()
        self._finished = False
        self._closed = False
        self._warned = False
        self._final_status: dict[str, Any] | None = None
        self._worker = threading.Thread(
            target=self._run_install,
            daemon=True,
            name="aqe-runtime-install-dialog",
        )

        self.setWindowTitle(t("runtime_installer.window_title"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(360)
        if hasattr(self, "setModal"):
            self.setModal(True)

        layout = QVBoxLayout(self)
        self._step_label = QLabel(t("runtime_installer.starting"))
        self._progress = QProgressBar(self)
        self._progress.setRange(0, 100)
        self._log = QTextEdit(self)
        self._log.setReadOnly(True)
        self._button = QPushButton(t("runtime_installer.cancel"), self)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self._button)

        layout.addWidget(self._step_label)
        layout.addWidget(self._progress)
        layout.addWidget(self._log)
        layout.addLayout(button_row)
        qconnect(self._button.clicked, self._handle_button)

    @property
    def final_status(self) -> dict[str, Any] | None:
        """Return the installer result, if the worker has finished."""
        return self._final_status

    def exec_install(self) -> Any:
        """Run the installer while the modal dialog is open."""
        self._append_log(t("runtime_installer.starting"))
        self._worker.start()
        result = self.exec()
        self._closed = True
        if not self._finished:
            self._cancel_event.set()
        return result

    def reject(self) -> None:
        """Cancel installation when the dialog is dismissed before completion."""
        if not self._finished:
            self._cancel_event.set()
            self._warn_incomplete()
        self._closed = True
        super().reject()

    def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        if not self._finished:
            self._cancel_event.set()
            self._warn_incomplete()
        self._closed = True
        super().closeEvent(event)

    def _handle_button(self) -> None:
        if self._finished:
            self.accept()
            return
        self.reject()

    def _run_install(self) -> None:
        from . import runtime_manager

        final_status = runtime_manager.ensure_runtime(
            self._addon_dir,
            progress=self._post_progress,
            cancel_event=self._cancel_event,
            force_verify=self._force_verify,
        )
        self._final_status = final_status
        self._post_progress(final_status, finished=True)

    def _post_progress(self, payload: dict[str, Any], *, finished: bool = False) -> None:
        def _apply() -> None:
            if self._closed and not finished:
                return
            self._apply_progress(payload, finished=finished)

        mw.taskman.run_on_main(_apply)

    def _apply_progress(self, payload: dict[str, Any], *, finished: bool) -> None:
        step, detail = self._payload_text(payload)
        self._set_step(step)
        self._set_progress(payload.get("progress"))
        self._append_progress_log(step, detail)
        if finished:
            self._mark_finished(payload)

    @staticmethod
    def _payload_text(payload: dict[str, Any]) -> tuple[str, str]:
        step = str(payload.get("step") or payload.get("message") or "")
        detail = str(payload.get("detail") or payload.get("error") or payload.get("message") or "")
        return step, detail

    def _set_step(self, step: str) -> None:
        if step:
            self._step_label.setText(step)

    def _set_progress(self, value: object) -> None:
        if isinstance(value, int):
            self._progress.setValue(max(0, min(100, value)))

    def _append_progress_log(self, step: str, detail: str) -> None:
        if step and detail:
            self._append_log(f"{step}: {detail}")
            return
        self._append_log(step or detail)

    def _mark_finished(self, payload: dict[str, Any]) -> None:
        self._finished = True
        if payload.get("phase") == "ready":
            self._progress.setValue(100)
        self._button.setText(t("runtime_installer.close"))

    def _append_log(self, line: str) -> None:
        if line:
            self._log.append(line)

    def _warn_incomplete(self) -> None:
        if self._warned:
            return
        self._warned = True
        QMessageBox.warning(
            self,
            t("runtime_installer.cancel_warning.title"),
            t("runtime_installer.cancel_warning.message"),
        )


def open_runtime_install_dialog(
    parent: object,
    addon_dir: str | Path,
    *,
    force_verify: bool = False,
) -> dict[str, Any]:
    """Open the modal runtime installer and return the resulting runtime status."""
    from . import runtime_manager

    addon_path = Path(addon_dir)
    dialog = RuntimeInstallDialog(parent, addon_path, force_verify=force_verify)
    dialog.exec_install()
    return dialog.final_status or runtime_manager.runtime_status(addon_path)
