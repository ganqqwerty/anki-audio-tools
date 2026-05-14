# Anki Audio Quick Editor — Feature Specification

## 1. Product Goal

Build a cross-platform Anki add-on that allows users to quickly edit audio files attached to Anki notes from inside the Anki Editor.

The add-on is optimized for language-learning sentence cards created by sentence-mining tools. The main goal is editing speed: the user should be able to fix short sentence audio clips with minimal clicks, instant preview, and safe reversible output.

## 2. Target User

### Primary user
A language learner who sentence-mines short audio clips and occasionally needs to clean up individual clips attached to Anki cards.

### User characteristics
- Uses Anki Desktop.
- Uses sentence-mining tools that insert `[sound:filename.mp3]` references into note fields.
- Edits one clip at a time.
- Needs quick manual correction, not large batch processing.
- Wants destructive audio transformation, but reversible by creating a new file rather than overwriting the original.

## 3. Scope

### In scope for MVP
- Detect a single audio reference in an Anki Editor field.
- Support fields containing HTML around the `[sound:...]` reference.
- Inject compact inline audio editing controls near fields containing audio.
- Provide instant preview after every edit operation.
- Crop audio from the left or right by small increments.
- Speed up or slow down audio while preserving pitch.
- Auto-trim leading and trailing silence.
- Remove internal pauses longer than a configurable threshold.
- Compress removed internal pauses to a fixed 100 ms gap.
- Save every edit as a new MP3 file.
- Replace the field’s `[sound:...]` reference with the newly generated MP3.
- Leave original files untouched.
- Let Anki handle note persistence normally.
- Work on Linux, Windows, and macOS.

### Out of scope for MVP
- Multiple sound references inside one field.
- Batch editing.
- Full audio editor dialog.
- Waveform visualization.
- Pitch visualization.
- Manual timeline editing.
- Drag selection.
- Noise reduction.
- Audio recording.
- TTS generation.
- Cleanup tracking for generated files.
- Mobile Anki support.
- Web Anki support.

## 4. Core Use Case

### Use case: Quickly clean a sentence audio clip

**Actor:** Anki user  
**Context:** User is editing a note that contains an audio reference such as `[sound:sentence.mp3]`.

### Main flow
1. User opens an Anki note in the Editor.
2. User places cursor in a field containing one or more `[sound:...]` references.
3. User triggers the add-on via toolbar button, menu item, or hotkey.
4. Add-on identifies the relevant audio file.
5. Add-on opens a compact editing dialog.
6. User previews the original clip.
7. User applies one or more transformations:
   - crop from left
   - crop from right
   - speed adjustment
   - edge silence trimming
   - internal pause removal
8. User previews the edited result instantly.
9. User saves.
10. Add-on creates a new audio file in Anki’s media collection.
11. Add-on replaces the old `[sound:...]` reference in the current field with the new reference.
12. Original file remains unchanged.

### Success outcome
The note now references the edited audio file, while the original file still exists and can be restored manually if needed.

## 5. Functional Requirements

## FR1 — Audio reference detection

The add-on must detect a single audio reference inside an Anki Editor field.

### Supported syntax
```text
[sound:filename.mp3]
[sound:filename.wav]
[sound:filename.ogg]
```

### Behavior
- Fields may contain surrounding HTML.
- Each supported field contains exactly one sound reference.
- Multiple sound references inside a single field are not supported.
- If no sound reference exists, no controls should be rendered.
- If the referenced file is missing, controls should show an error state.

### Acceptance criteria
- The add-on correctly detects `[sound:...]` references inside HTML fields.
- The add-on ignores fields without audio.
- The add-on does not attempt to support multiple sound tags.

## FR2 — Inline controls in Anki Editor

The add-on must inject compact inline controls near fields containing audio.

### UI concept
Instead of opening a separate editor dialog, the add-on provides small inline action buttons near the field.

### Example controls
```text
▶  [ -L ] [ +L ] [ -R ] [ +R ] [ Trim Silence ] [ Remove Pauses ] [ Slower ] [ Faster ]
```

### Behavior
- Controls appear only for fields containing a supported `[sound:...]` tag.
- Actions operate immediately.
- After each action, a new temporary preview is generated automatically.
- User can immediately replay the updated audio.

### Acceptance criteria
- Controls appear inline near supported fields.
- Controls are hidden for fields without audio.
- User can edit audio without opening a separate dialog.
- Updated preview is available after every operation.

## FR3 — Automatic preview regeneration

The add-on must automatically regenerate preview audio after every edit operation.

### Behavior
- Every transformation immediately produces a temporary preview MP3.
- The preview becomes the currently playable version.
- User does not manually request preview generation.

### Acceptance criteria
- After trimming, playback reflects the updated audio immediately.
- After speed changes, playback reflects the updated audio immediately.
- Preview generation feels interactive for short sentence clips.

## FR4 — Playback

The add-on must support quick playback of the current preview.

### Behavior
- Playback button always plays the latest preview state.
- Playback should stop any previous playback before starting a new one.
- Playback should remain lightweight and immediate.

### Acceptance criteria
- User can repeatedly modify and replay clips quickly.
- Playback uses the most recently generated preview.

## FR5 — Manual crop from left and right

The add-on must allow the user to crop time from the beginning or end of the clip.

### Controls
Recommended hotkeys:
- `[` trims from the left.
- `]` trims from the right.
- Modifier keys may change increment size.

### Default increments
- Small step: 100 ms.
- Large step: 500 ms.

### Behavior
- Left crop increases start offset.
- Right crop decreases end offset.
- Crop limits must prevent negative or zero-length output.

### Acceptance criteria
- User can remove 100 ms from the beginning.
- User can remove 100 ms from the end.
- User cannot crop beyond valid duration.
- Preview reflects crop changes.

## FR6 — Speed adjustment

The add-on must allow changing playback speed while preserving pitch.

### Default behavior
- Initial speed: 1.00x.
- Increase step: +0.05x.
- Decrease step: -0.05x.
- Suggested range: 0.75x to 1.50x.

### Implementation expectation
Use `ffmpeg` `atempo` filter or equivalent.

### Acceptance criteria
- User can speed up a clip to 1.15x.
- Pitch should not noticeably change.
- Preview reflects speed changes.
- Invalid speed values are rejected.

## FR7 — Auto-trim leading and trailing silence

The add-on must remove silence from the beginning and end of the clip.

### Default settings
- Silence threshold: configurable; initial default `-35 dB`.
- Minimum silence duration: configurable; initial default `100 ms` for edge trim.

### Behavior
- Leading silence is removed.
- Trailing silence is removed.
- Speech should not be cut off aggressively.

### Acceptance criteria
- Clip with silence before speech is trimmed at the beginning.
- Clip with silence after speech is trimmed at the end.
- Clip without significant silence remains mostly unchanged.

## FR8 — Remove internal pauses

The add-on must remove or shorten pauses inside the clip when silence exceeds a configurable threshold.

### Default settings
- Detect internal silence longer than 300 ms.
- Remove excess silence or compress it to a short remaining gap.
- Recommended remaining gap: 80–120 ms.

### Behavior
For short sentence cards, the add-on should make audio denser without making it sound unnaturally chopped.

### Preferred algorithm
1. Detect silent intervals using `ffmpeg silencedetect` or equivalent.
2. Identify internal silent intervals longer than threshold.
3. Preserve speech regions.
4. Reassemble speech regions with a small fixed pause between them.
5. Generate preview file.

### Acceptance criteria
- A 700 ms pause inside a clip is reduced or removed.
- Pauses shorter than 300 ms are preserved.
- Leading/trailing silence handling remains separate from internal pause removal.
- Output is still a single playable audio file.

## FR9 — Save as new MP3 file

The add-on must never overwrite the original audio file.

### Behavior
- Every save operation creates a new MP3 file.
- Original format is ignored.
- Output format is always MP3.
- Generated files are not tracked for cleanup.
- The field’s `[sound:...]` reference is replaced with the new MP3 reference.
- The original file remains untouched.

### Filename strategy
Example:
```text
originalname__aqe_20260512_143012.mp3
```

### Acceptance criteria
- Saving always creates a new MP3.
- Original file remains unchanged.
- Field reference updates correctly.
- Generated files are not deleted automatically.

## FR10 — Reversibility

The add-on must support manual reversal by preserving original media files.

### Behavior
- Original media files are never modified.
- The add-on only updates the field reference.
- Anki itself remains responsible for saving note changes.

### Acceptance criteria
- User can manually restore the old sound reference if desired.
- The add-on does not directly persist notes outside normal Anki workflows.

## FR11 — Cross-platform support

The add-on should work on:
- Windows
- macOS
- Linux

### Dependencies
- Python bundled with Anki.
- Qt/PyQt bundled with Anki.
- `ffmpeg` available on the user’s system.

### MVP dependency policy
The MVP may require the user to install `ffmpeg` manually.

### Acceptance criteria
- If `ffmpeg` is missing, add-on shows an installation/configuration error.
- Paths with spaces are handled correctly.
- Non-ASCII filenames are handled correctly where possible.

## 6. Non-Functional Requirements

## NFR1 — Speed

The add-on is optimized for short sentence clips.

### Target
For clips under 10 seconds, common operations should complete quickly enough to feel interactive.

## NFR2 — Safety

The add-on must avoid destructive data loss.

### Rules
- Never overwrite original file in MVP.
- Never delete media automatically in MVP.
- Cancel must leave note unchanged.
- Failed processing must leave note unchanged.

## NFR3 — Simplicity

The UI should be compact and keyboard-friendly.

### Principle
The user should not need to understand audio engineering concepts to use the tool.

## NFR4 — Reliability

The add-on must handle common failure cases gracefully.

### Examples
- Missing file.
- Unsupported format.
- Broken audio file.
- Missing `ffmpeg`.
- Processing failure.
- Multiple sound references.

## NFR5 — Maintainability

The code should separate concerns clearly:
- Anki integration
- field parsing
- media path handling
- audio processing
- preview playback
- UI state
- config/settings

## 7. Suggested MVP UI

## Inline controls

Controls are rendered directly near fields containing audio.

### Example

```text
▶  [ -L ] [ +L ] [ -R ] [ +R ] [ Trim Silence ] [ Remove Pauses ] [ Slower ] [ Faster ]
```

## Suggested button behavior

| Control | Action |
|---|---|
| ▶ | Play current preview |
| -L | Trim 100 ms from left |
| +L | Undo 100 ms left trim in current edit state |
| -R | Trim 100 ms from right |
| +R | Undo 100 ms right trim in current edit state |
| Trim Silence | Auto-trim leading/trailing silence |
| Remove Pauses | Compress pauses >300 ms to 100 ms |
| Slower | Decrease speed by 0.05x |
| Faster | Increase speed by 0.05x |

### Interaction model
- Every button press updates the edit state.
- Every button press automatically regenerates preview audio.
- User can immediately replay the updated preview.
- Saving occurs through a dedicated Save button or automatic apply action.

## 8. Configuration

MVP should have simple defaults, with optional settings later.

### Default settings
```json
{
  "manual_trim_small_ms": 100,
  "manual_trim_large_ms": 500,
  "speed_step": 0.05,
  "min_speed": 0.75,
  "max_speed": 1.5,
  "edge_silence_threshold_db": -35,
  "edge_silence_min_ms": 100,
  "internal_pause_threshold_ms": 300,
  "internal_pause_target_gap_ms": 100,
  "output_format": "mp3"
}
```

## 9. Technical Design Overview

## Components

### Anki integration layer
Responsibilities:
- add editor button/hotkey
- access current note and field
- update field HTML/text
- trigger editor refresh/save behavior

### Sound reference parser
Responsibilities:
- find `[sound:...]` tags
- choose target audio file
- replace selected sound reference

### Media service
Responsibilities:
- resolve file path in collection media
- generate unique output filename
- create temporary preview files
- clean temporary files

### Audio processing service
Responsibilities:
- inspect duration
- crop
- speed adjustment
- trim edge silence
- detect and remove internal pauses
- produce preview and final output

### UI dialog
Responsibilities:
- show current editing state
- bind hotkeys
- request previews
- call save/cancel

### Playback service
Responsibilities:
- play original file
- play preview file
- stop playback when needed

## 10. Processing Model

The editor should maintain an edit state object rather than modifying the file after every individual button press.

### Example edit state
```json
{
  "source_file": "sentence.mp3",
  "left_trim_ms": 200,
  "right_trim_ms": 100,
  "speed": 1.15,
  "edge_trim_enabled": true,
  "remove_internal_pauses_enabled": true,
  "internal_pause_threshold_ms": 300,
  "internal_pause_target_gap_ms": 100
}
```

Whenever the user requests preview, the add-on renders a temporary audio file from the current edit state.

When the user saves, the add-on renders the final file from the same edit state and updates the note field.

## 11. Error Handling

## Missing `ffmpeg`
Message:
```text
Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is available in PATH, or configure its path in the add-on settings.
```

## No audio in field
Message:
```text
No [sound:...] reference found in the current field.
```

## Missing media file
Message:
```text
The referenced audio file was not found in Anki's media folder.
```

## Processing failed
Message:
```text
Audio processing failed. The note was not changed.
```

## 12. MVP Acceptance Test Scenarios

### Scenario 1 — Open editor for single audio field
Given a note field contains `[sound:test.mp3]`, when user launches the add-on, then the dialog opens for `test.mp3`.

### Scenario 2 — Cancel safely
Given the dialog is open, when user clicks Cancel, then no new media file is created and the note field remains unchanged.

### Scenario 3 — Trim left and save
Given a 3-second clip, when user trims 200 ms from the left and saves, then a new file is created and the field references the new file.

### Scenario 4 — Speed up and preview
Given a sentence clip, when user sets speed to 1.15x, then preview plays faster without changing pitch noticeably.

### Scenario 5 — Remove edge silence
Given a clip with 500 ms leading silence and 600 ms trailing silence, when user applies edge trim, then preview removes most leading/trailing silence.

### Scenario 6 — Remove internal pause
Given a clip with a 700 ms pause between words, when user applies internal pause removal with threshold 300 ms, then the pause is reduced to approximately 100 ms.

### Scenario 7 — Multiple sound references
Given a field contains two `[sound:...]` references, when user launches the add-on, then the user can select which audio file to edit.

### Scenario 8 — Missing ffmpeg
Given `ffmpeg` is unavailable, when user launches the add-on, then the add-on shows a clear setup error and does not crash.

## 13. Development Milestones

## Milestone 1 — Skeleton Anki add-on
- Add toolbar/menu entry in Anki Editor.
- Detect current field.
- Parse `[sound:...]` reference.
- Show basic dialog.

## Milestone 2 — Media and preview foundation
- Resolve Anki media file path.
- Check `ffmpeg` availability.
- Play original audio.
- Generate temporary copy/preview.
- Play edited preview.

## Milestone 3 — Basic transforms
- Manual left/right crop.
- Speed adjustment.
- Save as new file.
- Replace field reference.

## Milestone 4 — Silence processing
- Edge silence trimming.
- Internal pause detection.
- Internal pause compression/removal.

## Milestone 5 — UX polish
- Hotkeys.
- Better status messages.
- Optional waveform preview.
- Settings dialog.

## Milestone 6 — Cross-platform hardening
- Test on Windows, macOS, Linux.
- Handle paths with spaces.
- Handle non-ASCII filenames.
- Improve ffmpeg configuration.

## 14. Resolved Product Decisions

| Topic | Decision |
|---|---|
| Output format | Always generate MP3 |
| Original format preservation | Not supported |
| HTML around sound tags | Supported |
| Multiple sound files in one field | Not supported |
| Preview generation | Automatic after every edit |
| Generated file cleanup | No cleanup tracking |
| Internal pause handling | Compress to fixed 100 ms gap |
| Waveform display | Not included |
| Pitch visualization | Not included |
| Save behavior | Only update editor field; Anki saves normally |
| Editing UI | Inline controls near fields instead of modal dialog |

