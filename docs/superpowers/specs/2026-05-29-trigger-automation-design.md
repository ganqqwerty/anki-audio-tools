# Trigger Automation Design

## Summary

Add automatic trigger rules that run Audio Quick Editor operations after manual note add/edit workflows. V1 targets Add Cards plus normal editor saves from Edit Current and the Browser editor. Imports, browser bulk operations, sync, and third-party collection updates are explicitly out of scope for the first version.

Triggers reuse the existing batch operation core through a headless one-note runner. The trigger layer owns automation policy: matching rules, detecting changed source audio, background scheduling, stale-completion guards, Graph replacement semantics, and loop prevention.

## Goals

- Let users configure per-note-type trigger rules in Settings.
- Support manual `add` and manual `edit` trigger events.
- Run one configured operation per rule.
- Support existing batch-capable operations: Graph, Convert, Denoise, Shorten Pauses, Slower, Faster, Volume Down, and Volume Up.
- Store operation parameters on each trigger rule so automatic behavior is reproducible and independent of later global default changes.
- Run triggers in the background so Add/Edit saves are not blocked.
- Run when the selected source field's first supported sound reference changes.
- Use latest-wins behavior when a note/field/rule changes again while processing is still running.
- Keep user notes clean by storing trigger state in an add-on sidecar store, not hidden fields or tags.
- Prevent trigger-initiated note updates from scheduling the same rule again.

## Non-Goals

- Triggering from imports, Browser bulk edits, sync, add-ons, or arbitrary collection operations.
- Multi-step trigger chains. Pipelines will cover grouped operations later.
- Triggering toolbar-only actions such as Play, Share, Record, Show File, Undo, Redo, Pitch Hum, Delete Selection, or Delete Rest.
- Blocking Add/Edit saves until processing finishes.
- Editing note types to add hidden tracking fields.
- Appending Graph output from triggers. Trigger Graph output replaces its target field in V1.
- Per-rule scheduling windows, debounce controls, or retry policies.

## User Experience

Settings gets a dedicated `Triggers` tab alongside General and Diagnostics. The tab contains a compact table of trigger rules plus add/edit/delete controls.

Each rule exposes:

- enabled toggle
- name
- event: `add` or `edit`
- note type
- source field
- operation
- operation parameters
- target field, required only for Graph

The rule editor should use the same operation parameter controls as batch/pipeline work where practical. Users can disable a rule without deleting it.

When a user manually adds or edits a note, the add-on saves immediately. Matching triggers run in the background. On success, the note updates after the generated media is ready. On failure, the note remains unchanged and the add-on records diagnostics; user-facing feedback should be concise, such as a tooltip or non-blocking status message.

## Saved Rule Model

Add a schema-backed `audio_trigger_rules` array to config. Existing configs migrate to an empty array.

```json
{
  "id": "trigger_clean_basic_audio",
  "name": "Clean Basic audio on add",
  "enabled": true,
  "event": "add",
  "note_type": {
    "id": 1234567890,
    "name": "Basic"
  },
  "source_field": "Audio",
  "operation": "remove_pauses",
  "target_field": null,
  "parameters": {
    "pause_aggressiveness": "normal",
    "pause_detection_algorithm": "silencedetect",
    "pause_threshold": -45.0,
    "pause_min_silence_seconds": 0.3,
    "pause_min_speech_seconds": 0.1,
    "pause_preprocess_denoise": true
  }
}
```

For Graph:

```json
{
  "id": "trigger_graph_basic_audio",
  "name": "Graph Basic audio on edit",
  "enabled": true,
  "event": "edit",
  "note_type": {
    "id": 1234567890,
    "name": "Basic"
  },
  "source_field": "Audio",
  "operation": "graph",
  "target_field": "Graph",
  "parameters": {
    "graph_voice_range": "general",
    "graph_recording_condition": "auto",
    "graph_smoothness": "very_smooth",
    "graph_connect_short_dropouts_ms": 240,
    "graph_voice_lock": "balanced"
  }
}
```

Validation rules:

- rule IDs are unique
- names are nonempty after trimming
- event is `add` or `edit`
- operation is one of the supported batch operations
- note type is selected
- source field is nonempty
- Graph rules require a target field
- non-Graph rules must not write a separate target field
- operation parameters are valid for the selected operation
- disabled rules still validate enough to preserve data shape, but missing note types or fields should be surfaced as inactive/unrunnable in the UI instead of crashing Settings

Prefer stable notetype IDs for matching when available. Store the note type name as display metadata and as a fallback when Anki APIs or tests provide only names. If a stored ID no longer resolves, the rule becomes inactive until the user repairs it.

## Sidecar State Model

Store trigger state outside user notes under the add-on data/artifact area. The store is keyed by collection identity, note id, rule id, and source field.

Each entry records:

- last handled field filename
- input filename that caused the latest run
- latest generation token
- processing state: idle, running, succeeded, failed
- last successful output filename, when applicable
- timestamp and last error summary for diagnostics

The sidecar store is not the source of note content. It only prevents repeated processing and stale completions. If the store is missing, the current note filename is treated as unhandled and matching rules may schedule processing.

Cleanup can be conservative in V1. Entries for deleted notes may remain until a later maintenance pass. They should be small JSON records and must not block normal operation.

## Architecture

Add a new startup hook next to editor and browser integration:

- `trigger_integration.py`: Anki hook registration and event classification.
- `trigger_rules.py`: config-backed trigger rule model, validation, matching, and parameter conversion.
- `trigger_state.py`: sidecar load/save/update helpers.
- `trigger_runner.py`: queueing, background execution, latest-wins policy, stale-completion checks, and note updates.
- `trigger_batch_adapter.py`: conversion from trigger rules to one-note batch execution, including Graph replacement semantics.

Existing modules remain the source of operation behavior:

- `audio_operations.py` defines supported operation names.
- `audio_operation_params.py` validates operation parameters.
- `batch_operation_types.py` provides `BatchRunRequest` and note result shapes where they fit.
- `batch_operations.py` provides the import-safe one-note operation core.
- `browser_batch_runner.py` provides useful snapshot/update patterns, but trigger runner should avoid browser-dialog assumptions.

The trigger layer should not call editor bridge commands. Editor commands depend on active UI state, field ordinals, playback, graph UI state, and undo/redo behavior, which are the wrong abstraction for background note automation.

## Anki Hook Integration

Add triggers are detected through `gui_hooks.add_cards_did_add_note(note)`. This hook runs after Add Cards successfully adds a note.

Edit triggers are detected through `gui_hooks.operation_did_execute(changes, handler)`, restricted to normal editor saves:

- `changes.note` or `changes.note_text` must indicate note content changed.
- `handler` must look like an Anki editor instance.
- Add Cards editor saves are excluded from the edit path because add triggers handle those notes.
- Trigger-initiated updates are excluded by passing/recording a trigger initiator object and by checking the sidecar generation token.

This intentionally excludes imports, bulk Browser operations, sync, and other add-ons in V1. If a future version expands the source scope, it should add explicit event classification rather than loosening this filter.

## Matching And Change Detection

For each candidate event:

1. Load enabled rules for the event.
2. Match the note type by stable ID when possible, with name fallback only when needed.
3. Check that the source field exists.
4. Extract the first supported `[sound:...]` reference from the source field.
5. Compare that filename with the sidecar entry for the note/rule/source field.
6. Schedule processing only when the filename differs from the last handled field filename.

For transform operations, the generated filename becomes the field's current sound reference after success. The state store records the input filename that caused the run, the generated output filename, and sets the last handled field filename to the generated output filename. That prevents later text-only edits from reprocessing the generated file.

For Graph, the source field remains unchanged. The state store sets the last handled field filename to the analyzed source filename so unrelated text edits do not regenerate the graph.

## Execution Semantics

Trigger jobs run in the background. Add/Edit saves return immediately.

Each scheduled job carries:

- note id
- rule id
- source field
- observed source filename
- generation token
- event type

Before writing results, the runner reloads the note and verifies:

- the rule is still enabled and still matches the note type
- the sidecar token is still the latest for this note/rule/source field
- the source field still contains the same observed source filename as its first supported sound reference
- the target field still exists for Graph

If any check fails, the completion is stale and must not mutate the note.

Latest-wins behavior:

- A new matching change for the same note/rule/source field supersedes older queued or running jobs by writing a newer generation token to the sidecar store.
- Older jobs may finish their media rendering, but their completion checks fail and they do not update the note.
- The implementation may avoid starting obsolete queued jobs when it sees a newer token before execution begins.

## Operation Behavior

Audio transforms use existing batch transform semantics:

- source media is not overwritten or deleted
- generated media is written to Anki media
- the source field's first supported sound reference is replaced with the generated filename
- failure leaves the note field unchanged

Graph trigger behavior intentionally differs from current Browser batch Graph behavior:

- Graph analyzes the configured source field audio.
- Graph writes an SVG media reference into the configured target field.
- The target field is replaced, not appended.
- Failure leaves the target field unchanged.

The trigger-specific Graph replacement adapter should be small and covered by tests. It should not change Browser batch Graph append behavior.

## Error Handling And Feedback

Expected skip cases should not be treated as crashes:

- disabled rule
- unresolved note type
- missing source field
- empty source field
- no supported sound reference
- stale completion
- missing Graph target field

Failures that happen during rendering, media writing, or note update should be logged through the existing diagnostics runtime with enough context to identify the rule, note id, operation, and field names.

User-facing feedback should be non-blocking. The first version can use concise tooltips for failures and success summaries. Detailed per-note logs belong in diagnostics, not modal dialogs.

## Settings UI Details

Settings adds a `Triggers` tab. Suggested Svelte modules:

- `TriggerSettingsPanel.svelte`
- `TriggerRuleTable.svelte`
- `TriggerRuleEditor.svelte`
- `TriggerOperationParameters.svelte`
- `trigger-settings-state.ts`

The table should show rule name, event, note type, source field, operation, target field where relevant, and enabled state. The editor should validate before Save and show inactive/unrunnable states when a referenced note type or field cannot be found.

The UI should use existing Settings styling, Anki theme variables, and `AqeTooltip` for live tooltips. Use stable `data-testid` attributes for e2e tests.

## Config And Contracts

Adding trigger rules touches the schema-backed config path:

- `addon/anki_audio_quick_editor/config.schema.json`
- default `config.json`
- config migration defaults
- generated Python and TypeScript contracts
- settings initial-state fixtures
- Settings save sanitization
- e2e default-config helpers

The Python backend remains authoritative for validation. Frontend validation should guide users before Save but must not be trusted as the only guard.

## Testing

Unit tests:

- config migration adds `audio_trigger_rules: []`
- schema accepts valid transform and Graph rules
- schema rejects invalid events, operations, missing source field, and missing Graph target field
- rule matching respects note type, event, enabled state, and field names
- sidecar state detects changed sound references and suppresses unchanged references
- latest-wins tokens reject stale completions
- trigger-initiated updates do not reschedule the same rule
- Graph trigger replaces target field instead of appending
- transform trigger replaces the source field sound reference and preserves surrounding HTML
- stale completion does not update a note after the source sound changed

Anki API compatibility tests:

- hook signatures for `add_cards_did_add_note` and `operation_did_execute`
- editor-save handler classification against installed Anki 25.09 APIs

Settings tests:

- Triggers tab renders with empty rules
- add/edit/delete/enable/disable rule flows
- operation-specific parameter controls save expected config
- Graph target field is required
- invalid rules block save with clear feedback

E2E tests:

- Add Cards with a matching transform trigger saves immediately and later updates the note audio field.
- Edit Current or Browser editor with a changed source sound schedules a trigger.
- Unrelated text edits do not rerun the rule when the sound reference is unchanged.
- Quick repeated edits use latest-wins behavior.
- Graph trigger replaces the configured target field.

Full completion requires `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e`.

## Open Implementation Notes

- Confirm the most reliable way to classify Edit Current versus Browser editor saves from `operation_did_execute` handlers during implementation.
- Decide the exact sidecar filename and collection identity key after checking available Anki collection metadata.
- Decide whether success feedback should be a tooltip, log-only, or both after seeing how noisy trigger runs are in e2e.
