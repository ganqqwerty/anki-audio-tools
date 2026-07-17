"""Select the platform-specific native recording backend."""

from __future__ import annotations

import platform
from importlib import import_module
from pathlib import Path
from typing import Any

from .native_macos import MacWavRecorderBackend
from .native_qt import QtAudioSourceRecorderBackend


def create_native_backend(output_path: Path, *, mw: Any, parent: Any) -> Any:
    """Create the supported recorder backend for the current Anki runtime."""
    macos_helper = load_macos_helper()
    if macos_helper is not None and platform.machine() == "arm64":
        return MacWavRecorderBackend(output_path, macos_helper=macos_helper)
    return QtAudioSourceRecorderBackend(output_path, mw=mw, parent=parent)


def load_macos_helper() -> Any | None:
    """Return Anki's native macOS recorder helper when available."""
    try:
        module = import_module("aqt._macos_helper")
    except (ImportError, ModuleNotFoundError):
        return None
    return getattr(module, "macos_helper", None)


__all__ = ["create_native_backend"]
