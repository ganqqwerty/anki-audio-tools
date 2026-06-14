"""Execute queued trigger jobs against one note."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .audio_processing_presets import AudioProcessingPreset
from .audio_state import AudioProcessingConfig
from .batch_operation_types import BatchNoteResult
from .browser_batch_runner import snapshot_from_note
from .diagnostics_runtime import capture_exception
from .error_codes import AQE_BATCH_INVALID_REQUEST, format_coded_message
from .trigger_batch_adapter import process_trigger_operation
from .trigger_jobs import TriggerExecutionResult, TriggerJob
from .trigger_preset_adapter import process_trigger_preset
from .trigger_result_application import apply_trigger_result, stale_trigger_result
from .trigger_state import TriggerStateStore, is_latest

logger = logging.getLogger(__name__)


def run_trigger_job(
    col: Any,
    job: TriggerJob,
    *,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path | None,
) -> TriggerExecutionResult:
    """Run a queued trigger job and persist successful note changes."""
    store = TriggerStateStore.load(job.state_path)
    if not is_latest(store.get(job.state_key), job.generation_token):
        return TriggerExecutionResult(stale_trigger_result(job))

    try:
        note = col.get_note(job.note_id)
        snapshot = snapshot_from_note(note)
        if job.rule.action_type == "preset":
            result = process_trigger_preset(
                snapshot,
                rule=job.rule,
                presets=presets,
                media_dir=media_dir,
                config=config,
                media_writer=col.media.write_data,
                artifact_root=artifact_root,
            )
        else:
            result = process_trigger_operation(
                snapshot,
                rule=job.rule,
                media_dir=media_dir,
                config=config,
                media_writer=col.media.write_data,
                artifact_root=artifact_root,
            )
        if result.written:
            return apply_trigger_result(col, result)
        return TriggerExecutionResult(result)
    except Exception as exc:
        message = format_coded_message(AQE_BATCH_INVALID_REQUEST, str(exc) or "trigger failed")
        capture_exception(
            "trigger.job",
            exc,
            operation="trigger.job",
            user_message=message,
            context={"note_id": job.note_id, "rule_id": job.rule.id},
            log=logger,
        )
        return TriggerExecutionResult(
            BatchNoteResult(note_id=job.note_id, status="failed", message=message)
        )
