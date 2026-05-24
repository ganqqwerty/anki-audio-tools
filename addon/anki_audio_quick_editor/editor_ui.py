"""Inline editor UI bundle injection for Audio Quick Editor."""

from __future__ import annotations

import json
from pathlib import Path

from .i18n import active_context

_BUNDLE_DIR = Path(__file__).parent / "templates" / "editor"
_BUNDLE_JS = _BUNDLE_DIR / "editor_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "editor_bundle.css"
_STYLE_ID = "aqe-inline-style"


def injection_script(
    audio_field_indices: list[int] | None = None,
    *,
    audio_field_sources: dict[int, str] | None = None,
    initial_status_by_field: dict[int, dict[str, str]] | None = None,
    repeat_playback_by_default: bool = False,
    show_graph_by_default: bool = False,
    split_button_defaults: dict[str, object] | None = None,
    visible_editor_buttons: list[str] | None = None,
    editor_button_modes: dict[str, str] | None = None,
) -> str:
    """Return JavaScript that mounts compact controls next to audio fields."""
    i18n = active_context()
    config = {
        "audioFieldIndices": audio_field_indices or [],
        "audioFieldSources": audio_field_sources or {},
        "initialStatusByField": initial_status_by_field or {},
        "repeatPlaybackByDefault": bool(repeat_playback_by_default),
        "showGraphByDefault": bool(show_graph_by_default),
        "visibleEditorButtons": visible_editor_buttons,
        "editorButtonModes": editor_button_modes,
        "splitButtonDefaults": split_button_defaults
        or {
            "volumeStepDb": 3.0,
            "speedStep": 0.05,
            "repeatPauseSeconds": 0.0,
            "shareTarget": "litterbox",
            "pauseAggressiveness": "normal",
            "outputFormat": "mp3",
            "denoiseAlgorithm": "standard",
            "pitchHumMode": "direct",
            "dpdfnetAttnLimitDb": 12.0,
            "graphVoiceRange": "general",
            "graphRecordingCondition": "auto",
            "graphSmoothness": "very_smooth",
            "graphConnectShortDropoutsMs": 240,
            "graphVoiceLock": "balanced",
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": i18n["messages"],
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
