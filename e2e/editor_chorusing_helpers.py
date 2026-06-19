"""Shared E2E helpers for graph chorusing workflows."""

from __future__ import annotations

from e2e.helpers import wait_for_js_condition


def _click_chorusing_marker(editor, ratio: float, *, expected_count: int):
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="aqe-chorusing-marker-row-0"]');
          const hitbox = document.querySelector('.aqe-chorusing-marker-hitbox');
          const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
          const rect = svg?.getBoundingClientRect();
          const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
          if (!row || !hitbox || !svg || !rect || !bounds) return null;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          const target = row.getAttribute("aria-hidden") === "true" ? hitbox : row;
          target.dispatchEvent(new EventCtor('pointerdown', {{
            bubbles: true,
            clientX: bounds.left + bounds.width * {ratio},
            clientY: rect.top + 14,
          }}));
          window.dispatchEvent(new EventCtor('pointerup', {{
            bubbles: true,
            clientX: bounds.left + bounds.width * {ratio},
            clientY: rect.top + 14,
          }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None and len(state["chorusingMarkersMs"]) == expected_count,
        timeout=5.0,
    )


def _click_chorusing_practice(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-chorusing-practice"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["chorusingState"] == "playing",
        timeout=5.0,
    )
