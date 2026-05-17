"""Compatibility wrappers for graph-oriented batch visualization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .audio_operations import OP_GRAPH
from .batch_operations import (
    BatchNoteResult,
    BatchNoteSnapshot,
    BatchRunRequest,
    MediaWriter,
    NowProvider,
    process_note_batch_operation,
)

if TYPE_CHECKING:
    from .audio_state import AudioProcessingConfig


def process_note_visualization(
    note: BatchNoteSnapshot,
    *,
    source_field: str,
    target_field: str,
    media_dir: Path,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    now_provider: NowProvider | None = None,
) -> BatchNoteResult:
    """Run the legacy graph-only batch path through the shared executor."""
    return process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_GRAPH,
            source_field=source_field,
            target_field=target_field,
        ),
        media_dir=media_dir,
        config=config,
        media_writer=media_writer,
        now_provider=now_provider,
    )
