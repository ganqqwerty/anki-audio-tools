"""Small import-safe cache for prosody analysis results."""

from __future__ import annotations

from pathlib import Path

from .audio_state import AudioProcessingConfig
from .prosody_analyzer import analyze_prosody
from .prosody_types import ProsodyTrack

ProsodyCacheKey = tuple[str, int, int]

_ANALYSIS_CACHE: dict[ProsodyCacheKey, ProsodyTrack] = {}
_ANALYSIS_CACHE_MAX = 32


def prosody_cache_key(path: Path) -> ProsodyCacheKey:
    """Return a cache key tied to a media file's current identity."""
    stat = path.stat()
    return str(path), int(stat.st_size), int(stat.st_mtime_ns)


def analyze_prosody_cached(path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
    """Analyze ``path`` and reuse results while the file identity is unchanged."""
    key = prosody_cache_key(path)
    cached = _ANALYSIS_CACHE.get(key)
    if cached is not None:
        return cached
    track = analyze_prosody(path, config)
    _ANALYSIS_CACHE[key] = track
    while len(_ANALYSIS_CACHE) > _ANALYSIS_CACHE_MAX:
        _ANALYSIS_CACHE.pop(next(iter(_ANALYSIS_CACHE)))
    return track
