# Processing Presets High-Level Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Before implementation, expand this high-level plan into a task-by-task execution plan and use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. This document intentionally defines sequencing, boundaries, risks, and verification at a high level.

**Goal:** Build Settings-defined processing presets that can run from both the inline editor and Browser batch dialog.

**Architecture:** Add a schema-backed `audio_processing_presets` config model, validate it through import-safe Python helpers, and execute presets through a shared staged runner. Editor and batch integrations should call the same preset runner but remain responsible for their own UI state, media writes, note-field commits, history, playback, and graph behavior.

**Tech Stack:** Python 3.13, Anki add-on runtime, JSON Schema, generated Python/TypeScript contracts, Svelte 5, Vitest, pytest, repository task runner `scripts/dev.py`, real Anki/Qt e2e tests.

---

## Reference

- Design spec: `docs/superpowers/specs/2026-05-29-processing-presets-design.md`
- Webview and contract rules: `WEBVIEW_AND_TEMPLATES.md`
- Editor modification contract: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`
- Full QC: `python3 scripts/dev.py check`
- E2E gate: `python3 scripts/dev.py test-e2e`

## File Map

### Backend model and contracts

- `addon/anki_audio_quick_editor/config.json`
  Add default `audio_processing_presets: []`.
- `addon/anki_audio_quick_editor/config.schema.json`
  Add the persisted preset schema and editor button enum entry for the Preset action.
- `contracts/communication.schema.json`
  Add preset data contracts for batch initial state/start requests so Svelte does not depend on ad hoc payload shapes.
- `addon/anki_audio_quick_editor/contracts_generated.py`
  Generated from contract/schema updates.
- `settings_ui/src/lib/generated/contracts.ts`
  Generated from contract/schema updates.
- `settings_ui/src/lib/types.ts`
  Re-export any generated preset types/enums needed by Svelte.
- `addon/anki_audio_quick_editor/config_migration.py`
  Normalize old configs to include `audio_processing_presets: []`.
- `tests/test_config_migration.py`
  Verify missing presets are filled and malformed presets are rejected or normalized consistently.

### Shared preset logic

- Create `addon/anki_audio_quick_editor/audio_processing_presets.py`
  Import-safe dataclasses and validation for `AudioProcessingPreset`, preset steps, graph options, unique names/IDs, and operation allow-listing.
- Create `addon/anki_audio_quick_editor/audio_processing_preset_runner.py`
  Shared staged runner that applies transform steps, produces final temp audio output, optionally produces terminal Graph output, and returns structured step statuses.
- Modify `addon/anki_audio_quick_editor/audio_operation_params.py`
  Reuse or add helpers for operation-specific parameter extraction from saved preset step payloads.
- Test `tests/test_audio_processing_presets.py`
  Validate model parsing, defaults, allow-listing, duplicate detection, graph-only presets, and invalid payloads.
- Test `tests/test_audio_processing_preset_runner.py`
  Validate ordered execution, no-op convert handling, failure atomicity, temp cleanup expectations, and graph-after-final-audio behavior.

### Batch integration

- Modify `addon/anki_audio_quick_editor/browser_dialog_state.py`
  Include saved runnable presets in initial state and decode preset batch start requests.
- Modify `addon/anki_audio_quick_editor/batch_operation_types.py`
  Represent preset batch requests without forcing them through single-operation semantics.
- Modify `addon/anki_audio_quick_editor/batch_operations.py`
  Add a preset branch that uses the shared runner and commits audio target and graph target atomically per note.
- Modify `addon/anki_audio_quick_editor/browser_batch_runner.py`
  Log preset names/step summaries and preserve existing progress/cancel behavior.
- Modify `settings_ui/src/batch/batch-state.ts`
  Add preset operation mode state, selected preset helpers, and target-field validation.
- Modify `settings_ui/src/batch/BatchControls.svelte`
  Add Preset picker and conditional source/audio-target/graph-target controls.
- Test `tests/test_browser_dialog_state.py`
  Cover initial preset state and request decoding.
- Test `tests/test_batch_visualization.py`
  Cover final audio target field and terminal Graph target field.
- Test `tests/test_batch_visualization_failures.py`
  Cover preset failure leaving note fields unchanged.
- Test `settings_ui/tests/*batch*.test.ts`
  Cover preset field requirements and start payload shape.

### Editor integration

- Modify `addon/anki_audio_quick_editor/editor_actions.py`
  Add `aqe:preset` command payload decoding with preset ID/name and source field guard data.
- Create or modify `addon/anki_audio_quick_editor/editor_presets.py`
  Coordinate editor-specific preset runs: busy guard, runner invocation, final media write, field replacement, one undo history entry, post-edit playback, and terminal graph refresh.
- Modify `addon/anki_audio_quick_editor/editor_processing.py`
  Dispatch preset commands to the editor preset coordinator without bloating standard single-operation rendering.
- Modify `addon/anki_audio_quick_editor/editor_ui.py`
  Inject runnable presets into editor runtime config.
- Modify `settings_ui/src/lib/editor-toolbar-buttons.ts`
  Add the Preset toolbar command, default button mode, slug, label, and visibility behavior.
- Modify `settings_ui/src/editor-inline/`
  Add the Preset split/dropdown UI and command payload generation.
- Test `tests/test_editor_actions.py`
  Cover preset command payload decoding and invalid payload handling.
- Test editor callback modules or new `tests/test_editor_presets.py`
  Cover successful transform preset, graph-only preset, failure behavior, history, and stale-source rejection.
- Test `settings_ui/tests/editor-inline*.test.ts`
  Cover visible Preset button, dropdown options, disabled/empty behavior, and payload shape.

### Settings UI

- Modify `settings_ui/src/settings/settings-state.ts`
  Add `SettingsTab = "general" | "presets" | "diagnostics"` and fallback `audio_processing_presets: []`.
- Modify `settings_ui/src/settings/SettingsApp.svelte`
  Add the Presets tab and route it to a focused panel.
- Create `settings_ui/src/settings/PresetSettingsPanel.svelte`
  Own the recipe-list layout and selected preset lifecycle.
- Create `settings_ui/src/settings/PresetList.svelte`
  Show saved presets, create/delete/duplicate actions, and selection state.
- Create `settings_ui/src/settings/PresetEditor.svelte`
  Edit preset name, ordered steps, and terminal Graph section.
- Create `settings_ui/src/settings/PresetStepList.svelte`
  Reorder, duplicate, and delete transform steps.
- Create `settings_ui/src/settings/PresetStepEditor.svelte`
  Render operation-specific parameter controls.
- Create shared operation parameter controls under `settings_ui/src/lib/` when the same pause/denoise/format editor is needed by both Settings and batch.
  Keep extraction limited to controls that are actually reused.
- Test `settings_ui/tests/settings*.test.ts`
  Cover create/rename/delete/duplicate/reorder, defaults copied at step creation, save payload, and validation warnings.

### Copy and docs

- Modify `addon/anki_audio_quick_editor/i18n/*.json`
  Add Settings, editor, and batch copy for Presets.
- Modify `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`
  Document Preset as a generated-file modification action and clarify graph-only behavior.
- Modify `WEBVIEW_AND_TEMPLATES.md`
  Document new bridge payload rules if preset batch/editor commands add new contract surfaces.

## Implementation Phases

### Phase 1: Schema, contracts, and defaults

- [ ] Add `audio_processing_presets` to default config and config schema.
- [ ] Add Preset toolbar command to visible-button schema and frontend toolbar types.
- [ ] Regenerate contracts with `python3 scripts/dev.py contracts-generate`.
- [ ] Verify schema and generated files with `python3 scripts/dev.py config-schema` and `python3 scripts/dev.py contracts-check`.
- [ ] Add migration and fallback-state tests proving old configs receive an empty preset list.

**Exit criteria:** config can round-trip through Python and TypeScript contracts with no runnable presets.

### Phase 2: Import-safe preset model

- [ ] Implement `audio_processing_presets.py` with dataclasses and validation.
- [ ] Reuse `AudioOperationParameters` for transform step parameters.
- [ ] Keep Graph terminal parameters explicit instead of modeling Graph as a normal transform step.
- [ ] Add unit tests for valid presets, duplicate IDs/names, empty presets, unsupported operations, graph-only presets, and malformed parameters.

**Exit criteria:** presets can be loaded, normalized, and rejected without importing Anki.

### Phase 3: Shared preset runner

- [ ] Implement `audio_processing_preset_runner.py` around staged temp outputs.
- [ ] Reuse existing renderers for convert, denoise, pause removal, speed, and volume.
- [ ] Run Graph after the final transform output, or against the source for graph-only presets.
- [ ] Return structured statuses and staged outputs without writing Anki media or note fields.
- [ ] Add runner tests for order, no-op convert, graph-after-transform, failure stops later steps, and cleanup expectations.

**Exit criteria:** one import-safe runner can execute preset semantics for both editor and batch callers.

### Phase 4: Batch preset mode

- [ ] Extend batch initial state with runnable presets.
- [ ] Add batch start request shape for preset ID, source field, audio target field, and graph target field.
- [ ] Add batch UI controls for Preset mode and target-field validation.
- [ ] Add batch backend processing that stages all requested outputs before committing note fields.
- [ ] Add Python and Svelte tests for payload decoding, target-field behavior, graph target behavior, and failure atomicity.

**Exit criteria:** Browser batch can run a preset to a separate final audio target and optional graph target.

### Phase 5: Editor preset action

- [ ] Add editor runtime injection for runnable presets.
- [ ] Add Preset toolbar/dropdown command in the inline editor UI.
- [ ] Add editor command decoding for selected preset ID.
- [ ] Add editor preset coordinator that calls the shared runner and commits one editor modification.
- [ ] Preserve busy guard, stale-source rejection, undo/redo, graph refresh, and post-edit playback behavior.
- [ ] Add Python and Svelte tests for command payloads, successful run, graph-only run, failure unchanged, and one history entry.

**Exit criteria:** inline editor can run saved presets while preserving the existing modification-button contract.

### Phase 6: Settings Presets tab

- [ ] Add `Presets` tab to Settings.
- [ ] Build the recipe-list constructor with focused components.
- [ ] Copy current Settings defaults into newly added steps.
- [ ] Validate empty names, duplicate names, empty runnable presets, and invalid step values before save.
- [ ] Add frontend tests for constructor behavior and save payload shape.

**Exit criteria:** users can create and edit persisted processing presets without touching JSON.

### Phase 7: E2E and documentation

- [ ] Add e2e coverage for creating a preset in Settings and running it in the editor.
- [ ] Add e2e coverage for Browser batch preset audio target plus terminal Graph target.
- [ ] Add graph-only preset coverage.
- [ ] Add failure-path coverage proving fields stay unchanged.
- [ ] Update `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e`.

**Exit criteria:** full QC and e2e pass, and docs describe Preset behavior without overloading pipeline terminology.

## Key Risks

- **Scope size:** This touches contracts, config, three webviews, editor runtime, batch runtime, and e2e. Keep commits phase-sized and avoid polishing unrelated UI.
- **Atomicity:** Batch preset writes must not partially update fields when graph generation or final media write fails.
- **Editor history:** A multi-step transform preset must produce one undo entry, not one per step.
- **Terminology drift:** New user-facing code should use `preset`; existing low-level `pipeline` files should not be renamed as part of this feature.
- **Generated artifacts:** Contracts and webview bundles are generated; commit source schemas and Svelte/TypeScript, not ignored bundles.

## Suggested Commit Boundaries

1. `schema: add processing preset config contract`
2. `feat: add import-safe processing preset model`
3. `feat: add shared processing preset runner`
4. `feat: run processing presets from browser batch`
5. `feat: run processing presets from editor`
6. `feat: add settings preset constructor`
7. `test: cover processing preset workflows`
8. `docs: document processing preset behavior`

Each commit body should explain why that layer exists and what behavior or system boundary it protects.
