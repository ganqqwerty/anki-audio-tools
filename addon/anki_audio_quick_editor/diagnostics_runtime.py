"""Runtime diagnostics, breadcrumbs, and exception-boundary helpers."""

from __future__ import annotations

import atexit
import copy
import faulthandler
import logging
import sys
import threading
import traceback
import uuid
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .diagnostics_runtime_json import safe_json as _safe_json
from .diagnostics_runtime_json import source_from_boundary as _source_from_boundary
from .diagnostics_runtime_storage import (
    append_event as _append_event,
)
from .diagnostics_runtime_storage import (
    enable_faulthandler as _enable_faulthandler,
)
from .diagnostics_runtime_storage import (
    install_process_hooks as _install_process_hooks,
)
from .diagnostics_runtime_storage import (
    read_dirty_session as _read_dirty_session,
)
from .diagnostics_runtime_storage import (
    resize_breadcrumb_ring as _resize_breadcrumb_ring,
)
from .diagnostics_runtime_storage import (
    write_session_marker as _write_session_marker,
)

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
        self.crash_file_handle: Any = None
        self.hooks_installed = False
        self.atexit_registered = False
        self.previous_sys_hook: Callable[..., Any] | None = None
        self.previous_thread_hook: Callable[..., Any] | None = None


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
        _write_session_marker(_STATE, clean_exit=False, utc_now=_utc_now, logger=logger)
        _enable_faulthandler(_STATE, logger=logger)
        _install_process_hooks(_STATE, capture_exception=capture_exception, logger=logger)
        if not _STATE.atexit_registered:
            atexit.register(mark_session_clean)
            _STATE.atexit_registered = True
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
        _resize_breadcrumb_ring(_STATE, DEBUG_BREADCRUMB_CAPACITY if enabled else DEFAULT_BREADCRUMB_CAPACITY)


def is_debug_enabled() -> bool:
    """Return whether debug-mode diagnostics are enabled."""
    with _STATE.lock:
        enabled = _STATE.debug_enabled
    return bool(enabled)


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
            _append_event(_STATE, entry, event_log_max_bytes=EVENT_LOG_MAX_BYTES, logger=logger)
        if should_flush:
            _write_session_marker(_STATE, clean_exit=False, utc_now=_utc_now, logger=logger)
            flush_logging()
    return copy.deepcopy(entry)


def recent_breadcrumbs(limit: int = 40) -> list[dict[str, Any]]:
    """Return the newest breadcrumbs in chronological order."""
    with _STATE.lock:
        events = list(_STATE.breadcrumbs)[-limit:]
    return copy.deepcopy(events)


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
        incident = _STATE.latest_incident
    return copy.deepcopy(incident)


def support_report_context() -> dict[str, Any]:
    """Return diagnostics data ready for support report rendering."""
    with _STATE.lock:
        latest_error = _STATE.latest_incident
        recent_events = list(_STATE.breadcrumbs)
        crash_forensics = {
            "session_id": _STATE.session_id,
            "started_at": _STATE.started_at,
            "debug_enabled": _STATE.debug_enabled,
            "event_log_path": str(_STATE.event_log_path or ""),
            "crash_log_path": str(_STATE.crash_log_path or ""),
            "session_marker_path": str(_STATE.session_marker_path or ""),
            "previous_dirty_session": _STATE.previous_dirty_session,
        }
    return {
        "latest_error": copy.deepcopy(latest_error),
        "recent_events": copy.deepcopy(recent_events),
        "crash_forensics": copy.deepcopy(crash_forensics),
    }


def mark_session_clean() -> None:
    """Mark the diagnostics session as cleanly closed when possible."""
    with _STATE.lock:
        _write_session_marker(_STATE, clean_exit=True, utc_now=_utc_now, logger=logger)
        if _STATE.crash_file_handle is not None:
            try:
                _STATE.crash_file_handle.flush()
            except OSError:
                pass


def release_runtime_files() -> None:
    """Close diagnostics files that would block add-on replacement on Windows."""
    with _STATE.lock:
        if _STATE.crash_file_handle is None:
            return
        try:
            faulthandler.disable()
        except RuntimeError:
            pass
        try:
            _STATE.crash_file_handle.flush()
        except OSError:
            pass
        try:
            _STATE.crash_file_handle.close()
        except OSError:
            pass
        _STATE.crash_file_handle = None


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
                except Exception as exc:  # pragma: no cover - logging handler defensive path
                    logger.debug("logging handler flush failed: %s", exc)
            if not current.propagate or current.parent is current:
                break
            current = current.parent


def reset_for_tests() -> None:
    """Reset module state for focused tests."""
    global _STATE
    old_state = _STATE
    with old_state.lock:
        if old_state.previous_sys_hook is not None:
            sys.excepthook = old_state.previous_sys_hook
        if old_state.previous_thread_hook is not None:
            threading.excepthook = old_state.previous_thread_hook
        if old_state.crash_file_handle is not None:
            try:
                faulthandler.disable()
                old_state.crash_file_handle.close()
            except OSError:
                pass
        _STATE = _DiagnosticsState()
