"""Helpers for parsing and replacing Anki ``[sound:...]`` references."""

from __future__ import annotations

import ntpath
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import UnsupportedAudioError

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".webm"}
)
SOUND_REF_RE = re.compile(r"(?i)\[sound:(?P<filename>[^\]]+)\]")


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
    for match in SOUND_REF_RE.finditer(field_html):
        filename = match.group("filename").strip()
        refs.append(
            SoundReference(
                tag=match.group(0),
                filename=filename,
                start=match.start(),
                end=match.end(),
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
    return Path(filename).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def safe_media_basename(filename: str) -> str:
    """Return a basename suitable for resolving inside Anki's media folder."""
    return os.path.basename(ntpath.basename(filename))


def replace_sound_reference(
    field_html: str,
    reference: SoundReference,
    new_filename: str,
) -> str:
    """Replace exactly ``reference`` with a new Anki sound tag."""
    return f"{field_html[:reference.start]}[sound:{new_filename}]{field_html[reference.end:]}"
