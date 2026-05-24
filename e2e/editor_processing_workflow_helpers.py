"""Shared helpers for editor processing workflow e2e tests."""

from __future__ import annotations


def split_slug(command: str) -> str:
    if command in {"aqe:volume-up", "aqe:volume-down"}:
        return "volume"
    if command in {"aqe:faster", "aqe:slower"}:
        return "speed"
    return command.removeprefix("aqe:")


def split_menu_selector(command: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-split-{ord_}-{split_slug(command)}-menu"]'


def split_popover_state_js(command: str, ord_: int = 0) -> str:
    slug = split_slug(command)
    return f"""
    (() => {{
      const popover = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-popover"]');
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      const anchor = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-menu"]')?.closest('.aqe-split-button');
      if (!popover || !slider || !anchor) return null;
      const popoverRect = popover.getBoundingClientRect();
      const anchorRect = anchor.getBoundingClientRect();
      return {{
        text: popover.textContent,
        sliderValue: slider.value,
        bottom: popoverRect.bottom,
        left: popoverRect.left,
        right: popoverRect.right,
        top: popoverRect.top,
        buttonBottom: anchorRect.bottom,
        viewportHeight: window.innerHeight,
        viewportWidth: window.innerWidth,
        centerDelta: Math.abs(
          popoverRect.left + popoverRect.width / 2 - (anchorRect.left + anchorRect.width / 2)
        )
      }};
    }})()
    """


def expected_final_status(command: str) -> str:
    return {
        "aqe:slower": "Decreased speed to x0.95.",
        "aqe:faster": "Increased speed to x1.05.",
        "aqe:volume-down": "Decreased volume by 3 dB.",
        "aqe:volume-up": "Increased volume by 3 dB.",
        "aqe:remove-pauses": "Shortened pauses with Normal level.",
        "aqe:pitch-hum": "Rendered pitch hum with Pitch-to-hum mode.",
    }[command]
