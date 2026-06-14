"""Shared helpers for one-note trigger operation adapters."""

from __future__ import annotations

import html

from .audio_processor import (
    render_audio,
    render_converted_audio,
    render_size_reduced_audio,
)
from .batch_operation_processing import BatchOperationDeps
from .batch_operations_helpers import render_batch_denoise
from .prosody_cache import analyze_prosody_cached


def trigger_image_reference(image_filename: str) -> str:
    """Return the complete target-field HTML for a trigger Graph output."""
    return f'<img src="{html.escape(image_filename, quote=True)}">'


def trigger_operation_deps() -> BatchOperationDeps:
    """Return low-level processing dependencies used by trigger adapters."""
    return BatchOperationDeps(
        analyze_prosody_cached=analyze_prosody_cached,
        render_audio=render_audio,
        render_converted_audio=render_converted_audio,
        render_size_reduced_audio=render_size_reduced_audio,
        render_batch_denoise=render_batch_denoise,
    )
