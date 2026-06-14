# Trigger Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable trigger rules that run Audio Quick Editor processing after manual Add Cards and editor-save workflows without blocking the save.

**Architecture:** Store trigger rules in schema-backed config, match manual add/edit events through Anki hooks, and queue latest-wins one-note jobs through the existing batch operation core and processing preset runner. Trigger-specific adapters own automation semantics that differ from Browser batch, especially Graph target-field replacement and source-field replacement for preset transforms.

**Tech Stack:** Python 3.13, Anki 25.09 hooks, JSON Schema, generated Python/TypeScript contracts, Svelte 5, pytest, Vitest, repository task runner `scripts/dev.py`, real Anki/Qt e2e tests.

---

## Reference

- Design spec: `docs/superpowers/specs/2026-05-29-trigger-automation-design.md`
- Anki API guidance: `ANKI_API.md`
- Settings/webview guidance: `WEBVIEW_AND_TEMPLATES.md`
- Editor operation behavior: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`
- Current preset implementation: `addon/anki_audio_quick_editor/audio_processing_presets.py`
- Shared preset runner: `addon/anki_audio_quick_editor/audio_processing_preset_runner.py`
- Batch operation core: `addon/anki_audio_quick_editor/batch_operation_processing.py`
- Batch preset adapter: `addon/anki_audio_quick_editor/batch_processing_presets.py`
- Shared batch/export webview state: `settings_ui/src/batch/batch-state.ts`, `settings_ui/src/batch/export-state.ts`, and `settings_ui/src/batch/BatchApp.svelte`
- Full QC: `python3 scripts/dev.py check`
- E2E gate: `python3 scripts/dev.py test-e2e-parallel` first, then `python3 scripts/dev.py test-e2e` if parallel exposes flake-only behavior.

## Current Baseline

Processing presets already exist in backend, Settings, editor, Browser batch, and tests. The trigger plan must reuse `AudioProcessingPreset`, `presets_from_raw()`, `preset_by_id()`, `run_processing_preset()`, and `batch_preset_runner_adapters()` instead of adding a parallel preset model.

Single-operation trigger rules must support `graph`, `convert`, `reduce_size`, `denoise`, `remove_pauses`, `slower`, `faster`, `volume_down`, and `volume_up`. Current preset Settings/schema code does not expose `reduce_size` as a preset step; that is separate preset-parity work. Trigger automation should still support `reduce_size` directly as a single-operation rule.

Main now includes selected-card audio export in the Browser batch webview. `contracts/communication.schema.json` has both `BatchInitialState` and `AudioExportInitialState`, `BatchInitialState` requires a `surface`, and `settings_ui/src/batch/batch-state.ts` exposes `BatchBundleInitialState = BatchInitialState | AudioExportInitialState`. Trigger implementation must preserve that shared operations/export contract surface when regenerating contracts or touching batch UI helpers.

Anki 25.09 installed source confirms:

```python
gui_hooks.add_cards_did_add_note(note)
gui_hooks.operation_did_execute(changes, handler)
```

Editor saves call `update_note(parent=self.widget, note=self.note).run_in_background(initiator=self)` from `aqt.editor.Editor._save_current_note()`, so `operation_did_execute` receives the editor object as `handler`.

## File Map

### Config, contracts, and validation

- Modify `addon/anki_audio_quick_editor/config.json`
  Add `"audio_trigger_rules": []`.
- Modify `addon/anki_audio_quick_editor/config.schema.json`
  Add required `audio_trigger_rules` and definitions for trigger rules, note type references, action type, event, operation, parameters, and target field constraints.
- Modify `addon/anki_audio_quick_editor/config_migration.py`
  Keep config version 2 and rely on deep-merge to add the default key. Do not normalize malformed rule objects during migration; Settings save validation rejects malformed trigger rules.
- Modify `contracts/communication.schema.json`
  Add trigger Settings metadata contracts for note type IDs, names, and field names. Keep persisted config shape sourced from `config.schema.json`. Preserve the existing `BatchInitialState`, `AudioExportInitialState`, `BatchSurface`, and audio-export command definitions when regenerating contracts.
- Modify `addon/anki_audio_quick_editor/settings_state.py`
  Include trigger metadata in `InitialState` so Settings can offer note type and field pickers.
- Modify `addon/anki_audio_quick_editor/settings/initial_state.py`
  Collect note type metadata from `mw.col.models` when a collection is available.
- Regenerate `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts`.
- Modify `addon/anki_audio_quick_editor/settings/commands.py`
  Validate `audio_trigger_rules` together with `audio_processing_presets`.
- Test `tests/test_config_migration.py`, `tests/test_config_migration_defaults.py`, `tests/test_settings_commands_save.py`, and new `tests/test_trigger_rules.py`.
- Test `tests/test_settings_initial_state.py` for trigger metadata serialization.
- Test `settings_ui/tests/batch-export-state.test.ts` and `settings_ui/tests/batch-export-app.test.ts` after contract regeneration if generated TypeScript types change.

### Trigger backend

- Create `addon/anki_audio_quick_editor/trigger_rules.py`
  Import-safe dataclasses and helpers for parsing, validation, event matching, source sound extraction, operation parameter normalization, preset resolution, and action fingerprints.
- Create `addon/anki_audio_quick_editor/trigger_state.py`
  JSON sidecar store under `<addon_dir>/aqe_artifacts/trigger_state/<collection-key>.json`.
- Create `addon/anki_audio_quick_editor/trigger_batch_adapter.py`
  One-note execution for single-operation trigger rules using existing batch operation processors with trigger-specific Graph replacement.
- Create `addon/anki_audio_quick_editor/trigger_preset_adapter.py`
  One-note execution for preset trigger rules using `run_processing_preset()` and trigger-specific field writes.
- Create `addon/anki_audio_quick_editor/trigger_runner.py`
  Queueing, background execution, latest-wins tokens, stale completion checks, note writes, diagnostics, and trigger-initiated update guard.
- Create `addon/anki_audio_quick_editor/trigger_integration.py`
  Anki hook registration and add/edit event classification.
- Modify `addon/anki_audio_quick_editor/__init__.py`
  Register `_setup_trigger_integration` during `main_window_did_init` after config migration and diagnostics are ready.

### Settings UI

- Modify `settings_ui/src/settings/settings-state.ts`
  Extend `SettingsTab` to `"general" | "presets" | "triggers" | "diagnostics"` and add fallback `audio_trigger_rules: []`.
- Modify `settings_ui/src/settings/SettingsApp.svelte`
  Add Triggers tab between Presets and Diagnostics.
- Create `settings_ui/src/settings/TriggerSettingsPanel.svelte`
  Own trigger list, selection, add/duplicate/delete, and validation summary.
- Create `settings_ui/src/settings/trigger-settings-state.ts`
  Frontend helpers for new rule creation, operation summaries, preset summaries, validation, and save payload normalization.
- Reuse existing controls:
  `PresetStepEditor.svelte`, `PresetGraphEditor.svelte`, `SettingsSizeReductionFields.svelte`, `GraphSettingsFields.svelte`, `PauseAdvancedParamsFields.svelte`, and size-reduction helpers where their APIs fit. Extract shared controls only when needed by both preset and trigger editors.
- Test `settings_ui/tests/settings*.test.ts` for tab rendering and rule editing flows.

### E2E

- Create `e2e/test_trigger_automation.py` for trigger scenarios.
- Reuse settings helpers from `e2e/settings_dialog_helpers.py` and media/note helpers from existing editor and batch e2e tests.

---

## Task 1: Schema, Defaults, And Contract Surface

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config_migration.py`
- Modify: `contracts/communication.schema.json`
- Modify: `addon/anki_audio_quick_editor/settings_state.py`
- Modify: `addon/anki_audio_quick_editor/settings/initial_state.py`
- Modify: `addon/anki_audio_quick_editor/settings/commands.py`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Test: `tests/test_config_migration_defaults.py`
- Test: `tests/test_settings_initial_state.py`
- Test: `tests/test_settings_commands_save.py`
- Test: `tests/test_trigger_rules.py`
- Test: `settings_ui/tests/batch-export-state.test.ts`
- Test: `settings_ui/tests/batch-export-app.test.ts`

- [ ] **Step 1: Add a failing default-config test**

```python
def test_default_config_includes_audio_trigger_rules(default_config: dict[str, object]) -> None:
    assert default_config["audio_trigger_rules"] == []
```

Run: `python3 scripts/dev.py test -- tests/test_config_migration_defaults.py -q`

Expected: FAIL because `audio_trigger_rules` is missing.

- [ ] **Step 2: Add the persisted config key**

In `addon/anki_audio_quick_editor/config.json`, add:

```json
"audio_trigger_rules": []
```

In `settings_ui/src/settings/settings-state.ts`, add the same empty array to `FALLBACK_INITIAL_STATE.config`.

- [ ] **Step 3: Add config schema definitions**

Add `audio_trigger_rules` to `required` and `properties`, with rule definitions equivalent to:

```json
"audio_trigger_rules": {
  "type": "array",
  "items": { "$ref": "#/definitions/AudioTriggerRule" }
}
```

Define `AudioTriggerRule` with required keys:

```json
[
  "id",
  "name",
  "enabled",
  "event",
  "note_type",
  "source_field",
  "action_type",
  "operation",
  "preset_id",
  "target_field",
  "parameters"
]
```

Use enums:

```json
"event": { "enum": ["add", "edit"] }
"action_type": { "enum": ["operation", "preset"] }
"operation": {
  "type": ["string", "null"],
  "enum": [
    "graph",
    "convert",
    "reduce_size",
    "denoise",
    "remove_pauses",
    "slower",
    "faster",
    "volume_down",
    "volume_up",
    null
  ]
}
```

Include parameter keys already supported by `AudioOperationParameters`, including:

```json
"size_reduction_mode"
"size_reduction_bitrate_kbps"
"size_reduction_sample_rate_hz"
"size_reduction_channels"
```

- [ ] **Step 4: Add backend save validation hook**

In `settings/commands.py`, parse presets once and pass them to trigger validation:

```python
from ..trigger_rules import trigger_rules_from_raw

def _validate_settings_config(config: dict[str, Any]) -> None:
    presets = presets_from_raw(config.get("audio_processing_presets"))
    trigger_rules_from_raw(
        config.get("audio_trigger_rules"),
        presets=presets,
    )
```

- [ ] **Step 5: Add Settings note type metadata contracts**

In `contracts/communication.schema.json`, add:

```json
"TriggerNoteTypeOption": {
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "name", "fields"],
  "properties": {
    "id": { "type": ["integer", "null"] },
    "name": { "type": "string" },
    "fields": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
},
"TriggerSettingsMetadata": {
  "type": "object",
  "additionalProperties": false,
  "required": ["note_types"],
  "properties": {
    "note_types": {
      "type": "array",
      "items": { "$ref": "#/definitions/TriggerNoteTypeOption" }
    }
  }
}
```

Add `"triggers"` to `InitialState.required` and `InitialState.properties`.

- [ ] **Step 6: Add Settings metadata builder**

In `settings/initial_state.py`, collect note type metadata before calling `build_initial_state_payload`:

```python
def _trigger_note_type_options() -> list[dict[str, Any]]:
    if mw.col is None:
        return []
    options: list[dict[str, Any]] = []
    for model in mw.col.models.all():
        fields = [str(field.get("name", "")) for field in model.get("flds", [])]
        options.append(
            {
                "id": int(model["id"]) if model.get("id") is not None else None,
                "name": str(model.get("name", "")),
                "fields": [field for field in fields if field],
            }
        )
    return options
```

Pass `triggers={"note_types": _trigger_note_type_options()}` into `build_initial_state_payload`.

In `settings_state.py`, add a required `triggers` argument and include it in the returned payload.

- [ ] **Step 7: Regenerate contracts**

Run: `python3 scripts/dev.py contracts-generate`

Expected: generated Python and TypeScript contracts include `audio_trigger_rules` and trigger Settings metadata, while existing audio-export contracts remain present.

- [ ] **Step 8: Verify schema and contracts**

Run: `python3 scripts/dev.py config-schema`

Expected: PASS.

Run: `python3 scripts/dev.py contracts-check`

Expected: PASS.

- [ ] **Step 9: Verify shared batch/export TypeScript still compiles**

Run:

```bash
python3 scripts/dev.py test -- settings_ui/tests/batch-export-state.test.ts settings_ui/tests/batch-export-app.test.ts
```

Expected: PASS. This protects the merged `BatchBundleInitialState` and `BatchSurface.AudioExport` path while trigger contracts are added.

- [ ] **Step 10: Commit**

```bash
git add addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config_migration.py contracts/communication.schema.json addon/anki_audio_quick_editor/settings_state.py addon/anki_audio_quick_editor/settings/initial_state.py addon/anki_audio_quick_editor/settings/commands.py addon/anki_audio_quick_editor/contracts_generated.py settings_ui/src/lib/generated/contracts.ts settings_ui/src/settings/settings-state.ts tests/test_config_migration_defaults.py tests/test_settings_initial_state.py tests/test_settings_commands_save.py tests/test_trigger_rules.py
git commit -m "schema: add trigger rule config contract"
```

Commit body: explain that persisted trigger rules need schema and generated contract coverage before hooks can consume user automation safely.

## Task 2: Import-Safe Trigger Rule Model

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_rules.py`
- Test: `tests/test_trigger_rules.py`

- [ ] **Step 1: Write parser and validation tests**

Add these tests:

- `test_trigger_rules_parse_transform_rule`: a valid `remove_pauses` add rule returns an enabled `AudioTriggerRule` with normalized pause parameters.
- `test_trigger_rules_parse_graph_rule_requires_target_field`: a `graph` operation rule with `target_field=None` raises `ValueError`.
- `test_trigger_rules_parse_reduce_size_parameters`: a `reduce_size` rule preserves normalized bitrate, sample rate, channel, and mode parameters.
- `test_trigger_rules_parse_preset_rule`: a preset rule stores `preset_id`, keeps `operation=None`, and does not copy preset steps.
- `test_trigger_rules_reject_duplicate_ids`: two rules with the same ID raise `ValueError`.
- `test_trigger_rules_match_event_note_type_and_field`: enabled add/edit matching respects event, note type ID, note type name fallback, and source field existence.
- `test_trigger_rules_action_fingerprint_changes_with_parameters`: changing one operation parameter changes the fingerprint.
- `test_trigger_rules_action_fingerprint_changes_with_preset_content`: changing a referenced preset step changes the fingerprint.

Run: `python3 scripts/dev.py test -- tests/test_trigger_rules.py -q`

Expected: FAIL because `trigger_rules.py` does not exist.

- [ ] **Step 2: Implement dataclasses**

Create:

```python
@dataclass(frozen=True)
class TriggerNoteTypeRef:
    id: int | None
    name: str

@dataclass(frozen=True)
class AudioTriggerRule:
    id: str
    name: str
    enabled: bool
    event: Literal["add", "edit"]
    note_type: TriggerNoteTypeRef
    source_field: str
    action_type: Literal["operation", "preset"]
    operation: str | None
    preset_id: str | None
    target_field: str | None
    parameters: AudioOperationParameters
```

Keep this module import-safe: no `aqt`, no `mw`, no Qt imports.

- [ ] **Step 3: Implement raw parsing**

Expose:

```python
def trigger_rules_from_raw(
    raw: Any,
    *,
    presets: tuple[AudioProcessingPreset, ...] = (),
) -> tuple[AudioTriggerRule, ...]
```

Use `parameters_from_raw()` for `parameters`. Validate operation rules against `BATCH_OPERATIONS`; validate preset rules with `preset_by_id()` only when `presets` is nonempty.

- [ ] **Step 4: Implement matching helpers**

Expose:

```python
def note_type_matches(rule: AudioTriggerRule, note_type_id: int | None, note_type_name: str) -> bool
def rule_applies_to_event(rule: AudioTriggerRule, event: str) -> bool
def first_supported_sound_filename(field_html: str) -> str | None
def action_fingerprint(rule: AudioTriggerRule, presets: tuple[AudioProcessingPreset, ...]) -> str
```

Derive the fingerprint from canonical JSON with sorted keys. For preset rules, include the resolved preset definition content, not only `preset_id`.

- [ ] **Step 5: Verify**

Run: `python3 scripts/dev.py test -- tests/test_trigger_rules.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_rules.py tests/test_trigger_rules.py
git commit -m "feat: add import-safe trigger rule model"
```

Commit body: explain that rule parsing and matching are isolated from Anki so automation policy can be unit-tested before hook integration.

## Task 3: Trigger Sidecar State

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_state.py`
- Test: `tests/test_trigger_state.py`

- [ ] **Step 1: Write state tests**

Add these tests:

- `test_state_marks_changed_filename_unhandled`: a different field filename returns `should_schedule=True`.
- `test_state_marks_same_filename_and_fingerprint_handled`: the same handled filename and fingerprint returns `should_schedule=False`.
- `test_state_marks_changed_fingerprint_unhandled`: a changed action fingerprint returns `should_schedule=True`.
- `test_state_generation_token_latest_wins`: an older token fails `is_latest()` after a newer token is written.
- `test_state_persists_failure_summary`: `mark_failed()` writes status `failed` and reloads the saved error summary.

Run: `python3 scripts/dev.py test -- tests/test_trigger_state.py -q`

Expected: FAIL because `trigger_state.py` does not exist.

- [ ] **Step 2: Implement state records**

Create:

```python
@dataclass(frozen=True)
class TriggerStateKey:
    note_id: int
    rule_id: str
    source_field: str

@dataclass(frozen=True)
class TriggerStateEntry:
    last_handled_field_filename: str | None
    input_filename: str | None
    action_fingerprint: str | None
    generation_token: str | None
    status: Literal["idle", "running", "succeeded", "failed"]
    last_successful_output_filename: str | None
    updated_at: str
    last_error: str | None
```

- [ ] **Step 3: Implement store paths**

Use:

```python
def collection_state_path(addon_dir: Path, collection_path: str | None) -> Path:
    identity = collection_path or "no_collection"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return addon_dir / "aqe_artifacts" / "trigger_state" / f"{digest}.json"
```

This avoids leaking full collection paths into filenames while keeping separate collections separate.

- [ ] **Step 4: Implement latest-wins helpers**

Expose:

```python
def should_schedule(entry: TriggerStateEntry | None, filename: str, fingerprint: str) -> bool
def new_generation_token() -> str
def is_latest(entry: TriggerStateEntry | None, token: str) -> bool
def mark_running(store: TriggerStateStore, key: TriggerStateKey, filename: str, fingerprint: str, token: str) -> None
def mark_succeeded(store: TriggerStateStore, key: TriggerStateKey, token: str, handled_filename: str, output_filename: str | None) -> None
def mark_failed(store: TriggerStateStore, key: TriggerStateKey, token: str, error: str) -> None
```

- [ ] **Step 5: Verify**

Run: `python3 scripts/dev.py test -- tests/test_trigger_state.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_state.py tests/test_trigger_state.py
git commit -m "feat: track trigger automation state outside notes"
```

Commit body: explain that sidecar state prevents repeated text-edit reruns and stale writes without adding hidden note fields.

## Task 4: Single-Operation Trigger Adapter

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_batch_adapter.py`
- Test: `tests/test_trigger_batch_adapter.py`

- [ ] **Step 1: Write adapter tests**

Add these tests:

- `test_transform_trigger_replaces_source_sound_and_preserves_html`: only the first supported sound reference changes and surrounding HTML remains.
- `test_graph_trigger_replaces_target_field_instead_of_appending`: old target field HTML is replaced by the generated SVG reference.
- `test_reduce_size_trigger_marks_already_compact_as_skipped`: `AudioAlreadyCompactError` returns a skipped result that the runner can mark handled.
- `test_trigger_adapter_reports_missing_target_field_as_skipped`: a Graph rule whose target field is absent does not write the note.

Run: `python3 scripts/dev.py test -- tests/test_trigger_batch_adapter.py -q`

Expected: FAIL because the adapter does not exist.

- [ ] **Step 2: Implement request conversion**

Expose:

```python
def batch_request_for_trigger(rule: AudioTriggerRule) -> BatchRunRequest:
    assert rule.operation is not None
    return BatchRunRequest(
        operation=rule.operation,
        source_field=rule.source_field,
        target_field=rule.target_field,
        parameters=rule.parameters,
    )
```

- [ ] **Step 3: Implement Graph replacement semantics**

Call `process_graph_operation()` with an image-reference callback that ignores old target HTML:

```python
def replace_with_image_reference(_existing_html: str, image_filename: str) -> str:
    return f'<img src="{html.escape(image_filename, quote=True)}">'
```

The Browser batch callback continues appending; only the trigger adapter uses replacement.

- [ ] **Step 4: Implement transform execution**

Call `process_transform_operation()` for all transform operations, including `reduce_size`. Pass the same `BatchOperationDeps` structure used by Browser batch so renderers stay shared.

- [ ] **Step 5: Verify**

Run: `python3 scripts/dev.py test -- tests/test_trigger_batch_adapter.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_batch_adapter.py tests/test_trigger_batch_adapter.py
git commit -m "feat: adapt batch operations for trigger rules"
```

Commit body: explain why trigger Graph writes replace the target field while Browser batch keeps append behavior.

## Task 5: Preset Trigger Adapter

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_preset_adapter.py`
- Test: `tests/test_trigger_preset_adapter.py`

- [ ] **Step 1: Write preset adapter tests**

Add these tests:

- `test_preset_trigger_replaces_source_with_final_audio`: a preset with transform steps writes the final generated audio to the source field.
- `test_preset_trigger_replaces_graph_target`: terminal Graph output replaces the configured target field.
- `test_graph_only_preset_uses_original_source_audio`: a graph-only preset analyzes the original source file.
- `test_preset_failure_leaves_all_fields_unchanged`: renderer failure returns a failed result with no field updates.

Run: `python3 scripts/dev.py test -- tests/test_trigger_preset_adapter.py -q`

Expected: FAIL because the adapter does not exist.

- [ ] **Step 2: Implement preset execution**

Use `preset_by_id()` and `run_processing_preset()`:

```python
result = run_processing_preset(
    preset,
    source_path=source_path,
    source_filename=audio_filename,
    config=config,
    adapters=batch_preset_runner_adapters(deps),
    artifact_root=artifact_root,
)
```

- [ ] **Step 3: Implement trigger field writes**

For transform output:

```python
field_updates[rule.source_field] = replace_sound_reference(
    source_html,
    selection,
    written_audio_name,
)
```

For Graph output:

```python
assert rule.target_field is not None
field_updates[rule.target_field] = f'<img src="{escaped_graph_name}">'
```

Do not call Browser batch `append_image_reference()` for trigger Graph output.

- [ ] **Step 4: Verify**

Run: `python3 scripts/dev.py test -- tests/test_trigger_preset_adapter.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_preset_adapter.py tests/test_trigger_preset_adapter.py
git commit -m "feat: run processing presets from trigger rules"
```

Commit body: explain that preset definitions stay the single source of processing behavior while triggers own note-field write semantics.

## Task 6: Trigger Runner And Stale Completion Guards

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_runner.py`
- Test: `tests/test_trigger_runner.py`

- [ ] **Step 1: Write runner tests**

Add these tests:

- `test_runner_schedules_when_source_filename_changes`: a new source filename creates a running state entry and queues a job.
- `test_runner_skips_when_filename_and_fingerprint_handled`: unchanged filename and fingerprint does not queue a job.
- `test_runner_rejects_stale_token_before_write`: an older completion does not mutate the note.
- `test_runner_rejects_note_with_changed_source_before_write`: a changed source sound cancels completion.
- `test_runner_marks_transform_output_filename_handled`: transform success stores the generated output filename as handled.
- `test_runner_marks_graph_source_filename_handled`: Graph success stores the original source filename as handled.
- `test_runner_sets_trigger_initiator_for_note_update`: published changes use `TRIGGER_INITIATOR`.

Run: `python3 scripts/dev.py test -- tests/test_trigger_runner.py -q`

Expected: FAIL because the runner does not exist.

- [ ] **Step 2: Implement job model**

Create:

```python
@dataclass(frozen=True)
class TriggerJob:
    note_id: int
    rule_id: str
    source_field: str
    observed_filename: str
    action_fingerprint: str
    generation_token: str
    event: Literal["add", "edit"]
```

Create a module-level initiator sentinel:

```python
class TriggerAutomationInitiator:
    pass

TRIGGER_INITIATOR = TriggerAutomationInitiator()
```

- [ ] **Step 3: Implement schedule logic**

`schedule_for_note_event` should:

1. Load config and parse presets/rules.
2. Match enabled rules for the event.
3. Extract the first supported source sound.
4. Compare source filename and fingerprint against sidecar state.
5. Write a new running token before dispatching the job.
6. Use `mw.taskman.run_in_background(task, done, uses_collection=True)`.

- [ ] **Step 4: Implement completion checks**

Before note mutation, reload note and verify:

```python
state.is_latest(key, job.generation_token)
rule.enabled
current_fingerprint == job.action_fingerprint
first_supported_sound_filename(note[rule.source_field]) == job.observed_filename
target field exists when graph output is required
```

If any check fails, mark the job stale/skipped and do not mutate fields.

- [ ] **Step 5: Implement note writes**

Use one collection update per trigger result and publish the resulting changes with the trigger initiator sentinel:

```python
undo_entry = mw.col.add_custom_undo_entry("Audio Quick Editor trigger")
for field_name, html in result.field_updates.items():
    note[field_name] = html
mw.col.update_note(note)
changes = mw.col.merge_undo_entries(undo_entry)
mw.taskman.run_on_main(lambda: gui_hooks.operation_did_execute(changes, TRIGGER_INITIATOR))
```

`trigger_integration.py` must ignore `handler is TRIGGER_INITIATOR`, which prevents trigger-initiated note writes from scheduling the same rule again while still refreshing Anki windows that listen to `operation_did_execute`.

- [ ] **Step 6: Verify**

Run: `python3 scripts/dev.py test -- tests/test_trigger_runner.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_runner.py tests/test_trigger_runner.py
git commit -m "feat: queue trigger jobs with latest-wins guards"
```

Commit body: explain that save hooks must return immediately and stale background completions must never overwrite newer note content.

## Task 7: Anki Hook Integration

**Files:**
- Create: `addon/anki_audio_quick_editor/trigger_integration.py`
- Modify: `addon/anki_audio_quick_editor/__init__.py`
- Test: `tests/test_trigger_integration.py`
- Test: `tests/test_anki_api_contract_mocks.py` if new mocks are required
- Test: `tests/test_anki_api_contract.py` or generated Anki API contract tests if discovery requires updates

- [ ] **Step 1: Write hook classification tests**

Add these tests:

- `test_add_cards_note_schedules_add_event`: `add_cards_did_add_note` sends event `"add"` and the note object to the scheduler.
- `test_operation_did_execute_ignores_trigger_initiator`: `handler is TRIGGER_INITIATOR` does not schedule.
- `test_operation_did_execute_requires_note_text_change`: changes without `note_text` do not schedule.
- `test_operation_did_execute_requires_editor_handler`: non-editor handlers do not schedule.
- `test_operation_did_execute_schedules_edit_event_for_editor_handler`: an editor handler with a note schedules event `"edit"`.

Run: `python3 scripts/dev.py test -- tests/test_trigger_integration.py -q`

Expected: FAIL because integration does not exist.

- [ ] **Step 2: Implement registration**

```python
def register_trigger_hooks(gui_hooks: Any, *, scheduler: TriggerScheduler | None = None) -> None:
    active_scheduler = scheduler or schedule_for_note_event
    gui_hooks.add_cards_did_add_note.append(lambda note: active_scheduler(note, event="add"))
    gui_hooks.operation_did_execute.append(
        lambda changes, handler: _on_operation_did_execute(changes, handler, active_scheduler)
    )
```

- [ ] **Step 3: Implement editor-save classification**

Use installed Anki 25.09 behavior:

```python
def _looks_like_editor_handler(handler: object | None) -> bool:
    return handler is not None and handler.__class__.__name__ == "Editor" and hasattr(handler, "note")
```

Use `changes.note_text` as the primary note-content signal. Schedule the handler note only when it exists.

- [ ] **Step 4: Wire startup**

In `__init__.py`, add:

```python
def _setup_trigger_integration() -> None:
    import_module(f"{__name__}.trigger_integration").register_trigger_hooks(gui_hooks)
```

Append it after diagnostics and before menu setup:

```python
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_trigger_integration", _setup_trigger_integration))
```

- [ ] **Step 5: Verify Anki API contract**

Run: `python3 scripts/dev.py test-anki-api`

Expected: PASS with `add_cards_did_add_note(note)` and `operation_did_execute(changes, handler)` signatures covered.

- [ ] **Step 6: Verify unit tests**

Run: `python3 scripts/dev.py test -- tests/test_trigger_integration.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/trigger_integration.py addon/anki_audio_quick_editor/__init__.py tests/test_trigger_integration.py tests/test_anki_api_contract_mocks.py
git commit -m "feat: schedule trigger automation from manual note saves"
```

Commit body: explain that V1 intentionally restricts automation to Add Cards and editor-initiated note text saves to avoid imports, sync, and arbitrary collection mutations.

## Task 8: Settings Triggers Tab

**Files:**
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Create: `settings_ui/src/settings/TriggerSettingsPanel.svelte`
- Create: `settings_ui/src/settings/trigger-settings-state.ts`
- Modify: `settings_ui/src/settings/styles.css`
- Modify: `addon/anki_audio_quick_editor/locales/*.json`
- Test: `settings_ui/tests/settings-triggers.test.ts`

- [ ] **Step 1: Write frontend tests**

Cover:

```typescript
it("renders the triggers tab with empty rules", async () => {});
it("adds an enabled add-event operation rule", async () => {});
it("requires a graph target field for graph rules", async () => {});
it("saves preset rules by preset id without copying preset steps", async () => {});
it("shows size reduction parameters for reduce_size rules", async () => {});
```

Run: `python3 scripts/dev.py test -- settings_ui/tests/settings-triggers.test.ts`

Expected: FAIL because the tab does not exist.

- [ ] **Step 2: Add tab state and route**

In `settings-state.ts`:

```typescript
export type SettingsTab = "general" | "presets" | "triggers" | "diagnostics";
```

In `SettingsApp.svelte`, add a Triggers button and render:

```svelte
{:else if activeTab === "triggers"}
  <TriggerSettingsPanel bind:config />
```

- [ ] **Step 3: Implement frontend rule helpers**

`trigger-settings-state.ts` should expose:

```typescript
export function newTriggerRule(config: Config): AudioTriggerRule
export function triggerActionSummary(rule: AudioTriggerRule, config: Config): string
export function validateTriggerRules(config: Config): string[]
export function ruleRequiresTargetField(rule: AudioTriggerRule, config: Config): boolean
```

For direct `reduce_size` rules, use existing size-reduction helper functions and fields.

- [ ] **Step 4: Implement the panel**

The panel should include:

- rule list with enabled toggle, name, event, note type, source field, action summary, and target field summary
- editor fields for event, note type ID/name, source field, action type, operation/preset, target field, and parameters
- add, duplicate, delete controls
- validation summary before Save

Use `AqeTooltip`, not native `title`.

- [ ] **Step 5: Verify frontend tests**

Run: `python3 scripts/dev.py test -- settings_ui/tests/settings-triggers.test.ts`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/settings/SettingsApp.svelte settings_ui/src/settings/settings-state.ts settings_ui/src/settings/TriggerSettingsPanel.svelte settings_ui/src/settings/trigger-settings-state.ts settings_ui/src/settings/styles.css addon/anki_audio_quick_editor/locales settings_ui/tests/settings-triggers.test.ts
git commit -m "feat: add settings UI for trigger rules"
```

Commit body: explain that the Triggers tab makes automation explicit, editable, and schema-backed instead of requiring JSON edits.

## Task 9: Integration And E2E Coverage

**Files:**
- Create: `e2e/test_trigger_automation.py`
- Modify: `e2e/settings_dialog_helpers.py` if helper support is needed
- Modify: `tests/test_architecture/*` only if new modules violate an intentional boundary

- [ ] **Step 1: Add e2e tests**

Add these e2e tests:

- `test_add_cards_transform_trigger_updates_audio_later`: Add Cards returns before processing finishes and the note audio field updates after the trigger job completes.
- `test_edit_current_trigger_runs_only_when_source_sound_changes`: a text-only edit after a handled source does not queue another job.
- `test_quick_repeated_edits_use_latest_wins`: the last edited source wins and stale output is not written.
- `test_graph_trigger_replaces_target_field`: Graph output replaces the configured target field.
- `test_preset_trigger_replaces_source_and_graph_target`: preset transform output replaces the source field and terminal Graph replaces the graph field.
- `test_reduce_size_trigger_does_not_retry_already_compact_audio`: already-compact audio is marked handled and text-only edits do not retry it.

Run: `python3 scripts/dev.py test-e2e-parallel`

Expected: FAIL until backend and UI integration are complete.

- [ ] **Step 2: Fix boundary tests deliberately**

If architecture tests fail because new trigger modules import UI or Anki too early, move Anki-facing code into `trigger_integration.py` and keep `trigger_rules.py`, `trigger_state.py`, and adapters import-safe.

- [ ] **Step 3: Run focused Python tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_trigger_rules.py tests/test_trigger_state.py tests/test_trigger_batch_adapter.py tests/test_trigger_preset_adapter.py tests/test_trigger_runner.py tests/test_trigger_integration.py -q
```

Expected: PASS.

- [ ] **Step 4: Run reusable QC**

Run: `python3 scripts/dev.py check`

Expected: PASS.

- [ ] **Step 5: Run e2e gate**

Run: `python3 scripts/dev.py test-e2e-parallel`

Expected: PASS.

If parallel e2e reports a concurrency-only failure, run: `python3 scripts/dev.py test-e2e`

Expected: PASS or a clearly isolated flake with logs attached to the final report.

- [ ] **Step 6: Commit**

```bash
git add e2e/test_trigger_automation.py e2e/settings_dialog_helpers.py tests/test_architecture
git commit -m "test: cover trigger automation workflows"
```

Commit body: explain which user workflows the e2e suite protects and mention if full non-parallel e2e was not run.

## Task 10: Documentation And Final Audit

**Files:**
- Modify: `WEBVIEW_AND_TEMPLATES.md`
- Modify: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md` only if trigger behavior affects documented editor/preset semantics
- Modify: `docs/superpowers/specs/2026-05-29-trigger-automation-design.md` if implementation decisions differ from the design

- [ ] **Step 1: Update docs**

Document:

- `audio_trigger_rules` are schema-backed Settings config
- trigger Graph output replaces target field
- trigger preset transforms replace the source field
- trigger state is stored in sidecar JSON under add-on artifacts
- V1 only schedules Add Cards and editor-save events

- [ ] **Step 2: Run doc and config checks**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
python3 scripts/dev.py test-anki-api
```

Expected: all PASS.

- [ ] **Step 3: Run full completion checks**

Run: `python3 scripts/dev.py check`

Expected: PASS.

Run: `python3 scripts/dev.py test-e2e-parallel`

Expected: PASS.

- [ ] **Step 4: Final commit**

```bash
git add WEBVIEW_AND_TEMPLATES.md EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md docs/superpowers/specs/2026-05-29-trigger-automation-design.md
git commit -m "docs: describe trigger automation behavior"
```

Commit body: explain the automation boundaries and mention any omitted full-check or e2e routine if it was not run.

## Scope Guardrails

- Do not call editor bridge commands from trigger code.
- Do not append trigger Graph output; replace the configured target field.
- Do not trigger on imports, sync, Browser bulk edits, or arbitrary collection operations in V1.
- Do not edit note types to add hidden fields.
- Do not use Settings frontend validation as the only validation layer; Python remains authoritative.
- Do not broaden preset-step support for `reduce_size` as part of trigger automation unless that parity work is explicitly added to scope.
- Do not collapse the shared batch/audio-export webview contracts back to a batch-only shape when adding trigger metadata or regenerating generated types.

## Suggested Commit Boundaries

1. `schema: add trigger rule config contract`
2. `feat: add import-safe trigger rule model`
3. `feat: track trigger automation state outside notes`
4. `feat: adapt batch operations for trigger rules`
5. `feat: run processing presets from trigger rules`
6. `feat: queue trigger jobs with latest-wins guards`
7. `feat: schedule trigger automation from manual note saves`
8. `feat: add settings UI for trigger rules`
9. `test: cover trigger automation workflows`
10. `docs: describe trigger automation behavior`

Each commit body should answer why the layer exists, what behavior it protects, and which verification was run. If a commit was made without `python3 scripts/dev.py check` and e2e, say that explicitly in the body.
