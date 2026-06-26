"""Characterization test: lock the audio injection wiring contract."""
from __future__ import annotations

import subprocess
import tempfile

from anki_audio_quick_editor import (
    audio_external,
    audio_noise_reduction,
    audio_pitch_hum,
    audio_rendering,
)
from anki_audio_quick_editor import audio_processor as facade


def test_sync_rendering_injects_wrapped_callables():
    facade._sync_rendering_dependencies()
    assert audio_rendering.find_ffmpeg is facade.find_ffmpeg
    assert audio_rendering.probe_duration_ms is facade.probe_duration_ms


def test_sync_noise_injects_wrapped_callables():
    facade._sync_noise_dependencies()
    assert audio_noise_reduction.find_ffmpeg is facade.find_ffmpeg
    assert audio_noise_reduction.find_deep_filter is facade.find_deep_filter


def test_sync_pitch_hum_injects_wrapped_callables():
    facade._sync_pitch_hum_dependencies()
    assert audio_pitch_hum.find_ffmpeg is facade.find_ffmpeg


def test_sync_external_injects_wrapped_callables():
    facade._sync_external_dependencies()
    assert audio_external.find_ffmpeg is facade.find_ffmpeg
    assert audio_external.find_ffprobe is facade.find_ffprobe


def test_leaf_modules_self_import_stdlib():
    """Stdlib identity is order-independent (shared module object)."""
    assert audio_rendering.subprocess is subprocess
    assert audio_rendering.tempfile is tempfile
