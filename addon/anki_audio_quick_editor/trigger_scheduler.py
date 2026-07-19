"""Schedule matching trigger rules for Anki notes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .audio_processing_presets import AudioProcessingPreset, presets_from_raw
from .audio_state import AudioProcessingConfig
from .browser_batch_runner import snapshot_from_note
from .diagnostics_runtime import capture_exception
from .trigger_dispatch import dispatch_trigger_job
from .trigger_jobs import TriggerEventName, TriggerJob
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
    mark_failed,
    mark_running,
    new_generation_token,
    should_schedule,
)

logger = logging.getLogger(__name__)


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
            allow_missing_presets=True,
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
    jobs = _matching_jobs(
        rules,
        event=event,
        note_id=snapshot.note_id,
        note_type_id=note_type_id,
        note_type_name=note_type_name,
        fields=snapshot.fields,
        presets=presets,
        store=store,
        state_path=state_path,
    )
    if not jobs:
        return 0

    for job in jobs:
        mark_running(
            store,
            job.state_key,
            job.input_filename,
            job.action_fingerprint,
            job.generation_token,
        )
    store.save()

    return _dispatch_selected_jobs(
        mw,
        jobs,
        presets=presets,
        media_dir=media_dir,
        config=config,
        artifact_root=artifact_root,
    )


def _matching_jobs(
    rules: tuple[AudioTriggerRule, ...],
    *,
    event: TriggerEventName,
    note_id: int,
    note_type_id: int | None,
    note_type_name: str,
    fields: dict[str, str],
    presets: tuple[AudioProcessingPreset, ...],
    store: TriggerStateStore,
    state_path: Path,
) -> list[TriggerJob]:
    jobs: list[TriggerJob] = []
    for rule in rules:
        job = _job_for_rule(
            rule,
            event=event,
            note_id=note_id,
            note_type_id=note_type_id,
            note_type_name=note_type_name,
            fields=fields,
            presets=presets,
            store=store,
            state_path=state_path,
        )
        if job is not None:
            jobs.append(job)
    return jobs


def _dispatch_selected_jobs(
    mw: Any,
    jobs: list[TriggerJob],
    *,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path,
) -> int:
    scheduled = 0
    for job in jobs:
        try:
            dispatch_trigger_job(
                mw,
                job,
                presets=presets,
                media_dir=media_dir,
                config=config,
                artifact_root=artifact_root,
            )
        except Exception as exc:
            _mark_dispatch_failed(job, exc)
            continue
        scheduled += 1
    return scheduled


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
    try:
        fingerprint = action_fingerprint(rule, presets)
    except ValueError as exc:
        logger.warning("Skipping trigger rule %s: %s", rule.id, exc)
        return None
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


def _addon_config(mw: Any) -> dict[str, Any]:
    addon_id = mw.addonManager.addonFromModule(__name__)
    config = mw.addonManager.getConfig(addon_id) or {}
    return config if isinstance(config, dict) else {}


def _addon_dir(mw: Any) -> Path:
    addon_id = mw.addonManager.addonFromModule(__name__)
    return Path(mw.addonManager.addonsFolder(addon_id))


def _collection_identity(col: Any) -> str | None:
    """Return the stable collection identity used to scope trigger state."""
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


def _mark_dispatch_failed(job: TriggerJob, exc: Exception) -> None:
    message = str(exc) or "trigger dispatch failed"
    store = TriggerStateStore.load(job.state_path)
    mark_failed(store, job.state_key, job.generation_token, message)
    store.save()
    capture_exception(
        "trigger.dispatch",
        exc,
        operation="trigger.dispatch",
        user_message=message,
        context={"note_id": job.note_id, "rule_id": job.rule.id},
        log=logger,
    )
