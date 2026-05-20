"""Shared frontend diagnostic log handling."""

from __future__ import annotations

import json
import logging
from typing import Any

from .contracts_generated import FrontendLogPayload
from .diagnostics_runtime import record_breadcrumb, record_frontend_error

CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def handle_frontend_log_payload(
    raw_payload: Any,
    *,
    logger: logging.Logger,
    default_scope: str,
    boundary: str,
    log_prefix: str,
    invalid_label: str | None = None,
) -> None:
    """Validate and record one frontend-originated diagnostic payload."""
    payload = decode_frontend_log_payload(
        raw_payload,
        logger=logger,
        invalid_label=invalid_label or f"{default_scope} frontend_log",
    )
    if payload is None:
        return

    level = payload.level.value
    message = payload.message
    context = payload.context
    stack = str(getattr(payload, "stack", "") or "")
    scope = str(getattr(payload, "scope", "") or default_scope)
    operation_id = str(getattr(payload, "operation_id", "") or "")
    operation = f"{default_scope}.frontend"
    _log_frontend(logger, level, _render_frontend_log(log_prefix, message, context, stack))
    record_breadcrumb(
        "frontend.log",
        source=scope,
        level=_breadcrumb_level(level),
        operation="frontend.log",
        operation_id=operation_id,
        boundary=boundary,
        context=_frontend_log_context(payload, level),
    )
    if level == "error":
        record_frontend_error(
            boundary,
            message=message,
            stack=stack,
            source=scope,
            operation=operation,
            operation_id=operation_id,
            context=context,
        )


def decode_frontend_log_payload(
    raw_payload: Any,
    *,
    logger: logging.Logger,
    invalid_label: str,
) -> FrontendLogPayload | None:
    """Decode a frontend log payload from either JSON text or an object."""
    try:
        payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
    except json.JSONDecodeError:
        logger.warning("%s: invalid payload", invalid_label)
        return None
    try:
        return FrontendLogPayload.from_dict(payload)
    except CONTRACT_DECODE_ERRORS:
        logger.warning("%s: invalid payload", invalid_label)
        return None


def _render_frontend_log(prefix: str, message: str, context: Any, stack: str) -> str:
    rendered = f"{prefix}: {message}"
    if context is not None:
        rendered = f"{rendered} | {context!r}"
    return f"{rendered}\n{stack}" if stack else rendered


def _log_frontend(logger: logging.Logger, level: str, rendered: str) -> None:
    log_fn = {
        "debug": logger.debug,
        "warn": logger.warning,
        "error": logger.error,
    }.get(level, logger.info)
    log_fn(rendered)


def _breadcrumb_level(level: str) -> str:
    return "error" if level == "error" else "debug"


def _frontend_log_context(payload: FrontendLogPayload, level: str) -> dict[str, object]:
    return {
        "level": level,
        "message": payload.message,
        "filename": getattr(payload, "filename", None),
        "lineno": getattr(payload, "lineno", None),
        "colno": getattr(payload, "colno", None),
        "context": payload.context,
    }
