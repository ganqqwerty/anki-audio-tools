"""Helpers for parsing and replacing Anki ``[sound:...]`` references."""

from __future__ import annotations

import html
import ntpath
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import UnsupportedAudioError

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".webm"}
)
SOUND_REF_START_RE = re.compile(r"(?i)\[sound:")


@dataclass(frozen=True)
class SoundReference:
    """A single sound tag occurrence inside a field."""

    tag: str
    filename: str
    start: int
    end: int

    @property
    def extension(self) -> str:
        """Return the lowercase filename extension."""
        return Path(self.filename).suffix.lower()


@dataclass(frozen=True)
class SoundReferenceSelection:
    """The parser result for a field that may contain one or more sound tags."""

    selected: SoundReference | None
    references: tuple[SoundReference, ...]

    @property
    def has_multiple(self) -> bool:
        """Return true when the field contains more than one sound reference."""
        return len(self.references) > 1


def find_sound_references(field_html: str) -> tuple[SoundReference, ...]:
    """Return all Anki sound references in field order."""
    refs: list[SoundReference] = []
    starts = tuple(SOUND_REF_START_RE.finditer(field_html))
    for index, match in enumerate(starts):
        filename_start = match.end()
        next_start = starts[index + 1].start() if index + 1 < len(starts) else len(field_html)
        filename_end = _sound_reference_filename_end(field_html, filename_start, next_start)
        if filename_end is None:
            continue
        filename = html.unescape(field_html[filename_start:filename_end])
        refs.append(
            SoundReference(
                tag=field_html[match.start() : filename_end + 1],
                filename=filename,
                start=match.start(),
                end=filename_end + 1,
            )
        )
    return tuple(refs)


def select_first_sound_reference(field_html: str) -> SoundReferenceSelection:
    """Select the first supported sound reference in a field.

    MVP intentionally edits the first supported tag when a field contains
    multiple references.
    """
    refs = find_sound_references(field_html)
    for ref in refs:
        if is_supported_audio_filename(ref.filename):
            return SoundReferenceSelection(selected=ref, references=refs)
    if refs:
        raise UnsupportedAudioError("The first audio reference uses an unsupported format.")
    return SoundReferenceSelection(selected=None, references=refs)


def is_supported_audio_filename(filename: str) -> bool:
    """Return whether ``filename`` has a supported audio extension."""
    return _audio_extension_for_support(filename) in SUPPORTED_AUDIO_EXTENSIONS


def _sound_reference_filename_end(
    field_html: str,
    filename_start: int,
    search_limit: int,
) -> int | None:
    first_close = field_html.find("]", filename_start, search_limit)
    if first_close < 0:
        return None
    best_supported_close: int | None = None
    close = first_close
    while close >= 0:
        filename = html.unescape(field_html[filename_start:close])
        if is_supported_audio_filename(filename):
            best_supported_close = close
        close = field_html.find("]", close + 1, search_limit)
    return best_supported_close if best_supported_close is not None else first_close


def _audio_extension_for_support(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return suffix
    visible_filename = filename.rstrip().rstrip(".")
    if visible_filename != filename:
        return Path(visible_filename).suffix.lower()
    return suffix


def safe_media_basename(filename: str) -> str:
    """Return a basename suitable for resolving inside Anki's media folder."""
    if platform.system() == "Windows":
        return ntpath.basename(filename)
    return os.path.basename(filename)


def replace_sound_reference(
    field_html: str,
    reference: SoundReference,
    new_filename: str,
) -> str:
    """Replace exactly ``reference`` with a new Anki sound tag."""
    return f"{field_html[:reference.start]}[sound:{new_filename}]{field_html[reference.end:]}"
