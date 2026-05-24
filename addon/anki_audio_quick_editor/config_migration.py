"""Config migration helpers for Anki Audio Quick Editor."""

from __future__ import annotations

import copy
from typing import Any

from .audio_formats import normalize_output_format
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db

CURRENT_CONFIG_VERSION = 20

REMOVED_CONFIG_KEYS = frozenset(
    {
        "edge_silence_threshold_db",
        "edge_silence_min_ms",
        "manual_trim_small_ms",
        "manual_trim_large_ms",
        "deep_filter_path",
    }
)


def deep_merge(defaults: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge user config into defaults without mutating either input."""
    merged = copy.deepcopy(defaults)
    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def migrate_config(
    user_config: dict[str, Any],
    defaults: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Merge defaults into user config and stamp the current schema version."""
    merged = deep_merge(defaults, user_config)
    for key in REMOVED_CONFIG_KEYS:
        merged.pop(key, None)
    changed = merged != user_config

    if "dpdfnet_attn_limit_db" in merged:
        normalized_dpdfnet_limit = normalize_dpdfnet_attn_limit_db(
            merged.get("dpdfnet_attn_limit_db")
        )
        if merged.get("dpdfnet_attn_limit_db") != normalized_dpdfnet_limit:
            merged["dpdfnet_attn_limit_db"] = normalized_dpdfnet_limit
            changed = True

    if "output_format" in merged:
        normalized_output_format = normalize_output_format(merged.get("output_format"))
        if merged.get("output_format") != normalized_output_format:
            merged["output_format"] = normalized_output_format
            changed = True

    if _insert_share_button(merged.get("visible_editor_buttons")):
        changed = True

    if _normalize_editor_button_modes(merged.get("editor_button_modes"), defaults):
        changed = True

    if merged.get("_config_version") != CURRENT_CONFIG_VERSION:
        merged["_config_version"] = CURRENT_CONFIG_VERSION
        changed = True

    return merged, changed


def _insert_share_button(visible_buttons: Any) -> bool:
    if not isinstance(visible_buttons, list) or "aqe:share" in visible_buttons:
        return False
    show_file_index = (
        visible_buttons.index("aqe:show-file") if "aqe:show-file" in visible_buttons else None
    )
    if show_file_index is None:
        visible_buttons.append("aqe:share")
    else:
        visible_buttons.insert(show_file_index + 1, "aqe:share")
    return True


def _normalize_editor_button_modes(
    button_modes: Any,
    defaults: dict[str, Any],
) -> bool:
    default_modes = defaults.get("editor_button_modes")
    if not isinstance(default_modes, dict) or not isinstance(button_modes, dict):
        return False

    changed = False
    invalid_keys = [key for key in button_modes if key not in default_modes]
    for key in invalid_keys:
        button_modes.pop(key, None)
        changed = True

    for command, default_mode in default_modes.items():
        if button_modes.get(command) in {"text", "icon"}:
            continue
        button_modes[command] = default_mode
        changed = True
    return changed
