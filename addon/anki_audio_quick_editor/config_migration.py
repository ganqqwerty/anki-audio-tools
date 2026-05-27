"""Config migration helpers for Anki Audio Quick Editor."""

from __future__ import annotations

import copy
from typing import Any

from .audio_formats import normalize_output_format
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db

CURRENT_CONFIG_VERSION = 1
PAUSE_DETECTION_ALGORITHMS = frozenset({"silencedetect", "silero_vad"})


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
    changed = merged != user_config
    changed = _apply_post_merge_migrations(merged, defaults) or changed
    changed = _stamp_current_config_version(merged) or changed

    return merged, changed


def _apply_post_merge_migrations(
    merged: dict[str, Any],
    defaults: dict[str, Any],
) -> bool:
    changed = False
    changed = _normalize_dpdfnet_limit_setting(merged) or changed
    changed = _normalize_output_format_setting(merged) or changed
    changed = _normalize_pause_detection_algorithm_setting(merged) or changed
    changed = _normalize_visible_editor_buttons_setting(merged, defaults) or changed
    return _normalize_editor_button_mode_settings(merged, defaults) or changed


def _normalize_dpdfnet_limit_setting(merged: dict[str, Any]) -> bool:
    if "dpdfnet_attn_limit_db" not in merged:
        return False
    normalized_dpdfnet_limit = normalize_dpdfnet_attn_limit_db(
        merged.get("dpdfnet_attn_limit_db")
    )
    if merged.get("dpdfnet_attn_limit_db") == normalized_dpdfnet_limit:
        return False
    merged["dpdfnet_attn_limit_db"] = normalized_dpdfnet_limit
    return True


def _normalize_output_format_setting(merged: dict[str, Any]) -> bool:
    if "output_format" not in merged:
        return False
    normalized_output_format = normalize_output_format(merged.get("output_format"))
    if merged.get("output_format") == normalized_output_format:
        return False
    merged["output_format"] = normalized_output_format
    return True


def _normalize_pause_detection_algorithm_setting(merged: dict[str, Any]) -> bool:
    if "pause_detection_algorithm" not in merged:
        return False
    value = merged.get("pause_detection_algorithm")
    if value in PAUSE_DETECTION_ALGORITHMS:
        return False
    merged["pause_detection_algorithm"] = "silencedetect"
    return True


def _normalize_visible_editor_buttons_setting(
    merged: dict[str, Any],
    defaults: dict[str, Any],
) -> bool:
    visible_buttons = merged.get("visible_editor_buttons")
    default_buttons = defaults.get("visible_editor_buttons")
    if not isinstance(visible_buttons, list) or not isinstance(default_buttons, list):
        return False

    allowed_buttons = set(default_buttons)
    normalized = [button for button in visible_buttons if button in allowed_buttons]
    if normalized == visible_buttons:
        return False
    merged["visible_editor_buttons"] = normalized
    return True


def _normalize_editor_button_mode_settings(
    merged: dict[str, Any],
    defaults: dict[str, Any],
) -> bool:
    return _normalize_editor_button_modes(merged.get("editor_button_modes"), defaults)


def _stamp_current_config_version(merged: dict[str, Any]) -> bool:
    if merged.get("_config_version") == CURRENT_CONFIG_VERSION:
        return False
    merged["_config_version"] = CURRENT_CONFIG_VERSION
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
