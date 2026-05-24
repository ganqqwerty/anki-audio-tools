"""Stateful diagnostics runtime helpers."""

from __future__ import annotations

import faulthandler
import json
import logging
import os
import sys
import threading
from collections import deque
from pathlib import Path
from types import TracebackType
from typing import Any

from .diagnostics_runtime_json import safe_json


def install_process_hooks(state: Any, *, capture_exception: Any, logger: logging.Logger) -> None:
    if state.hooks_installed:
        return
    state.previous_sys_hook = sys.excepthook
    state.previous_thread_hook = threading.excepthook

    def _sys_hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        if exc.__traceback__ is None and tb is not None:
            exc = exc.with_traceback(tb)
        capture_exception("process.sys_excepthook", exc, operation="process", log=logger)
        previous = state.previous_sys_hook
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
        previous = state.previous_thread_hook
        if previous is not None and previous is not threading.__excepthook__ and previous is not _thread_hook:
            previous(args)

    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook
    state.hooks_installed = True


def enable_faulthandler(state: Any, *, logger: logging.Logger) -> None:
    if state.crash_log_path is None:
        return
    try:
        if state.crash_file_handle is not None:
            state.crash_file_handle.close()
        state.crash_file_handle = state.crash_log_path.open("a", encoding="utf-8")
        faulthandler.enable(file=state.crash_file_handle, all_threads=True)
    except (OSError, RuntimeError) as exc:
        logger.warning("could not enable faulthandler diagnostics: %s", exc)


def append_event(
    state: Any,
    entry: dict[str, Any],
    *,
    event_log_max_bytes: int,
    logger: logging.Logger,
) -> None:
    path = state.event_log_path
    if path is None:
        return
    try:
        if path.exists() and path.stat().st_size > event_log_max_bytes:
            rotated = path.with_suffix(path.suffix + ".1")
            path.replace(rotated)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, sort_keys=True) + "\n")
            file.flush()
    except OSError as exc:
        logger.warning("could not write diagnostics event log: %s", exc)


def read_dirty_session(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict) and raw.get("clean_exit") is False:
        safe = safe_json(raw)
        return safe if isinstance(safe, dict) else None
    return None


def write_session_marker(state: Any, *, clean_exit: bool, utc_now: Any, logger: logging.Logger) -> None:
    path = state.session_marker_path
    if path is None:
        return
    payload = {
        "session_id": state.session_id,
        "pid": os.getpid(),
        "started_at": state.started_at,
        "updated_at": utc_now(),
        "clean_exit": clean_exit,
        "last_event_seq": state.seq,
    }
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        logger.warning("could not write diagnostics session marker: %s", exc)


def resize_breadcrumb_ring(state: Any, capacity: int) -> None:
    if state.breadcrumbs.maxlen == capacity:
        return
    state.breadcrumbs = deque(list(state.breadcrumbs)[-capacity:], maxlen=capacity)
