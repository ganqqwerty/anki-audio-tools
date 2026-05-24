"""JSON-safe diagnostics rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def safe_json(value: Any, *, depth: int = 0) -> Any:
    if is_json_scalar(value):
        return truncate_string(value) if isinstance(value, str) else value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseException):
        return {"type": type(value).__name__, "message": str(value)}
    if depth >= 4:
        return fallback_label(value)
    if isinstance(value, dict):
        return safe_json_mapping(value, depth=depth)
    if isinstance(value, (list, tuple, set)):
        return safe_json_sequence(value, depth=depth)
    return fallback_label(value)


def is_json_scalar(value: Any) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def safe_json_mapping(value: dict[Any, Any], *, depth: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= 50:
            result["..."] = "truncated"
            break
        result[str(key)] = safe_json(item, depth=depth + 1)
    return result


def safe_json_sequence(value: list[Any] | tuple[Any, ...] | set[Any], *, depth: int) -> list[Any]:
    items = list(value)
    rendered = [safe_json(item, depth=depth + 1) for item in items[:50]]
    if len(items) > 50:
        rendered.append("truncated")
    return rendered


def truncate_string(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}... [truncated {len(value) - limit} chars]"


def fallback_label(value: Any) -> str:
    return f"[{type(value).__name__}]"


def source_from_boundary(boundary: str) -> str:
    return boundary.split(".", 1)[0] if boundary else "diagnostics"
