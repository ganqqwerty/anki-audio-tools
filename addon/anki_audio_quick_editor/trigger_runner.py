"""Scheduling and persistence for trigger automation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .audio_processing_presets import AudioProcessingPreset, presets_from_raw
from .audio_state import AudioProcessingConfig
from .batch_operation_types import BatchNoteResult
from .browser_batch_runner import snapshot_from_note
from .diagnostics_runtime import capture_exception, record_breadcrumb
from .error_codes import AQE_BATCH_INVALID_REQUEST, format_coded_message
from .trigger_batch_adapter import process_trigger_operation
from .trigger_preset_adapter import process_trigger_preset
from .trigger_rules import (
    AudioTriggerRule,
    action_fingerprint,
    first_supported_sound_filename,
    note_type_matches,
    rule_applies_to_event,
    trigger_rules_from_raw,
)
from .trigger_state import (
    TriggerStateKey,
    TriggerStateStore,
    collection_state_path,
    is_latest,
    mark_failed,
    mark_running,
    mark_succeeded,
    new_generation_token,
    should_schedule,
)

TriggerEventName = Literal["add", "edit"]
TRIGGER_UPDATE_INITIATOR = object()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TriggerJob:
    """One queued trigger execution."""

    note_id: int
    rule: AudioTriggerRule
    state_key: TriggerStateKey
    state_path: Path
    generation_token: str
    input_filename: str
    action_fingerprint: str


def schedule_trigger_event(mw: Any, note: Any, event: TriggerEventName) -> int:
    """Schedule matching trigger rules for one manually added or edited note."""
    if getattr(mw, "col", None) is None:
        return 0
    col = mw.col
    config_payload = _addon_config(mw)
    try:
        presets = presets_from_raw(config_payload.get("audio_processing_presets"))
        rules = trigger_rules_from_raw(
            config_payload.get("audio_trigger_rules"),
            presets=presets,
        )
    except Exception as exc:
        _capture_scheduler_exception(exc, note_id=_note_id(note), event=event)
        return 0

    if not rules:
        return 0

    snapshot = snapshot_from_note(note)
    note_type_id, note_type_name = _note_type_identity(note, snapshot.notetype_name)
    addon_dir = _addon_dir(mw)
    state_path = collection_state_path(addon_dir, _collection_identity(col))
    store = TriggerStateStore.load(state_path)
    config = AudioProcessingConfig.from_config(config_payload)
    media_dir = Path(col.media.dir())
    artifact_root = addon_dir / "aqe_artifacts"

    scheduled = 0
    for rule in rules:
        job = _job_for_rule(
            rule,
            event=event,
            note_id=snapshot.note_id,
            note_type_id=note_type_id,
            note_type_name=note_type_name,
            fields=snapshot.fields,
            presets=presets,
            store=store,
            state_path=state_path,
        )
        if job is None:
            continue
        mark_running(
            store,
            job.state_key,
            job.input_filename,
            job.action_fingerprint,
            job.generation_token,
        )
        store.save()
        _dispatch_job(
            mw,
            job,
            presets=presets,
            media_dir=media_dir,
            config=config,
            artifact_root=artifact_root,
        )
        scheduled += 1

    return scheduled


def run_trigger_job(
    col: Any,
    job: TriggerJob,
    *,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path | None,
) -> BatchNoteResult:
    """Run a queued trigger job and persist successful note changes."""
    store = TriggerStateStore.load(job.state_path)
    if not is_latest(store.get(job.state_key), job.generation_token):
        return BatchNoteResult(
            note_id=job.note_id,
            status="skipped",
            message="stale trigger completion",
            audio_filename=job.input_filename,
        )

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
            result = _apply_trigger_result(col, result)
        return result
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
        return BatchNoteResult(note_id=job.note_id, status="failed", message=message)


def complete_trigger_job(job: TriggerJob, result: BatchNoteResult) -> None:
    """Persist latest trigger completion status."""
    store = TriggerStateStore.load(job.state_path)
    if result.written or _handled_skip(result):
        mark_succeeded(
            store,
            job.state_key,
            job.generation_token,
            result.audio_filename or job.input_filename,
            result.written_filename,
        )
    elif result.status != "skipped" or result.message != "stale trigger completion":
        mark_failed(store, job.state_key, job.generation_token, result.message)
    store.save()


def publish_trigger_changes(mw: Any, changes: Any) -> None:
    """Notify Anki that trigger-initiated note updates completed."""
    if changes is None:
        return
    try:
        from aqt import gui_hooks

        mw.update_undo_actions()
        gui_hooks.operation_did_execute(changes, TRIGGER_UPDATE_INITIATOR)
    except Exception as exc:  # pragma: no cover - UI refresh is best effort
        capture_exception(
            "trigger.refresh_after_update",
            exc,
            operation="trigger.refresh",
            user_message=str(exc),
            context={"has_changes": changes is not None},
            log=logger,
        )


def _dispatch_job(
    mw: Any,
    job: TriggerJob,
    *,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path,
) -> None:
    record_breadcrumb(
        "trigger.scheduled",
        source="trigger",
        operation="trigger.schedule",
        context={"note_id": job.note_id, "rule_id": job.rule.id},
    )

    def task() -> tuple[BatchNoteResult, Any]:
        result = run_trigger_job(
            mw.col,
            job,
            presets=presets,
            media_dir=media_dir,
            config=config,
            artifact_root=artifact_root,
        )
        return result, getattr(result, "_trigger_changes", None)

    def done(future: Any) -> None:
        try:
            result, changes = future.result()
        except Exception as exc:
            result = BatchNoteResult(job.note_id, "failed", str(exc) or "trigger failed")
            changes = None
            capture_exception(
                "trigger.worker",
                exc,
                operation="trigger.worker",
                user_message=result.message,
                context={"note_id": job.note_id, "rule_id": job.rule.id},
                log=logger,
            )
        complete_trigger_job(job, result)
        publish_trigger_changes(mw, changes)

    mw.taskman.run_in_background(task, done, uses_collection=True)


def _job_for_rule(
    rule: AudioTriggerRule,
    *,
    event: TriggerEventName,
    note_id: int,
    note_type_id: int | None,
    note_type_name: str,
    fields: dict[str, str],
    presets: tuple[AudioProcessingPreset, ...],
    store: TriggerStateStore,
    state_path: Path,
) -> TriggerJob | None:
    if not rule_applies_to_event(rule, event):
        return None
    if not note_type_matches(rule, note_type_id, note_type_name):
        return None
    field_html = fields.get(rule.source_field)
    if field_html is None:
        return None
    filename = first_supported_sound_filename(field_html)
    if filename is None:
        return None
    fingerprint = action_fingerprint(rule, presets)
    key = TriggerStateKey(note_id=note_id, rule_id=rule.id, source_field=rule.source_field)
    if not should_schedule(store.get(key), filename, fingerprint):
        return None
    return TriggerJob(
        note_id=note_id,
        rule=rule,
        state_key=key,
        state_path=state_path,
        generation_token=new_generation_token(),
        input_filename=filename,
        action_fingerprint=fingerprint,
    )


def _apply_trigger_result(col: Any, result: BatchNoteResult) -> BatchNoteResult:
    note = col.get_note(result.note_id)
    if result.field_updates is not None:
        for field_name, expected_html in (result.original_field_html or {}).items():
            if _note_field_value(note, field_name) != expected_html:
                return _conflict_result(result, field_name)
        for field_name, html in result.field_updates.items():
            note[field_name] = html
    else:
        assert result.target_field is not None
        assert result.target_html is not None
        if (
            result.original_target_html is not None
            and _note_field_value(note, result.target_field) != result.original_target_html
        ):
            return _conflict_result(result, result.target_field)
        note[result.target_field] = result.target_html
    changes = col.update_note(note)
    object.__setattr__(result, "_trigger_changes", changes)
    return result


def _conflict_result(result: BatchNoteResult, field_name: str) -> BatchNoteResult:
    return BatchNoteResult(
        note_id=result.note_id,
        status="failed",
        message=format_coded_message(
            AQE_BATCH_INVALID_REQUEST,
            f"target field {field_name!r} changed during trigger processing",
        ),
        target_field=field_name,
        audio_filename=result.audio_filename,
        image_filename=result.image_filename,
        written_filename=result.written_filename,
        field_updates=result.field_updates,
        original_field_html=result.original_field_html,
    )


def _handled_skip(result: BatchNoteResult) -> bool:
    return result.status == "skipped" and result.audio_filename is not None


def _addon_config(mw: Any) -> dict[str, Any]:
    addon_id = mw.addonManager.addonFromModule(__name__)
    config = mw.addonManager.getConfig(addon_id) or {}
    return config if isinstance(config, dict) else {}


def _addon_dir(mw: Any) -> Path:
    addon_id = mw.addonManager.addonFromModule(__name__)
    return Path(mw.addonManager.addonsFolder(addon_id))


def _collection_identity(col: Any) -> str | None:
    value = getattr(col, "path", None)
    if callable(value):
        value = value()
    if value:
        return str(value)
    media = getattr(col, "media", None)
    if media is not None and hasattr(media, "dir"):
        return str(media.dir())
    return None


def _note_type_identity(note: Any, fallback_name: str) -> tuple[int | None, str]:
    try:
        note_type = note.note_type()
    except (AttributeError, TypeError):
        return None, fallback_name
    if not isinstance(note_type, dict):
        return None, fallback_name
    raw_id = note_type.get("id")
    note_type_id = raw_id if isinstance(raw_id, int) and not isinstance(raw_id, bool) else None
    return note_type_id, str(note_type.get("name", fallback_name))


def _note_id(note: Any) -> int | None:
    try:
        return int(note.id)
    except (AttributeError, TypeError, ValueError):
        return None


def _note_field_value(note: Any, field_name: str) -> str:
    try:
        return str(note[field_name])
    except (KeyError, TypeError, AttributeError):
        return ""


def _capture_scheduler_exception(
    exc: Exception, *, note_id: int | None, event: TriggerEventName
) -> None:
    capture_exception(
        "trigger.schedule",
        exc,
        operation="trigger.schedule",
        user_message=str(exc),
        context={"note_id": note_id, "event": event},
        log=logger,
    )
