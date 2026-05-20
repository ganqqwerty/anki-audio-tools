# Voice Recording Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add whole-clip learner voice recording in the editor and overlay learner pitch on the target prosody graph.

**Architecture:** Keep recording and media ownership in Python, modeled on Anki's native recorder path, while the Svelte editor owns controls, countdown/progress display, and graph overlay rendering. The target graph is the prerequisite; Python records for that duration, writes the learner file to Anki media without changing the note field, analyzes it through the existing prosody analyzer, and returns a learner pitch-only track.

**Tech Stack:** Python 3.13, Anki 25.09 `aqt.sound` recorder behavior, PyQt6/QtMultimedia, Svelte 5, TypeScript, generated JSON communication contracts, pytest, Vitest, Anki/Qt e2e tests, GitNexus.

---

## Code Research Summary

- Native Anki voice recording does not use WebView `MediaRecorder`. In Anki 25.09, `aqt.sound.RecordDialog` uses `NativeMacRecorder` on Apple Silicon macOS and `QtAudioInputRecorder` with `QAudioSource` elsewhere.
- `aqt.sound.record_audio()` is not a direct fit because it opens a modal Save/Cancel dialog and expects user-stopped recording. This feature needs non-modal fixed-duration capture.
- Existing target graph analysis is in `addon/anki_audio_quick_editor/editor_analysis.py`. It already handles generation ids, stale callbacks, cached prosody analysis, and frontend visualizer payloads.
- Existing playback is in `addon/anki_audio_quick_editor/editor_playback.py`. Target playback uses the editor session and `aqt.sound.av_player`.
- Existing command routing is in `addon/anki_audio_quick_editor/editor_bridge.py` and command constants are in `addon/anki_audio_quick_editor/editor_actions.py`.
- Existing frontend graph rendering is in `settings_ui/src/editor-inline/visualizer-renderer.ts` and `settings_ui/src/editor-inline/plot.ts`. The current plot has one intensity path and one pitch group.
- Latest `main` renamed the repeat control to `PlaySplitButton`, so the new `Play yours` action should be separate from the existing target `Play` split control.
- Contract source is `contracts/communication.schema.json`; generated contract files are ignored and regenerated with `python3 scripts/dev.py contracts-generate`.
- Architecture tests require every new production Python module to be registered in `tests/test_architecture/contract_*.py`.

## GitNexus Baseline

- `EditorSession`: MEDIUM risk, 8 direct importers. Any added fields should be additive and reset in `reset_for_note_load()`.
- `handle_non_processing_command`: LOW risk, direct caller is `handle_bridge_command`.
- `start_field_analysis_async`: LOW risk, direct callers are `analyze_current_async` and `analyze_requested_field_async`.
- `renderVisualizerTrack`: LOW risk in the index, but frontend tests are the real guard because this is DOM-driven code.

Run fresh `mcp__gitnexus__.impact` before editing each function, class, or method named in the tasks below.

## File Structure

- Create `addon/anki_audio_quick_editor/editor_recording.py`: editor recording lifecycle, request validation, generation checks, recorder callbacks, media write, learner analysis, and learner playback bridge behavior.
- Create `addon/anki_audio_quick_editor/audio_recording.py`: small native recorder adapter modeled on Anki's `NativeMacRecorder` and `QtAudioInputRecorder`, with runtime imports inside functions.
- Modify `addon/anki_audio_quick_editor/editor_session.py`: add per-field learner recording state and reset it on note load.
- Modify `addon/anki_audio_quick_editor/editor_actions.py`: add bridge command constants for learner recording and learner playback.
- Modify `addon/anki_audio_quick_editor/editor_bridge.py`: route new non-processing commands to `editor_recording`.
- Modify `addon/anki_audio_quick_editor/editor_callbacks.py`: export dependency-wrapped recording callbacks.
- Modify `addon/anki_audio_quick_editor/editor_dependencies.py`: add `recording_deps()` and dependencies for recorder factory, media writer, analyzer, playback, and frontend eval helpers.
- Modify `addon/anki_audio_quick_editor/editor_frontend_callbacks.py`: add helpers for learner recording state and learner visualizer payloads.
- Modify `addon/anki_audio_quick_editor/locales/*.json` and `settings_ui/src/lib/i18n.ts`: add labels and statuses for `Record`, countdown, recording, analyzing, ready, failed, and `Play yours`.
- Modify `contracts/communication.schema.json`: add schema-backed payloads for learner recording request/status/result if structured bridge payloads cross Python/TypeScript.
- Modify `settings_ui/src/editor-inline/types.ts`: add learner recording types and test-state fields.
- Modify `settings_ui/src/editor-inline/commands.ts`: add `aqe:record-voice` and `aqe:play-recording` button specs and slugs.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: render `Record` and `Play yours` controls with stable `data-testid` selectors.
- Modify `settings_ui/src/editor-inline/bridge.ts` and `window-contract.ts`: queue/pop recording requests if needed and install Python-to-frontend callbacks.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts` and `plot.ts`: render learner pitch as a second pitch group/path without learner intensity.
- Modify `settings_ui/src/editor-inline/control-actions.ts`, `graph-actions.ts`, and `playback-actions.ts`: enable/disable recording based on target graph state and keep target playback/recording states from conflicting.
- Modify `settings_ui/src/editor-inline/test-contract.ts`: expose learner overlay and recording state for frontend and e2e assertions.
- Modify `settings_ui/src/editor-inline/styles.css`: style recording buttons, recording status, and learner pitch line.
- Add Python tests for recording lifecycle and bridge integration.
- Add frontend integration tests for controls, countdown/record/analyze states, overlay rendering, and `Play yours`.
- Add an e2e workflow using a fake recorder dependency; keep real microphone capture as a manual/local hardware gate.
- Modify architecture contracts for new production modules and any broad exception allowlist entries required by recorder boundaries.

## Task 1: Recorder Adapter Spike

**Files:**
- Create: `addon/anki_audio_quick_editor/audio_recording.py`
- Test: `tests/test_audio_recording.py`
- Modify: `tests/test_architecture/contract_editor.py` or `tests/test_architecture/contract_core.py`
- Modify: `tests/conftest.py` if additional Anki/Qt mocks are needed

- [ ] Run GitNexus impact before editing any existing architecture contract helper touched by this task.
- [ ] Add unit tests for a fake recorder implementation: start records a generation, stop calls a completion callback with a WAV path, failures surface a typed add-on error.
- [ ] Implement an adapter interface such as `RecordingController` with `start()` and `stop()` methods and a `RecordingResult` dataclass.
- [ ] Keep `PyQt6.QtMultimedia`, `aqt`, and macOS helper imports inside functions or methods so import-safe tests do not load Anki/Qt at module import time.
- [ ] Add an architecture contract for the new module with the minimum required side effects.
- [ ] Run `python3 scripts/dev.py test tests/test_audio_recording.py tests/test_architecture`.

## Task 2: Recording Session State

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Test: `tests/test_editor_recording_state.py`

- [ ] Run GitNexus impact for `EditorSession` and `reset_for_note_load`.
- [ ] Add import-safe dataclasses for learner recording state, including field index, generation id, target duration, status, latest media filename/path, latest prosody payload, and failure message.
- [ ] Ensure `reset_for_note_load()` clears learner recording state, increments stale generations, and leaves edit undo/redo behavior unchanged.
- [ ] Add tests that note changes clear learner recording state and stale generations are ignored.
- [ ] Run `python3 scripts/dev.py test tests/test_editor_recording_state.py tests/test_editor_integration.py`.

## Task 3: Python Recording Lifecycle

**Files:**
- Create: `addon/anki_audio_quick_editor/editor_recording.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Test: `tests/test_editor_recording.py`
- Test: `tests/test_editor_bridge_commands.py`
- Test: `tests/test_editor_actions.py`

- [ ] Run GitNexus impact for `handle_non_processing_command`, `_bridge_deps`, `_exports`, and any dependency builder edited.
- [ ] Add bridge commands for starting learner recording and playing the latest learner recording.
- [ ] Validate recording requests against the current field, current visualized filename, and known visualized duration.
- [ ] Stop target playback before recording starts.
- [ ] Start a fixed-duration recorder after frontend countdown completion or after a Python-owned countdown decision, then auto-stop at target duration.
- [ ] Write or copy the resulting WAV to Anki media with an add-on-specific generated filename without mutating the note field.
- [ ] Analyze the learner file with `analyze_prosody_cached()` and return a learner pitch payload to the frontend.
- [ ] Ignore callbacks whose generation no longer matches the active field/session.
- [ ] Add tests for success, recorder start failure, empty file failure, analysis failure, stale completion, and media filename persistence.
- [ ] Run `python3 scripts/dev.py test tests/test_editor_recording.py tests/test_editor_bridge_commands.py tests/test_editor_actions.py`.

## Task 4: Frontend Recording Controls

**Files:**
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/window-contract.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`

- [ ] Run GitNexus impact for `commandButtons`, `setControlsBusy`, and `installEditorWindowContract` before editing.
- [ ] Add `Record` and `Play yours` controls with `mic` and `play`/recording-appropriate icons.
- [ ] Keep `Record` disabled until the target graph has a track and duration.
- [ ] Show countdown, recording, stopping, analyzing, ready, and failed states without using visible instructional copy beyond concise statuses.
- [ ] Ensure global busy state disables conflicting edit buttons while recording or analyzing.
- [ ] Add test-state fields for recording status, learner pitch path count, and `Play yours` availability.
- [ ] Run `cd settings_ui && npm run test -- editor-inline.integration.test.ts`.

## Task 5: Learner Pitch Overlay

**Files:**
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Modify: `settings_ui/src/editor-inline/plot.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/styles.css`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.playback.integration.test.ts`

- [ ] Run GitNexus impact for `renderVisualizerTrack`, `drawPitch`, and `resetVisualizerPlot`.
- [ ] Add a second SVG group for learner pitch.
- [ ] Render learner pitch with the target time axis and pitch range; do not render learner intensity.
- [ ] Clear learner overlay on new target graph requests, note load, source changes, and re-record countdown start.
- [ ] Keep existing selection, cursor, target intensity, and target pitch behavior unchanged.
- [ ] Add frontend tests proving target intensity remains, target pitch remains, learner pitch appears, and no learner intensity path is added.
- [ ] Run `cd settings_ui && npm run test -- editor-inline.integration.test.ts editor-inline.playback.integration.test.ts`.

## Task 6: Learner Playback

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_recording.py`
- Modify: `addon/anki_audio_quick_editor/editor_playback.py` only if shared playback helpers are needed
- Modify: `settings_ui/src/editor-inline/playback-actions.ts` only if frontend state needs a separate learner playback display
- Test: `tests/test_editor_recording.py`
- Test: `settings_ui/tests/editor-inline.playback.integration.test.ts`

- [ ] Run GitNexus impact for playback functions edited in this task.
- [ ] Route `Play yours` to Python using the latest learner media tracked in `EditorSession`.
- [ ] Stop target playback before learner playback.
- [ ] Keep target cursor/selection state intact unless the frontend intentionally shows a learner playback progress state.
- [ ] Add tests for disabled playback before recording, successful latest-attempt playback, and stale/missing media failure.
- [ ] Run `python3 scripts/dev.py test tests/test_editor_recording.py` and `cd settings_ui && npm run test -- editor-inline.playback.integration.test.ts`.

## Task 7: Contracts, Localization, And Architecture

**Files:**
- Modify: `contracts/communication.schema.json`
- Regenerate: `addon/anki_audio_quick_editor/contracts_generated.py`
- Regenerate: `settings_ui/src/lib/generated/contracts.ts`
- Modify: `addon/anki_audio_quick_editor/locales/*.json`
- Modify: `settings_ui/src/lib/i18n.ts`
- Modify: `tests/test_architecture/contract_editor.py`
- Modify: `tests/test_architecture/test_rule21_broad_exception_allowlist.py` if broad recorder boundaries are added
- Test: `tests/test_editor_ui.py`
- Test: `tests/test_architecture`

- [ ] Add schema definitions only for structured payloads that actually cross the bridge.
- [ ] Run `python3 scripts/dev.py contracts-generate`.
- [ ] Add English strings first, then mirror keys across the existing locale JSON files.
- [ ] Update injection and bridge contract tests for new commands and callbacks.
- [ ] Run `python3 scripts/dev.py contracts-check` and `python3 scripts/dev.py arch`.

## Task 8: E2E And Verification

**Files:**
- Add: `e2e/test_editor_voice_recording_comparison_workflow.py`
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/editor_note_helpers.py` only if helper selectors are needed
- Test command targets: editor recording unit tests, frontend integration tests, Anki API compatibility, and focused e2e

- [ ] Add an e2e fake recorder hook or dependency injection point so CI can simulate a recorded WAV without using a real microphone.
- [ ] Use a real WAV fixture or generated tone for the fake learner recording and assert the learner overlay appears without mutating the note field.
- [ ] Assert the generated learner media file exists in Anki media and `Play yours` becomes enabled.
- [ ] Add a manual test checklist for real microphone capture through Anki/Qt on macOS.
- [ ] Run `python3 scripts/dev.py test`, `python3 scripts/dev.py test-svelte`, `python3 scripts/dev.py test-anki-api`, and focused `python3 scripts/dev.py test-e2e e2e/test_editor_voice_recording_comparison_workflow.py`.

## Open Implementation Decisions

- Whether the countdown is frontend-owned or Python-owned. Frontend-owned is better for responsiveness; Python-owned can be simpler for exact recorder start timing. The implementation should pick one path in Task 3 and keep all tests consistent with it.
- Whether learner playback needs its own progress cursor. The current design only requires playback, not synchronized learner progress; avoid extra cursor state unless usability testing proves it necessary.
- Whether learner recordings should remain WAV in media or be encoded to MP3. WAV is simplest for analyzer fidelity and matches Anki review recording; MP3 is smaller. The first implementation should prefer WAV unless media size becomes a real issue.

## Final Verification Before Merge

- Run `python3 scripts/dev.py check`.
- Run `python3 scripts/dev.py test-e2e`.
- Run `mcp__gitnexus__.detect_changes` before each commit and before final handoff.
- Run manual microphone capture once in real Anki and record the result in the PR notes.
