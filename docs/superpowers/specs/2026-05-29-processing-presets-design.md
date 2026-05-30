# Processing Presets Design

## Summary

Add a Settings-based processing preset constructor for named audio processing recipes. A preset is a saved sequence of shared audio transform operations plus an optional terminal Graph output. Presets are available from both the inline editor and Browser batch dialog.

The design uses a shared preset runner so editor and batch behavior stay consistent. Settings is the only place where preset parameters are edited; editor and batch run surfaces only select a named preset and the required fields.

## Terminology

- **Processing preset**: a user-facing saved recipe that orders shared audio operations and optional terminal Graph output.
- **Step**: one operation inside a processing preset.
- **Runner**: the shared code that applies a preset to one source audio file.
- **Pipeline**: reserved for existing low-level staged processing internals such as pause-removal pipeline files. New user-facing preset code should avoid generic `pipeline` names.

## Goals

- Let users create, edit, reorder, duplicate, delete, and rename saved audio presets in Settings.
- Let a preset run from the inline editor against the active audio field.
- Let a preset run from Browser batch against selected notes.
- Store operation parameters per preset step so a preset is reproducible.
- Keep Graph as an optional terminal output that analyzes the final audio.
- Preserve existing non-destructive editor behavior: source media remains untouched, field replacement happens only after success, undo/redo sees one preset modification, and failed runs leave fields unchanged.
- Preserve editor and batch parity by sharing validation and execution semantics.

## Non-Goals

- Arbitrary toolbar actions inside presets.
- Playback, share, record, show-file, undo, redo, selection delete, or delete-rest steps.
- Intermediate graph outputs.
- Per-step note field targets.
- Per-run parameter prompts or overrides.
- A node-canvas builder.
- Preset execution optimization or FFmpeg filtergraph compilation.

## User Experience

Settings gets a `Presets` tab alongside General and Diagnostics. The tab uses a recipe-list layout:

- Left side: saved preset list and a `New` action.
- Right side: selected preset editor.
- The editor contains the preset name, ordered transform steps, an optional terminal Graph section, and delete/duplicate/reorder controls.

When a user adds a step, the step copies the current global Settings defaults for that operation. Later global default changes do not mutate existing preset steps.

The editor gets a Preset action with a named dropdown. Choosing a preset runs it against the active audio field. The action is useful only when at least one runnable preset exists and should participate in the existing toolbar visibility settings.

Browser batch gets a Preset operation mode. Users choose:

- preset
- source field
- final audio target field, when the selected preset has transform steps
- graph target field, when the selected preset has Graph enabled

If the batch audio target differs from the source field, the target receives source field HTML with the selected sound reference replaced by the final generated audio. The source field remains unchanged. If the target is the source field, behavior matches current transform replacement semantics.

## Saved Data Model

Add a schema-backed `audio_processing_presets` array to config. Existing configs migrate to `audio_processing_presets: []`.

```json
{
  "id": "preset_clean_graph",
  "name": "Clean + graph",
  "steps": [
    {
      "id": "step_1",
      "operation": "denoise",
      "parameters": {
        "denoise_algorithm": "standard"
      }
    },
    {
      "id": "step_2",
      "operation": "remove_pauses",
      "parameters": {
        "pause_aggressiveness": "normal"
      }
    },
    {
      "id": "step_3",
      "operation": "convert",
      "parameters": {
        "target_format": "source"
      }
    }
  ],
  "graph": {
    "enabled": true,
    "parameters": {
      "graph_voice_range": "general",
      "graph_recording_condition": "auto",
      "graph_smoothness": "very_smooth",
      "graph_connect_short_dropouts_ms": 240,
      "graph_voice_lock": "balanced"
    }
  }
}
```

`operation` accepts only shared transform operations:

- `convert`
- `denoise`
- `remove_pauses`
- `slower`
- `faster`
- `volume_down`
- `volume_up`

Graph is not stored as a normal step. It is a terminal output because it always analyzes the final audio.

Validation rules:

- preset IDs are unique
- preset names are unique after trimming
- step IDs are unique within a preset
- names are nonempty after trimming
- a preset has at least one transform step or Graph enabled
- each step operation is supported
- each step's parameters are valid for that operation
- Graph parameters follow the existing graph config ranges and enums

## Architecture

Add import-safe preset model and validation code in `audio_processing_presets.py`.

Add a shared execution module in `audio_processing_preset_runner.py` that accepts:

- `AudioProcessingPreset`
- source media path
- source audio filename
- base `AudioProcessingConfig`
- temp artifact root
- renderer and analyzer adapters needed to produce staged outputs
- operation ID / logging context

The runner returns a structured result:

- final audio temp path and desired filename, when transforms produce audio
- graph SVG bytes and desired filename, when Graph is enabled
- per-step status/log entries
- no-op status when no field mutation is needed

Editor and batch integrations call this shared preset runner instead of independently looping through operation-specific code. The runner stages outputs only; editor and batch integrations remain responsible for writing final media into Anki and committing note field changes.

Existing operation implementations remain the source of truth:

- convert uses the existing convert renderer
- denoise uses the existing batch/editor denoise path
- shorten pauses, speed, and volume use `AudioEditState`, `effective_config_for_operation`, and `render_audio`
- Graph uses the existing prosody analysis and SVG/inline rendering paths

## Execution Semantics

The runner executes transform steps linearly against temporary files. Intermediate files are private implementation details. Only the final generated audio is written to Anki media.

For each transform step:

1. Merge the base config with the step's saved parameters.
2. Run the existing operation-specific renderer against the current temp input.
3. Treat that output as the next step's input.

Graph runs after transforms. If there are no transforms, Graph analyzes the original source audio.

Convert-to-same-format is a step-level no-op. The preset continues if later steps exist. If all transform steps are no-ops and Graph is disabled, the run reports "nothing to change" and does not mutate fields.

## Editor Integration

An editor preset run follows the existing modification-button contract.

When a preset has transform steps and succeeds:

- the active field's first supported sound reference is replaced with the final generated audio
- original media is not overwritten or deleted
- undo/redo receives one entry for the whole preset
- redo history is cleared
- busy state blocks concurrent modification commands
- stale playback/progress/selection state is reset
- post-edit playback uses the final generated audio
- Graph, when enabled, opens or refreshes the inline graph for the final audio

When a preset is graph-only:

- the note field is not changed
- modification history is not pushed
- the inline graph is opened or refreshed for the current audio

Failure leaves the note unchanged and does not push editor history.

## Batch Integration

Batch receives saved presets in its initial state. The UI offers a Preset mode when at least one runnable preset exists.

For each note:

1. Find the first supported sound reference in the selected source field.
2. Run the selected preset against that audio.
3. If transforms produced final audio, write copied source HTML with the selected reference replaced into the audio target field.
4. If Graph is enabled, render an SVG for the final audio and append it to the graph target field.
5. Commit note field updates only after all requested outputs for that note are ready.

If any step fails, later steps do not run and the note fields remain unchanged. Generated temp files are cleaned up. If a media write succeeds but a later media write fails, note fields still remain unchanged and logs should call out any possible orphaned generated media.

## Settings UI Details

New Svelte modules should keep the Settings panel focused:

- `PresetSettingsPanel.svelte`
- `PresetList.svelte`
- `PresetEditor.svelte`
- `PresetStepList.svelte`
- `PresetStepEditor.svelte`
- small operation-specific parameter editors where extraction from batch/editor controls is practical

The UI should use existing Settings styling, Anki theme variables, and `AqeTooltip` for live tooltips. It should use stable `data-testid` attributes for e2e tests.

Frontend validation should guide the user before save:

- empty preset names
- duplicate preset names
- empty runnable presets
- invalid step parameter values
- missing batch fields for selected preset outputs

Python validation remains authoritative on save.

## Error Handling

Preset errors should identify the failing step by name and operation. Existing coded audio processing and graph analysis errors should be reused.

Field writes are all-or-nothing at the note level. A failure in one preset step, final audio generation, graph generation, or field replacement leaves editor and batch note fields unchanged.

Settings save errors use the existing `window.onSaveError(...)` path. Invalid preset config should not be written.

## Testing

Unit tests:

- preset model validation
- duplicate IDs and empty-name rejection
- operation allow-list enforcement
- parameter normalization per operation
- graph terminal validation
- no-op handling
- failure atomicity in the shared runner

Frontend tests:

- Settings preset constructor state
- create/rename/delete/duplicate/reorder preset
- add step initialized from current defaults
- operation-specific parameter editors
- save payload shape
- editor preset dropdown behavior
- batch preset mode field requirements
- empty-state behavior when no presets exist

Integration tests:

- editor command decoding for preset runs
- batch request decoding for preset runs
- config schema and generated contract synchronization
- editor runtime config injection
- batch initial-state preset injection

E2E tests:

- create a preset in Settings, save it, and run it in the editor
- editor preset run replaces the field only after success
- editor undo/redo treats the preset as one modification
- editor post-edit playback uses the final audio
- Browser batch preset writes transformed audio to a separate audio target field
- Browser batch preset appends terminal Graph to a graph target field
- graph-only preset behavior in editor and batch
- failure leaves fields unchanged

Verification gate:

- `python3 scripts/dev.py check`
- `python3 scripts/dev.py test-e2e`
