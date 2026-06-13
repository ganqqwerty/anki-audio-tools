# Selected Card Audio Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #29: export all audio references from selected Browser cards as either a zip archive of original clips or one combined MP3 with configurable silence.

**Architecture:** Add a non-mutating Browser audio export workflow beside the existing mutating Browser batch workflow. Keep collection and naming import-safe, keep zip/ffmpeg/filesystem work in UI-adapter runners, reuse generated WebView contracts, and reuse the existing batch Svelte bundle by adding an export surface.

**Tech Stack:** Python 3.13 Anki add-on modules, Svelte 5 + TypeScript Browser WebView bundle, schema-first JSON communication contracts, ffmpeg/ffprobe runtime discovery, pytest, Vitest/Svelte tests, e2e Anki tests.

---

## File Structure

Create:

- `addon/anki_audio_quick_editor/audio_export_types.py`  
  Import-safe dataclasses and constants for export mode, field selections, export items, per-item results, and export reports.

- `addon/anki_audio_quick_editor/audio_export_planning.py`  
  Import-safe planner that maps selected `BatchNoteSnapshot` values and field selections to ordered export items, skip/failure records, and zip entry names.

- `addon/anki_audio_quick_editor/audio_export_rendering.py`  
  Import-safe ffmpeg command builders and rendering helpers for combined MP3 export. This module may run subprocesses through existing audio external helpers and should be covered separately from Browser UI.

- `addon/anki_audio_quick_editor/browser_audio_export_runner.py`  
  UI adapter for background export execution, destination temp promotion, zip writes, ffmpeg rendering calls, cancellation, diagnostics, and progress callbacks.

- `addon/anki_audio_quick_editor/browser_audio_export_dialog.py`  
  UI adapter dialog shell for export commands, using the existing batch bundle and WebView bridge.

- `addon/anki_audio_quick_editor/browser_audio_export_state.py`  
  Import-safe initial-state and request decoding helpers for the export surface.

- `tests/test_audio_export_planning.py`
- `tests/test_audio_export_rendering.py`
- `tests/test_browser_audio_export_state.py`
- `tests/test_browser_audio_export_runner.py`
- `settings_ui/src/batch/BatchExportControls.svelte`
- `settings_ui/src/batch/export-state.ts`
- `settings_ui/tests/batch-export-state.test.ts`
- `settings_ui/tests/batch-export-app.test.ts`
- `e2e/test_browser_audio_export_workflow.py`

Modify:

- `contracts/communication.schema.json`  
  Add export initial state, request, progress, finish, and error payloads.

- `settings_ui/src/lib/types.ts`  
  Re-export generated export types/enums after contract generation.

- `settings_ui/src/batch/bridge.ts`  
  Add export bridge commands and callbacks while preserving existing batch commands.

- `settings_ui/src/batch/BatchApp.svelte`  
  Render either the existing batch operation surface or the new export surface based on initial state.

- `settings_ui/src/batch/batch-state.ts`  
  Add `surface` support to fallback initial state without changing existing batch operation behavior.

- `addon/anki_audio_quick_editor/browser_integration.py`  
  Add `Export Audio...` action and dialog creation path next to the existing batch action.

- `addon/anki_audio_quick_editor/locales/en.json` and other locale files if tests require complete key coverage. At minimum add English keys; non-English catalogs fall back to English through `i18n.py`.

- `tests/test_architecture/contract_audio.py`
- `tests/test_architecture/contract_ui.py`
- `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`
- `tests/test_architecture/test_rule19_shared_operation_contracts.py`

Do not modify generated files directly:

- `addon/anki_audio_quick_editor/contracts_generated.py`
- `settings_ui/src/lib/generated/contracts.ts`
- `addon/anki_audio_quick_editor/templates/batch/batch_bundle.*`

Regenerate those with repo commands when the relevant tasks say to.

---

## Task 1: Add Export Contracts

**Files:**

- Modify: `contracts/communication.schema.json`
- Modify: `settings_ui/src/lib/types.ts`
- Modify: `addon/anki_audio_quick_editor/browser_dialog_state.py`
- Modify: `settings_ui/src/batch/batch-state.ts`
- Modify: `tests/test_browser_dialog_state.py`
- Test: generated contract check via `python3 scripts/dev.py contracts-generate` and `python3 scripts/dev.py contracts-check`

- [ ] **Step 1: Add failing schema expectations through contract generation**

Run:

```bash
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py contracts-check
```

Expected before schema edits: generated files do not contain `AudioExportStartRequest`, `AudioExportInitialState`, or `AudioExportMode`.

- [ ] **Step 2: Extend `contracts/communication.schema.json` top-level properties**

Add these properties beside the existing batch properties:

```json
"audioExportInitialState": { "$ref": "#/definitions/AudioExportInitialState" },
"audioExportStartRequest": { "$ref": "#/definitions/AudioExportStartRequest" },
"audioExportDestinationRequest": { "$ref": "#/definitions/AudioExportDestinationRequest" },
"audioExportDestinationPayload": { "$ref": "#/definitions/AudioExportDestinationPayload" },
"audioExportProgressPayload": { "$ref": "#/definitions/AudioExportProgressPayload" },
"audioExportFinishPayload": { "$ref": "#/definitions/AudioExportFinishPayload" },
"audioExportErrorPayload": { "$ref": "#/definitions/BatchErrorPayload" }
```

- [ ] **Step 3: Add schema definitions**

Add these definitions near the existing batch definitions:

```json
"BatchSurface": {
  "enum": ["operations", "audio_export"]
},
"AudioExportMode": {
  "enum": ["zip", "combined_mp3"]
},
"AudioExportFieldSelection": {
  "type": "object",
  "additionalProperties": false,
  "required": ["notetype_name", "fields"],
  "properties": {
    "notetype_name": { "type": "string" },
    "fields": { "type": "array", "items": { "type": "string" } }
  }
},
"AudioExportDefaults": {
  "type": "object",
  "additionalProperties": false,
  "required": ["mode", "silence_between_clips_seconds"],
  "properties": {
    "mode": { "$ref": "#/definitions/AudioExportMode" },
    "silence_between_clips_seconds": { "type": "number", "minimum": 0, "maximum": 10 }
  }
},
"AudioExportInitialState": {
  "type": "object",
  "additionalProperties": false,
  "required": [
    "surface",
    "note_count",
    "field_groups",
    "default_field_selections",
    "defaults",
    "locale",
    "direction",
    "messages"
  ],
  "properties": {
    "surface": { "enum": ["audio_export"] },
    "note_count": { "type": "integer" },
    "field_groups": { "type": "array", "items": { "$ref": "#/definitions/BatchFieldGroup" } },
    "default_field_selections": {
      "type": "array",
      "items": { "$ref": "#/definitions/AudioExportFieldSelection" }
    },
    "defaults": { "$ref": "#/definitions/AudioExportDefaults" },
    "locale": { "type": "string" },
    "direction": { "enum": ["ltr", "rtl"] },
    "messages": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    }
  }
},
"AudioExportDestinationRequest": {
  "type": "object",
  "additionalProperties": false,
  "required": ["mode"],
  "properties": {
    "mode": { "$ref": "#/definitions/AudioExportMode" }
  }
},
"AudioExportDestinationPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["destination_path"],
  "properties": {
    "destination_path": { "type": "string" }
  }
},
"AudioExportStartRequest": {
  "type": "object",
  "additionalProperties": false,
  "required": [
    "mode",
    "destination_path",
    "field_selections",
    "silence_between_clips_seconds"
  ],
  "properties": {
    "mode": { "$ref": "#/definitions/AudioExportMode" },
    "destination_path": { "type": "string" },
    "field_selections": {
      "type": "array",
      "items": { "$ref": "#/definitions/AudioExportFieldSelection" }
    },
    "silence_between_clips_seconds": { "type": "number", "minimum": 0, "maximum": 10 }
  }
},
"AudioExportProgressPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["processed", "total", "current_audio", "failures", "message"],
  "properties": {
    "processed": { "type": "integer" },
    "total": { "type": "integer" },
    "current_audio": { "type": "string" },
    "failures": { "type": "integer" },
    "message": { "type": "string" }
  }
},
"AudioExportFinishPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": [
    "processed",
    "total",
    "exported",
    "skipped",
    "failures",
    "canceled",
    "output_path",
    "summary"
  ],
  "properties": {
    "processed": { "type": "integer" },
    "total": { "type": "integer" },
    "exported": { "type": "integer" },
    "skipped": { "type": "integer" },
    "failures": { "type": "integer" },
    "canceled": { "type": "boolean" },
    "output_path": { "type": "string" },
    "summary": { "type": "string" }
  }
}
```

Also add `"surface": { "$ref": "#/definitions/BatchSurface" }` to `BatchInitialState`, include `"surface"` in its required list, and set the operations initial state to `"operations"` in Python and frontend fallbacks.

- [ ] **Step 4: Update existing batch initial states**

Modify `addon/anki_audio_quick_editor/browser_dialog_state.py` in `build_batch_initial_state()`:

```python
    return {
        "surface": "operations",
        "note_count": note_count,
        "operations": [_operation_option(operation, messages) for operation in BATCH_OPERATIONS],
        ...
    }
```

Modify `tests/test_browser_dialog_state.py` in `test_build_batch_initial_state_contains_operations_fields_defaults_and_i18n()`:

```python
    assert state["surface"] == "operations"
```

Modify `settings_ui/src/batch/batch-state.ts` imports:

```typescript
  BatchSurface,
```

Set the fallback surface:

```typescript
export const FALLBACK_BATCH_INITIAL_STATE: BatchInitialState = {
  surface: BatchSurface.Operations,
  note_count: 0,
  operations: [
```

- [ ] **Step 5: Regenerate contracts**

Run:

```bash
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py contracts-check
```

Expected: both commands pass and generated Python/TypeScript contracts include `AudioExportStartRequest`, `AudioExportMode`, `AudioExportInitialState`, and `BatchSurface`.

- [ ] **Step 6: Re-export export types in `settings_ui/src/lib/types.ts`**

Add these to the type export block:

```typescript
  AudioExportDestinationPayload,
  AudioExportDestinationRequest,
  AudioExportFieldSelection,
  AudioExportFinishPayload,
  AudioExportInitialState,
  AudioExportProgressPayload,
  AudioExportStartRequest,
```

Add these to the value export block:

```typescript
  AudioExportMode,
  BatchSurface,
```

- [ ] **Step 7: Run focused validation**

Run:

```bash
python3 scripts/dev.py contracts-check
python3 scripts/dev.py typecheck
python3 -m pytest tests/test_browser_dialog_state.py -q
```

Expected: all commands pass.

- [ ] **Step 8: Commit**

```bash
git add contracts/communication.schema.json addon/anki_audio_quick_editor/contracts_generated.py settings_ui/src/lib/generated/contracts.ts settings_ui/src/lib/types.ts addon/anki_audio_quick_editor/browser_dialog_state.py settings_ui/src/batch/batch-state.ts tests/test_browser_dialog_state.py
git commit -m "Define audio export bridge contracts" -m "The export workflow needs schema-owned payloads before Python and Svelte can communicate safely. This adds typed requests and callbacks so later tasks do not create ad hoc bridge shapes."
```

---

## Task 2: Add Import-Safe Export Types And Planning

**Files:**

- Create: `addon/anki_audio_quick_editor/audio_export_types.py`
- Create: `addon/anki_audio_quick_editor/audio_export_planning.py`
- Create: `tests/test_audio_export_planning.py`
- Modify: `tests/test_architecture/contract_audio.py`

- [ ] **Step 1: Write failing planner tests**

Create `tests/test_audio_export_planning.py`:

```python
from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_planning import (
    collect_audio_export_items,
    default_audio_field_selections,
    make_zip_entry_name,
)
from anki_audio_quick_editor.audio_export_types import AudioExportFieldSelection
from anki_audio_quick_editor.batch_operations import BatchNoteSnapshot


def test_default_audio_field_selections_choose_fields_with_supported_sound_refs() -> None:
    notes = [
        BatchNoteSnapshot(1, "Basic", {"Front": "[sound:front.mp3]", "Back": "text"}),
        BatchNoteSnapshot(2, "Basic", {"Front": "text", "Back": "[sound:back.wav]"}),
        BatchNoteSnapshot(3, "Cloze", {"Text": "[sound:movie.mp4]", "Audio": "[sound:ok.m4a]"}),
    ]

    assert default_audio_field_selections(notes) == (
        AudioExportFieldSelection("Basic", ("Front", "Back")),
        AudioExportFieldSelection("Cloze", ("Audio",)),
    )


def test_collect_audio_export_items_includes_all_sound_refs_in_selected_order(tmp_path: Path) -> None:
    for filename in ("a.mp3", "b.wav", "c.m4a"):
        (tmp_path / filename).write_bytes(b"audio")
    notes = [
        BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] x [sound:b.wav]", "Back": "[sound:c.m4a]"}),
    ]

    plan = collect_audio_export_items(
        notes,
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
    )

    assert [(item.sequence, item.note_id, item.field_name, item.field_sound_index, item.original_filename) for item in plan.items] == [
        (1, 10, "Front", 1, "a.mp3"),
        (2, 10, "Front", 2, "b.wav"),
        (3, 10, "Back", 1, "c.m4a"),
    ]
    assert plan.skipped == []
    assert plan.failures == []


def test_collect_audio_export_items_reports_skips_and_missing_media(tmp_path: Path) -> None:
    notes = [
        BatchNoteSnapshot(10, "Basic", {"Front": "no audio", "Audio": "[sound:missing.mp3]"}),
        BatchNoteSnapshot(11, "Other", {"Audio": "[sound:ignored.mp3]"}),
    ]

    plan = collect_audio_export_items(
        notes,
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Audio", "Missing")),),
    )

    assert plan.items == ()
    assert [entry.message for entry in plan.skipped] == [
        "field 'Front' has no supported sound reference",
        "missing selected field 'Missing'",
    ]
    assert len(plan.failures) == 1
    assert plan.failures[0].message == "media file not found: missing.mp3"


def test_make_zip_entry_name_is_ordered_sanitized_and_collision_safe(tmp_path: Path) -> None:
    (tmp_path / "bad name.mp3").write_bytes(b"audio")
    note = BatchNoteSnapshot(42, "Basic", {"A/B": "[sound:bad name.mp3]"})
    plan = collect_audio_export_items(
        [note],
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("A/B",)),),
    )
    item = plan.items[0]

    assert make_zip_entry_name(item, used_names=set()) == "0001__note-42__A_B__001__bad_name.mp3"
    assert make_zip_entry_name(item, used_names={"0001__note-42__A_B__001__bad_name.mp3"}) == (
        "0001__note-42__A_B__001__bad_name__2.mp3"
    )
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_audio_export_planning.py -q
```

Expected: fails with `ModuleNotFoundError` for `audio_export_planning` or `audio_export_types`.

- [ ] **Step 3: Implement `audio_export_types.py`**

Create:

```python
"""Import-safe data structures for Browser audio export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

AudioExportMode = Literal["zip", "combined_mp3"]

EXPORT_MODE_ZIP: AudioExportMode = "zip"
EXPORT_MODE_COMBINED_MP3: AudioExportMode = "combined_mp3"
MAX_SILENCE_BETWEEN_CLIPS_SECONDS = 10.0


@dataclass(frozen=True)
class AudioExportFieldSelection:
    notetype_name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class AudioExportRequest:
    mode: AudioExportMode
    destination_path: Path
    field_selections: tuple[AudioExportFieldSelection, ...]
    silence_between_clips_seconds: float = 1.0


@dataclass(frozen=True)
class AudioExportItem:
    sequence: int
    note_id: int
    notetype_name: str
    field_name: str
    field_sound_index: int
    original_filename: str
    source_path: Path


@dataclass(frozen=True)
class AudioExportNotice:
    note_id: int
    notetype_name: str
    field_name: str
    message: str
    filename: str | None = None


@dataclass(frozen=True)
class AudioExportPlan:
    items: tuple[AudioExportItem, ...]
    skipped: tuple[AudioExportNotice, ...] = ()
    failures: tuple[AudioExportNotice, ...] = ()


@dataclass
class AudioExportReport:
    total: int
    processed: int = 0
    exported: int = 0
    skipped: int = 0
    failures: int = 0
    canceled: bool = False
    output_path: str = ""
    log_lines: list[str] = field(default_factory=list)
    messages: dict[str, str] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        if self.canceled:
            return (
                f"Audio export canceled after {self.processed}/{self.total} files. "
                f"Exported: {self.exported}. Skipped: {self.skipped}. Failures: {self.failures}."
            )
        return (
            f"Audio export completed. Exported: {self.exported}. "
            f"Skipped: {self.skipped}. Failures: {self.failures}. Output: {self.output_path}"
        )
```

- [ ] **Step 4: Implement `audio_export_planning.py`**

Create:

```python
"""Import-safe planning for selected-card audio export."""

from __future__ import annotations

import re
from pathlib import Path

from .audio_export_types import (
    AudioExportFieldSelection,
    AudioExportItem,
    AudioExportNotice,
    AudioExportPlan,
)
from .batch_operations import BatchNoteSnapshot
from .media_paths import existing_media_file_path
from .sound_refs import find_sound_references, safe_media_basename

_UNSAFE_ENTRY_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")
_SUPPORTED_AUDIO_EXTENSIONS = frozenset({".mp3", ".m4a", ".wav", ".flac"})


def default_audio_field_selections(
    notes: list[BatchNoteSnapshot] | tuple[BatchNoteSnapshot, ...],
) -> tuple[AudioExportFieldSelection, ...]:
    grouped: dict[str, list[str]] = {}
    for note in notes:
        fields = grouped.setdefault(note.notetype_name, [])
        for field_name, html in note.fields.items():
            if field_name in fields:
                continue
            if any(_is_supported_audio_filename(ref.filename) for ref in find_sound_references(html)):
                fields.append(field_name)
    return tuple(
        AudioExportFieldSelection(notetype_name, tuple(fields))
        for notetype_name, fields in sorted(grouped.items(), key=lambda item: item[0].casefold())
        if fields
    )


def collect_audio_export_items(
    notes: list[BatchNoteSnapshot] | tuple[BatchNoteSnapshot, ...],
    *,
    media_dir: Path,
    field_selections: tuple[AudioExportFieldSelection, ...],
) -> AudioExportPlan:
    selected = {selection.notetype_name: selection.fields for selection in field_selections}
    items: list[AudioExportItem] = []
    skipped: list[AudioExportNotice] = []
    failures: list[AudioExportNotice] = []
    sequence = 1
    for note in notes:
        selected_fields = selected.get(note.notetype_name)
        if selected_fields is None:
            continue
        for field_name in selected_fields:
            if field_name not in note.fields:
                skipped.append(_notice(note, field_name, f"missing selected field {field_name!r}"))
                continue
            refs = tuple(ref for ref in find_sound_references(note.fields[field_name]) if _is_supported_audio_filename(ref.filename))
            if not refs:
                skipped.append(_notice(note, field_name, f"field {field_name!r} has no supported sound reference"))
                continue
            for index, ref in enumerate(refs, start=1):
                filename = safe_media_basename(ref.filename)
                source_path = existing_media_file_path(media_dir, filename)
                if source_path is None:
                    failures.append(_notice(note, field_name, f"media file not found: {filename}", filename))
                    continue
                items.append(
                    AudioExportItem(
                        sequence=sequence,
                        note_id=note.note_id,
                        notetype_name=note.notetype_name,
                        field_name=field_name,
                        field_sound_index=index,
                        original_filename=filename,
                        source_path=source_path,
                    )
                )
                sequence += 1
    return AudioExportPlan(items=tuple(items), skipped=tuple(skipped), failures=tuple(failures))


def make_zip_entry_name(item: AudioExportItem, *, used_names: set[str]) -> str:
    stem = _safe_zip_fragment(Path(item.original_filename).stem) or "audio"
    suffix = Path(item.original_filename).suffix.lower()
    base = (
        f"{item.sequence:04d}__note-{item.note_id}__"
        f"{_safe_zip_fragment(item.field_name)}__{item.field_sound_index:03d}__{stem}"
    )
    candidate = f"{base}{suffix}"
    counter = 2
    while candidate in used_names:
        candidate = f"{base}__{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _notice(
    note: BatchNoteSnapshot,
    field_name: str,
    message: str,
    filename: str | None = None,
) -> AudioExportNotice:
    return AudioExportNotice(
        note_id=note.note_id,
        notetype_name=note.notetype_name,
        field_name=field_name,
        message=message,
        filename=filename,
    )


def _is_supported_audio_filename(filename: str) -> bool:
    return Path(filename.rstrip(" .")).suffix.lower() in _SUPPORTED_AUDIO_EXTENSIONS


def _safe_zip_fragment(value: str) -> str:
    sanitized = _UNSAFE_ENTRY_CHARS_RE.sub("_", value.strip()).strip("._")
    return sanitized or "field"
```

- [ ] **Step 5: Add architecture contracts**

Modify `tests/test_architecture/contract_audio.py`:

```python
    "audio_export_types": contract(
        "audio_export_types",
        layer=Layer.IMPORT_SAFE_CORE,
    ),
    "audio_export_planning": contract(
        "audio_export_planning",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_export_types",
            "batch_operations",
            "media_paths",
            "sound_refs",
        ),
    ),
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_audio_export_planning.py -q
python3 scripts/dev.py arch
```

Expected: export planning tests pass and architecture contracts pass.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_export_types.py addon/anki_audio_quick_editor/audio_export_planning.py tests/test_audio_export_planning.py tests/test_architecture/contract_audio.py
git commit -m "Plan selected audio export items" -m "The export workflow needs a non-mutating core that can be tested without Anki UI objects. This adds ordered all-reference collection and stable zip naming before adding filesystem side effects."
```

---

## Task 3: Add Combined MP3 Rendering Helpers

**Files:**

- Create: `addon/anki_audio_quick_editor/audio_export_rendering.py`
- Create: `tests/test_audio_export_rendering.py`
- Modify: `tests/test_architecture/contract_audio.py`

- [ ] **Step 1: Write failing rendering tests**

Create `tests/test_audio_export_rendering.py`:

```python
from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_rendering import (
    build_concat_list_text,
    build_final_mp3_command,
    build_normalize_wav_command,
    build_silence_wav_command,
)


def test_build_normalize_wav_command_uses_stable_pcm_output() -> None:
    command = build_normalize_wav_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        source_path=Path("/media/source.mp3"),
        output_path=Path("/tmp/0001.wav"),
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        "/media/source.mp3",
        "-vn",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        "/tmp/0001.wav",
    )


def test_build_silence_wav_command_uses_anullsrc_duration() -> None:
    command = build_silence_wav_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        duration_seconds=1.25,
        output_path=Path("/tmp/silence.wav"),
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        "1.250",
        "-c:a",
        "pcm_s16le",
        "/tmp/silence.wav",
    )


def test_build_concat_list_text_escapes_single_quotes() -> None:
    text = build_concat_list_text([Path("/tmp/a.wav"), Path("/tmp/has'quote.wav")])

    assert text == "file '/tmp/a.wav'\\nfile '/tmp/has'\\\\''quote.wav'\\n"


def test_build_final_mp3_command_uses_concat_demuxer_and_mp3_codec() -> None:
    command = build_final_mp3_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        concat_list_path=Path("/tmp/list.txt"),
        output_path=Path("/tmp/out.mp3"),
    )

    assert command[:7] == (
        "/bin/ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
    )
    assert command[7] == "/tmp/list.txt"
    assert command[-1] == "/tmp/out.mp3"
    assert "-vn" in command
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_audio_export_rendering.py -q
```

Expected: fails with `ModuleNotFoundError`.

- [ ] **Step 3: Implement command builders**

Create `addon/anki_audio_quick_editor/audio_export_rendering.py`:

```python
"""ffmpeg helpers for combined selected-card audio export."""

from __future__ import annotations

from pathlib import Path

from .audio_commands import conversion_codec_args

EXPORT_SAMPLE_RATE_HZ = 44100
EXPORT_CHANNELS = 2


def build_normalize_wav_command(
    *,
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ar",
        str(EXPORT_SAMPLE_RATE_HZ),
        "-ac",
        str(EXPORT_CHANNELS),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    )


def build_silence_wav_command(
    *,
    ffmpeg_path: Path,
    duration_seconds: float,
    output_path: Path,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={EXPORT_SAMPLE_RATE_HZ}:cl=stereo",
        "-t",
        f"{duration_seconds:.3f}",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    )


def build_concat_list_text(paths: list[Path] | tuple[Path, ...]) -> str:
    return "".join(f"file '{_concat_escape(path)}'\\n" for path in paths)


def build_final_mp3_command(
    *,
    ffmpeg_path: Path,
    concat_list_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list_path),
        "-vn",
        *conversion_codec_args("mp3"),
        str(output_path),
    )


def _concat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\\\''")
```

- [ ] **Step 4: Add architecture contract**

Modify `tests/test_architecture/contract_audio.py`:

```python
    "audio_export_rendering": contract(
        "audio_export_rendering",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_commands",),
    ),
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_audio_export_rendering.py -q
python3 scripts/dev.py arch
```

Expected: both pass.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_export_rendering.py tests/test_audio_export_rendering.py tests/test_architecture/contract_audio.py
git commit -m "Build combined audio export commands" -m "Combined MP3 export needs predictable ffmpeg commands before it is wired into Browser UI. The helpers normalize diverse source clips, insert optional silence, and encode through the existing MP3 codec policy."
```

---

## Task 4: Add Export State Decoding And Payload Helpers

**Files:**

- Create: `addon/anki_audio_quick_editor/browser_audio_export_state.py`
- Create: `tests/test_browser_audio_export_state.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `tests/test_architecture/contract_ui.py`

- [ ] **Step 1: Write failing state tests**

Create `tests/test_browser_audio_export_state.py`:

```python
from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_types import AudioExportFieldSelection
from anki_audio_quick_editor.batch_operations import BatchNoteSnapshot, FieldGroup
from anki_audio_quick_editor.browser_audio_export_state import (
    audio_export_finish_payload,
    audio_export_progress_payload,
    build_audio_export_initial_state,
    request_from_audio_export_start_payload,
)


def test_build_audio_export_initial_state_contains_defaults_and_audio_fields() -> None:
    state = build_audio_export_initial_state(
        note_count=2,
        groups=(FieldGroup("Basic", ("Front", "Back")),),
        snapshots=(
            BatchNoteSnapshot(1, "Basic", {"Front": "[sound:a.mp3]", "Back": ""}),
            BatchNoteSnapshot(2, "Basic", {"Front": "", "Back": "[sound:b.wav]"}),
        ),
    )

    assert state["surface"] == "audio_export"
    assert state["note_count"] == 2
    assert state["field_groups"] == [{"notetype_name": "Basic", "fields": ["Front", "Back"]}]
    assert state["default_field_selections"] == [{"notetype_name": "Basic", "fields": ["Front", "Back"]}]
    assert state["defaults"] == {"mode": "zip", "silence_between_clips_seconds": 1.0}
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "audio_export.window_title" in state["messages"]


def test_request_from_audio_export_start_payload_validates_and_decodes() -> None:
    request = request_from_audio_export_start_payload(
        {
            "mode": "combined_mp3",
            "destination_path": "/tmp/export.mp3",
            "field_selections": [{"notetype_name": "Basic", "fields": ["Front", "Back"]}],
            "silence_between_clips_seconds": 1.5,
        }
    )

    assert request.mode == "combined_mp3"
    assert request.destination_path == Path("/tmp/export.mp3")
    assert request.field_selections == (AudioExportFieldSelection("Basic", ("Front", "Back")),)
    assert request.silence_between_clips_seconds == 1.5


def test_request_from_audio_export_start_payload_rejects_bad_silence() -> None:
    try:
        request_from_audio_export_start_payload(
            {
                "mode": "combined_mp3",
                "destination_path": "/tmp/export.mp3",
                "field_selections": [{"notetype_name": "Basic", "fields": ["Front"]}],
                "silence_between_clips_seconds": 11,
            }
        )
    except ValueError as exc:
        assert str(exc) == "Silence between clips must be between 0 and 10 seconds."
    else:
        raise AssertionError("expected invalid silence to fail")


def test_export_progress_and_finish_payloads() -> None:
    progress = audio_export_progress_payload(
        processed=1,
        total=3,
        current_audio="clip.mp3",
        failures=0,
        message="Exported 1/3 audio files. Current audio: clip.mp3. Failures: 0.",
    )
    finish = audio_export_finish_payload(
        processed=3,
        total=3,
        exported=3,
        skipped=1,
        failures=0,
        canceled=False,
        output_path="/tmp/export.zip",
        summary="Audio export completed.",
    )

    assert progress["current_audio"] == "clip.mp3"
    assert finish["exported"] == 3
    assert finish["output_path"] == "/tmp/export.zip"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_state.py -q
```

Expected: fails with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `browser_audio_export_state.py`**

Create:

```python
"""Initial state and contract decoding for Browser audio export."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .audio_export_planning import default_audio_field_selections
from .audio_export_types import (
    EXPORT_MODE_ZIP,
    MAX_SILENCE_BETWEEN_CLIPS_SECONDS,
    AudioExportFieldSelection,
    AudioExportRequest,
)
from .batch_operations import BatchNoteSnapshot, FieldGroup
from .contracts_generated import AudioExportStartRequest
from .i18n import active_context


def build_audio_export_initial_state(
    *,
    note_count: int,
    groups: tuple[FieldGroup, ...],
    snapshots: tuple[BatchNoteSnapshot, ...],
) -> dict[str, Any]:
    i18n = active_context()
    return {
        "surface": "audio_export",
        "note_count": note_count,
        "field_groups": [
            {"notetype_name": group.notetype_name, "fields": list(group.fields)}
            for group in groups
        ],
        "default_field_selections": [
            {"notetype_name": selection.notetype_name, "fields": list(selection.fields)}
            for selection in default_audio_field_selections(snapshots)
        ],
        "defaults": {
            "mode": EXPORT_MODE_ZIP,
            "silence_between_clips_seconds": 1.0,
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": dict(i18n["messages"]),
    }


def request_from_audio_export_start_payload(raw_payload: object) -> AudioExportRequest:
    payload = AudioExportStartRequest.from_dict(raw_payload).to_dict()
    mode = str(payload.get("mode") or "")
    destination = Path(str(payload.get("destination_path") or ""))
    selections = _field_selections(payload.get("field_selections") or [])
    silence = float(payload.get("silence_between_clips_seconds"))
    if mode not in {"zip", "combined_mp3"}:
        raise ValueError("Choose an export mode before starting.")
    if str(destination) == "." or not str(destination):
        raise ValueError("Choose a destination before starting.")
    if not selections or not any(selection.fields for selection in selections):
        raise ValueError("Choose at least one field before starting.")
    if not math.isfinite(silence) or silence < 0 or silence > MAX_SILENCE_BETWEEN_CLIPS_SECONDS:
        raise ValueError("Silence between clips must be between 0 and 10 seconds.")
    return AudioExportRequest(
        mode=mode,  # type: ignore[arg-type]
        destination_path=destination,
        field_selections=selections,
        silence_between_clips_seconds=silence,
    )


def audio_export_progress_payload(
    *,
    processed: int,
    total: int,
    current_audio: str,
    failures: int,
    message: str,
) -> dict[str, Any]:
    return {
        "processed": processed,
        "total": total,
        "current_audio": current_audio,
        "failures": failures,
        "message": message,
    }


def audio_export_finish_payload(
    *,
    processed: int,
    total: int,
    exported: int,
    skipped: int,
    failures: int,
    canceled: bool,
    output_path: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "processed": processed,
        "total": total,
        "exported": exported,
        "skipped": skipped,
        "failures": failures,
        "canceled": canceled,
        "output_path": output_path,
        "summary": summary,
    }


def _field_selections(raw: object) -> tuple[AudioExportFieldSelection, ...]:
    selections: list[AudioExportFieldSelection] = []
    if not isinstance(raw, list):
        return ()
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        fields = entry.get("fields") or []
        if not isinstance(fields, list):
            fields = []
        selections.append(
            AudioExportFieldSelection(
                notetype_name=str(entry.get("notetype_name") or ""),
                fields=tuple(str(field) for field in fields if str(field)),
            )
        )
    return tuple(selection for selection in selections if selection.notetype_name)
```

- [ ] **Step 4: Add English messages**

Add to `addon/anki_audio_quick_editor/locales/en.json`:

```json
"audio_export.action": "Export Audio...",
"audio_export.window_title": "Export Audio",
"audio_export.instructions": "Choose fields and an export destination.",
"audio_export.choose_destination": "Choose...",
"audio_export.start": "Export",
"audio_export.cancel": "Cancel",
"audio_export.cancel_requested": "Cancel requested. The current file may finish first.",
"audio_export.mode.zip": "Zip archive",
"audio_export.mode.combined_mp3": "Combined MP3",
"audio_export.destination": "Destination",
"audio_export.fields": "Fields",
"audio_export.silence_between_clips": "Silence between clips",
"audio_export.no_audio": "No audio",
"audio_export.starting": "Starting audio export.",
"audio_export.progress": "Exported {processed}/{total} audio files. Current audio: {audio}. Failures: {failures}.",
"audio_export.completed": "Audio export completed. Exported: {exported}. Skipped: {skipped}. Failures: {failures}. Output: {output}.",
"audio_export.canceled": "Audio export canceled after {processed}/{total} audio files. Exported: {exported}. Skipped: {skipped}. Failures: {failures}.",
"audio_export.failed": "Audio export failed: {error}"
```

- [ ] **Step 5: Add architecture contract**

Modify `tests/test_architecture/contract_ui.py`:

```python
    "browser_audio_export_state": contract(
        "browser_audio_export_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_export_planning",
            "audio_export_types",
            "batch_operations",
            "contracts_generated",
            "i18n",
        ),
    ),
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_state.py -q
python3 scripts/dev.py contracts-check
python3 scripts/dev.py arch
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_audio_export_state.py tests/test_browser_audio_export_state.py addon/anki_audio_quick_editor/locales/en.json tests/test_architecture/contract_ui.py
git commit -m "Decode browser audio export state" -m "The export dialog needs validated initial state and start requests before UI wiring. This keeps field defaults, silence limits, and callback payloads schema-backed and import-safe."
```

---

## Task 5: Implement Export Runner Side Effects

**Files:**

- Create: `addon/anki_audio_quick_editor/browser_audio_export_runner.py`
- Create: `tests/test_browser_audio_export_runner.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`

- [ ] **Step 1: Write failing runner tests**

Create `tests/test_browser_audio_export_runner.py`:

```python
from __future__ import annotations

import threading
import zipfile
from pathlib import Path

from anki_audio_quick_editor.audio_export_types import (
    EXPORT_MODE_ZIP,
    AudioExportFieldSelection,
    AudioExportRequest,
)
from anki_audio_quick_editor.batch_operations import BatchNoteSnapshot
from anki_audio_quick_editor.browser_audio_export_runner import run_audio_export


def test_run_audio_export_writes_zip_without_mutating_notes(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    (media / "b.wav").write_bytes(b"b")
    output = tmp_path / "out.zip"
    snapshots = (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.wav]"}),)
    logs: list[str] = []
    progress: list[tuple[int, int, str, int]] = []

    report = run_audio_export(
        snapshots,
        request=AudioExportRequest(
            mode=EXPORT_MODE_ZIP,
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
        ),
        media_dir=media,
        cancel_event=threading.Event(),
        on_log=logs.append,
        on_progress=lambda *args: progress.append(args),  # type: ignore[arg-type]
    )

    assert report.exported == 2
    assert report.failures == 0
    assert output.is_file()
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == [
            "0001__note-10__Front__001__a.mp3",
            "0002__note-10__Front__002__b.wav",
        ]
        assert archive.read("0001__note-10__Front__001__a.mp3") == b"a"
    assert progress[-1] == (2, 2, "b.wav", 0)
    assert any("Audio export completed" in line for line in logs)


def test_run_audio_export_does_not_promote_when_no_items(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    output = tmp_path / "out.zip"
    report = run_audio_export(
        (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:missing.mp3]"}),),
        request=AudioExportRequest(
            mode=EXPORT_MODE_ZIP,
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
        ),
        media_dir=media,
        cancel_event=threading.Event(),
        on_log=lambda _line: None,
        on_progress=lambda *_args: None,
    )

    assert report.exported == 0
    assert report.failures == 1
    assert not output.exists()


def test_run_audio_export_cancel_removes_temporary_zip(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    (media / "b.mp3").write_bytes(b"b")
    output = tmp_path / "out.zip"
    cancel_event = threading.Event()

    def on_progress(processed: int, *_args) -> None:
        if processed == 1:
            cancel_event.set()

    report = run_audio_export(
        (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.mp3]"}),),
        request=AudioExportRequest(
            mode=EXPORT_MODE_ZIP,
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
        ),
        media_dir=media,
        cancel_event=cancel_event,
        on_log=lambda _line: None,
        on_progress=on_progress,
    )

    assert report.canceled is True
    assert not output.exists()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_runner.py -q
```

Expected: fails with `ModuleNotFoundError`.

- [ ] **Step 3: Implement zip runner first**

Create `addon/anki_audio_quick_editor/browser_audio_export_runner.py`:

```python
"""Background runner for non-mutating Browser audio export."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Any, Callable

from .audio_export_planning import collect_audio_export_items, make_zip_entry_name
from .audio_export_types import (
    EXPORT_MODE_ZIP,
    AudioExportReport,
    AudioExportRequest,
)
from .batch_operations import BatchNoteSnapshot
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)


def run_audio_export(
    snapshots: tuple[BatchNoteSnapshot, ...],
    *,
    request: AudioExportRequest,
    media_dir: Path,
    cancel_event: threading.Event,
    on_log: Callable[[str], None],
    on_progress: Callable[[int, int, str, int], None],
) -> AudioExportReport:
    messages = dict(active_context()["messages"])
    plan = collect_audio_export_items(
        snapshots,
        media_dir=media_dir,
        field_selections=request.field_selections,
    )
    report = AudioExportReport(
        total=len(plan.items),
        skipped=len(plan.skipped),
        failures=len(plan.failures),
        output_path=str(request.destination_path),
        messages=messages,
    )
    _log(report, on_log, f"Starting audio export: {len(plan.items)} files -> {request.destination_path}")
    for notice in plan.skipped:
        _log(report, on_log, f"SKIP note {notice.note_id}: {notice.message}")
    for notice in plan.failures:
        _log(report, on_log, f"FAIL note {notice.note_id}: {notice.message}")
    if not plan.items:
        _log(report, on_log, report.summary)
        return report
    if request.mode == EXPORT_MODE_ZIP:
        _write_zip_export(plan.items, request.destination_path, cancel_event, report, on_log, on_progress)
    else:
        raise ValueError(f"Unsupported export mode: {request.mode}")
    _log(report, on_log, report.summary)
    return report


def _write_zip_export(
    items,
    destination_path: Path,
    cancel_event: threading.Event,
    report: AudioExportReport,
    on_log: Callable[[str], None],
    on_progress: Callable[[int, int, str, int], None],
) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=str(destination_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    used_names: set[str] = set()
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in items:
                if cancel_event.is_set():
                    report.canceled = True
                    break
                entry_name = make_zip_entry_name(item, used_names=used_names)
                archive.write(item.source_path, entry_name)
                report.processed += 1
                report.exported += 1
                on_progress(report.processed, report.total, item.original_filename, report.failures)
                _log(report, on_log, f"WROTE {entry_name}")
        if report.canceled:
            temp_path.unlink(missing_ok=True)
            return
        shutil.move(str(temp_path), str(destination_path))
    finally:
        temp_path.unlink(missing_ok=True)


def _log(report: AudioExportReport, on_log: Callable[[str], None], line: str) -> None:
    report.log_lines.append(line)
    on_log(line)
```

- [ ] **Step 4: Add architecture contract**

Modify `tests/test_architecture/contract_ui.py`:

```python
    "browser_audio_export_runner": contract(
        "browser_audio_export_runner",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_export_planning",
            "audio_export_types",
            "batch_operations",
            "i18n",
        ),
        allowed_side_effects=(
            SideEffect.TEMP_FILESYSTEM_CLEANUP,
        ),
    ),
```

- [ ] **Step 5: Update persistence boundary test**

Modify `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`:

```python
ALLOWED_PERSISTENCE_FILES = {
    "browser_batch_runner.py",
    "browser_audio_export_runner.py",
    "editor_processing.py",
    "reviewer_integration.py",
}
```

Keep the assertion that `browser_audio_export_runner.py` does not call `.media.write_data(`, `.update_note(`, or `.merge_undo_entries(`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_runner.py tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py -q
python3 scripts/dev.py arch
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_audio_export_runner.py tests/test_browser_audio_export_runner.py tests/test_architecture/contract_ui.py tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py
git commit -m "Export selected audio as zip" -m "The first executable export path should prove the workflow is non-mutating before adding ffmpeg complexity. This writes ordered original media into an external archive and keeps note/media persistence out of the runner."
```

---

## Task 6: Add Combined MP3 Runner Path

**Files:**

- Modify: `addon/anki_audio_quick_editor/browser_audio_export_runner.py`
- Modify: `addon/anki_audio_quick_editor/audio_export_rendering.py`
- Modify: `tests/test_browser_audio_export_runner.py`
- Modify: `tests/test_architecture/contract_ui.py`

- [ ] **Step 1: Add failing combined-runner test**

Append to `tests/test_browser_audio_export_runner.py`:

```python
def test_run_audio_export_combined_mp3_invokes_render_steps(monkeypatch, tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    (media / "b.wav").write_bytes(b"b")
    output = tmp_path / "out.mp3"
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg", lambda _path="": Path("/bin/ffmpeg"))

    def fake_run(command, *_args, **_kwargs):
        commands.append(tuple(command))
        Path(command[-1]).write_bytes(b"rendered")

    monkeypatch.setattr("anki_audio_quick_editor.browser_audio_export_runner._run_export_command", fake_run)

    report = run_audio_export(
        (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.wav]"}),),
        request=AudioExportRequest(
            mode="combined_mp3",
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            silence_between_clips_seconds=0.5,
        ),
        media_dir=media,
        cancel_event=threading.Event(),
        on_log=lambda _line: None,
        on_progress=lambda *_args: None,
    )

    assert report.exported == 2
    assert output.read_bytes() == b"rendered"
    assert len(commands) == 4
    assert commands[0][0] == "/bin/ffmpeg"
    assert commands[-1][-1].endswith(".mp3")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_runner.py::test_run_audio_export_combined_mp3_invokes_render_steps -q
```

Expected: fails with `ValueError: Unsupported export mode: combined_mp3`.

- [ ] **Step 3: Implement combined mode**

Modify `browser_audio_export_runner.py` imports:

```python
from .audio_export_rendering import (
    build_concat_list_text,
    build_final_mp3_command,
    build_normalize_wav_command,
    build_silence_wav_command,
)
from .audio_external import _run_external_command
from .audio_processor import find_ffmpeg
```

Replace the unsupported-mode branch:

```python
    elif request.mode == EXPORT_MODE_COMBINED_MP3:
        _write_combined_mp3_export(plan.items, request, cancel_event, report, on_log, on_progress)
```

Add helpers:

```python
def _write_combined_mp3_export(
    items,
    request: AudioExportRequest,
    cancel_event: threading.Event,
    report: AudioExportReport,
    on_log: Callable[[str], None],
    on_progress: Callable[[int, int, str, int], None],
) -> None:
    request.destination_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    temp_root = Path(tempfile.mkdtemp(prefix="aqe_audio_export_"))
    temp_output = request.destination_path.with_name(f".{request.destination_path.name}.tmp.mp3")
    try:
        normalized: list[Path] = []
        for item in items:
            if cancel_event.is_set():
                report.canceled = True
                break
            wav_path = temp_root / f"{item.sequence:04d}.wav"
            _run_export_command(
                build_normalize_wav_command(
                    ffmpeg_path=ffmpeg,
                    source_path=item.source_path,
                    output_path=wav_path,
                ),
                "audio export normalization failed",
            )
            normalized.append(wav_path)
            report.processed += 1
            report.exported += 1
            on_progress(report.processed, report.total, item.original_filename, report.failures)
        if report.canceled:
            return
        concat_paths = _concat_paths_with_silence(
            ffmpeg,
            normalized,
            temp_root,
            request.silence_between_clips_seconds,
        )
        concat_list = temp_root / "concat.txt"
        concat_list.write_text(build_concat_list_text(concat_paths), encoding="utf-8")
        _run_export_command(
            build_final_mp3_command(
                ffmpeg_path=ffmpeg,
                concat_list_path=concat_list,
                output_path=temp_output,
            ),
            "audio export concat failed",
        )
        if not cancel_event.is_set():
            shutil.move(str(temp_output), str(request.destination_path))
        else:
            report.canceled = True
    finally:
        temp_output.unlink(missing_ok=True)
        shutil.rmtree(temp_root, ignore_errors=True)


def _concat_paths_with_silence(
    ffmpeg: Path,
    normalized: list[Path],
    temp_root: Path,
    silence_seconds: float,
) -> list[Path]:
    if silence_seconds <= 0 or len(normalized) <= 1:
        return normalized
    silence_path = temp_root / "silence.wav"
    _run_export_command(
        build_silence_wav_command(
            ffmpeg_path=ffmpeg,
            duration_seconds=silence_seconds,
            output_path=silence_path,
        ),
        "audio export silence generation failed",
    )
    concat_paths: list[Path] = []
    for index, path in enumerate(normalized):
        concat_paths.append(path)
        if index < len(normalized) - 1:
            concat_paths.append(silence_path)
    return concat_paths


def _run_export_command(command: tuple[str, ...], launch_error_prefix: str) -> None:
    _run_external_command(command, launch_error_prefix)
```

- [ ] **Step 4: Update architecture contract**

Modify `browser_audio_export_runner` contract in `tests/test_architecture/contract_ui.py` to include deps and side effects:

```python
        allowed_addon_deps=(
            "audio_export_planning",
            "audio_export_rendering",
            "audio_export_types",
            "audio_external",
            "audio_processor",
            "batch_operations",
            "i18n",
        ),
        allowed_side_effects=(
            SideEffect.SUBPROCESS_RUN,
            SideEffect.TEMP_FILESYSTEM_CLEANUP,
        ),
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_audio_export_rendering.py tests/test_browser_audio_export_runner.py -q
python3 scripts/dev.py arch
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_audio_export_runner.py addon/anki_audio_quick_editor/audio_export_rendering.py tests/test_browser_audio_export_runner.py tests/test_architecture/contract_ui.py
git commit -m "Export selected audio as combined MP3" -m "MP3-player export needs one listenable file when users do not want to manage individual clips. This adds the normalized concat path while preserving the non-mutating Browser export boundary."
```

---

## Task 7: Add Export Dialog And Browser Menu Action

**Files:**

- Create: `addon/anki_audio_quick_editor/browser_audio_export_dialog.py`
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Modify: `tests/test_browser_integration_hooks.py`
- Create: `tests/test_browser_audio_export_dialog.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py`

- [ ] **Step 1: Add failing Browser integration test**

Extend `tests/test_browser_integration_hooks.py` with a test mirroring `test_open_batch_dialog_builds_field_groups_from_selected_notes`:

```python
def test_open_audio_export_dialog_builds_field_groups_from_selected_notes(monkeypatch) -> None:
    from anki_audio_quick_editor import browser_integration

    dialog_calls: list[tuple[object, ...]] = []

    class Dialog:
        def exec(self) -> None:
            dialog_calls.append(("exec", ()))  # type: ignore[arg-type]

    def create_export_dialog(
        _browser: object,
        note_ids: list[int],
        groups: tuple[object, ...],
        snapshots: tuple[object, ...],
    ) -> Dialog:
        dialog_calls.append((note_ids, groups, snapshots))
        return Dialog()

    col = SimpleNamespace(get_note=lambda _note_id: FakeNote(int(_note_id)))
    browser = SimpleNamespace(selected_notes=lambda: [2, 1, 2], mw=SimpleNamespace(col=col))
    monkeypatch.setattr(browser_integration, "_create_export_dialog", create_export_dialog)
    browser_integration._open_audio_export_dialog(browser)

    assert dialog_calls[0][0] == [2, 1]
    groups = dialog_calls[0][1]
    assert len(groups) == 1
    assert groups[0].notetype_name == "Basic"
    assert groups[0].fields == ("Audio", "Image")
    snapshots = dialog_calls[0][2]
    assert [snapshot.note_id for snapshot in snapshots] == [2, 1]
    assert dialog_calls[1] == ("exec", ())
```

- [ ] **Step 2: Add failing dialog command tests**

Create `tests/test_browser_audio_export_dialog.py`:

```python
from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.browser_audio_export_dialog import AudioExportDialog


def test_audio_export_dialog_handles_cancel_when_running() -> None:
    dialog = SimpleNamespace(
        _running=True,
        cancel_event=threading.Event(),
        append_log=MagicMock(),
        tr=lambda key, values=None: key,
    )

    AudioExportDialog._cancel_or_close(dialog)  # type: ignore[arg-type]

    assert dialog.cancel_event.is_set()
    dialog.append_log.assert_called_once_with("audio_export.cancel_requested")
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_browser_integration_hooks.py::test_open_audio_export_dialog_builds_field_groups_from_selected_notes tests/test_browser_audio_export_dialog.py -q
```

Expected: fails because `_open_audio_export_dialog` and `AudioExportDialog` do not exist.

- [ ] **Step 4: Implement `browser_audio_export_dialog.py`**

Create a dialog modeled on `browser_dialog.py`. Use this structure:

```python
"""WebView dialog for non-mutating Browser audio export."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from .batch_operations import BatchNoteSnapshot, FieldGroup
from .browser_audio_export_runner import run_audio_export_in_background
from .browser_audio_export_state import (
    audio_export_finish_payload,
    audio_export_progress_payload,
    build_audio_export_initial_state,
    request_from_audio_export_start_payload,
)
from .error_codes import AQE_BATCH_INVALID_REQUEST, coded_error
from .external_links import open_trusted_external_url_from_payload
from .frontend_logs import handle_frontend_log_payload
from .i18n import active_context, format_message
from .webview_bridge import decode_webview_bridge_command
from .webview_shell import render_webview_content

logger = logging.getLogger(__name__)

_BUNDLE_DIR = Path(__file__).parent / "templates" / "batch"
_BUNDLE_JS = _BUNDLE_DIR / "batch_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "batch_bundle.css"


class AudioExportDialog:
    def __init__(
        self,
        browser: Any,
        note_ids: list[int],
        groups: tuple[FieldGroup, ...],
        snapshots: tuple[BatchNoteSnapshot, ...],
    ) -> None:
        from aqt.qt import QDialog, QVBoxLayout
        from aqt.webview import AnkiWebView

        self.browser = browser
        self.note_ids = note_ids
        self.snapshots = snapshots
        self._i18n = active_context()
        self._messages = dict(self._i18n["messages"])
        self.cancel_event = threading.Event()
        self._running = False
        self._finished = False
        self._log_lines: list[str] = []
        self._dialog = QDialog(browser)
        self._dialog.setWindowTitle(self.tr("audio_export.window_title"))
        self._dialog.setMinimumWidth(680)
        self._dialog.setMinimumHeight(560)
        layout = QVBoxLayout(self._dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        self._webview = AnkiWebView(parent=self._dialog)
        self._webview.requiresCol = False
        self._webview.set_bridge_command(self._handle_bridge_command, self)
        body, head = _render_audio_export_content(
            build_audio_export_initial_state(
                note_count=len(note_ids),
                groups=groups,
                snapshots=snapshots,
            )
        )
        self._webview.stdHtml(body=body, head=head, context=self)
        layout.addWidget(self._webview)

    def tr(self, key: str, values: dict[str, object] | None = None) -> str:
        return format_message(self._messages, key, values)

    def exec(self) -> Any:
        return self._dialog.exec()

    def append_log(self, line: str) -> None:
        self._log_lines.append(line)
        self._emit("onAudioExportLog", {"line": line})

    def update_progress(self, processed: int, total: int, current_audio: str, failures: int) -> None:
        audio = current_audio or self.tr("audio_export.no_audio")
        self._emit(
            "onAudioExportProgress",
            audio_export_progress_payload(
                processed=processed,
                total=total,
                current_audio=current_audio,
                failures=failures,
                message=self.tr(
                    "audio_export.progress",
                    {"processed": processed, "total": total, "audio": audio, "failures": failures},
                ),
            ),
        )

    def finish_with_report(self, report) -> None:
        self._running = False
        self._finished = True
        self.append_log(report.summary)
        self._emit(
            "onAudioExportFinish",
            audio_export_finish_payload(
                processed=report.processed,
                total=report.total,
                exported=report.exported,
                skipped=report.skipped,
                failures=report.failures,
                canceled=report.canceled,
                output_path=report.output_path,
                summary=report.summary,
            ),
        )

    def finish_with_error(self, message: str, *, recoverable: bool = False, user_error: dict[str, str] | None = None) -> None:
        self._running = False
        self._finished = not recoverable
        self.append_log(message)
        self._emit(
            "onAudioExportError",
            {"message": message, "recoverable": recoverable, "user_error": user_error or coded_error(AQE_BATCH_INVALID_REQUEST, message)},
        )

    def _emit(self, callback: str, payload: dict[str, Any]) -> None:
        self._webview.eval(f"window.{callback}({json.dumps(payload)})")

    def _handle_bridge_command(self, cmd: str) -> bool:
        command = decode_webview_bridge_command(cmd)
        if command.name == "audio-export.start":
            return self._handle_audio_export_start(command.payload)
        if command.name == "audio-export.cancel":
            self._cancel_or_close()
            return True
        if command.name == "audio-export.close":
            self._dialog.reject()
            return True
        if command.name == "audio-export.copy_log":
            _clipboard_set_text("\\n".join(self._log_lines))
            return True
        if command.name == "frontend.log":
            _handle_frontend_log(command.payload)
            return True
        if command.name == "webview.open_url":
            open_trusted_external_url_from_payload(command.payload, logger=logger)
            return True
        return False

    def _handle_audio_export_start(self, raw_payload: object) -> bool:
        if self._running:
            return True
        try:
            request = request_from_audio_export_start_payload(raw_payload)
        except (AssertionError, TypeError, ValueError) as exc:
            message = str(exc) or self.tr("audio_export.failed", {"error": "Invalid export request"})
            self.finish_with_error(message, recoverable=True, user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message))
            return True
        self._running = True
        self._finished = False
        self._log_lines.clear()
        self._emit(
            "onAudioExportProgress",
            audio_export_progress_payload(
                processed=0,
                total=0,
                current_audio="",
                failures=0,
                message=self.tr("audio_export.starting"),
            ),
        )
        run_audio_export_in_background(self.browser, self, self.snapshots, request)
        return True

    def _cancel_or_close(self) -> None:
        if self._running:
            self.cancel_event.set()
            self.append_log(self.tr("audio_export.cancel_requested"))
            return
        self._dialog.reject()
```

Also include `_render_audio_export_content`, `_clipboard_set_text`, and `_handle_frontend_log` helpers equivalent to `browser_dialog.py`, using `initial_state_name="__AQE_BATCH_INITIAL_STATE__"` so the existing batch bundle can mount.

- [ ] **Step 5: Add `run_audio_export_in_background`**

Add to `browser_audio_export_runner.py`:

```python
def run_audio_export_in_background(
    browser: Any,
    dialog: Any,
    snapshots: tuple[BatchNoteSnapshot, ...],
    request: AudioExportRequest,
) -> None:
    mw = getattr(browser, "mw", browser)
    media_dir = Path(mw.col.media.dir())

    def on_log(line: str) -> None:
        logger.info("audio export: %s", line)
        mw.taskman.run_on_main(lambda value=line: dialog.append_log(value))

    def on_progress(processed: int, total: int, current_audio: str, failures: int) -> None:
        mw.taskman.run_on_main(lambda: dialog.update_progress(processed, total, current_audio, failures))

    def task() -> AudioExportReport:
        return run_audio_export(
            snapshots,
            request=request,
            media_dir=media_dir,
            cancel_event=dialog.cancel_event,
            on_log=on_log,
            on_progress=on_progress,
        )

    def done(future: Any) -> None:
        try:
            report = future.result()
        except Exception as exc:
            dialog.finish_with_error(f"Audio export failed: {exc}", user_error=coded_error(AQE_BATCH_INVALID_REQUEST, f"Audio export failed: {exc}"))
            return
        dialog.finish_with_report(report)

    mw.taskman.run_in_background(task, done, uses_collection=True)
```

- [ ] **Step 6: Wire Browser action**

Modify `browser_integration.py`:

```python
from .browser_audio_export_dialog import AudioExportDialog
```

Add setup near the batch action:

```python
export_action = browser.form.menu_Cards.addAction(_tr("audio_export.action"))
export_action.triggered.connect(lambda _checked=False, b=browser: _open_audio_export_dialog(b))
```

Add:

```python
def _open_audio_export_dialog(browser: Any) -> None:
    from aqt.utils import showWarning

    note_ids = unique_note_ids(browser.selected_notes())
    if not note_ids:
        showWarning(_tr("batch.no_cards_selected"), parent=browser)
        return
    snapshots = _snapshots_for_note_ids(browser.mw.col, note_ids)
    groups = field_groups_for_notes(snapshots)
    if not groups:
        showWarning(_tr("batch.no_fields"), parent=browser)
        return
    dialog = AudioExportDialog(browser, note_ids, groups, tuple(snapshots))
    dialog.exec()
```

- [ ] **Step 7: Update architecture contracts**

Modify `browser_integration` allowed deps to include `browser_audio_export_dialog`.

Add:

```python
    "browser_audio_export_dialog": contract(
        "browser_audio_export_dialog",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "batch_operations",
            "browser_audio_export_runner",
            "browser_audio_export_state",
            "error_codes",
            "external_links",
            "frontend_logs",
            "i18n",
            "webview_bridge",
            "webview_shell",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.WEB_EVAL,
        ),
        allow_any_anki_imports=True,
    ),
```

Update `tests/test_architecture/test_rule19_shared_operation_contracts.py` expected `browser_integration` deps to include `browser_audio_export_dialog`, and add assertions that `browser_audio_export_dialog.py` does not import `process_note_batch_operation`.

- [ ] **Step 8: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_integration_hooks.py tests/test_browser_audio_export_dialog.py tests/test_browser_audio_export_runner.py -q
python3 scripts/dev.py arch
```

Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_audio_export_dialog.py addon/anki_audio_quick_editor/browser_audio_export_runner.py addon/anki_audio_quick_editor/browser_integration.py tests/test_browser_integration_hooks.py tests/test_browser_audio_export_dialog.py tests/test_architecture/contract_ui.py tests/test_architecture/test_rule19_shared_operation_contracts.py
git commit -m "Add browser audio export dialog" -m "Users need export access from the Browser selection, but export must stay separate from mutating batch operations. This wires a sibling WebView dialog and background runner without adding note update or undo behavior."
```

---

## Task 8: Add Export Frontend State And Controls

**Files:**

- Create: `settings_ui/src/batch/export-state.ts`
- Create: `settings_ui/src/batch/BatchExportControls.svelte`
- Modify: `settings_ui/src/batch/bridge.ts`
- Modify: `settings_ui/src/batch/BatchApp.svelte`
- Modify: `settings_ui/src/batch/batch-state.ts`
- Create: `settings_ui/tests/batch-export-state.test.ts`
- Create: `settings_ui/tests/batch-export-app.test.ts`

- [ ] **Step 1: Write failing export-state tests**

Create `settings_ui/tests/batch-export-state.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { AudioExportMode, Direction } from "../src/lib/types.js";
import {
  audioExportStartRequest,
  canStartAudioExport,
  initialAudioExportFormState,
} from "../src/batch/export-state.js";

const state = {
  surface: "audio_export",
  note_count: 2,
  field_groups: [{ notetype_name: "Basic", fields: ["Front", "Back"] }],
  default_field_selections: [{ notetype_name: "Basic", fields: ["Front"] }],
  defaults: { mode: AudioExportMode.Zip, silence_between_clips_seconds: 1 },
  locale: "en",
  direction: Direction.LTR,
  messages: {},
} as const;

describe("audio export state", () => {
  it("initializes from default field selections", () => {
    const form = initialAudioExportFormState(state);
    expect(form.mode).toBe(AudioExportMode.Zip);
    expect(form.selectedFields.Basic).toEqual(new Set(["Front"]));
    expect(form.silenceBetweenClipsSeconds).toBe(1);
  });

  it("requires destination and at least one field", () => {
    const form = initialAudioExportFormState(state);
    expect(canStartAudioExport(form)).toBe(false);
    form.destinationPath = "/tmp/out.zip";
    expect(canStartAudioExport(form)).toBe(true);
    form.selectedFields.Basic.clear();
    expect(canStartAudioExport(form)).toBe(false);
  });

  it("builds the generated bridge payload", () => {
    const form = initialAudioExportFormState(state);
    form.destinationPath = "/tmp/out.zip";
    const request = audioExportStartRequest(form);
    expect(request).toEqual({
      mode: AudioExportMode.Zip,
      destination_path: "/tmp/out.zip",
      field_selections: [{ notetype_name: "Basic", fields: ["Front"] }],
      silence_between_clips_seconds: 1,
    });
  });
});
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd settings_ui && npm test -- batch-export-state.test.ts
```

Expected: fails because `export-state.ts` does not exist.

- [ ] **Step 3: Implement `export-state.ts`**

Create:

```typescript
import { AudioExportMode } from "$lib/types.js";
import type { AudioExportInitialState, AudioExportStartRequest } from "$lib/types.js";

export interface AudioExportFormState {
  mode: AudioExportMode;
  destinationPath: string;
  selectedFields: Record<string, Set<string>>;
  silenceBetweenClipsSeconds: number;
}

export function initialAudioExportFormState(state: AudioExportInitialState): AudioExportFormState {
  const selectedFields: Record<string, Set<string>> = {};
  for (const group of state.field_groups) {
    selectedFields[group.notetype_name] = new Set<string>();
  }
  for (const selection of state.default_field_selections) {
    selectedFields[selection.notetype_name] = new Set(selection.fields);
  }
  return {
    mode: state.defaults.mode,
    destinationPath: "",
    selectedFields,
    silenceBetweenClipsSeconds: clampSilenceSeconds(state.defaults.silence_between_clips_seconds),
  };
}

export function canStartAudioExport(form: AudioExportFormState): boolean {
  return form.destinationPath.trim().length > 0 && selectedFieldCount(form) > 0;
}

export function audioExportStartRequest(form: AudioExportFormState): AudioExportStartRequest {
  return {
    mode: form.mode,
    destination_path: form.destinationPath,
    field_selections: Object.entries(form.selectedFields)
      .map(([notetype_name, fields]) => ({ notetype_name, fields: Array.from(fields) }))
      .filter((selection) => selection.fields.length > 0),
    silence_between_clips_seconds: clampSilenceSeconds(form.silenceBetweenClipsSeconds),
  };
}

export function setAudioExportFieldSelected(
  form: AudioExportFormState,
  notetypeName: string,
  field: string,
  selected: boolean,
): void {
  const fields = form.selectedFields[notetypeName] ?? new Set<string>();
  if (selected) {
    fields.add(field);
  } else {
    fields.delete(field);
  }
  form.selectedFields[notetypeName] = fields;
}

export function selectedFieldCount(form: AudioExportFormState): number {
  return Object.values(form.selectedFields).reduce((total, fields) => total + fields.size, 0);
}

export function clampSilenceSeconds(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(10, Math.max(0, Number(value)));
}
```

- [ ] **Step 4: Add bridge functions**

Modify `settings_ui/src/batch/bridge.ts` imports:

```typescript
  AudioExportDestinationPayload,
  AudioExportDestinationRequest,
  AudioExportFinishPayload,
  AudioExportProgressPayload,
  AudioExportStartRequest,
```

Add:

```typescript
export interface AudioExportCallbacks {
  onDestination?: (payload: AudioExportDestinationPayload) => void;
  onProgress?: (payload: AudioExportProgressPayload) => void;
  onLog?: (payload: BatchLogPayload) => void;
  onFinish?: (payload: AudioExportFinishPayload) => void;
  onError?: (payload: BatchErrorPayload) => void;
}

export function audioExportChooseDestination(request: AudioExportDestinationRequest): void {
  sendBridgeEnvelope("audio-export.choose-destination", request);
}

export function audioExportStart(request: AudioExportStartRequest): void {
  sendBridgeEnvelope("audio-export.start", request);
}

export function audioExportCancel(): void {
  sendBridgeEnvelope("audio-export.cancel");
}

export function audioExportClose(): void {
  sendBridgeEnvelope("audio-export.close");
}

export function audioExportCopyLog(): void {
  sendBridgeEnvelope("audio-export.copy_log");
}

export function registerAudioExportCallbacks(callbacks: AudioExportCallbacks): void {
  if (callbacks.onDestination) window.onAudioExportDestination = callbacks.onDestination;
  if (callbacks.onProgress) window.onAudioExportProgress = callbacks.onProgress;
  if (callbacks.onLog) window.onAudioExportLog = callbacks.onLog;
  if (callbacks.onFinish) window.onAudioExportFinish = callbacks.onFinish;
  if (callbacks.onError) window.onAudioExportError = callbacks.onError;
}
```

Extend `declare global` with the new `window.onAudioExport*` callbacks.

- [ ] **Step 5: Implement `BatchExportControls.svelte`**

Create a compact control component:

```svelte
<script lang="ts">
  import { AudioExportMode } from "$lib/types.js";
  import { t } from "$lib/i18n.js";
  import type { AudioExportInitialState } from "$lib/types.js";
  import type { AudioExportFormState } from "./export-state.js";
  import { setAudioExportFieldSelected } from "./export-state.js";

  interface Props {
    state: AudioExportInitialState;
    form: AudioExportFormState;
    disabled: boolean;
    onChooseDestination: () => void;
  }

  let { state, form = $bindable(), disabled, onChooseDestination }: Props = $props();
</script>

<section class="batch-grid" data-testid="audio-export-controls">
  <fieldset>
    <legend>{t("audio_export.mode.zip")}</legend>
    <label>
      <input type="radio" bind:group={form.mode} value={AudioExportMode.Zip} {disabled} />
      <span>{t("audio_export.mode.zip")}</span>
    </label>
    <label>
      <input type="radio" bind:group={form.mode} value={AudioExportMode.CombinedMp3} {disabled} />
      <span>{t("audio_export.mode.combined_mp3")}</span>
    </label>
  </fieldset>

  <label>
    <span>{t("audio_export.destination")}</span>
    <div class="destination-row">
      <input readonly value={form.destinationPath} data-testid="audio-export-destination" />
      <button type="button" onclick={onChooseDestination} {disabled}>
        {t("audio_export.choose_destination")}
      </button>
    </div>
  </label>

  {#if form.mode === AudioExportMode.CombinedMp3}
    <label>
      <span>{t("audio_export.silence_between_clips")}</span>
      <input
        type="number"
        min="0"
        max="10"
        step="0.1"
        bind:value={form.silenceBetweenClipsSeconds}
        disabled={disabled}
        data-testid="audio-export-silence"
      />
    </label>
  {/if}

  <fieldset>
    <legend>{t("audio_export.fields")}</legend>
    {#each state.field_groups as group}
      <section class="field-group">
        <h2>{group.notetype_name}</h2>
        {#each group.fields as field}
          <label>
            <input
              type="checkbox"
              checked={form.selectedFields[group.notetype_name]?.has(field) ?? false}
              onchange={(event) =>
                setAudioExportFieldSelected(
                  form,
                  group.notetype_name,
                  field,
                  event.currentTarget.checked,
                )}
              disabled={disabled}
            />
            <span>{field}</span>
          </label>
        {/each}
      </section>
    {/each}
  </fieldset>
</section>
```

Add CSS matching existing batch controls without nested cards.

- [ ] **Step 6: Update `BatchApp.svelte`**

Add imports:

```typescript
  import { BatchSurface } from "$lib/types.js";
  import BatchExportControls from "./BatchExportControls.svelte";
  import {
    audioExportStartRequest,
    canStartAudioExport,
    initialAudioExportFormState,
  } from "./export-state.js";
  import {
    audioExportCancel,
    audioExportChooseDestination,
    audioExportClose,
    audioExportCopyLog,
    audioExportStart,
    registerAudioExportCallbacks,
  } from "./bridge.js";
```

Add export form state:

```typescript
  const isAudioExport = batchState.surface === BatchSurface.AudioExport;
  let exportForm = $state(
    isAudioExport ? initialAudioExportFormState(batchState as import("$lib/types.js").AudioExportInitialState) : undefined,
  );
  let canStartExport = $derived(exportForm ? canStartAudioExport(exportForm) : false);
```

Inside `onMount`, register export callbacks when `isAudioExport` is true:

```typescript
    if (isAudioExport) {
      registerAudioExportCallbacks({
        onDestination: (payload) => {
          if (exportForm) exportForm.destinationPath = payload.destination_path;
        },
        onProgress: (payload) => {
          processed = payload.processed;
          total = payload.total;
          failures = payload.failures;
          status = payload.message;
        },
        onLog: (payload) => {
          logLines = [...logLines, payload.line];
        },
        onFinish: (payload) => {
          running = false;
          finished = true;
          processed = payload.processed;
          total = payload.total;
          failures = payload.failures;
          status = payload.summary;
        },
        onError: (payload) => {
          running = false;
          finished = payload.recoverable !== true;
          status = isUserFacingError(payload.user_error)
            ? payload.user_error
            : frontendUnknownError(payload.message);
        },
      });
    } else {
      registerBatchCallbacks({ ...existing callbacks... });
    }
```

Split `start()` and `cancel()` so export uses export commands:

```typescript
  function start(): void {
    if (isAudioExport) {
      if (!exportForm || !canStartExport) return;
      running = true;
      finished = false;
      processed = 0;
      total = 0;
      failures = 0;
      logLines = [];
      status = t("audio_export.starting");
      audioExportStart(audioExportStartRequest(exportForm));
      return;
    }
    // existing batch start body
  }

  function cancel(): void {
    status = isAudioExport ? t("audio_export.cancel_requested") : t("batch.cancel_requested");
    if (isAudioExport) audioExportCancel();
    else batchCancel();
  }
```

Render:

```svelte
{#if isAudioExport && exportForm}
  <BatchExportControls
    state={batchState}
    bind:form={exportForm}
    disabled={running}
    onChooseDestination={() => audioExportChooseDestination({ mode: exportForm.mode })}
  />
{:else}
  <BatchControls state={batchState} bind:form selected={selected} disabled={running} />
{/if}
```

Pass footer callbacks conditionally:

```svelte
<BatchFooter
  running={running}
  finished={finished}
  onStart={start}
  onClose={isAudioExport ? audioExportClose : batchClose}
  onCopyLog={isAudioExport ? audioExportCopyLog : batchCopyLog}
  canStart={isAudioExport ? canStartExport : canStart}
/>
```

- [ ] **Step 7: Update fallback batch state**

In `settings_ui/src/batch/batch-state.ts`, set:

```typescript
surface: BatchSurface.Operations,
```

Import `BatchSurface`.

- [ ] **Step 8: Run frontend tests**

Run:

```bash
cd settings_ui && npm test -- batch-export-state.test.ts batch-export-app.test.ts batch-state.test.ts batch-app.test.ts
python3 scripts/dev.py typecheck
```

Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add settings_ui/src/batch/export-state.ts settings_ui/src/batch/BatchExportControls.svelte settings_ui/src/batch/bridge.ts settings_ui/src/batch/BatchApp.svelte settings_ui/src/batch/batch-state.ts settings_ui/tests/batch-export-state.test.ts settings_ui/tests/batch-export-app.test.ts
git commit -m "Add browser audio export controls" -m "The export dialog needs a dedicated non-mutating form while reusing the existing Browser batch bundle. This adds field selection, destination, and silence controls backed by generated bridge contracts."
```

---

## Task 9: Add Native Destination Picker

**Files:**

- Modify: `addon/anki_audio_quick_editor/browser_audio_export_dialog.py`
- Modify: `tests/test_browser_audio_export_dialog.py`

- [ ] **Step 1: Add failing destination picker test**

Append:

```python
def test_default_audio_export_filename_uses_mode_extension() -> None:
    from anki_audio_quick_editor.browser_audio_export_dialog import _default_export_filename

    assert _default_export_filename("zip").endswith(".zip")
    assert _default_export_filename("combined_mp3").endswith(".mp3")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_dialog.py::test_default_audio_export_filename_uses_mode_extension -q
```

Expected: fails because helper is missing.

- [ ] **Step 3: Implement choose-destination handling**

In `_handle_bridge_command`, add before start:

```python
        if command.name == "audio-export.choose-destination":
            return self._handle_choose_destination(command.payload)
```

Add:

```python
    def _handle_choose_destination(self, raw_payload: object) -> bool:
        mode = "zip"
        if isinstance(raw_payload, dict):
            mode = str(raw_payload.get("mode") or "zip")
        destination = _choose_export_destination(self._dialog, mode)
        if destination:
            self._emit("onAudioExportDestination", {"destination_path": destination})
        return True
```

Add module helpers:

```python
def _default_export_filename(mode: str) -> str:
    from datetime import datetime

    extension = ".mp3" if mode == "combined_mp3" else ".zip"
    return f"anki-audio-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}{extension}"


def _choose_export_destination(parent: Any, mode: str) -> str:
    from aqt.qt import QFileDialog

    filename = _default_export_filename(mode)
    filter_text = "MP3 audio (*.mp3)" if mode == "combined_mp3" else "Zip archives (*.zip)"
    selected, _filter = QFileDialog.getSaveFileName(parent, "Export Audio", filename, filter_text)
    if not selected:
        return ""
    path = Path(selected)
    suffix = ".mp3" if mode == "combined_mp3" else ".zip"
    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)
    return str(path)
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_audio_export_dialog.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_audio_export_dialog.py tests/test_browser_audio_export_dialog.py
git commit -m "Choose audio export destinations" -m "Users need a native save path before export can start. This adds mode-aware destination selection while keeping path validation at the Python request boundary."
```

---

## Task 10: Build Bundles And Add E2E Coverage

**Files:**

- Create: `e2e/test_browser_audio_export_workflow.py`
- Modify: `settings_ui/src/batch/BatchExportControls.svelte` only if the e2e test needs an additional stable `data-testid`.

- [ ] **Step 1: Build generated contracts and frontend bundle**

Run:

```bash
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py build
```

Expected: contracts and Svelte bundles regenerate successfully. Do not commit generated `templates/batch/batch_bundle.*`; they are ignored runtime artifacts.

- [ ] **Step 2: Write e2e tests**

Create `e2e/test_browser_audio_export_workflow.py` using the repo's direct-dialog e2e pattern. The test should:

```python
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import generate_tone
from e2e.helpers import run_js, wait_for_condition


def test_browser_audio_export_zip_leaves_note_fields_unchanged(anki_mw, ffmpeg_config, tmp_path: Path) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_export_zip_source.mp3"
    generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = _add_audio_note(anki_mw, source.name)
    original_html = note.fields[0]
    output = tmp_path / "cards.zip"

    _run_export_dialog(
        anki_mw,
        note.id,
        output,
        mode="zip",
    )

    wait_for_condition(lambda: output.is_file(), timeout=10, message="zip export was not written")
    note.load()
    assert note.fields[0] == original_html
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == [f"0001__note-{note.id}__Front__001__{source.name}"]


def test_browser_audio_export_combined_mp3_leaves_note_fields_unchanged(anki_mw, ffmpeg_config, tmp_path: Path) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_export_mp3_source.mp3"
    generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = _add_audio_note(anki_mw, source.name)
    original_html = note.fields[0]
    output = tmp_path / "cards.mp3"

    _run_export_dialog(
        anki_mw,
        note.id,
        output,
        mode="combined_mp3",
        silence_seconds=0.2,
    )

    wait_for_condition(lambda: output.is_file() and output.stat().st_size > 0, timeout=15, message="mp3 export was not written")
    note.load()
    assert note.fields[0] == original_html


def _add_audio_note(anki_mw, filename: str):
    note = anki_mw.col.new_note(anki_mw.col.models.by_name("Basic"))
    note.fields[0] = f"[sound:{filename}]"
    note.fields[1] = "Back"
    anki_mw.col.add_note(note, anki_mw.col.decks.current()["id"])
    return note


def _run_export_dialog(
    anki_mw,
    note_id: int,
    output: Path,
    *,
    mode: str,
    silence_seconds: float = 1.0,
) -> None:
    batch_operations = import_runtime_addon_module(".batch_operations")
    export_dialog_module = import_runtime_addon_module(".browser_audio_export_dialog")
    field_group = batch_operations.FieldGroup("Basic", ("Front", "Back"))
    note = anki_mw.col.get_note(note_id)
    snapshot = batch_operations.BatchNoteSnapshot(
        note_id,
        "Basic",
        {"Front": note.fields[0], "Back": note.fields[1]},
    )
    dialog = export_dialog_module.AudioExportDialog(anki_mw, [note_id], (field_group,), (snapshot,))
    dialog._dialog.show()
    try:
        request = {
            "mode": mode,
            "destination_path": str(output),
            "field_selections": [{"notetype_name": "Basic", "fields": ["Front"]}],
            "silence_between_clips_seconds": silence_seconds,
        }
        command = "bridge:" + json.dumps({"command": "audio-export.start", "payload": request})
        run_js(dialog._webview, f"pycmd({command!r});")
        wait_for_condition(lambda: dialog._finished is True, timeout=20, message="audio export dialog did not finish")
    finally:
        dialog._dialog.close()
```

- [ ] **Step 3: Run targeted e2e**

Run:

```bash
python3 scripts/dev.py test-e2e -- e2e/test_browser_audio_export_workflow.py
```

Expected: both export tests pass.

- [ ] **Step 4: Run frontend and Python focused tests**

Run:

```bash
python3 -m pytest \
  tests/test_audio_export_planning.py \
  tests/test_audio_export_rendering.py \
  tests/test_browser_audio_export_state.py \
  tests/test_browser_audio_export_runner.py \
  tests/test_browser_audio_export_dialog.py \
  tests/test_browser_integration_hooks.py \
  -q
cd settings_ui && npm test -- batch-export-state.test.ts batch-export-app.test.ts batch-state.test.ts batch-app.test.ts
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add e2e/test_browser_audio_export_workflow.py settings_ui/src/batch/BatchExportControls.svelte settings_ui/src/batch/BatchApp.svelte
git commit -m "Verify browser audio export workflows" -m "The export feature changes a user-facing Browser workflow, so it needs real Anki coverage proving both zip and combined MP3 outputs are written while note fields remain unchanged."
```

---

## Task 11: Final Quality Gate And Documentation Check

**Files:**

- Modify docs only if implementation changed architecture prose beyond the approved design.

- [ ] **Step 1: Run full check**

Run:

```bash
python3 scripts/dev.py check
```

Expected: pass.

- [ ] **Step 2: Run required e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: pass.

- [ ] **Step 3: Review architecture/doc drift**

Run:

```bash
python3 scripts/dev.py graphs-archive
git status --short
```

Expected: generated archive changes may appear if tracked by this workflow. If production architecture materially changed beyond the new export modules, update `ARCHITECTURE.md` Browser Batch/Export sections; otherwise leave docs alone because the design spec is the source of feature intent.

- [ ] **Step 4: Final status**

Run:

```bash
git status --short
```

Expected: only intentional files are modified.

- [ ] **Step 5: Commit final docs or cleanup**

If documentation or architecture archive files changed intentionally:

```bash
git add ARCHITECTURE.md docs/archive/architecture_diagrams tests/test_architecture
git commit -m "Document audio export architecture impact" -m "The Browser export workflow adds non-mutating modules beside batch operations. This records the boundary impact so future changes know export does not participate in note mutation or undo merging."
```

If no files changed, do not create an empty commit.

---

## Self-Review Notes

Spec coverage:

- Zip archive output: Tasks 2, 5, 10.
- Combined MP3 output: Tasks 3, 6, 10.
- All sound refs from picked fields: Task 2.
- Configurable silence: Tasks 1, 4, 8, 10.
- Non-mutating Browser workflow: Tasks 5, 7, 10, 11.
- Generated contracts and WebView bridge: Tasks 1, 4, 8.
- Architecture boundaries: Tasks 2, 3, 4, 5, 7, 11.
- Error handling and cancellation: Tasks 4, 5, 6, 7, 10.
- Full verification: Tasks 10 and 11.

No known spec gaps remain.
