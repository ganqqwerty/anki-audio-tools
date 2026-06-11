# Anki Audio Quick Editor Feature Specification

## 1. Product Goal

Anki Audio Quick Editor is an Anki Desktop add-on for fast, inline, non-destructive audio cleanup from the Anki Editor plus batch prosody visualization from the Anki Browser.

The product is optimized for sentence-mining language learners who frequently need to trim, speed-adjust, denoise, or clean short audio clips attached to individual notes. The core interaction is deliberately lightweight: click a control near the audio field, wait for processing, and the field is automatically updated to reference a newly generated MP3.

## 2. Target User

The primary user is a language learner who sentence-mines short clips and occasionally needs to clean up one audio reference while editing an Anki note.

User characteristics:

- Uses Anki Desktop.
- Uses note fields containing `[sound:filename.ext]` references.
- Edits one clip at a time in the editor, or runs batch operations from the Browser.
- Wants quick correction, not a full waveform editor.
- Wants transformations to be reversible by keeping older media files, not by modifying originals.

## 3. Core Interaction

Example field:

```text
[sound:sentence.wav]
```

The add-on injects inline controls near supported audio fields in the Anki Editor. Controls include playback, a prosody graph, processing actions (speed, volume, denoise, pause removal, convert, pitch hum, size reduction, region delete), undo/redo, recording, and sharing.

Main flow:

1. User opens an Anki note in the editor.
2. The add-on scans fields and injects controls near supported audio fields.
3. User clicks an edit action. Controls disable immediately and show a processing status.
4. The add-on renders a new MP3 with ffmpeg (and optionally deep-filter / RNNoise / DPDFNet / Sherpa Spleeter).
5. The new MP3 is added to Anki media using Anki's media APIs.
6. The field's first supported `[sound:...]` reference is replaced with the new file.
7. Controls re-enable. The prosody graph refreshes for the newly referenced clip.
8. User may drag the cursor and press Play to listen from that position.
9. Undo restores the previous generated reference and edit state. Undo history persists across editor sessions.
10. Browser batch operations run the same processing pipeline over multiple selected notes.

Success outcome:

- The field references the latest generated MP3.
- Original media remains unchanged.
- Older generated files remain on disk.

## 4. Non-Destructive Media

Modification buttons must never overwrite or delete the source media file. Every successful modification renders a new media file. The original media file remains available in Anki media. Generated files used by undo and redo remain available. Failure must leave the note field and current audio reference unchanged.

The authoritative filename strategy and corner cases are defined in [`sound_refs.py`](addon/anki_audio_quick_editor/sound_refs.py).

## 5. Non-Destructive Undo

Every successful modification must be reversible. Undo restores the previous generated reference and edit state without deleting generated media. A new modification pushes the previous state onto undo history and clears redo history. Undo and redo are disabled while processing is busy. Persistent undo survives editor close/reopen via [`editor_persistent_undo.py`](addon/anki_audio_quick_editor/editor_persistent_undo.py).

## 6. Shared Operations

All audio processing operations (editor and batch) share a single source of truth in [`audio_operations.py`](addon/anki_audio_quick_editor/audio_operations.py). Operations include: graph, convert, reduce_size, denoise, remove_pauses, slower, faster, volume_down, volume_up. New batch-capable behavior must be introduced as an import-safe shared operation before either UI surface uses it.

The full editor modification-button contract, quick-setting behavior, and editor/batch parity rules are in [`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`](EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md).

## 7. Architecture Requirements

The implementation must preserve these boundaries:

- Anki-import-safe parsing, edit-state, config-migration, settings-state, editor-action, and audio-planning helpers must not import Anki at module level.
- Prosody type, analyzer-selection, Parselmouth backend, and ffmpeg/PCM fallback modules must not import Anki at module level.
- Optional Parselmouth imports must be isolated to `prosody_praat.py` function bodies.
- Thin runtime integration modules should avoid Anki imports at module level where practical.
- Anki editor/media/player operations stay in the UI adapter layer.
- Settings shell stays a small `QDialog` plus `AnkiWebView`.
- Settings backend does not import editor integration.
- Python bridge command registration must stay in sync with injected editor UI commands.
- Runtime code must not depend on generated Svelte source files; Anki consumes committed bundle output.
- Every production module has an executable architecture contract in [`tests/test_architecture/`](tests/test_architecture/). See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full contract-driven architecture.

## 8. Development Notes

- Local development add-on ID is `1000000002`.
- Anki on this machine is version `25.09` and uses Python `3.13.5`.
- A feature is not complete until `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` pass.
- See [`DEVELOPMENT.md`](DEVELOPMENT.md) for setup, dependencies, and release workflow.
- See [`CONFIG_SCHEMA.md`](CONFIG_SCHEMA.md) for config access patterns.
- See [`WEBVIEW_AND_TEMPLATES.md`](WEBVIEW_AND_TEMPLATES.md) for frontend bundle and bridge rules.
