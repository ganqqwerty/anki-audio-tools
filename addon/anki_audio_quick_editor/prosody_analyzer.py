"""Prosody analyzer selection behind a stable import-safe interface."""

from __future__ import annotations

import logging
from pathlib import Path

from .audio_state import AudioProcessingConfig
from .prosody_fallback import analyze_with_fallback
from .prosody_praat import analyze_with_praat, is_praat_available
from .prosody_types import ProsodyTrack

logger = logging.getLogger(__name__)


def analyze_prosody(source_path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
    """Analyze a clip with Parselmouth when available, otherwise use ffmpeg/PCM."""
    if is_praat_available():
        try:
            return analyze_with_praat(source_path, config)
        except Exception as exc:
            logger.info("Parselmouth analysis failed; falling back to ffmpeg/PCM: %s", exc)
    return analyze_with_fallback(source_path, config)
