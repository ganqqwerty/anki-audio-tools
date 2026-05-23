# Voice Recording Comparison Reimplementation Design For Current Main

## Goal

Reintroduce learner voice recording and pitch comparison into the editor on top of the current `main` architecture, while changing the recording model from target-duration auto-stop to explicit user-controlled stop.

## Scope

In scope:

- Record a learner attempt from the inline editor after a target graph exists.
- Use native Anki/Qt recording, not browser recording APIs.
- Save learner audio into Anki media without changing the note field.
- Show learner pitch overlaid on the same graph as the target.
- Keep target pitch and target intensity visible.
- Do not render learner intensity.
- Add explicit start/stop recording behavior in the editor UI.
- Let the learner replay the latest attempt through a dedicated editor control.
- Extend the graph x-axis to the longer of the target duration and learner duration.
- Preserve stale-callback protection, field isolation, and note-switch safety.
- Add unit, integration, frontend, contract, and e2e coverage.

Out of scope:

- Scoring or similarity metrics.
- Pass/fail feedback.
- Multiple learner attempt history.
- Recording constrained to the target duration.
- Timeline normalization or stretching of learner data to fit the target.
- Selected-region recording.
- Note-field insertion of learner recordings.
- Playback of target audio during recording.
- CI use of a real microphone or real virtual microphone device.

## Background

The feature was already designed and implemented once on earlier local branches, but that work never landed on the current `main`.

Since then, `main` has moved substantially:

- editor toolbar definitions now live in `settings_ui/src/lib/editor-toolbar-buttons.ts`
- the editor uses richer tooltip infrastructure
- graph, selection, and split-button logic have been refactored
- current frontend command dispatch and window contract differ from the old branch
- new backend feature modules such as sharing and conversion have established clearer extension patterns

That means the old implementation is useful as a domain reference but should not be replayed mechanically.

The product requirement also changed:

- old model: recording auto-stopped at target duration
- new model: recording starts from the editor and stops only when the user explicitly stops it

## Prior Work To Inspect

The following local branches and commits capture the earlier design and implementation work.

### Branches

- `codex/voice-recording-comparison-plan`
  - previous design and implementation plan

- `codex/voice-recording-comparison`
  - previous implementation attempt

### Commits

- `483a9b7` `Add voice recording comparison design`
  - original product/design intent

- `6aa62df` `Add voice recording comparison implementation plan`
  - the earlier implementation breakdown

- `759b88a` `Add voice recording comparison`
  - the main feature implementation commit
  - this is the best single commit to study first

- `8ef21f1` `Merge main into codex/voice-recording-comparison`
  - later branch tip after integrating a newer `main`
  - useful for seeing friction with a more modern editor base, but less clean than `759b88a`

### What A Developer Should Reuse From Prior Work

Reuse the ideas, not the old wiring:

- native recorder adapter shape
- learner recording session state
- generation-based stale callback handling
- Python-owned learner playback eligibility
- learner pitch-only overlay behavior

Do not assume the old toolbar code, contract names, or graph rendering hooks still fit.

## Product Behavior

### User Flow

1. The learner opens or redraws the target graph.
2. Once the graph exists for the field, `Record` becomes enabled.
3. Clicking `Record` stops any target playback and starts learner recording.
4. The record control switches into a stop state while recording is active.
5. The learner records for as long as they want.
6. Clicking the control again stops recording.
7. The UI enters analyzing state.
8. If analysis succeeds, learner pitch appears on the shared graph.
9. `Play yours` becomes enabled for the latest learner attempt.
10. Starting a new attempt clears the previous learner overlay immediately.

### Recording Control Model

Use one visible control that toggles between:

- `Record`
- `Stop`

The backend should still expose explicit commands:

- `aqe:record-voice`
- `aqe:stop-recording`
- `aqe:play-recording`

This keeps backend semantics unambiguous while keeping the toolbar compact.

### Graph Comparison Model

Use one shared graph, not stacked graphs.

- target pitch remains visible
- target intensity remains visible
- learner pitch appears as a second pitch layer
- learner intensity is not rendered

Timeline rules:

- learner pitch uses its real timestamps
- target pitch uses its real timestamps
- the x-axis duration is `max(targetDurationMs, learnerDurationMs)`

This means:

- if the learner is shorter, their line ends earlier
- if the learner is longer, the graph expands and the target occupies only the earlier segment

### Pitch Scale

When both tracks are present, the y-axis should use a combined pitch range across target and learner so the learner line cannot clip off the graph unnecessarily.

Recommended rule:

- target only: use target range
- target plus learner: use combined min/max from both tracks
- preserve current fallback behavior when pitch data is sparse

## Architecture

### High-Level Boundary

Python owns:

- native recording lifecycle
- media output path
- learner recording duration
- prosody analysis
- stale callback validation
- learner playback

Frontend owns:

- button presentation and state
- visible recording/analyzing/ready/failed status
- target and learner graph rendering
- local disablement based on graph readiness and busy state

This is the recommended architecture because it matches both:

- the previous feature’s strongest design decisions
- the current `main` frontend/backend split

### Backend Modules

Add or restore dedicated modules:

- `addon/anki_audio_quick_editor/audio_recording.py`
  - import-safe native recording adapter
  - platform-specific recorder creation
  - start/stop lifecycle and result validation

- `addon/anki_audio_quick_editor/editor_recording.py`
  - editor recording request validation
  - learner recording state transitions
  - learner media persistence into Anki media
  - learner prosody analysis
  - learner playback
  - frontend callback emission

Do not fold learner recording into:

- `editor_processing.py`
- `editor_playback.py`
- `editor_actions.py`

Those modules can be extended for routing, but the recording feature should keep its own runtime boundary.

### Native Recording Strategy

Keep the previous recording strategy:

- native macOS helper where Anki uses it
- `QAudioSource` elsewhere
- WAV output
- import-safe Qt/Anki boundaries
- explicit permission/device failure handling

Do not use WebView `MediaRecorder`.

Do not use `aqt.sound.record_audio()` directly because it is modal and user-save oriented rather than editor-session oriented.

### Session State

Extend `EditorSession` with additive learner recording state.

Recommended tracked fields:

- `status`
- `field_index`
- `generation`
- `source_filename`
- `media_filename`
- `media_path`
- `recording_started_at_monotonic`
- `recording_duration_ms`
- `prosody_payload`
- `failure_message`

Recommended statuses:

- `idle`
- `recording`
- `stopping`
- `analyzing`
- `ready`
- `failed`

Do not carry over the old countdown state unless product requirements explicitly restore it.

### Stale Callback Model

Keep generation-based invalidation from the old implementation.

Every learner recording attempt should be tied to:

- generation
- field index
- source filename

Completions or analysis callbacks that no longer match the active session state must be ignored.

This protects:

- note switches
- field changes
- graph redraws
- overlapping async completions
- replay after a newer attempt already replaced the old one

### Bridge Model

Add backend command support for:

- `aqe:record-voice`
- `aqe:stop-recording`
- `aqe:play-recording`

Recommended payload shape for `aqe:record-voice`:

```json
{
  "command": "aqe:record-voice",
  "fieldOrd": 0,
  "graphSettings": {
    "voiceRange": "general",
    "smoothness": "balanced"
  }
}
```

The stop command can be a plain command without extra payload.

Recommended Python-to-frontend callbacks:

- `window.__aqeSetLearnerRecordingState(payload)`
- `window.__aqeSetLearnerVisualizer(ord, payload)`

These should be installed through the current `window-contract.ts`.

## Frontend Integration On Current Main

### Toolbar And Command Definitions

Current `main` defines editor toolbar commands centrally.

Integrate learner recording through:

- `settings_ui/src/lib/editor-toolbar-buttons.ts`
- `settings_ui/src/editor-inline/commands.ts`

Add:

- command union entries
- button metadata
- command slugs
- default visibility decisions

Do not reintroduce old button-definition patterns directly inside `editor-inline/commands.ts`.

### Command Dispatch

Extend `settings_ui/src/editor-inline/command-actions.ts` so that:

- `aqe:record-voice` starts recording
- `aqe:stop-recording` stops recording
- `aqe:play-recording` triggers learner playback

It must also:

- stop target playback before recording begins
- stop target playback before learner playback begins
- avoid breaking current post-edit playback behavior for unrelated commands

### Controls And Visual Surface

Extend `settings_ui/src/editor-inline/EditorControls.svelte` to:

- render the record/stop control
- render `Play yours`
- show learner recording status near the existing status area
- add a learner pitch SVG group

The controls should use the current tooltip wrapper style, not old `title`-only behavior.

### Busy-State And Disablement

Extend `settings_ui/src/editor-inline/control-actions.ts` and related state helpers so that:

- `Record` is disabled until a target graph exists
- `Stop` is enabled only while recording is active
- `Play yours` is enabled only when the learner attempt is ready and playable
- global busy state and learner state do not conflict with undo/redo, selection toolbar, or current processing flows

### Window Contract

Extend:

- `settings_ui/src/editor-inline/window-contract.ts`
- `settings_ui/src/editor-inline/globals.d.ts`

Add learner callback names to both installation and declaration coverage.

### Test Contract

Extend `settings_ui/src/editor-inline/test-contract.ts` to expose:

- learner recording status
- record button disabled state
- play-yours disabled state
- learner pitch path count
- learner intensity path count
- effective graph duration after learner overlay is present

This is required so frontend integration tests and e2e tests can assert the comparison behavior directly.

## Graph Rendering Model

Current `main` is still target-track centric:

- one intensity path
- one pitch group
- one effective track driving duration and cursor interpretation

That is not sufficient for comparison mode.

### Required Refactor

Refactor the graph scene to support:

- target track
- optional learner track
- computed shared axis duration
- computed shared pitch range

Recommended storage:

- `visualizer.__aqeTrack` for target
- `visualizer.__aqeLearnerTrack` for learner

Recommended rendering approach:

1. Keep target intensity rendering unchanged.
2. Keep target pitch rendering in `.aqe-pitch`.
3. Add learner pitch rendering in `.aqe-learner-pitch`.
4. Compute the effective duration from both tracks.
5. Compute the pitch range from both tracks when learner data exists.

### Cursor And Time Axis

The cursor and x-axis should use the effective shared duration.

This means:

- cursor projection remains coherent even when learner is longer than target
- x-axis labels reflect the extended duration
- target and learner lines are both plotted on the same time base without normalization

## Error Handling

- If no graph is ready, recording is unavailable.
- If the field/source no longer matches the active graph, recording start fails with an error and no graph mutation.
- If recording cannot start because of permission or device failure, show an error and keep the target graph intact.
- If stop occurs too quickly and the output file is invalid or empty, fail cleanly without showing a learner overlay.
- If analysis fails, do not show learner pitch.
- If a note or field changes during recording or analysis, ignore stale completions.
- If learner media is missing later, `Play yours` should fail cleanly and remain disabled after state refresh.
- Starting a new attempt clears the prior learner overlay immediately.
- Redrawing the target graph clears learner overlay and learner recording readiness until the new graph is valid.

## Testing

Testing needs to span multiple layers because the risk is split across:

- native-recorder boundary behavior
- Python session state
- bridge/contract wiring
- frontend graph rendering

### Python Unit And Integration Tests

Add focused coverage for:

- native recorder adapter start/stop behavior
- learner recording state transitions
- stale generation invalidation
- success path from record -> stop -> analyze
- recorder start failure
- recorder stop failure
- empty file failure
- analysis failure
- learner playback success and missing-file failure
- note field remains unchanged

### Frontend Integration Tests

Add coverage for:

- record disabled before graph render
- record enabled after graph render
- record button switches to stop state while recording
- learner status transitions
- learner pitch overlays without learner intensity
- x-axis expansion when learner duration exceeds target duration
- learner overlay clearing on new attempt
- learner overlay clearing on graph redraw and note reset
- play-yours enablement only after ready state

### Contract Tests

Update:

- command union and slug coverage
- window contract callback coverage
- bridge payload expectations
- test-contract shape assertions

### E2E Coverage

There was prior e2e coverage on the old branch, but it did **not** use a real virtual microphone.

The old e2e test:

- `e2e/test_editor_voice_recording_comparison_workflow.py`

used a fake recorder dependency injected at:

- `anki_audio_quick_editor.editor_dependencies._native_recorder_factory`

That is the right pattern to reuse on current `main`.

The new e2e should again:

- patch the recorder factory with a fake recorder
- write a deterministic WAV fixture on stop
- verify learner overlay rendering
- verify note field remains unchanged
- verify `Play yours` routes to playback

Do not attempt to introduce a real virtual microphone dependency in CI.

### Manual Hardware Gate

Keep one manual hardware validation step in real Anki to verify:

- microphone permission behavior
- recorder startup and stop
- generated learner overlay correctness

## Implementation Approach

### Phase 1: Recover Domain Behavior From Prior Work

Review:

- branch `codex/voice-recording-comparison-plan`
- branch `codex/voice-recording-comparison`
- commit `483a9b7`
- commit `6aa62df`
- commit `759b88a`

Reuse:

- state model
- recorder boundary
- learner overlay concept
- testing seams

Discard:

- target-duration auto-stop assumption
- old toolbar integration approach
- any outdated graph-rendering assumptions

### Phase 2: Rebuild Python Recording On Current Main

1. Add `audio_recording.py`.
2. Add `editor_recording.py`.
3. Extend `editor_session.py`.
4. Route commands through `editor_actions.py`, `editor_bridge.py`, `editor_callbacks.py`, and `editor_dependencies.py`.
5. Keep recording isolated from conversion, sharing, and processing responsibilities.

### Phase 3: Integrate With Current Frontend Command And Contract Surfaces

1. Add recording commands to `editor-toolbar-buttons.ts`.
2. Wire dispatch through current `command-actions.ts`.
3. Install learner callbacks through current `window-contract.ts`.
4. Extend test-contract visibility for learner state.

### Phase 4: Refactor Graph Rendering For Two-Track Comparison

1. Add learner track storage on the visualizer.
2. Add learner pitch SVG group.
3. Compute shared axis duration.
4. Compute shared pitch range.
5. Keep target intensity logic target-only.

### Phase 5: Verify Thoroughly

Run focused tests first, then full validation:

- Python recording tests
- frontend integration tests
- contract tests
- fake-recorder e2e workflow
- `python3 scripts/dev.py check`

## File Map

### Python

- create `addon/anki_audio_quick_editor/audio_recording.py`
- create `addon/anki_audio_quick_editor/editor_recording.py`
- modify `addon/anki_audio_quick_editor/editor_session.py`
- modify `addon/anki_audio_quick_editor/editor_actions.py`
- modify `addon/anki_audio_quick_editor/editor_bridge.py`
- modify `addon/anki_audio_quick_editor/editor_callbacks.py`
- modify `addon/anki_audio_quick_editor/editor_dependencies.py`
- modify `addon/anki_audio_quick_editor/locales/*.json`

### Frontend

- modify `settings_ui/src/lib/editor-toolbar-buttons.ts`
- modify `settings_ui/src/editor-inline/commands.ts`
- modify `settings_ui/src/editor-inline/command-actions.ts`
- modify `settings_ui/src/editor-inline/control-actions.ts`
- modify `settings_ui/src/editor-inline/EditorControls.svelte`
- modify `settings_ui/src/editor-inline/types.ts`
- modify `settings_ui/src/editor-inline/globals.d.ts`
- modify `settings_ui/src/editor-inline/window-contract.ts`
- modify `settings_ui/src/editor-inline/test-contract.ts`
- modify `settings_ui/src/editor-inline/plot.ts`
- modify `settings_ui/src/editor-inline/visualizer-renderer.ts`
- modify `settings_ui/src/editor-inline/graph-actions.ts`
- modify `settings_ui/src/editor-inline/styles/controls.css`
- modify `settings_ui/src/lib/i18n.ts`

### Tests

- add or restore Python recording tests
- add frontend recording integration tests
- update playback integration tests where learner playback is asserted
- add or restore fake-recorder e2e workflow

## Notes For The Implementer

- Treat `759b88a` as the cleanest implementation snapshot.
- Treat `8ef21f1` as a secondary integration reference only.
- Preserve the current `main` architecture instead of reviving removed code paths.
- Keep the feature additive and modular.
- Use a fake recorder dependency in automated e2e coverage; do not build CI around a virtual microphone device.
