# Inline Graph Region Delete Feature Specification

Implemented in commit: `5da7f88172b831eab3480d9761f48bb99845dfb6`

## 1. Background

Audio Quick Editor already supports inline, non-destructive audio edits from the Anki Editor. Current processing actions are initiated from editor controls, rendered through ffmpeg, saved as new Anki media files, and applied by replacing the active field's selected `[sound:...]` reference. The original media file remains untouched, generated files remain on disk, and Undo/Redo restores previous audio references and edit state.

The inline graph currently provides:

- Prosody graph rendering for the active audio reference.
- Cursor dragging for playback start.
- Shift-drag region selection for selected-region playback.
- Repeat playback for either the full clip or selected region.
- Graph redraw after successful processing actions.
- Playback shutdown before processing starts.

This feature adds the missing editing action for an existing selected region: a Delete Region action appears when the user has a committed graph selection, and either clicking that action or pressing Backspace while the graph has focus removes that region from the current audio and replaces only the opened audio reference in the active field with a newly generated media file.

## 2. Product Goal

Let users quickly cut unwanted words, silence, or noise from the inline graph without opening a full audio editor.

The desired interaction is:

1. User opens the inline graph for an audio field.
2. User selects a region in the graph.
3. User clicks Delete Region, or presses Backspace while the graph has focus.
4. Playback stops immediately, even during selected repeat playback.
5. The add-on renders a new audio file with the selected region removed.
6. The active field's opened audio reference is replaced with the generated filename.
7. The graph is re-rendered for the new audio.
8. The edit participates in the existing Undo/Redo history.

## 3. Scope

In scope:

- Inline editor graph only.
- Delete Region button for committed graph selections.
- Backspace key shortcut for the focused graph.
- Deleting any committed non-zero selected region that leaves some audio outside the selection.
- Deleting from the very beginning.
- Deleting through the very end.
- Rejecting whole-clip deletion without mutating the field.
- New generated media file following existing AQE filename rules.
- Non-destructive source media behavior.
- Full e2e verification with real audio duration/content checks.

Out of scope:

- Confirmation UI.
- Delete key, Fn+Delete, context menus, always-visible toolbar buttons, or global shortcuts.
- Browser batch graph output.
- Choosing among multiple audio references inside one field.
- Destructive modification of the original Anki media file.

## 4. Functional Specification

### FR1 - Delete Region Action And Focus

The primary action is a Delete Region button that appears only when the inline graph has a committed selected region. Backspace is a keyboard shortcut for the same action and must work only when the inline graph itself has focus.

Behavior:

- The Delete Region button is hidden when there is no committed selection.
- The Delete Region button appears when there is a committed selection.
- The Delete Region button is disabled, or otherwise clearly unavailable, when the selection would delete the whole audio.
- Clicking Delete Region dispatches the same region-delete command as the Backspace shortcut.
- Clicking or dragging in the graph should make that graph focusable and focused.
- Backspace must do nothing when focus is in the Anki field editor, another button, a graph without a valid selection, or any unrelated page element.
- The event handler must check the focused graph/visualizer identity, not merely the existence of a selection somewhere on the page.
- The handler must ignore Backspace while AQE is busy.
- The handler must call `preventDefault()` only when it will handle the delete operation, so normal Anki text editing keeps working outside the focused graph.

Acceptance criteria:

- Selecting a valid region shows an enabled Delete Region button.
- Clearing the selected region hides the Delete Region button.
- Selecting the whole audio shows a non-actionable Delete Region state or hides the action, but must not allow deletion.
- Clicking Delete Region dispatches the region-delete command.
- Selecting a region and pressing Backspace with graph focus dispatches the region-delete command.
- Pressing Backspace with the field text focused does not generate audio and does not remove text unexpectedly.
- In a note with multiple audio fields, Backspace affects only the focused graph.

### FR2 - Valid Selection

Any committed non-zero selected region that leaves some audio outside the selection is valid.

Behavior:

- The selected range is normalized as `startMs < endMs`.
- A selection may start at `0`.
- A selection may end at the current audio duration.
- A selection must not cover the whole duration.
- Whole-audio deletion is rejected before rendering and must not create a media file.
- Draft selections do not count until committed.
- No selection means Delete Region is hidden and Backspace is ignored.
- Click-like tiny gestures may still be rejected by existing selection gesture logic. Once a committed non-zero region exists, it is valid for deletion only if it leaves some audio outside the selection.

Acceptance criteria:

- Middle selection deletes only the middle region.
- Beginning selection deletes the prefix.
- Ending selection deletes the suffix.
- Full selection does not render, does not update the field, and does not push Undo history.

### FR3 - Audio Rendering Semantics

The generated audio must contain the original audio before the selection plus the original audio after the selection, with the selected region removed.

Behavior:

- The source for rendering is the active/opened audio reference for the focused graph.
- The old media file remains unchanged.
- The output format remains the existing configured output strategy, currently generated `.mp3`.
- The filename must follow existing AQE generated-audio naming rules.
- If the selected region covers the whole audio, reject the action before rendering.
- The operation should be independent of content. Speech, silence, noise, and tiny blips are treated identically.

Implementation direction:

- Add an explicit "cut region" representation to the processing model rather than faking it as left/right trims.
- Prefer a pure planning helper that builds a two-segment ffmpeg concat/filter plan from `source_path`, `selectionStartMs`, `selectionEndMs`, and `durationMs`.
- Keep ffmpeg invocation and temp output writing inside `audio_processor.py`.
- Keep Anki media writes and field replacement inside `editor_integration.py`.

Acceptance criteria:

- `ffprobe` duration of middle deletion is approximately `originalDuration - deletedDuration`, allowing encoder tolerance.
- The generated file is playable and analyzable.
- The original file bytes are unchanged.

### FR4 - Field And Audio Reference Scoping

Deletion updates only the active field and only the opened audio reference.

Behavior:

- The frontend command must carry or imply the focused graph ordinal.
- Python must resolve the current field consistently with existing processing commands.
- If the active field contains multiple sound refs, update the opened/selected reference, not an arbitrary sound reference from a different field.
- For the current MVP, if existing runtime support still always opens the first supported reference, deletion follows that same opened reference.
- Fields that are not active/focused must remain unchanged.

Acceptance criteria:

- In a multi-field note, deleting a region in field 2 changes only field 2.
- In a field with surrounding HTML, replacement preserves the surrounding HTML.
- In a note with multiple audio fields, graph redraw happens for the edited graph and does not corrupt other graph state.

### FR5 - Playback Shutdown

Deletion must stop playback before rendering.

Behavior:

- Stop frontend progress clocks immediately when Delete Region or Backspace is accepted.
- Stop browser audio playback if the graph is using HTML audio.
- Stop Anki native playback through the existing Python session playback shutdown path.
- This must happen even when Repeat is enabled and selected-region playback is looping indefinitely.
- After deletion, playback state is `stopped`.

Acceptance criteria:

- During selected repeat playback, Delete Region or Backspace stops playback and produces one generated audio file.
- No repeat loop restarts while processing is active.
- After graph redraw, Play starts from `0`, matching the existing successful edit behavior.

### FR6 - Cursor, Selection, And Graph State After Success

After deletion, the graph must re-render from the new audio and clear the region selection.

Cursor behavior:

- Successful region deletion resets the cursor to `0`.
- This matches the existing behavior for successful trim, speed, volume, pause-shortening, and denoise edits.

Graph behavior:

- Re-render the graph for the generated audio.
- Clear committed and draft selection.
- Preserve the graph's visible active/open state.
- Busy state clears only after the graph is usable again or a clear graph error is shown.

Acceptance criteria:

- Cursor reset to `0` is verified after button-driven and Backspace-driven deletion.
- Selection is cleared after redraw.
- The graph source filename matches the newly generated filename.

### FR7 - Error Handling

Failure must leave the old field value and graph untouched.

Behavior:

- If rendering, media write, source lookup, or command decoding fails, do not replace the field reference.
- Clear busy state after failure.
- Show a user-visible error notification/status.
- Keep the previous graph and selection so the user can retry or adjust the selection.
- Do not push an Undo entry on failure.

Acceptance criteria:

- Simulated ffmpeg failure leaves the field's sound filename unchanged.
- Existing graph state remains associated with the old source.
- Error status is visible.
- Undo still restores the last successful edit, not the failed attempt.

### FR8 - Undo And Redo

Region deletion must participate in the existing generated-reference history.

Behavior:

- Before successful replacement, push the previous state and filename to Undo history.
- Clear Redo history after a new successful region deletion.
- Undo restores the previous generated/original reference and edit state.
- Redo restores the deleted-region generated reference.
- Undo/Redo should redraw the graph using existing graph redraw behavior.

Acceptance criteria:

- Delete region, Undo restores original duration/filename, Redo restores cut duration/filename.
- Delete region after Undo clears Redo.
- Generated media files remain on disk.

### FR9 - Logging And Diagnostics

Region deletion must use the unified package logger and provide enough diagnostic context to debug failures without exposing noisy or sensitive details in normal operation.

Behavior:

- Log a structured/info-level event when a valid region-delete request is accepted.
- Log the field ordinal, source filename, normalized selection start/end, source duration, trigger type if available (`button` or `backspace`), and whether playback was active when deletion started.
- Log when whole-audio deletion is rejected before rendering, including field ordinal, source filename, selection start/end, and duration. This may be a frontend log when the UI blocks dispatch before Python receives a request.
- Log successful completion with source filename, generated filename, selected duration removed, approximate output duration if available, and elapsed processing time.
- Log failures at warning or error level with exception details and the same request context.
- Do not log raw audio bytes, note contents, or full field HTML.
- Do not show raw ffmpeg commands in user-facing status unless `show_ffmpeg_commands` is enabled. Existing command logging/status behavior for processing actions should remain consistent.
- Frontend logging should use the existing frontend log bridge only for meaningful state transitions or unexpected conditions, such as Backspace ignored because focus is outside the graph, whole-selection rejection, or missing pending payload.
- Avoid high-volume logs during pointer movement, selection draft updates, playback progress frames, or repeat-loop ticks.

Acceptance criteria:

- Successful region deletion produces one concise backend log entry for request start and one for completion.
- Failed region deletion logs enough context to identify source file, selected interval, and failure stage.
- Whole-audio rejection is visible in frontend or backend logs but does not create media, mutate the field, or push Undo history.
- Logs do not include full note HTML or audio payload data.

## 5. Proposed Architecture

### Frontend

Likely files:

- `settings_ui/src/editor-inline/types.ts`
- `settings_ui/src/editor-inline/commands.ts`
- `settings_ui/src/editor-inline/actions.ts`
- `settings_ui/src/editor-inline/selection-controller.ts`
- `settings_ui/src/editor-inline/selection-gestures.ts`
- `settings_ui/src/editor-inline/field-state.ts`
- `settings_ui/src/editor-inline/runtime.ts` or the Svelte component that renders the visualizer.

Implementation notes:

- Add a new editor command, suggested name `aqe:delete-selection`.
- Add a small payload queue similar to playback/cursor intent, suggested shape:

```ts
interface RegionDeleteRequest {
  ord: number;
  sourceFilename: string;
  selectionStartMs: number;
  selectionEndMs: number;
  cursorMs: number;
  durationMs: number;
}
```

- Expose `setPendingRegionDeleteRequest()` and `popPendingRegionDeleteRequest()` in the bridge layer.
- Add a Delete Region control that appears only when the visualizer has a committed selection.
- Make the visualizer focusable with `tabindex="0"` and a focused style that fits the existing UI.
- On graph `keydown`, handle Backspace only when the focused visualizer has a committed selection and is not busy.
- Before dispatching the command, stop progress/audio clocks through existing frontend helpers.
- Set busy status to a processing message immediately to prevent double clicks or double Backspace.
- Clear selection only after Python reports successful graph redraw. On failure, keep it.

### Python Bridge

Likely files:

- `addon/anki_audio_quick_editor/editor_actions.py`
- `addon/anki_audio_quick_editor/editor_integration.py`
- `addon/anki_audio_quick_editor/audio_state.py`
- `addon/anki_audio_quick_editor/audio_processor.py`
- `contracts/` and generated contract files if the project models bridge payloads there.

Implementation notes:

- Register `aqe:delete-selection` in `BRIDGE_COMMANDS`.
- Treat region delete as a processing command in the frontend busy model, but do not map it to a batch operation.
- Add a bridge handler that pops the pending region-delete request from JS and validates it.
- Validate that request `ord` matches the active field and that `selectionStartMs < selectionEndMs`.
- Resolve source path using the same active field/current media logic as existing processing.
- Stop session playback before rendering, using existing `_stop_session_playback(session)`.
- Render asynchronously using the same media-write pattern as `_render_and_replace_async`.
- Replace the current field with the stored filename only after render and media write succeed.
- Push Undo history only in the success replacement path.
- Reset cursor to `0` after successful replacement, consistent with existing processing actions.

### Audio Processing

Implementation options:

1. Extend `AudioEditState` with a list of removed regions, for example `removed_regions: tuple[AudioRegion, ...]`.
2. Add a dedicated render helper, for example `render_audio_region_deleted(...)`, that composes existing state plus one cut operation.

Preferred direction:

- Use a dedicated region deletion operation first if it keeps the existing trim/speed/pause state simpler.
- If future multiple arbitrary cuts are expected, use an immutable region list in `AudioEditState`.

Rendering approach:

- Probe duration with existing `probe_duration_ms`.
- Clamp start/end to `[0, durationMs]`.
- For prefix-only remaining audio, render `atrim=start=<end>`.
- For suffix-only remaining audio, render `atrim=end=<start>`.
- For middle deletion, render two `atrim` streams and `concat=n=2:v=0:a=1`.
- For whole-file deletion, do not render. Reject before ffmpeg is invoked.
- Apply speed/volume state consistently if the operation composes with existing edit state; document and test the ordering.

Suggested render ordering:

1. Start with the current referenced audio file.
2. Remove the selected region in that current timeline.
3. Do not re-apply earlier generated edits that are already baked into the current referenced audio file.

Because existing actions repeatedly replace the field with the latest generated file, the simplest first implementation should treat region deletion as an operation against the current referenced file and reset state source to the generated filename after success, like special transforms do.

## 6. Extensive E2E Test Plan

Add tests under `e2e/`, most likely in a new `e2e/test_editor_region_delete_workflow.py` or near the existing region tests if reuse is cleaner.

Use `python3 scripts/dev.py test-e2e` for final verification. After frontend changes, do not rely on bare `pytest e2e` because the committed editor bundle must be rebuilt.

### E2E Helpers To Add

Add or reuse helpers for:

- Selecting a graph region by ratio.
- Focusing the visualizer.
- Clicking Delete Region.
- Pressing Backspace on the focused visualizer.
- Reading the active graph state.
- Waiting for generated MP3 replacement.
- Probing generated audio duration through `probe_duration_ms`.
- Optionally sampling/validating audio content with ffmpeg for stronger middle-cut verification.

Suggested helpers:

- `_focus_visualizer(editor, ord_=0)`
- `_press_backspace_on_visualizer(editor, ord_=0)`
- `_click_delete_region(editor, ord_=0)`
- `_select_region(editor, start_ratio, end_ratio, ord_=0)`
- `_wait_for_region_delete_result(note, media_dir, previous_name, field_index=0)`

### Core Success Tests - to implement as e2e tests

1. Middle region deletion:
   - Generate a `2.0 s` tone fixture.
   - Open graph, select `0.5 s` to `1.25 s`.
   - Click Delete Region.
   - Verify field filename changed to `__aqe_*.mp3`.
   - Verify source bytes unchanged.
   - Verify generated duration is about `1.25 s`.
   - Verify graph redraw source filename is generated file.
   - Verify selection cleared.
   - Verify cursor reset to `0`.

2. Delete from beginning:
   - Select `0` to `0.4 s`.
   - Verify output duration is about `original - 0.4 s`.
   - Verify cursor resets to `0`.

3. Delete through end:
   - Select `1.4 s` to `2.0 s`.
   - Verify output duration is about `1.4 s`.

4. Reject whole-audio deletion:
   - Select `0` to full duration.
   - Verify Delete Region is unavailable or disabled.
   - Press Backspace while the graph has focus.
   - Verify no generated file, no field change, no graph redraw, and no Undo push.

5. Identical behavior for silence:
   - Generate silence or tone-silence-tone.
   - Delete a silent-only region.
   - Verify duration and field replacement exactly like speech/tone content.

### Focus And Keyboard Tests

6. Delete Region button visibility:
   - Open graph with no selection.
   - Verify Delete Region is hidden.
   - Select a valid region.
   - Verify Delete Region appears and is enabled.
   - Clear the region.
   - Verify Delete Region is hidden again.

7. Backspace ignored when field text has focus:
   - Select a region.
   - Focus the contenteditable field.
   - Press Backspace.
   - Verify no generated file and field sound filename unchanged.

8. Backspace scopes to the focused graph:
   - Two audio fields.
   - Select valid regions in both graphs.
   - Focus field 1 graph and press Backspace.
   - Verify only field 1 changes.
   - Repeat with only field 2 selected and field 1 focused.
   - Verify no field changes.

9. No selection:
   - Open graph and focus it.
   - Press Backspace with no committed selection.
   - Verify no generated file, no busy state stuck, no error required.

10. Draft selection:
   - Start a Shift-drag draft and cancel or avoid committing.
   - Press Backspace.
   - Verify no deletion.

### Playback And Repeat Tests

11. Button stops selected repeat playback:
   - Select a region and enable Repeat.
   - Start playback with HTML audio test driver.
   - Click Delete Region while playback is looping.
   - Verify frontend playback state becomes `stopped` and buttons become busy.
   - Verify no repeat restart occurs.
   - Verify generated file and graph redraw.

12. Backspace stops selected repeat playback:
   - Select a region and enable Repeat.
   - Start playback with HTML audio test driver.
   - Press Backspace while playback is looping.
   - Verify frontend playback state becomes `stopped` and buttons become busy.
   - Verify no repeat restart occurs.
   - Verify generated file and graph redraw.

13. Backspace stops native playback fallback:
   - Force native playback path or fake Anki player.
   - Press Backspace during playback.
   - Verify `stop_and_clear_queue()` is called before or during processing.

### Cursor Reset Tests

14. Cursor before deleted region:
   - Cursor at `0.25 s`, selection `0.75 s` to `1.25 s`.
   - Delete.
   - Verify redrawn cursor is `0`.

15. Cursor inside deleted region:
   - Cursor at `1.0 s`, selection `0.75 s` to `1.25 s`.
   - Delete.
   - Verify redrawn cursor is `0`.

16. Cursor after deleted region:
   - Cursor at `1.75 s`, selection `0.75 s` to `1.25 s`.
   - Delete.
   - Verify redrawn cursor is `0`.

### Undo/Redo Tests

17. Undo and Redo:
   - Delete region.
   - Verify generated duration.
   - Click Undo.
   - Verify previous filename and original duration/graph restored.
   - Click Redo.
   - Verify deleted-region filename/duration restored.

18. New delete after Undo clears Redo:
   - Delete region A.
   - Undo.
   - Delete region B.
   - Click Redo.
   - Verify "Nothing to redo" behavior and filename remains region B output.

### Failure Tests

19. ffmpeg/render failure:
   - Configure invalid ffmpeg path or monkeypatch renderer in an e2e-safe way.
   - Select region and press Backspace.
   - Verify field filename unchanged.
   - Verify old graph source remains.
   - Verify selection remains visible.
   - Verify user-facing error status appears.

20. Missing media:
   - Remove the referenced file before pressing Backspace.
   - Verify non-mutating failure and clear error.

21. Media write failure, if practical:
   - Patch `write_data` to raise.
   - Verify no field replacement and no undo push.

### Multi-Reference And HTML Tests

22. Surrounding HTML preservation:
   - Field contains `<b>Prompt</b> [sound:clip.wav] extra`.
   - Delete region.
   - Verify HTML around `[sound:generated.mp3]` remains.

23. Multiple audio refs in one field:
   - Field contains two sound refs.
   - Open graph for the current supported reference.
   - Delete region.
   - Verify only that opened reference is replaced. If the UI still opens only the first supported ref, assert the first ref changes and the second remains unchanged.

## 7. Unit And Frontend Test Plan

### Python Unit Tests

Add tests in:

- `tests/test_audio_state.py`
- `tests/test_audio_processor.py`
- `tests/test_editor_actions.py`
- `tests/test_editor_integration.py`

Required coverage:

- Region request validation rejects zero/negative duration selections.
- Region clamping accepts start `0` and end `durationMs`.
- Filter command construction for prefix, suffix, and middle deletion.
- Whole-audio deletion validation rejects the operation before rendering.
- Render smoke test with real ffmpeg verifies duration reduction.
- Generated filename still uses existing AQE naming.
- New bridge command is registered.
- Command is not exposed as a batch operation.
- Success path pushes Undo and clears Redo.
- Failure path leaves field/session unchanged.
- Cursor reset behavior matches existing successful processing actions.

### Architecture Tests

Add architecture tests only if implementation introduces new modules, new bridge contracts, or new cross-layer dependencies. Place them under `tests/test_architecture/` and keep them contract-driven like the existing rules.

Required architecture coverage if new source modules are added:

- Region-delete planning helpers must be import-safe and must not import `anki`, `aqt`, Qt, or editor integration modules at module level.
- Audio processing helpers may call ffmpeg through `audio_processor.py`, but must not import Anki APIs or mutate notes/media fields.
- Frontend bridge command registration must stay in sync with Python `BRIDGE_COMMANDS`; add or extend a rule if `aqe:delete-selection` can drift between generated/editor command definitions and Python.
- Region-delete command handling must keep Anki side effects in `editor_integration.py`: media writes, note field replacement, editor reload, playback stop through Anki player, and user-facing status updates.
- The operation must not become a Browser batch operation unless explicitly designed later; architecture tests should catch accidental imports from browser/batch modules into inline-only region-delete code.
- If a typed region-delete payload is added to `contracts/`, generated Python and TypeScript contract outputs must be checked by the existing contracts architecture rules or a new rule specific to editor bridge payloads.

Suggested architecture tests:

- `test_rule_editor_region_delete_boundaries.py`: verifies any new region-delete planning module is classified as import-safe and has no Anki/UI imports.
- Extend `test_rule3_editor_bridge_contract.py`: verifies `aqe:delete-selection` is registered consistently across editor command definitions.
- Extend `test_rule19_shared_operation_contracts.py` only if region delete is modeled as a shared audio operation; otherwise assert it remains editor-only and is not listed in batchable operations.

### Frontend Unit/Integration Tests

Add tests in:

- `settings_ui/tests/editor-inline.actions.test.ts`
- `settings_ui/tests/editor-inline.integration.test.ts`
- `settings_ui/tests/playback-state.test.ts` if cursor/playback region helpers change.

Required coverage:

- Delete Region appears only for committed selections and is enabled only for selections that leave some audio.
- Clicking Delete Region dispatches `aqe:delete-selection`.
- Backspace dispatches `aqe:delete-selection` only when a visualizer is focused and has a committed valid selection.
- Backspace does not dispatch when focus is outside the graph.
- Backspace does not dispatch for draft-only selection.
- Backspace does not dispatch for whole-audio selection.
- Busy state prevents duplicate dispatch.
- Playback clocks stop before dispatch.
- Pending region-delete payload contains ord, source filename, selection, cursor, and duration.
- Selection is preserved on failure status and cleared on successful graph redraw.
- Frontend logging is emitted only for command dispatch/rejection paths, not for high-frequency selection or playback progress updates.

## 8. Documentation Updates

When implementing the feature, update:

- `anki_audio_quick_editor_feature_spec.md`: move "Manual timeline selection" out of out-of-scope where appropriate and add the region delete requirement.
- `E2E_TESTING.md`: add a short "Region Delete Tests" section explaining Delete Region visibility, Backspace focus requirements, full audio verification, and duration tolerance.
- `DEBUGGING.md`: add notes for diagnosing region delete failures, especially graph focus, pending delete payload, and playback stopping.
- Logging/debugging docs should list the expected region-delete log events and the context fields they include.
- `ARCHITECTURE.md`: update the editor processing flow to include arbitrary selected-region deletion if the processing model changes.
- `WEBVIEW_AND_TEMPLATES.md`: if frontend build/test workflow notes change.
- `tests/test_architecture/`: add or extend architecture rules if implementation introduces new modules, new contracts, or new layer boundaries.
- Contract documentation or generated contract notes if a typed bridge payload is added under `contracts/`.

If the implementation changes schema, hooks, package boundaries, or architecture rules, run the `$doc-maintain` workflow afterward.

## 9. Implementation Checklist

Before editing code:

- Read `WEBVIEW_AND_TEMPLATES.md` before editing `settings_ui` or committed editor bundles.
- Read `ANKI_API.md` before changing Anki bridge/media/player behavior.

Suggested order:

1. Add failing Python unit tests for region planning, render duration, command registration, success, and failure.
2. Add failing frontend tests for Delete Region visibility/click behavior, focused Backspace dispatch, whole-audio rejection, and payload handling.
3. Add architecture tests if the design introduces new modules, new contracts, or new cross-layer dependencies.
4. Add failing e2e tests for the core success path and repeat-playback stop behavior.
5. Implement the audio processing helper.
6. Implement Python bridge command handling and success/failure session updates.
7. Implement frontend focus, key handling, pending payload, and busy/playback shutdown.
8. Add remaining e2e corner cases.
9. Rebuild frontend bundles through the dev runner.
10. Run targeted tests, then `python3 scripts/dev.py check`.
11. Run `python3 scripts/dev.py test-e2e`.

## 10. Open Implementation Decisions

These should be resolved during implementation:

- Whether to model region deletion in `AudioEditState` or as a one-shot transform against the current referenced file.
- Whether multiple audio references in one field need a new "opened reference" identity beyond the current first-supported-reference behavior.
- Whether the user-facing error appears only in inline status or also through Anki's notification mechanism.
