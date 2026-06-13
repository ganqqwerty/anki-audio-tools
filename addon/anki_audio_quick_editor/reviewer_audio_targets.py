"""Import-safe Reviewer audio target HTML contract helpers."""

from __future__ import annotations

import html
import re

AQE_REVIEW_TARGET_CLASS = "aqe-review-audio-target"
AQE_REVIEW_TRIGGER_CLASS = "aqe-review-audio-panel-trigger"
AQE_AUDIO_PANEL_FILTER = "aqe-audio-panel"


def target_html(field_index: int, filename: str) -> str:
    """Render an always-open Reviewer mount target."""
    return target_html_with_attrs(field_index, filename, "")


def explicit_target_field_indices(text: str) -> set[int]:
    """Return field ordinals already represented by explicit Reviewer targets."""
    return {
        int(match)
        for match in re.findall(
            r'class="[^"]*\baqe-review-audio-target\b[^"]*"[^>]*data-field-ord="(\d+)"',
            text,
        )
    }


def audio_panel_trigger_html(field_index: int, filename: str, *, label: str) -> str:
    """Render a click-to-open Reviewer audio-panel trigger and hidden mount target."""
    target = target_html_with_attrs(
        field_index,
        filename,
        ' data-aqe-panel-trigger-target="true" data-aqe-panel-open="false"',
    )
    escaped_filename = html.escape(filename, quote=True)
    escaped_label = html.escape(label, quote=False)
    return (
        f'<button type="button" class="{AQE_REVIEW_TRIGGER_CLASS}" '
        f'data-testid="aqe-review-audio-panel-trigger-{int(field_index)}" '
        f'data-field-ord="{int(field_index)}" '
        f'data-aqe-source-filename="{escaped_filename}">{escaped_label}</button>'
        f"{target}"
    )


def target_html_with_attrs(field_index: int, filename: str, extra_attrs: str) -> str:
    """Render a Reviewer mount target with caller-owned extra data attributes."""
    return (
        f'<div class="{AQE_REVIEW_TARGET_CLASS}" '
        f'data-field-ord="{int(field_index)}" '
        f'data-aqe-source-filename="{html.escape(filename, quote=True)}"{extra_attrs}></div>'
    )
