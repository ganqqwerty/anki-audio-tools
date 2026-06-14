"""Compatibility facade for trigger automation runtime entrypoints."""

from __future__ import annotations

from .trigger_dispatch import dispatch_trigger_job
from .trigger_executor import run_trigger_job
from .trigger_jobs import (
    TRIGGER_UPDATE_INITIATOR,
    TriggerEventName,
    TriggerExecutionResult,
    TriggerJob,
)
from .trigger_result_application import complete_trigger_job, publish_trigger_changes
from .trigger_scheduler import schedule_trigger_event

__all__ = [
    "TRIGGER_UPDATE_INITIATOR",
    "TriggerEventName",
    "TriggerExecutionResult",
    "TriggerJob",
    "complete_trigger_job",
    "dispatch_trigger_job",
    "publish_trigger_changes",
    "run_trigger_job",
    "schedule_trigger_event",
]
