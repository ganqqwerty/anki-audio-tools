# Record Own Voice Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the inline editor learner-recording workflow so the recording aligns to the current graph cursor, learner playback toggles between play and pause, the learner sidecar can be shared or revealed directly, and the learner pitch remains legible in dark theme.

**Architecture:** Keep learner recording as a sidecar workflow that never mutates the note field. Extend the existing learner-recording session and frontend payload with explicit alignment and learner-playback state, then add dedicated learner-sidecar share/reveal commands that reuse existing editor sharing and file-reveal adapters without reusing the main-field media lookup.

**Tech Stack:** Python 3.13 Anki add-on runtime, Anki native `av_player`, Svelte 5 + TypeScript, existing editor bridge callbacks, pytest, Vitest, editor e2e tests.

---

## File Structure

Modify:

- `addon/anki_audio_quick_editor/editor_recording.py`: add learner recording alignment, learner playback toggle logic, and learner-sidecar path validation.
- `addon/anki_audio_quick_editor/editor_recording_frontend.py`: publish extra learner state fields to the webview.
- `addon/anki_audio_quick_editor/editor_session.py`: store learner alignment and learner playback state in the Python-owned session.
- `addon/anki_audio_quick_editor/editor_actions.py`: add payload fields and new learner-sidecar commands.
- `addon/anki_audio_quick_editor/editor_bridge.py`: route the new commands and keep learner actions non-processing.
- `addon/anki_audio_quick_editor/editor_callbacks.py`, `addon/anki_audio_quick_editor/editor_dependencies.py`, `addon/anki_audio_quick_editor/editor_integration.py`: export and wire the new learner-sidecar callbacks.
- `addon/anki_audio_quick_editor/editor_sharing.py`: add an explicit-path learner-sharing adapter entrypoint that uploads `session.learner_recording.media_path`.
- `addon/anki_audio_quick_editor/editor_settings_actions.py`: add an explicit-path reveal helper for learner media.
- `addon/anki_audio_quick_editor/locales/en.json`, `de.json`, `ja.json`, `ru.json`, `vi.json`, `zh_CN.json`, `zh_TW.json`: add labels, disabled titles, and statuses for learner playback/share/reveal.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`, `settings_ui/src/lib/editor-toolbar-command-slugs.ts`: register `aqe:share-recording` and `aqe:show-recording-file`.
- `settings_ui/src/editor-inline/types.ts`, `settings_ui/src/editor-inline/recording-state.ts`: add learner payload fields such as `startCursorMs` and `playbackStatus`.
- `settings_ui/src/editor-inline/recording-actions.ts`: capture the current cursor when starting learner recording, reflect learner play/pause state, and manage disabled-state rules for the learner panel.
- `settings_ui/src/editor-inline/EditorControls.svelte`: render the extra learner-sidecar buttons inside the existing `Record / Play yours` panel.
- `settings_ui/src/editor-inline/test-contract.ts`: expose learner playback status and learner start cursor for e2e assertions.
- `settings_ui/src/editor-inline/styles/graph.css`: add a dark-theme learner-pitch yellow with stronger contrast.
- `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`: document the new learner-panel behavior.
- `tests/test_editor_recording.py`, `tests/test_editor_recording_state.py`, `tests/test_editor_sharing.py`, `tests/test_editor_bridge_facade_commands.py`, `tests/test_editor_actions.py`: cover backend behavior and command routing.
- `settings_ui/tests/editor-inline.recording.integration.test.ts`: cover learner-panel state transitions and button enablement.
- `e2e/test_editor_voice_recording_comparison_workflow.py`: cover cursor-aligned start, learner play/pause toggle, learner share, learner reveal, and media-folder invariants.

## Public Interface Changes

- `LearnerRecordingRequest` gains `start_cursor_ms`.
- `LearnerRecordingState` gains `start_cursor_ms` and `playback_status` with values `stopped | playing | paused`.
- `LearnerRecordingStatePayload` gains `startCursorMs` and `playbackStatus`.
- `EditorCommandPayload` gains `start_cursor_ms` support for `aqe:record-voice`.
- New editor bridge commands: `aqe:share-recording` and `aqe:show-recording-file`.
- Existing `aqe:play-recording` changes from one-shot play to toggle semantics: start when stopped, pause when playing, resume when paused.

## Tasks

### Task 1: Align learner recording to the current cursor

**Files:**
- Modify: `settings_ui/src/editor-inline/recording-actions.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/recording-state.ts`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_recording.py`
- Modify: `addon/anki_audio_quick_editor/editor_recording_frontend.py`
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Test: `tests/test_editor_recording.py`
- Test: `e2e/test_editor_voice_recording_comparison_workflow.py`

- [ ] Capture `cursorMs` from the active visualizer before dispatching `aqe:record-voice` and include it in the pending command payload.
- [ ] Add `start_cursor_ms` to the Python request and session state, clamped to the current target graph duration.
- [ ] Stop resetting the learner recording cursor to `0`; initialize it from `startCursorMs` and keep the graph cursor anchored there during countdown and recording.
- [ ] Offset learner overlay rendering by `start_cursor_ms` so the learner pitch begins at the selected target timestamp while the learner WAV itself remains unmodified.
- [ ] Keep the completed recording in Anki media as the invariant storage location and treat any implementation change here as a bug fix only if runtime verification shows a mismatch with the current tested behavior.

### Task 2: Make `Play yours` toggle between play and pause

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_recording.py`
- Modify: `addon/anki_audio_quick_editor/editor_recording_frontend.py`
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Modify: `settings_ui/src/editor-inline/recording-actions.ts`
- Modify: `settings_ui/src/editor-inline/recording-state.ts`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Test: `tests/test_editor_recording.py`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Test: `e2e/test_editor_voice_recording_comparison_workflow.py`

- [ ] Keep learner playback on Anki native playback rather than moving it to HTML audio.
- [ ] Change `aqe:play-recording` to a toggle command: start learner playback when `playback_status == "stopped"`, call `av_player.toggle_pause()` and publish `paused` when `playback_status == "playing"`, and call it again to resume when `playback_status == "paused"`.
- [ ] Publish learner playback state through `window.__aqeSetLearnerRecordingState(...)` so the frontend can swap label, tooltip, and button state between Play and Pause.
- [ ] Add a learner-playback completion timer based on the learner recording duration so the backend can reset `playback_status` to `stopped` when native playback finishes, even though the learner audio is not driven by the main graph progress clock.
- [ ] Reset learner playback state on note load, graph reset, explicit stop of editor playback, and missing-media failure paths.

### Task 3: Add learner-sidecar share and reveal actions

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Modify: `addon/anki_audio_quick_editor/editor_sharing.py`
- Modify: `addon/anki_audio_quick_editor/editor_settings_actions.py`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-command-slugs.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/recording-actions.ts`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Test: `tests/test_editor_sharing.py`
- Test: `tests/test_editor_bridge_facade_commands.py`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Test: `e2e/test_editor_voice_recording_comparison_workflow.py`

- [ ] Add `aqe:share-recording` and `aqe:show-recording-file` as learner-panel commands, not as standalone top-level toolbar visibility settings.
- [ ] Reuse the existing `share_target` default for learner sharing and do not introduce a separate persisted preference for learner audio.
- [ ] Implement explicit learner-media lookup from `session.learner_recording.media_path` and reject the action when learner state is not `ready` or the file is missing.
- [ ] Render the new buttons inside the existing `Record / Play yours` panel and keep them disabled until learner media is ready.
- [ ] Preserve the non-mutating contract: sharing or revealing learner media must never replace the note field’s `[sound:...]` reference or alter undo/redo history.

### Task 4: Improve learner pitch contrast in dark theme

**Files:**
- Modify: `settings_ui/src/editor-inline/styles/graph.css`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`

- [ ] Keep the target pitch stroke unchanged.
- [ ] Move the learner stroke to a yellow family in dark theme only, with enough contrast against Anki dark backgrounds and the existing target pitch/intensity layers.
- [ ] Leave light-theme learner pitch readable and distinct from the target line.

### Task 5: Lock in regressions and docs

**Files:**
- Modify: `tests/test_editor_recording.py`
- Modify: `tests/test_editor_recording_state.py`
- Modify: `tests/test_editor_actions.py`
- Modify: `tests/test_editor_sharing.py`
- Modify: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Modify: `e2e/test_editor_voice_recording_comparison_workflow.py`
- Modify: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`

- [ ] Add backend tests for `start_cursor_ms` propagation, learner playback toggle transitions, learner-sidecar share/reveal missing-media rejection, and the media-folder invariant.
- [ ] Add frontend integration coverage for the learner panel showing `Pause yours` while learner playback is active, restoring `Play yours` after completion, and enabling share/reveal only when learner media is ready.
- [ ] Expand the existing learner-recording e2e to start recording from a non-zero cursor, verify the overlay aligns to that cursor, verify learner WAV remains in media, then verify play/pause, share, and reveal behavior.
- [ ] Update `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md` so the learner-recording divergence section matches the new panel contract.

## Verification

- Focused Python: `python3 scripts/dev.py test tests/test_editor_recording.py tests/test_editor_recording_state.py tests/test_editor_sharing.py tests/test_editor_actions.py`
- Focused frontend: `python3 scripts/dev.py test-svelte -- --run settings_ui/tests/editor-inline.recording.integration.test.ts`
- Focused e2e: `python3 scripts/dev.py test-e2e e2e/test_editor_voice_recording_comparison_workflow.py`
- Full gate before merge: `python3 scripts/dev.py check`

## Assumptions

- The two new learner-sidecar actions live inside the existing `Record / Play yours` panel and share its visibility setting.
- Learner playback remains native Anki playback; the plan does not move learner audio to browser playback.
- “Store recordings in the media folder” is already the intended contract; implementation work should verify and preserve it unless actual runtime behavior in this worktree contradicts the current backend and test suite.
