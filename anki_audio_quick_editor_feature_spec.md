# Anki Audio Quick Editor Feature Specification

## 1. Product Goal

Anki Audio Quick Editor is an Anki Desktop add-on for fast, inline, non-destructive audio cleanup from the Anki Editor.

The product is optimized for sentence-mining language learners who frequently need to trim, speed-adjust, or clean short audio clips attached to individual notes. The core interaction is deliberately lightweight: click a control near the audio field, wait for processing, and the field is automatically updated to reference a newly generated MP3.

## 2. Target User

The primary user is a language learner who sentence-mines short clips and occasionally needs to clean up one audio reference while editing an Anki note.

User characteristics:

- Uses Anki Desktop.
- Uses note fields containing `[sound:filename.ext]` references.
- Edits one clip at a time.
- Sometimes wants to edit clips in a batch
- Wants quick correction, not a full waveform editor.
- Wants transformations to be reversible by keeping older media files, not by modifying originals.

## 3. Current MVP Scope

In scope:

- Detect supported `[sound:...]` tags in Anki Editor fields.
- Support `[sound:...]` references surrounded by field HTML.
- Inject compact inline controls near fields containing supported audio.
- When a field has multiple supported sound tags, edit the first supported reference.
- Apply each processing action immediately.
- Create a new MP3 file after every processing action.
- Replace the current field's first selected sound reference with the newly generated MP3.
- Preserve all original and previously generated media files.
- Provide an Undo button that restores the previous generated field reference and edit state.
- Disable inline controls while ffmpeg processing is running.
- Show a processing status while work is running.
- Hide the exact ffmpeg command by default.
- Optionally show the exact ffmpeg command while processing through a settings flag.
- Show a compact prosody visualization below the inline buttons for the current clip.
- Draw pitch in Hertz, intensity as a neutral filled background, and blank pitch gaps for unvoiced frames.
- Let the user drag a position indicator to choose the playback start position.
- Leave note persistence to Anki's normal editor save flow.
- Require user-installed system `ffmpeg` and `ffprobe` for MVP.

Out of scope:

- Save and Cancel buttons in the inline editor controls.
- Selector UI for choosing among multiple sound tags in one field.
- Batch editing.
- Waveform visualization.
- Comparison between native/user recordings.
- Manual timeline selection.
- Noise reduction.
- Recording.
- TTS generation.
- Generated-file cleanup tracking.
- Mobile Anki and AnkiWeb support.

## 4. Core Interaction

Example field:

```text
[sound:sentence.wav]
```

Example inline controls:

```text
▶  [ -L ] [ +L ] [ -R ] [ +R ] [ Shorten Pauses ] [ Slower ] [ Faster ] [ Undo ]
<pitch Hz line over intensity fill, draggable cursor>
```

Main flow:

1. User opens an Anki note in the editor.
2. The add-on scans fields and injects controls near supported audio fields.
3. User clicks an edit action such as `-L`, `Faster`, or `Shorten Pauses`.
4. Controls disable immediately and show a processing status.
5. The add-on renders a new MP3 with ffmpeg.
6. The new MP3 is added to Anki media using Anki's media APIs.
7. The field's first selected `[sound:...]` reference is replaced with the new file.
8. Controls re-enable and status reports the updated filename.
9. The prosody graph refreshes for the newly referenced clip.
10. User may drag the cursor and press Play to listen from that position.
11. User may click Undo to restore the previous generated reference and edit state.

Success outcome:

- The field references the latest generated MP3.
- Original media remains unchanged.
- Older generated files remain on disk and may be manually restored if needed.

## 5. Functional Requirements

## FR1 - Sound Reference Detection

The add-on must detect Anki sound references in editor fields.

Supported input extensions:

```text
.aac
.flac
.m4a
.mp3
.oga
.ogg
.opus
.wav
.webm
```

Behavior:

- Fields may contain surrounding HTML.
- Fields without supported audio do not get controls.
- If multiple supported references exist, MVP edits the first supported reference.
- Unsupported audio extensions are ignored for inline-control mounting.
- If the selected media file is missing, the action must fail non-destructively with a clear error.

Acceptance criteria:

- `[sound:...]` tags are detected inside HTML.
- The first supported reference is selected in multi-sound fields.
- Replacement preserves surrounding HTML.
- Fields without supported audio remain unchanged.

## FR2 - Inline Editor Controls

The add-on must inject compact controls near supported fields inside the Anki Editor webview.

Behavior:

- Controls appear only for fields with supported audio.
- Controls send `aqe:*` bridge commands through Anki's editor bridge.
- Processing actions immediately render and apply a new MP3.
- Playback plays the latest referenced/generated audio.
- Undo restores the previous generated reference and edit state.

Bridge commands:

- `aqe:scan`
- `aqe:analyze`
- `aqe:set-cursor`
- `aqe:play`
- `aqe:trim-left`
- `aqe:untrim-left`
- `aqe:trim-right`
- `aqe:untrim-right`
- `aqe:slower`
- `aqe:faster`
- `aqe:remove-pauses`
- `aqe:undo`

Not supported as inline commands:

- `aqe:preview`
- `aqe:save`
- `aqe:cancel`

## FR3 - Automatic Apply

Every processing action must produce a new media file and update the current field automatically.

Behavior:

- There is no separate Save button.
- There is no Cancel button.
- Each meaningful state change creates a distinct MP3 filename.
- No-op actions should not create a new file.
- Failed processing must leave the field unchanged.

Acceptance criteria:

- Clicking `-L` creates a shorter MP3 and updates the field reference.
- Clicking `Faster` creates a shorter pitch-preserving MP3 and updates the field reference.
- Clicking quickly while processing does not queue conflicting operations.
- The previous field reference is available through Undo.

## FR4 - Busy State And Processing Status

Audio processing can take significant time, so the UI must prevent overlapping operations.

Behavior:

- Processing buttons are disabled while ffmpeg runs.
- Status shows that processing is active.
- By default, status does not show the ffmpeg command.
- If `show_ffmpeg_commands` is enabled, status shows the exact shell-escaped ffmpeg command and stores it in the status title.

Acceptance criteria:

- Fast repeated clicks during processing produce at most one generated result.
- Controls re-enable after success or failure.
- Default status hides command details.
- Enabling the setting exposes command details for diagnostics.

## FR5 - Playback

The add-on must support quick playback of the currently referenced audio.

Behavior:

- Playback stops any current Anki audio playback before starting.
- Playback prefers the latest generated filename from the edit session.
- If the generated file is unavailable, playback falls back to the source path when possible.
- Playback starts from the visualizer cursor when one has been set.
- Seeking uses Anki's current audio player after playback starts; if seeking is unavailable, playback falls back to the beginning with a non-fatal status.

Acceptance criteria:

- User can repeatedly edit and replay a clip.
- Playback uses the latest applied audio reference.
- Dragging the cursor changes the next playback start position.

## FR5A - Prosody Visualization

The add-on must show a compact visualization for the current clip below the inline controls.

Behavior:

- Analysis runs automatically after controls mount, after each successful generated-file update, and after Undo.
- V1 shows only the current clip; no comparison track is included.
- Pitch is rendered as segmented SVG paths with Hertz labels only.
- Unvoiced pitch frames render as blank gaps instead of bridged lines.
- Intensity is rendered as a neutral filled area behind the pitch contour.
- The vertical cursor can be dragged; the displayed seconds update immediately.
- The graph may take up to about `300 ms` to refresh after an edit.
- Analysis is recomputed for the current clip and is not cached by generated filename.
- If visualization analysis fails, edit buttons remain usable and the field is not mutated.

Implementation:

- Prefer `praat-parselmouth` when it is available in Anki's Python.
- Keep Parselmouth isolated behind the analyzer backend.
- Use the built-in ffmpeg/PCM fallback as the required cross-platform path.
- Do not add `librosa` for V1.

Acceptance criteria:

- The real Anki editor shows pitch paths, intensity fill, Hertz labels, and cursor line for voiced fixtures.
- Silent/unvoiced fixtures show no pitch path and do not crash.
- Graph data refreshes after processing buttons generate new media.
- Dragging the cursor updates editor session state and playback attempts to seek from that offset.

## FR6 - Manual Trim

The add-on must crop time from the beginning or end of the clip.

Controls:

- `-L`: trim configured small step from the left.
- `+L`: undo configured small step from the left trim in the current edit state.
- `-R`: trim configured small step from the right.
- `+R`: undo configured small step from the right trim in the current edit state.

Default increments:

- Small step: `100 ms`.
- Large step: `500 ms`, reserved for future shortcut/modifier behavior.

Acceptance criteria:

- Trimming from the left makes output duration shorter.
- Trimming from the right makes output duration shorter.
- Trim values cannot produce zero or negative-duration output.
- Untrim buttons cannot reduce trim below zero.

## FR7 - Speed Adjustment

The add-on must change playback speed while preserving pitch.

Defaults:

- Initial speed: `1.00x`.
- Step: `0.05x`.
- Minimum speed: `0.75x`.
- Maximum speed: `1.50x`.

Implementation:

- Use ffmpeg `atempo` filters.
- Split atempo filters when needed to stay within ffmpeg's valid range.

Acceptance criteria:

- Faster output has shorter duration.
- Slower output has longer duration where allowed.
- Pitch remains preserved.
- Invalid speeds are rejected before rendering.

## FR8 - Internal Pause Compression

The add-on must optionally compress long internal pauses.

Defaults:

- Internal pause threshold: `300 ms`.
- Remaining target gap: `100 ms`.

Acceptance criteria:

- A long internal pause is reduced toward the configured target gap.
- Short pauses below threshold remain mostly unchanged.
- Output remains a single playable MP3.

## FR10 - Filename Strategy

Every generated output must use a new, collection-safe MP3 filename.

Filename shape:

```text
safe-original-stem__aqe_YYYYMMDD_HHMMSS_microseconds_randomtoken.mp3
```

Rules:

- Always use `.mp3`.
- Sanitize illegal or awkward stem characters to safe ASCII.
- Collapse empty or fully illegal stems to `audio`.
- Bound the preferred generated filename length before handing it to Anki media APIs.
- Include timestamp microseconds and a random token to avoid collisions during rapid clicks.
- Let Anki media APIs finalize collection-safe naming if a collision still occurs.

Corner cases:

- Original filename contains path separators: resolve only the media basename.
- Original filename contains illegal characters: sanitize the generated stem.
- Original filename is very long: truncate the generated stem while preserving uniqueness suffix.
- Original filename is non-ASCII: smoke-test and sanitize to a safe generated basename.
- Original file is missing: do not change the field.
- Original file cannot be read by ffmpeg: show processing failure and do not change the field.
- Generated preferred name collides: accept Anki's returned stored filename.

## FR11 - Error Handling

Errors must be non-mutating unless the new media file has already been successfully written and the field replacement is intentional.

Required error cases:

- Missing `ffmpeg` or `ffprobe`.
- Missing referenced media file.
- Unsupported audio reference.
- Invalid edit state.
- ffmpeg probe or render failure.
- No audio in the current field.
- Processing command received while another operation is still active.

User-facing missing ffmpeg message:

```text
Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is available in PATH, or configure its path in the add-on settings.
```

## 6. Configuration

Current config defaults:

```json
{
  "_config_version": 7,
  "enabled": true,
  "debug_logging": false,
  "show_ffmpeg_commands": false,
  "manual_trim_small_ms": 100,
  "manual_trim_large_ms": 500,
  "speed_step": 0.05,
  "min_speed": 0.75,
  "max_speed": 1.5,
  "volume_step_db": 3.0,
  "min_volume_db": -24.0,
  "max_volume_db": 24.0,
  "internal_pause_silence_threshold_db": -45,
  "internal_pause_threshold_ms": 300,
  "internal_pause_target_gap_ms": 100,
  "output_format": "mp3",
  "ffmpeg_path": "",
  "deep_filter_path": "",
  "deep_filter_post_filter": true
}
```

Settings behavior:

- Inline editor controls are always enabled in MVP.
- Debug logging is optional.
- ffmpeg command visibility is optional and disabled by default.
- `ffmpeg_path` may point to a specific ffmpeg binary; blank uses PATH.

## 7. Architecture Requirements

The implementation must preserve these boundaries:

- Anki-import-safe parsing, edit-state, config-migration, settings-state, editor-action, and audio-planning helpers must not import Anki at module level.
- Prosody type, analyzer-selection, Parselmouth backend, and ffmpeg/PCM fallback modules must not import Anki at module level.
- Optional Parselmouth imports must be isolated to `prosody_praat.py` function bodies.
- Thin runtime integration modules should avoid Anki imports at module level where practical.
- Anki editor/media/player operations stay in `editor_integration.py`.
- Settings shell stays a small `QDialog` plus `AnkiWebView`.
- Settings backend does not import editor integration.
- Python bridge command registration must stay in sync with injected editor UI commands.
- Runtime code must not depend on generated Svelte source files; Anki consumes committed bundle output.

## 8. Acceptance Test Scenarios

Required automated coverage:

- Unit tests for sound tag parsing, first-reference selection, unsupported extensions, and safe replacement.
- Unit tests for edit-state bounds, speed clamping, trim/untrim, and invalid zero-duration output.
- Unit tests for filename sanitization, long names, non-ASCII smoke coverage, and command construction.
- ffmpeg tests that render real audio and verify duration changes.
- E2E tests that open real Anki editor UI, find inline controls, click buttons, and verify generated audio exists.
- E2E tests for each processing button.
- E2E tests for prosody visualization, graph refresh after each processing button, cursor dragging, playback seek, silence gaps, and visualization failure.
- E2E tests for fast clicking while processing.
- E2E tests for Undo after multiple generated outputs.
- E2E tests for settings-driven behavior such as trim step and ffmpeg command visibility.
- E2E tests for missing media or processing failure paths where practical.

Current manual smoke expectations:

- Settings are available from `Tools -> Anki Audio Quick Editor -> Settings`.
- Fields with audio show inline controls in the editor.
- Fields without audio do not show inline controls.
- Original media files remain untouched after processing.

## 9. Development Notes

- Local development add-on ID is `1000000002`.
- Anki on this machine is version `25.09` and uses Python `3.13.5`.
- MVP depends on Homebrew/system ffmpeg during local development.
- `praat-parselmouth` is optional; a dry-run verified compatible wheels for this machine, but the shipped add-on uses the built-in ffmpeg/PCM fallback when it is not installed.
- A feature is not complete until `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` pass.
