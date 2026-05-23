"""Shared polling and callback helpers for E2E tests."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtWidgets import QApplication

DEFAULT_E2E_TIMEOUT = 2.0


def _run_event_loop_step() -> None:
    QApplication.processEvents()
    time.sleep(0.01)


def run_js(target, expr: str, callback: Callable[[Any], None] | None = None) -> None:
    """Evaluate JavaScript against a settings dialog or raw Anki webview."""
    if hasattr(target, "run_js"):
        target.run_js(expr, callback)
        return
    if hasattr(target, "evalWithCallback"):
        target.evalWithCallback(expr, callback)
        return
    target.page().runJavaScript(expr, callback)


def wait_for_condition(
    predicate: Callable[[], bool],
    timeout: float = DEFAULT_E2E_TIMEOUT,
    message: str = "Timed out waiting for condition",
) -> None:
    """Process Qt events until a Python predicate becomes true."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        _run_event_loop_step()
    raise TimeoutError(message)


def wait_for_js(target, expr: str, timeout: float = DEFAULT_E2E_TIMEOUT):
    """Evaluate a JS expression until it returns a non-None value."""
    result = [None]

    def _capture(value):
        result[0] = value

    deadline = time.time() + timeout
    while time.time() < deadline:
        result[0] = None
        run_js(target, expr, _capture)
        inner_deadline = time.time() + 0.25
        while result[0] is None and time.time() < inner_deadline:
            _run_event_loop_step()
        if result[0] is not None:
            return result[0]
        _run_event_loop_step()
    raise TimeoutError(f"Timed out waiting for JS result: {expr}")


def wait_for_js_condition(
    target,
    expr: str,
    predicate: Callable[[Any], bool] = bool,
    timeout: float = DEFAULT_E2E_TIMEOUT,
):
    """Poll a JS expression until ``predicate(result)`` returns True.

    Returns the result that satisfied the predicate. Raises ``TimeoutError``
    if the predicate is never satisfied within ``timeout`` seconds. The
    default predicate is :class:`bool`, i.e. wait until the JS result is
    truthy.
    """
    deadline = time.time() + timeout
    last_result: Any = None
    while time.time() < deadline:
        remaining = max(0.01, deadline - time.time())
        try:
            result = wait_for_js(target, expr, timeout=min(0.5, remaining))
            last_result = result
            if predicate(result):
                return result
        except TimeoutError:
            # Inner poll got no JS callback yet — keep the outer loop alive.
            pass
        _run_event_loop_step()
    raise TimeoutError(
        f"Condition not met within {timeout}s for: {expr} "
        f"(last result: {last_result!r})"
    )


def wait_for_selector(target, selector: str, timeout: float = DEFAULT_E2E_TIMEOUT) -> bool:
    """Poll until ``document.querySelector(selector)`` returns an element."""
    deadline = time.time() + timeout
    expr = f"document.querySelector({json.dumps(selector)}) !== null"
    while time.time() < deadline:
        try:
            if wait_for_js(target, expr, timeout=min(0.5, timeout)):
                return True
        except TimeoutError:
            pass
        _run_event_loop_step()
    try:
        body = wait_for_js(
            target,
            "document.body ? document.body.outerHTML.slice(0, 4000) : ''",
            timeout=0.5,
        )
    except TimeoutError:
        body = "<unavailable>"
    raise TimeoutError(f"Timed out waiting for selector: {selector}\nDOM excerpt: {body}")


def click_selector(target, selector: str, timeout: float = DEFAULT_E2E_TIMEOUT) -> None:
    """Wait for a selector, then click it in the webview."""
    wait_for_js_condition(
        target,
        f"""
        (() => {{
          const node = document.querySelector({json.dumps(selector)});
          if (!node) return false;
          if (node.disabled === true || node.getAttribute("aria-disabled") === "true") return false;
          const rect = node.getBoundingClientRect();
          const clientX = rect.left + Math.min(rect.width / 2, Math.max(rect.width - 1, 1));
          const clientY = rect.top + Math.min(rect.height / 2, Math.max(rect.height - 1, 1));
          const base = {{ bubbles: true, button: 0, buttons: 1, clientX, clientY, composed: true }};
          if (typeof PointerEvent === "function") {{
            node.dispatchEvent(new PointerEvent("pointerdown", {{ ...base, pointerId: 1, pointerType: "mouse" }}));
          }}
          node.dispatchEvent(new MouseEvent("mousedown", base));
          if (typeof PointerEvent === "function") {{
            node.dispatchEvent(new PointerEvent("pointerup", {{ ...base, buttons: 0, pointerId: 1, pointerType: "mouse" }}));
          }}
          node.dispatchEvent(new MouseEvent("mouseup", {{ ...base, buttons: 0 }}));
          node.dispatchEvent(new MouseEvent("click", {{ ...base, buttons: 0, detail: 1 }}));
          return true;
        }})()
        """,
        lambda value: value is True,
        timeout=timeout,
    )
    _run_event_loop_step()


def generate_tone(ffmpeg_config, path: Path, duration_s: float) -> None:
    """Generate a deterministic audio fixture through real ffmpeg."""
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={duration_s}",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def parse_async_done_payload(calls: list[str]) -> dict | None:
    """Parse the first ``window.onAsyncDone(...)`` payload from eval calls."""
    prefix = "window.onAsyncDone("
    for call in calls:
        if call.startswith(prefix) and call.endswith(")"):
            return json.loads(call[len(prefix):-1])
    return None
