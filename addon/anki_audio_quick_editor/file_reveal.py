"""Cross-platform helpers for revealing local files to the user."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess  # nosec B404
from pathlib import Path

from .errors import AudioProcessingError, MissingMediaError

logger = logging.getLogger(__name__)


def reveal_file(
    path: Path,
    *,
    missing_message: str = "The referenced audio file was not found in Anki's media folder.",
) -> None:
    """Reveal ``path`` in the platform file manager."""
    if not path.is_file():
        raise MissingMediaError(missing_message)
    resolved = path.resolve()
    system = platform.system()
    if system == "Darwin":
        _run_detached(("open", "-R", str(resolved)))
        return
    if system == "Windows":
        _run_detached(("explorer", f"/select,{resolved}"))
        return
    _open_parent_folder(resolved.parent)


def _open_parent_folder(folder: Path) -> None:
    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        _run_detached((xdg_open, str(folder)))
        return
    try:
        from aqt.qt import QDesktopServices, QUrl

        if QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            return
    except Exception as exc:
        logger.info("Qt folder open failed: %s", exc)
    raise AudioProcessingError("Could not open the containing folder.")


def _run_detached(command: tuple[str, ...]) -> None:
    try:
        subprocess.Popen(command)  # nosec B603
    except OSError as exc:
        raise AudioProcessingError("Could not open the containing folder.") from exc
