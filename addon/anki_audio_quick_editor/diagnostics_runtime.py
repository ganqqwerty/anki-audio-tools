"""Runtime diagnostics, breadcrumbs, and exception-boundary helpers."""

from __future__ import annotations

import atexit
import copy
import faulthandler
import json
import logging
import os
import sys
import threading
import traceback
import uuid
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

DEFAULT_BREADCRUMB_CAPACITY = 100
DEBUG_BREADCRUMB_CAPACITY = 2000
EVENT_LOG_MAX_BYTES = 1024 * 1024
PACKAGE_LOGGER_NAME = "anki_audio_quick_editor"

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _new_session_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


class _DiagnosticsState:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.session_id = _new_session_id()
        self.started_at = _utc_now()
        self.debug_enabled = False
        self.seq = 0
        self.breadcrumbs: deque[dict[str, Any]] = deque(maxlen=DEFAULT_BREADCRUMB_CAPACITY)
        self.latest_incident: dict[str, Any] | None = None
        self.addon_dir: Path | None = None
        self.event_log_path: Path | None = None
        self.crash_log_path: Path | None = None
        self.session_marker_path: Path | None = None
        self.previous_dirty_session: dict[str, Any] | None = None
        self._crash_file: Any = None
        self._hooks_installed = False
        self._atexit_registered = False
        self._previous_sys_hook: Callable[..., Any] | None = None
        self._previous_thread_hook: Callable[..., Any] | None = None


_STATE = _DiagnosticsState()


def configure_runtime(addon_dir: str | Path, *, debug_enabled: bool) -> None:
    """Configure diagnostics files and process-level exception hooks."""
    root = Path(addon_dir)
    root.mkdir(parents=True, exist_ok=True)
    with _STATE.lock:
        _STATE.addon_dir = root
        _STATE.event_log_path = root / "anki_audio_quick_editor_events.jsonl"
        _STATE.crash_log_path = root / "anki_audio_quick_editor_crash.log"
        _STATE.session_marker_path = root / "anki_audio_quick_editor_session.json"
        set_debug_enabled(debug_enabled)
        _STATE.previous_dirty_session = _read_dirty_session(_STATE.session_marker_path)
        _write_session_marker(clean_exit=False)
        _enable_faulthandler()
        _install_process_hooks()
        if not _STATE._atexit_registered:
            atexit.register(mark_session_clean)
            _STATE._atexit_registered = True
    if _STATE.previous_dirty_session is not None:
        logger.warning("previous diagnostics session did not exit cleanly: %s", _STATE.previous_dirty_session)
    record_breadcrumb(
        "diagnostics.session_started",
        source="diagnostics",
        level="info",
        context={"addon_dir": str(root), "debug_enabled": debug_enabled},
        flush=True,
    )


def set_debug_enabled(enabled: bool) -> None:
    """Update debug-mode breadcrumb behavior."""
    with _STATE.lock:
        _STATE.debug_enabled = bool(enabled)
        _resize_breadcrumb_ring(DEBUG_BREADCRUMB_CAPACITY if enabled else DEFAULT_BREADCRUMB_CAPACITY)


def new_operation_id(prefix: str = "op") -> str:
    """Return a compact id for correlating breadcrumbs from one user action."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def record_breadcrumb(
    event: str,
    *,
    source: str = "",
    level: str = "debug",
    operation: str = "",
    operation_id: str = "",
    boundary: str = "",
    context: Any = None,
    flush: bool = False,
) -> dict[str, Any]:
    """Record one structured diagnostic event."""
    with _STATE.lock:
        _STATE.seq += 1
        entry = {
            "schema": 1,
            "session_id": _STATE.session_id,
            "seq": _STATE.seq,
            "timestamp": _utc_now(),
            "level": level,
            "source": source,
            "operation": operation,
            "operation_id": operation_id,
            "boundary": boundary,
            "event": event,
        }
        safe_context = _safe_json(context)
        if safe_context not in ({}, None, ""):
            entry["context"] = safe_context
        _STATE.breadcrumbs.append(copy.deepcopy(entry))
        should_flush = flush or level in {"error", "critical", "warning"}
        if _STATE.debug_enabled:
            _append_event(entry)
        if should_flush:
            _write_session_marker(clean_exit=False)
            flush_logging()
        return copy.deepcopy(entry)


def recent_breadcrumbs(limit: int = 40) -> list[dict[str, Any]]:
    """Return the newest breadcrumbs in chronological order."""
    with _STATE.lock:
        return copy.deepcopy(list(_STATE.breadcrumbs)[-limit:])


def capture_exception(
    boundary: str,
    exc: BaseException,
    *,
    operation: str = "",
    operation_id: str = "",
    user_message: str = "",
    context: Any = None,
    log: logging.Logger | None = None,
) -> dict[str, Any]:
    """Log and store an unexpected exception captured at a boundary."""
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    safe_context = _safe_json(context)
    record_breadcrumb(
        "boundary.failed",
        source=_source_from_boundary(boundary),
        level="error",
        operation=operation,
        operation_id=operation_id,
        boundary=boundary,
        context={
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "context": safe_context,
        },
        flush=True,
    )
    incident = {
        "timestamp": _utc_now(),
        "session_id": _STATE.session_id,
        "operation": operation,
        "operation_id": operation_id,
        "boundary": boundary,
        "exception_type": type(exc).__name__,
        "message": str(exc),
        "user_message": user_message or str(exc),
        "context": safe_context,
        "traceback": tb_text,
        "breadcrumbs": recent_breadcrumbs(),
    }
    with _STATE.lock:
        _STATE.latest_incident = copy.deepcopy(incident)
    target_logger = log or logging.getLogger(PACKAGE_LOGGER_NAME)
    target_logger.error(
        "boundary failed: %s operation=%s operation_id=%s context=%r",
        boundary,
        operation,
        operation_id,
        safe_context,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    flush_logging()
    return copy.deepcopy(incident)


def record_frontend_error(
    boundary: str,
    *,
    message: str,
    stack: str = "",
    source: str = "frontend",
    operation: str = "",
    operation_id: str = "",
    context: Any = None,
) -> dict[str, Any]:
    """Store a frontend-originated error as the latest support incident."""
    safe_context = _safe_json(context)
    record_breadcrumb(
        "frontend.error",
        source=source,
        level="error",
        operation=operation,
        operation_id=operation_id,
        boundary=boundary,
        context={"message": message, "context": safe_context},
        flush=True,
    )
    incident = {
        "timestamp": _utc_now(),
        "session_id": _STATE.session_id,
        "operation": operation,
        "operation_id": operation_id,
        "boundary": boundary,
        "exception_type": "FrontendError",
        "message": message,
        "user_message": message,
        "context": safe_context,
        "traceback": stack,
        "breadcrumbs": recent_breadcrumbs(),
    }
    with _STATE.lock:
        _STATE.latest_incident = copy.deepcopy(incident)
    return copy.deepcopy(incident)


def latest_incident() -> dict[str, Any] | None:
    """Return the latest captured incident, if any."""
    with _STATE.lock:
        return copy.deepcopy(_STATE.latest_incident)


def support_report_context() -> dict[str, Any]:
    """Return diagnostics data ready for support report rendering."""
    with _STATE.lock:
        return {
            "latest_error": copy.deepcopy(_STATE.latest_incident),
            "recent_events": copy.deepcopy(list(_STATE.breadcrumbs)),
            "crash_forensics": {
                "session_id": _STATE.session_id,
                "started_at": _STATE.started_at,
                "debug_enabled": _STATE.debug_enabled,
                "event_log_path": str(_STATE.event_log_path or ""),
                "crash_log_path": str(_STATE.crash_log_path or ""),
                "session_marker_path": str(_STATE.session_marker_path or ""),
                "previous_dirty_session": copy.deepcopy(_STATE.previous_dirty_session),
            },
        }


def mark_session_clean() -> None:
    """Mark the diagnostics session as cleanly closed when possible."""
    with _STATE.lock:
        _write_session_marker(clean_exit=True)
        if _STATE._crash_file is not None:
            try:
                _STATE._crash_file.flush()
            except OSError:
                pass


def flush_logging() -> None:
    """Flush handlers for add-on loggers."""
    seen: set[int] = set()
    logger_names = (PACKAGE_LOGGER_NAME, __name__, __name__.split(".", 1)[0])
    for name in logger_names:
        current: logging.Logger | None = logging.getLogger(name)
        while current is not None:
            for handler in current.handlers:
                marker = id(handler)
                if marker in seen:
                    continue
                seen.add(marker)
                try:
                    handler.flush()
                except Exception:  # pragma: no cover - logging handler defensive path
                    pass
            if not current.propagate or current.parent is current:
                break
            current = current.parent


def reset_for_tests() -> None:
    """Reset module state for focused tests."""
    global _STATE
    old_state = _STATE
    with old_state.lock:
        if old_state._previous_sys_hook is not None:
            sys.excepthook = old_state._previous_sys_hook
        if old_state._previous_thread_hook is not None:
            threading.excepthook = old_state._previous_thread_hook
        if old_state._crash_file is not None:
            try:
                faulthandler.disable()
                old_state._crash_file.close()
            except OSError:
                pass
        _STATE = _DiagnosticsState()


def _install_process_hooks() -> None:
    if _STATE._hooks_installed:
        return
    _STATE._previous_sys_hook = sys.excepthook
    _STATE._previous_thread_hook = threading.excepthook

    def _sys_hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        if exc.__traceback__ is None and tb is not None:
            exc = exc.with_traceback(tb)
        capture_exception("process.sys_excepthook", exc, operation="process", log=logger)
        previous = _STATE._previous_sys_hook
        if previous is not None and previous is not sys.__excepthook__ and previous is not _sys_hook:
            previous(exc_type, exc, tb)

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        exc = args.exc_value
        if exc is not None:
            capture_exception(
                "process.threading_excepthook",
                exc,
                operation="process.thread",
                context={"thread_name": getattr(args.thread, "name", "")},
                log=logger,
            )
        previous = _STATE._previous_thread_hook
        if previous is not None and previous is not threading.__excepthook__ and previous is not _thread_hook:
            previous(args)

    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook
    _STATE._hooks_installed = True


def _enable_faulthandler() -> None:
    if _STATE.crash_log_path is None:
        return
    try:
        if _STATE._crash_file is not None:
            _STATE._crash_file.close()
        _STATE._crash_file = _STATE.crash_log_path.open("a", encoding="utf-8")
        faulthandler.enable(file=_STATE._crash_file, all_threads=True)
    except (OSError, RuntimeError) as exc:
        logger.warning("could not enable faulthandler diagnostics: %s", exc)


def _append_event(entry: dict[str, Any]) -> None:
    path = _STATE.event_log_path
    if path is None:
        return
    try:
        if path.exists() and path.stat().st_size > EVENT_LOG_MAX_BYTES:
            rotated = path.with_suffix(path.suffix + ".1")
            path.replace(rotated)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, sort_keys=True) + "\n")
            file.flush()
    except OSError as exc:
        logger.warning("could not write diagnostics event log: %s", exc)


def _read_dirty_session(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict) and raw.get("clean_exit") is False:
        safe = _safe_json(raw)
        return safe if isinstance(safe, dict) else None
    return None


def _write_session_marker(*, clean_exit: bool) -> None:
    path = _STATE.session_marker_path
    if path is None:
        return
    payload = {
        "session_id": _STATE.session_id,
        "pid": os.getpid(),
        "started_at": _STATE.started_at,
        "updated_at": _utc_now(),
        "clean_exit": clean_exit,
        "last_event_seq": _STATE.seq,
    }
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        logger.warning("could not write diagnostics session marker: %s", exc)


def _resize_breadcrumb_ring(capacity: int) -> None:
    if _STATE.breadcrumbs.maxlen == capacity:
        return
    _STATE.breadcrumbs = deque(list(_STATE.breadcrumbs)[-capacity:], maxlen=capacity)


def _safe_json(value: Any, *, depth: int = 0) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return _truncate_string(value) if isinstance(value, str) else value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseException):
        return {"type": type(value).__name__, "message": str(value)}
    if depth >= 4:
        return _fallback_label(value)
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 50:
                result["..."] = "truncated"
                break
            result[str(key)] = _safe_json(item, depth=depth + 1)
        return result
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        rendered = [_safe_json(item, depth=depth + 1) for item in items[:50]]
        if len(items) > 50:
            rendered.append("truncated")
        return rendered
    return _fallback_label(value)


def _truncate_string(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}... [truncated {len(value) - limit} chars]"


def _fallback_label(value: Any) -> str:
    return f"[{type(value).__name__}]"


def _source_from_boundary(boundary: str) -> str:
    return boundary.split(".", 1)[0] if boundary else "diagnostics"
