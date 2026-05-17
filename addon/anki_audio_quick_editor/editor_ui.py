"""Inline editor UI bundle injection for Audio Quick Editor."""

from __future__ import annotations

import json
from pathlib import Path

_BUNDLE_DIR = Path(__file__).parent / "templates" / "editor"
_BUNDLE_JS = _BUNDLE_DIR / "editor_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "editor_bundle.css"
_STYLE_ID = "aqe-inline-style"


def injection_script(
    audio_field_indices: list[int] | None = None,
    *,
    repeat_playback_by_default: bool = False,
) -> str:
    """Return JavaScript that mounts compact controls next to audio fields."""
    config = {
        "audioFieldIndices": audio_field_indices or [],
        "repeatPlaybackByDefault": bool(repeat_playback_by_default),
    }
    return (
        "(function() {\n"
        f"  window.__AQE_EDITOR_CONFIG__ = {json.dumps(config)};\n"
        "  if (window.__aqeEditorDispose) window.__aqeEditorDispose();\n"
        "  const styleId = "
        f"{json.dumps(_STYLE_ID)};\n"
        "  let style = document.getElementById(styleId);\n"
        "  if (!style) {\n"
        "    style = document.createElement('style');\n"
        "    style.id = styleId;\n"
        "    document.head.appendChild(style);\n"
        "  }\n"
        f"  style.textContent = {json.dumps(_read_text(_BUNDLE_CSS))};\n"
        f"{_read_text(_BUNDLE_JS)}\n"
        "})();"
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
