# Delete The Rest Button Design

## Goal

Add a **Delete the rest** button to the inline editor graph controls. The button appears only when the user has selected a graph region. Clicking it keeps the selected audio and removes everything before and after the selection.

This is the complement of the existing **Delete Region** behavior:

- **Delete Region** removes the selected interval.
- **Delete the rest** keeps only the selected interval.

Both actions must use the same non-destructive editing model: generate a new media file, update the note field to reference it, leave the previous media file untouched, redraw the graph, and allow Undo to restore the previous field reference.

## Current Context

The inline editor already supports graph selection and region deletion:

- `settings_ui/src/editor-inline/selection-state.ts` validates and normalizes selected ranges.
- `settings_ui/src/editor-inline/selection-controller.ts` stores committed selection state on the visualizer dataset.
- `settings_ui/src/editor-inline/region-delete-state.ts` controls **Delete Region** visibility and builds the frontend request.
- `settings_ui/src/editor-inline/region-delete.ts` queues the frontend request, stops playback, marks controls busy, and sends `aqe:delete-selection` to Python.
- `addon/anki_audio_quick_editor/editor_region_delete.py` validates the request, renders the generated file, replaces the sound reference, updates Undo/Redo state, and requests graph redraw.
- `addon/anki_audio_quick_editor/audio_commands.py` builds the ffmpeg filter plan for deleting the selected interval.

The new feature should extend this existing flow rather than introduce a separate bridge or replacement path.

## Chosen UX

Use two adjacent revealed buttons.

When no graph region is selected, no selection-delete buttons are visible. When an active graph region exists, the controls reveal:

- **Delete Region**
- **Delete the rest**

The new button label is exactly **Delete the rest**.

The action is button-only. Backspace remains mapped to **Delete Region**. **Delete the rest** does not get a keyboard shortcut in this pass.

Clicking **Delete the rest** executes immediately with no confirmation dialog. This matches the existing generated-file workflow and relies on Undo for recovery.

## Selection Semantics

**Delete the rest** keeps only the committed selected interval.

Examples:

- Selecting `500ms -> 1250ms` from a `2000ms` clip produces an output clip of about `750ms`.
- Selecting `0ms -> 1200ms` keeps the first `1200ms`.
- Selecting `3000ms -> end` keeps the tail from `3000ms` to the original end.

After a successful render:

- playback is stopped,
- the field references the generated file,
- graph redraw is requested for the generated file,
- selection is cleared,
- cursor resets to `0ms`,
- playback region resets to the full new clip.

Whole-clip selection is treated as unavailable. The frontend may show the revealed button in a disabled state for the active selection, and Python must reject it as a no-op fallback. It should not regenerate media.

## Architecture

Add a second operation to the existing region-delete pipeline.

The frontend request should include an operation discriminator so Python can distinguish:

- remove selected interval,
- keep selected interval.

The exact naming can be chosen during implementation, but the contract should be explicit and closed over the known operations. For example, an operation value such as `delete_selection` can preserve current behavior and `delete_rest` can represent the new behavior.

Shared behavior remains in the existing pipeline:

- request parsing and normalization,
- active field validation,
- source filename validation,
- current media validation,
- busy state,
- playback stop,
- generated filename creation,
- output write to Anki media,
- note field replacement,
- Undo/Redo history update,
- graph redraw,
- frontend status rendering,
- failure handling.

The operation-specific behavior is the ffmpeg plan:

- **Delete Region** keeps the current concat/trim plan that removes the selected interval.
- **Delete the rest** uses a single trim from `selectionStartMs` to `selectionEndMs`, then resets timestamps to start at `0ms`.

## Data Flow

Frontend selection state remains the source of truth for the selected interval.

The request builder should produce a selection operation request only when:

- there is an active committed selection,
- `selectionEndMs > selectionStartMs`,
- duration is known,
- a source filename is present,
- the operation is recognized.

For **Delete Region**, whole-clip selection remains invalid because it would produce empty audio.

For **Delete the rest**, whole-clip selection is invalid because it changes nothing and should not create another generated file.

Python must re-validate the full request before rendering:

- payload is a dictionary,
- field index is non-negative,
- duration is positive,
- selection bounds are numeric and clamped into duration,
- selection is non-empty,
- source filename is a safe media basename,
- operation is recognized,
- active field matches the request,
- current field media still matches the requested source filename,
- operation-specific no-op or empty-output cases are rejected.

If validation fails after a click, the UI should leave busy state and show a warning or error without changing the note.

## Audio Rendering

The existing region-delete plan removes the selected interval by trimming the audio before and after the selection and concatenating those parts.

The new keep-selection plan should render:

```text
[0:a]atrim=start=<selectionStartSeconds>:end=<selectionEndSeconds>,asetpts=PTS-STARTPTS[out]
```

The output duration should be approximately:

```text
selectionEndMs - selectionStartMs
```

Encoder tolerance should be handled the same way existing duration assertions handle generated MP3 output.

## Accessibility And Labels

The button title and accessible label should match the visible action:

- visible label: `Delete the rest`
- title: `Delete the rest of the audio`
- aria-label: `Delete the rest of the audio`

The existing button styling and dark/light mode behavior should be reused. The new button should not introduce a new visual hierarchy beyond sitting beside **Delete Region** as another selection-scoped operation.

## Considered Alternatives

### Separate Trim-To-Selection Pipeline

A separate backend path would make the new behavior independently named, but it would duplicate validation, media replacement, Undo/Redo handling, graph redraw, and error recovery. It was rejected because this feature is a sibling of **Delete Region**, not a new subsystem.


The action could be modeled as trimming right to the selection end and trimming left to the selection start. This was rejected because it would likely generate multiple files, create multiple Undo entries, and make redraw/status behavior harder to reason about.

### Menu Or Positive Label

A split menu and a **Keep Selection** label were considered. The chosen design uses a second revealed button labeled **Delete the rest** because it is discoverable, matches the requested wording, and pairs clearly with **Delete Region**.

## Testing

Use test-first implementation where practical.

### TypeScript Tests

Add or update frontend tests for:

- **Delete the rest** stays hidden when no selection exists.
- **Delete the rest** appears when a valid selection exists.
- **Delete the rest** becomes disabled or unavailable when the app is busy.
- **Delete the rest** is unavailable for whole-clip selection.
- Request payload includes the keep-selection operation.
- Backspace continues to send only the existing **Delete Region** operation.
- Button click sets busy state and queues the request.

### Python Unit Tests

Add parser and rendering-plan coverage for:

- recognized operation values,
- unknown operation rejection,
- middle selection keep plan,
- start-edge selection keep plan,
- end-edge selection keep plan,
- empty selection rejection,
- whole-clip keep-selection rejection,
- source filename sanitization still applies,
- active/current media mismatch still prevents mutation.

### E2E Tests

Add a workflow test mirroring the existing region-delete e2e case:

- generate a `2s` tone,
- graph it,
- select roughly `500ms -> 1250ms`,
- click **Delete the rest**,
- confirm the original source bytes are unchanged,
- confirm the note references a generated file,
- confirm generated duration is about `750ms`,
- confirm graph redraws for the generated file,
- confirm selection is cleared,
- confirm cursor is `0ms`,
- confirm playback is stopped.

If an Undo e2e helper is already available, include a focused assertion that Undo restores the previous field reference. If not, keep Undo covered through the shared backend/session behavior and avoid expanding e2e scope just for helper creation.

## Risks

The main product risk is accidental confusion between two opposite operations shown at the same time. The design mitigates this by using clear labels and leaving Backspace mapped only to **Delete Region**.

The main implementation risk is creating divergent behavior between **Delete Region** and **Delete the rest**. The design avoids this by sharing the existing request validation, generated-file replacement, Undo/Redo, graph redraw, and error handling.

The audio-rendering risk is off-by-one or encoder tolerance around selection bounds. Tests should assert practical duration ranges rather than exact MP3 duration equality.

## Out Of Scope

- Keyboard shortcut for **Delete the rest**.
- Confirmation dialog.
- Persistent user preference for hiding or showing selection operation buttons.
- Multi-region selection.
- Silence-padding behavior that preserves original timeline position.
- Regenerating media for whole-clip selection.
