"""Shared DPDFNet aggressiveness settings."""

from __future__ import annotations

from math import isfinite
from typing import Any

DPDFNET_ATTENUATION_LIMIT_DB_VALUES = (6.0, 12.0, 18.0)
DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB = 12.0


def normalize_dpdfnet_attn_limit_db(value: Any) -> float:
    """Return the nearest supported DPDFNet attenuation limit."""
    if isinstance(value, bool):
        raw = DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB
    else:
        try:
            raw = float(value)
        except (TypeError, ValueError):
            raw = DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB
    if not isfinite(raw):
        raw = DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB
    return min(
        DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
        key=lambda candidate: (abs(candidate - raw), -candidate),
    )
