# Selected Card Audio Export Design

## Purpose

Issue #29 asks for a way to listen to the audio from selected Anki cards on an MP3 player. The add-on should support two export forms:

- a zip archive containing the audio files from user-picked fields;
- one combined MP3 made by joining those clips in order.

This is an export workflow, not an audio editing workflow. It must leave notes, fields, Anki media, generated edit history, and Browser batch undo state unchanged.

## User Guarantee

From the Anki Browser, a user can select cards, choose fields, choose zip or combined MP3 output, choose a destination path, and start export. The add-on writes the requested external artifact and reports exported, skipped, and failed items.

For each picked field, every supported `[sound:...]` reference is included, not only the first one. Export order is deterministic:

1. selected notes after the existing card-to-note de-duplication order;
2. picked fields in the order shown for that note type;
3. sound references in field HTML order.

The export must never update note HTML or write new files into Anki media.

## Current System Context

The Browser batch flow already provides most of the selection and shell infrastructure:

- `browser_integration.py` deduplicates selected Browser cards to note IDs, snapshots note fields, and builds note-type field groups.
- `browser_dialog.py` hosts the Browser batch Svelte bundle through `webview_shell.py`.
- `browser_dialog_state.py` builds initial state and decodes generated bridge contracts.
- `browser_batch_runner.py` runs work through `mw.taskman.run_in_background(..., uses_collection=True)` and emits progress/log callbacks on the main thread.
- `batch_operations.py`, `sound_refs.py`, and `media_paths.py` already contain import-safe note snapshot, field, sound-reference, and media-path decisions.

Existing batch operations intentionally mutate notes for transforms or append generated graph media. Export should reuse the Browser selection and WebView patterns, but it should be a sibling workflow rather than another entry in `BATCH_OPERATIONS`.

## Entry Point And UX

Add a Browser action named `Export Audio...` next to `Run Audio Batch Operation...` in the Cards menu and row context menu.

The export dialog should reuse the existing Browser batch WebView bundle instead of adding a fourth generated bundle. The initial state can select an export surface so the Svelte app renders export controls rather than the mutating batch operation controls.

Controls:

- export mode segmented control: `Zip archive` or `Combined MP3`;
- grouped field checkboxes by note type;
- destination row with a `Choose...` button backed by a native save dialog;
- silence-between-clips numeric input for combined MP3 only;
- progress, log, cancel, close, and error display matching Browser batch behavior.

Default field selection should include fields that contain at least one supported sound reference among the selected notes. Users may uncheck or add fields before starting.

Default destination names:

- `anki-audio-export-YYYYMMDD-HHMMSS.zip`;
- `anki-audio-export-YYYYMMDD-HHMMSS.mp3`.

The first version does not need to persist the last export directory.

## Request Contract

Add generated communication contracts rather than ad hoc payloads.

The start request should be equivalent to:

```typescript
type AudioExportMode = "zip" | "combined_mp3";

type AudioExportFieldSelection = {
  notetype_name: string;
  fields: string[];
};

type AudioExportStartRequest = {
  mode: AudioExportMode;
  destination_path: string;
  field_selections: AudioExportFieldSelection[];
  silence_between_clips_seconds: number;
};
```

Bridge commands in the existing Browser batch bridge namespace:

- `audio-export.choose-destination`, with mode in the payload;
- `audio-export.start`;
- `audio-export.cancel`, which sets the dialog's shared cancel event;
- `frontend.log`, reused as today.

Python-to-JavaScript callbacks should mirror existing batch callbacks with export-specific names or a shared typed shape:

- destination selected;
- progress update;
- log line;
- finish;
- recoverable error.

Python remains the validation boundary. It should reject empty destination paths, unsupported modes, empty field selections, non-finite silence values, negative silence values, and silence values above the configured hard cap. Use a simple cap of `10.0` seconds for the first implementation.

## Backend Modules

Keep import-safe planning separate from UI and filesystem side effects.

Proposed modules:

- `audio_export_types.py`: dataclasses for export request, field selection, export item, per-item result, and report.
- `audio_export_planning.py`: import-safe collection and naming logic using `BatchNoteSnapshot`, `find_sound_references`, `safe_media_basename`, and `existing_media_file_path`.
- `audio_export_rendering.py`: ffmpeg command builders for normalization, optional silence generation, concat-list rendering, and final MP3 encoding. This should follow the existing `audio_commands.py` and `audio_rendering.py` style.
- `browser_audio_export_runner.py`: UI-adapter side effects: collection loading, destination temp files, zip writing, ffmpeg execution, cancellation, progress, diagnostics, and final report.
- `browser_audio_export_dialog.py` and `browser_audio_export_state.py`: dialog shell and generated-contract decoding. These can share helpers with `browser_dialog.py` and `browser_dialog_state.py` where the sharing stays simple.

Update architecture contracts for any new production modules. Export runner side effects should allow filesystem writes and subprocess execution, but not note updates, media writes, or undo merges.

## Export Item Collection

The planner receives selected note snapshots and field selections grouped by note type. For each note:

- if the note type is not selected, skip it;
- if a selected field is missing on that note, record a skip;
- if a selected field has no supported sound references, record a skip;
- for each supported sound reference, resolve the media basename and media path;
- missing media is a failure for that item, but the export continues.

Each collected item should carry:

- note ID;
- note type;
- field name;
- one-based field sound index;
- original sound filename;
- resolved source path;
- deterministic export sequence number.

If no items are exportable, the runner should report a recoverable "no audio found" error and leave no destination artifact behind.

## Zip Mode

Zip mode copies original media bytes into a user-selected zip file. It does not transcode.

Zip entry names should be stable, ordered, and collision-resistant:

```text
0001__note-123__Front__001__original-name.mp3
0002__note-123__Back__001__example.wav
```

Rules:

- prefix every entry with a zero-padded export sequence;
- sanitize note type, field name, and filename fragments for zip paths;
- avoid directories for the first implementation so extraction is simple;
- if the sanitized entry still collides, append a short deterministic suffix;
- include audio files only, not a manifest file, so extracted output is clean for simple MP3 players.

Write to a temporary zip in the destination directory and atomically promote it to the chosen path on success. On cancellation or failure before completion, remove the temporary archive.

## Combined MP3 Mode

Combined mode outputs one MP3 for broad MP3-player compatibility.

Use a temporary working directory and a two-stage ffmpeg pipeline:

1. Normalize each source clip to a numbered temporary WAV with consistent sample rate, channel count, and PCM codec.
2. If silence is greater than zero, generate one temporary silence WAV of the configured duration.
3. Build a concat-list file alternating normalized clip WAVs and the silence WAV between clips.
4. Render the concat list to the selected MP3 destination using existing ffmpeg discovery and error formatting conventions.

This avoids relying on source files having matching codecs and avoids very long single ffmpeg filter command lines for large exports.

The first implementation should use `44100 Hz`, stereo, `pcm_s16le` temporary WAVs, and the MP3 codec arguments exposed by the existing conversion command helpers. If that helper is not directly reusable, extract a shared MP3 codec helper instead of duplicating literal codec arguments. Future output format choices are out of scope.

## Progress, Cancellation, And Reporting

Progress should count exportable items, not selected notes. The UI can show collection progress first when the item total is not yet known, then item progress once collection completes.

Zip progress advances after each file is copied into the archive.

Combined MP3 progress advances after each clip is normalized, then shows a finalizing state for concat rendering.

Cancellation behavior:

- collection checks cancellation between notes;
- zip mode checks cancellation between files;
- combined mode checks cancellation between clip normalization steps and before final concat;
- cancellation during a single ffmpeg subprocess may wait for that subprocess to return in the first implementation;
- canceled exports do not promote partial output files.

The final report should include:

- output path;
- exported item count;
- skipped count;
- failure count;
- whether canceled;
- concise log lines for skipped fields and failed media references.

## Error Handling

Recoverable request errors keep the dialog open:

- no destination path;
- no fields selected;
- no exportable audio;
- invalid silence value.

Runtime failures finish with an error but leave notes untouched:

- destination directory missing or unwritable;
- zip write failure;
- ffmpeg lookup failure;
- ffmpeg normalization or concat failure.

Missing media is an item-level failure. The run should continue for later valid items; if no valid item remains, it should finish without promoting an output artifact and report the failures in the log.

Use existing diagnostic helpers to capture exceptions with operation context such as `browser.audio_export`, mode, destination extension, note count, item count, and current source filename. Add new user-facing error codes only where existing codes would be misleading.

## Testing

Python unit tests:

- field selections are applied by note type;
- all supported sound references in a selected field are collected in order;
- missing fields and empty fields are skipped;
- missing media is reported without stopping later items;
- zip entry names are ordered, sanitized, and collision-resistant;
- no exportable items produces a recoverable error;
- combined MP3 command builders create normalization, silence, concat-list, and final encode commands;
- silence seconds are rejected at the Python request boundary when outside `0.0..10.0`;
- cancellation prevents final output promotion.

Frontend tests:

- export mode selector toggles zip and combined controls;
- field checkboxes are grouped by note type and initialize from audio-containing fields;
- start is disabled without a destination or selected fields;
- combined MP3 enables the silence input and clamps visible input before sending;
- bridge payloads match the generated `AudioExportStartRequest` contract.

Integration or runner tests:

- zip export writes the expected archive entries and does not call note update or media write APIs;
- combined MP3 invokes ffmpeg through the configured runtime path and writes the destination MP3;
- progress/log callbacks are emitted for success, skips, failures, and cancellation.

E2E coverage:

- Browser selection with audio fields exports a zip and leaves note fields unchanged;
- Browser selection exports a combined MP3 with configured silence and leaves note fields unchanged;
- missing media is surfaced in the export log while other valid clips still export.

Run `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` before considering the implementation complete.

## Out Of Scope

- Editing or replacing card audio.
- Writing exported artifacts back into Anki media.
- Per-card playlists, M3U files, ID3 tags, chapters, or spoken card labels.
- Persisting export presets or last destination directory.
- Output formats other than zip and combined MP3.
- Parallel ffmpeg normalization.
- Killing in-flight ffmpeg subprocesses immediately on cancel.
