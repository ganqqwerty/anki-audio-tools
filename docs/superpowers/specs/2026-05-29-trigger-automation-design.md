# Trigger Automation Design

## Summary

Add automatic trigger rules that run Audio Quick Editor processing after manual note add/edit workflows. V1 targets Add Cards plus normal editor saves from Edit Current and the Browser editor. Imports, browser bulk operations, sync, and third-party collection updates are explicitly out of scope for the first version.

Triggers reuse the existing batch operation core and the processing preset runner through a headless one-note runner. The trigger layer owns automation policy: matching rules, detecting changed source audio, background scheduling, stale-completion guards, Graph replacement semantics, and loop prevention.

## Current Baseline

As of 2026-06-13, trigger automation is still design-stage, but processing presets have landed in config, Settings, editor, Browser batch, and the shared preset runner. Trigger implementation should therefore add the Triggers tab to the current Settings layout alongside General, Presets, and Diagnostics, and should reuse the existing preset model and runner instead of inventing a second preset path.

The shared batch/editor operation surface has changed since the original design. `audio_operations.py` now includes `reduce_size` as a transform operation backed by size-reduction parameters and `render_size_reduced_audio`. Trigger single-operation allow-lists and parameter editors must include it. Current preset Settings/schema code still omits `reduce_size` from preset steps even though the backend transform list includes it; broadening preset-step parity should be handled as a focused prerequisite or follow-up, not hidden inside trigger automation.

## Goals

- Let users configure per-note-type trigger rules in Settings.
- Support manual `add` and manual `edit` trigger events.
- Run one configured action per rule: either a single batch-capable operation or a saved processing preset.
- Support existing batch-capable operations: Graph, Convert, Size Reduction, Denoise, Shorten Pauses, Slower, Faster, Volume Down, and Volume Up.
- Support processing presets when `audio_processing_presets` and the shared preset runner are available.
- Store parameters on single-operation trigger rules so automatic behavior is reproducible and independent of later global default changes.
- Reference processing presets by ID instead of copying preset steps into trigger rules.
- Run triggers in the background so Add/Edit saves are not blocked.
- Run when the selected source field's first supported sound reference changes, or when the configured action fingerprint changes for a later add/edit event.
- Use latest-wins behavior when a note/field/rule changes again while processing is still running.
- Keep user notes clean by storing trigger state in an add-on sidecar store, not hidden fields or tags.
- Prevent trigger-initiated note updates from scheduling the same rule again.

## Non-Goals

- Triggering from imports, Browser bulk edits, sync, add-ons, or arbitrary collection operations.
- Multi-step trigger chains embedded directly in trigger rules. Processing presets cover grouped operations.
- Triggering toolbar-only or editor-session actions such as Play, Share, Record, Play Recording, Share Recording, Show File, Show Recording File, Chorusing Practice/Next/Previous, Undo, Redo, Pitch Hum, Delete Selection, or Delete Rest.
- Blocking Add/Edit saves until processing finishes.
- Editing note types to add hidden tracking fields.
- Appending Graph output from triggers. Trigger Graph output replaces its target field in V1.
- Per-rule scheduling windows, debounce controls, or retry policies.

## User Experience

Settings gets a dedicated `Triggers` tab alongside General, Presets, and Diagnostics. The tab contains a compact table of trigger rules plus add/edit/delete controls.

Each rule exposes:

- enabled toggle
- name
- event: `add` or `edit`
- note type
- source field
- action type: single operation or processing preset
- operation and operation parameters, for single-operation rules
- preset, for preset rules
- target field, required when the action emits Graph output

The rule editor should use the same operation parameter controls as batch/preset work where practical. Users can disable a rule without deleting it.

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
  "action_type": "operation",
  "operation": "remove_pauses",
  "preset_id": null,
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
  "action_type": "operation",
  "operation": "graph",
  "preset_id": null,
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

For Size Reduction:

```json
{
  "id": "trigger_smaller_basic_audio",
  "name": "Compress Basic audio on add",
  "enabled": true,
  "event": "add",
  "note_type": {
    "id": 1234567890,
    "name": "Basic"
  },
  "source_field": "Audio",
  "action_type": "operation",
  "operation": "reduce_size",
  "preset_id": null,
  "target_field": null,
  "parameters": {
    "size_reduction_mode": "normal",
    "size_reduction_bitrate_kbps": 64,
    "size_reduction_sample_rate_hz": 32000,
    "size_reduction_channels": 1
  }
}
```

For a processing preset:

```json
{
  "id": "trigger_preset_basic_audio",
  "name": "Clean preset on add",
  "enabled": true,
  "event": "add",
  "note_type": {
    "id": 1234567890,
    "name": "Basic"
  },
  "source_field": "Audio",
  "action_type": "preset",
  "operation": null,
  "preset_id": "preset_clean_graph",
  "target_field": "Graph",
  "parameters": {}
}
```

Validation rules:

- rule IDs are unique
- names are nonempty after trimming
- event is `add` or `edit`
- action type is `operation` or `preset`
- note type is selected
- source field is nonempty
- operation rules require an operation from the supported batch operation list
- operation rule parameters are valid for the selected operation
- preset rules require a valid `preset_id`
- preset rules do not duplicate preset step parameters; the referenced preset remains the parameter owner
- actions that emit Graph output require a target field
- actions that do not emit Graph output must not write a separate target field
- preset rules whose referenced preset changes to require a missing Graph target become inactive until repaired
- disabled rules still validate enough to preserve data shape, but missing note types or fields should be surfaced as inactive/unrunnable in the UI instead of crashing Settings

Prefer stable notetype IDs for matching when available. Store the note type name as display metadata and as a fallback when Anki APIs or tests provide only names. If a stored ID no longer resolves, the rule becomes inactive until the user repairs it.

Preset rules use the referenced preset definition at execution time. If a preset ID no longer resolves, the rule becomes inactive until the user selects another preset. Editing a preset changes future trigger executions but does not proactively rerun existing notes; matching still happens on later add/edit events.

## Sidecar State Model

Store trigger state outside user notes under the add-on data/artifact area. The store is keyed by collection identity, note id, rule id, and source field.

Each entry records:

- last handled field filename
- input filename that caused the latest run
- action fingerprint for the rule or referenced preset used by the latest run
- latest generation token
- processing state: idle, running, succeeded, failed
- last successful output filename, when applicable
- timestamp and last error summary for diagnostics

The sidecar store is not the source of note content. It only prevents repeated processing and stale completions. If the store is missing, the current note filename is treated as unhandled and matching rules may schedule processing.

The action fingerprint is derived from the rule's selected action. For operation rules, it includes the operation and normalized parameters. For preset rules, it includes the preset ID and a stable hash or revision of the referenced preset definition. A changed action fingerprint is treated as unhandled on the next matching add/edit event, but editing a rule or preset does not schedule work by itself.

Cleanup can be conservative in V1. Entries for deleted notes may remain until a later maintenance pass. They should be small JSON records and must not block normal operation.

## Architecture

Add a new startup hook next to editor and browser integration:

- `trigger_integration.py`: Anki hook registration and event classification.
- `trigger_rules.py`: config-backed trigger rule model, validation, matching, and parameter conversion.
- `trigger_state.py`: sidecar load/save/update helpers.
- `trigger_runner.py`: queueing, background execution, latest-wins policy, stale-completion checks, and note updates.
- `trigger_batch_adapter.py`: conversion from operation trigger rules to one-note batch execution, including Graph replacement semantics.
- `trigger_preset_adapter.py`: conversion from preset trigger rules to shared preset runner execution and trigger-specific note field writes.

Existing modules remain the source of operation behavior:

- `audio_operations.py` defines supported operation names.
- `audio_operation_params.py` validates operation parameters.
- `audio_size_reduction.py` owns size-reduction modes and encoder parameter normalization.
- `batch_operation_types.py` provides `BatchRunRequest` and note result shapes where they fit.
- `batch_operations.py` provides the import-safe one-note operation core.
- `audio_processing_presets.py` will provide saved preset model and validation when processing presets land.
- `audio_processing_preset_runner.py` will provide shared staged preset execution when processing presets land.
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
5. Resolve the rule action. Preset rules resolve the current preset definition.
6. Compare the filename and action fingerprint with the sidecar entry for the note/rule/source field.
7. Schedule processing only when the filename differs from the last handled field filename or the action fingerprint differs from the last handled fingerprint.

For transform operation rules, the generated filename becomes the field's current sound reference after success. The state store records the input filename that caused the run, the generated output filename, and sets the last handled field filename to the generated output filename. That prevents later text-only edits from reprocessing the generated file.

For preset rules with transform steps, the final generated audio filename becomes the field's current sound reference after success. The state store uses the final generated filename as the last handled field filename, matching single-operation transform behavior.

For Graph-only operation rules or Graph-only preset rules, the source field remains unchanged. The state store sets the last handled field filename to the analyzed source filename so unrelated text edits do not regenerate the graph.

## Execution Semantics

Trigger jobs run in the background. Add/Edit saves return immediately.

Each scheduled job carries:

- note id
- rule id
- source field
- observed source filename
- action type and action fingerprint
- generation token
- event type

Before writing results, the runner reloads the note and verifies:

- the rule is still enabled and still matches the note type
- the rule still resolves to the same action fingerprint
- the sidecar token is still the latest for this note/rule/source field
- the source field still contains the same observed source filename as its first supported sound reference
- the target field still exists when the action emits Graph output

If any check fails, the completion is stale and must not mutate the note.

Latest-wins behavior:

- A new matching change for the same note/rule/source field supersedes older queued or running jobs by writing a newer generation token to the sidecar store.
- Older jobs may finish their media rendering, but their completion checks fail and they do not update the note.
- The implementation may avoid starting obsolete queued jobs when it sees a newer token before execution begins.

## Action Behavior

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

Preset trigger behavior uses the shared processing preset runner:

- transform steps run through the preset runner and produce one final audio output
- if the preset has transform steps, the source field's first supported sound reference is replaced with the final generated audio
- if the preset has terminal Graph enabled, Graph analyzes the final audio when transforms exist, otherwise the original source audio
- preset Graph output replaces the trigger target field, not appends
- preset failure leaves all note fields unchanged
- preset parameters remain owned by the preset definition; trigger rules only select the preset and graph target field when needed

Size Reduction trigger behavior follows existing batch transform semantics:

- the operation always writes MP3 output when it produces a new file
- rule parameters include `size_reduction_mode`, `size_reduction_bitrate_kbps`, `size_reduction_sample_rate_hz`, and `size_reduction_channels`
- if the renderer reports that the source is already compact, the trigger records a skipped result and marks the current field filename handled so unrelated text edits do not repeatedly retry the same compact source

## Error Handling And Feedback

Expected skip cases should not be treated as crashes:

- disabled rule
- unresolved note type
- missing source field
- empty source field
- no supported sound reference
- unresolved preset
- stale completion
- missing Graph target field
- already-compact Size Reduction source

Failures that happen during rendering, media writing, or note update should be logged through the existing diagnostics runtime with enough context to identify the rule, note id, action, and field names.

User-facing feedback should be non-blocking. The first version can use concise tooltips for failures and success summaries. Detailed per-note logs belong in diagnostics, not modal dialogs.

## Settings UI Details

Settings adds a `Triggers` tab. Suggested Svelte modules:

- `TriggerSettingsPanel.svelte`
- `TriggerRuleTable.svelte`
- `TriggerRuleEditor.svelte`
- `TriggerOperationParameters.svelte`
- `trigger-settings-state.ts`

The table should show rule name, event, note type, source field, action summary, target field where relevant, and enabled state. The editor should validate before Save and show inactive/unrunnable states when a referenced note type, field, or preset cannot be found.

For operation rules, the editor shows operation-specific parameter controls and stores normalized parameters on the rule. For preset rules, the editor shows a preset selector plus a read-only summary of the selected preset's steps and terminal Graph state. Preset rules do not expose per-step parameter editors; users edit those in the Presets tab.

The UI should use existing Settings styling, Anki theme variables, and `AqeTooltip` for live tooltips. Use stable `data-testid` attributes for e2e tests.

## Config And Contracts

Adding trigger rules touches the schema-backed config path:

- `addon/anki_audio_quick_editor/config.schema.json`
- default `config.json`
- config migration defaults, starting from the current config version 2 baseline
- `audio_processing_presets` config and contracts, because preset rules reference saved presets by ID
- generated Python and TypeScript contracts
- settings initial-state fixtures
- Settings save sanitization
- e2e default-config helpers

The trigger schema must include the current Size Reduction parameter keys in `AudioOperationParameters`: `size_reduction_mode`, `size_reduction_bitrate_kbps`, `size_reduction_sample_rate_hz`, and `size_reduction_channels`.

The Python backend remains authoritative for validation. Frontend validation should guide users before Save but must not be trusted as the only guard.

## Testing

Unit tests:

- config migration adds `audio_trigger_rules: []`
- schema accepts valid transform and Graph rules
- schema accepts valid Size Reduction rules
- schema accepts valid preset rules
- schema rejects invalid events, operations, missing source field, and missing Graph target field
- schema rejects preset rules with missing preset IDs
- rule matching respects note type, event, enabled state, and field names
- sidecar state detects changed sound references and suppresses unchanged references
- sidecar state detects changed action fingerprints
- latest-wins tokens reject stale completions
- trigger-initiated updates do not reschedule the same rule
- Graph trigger replaces target field instead of appending
- preset trigger replaces source audio with final preset audio
- preset trigger replaces terminal Graph target field instead of appending
- Size Reduction trigger writes MP3 output and marks already-compact sources handled after a skipped result
- transform trigger replaces the source field sound reference and preserves surrounding HTML
- stale completion does not update a note after the source sound changed

Anki API compatibility tests:

- hook signatures for `add_cards_did_add_note` and `operation_did_execute`
- editor-save handler classification against installed Anki 25.09 APIs

Settings tests:

- Triggers tab renders with empty rules
- add/edit/delete/enable/disable rule flows
- operation-specific parameter controls save expected config
- preset selector saves preset rule references without copying preset steps
- Graph target field is required
- invalid rules block save with clear feedback

E2E tests:

- Add Cards with a matching transform trigger saves immediately and later updates the note audio field.
- Edit Current or Browser editor with a changed source sound schedules a trigger.
- Unrelated text edits do not rerun the rule when the sound reference and action fingerprint are unchanged.
- Quick repeated edits use latest-wins behavior.
- Graph trigger replaces the configured target field.
- Preset trigger runs the referenced preset and uses trigger Graph replacement semantics.
- Size Reduction trigger uses the configured compression parameters and does not repeatedly retry already-compact audio on text-only edits.

Full completion requires `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e`.

## Open Implementation Notes

- Confirm the most reliable way to classify Edit Current versus Browser editor saves from `operation_did_execute` handlers during implementation.
- Decide the exact sidecar filename and collection identity key after checking available Anki collection metadata.
- Decide the preset action fingerprint source during implementation: explicit preset revision, content hash, or config save version.
- Decide whether success feedback should be a tooltip, log-only, or both after seeing how noisy trigger runs are in e2e.
