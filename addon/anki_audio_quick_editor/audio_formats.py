"""Shared audio output format helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

OutputFormat = Literal["source", "mp3", "m4a", "wav", "flac"]
ConcreteOutputFormat = Literal["mp3", "m4a", "wav", "flac"]

SUPPORTED_OUTPUT_FORMATS: tuple[OutputFormat, ...] = ("source", "mp3", "m4a", "wav", "flac")
CONCRETE_OUTPUT_FORMATS: tuple[ConcreteOutputFormat, ...] = ("mp3", "m4a", "wav", "flac")
DEFAULT_OUTPUT_FORMAT: OutputFormat = "source"

_SUPPORTED_FORMAT_SET = frozenset(SUPPORTED_OUTPUT_FORMATS)
_CONCRETE_FORMAT_SET = frozenset(CONCRETE_OUTPUT_FORMATS)


def normalize_output_format(value: object, default: OutputFormat = DEFAULT_OUTPUT_FORMAT) -> OutputFormat:
    """Return a supported output format for permissive settings loading."""
    candidate = str(value).strip().lower() if isinstance(value, str) else ""
    if candidate in _SUPPORTED_FORMAT_SET:
        return candidate
    return default


def validate_target_format(value: object) -> ConcreteOutputFormat:
    """Return a concrete target format or raise for explicit operation requests."""
    candidate = str(value).strip().lower() if isinstance(value, str) else ""
    if candidate in _CONCRETE_FORMAT_SET:
        return candidate
    raise ValueError(f"Unsupported concrete audio output format: {value!r}")


def output_extension(target_format: object) -> str:
    """Return the file extension for a supported output format."""
    return f".{validate_target_format(target_format)}"


def format_label(target_format: object) -> str:
    """Return a user-facing label for a supported output format."""
    if normalize_output_format(target_format) == "source":
        return "Same as source"
    return validate_target_format(target_format).upper()


def visible_extension(filename: str | Path) -> str | None:
    """Return the user-visible file extension without the leading dot."""
    suffix = Path(filename).suffix
    if not suffix:
        return None
    return suffix[1:].lower()


def is_same_visible_format(filename: str | Path, target_format: object) -> bool:
    """Return whether a source filename already uses the target visible extension."""
    if normalize_output_format(target_format) == "source":
        return True
    return visible_extension(filename) == validate_target_format(target_format)
