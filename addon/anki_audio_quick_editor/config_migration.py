"""Config migration helpers for Anki Audio Quick Editor."""

from __future__ import annotations

import copy
from typing import Any

from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db

CURRENT_CONFIG_VERSION = 14

REMOVED_CONFIG_KEYS = frozenset(
    {
        "edge_silence_threshold_db",
        "edge_silence_min_ms",
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

    if merged.get("_config_version") != CURRENT_CONFIG_VERSION:
        merged["_config_version"] = CURRENT_CONFIG_VERSION
        changed = True

    return merged, changed
