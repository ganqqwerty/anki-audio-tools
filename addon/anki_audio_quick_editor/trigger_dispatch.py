"""Dispatch trigger jobs through Anki's background task manager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .audio_processing_presets import AudioProcessingPreset
from .audio_state import AudioProcessingConfig
from .batch_operation_types import BatchNoteResult
from .diagnostics_runtime import capture_exception, record_breadcrumb
from .trigger_executor import run_trigger_job
from .trigger_jobs import TriggerExecutionResult, TriggerJob
from .trigger_result_application import complete_trigger_job, publish_trigger_changes

logger = logging.getLogger(__name__)


def dispatch_trigger_job(
    mw: Any,
    job: TriggerJob,
    *,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path,
) -> None:
    """Schedule one trigger job in Anki's background task manager."""
    record_breadcrumb(
        "trigger.scheduled",
        source="trigger",
        operation="trigger.schedule",
        context={"note_id": job.note_id, "rule_id": job.rule.id},
    )

    def task() -> TriggerExecutionResult:
        return run_trigger_job(
            mw.col,
            job,
            presets=presets,
            media_dir=media_dir,
            config=config,
            artifact_root=artifact_root,
        )

    def done(future: Any) -> None:
        try:
            execution = future.result()
        except Exception as exc:
            result = BatchNoteResult(job.note_id, "failed", str(exc) or "trigger failed")
            execution = TriggerExecutionResult(result)
            capture_exception(
                "trigger.worker",
                exc,
                operation="trigger.worker",
                user_message=result.message,
                context={"note_id": job.note_id, "rule_id": job.rule.id},
                log=logger,
            )
        complete_trigger_job(job, execution.result)
        publish_trigger_changes(mw, execution.changes)

    mw.taskman.run_in_background(task, done, uses_collection=True)
