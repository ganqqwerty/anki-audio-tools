"""Cross-platform helpers for resolving Anki collection media files."""

from __future__ import annotations

import platform
from pathlib import Path

from .sound_refs import safe_media_basename


def media_filenames_match(left: str, right: str) -> bool:
    """Return whether two Anki media filenames identify the same file."""
    left_name = safe_media_basename(left)
    right_name = safe_media_basename(right)
    if platform.system() == "Windows":
        return left_name.casefold() == right_name.casefold()
    return left_name == right_name


def resolve_media_file_path(media_dir: Path, filename: str) -> Path:
    """Return the media path for ``filename`` using the platform filename policy."""
    basename = safe_media_basename(filename)
    candidate = media_dir / basename
    if platform.system() == "Windows":
        return _windows_case_variant(media_dir, basename) or candidate
    return candidate


def existing_media_file_path(media_dir: Path, filename: str) -> Path | None:
    """Return an existing media path when it exists under the platform policy."""
    basename = safe_media_basename(filename)
    if platform.system() == "Windows":
        candidate = _windows_case_variant(media_dir, basename) or (media_dir / basename)
        return candidate if candidate.is_file() else None
    return _exact_file_variant(media_dir, basename)


def _exact_file_variant(media_dir: Path, basename: str) -> Path | None:
    try:
        for child in media_dir.iterdir():
            if child.name == basename and child.is_file():
                return child
    except OSError:
        return None
    return None


def _windows_case_variant(media_dir: Path, basename: str) -> Path | None:
    folded = basename.casefold()
    try:
        for child in media_dir.iterdir():
            if child.name.casefold() == folded and child.is_file():
                return child
    except OSError:
        return None
    return None
