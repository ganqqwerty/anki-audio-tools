"""Import-safe sidecar state for trigger automation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

TriggerProcessingStatus = Literal["idle", "running", "succeeded", "failed"]


@dataclass(frozen=True)
class TriggerStateKey:
    """Identity for one trigger state entry."""

    note_id: int
    rule_id: str
    source_field: str


@dataclass(frozen=True)
class TriggerStateEntry:
    """Persisted state for one note/rule/source field trigger."""

    last_handled_field_filename: str | None
    input_filename: str | None
    action_fingerprint: str | None
    generation_token: str | None
    status: TriggerProcessingStatus
    last_successful_output_filename: str | None
    updated_at: str
    last_error: str | None


class TriggerStateStore:
    """JSON-backed store for trigger state entries."""

    def __init__(self, path: Path, entries: dict[TriggerStateKey, TriggerStateEntry] | None = None):
        self.path = path
        self.entries: dict[TriggerStateKey, TriggerStateEntry] = entries or {}

    @classmethod
    def load(cls, path: Path) -> "TriggerStateStore":
        """Load a store from ``path`` or return an empty store."""
        if not path.exists():
            return cls(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return cls(path)
        entries: dict[TriggerStateKey, TriggerStateEntry] = {}
        for raw_key, raw_entry in raw.items():
            key = _key_from_storage(raw_key)
            entry = _entry_from_raw(raw_entry)
            if key is not None and entry is not None:
                entries[key] = entry
        return cls(path, entries)

    def save(self) -> None:
        """Write the current entries to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            _key_to_storage(key): asdict(entry)
            for key, entry in sorted(
                self.entries.items(),
                key=lambda item: _key_to_storage(item[0]),
            )
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, key: TriggerStateKey) -> TriggerStateEntry | None:
        """Return the entry for ``key`` when present."""
        return self.entries.get(key)

    def set(self, key: TriggerStateKey, entry: TriggerStateEntry) -> None:
        """Set the entry for ``key``."""
        self.entries[key] = entry


def collection_state_path(addon_dir: Path, collection_path: str | None) -> Path:
    """Return the trigger sidecar path for one collection identity."""
    identity = collection_path or "no_collection"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return addon_dir / "aqe_artifacts" / "trigger_state" / f"{digest}.json"


def should_schedule(
    entry: TriggerStateEntry | None,
    filename: str,
    fingerprint: str,
) -> bool:
    """Return whether a matching trigger should schedule work."""
    if entry is None:
        return True
    if entry.action_fingerprint != fingerprint:
        return True
    if entry.status == "running":
        return entry.input_filename != filename
    if entry.status == "succeeded":
        return entry.last_handled_field_filename != filename
    return True


def new_generation_token() -> str:
    """Return a unique generation token for latest-wins checks."""
    return uuid4().hex


def is_latest(entry: TriggerStateEntry | None, token: str) -> bool:
    """Return whether ``token`` is still the latest token for an entry."""
    return entry is not None and entry.generation_token == token


def mark_running(
    store: TriggerStateStore,
    key: TriggerStateKey,
    filename: str,
    fingerprint: str,
    token: str,
) -> None:
    """Record that a trigger job started or superseded an older job."""
    current = store.get(key)
    store.set(
        key,
        TriggerStateEntry(
            last_handled_field_filename=(
                current.last_handled_field_filename if current is not None else None
            ),
            input_filename=filename,
            action_fingerprint=fingerprint,
            generation_token=token,
            status="running",
            last_successful_output_filename=(
                current.last_successful_output_filename if current is not None else None
            ),
            updated_at=_now_iso(),
            last_error=None,
        ),
    )


def mark_succeeded(
    store: TriggerStateStore,
    key: TriggerStateKey,
    token: str,
    handled_filename: str,
    output_filename: str | None,
) -> None:
    """Record a successful latest trigger completion."""
    current = store.get(key)
    if not is_latest(current, token):
        return
    assert current is not None
    store.set(
        key,
        TriggerStateEntry(
            last_handled_field_filename=handled_filename,
            input_filename=current.input_filename,
            action_fingerprint=current.action_fingerprint,
            generation_token=token,
            status="succeeded",
            last_successful_output_filename=output_filename,
            updated_at=_now_iso(),
            last_error=None,
        ),
    )


def mark_failed(
    store: TriggerStateStore,
    key: TriggerStateKey,
    token: str,
    error: str,
) -> None:
    """Record a failed latest trigger completion."""
    current = store.get(key)
    if not is_latest(current, token):
        return
    assert current is not None
    store.set(
        key,
        TriggerStateEntry(
            last_handled_field_filename=current.last_handled_field_filename,
            input_filename=current.input_filename,
            action_fingerprint=current.action_fingerprint,
            generation_token=token,
            status="failed",
            last_successful_output_filename=current.last_successful_output_filename,
            updated_at=_now_iso(),
            last_error=error,
        ),
    )


def _key_to_storage(key: TriggerStateKey) -> str:
    return json.dumps([key.note_id, key.rule_id, key.source_field], separators=(",", ":"))


def _key_from_storage(raw: str) -> TriggerStateKey | None:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list) or len(value) != 3:
        return None
    note_id, rule_id, source_field = value
    if isinstance(note_id, bool) or not isinstance(note_id, int):
        return None
    if not isinstance(rule_id, str) or not isinstance(source_field, str):
        return None
    return TriggerStateKey(note_id=note_id, rule_id=rule_id, source_field=source_field)


def _entry_from_raw(raw: object) -> TriggerStateEntry | None:
    if not isinstance(raw, dict):
        return None
    status = raw.get("status")
    if status not in {"idle", "running", "succeeded", "failed"}:
        return None
    return TriggerStateEntry(
        last_handled_field_filename=_optional_str(raw.get("last_handled_field_filename")),
        input_filename=_optional_str(raw.get("input_filename")),
        action_fingerprint=_optional_str(raw.get("action_fingerprint")),
        generation_token=_optional_str(raw.get("generation_token")),
        status=status,
        last_successful_output_filename=_optional_str(raw.get("last_successful_output_filename")),
        updated_at=str(raw.get("updated_at", "")),
        last_error=_optional_str(raw.get("last_error")),
    )


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
