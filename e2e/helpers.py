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
    deadline = time.time() + timeout
    result: list[str | None] = [None]

    def _capture(value):
        result[0] = str(value)

    while time.time() < deadline:
        result[0] = None
        run_js(
            target,
            f"""
            (() => {{
              let node = document.querySelector({json.dumps(selector)});
              if (!node) return "missing";
              if (node.disabled === true || node.getAttribute("aria-disabled") === "true") return "disabled";
              const style = window.getComputedStyle(node);
              if (
                style.display === "none" ||
                style.visibility !== "visible" ||
                style.pointerEvents === "none" ||
                Number(style.opacity) === 0
              ) return `style:${{style.display}}:${{style.visibility}}:${{style.pointerEvents}}:${{style.opacity}}`;
              let rect = node.getBoundingClientRect();
              if (rect.bottom <= 0 || rect.top >= window.innerHeight) {{
                node.scrollIntoView({{ block: "center", inline: "nearest" }});
                rect = node.getBoundingClientRect();
              }}
              if (rect.width <= 0 || rect.height <= 0) return `geometry:${{rect.width}}x${{rect.height}}`;
              const left = Math.max(0, rect.left);
              const right = Math.min(window.innerWidth, rect.right);
              const top = Math.max(0, rect.top);
              const bottom = Math.min(window.innerHeight, rect.bottom);
              const clientX = (left + right) / 2;
              const clientY = (top + bottom) / 2;
              if (
                right <= left || bottom <= top
              ) return `viewport:${{clientX}},${{clientY}}`;
              const candidates = [
                [clientX, clientY], [left + 2, top + 2], [right - 2, top + 2],
                [left + 2, bottom - 2], [right - 2, bottom - 2],
              ];
              const point = candidates.find(([x, y]) => {{
                const candidateHit = document.elementFromPoint(x, y);
                const currentNode = candidateHit?.closest?.({json.dumps(selector)});
                return candidateHit && (
                  candidateHit === node || node.contains(candidateHit) || currentNode === document.querySelector({json.dumps(selector)})
                );
              }});
              const hit = document.elementFromPoint(clientX, clientY);
              if (!point) {{
                let overlay = hit;
                while (overlay) {{
                  const position = window.getComputedStyle(overlay).position;
                  if (position === "sticky" || position === "fixed") break;
                  overlay = overlay.parentElement;
                }}
                if (overlay) {{
                  const overlayRect = overlay.getBoundingClientRect();
                  const delta = rect.top >= overlayRect.top ? overlayRect.height + 8 : -(overlayRect.height + 8);
                  let scroller = node.parentElement;
                  while (scroller) {{
                    const scrollerStyle = window.getComputedStyle(scroller);
                    const canScroll = /(auto|scroll|overlay)/.test(scrollerStyle.overflowY)
                      && scroller.scrollHeight > scroller.clientHeight;
                    if (canScroll) break;
                    scroller = scroller.parentElement;
                  }}
                  const before = scroller?.scrollTop ?? window.scrollY;
                  if (scroller) scroller.scrollTop += delta;
                  else window.scrollBy(0, delta);
                  const after = scroller?.scrollTop ?? window.scrollY;
                  return `scrolling-overlay:target=${{rect.top}}-${{rect.bottom}}:overlay=${{overlayRect.top}}-${{overlayRect.bottom}}:scroll=${{before}}-${{after}}:max=${{scroller ? scroller.scrollHeight - scroller.clientHeight : document.documentElement.scrollHeight - window.innerHeight}}`;
                }}
                if (node.getAttribute("data-aqe-click-scroll-attempted") !== "true") {{
                  node.setAttribute("data-aqe-click-scroll-attempted", "true");
                  node.scrollIntoView({{ block: "center", inline: "nearest" }});
                  return "scrolling-covered-target";
                }}
                return `covered:${{hit?.tagName || "none"}}:${{hit?.getAttribute?.("data-testid") || ""}}:${{hit?.className || ""}}:command=${{hit?.closest?.('[data-aqe-command]')?.getAttribute?.('data-aqe-command') || ''}}:html=${{hit?.parentElement?.outerHTML?.slice?.(0, 500) || ''}}:rect=${{rect.left}},${{rect.top}},${{rect.right}},${{rect.bottom}}`;
              }}
              const [clickX, clickY] = point;
              const resolvedNode = document.elementFromPoint(clickX, clickY)?.closest?.({json.dumps(selector)});
              if (resolvedNode) node = resolvedNode;
              node.removeAttribute("data-aqe-click-scroll-attempted");
              const base = {{ bubbles: true, button: 0, buttons: 1, clientX: clickX, clientY: clickY, composed: true }};
              if (typeof PointerEvent === "function") {{
                node.dispatchEvent(new PointerEvent("pointerdown", {{ ...base, pointerId: 1, pointerType: "mouse" }}));
              }}
              node.dispatchEvent(new MouseEvent("mousedown", base));
              if (typeof PointerEvent === "function") {{
                node.dispatchEvent(new PointerEvent("pointerup", {{ ...base, buttons: 0, pointerId: 1, pointerType: "mouse" }}));
              }}
              node.dispatchEvent(new MouseEvent("mouseup", {{ ...base, buttons: 0 }}));
              node.dispatchEvent(new MouseEvent("click", {{ ...base, buttons: 0, detail: 1 }}));
              return "clicked";
            }})()
            """,
            _capture,
        )
        while result[0] is None and time.time() < deadline:
            _run_event_loop_step()
        if result[0] == "clicked":
            _run_event_loop_step()
            return
        _run_event_loop_step()
    raise TimeoutError(f"Timed out clicking selector: {selector}; last result={result[0]!r}")


def trusted_pointer_to_selector(target, selector: str, *, click: bool) -> None:
    """Move or click through Qt at the center of a verified WebView element."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    point = wait_for_js_condition(
        target,
        f"""
        (() => {{
          const node = document.querySelector({json.dumps(selector)});
          if (!node || node.disabled || node.getAttribute('aria-disabled') === 'true') return null;
          const rect = node.getBoundingClientRect();
          return {{ x: Math.round(rect.left + rect.width / 2), y: Math.round(rect.top + rect.height / 2) }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )
    web_point = QPoint(int(point["x"]), int(point["y"]))
    widget = target.childAt(web_point) or target.focusProxy() or target
    widget_point = widget.mapFrom(target, web_point) if widget is not target else web_point
    if click:
        QTest.mouseClick(
            widget,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            widget_point,
        )
    else:
        QTest.mouseMove(target, QPoint(1, 1))
        _run_event_loop_step()
        QTest.mouseMove(widget, widget_point)
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
        encoding="utf-8",
        errors="replace",
    )


def parse_async_done_payload(calls: list[str]) -> dict | None:
    """Parse the first ``window.onAsyncDone(...)`` payload from eval calls."""
    prefix = "window.onAsyncDone("
    for call in calls:
        if call.startswith(prefix) and call.endswith(")"):
            return json.loads(call[len(prefix):-1])
    return None
