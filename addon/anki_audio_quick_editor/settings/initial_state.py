"""Thin Anki wrapper for settings UI initial state."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _trigger_note_type_options(mw: Any) -> list[dict[str, Any]]:
    """Return note type and field options for trigger rule Settings UI."""
    raw_models = _all_note_type_models(mw)
    if raw_models is None:
        return []
    return [
        option
        for model in raw_models
        if isinstance(model, dict)
        for option in [_trigger_note_type_option(model)]
    ]


def _all_note_type_models(mw: Any) -> list[Any] | tuple[Any, ...] | None:
    collection = getattr(mw, "col", None)
    models = getattr(collection, "models", None)
    all_models = getattr(models, "all", None)
    if collection is None or not callable(all_models):
        return None
    try:
        raw_models = all_models()
    except (AttributeError, TypeError):
        return None
    return raw_models if isinstance(raw_models, list | tuple) else None


def _trigger_note_type_option(model: dict[str, Any]) -> dict[str, Any]:
    fields = [
        str(field.get("name", ""))
        for field in model.get("flds", [])
        if isinstance(field, dict)
    ]
    return {
        "id": _model_id(model.get("id")),
        "name": str(model.get("name", "")),
        "fields": [field for field in fields if field],
    }


def _model_id(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_initial_state(config: dict[str, Any]) -> str:
    """Build the JSON blob embedded into ``window.__INITIAL_STATE__``."""
    from aqt import mw

    from .._version import __version__
    from ..i18n import active_context
    from ..release_info import read_release_info
    from ..runtime_manager import runtime_status
    from ..settings_state import build_initial_state_payload, encode_initial_state

    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    i18n = active_context()
    state = build_initial_state_payload(
        config,
        version=__version__,
        addon_id=addon_id,
        addon_dir=addon_dir,
        collection_available=mw.col is not None,
        locale=str(i18n["locale"]),
        direction=str(i18n["direction"]),
        messages=dict(i18n["messages"]),
        triggers={"note_types": _trigger_note_type_options(mw)},
        release_info=read_release_info(addon_dir),
        runtime_status=runtime_status(Path(addon_dir)),
    )
    return encode_initial_state(state)
