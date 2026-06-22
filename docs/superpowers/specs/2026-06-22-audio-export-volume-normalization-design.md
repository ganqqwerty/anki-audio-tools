# Audio Export Volume Normalization Design

## Purpose

Users should be able to normalize volume when exporting selected-card audio from the Browser audio export dialog. The option applies to both current export modes:

- a ZIP archive of selected audio files;
- one combined MP3 made from the selected clips.

The option is export-only. It must not mutate note HTML, write normalized files into Anki media, update generated edit history, or affect Browser batch undo state.

## User Guarantee

The audio export dialog adds a `Normalize volume` checkbox. It is unchecked by default so existing exports remain unchanged unless the user opts in.

When unchecked:

- ZIP export keeps today's byte-for-byte original media entries.
- Combined MP3 keeps today's staging and concatenation behavior.

When checked:

- ZIP export contains normalized MP3 copies of the selected audio files.
- Combined MP3 normalizes each selected clip before concatenating and encoding the final MP3.

The normalized ZIP mode intentionally uses MP3 entries instead of preserving every original extension. Existing project codec helpers support a limited conversion set, while export collection accepts formats such as OGG, Opus, and WebM. Converting normalized ZIP entries to MP3 gives consistent behavior across all supported audio references and keeps exported files suitable for common MP3 players.

## Current System Context

The selected-card audio export flow already has the right boundaries:

- `settings_ui/src/batch/BatchExportControls.svelte` renders export controls.
- `settings_ui/src/batch/export-state.ts` owns frontend export form state and builds the start payload.
- `contracts/communication.schema.json` defines generated Browser export contracts.
- `browser_audio_export_state.py` builds initial state and validates the generated start request.
- `audio_export_types.py` carries import-safe export request and report dataclasses.
- `audio_export_rendering.py` builds ffmpeg commands for export staging, silence, concat, and final MP3 rendering.
- `browser_audio_export_runner.py` collects items, writes ZIP archives, runs ffmpeg, reports progress, handles cancellation, and cleans temporary files.

The existing `build_normalize_wav_command` name currently means "standardize to WAV shape for concat"; it does not perform loudness normalization. The implementation should make that distinction explicit so future readers do not confuse container/sample normalization with volume normalization.

## UX And Contract

Add a checkbox below the export mode/destination controls:

```text
[ ] Normalize volume
```

The checkbox remains available for both modes. It disables while export is running like the other export controls.

Generated contracts gain a boolean:

```typescript
type AudioExportDefaults = {
  mode: AudioExportMode;
  silence_between_clips_seconds: number;
  normalize_volume: boolean;
};

type AudioExportStartRequest = {
  mode: AudioExportMode;
  destination_path: string;
  field_selections: AudioExportFieldSelection[];
  silence_between_clips_seconds: number;
  normalize_volume: boolean;
};
```

Initial state sets `defaults.normalize_volume` to `false`. Frontend form state stores `normalizeVolume`, and `audioExportStartRequest()` serializes it as `normalize_volume`.

Python remains the validation boundary. Missing `normalize_volume` from stale or malformed payloads must decode as a request error through the generated contract path, not silently enable normalization.

## Rendering Design

Use FFmpeg `loudnorm` for the first implementation:

```text
loudnorm=I=-16:TP=-1.5:LRA=11
```

This is a fixed, voice-friendly loudness target. The first version does not expose target loudness settings in the UI.

Add focused command builders in `audio_export_rendering.py`:

- a shape-only WAV staging command for combined MP3 when normalization is off;
- a loudness-normalized WAV staging command for combined MP3 when normalization is on;
- a loudness-normalized MP3 command for ZIP entries when normalization is on.

Use the existing MP3 codec helper for normalized ZIP entries and final MP3 output. Validate output paths through the same ffmpeg output-contract helpers already used by export rendering.

## ZIP Mode

Unchecked ZIP mode remains byte-for-byte copy:

1. open temporary ZIP in the destination directory;
2. write each source file with the existing stable entry name;
3. promote the temp archive only after success.

Checked ZIP mode renders normalized MP3 files into a temporary export directory before writing them to the archive:

1. create a temporary working directory;
2. for each export item, render `sequence.mp3` with `loudnorm`;
3. write the rendered MP3 to the ZIP;
4. use the existing stable entry naming scheme, but force the entry extension to `.mp3`;
5. clean the temporary working directory after success, failure, or cancellation.

The archive must still contain only audio files. No manifest is added.

## Combined MP3 Mode

Combined MP3 keeps the current two-stage design:

1. render each source clip to numbered temporary WAV;
2. optionally insert generated silence WAVs;
3. write a concat list;
4. render the final MP3 to a temporary destination file and promote it on success.

When `normalize_volume` is false, the per-clip WAV command only standardizes sample rate, channels, and codec. When `normalize_volume` is true, the per-clip WAV command applies `loudnorm` while producing the same standardized WAV shape.

Final MP3 encoding must not apply another loudness filter. Normalizing each clip before concat is the user-visible behavior because it makes clips more consistent with each other.

## Progress, Cancellation, And Reporting

Progress continues to count exportable items.

- ZIP unchecked: progress advances after each original file is copied into the archive.
- ZIP checked: progress advances after each file is normalized and written to the archive.
- Combined MP3 unchecked or checked: progress advances after each source clip is staged to WAV.

Cancellation checks remain between items and before final promotion. The first implementation does not need to kill an already-running ffmpeg subprocess; cancellation may wait for the current subprocess to return.

Log lines should make normalization visible without becoming noisy:

- unchecked ZIP: keep the existing `Exported ... as ...` wording;
- checked ZIP: log `Normalized and exported ... as ...`;
- unchecked combined MP3: keep the existing preparation wording;
- checked combined MP3: log `Normalized ... for combined MP3 export.`

## Error Handling

Normalization failures are runtime export failures. They must:

- leave notes unchanged;
- avoid promoting partial output files;
- remove temporary ZIP/output files and temporary working directories;
- surface the existing ffmpeg error message path in the dialog.

Missing media remains an item-level planning failure before rendering starts. Unsupported export modes, empty destination paths, empty field selections, and invalid silence values keep their current request validation behavior.

## Testing

Python unit tests:

- `AudioExportRequest` carries `normalize_volume` with a default of `False`.
- `request_from_audio_export_start_payload()` accepts explicit true/false values and rejects malformed contract payloads.
- initial audio export state includes `defaults.normalize_volume: false`.
- ffmpeg command builders include `loudnorm=I=-16:TP=-1.5:LRA=11` only in normalized commands.
- unchecked ZIP export still writes original bytes.
- checked ZIP export renders MP3 temp files, writes `.mp3` archive entries, and leaves source media untouched.
- checked combined MP3 uses the normalized WAV staging command before concat.
- cancellation removes temporary artifacts in normalized ZIP and combined MP3 modes.

Frontend tests:

- export form initializes `normalizeVolume` from defaults.
- the checkbox toggles `normalize_volume` in `audioExportStartRequest()`.
- the checkbox is disabled during export.

Contract tests:

- regenerate and check Python/TypeScript contract outputs after schema changes.

E2E coverage:

- Browser audio export can create a normalized ZIP from selected cards and leaves note fields unchanged.
- Browser audio export can create a normalized combined MP3 and leaves note fields unchanged.

Run `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` before considering the implementation complete.

## Out Of Scope

- Persisting the normalize-volume preference.
- User-configurable LUFS, true peak, or loudness range targets.
- Two-pass loudnorm analysis.
- Normalized ZIP output formats other than MP3.
- Replacing or editing Anki media.
- Killing in-flight ffmpeg immediately on cancel.
