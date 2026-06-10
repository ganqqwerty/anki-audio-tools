# Architecture Problems - SOLID Re-review

_Re-reviewed 2026-06-10 against the current workspace using CodeGraph plus targeted source reads._

This file is no longer a direct acceptance of the original review. Some points were correct, some were stale, and some were framed as SOLID violations when they are really line-count or framework-boundary costs. The useful conclusion is more specific:

- The enforced layer architecture is healthy.
- The Python runtime has a few real DIP/ISP problems hidden behind compatibility facades and `deps: Any` bags.
- The Svelte/TS frontend has a broader ambient-global contract problem than the original review captured.
- Several "large file" findings should not drive work unless they are being touched for related behavior.

## 1. Executive Summary

The project has good formal boundaries. The architecture tests and import-linter contracts are doing useful work: import-safe core modules do not import UI adapters, settings backend modules avoid editor integration, and Browser batch code does not directly depend on editor bridge modules.

From a SOLID perspective, the main weaknesses are not the layer boundaries. They are:

1. **Mutable runtime wiring behind public facades** (`audio_processor.py`, `audio_processor_rendering_portal.py`, `batch_operations.py`, `batch_operation_processing.py`, `batch_operations_helpers.py`). The code is contract-compliant, but it relies on repeated dependency objects, module-global patching, and lazy facade lookup.
2. **Editor dependency bags** (`editor_dependencies.py` plus most editor workflow modules). The repo has made a deliberate testability move by injecting dependencies, but the injection surface is still untyped `SimpleNamespace`/`Any`, so callers and consumers are coupled by convention.
3. **Frontend ambient globals outside narrow adapter modules** (`window.__AQE_EDITOR_CONFIG__`, `window.__aqe*`, `globalThis.pycmd`). Some globals are unavoidable WebView bridge surface, but config and pending-state reads leak into otherwise pure UI/state modules.
4. **Diagnostics probe cloning** (`diagnostics.py`). This is a clean, isolated DRY/OCP problem: multiple health checks repeat the same path lookup, subprocess probe, timeout, and result shaping logic.

The original top-three list should be changed:

| Original claim | Revised priority | Why |
|---|---:|---|
| `audio_processor.py` is a triple-role module with 287 lines of duplicated wiring | **HIGH, but reframed** | The facade role is intentional compatibility. The real problem is six repeated `AudioModuleDeps(...)` blocks plus module-global patching. Do not split the public facade first; centralize the dependency builder first. |
| `diagnostics.py` has six cloned health-check builders | **MEDIUM-HIGH** | Correct, but isolated and low blast radius. Worth fixing before adding more runtime probes. |
| `lib/editor-toolbar-buttons.ts` is a god module | **MEDIUM-HIGH** | Correct for global config reads and mixed button metadata/defaults. "God module" overstates it; the better fix is parameterized button factories and a runtime config adapter, not a broad split first. |

## 2. Methodology

Inputs used for this revision:

- CodeGraph status: 631 indexed files, 9605 symbols, 15186 edges.
- Structural checks around the named modules: audio facade/wiring, diagnostics, editor dependencies, batch processors, reviewer integration, Svelte toolbar/split-button/graph state.
- Literal searches for `window.__AQE_*`, `window.__aqe*`, `globalThis.pycmd`, `SimpleNamespace`, `deps: Any`, and lazy `import_module(...)` facade patterns.
- Current line counts excluding vendored/user runtime files.

I did not run the full QC suite because this is a documentation-only review update.

## 3. Formal Architecture Rules

The original statement still holds: the formal rules are clean. The contracts validate directional boundaries, not fine-grained SOLID concerns.

| Rule area | Current assessment |
|---|---|
| Import-safe core avoiding UI adapters | Good. Import-linter and architecture tests cover this. |
| Settings backend avoiding editor integration | Good. |
| Batch operation boundary from editor bridge strings/modules | Mostly good. There is no direct editor bridge dependency, but batch uses facade indirection for audio/prosody operations. |
| Every production Python module classified | Good. |
| Cross-screen Svelte imports | Good from a directory-boundary perspective. |

Important nuance: a module can pass these rules and still have SOLID debt. `audio_processor.py`, `editor_dependencies.py`, and `diagnostics.py` are the best examples.

## 4. Revised Findings

### 4.1 `audio_processor.py` and audio facade wiring - HIGH

**Current facts**

- `audio_processor.py` is explicitly a backward-compatible facade.
- The original claim that all dependency sync logic lives directly in the facade is stale in part: assignment logic has moved to `audio_processor_runtime.py`.
- The duplicate dependency construction is still real. `audio_processor.py` repeats near-identical 19-field `AudioModuleDeps(...)` objects in `_sync_tool_dependencies`, `_sync_external_dependencies`, `_sync_pause_dependencies`, `_sync_rendering_dependencies`, `_sync_noise_dependencies`, and `_sync_pitch_hum_dependencies`.
- `audio_processor_rendering_portal.py` lazily imports the facade and calls `_sync_*` before delegating to implementation modules.

**SOLID impact**

| Principle | Assessment |
|---|---|
| SRP | Medium. The facade is intentionally compatibility-oriented, but it also owns runtime dependency construction. |
| DIP | High. Leaf audio modules are patched through module globals instead of receiving explicit dependencies. |
| OCP | Medium-high. Adding one field to `AudioModuleDeps` touches every repeated construction block. |

**Better solution than the original**

Do not start by splitting `audio_processor.py` into `_facade.py`; it already is the public facade and likely protects compatibility for tests, add-on callers, and monkeypatch seams.

First step:

1. Add one `_audio_module_deps()` helper that constructs `AudioModuleDeps` once.
2. Have all `_sync_*_dependencies()` functions call that helper.
3. Add a focused architecture test that `audio_processor.py` contains only one `AudioModuleDeps(` construction.

Second step:

1. Replace module-global patching with explicit `configure_*_runtime(deps)` functions where practical.
2. Keep `audio_processor.py` as the compatibility facade until callers have moved to narrower modules.

### 4.2 `editor_dependencies.py` and editor `deps: Any` - HIGH

The original review under-scoped this as mostly `processing_deps`. It is systemic.

**Evidence**

- `editor_dependencies.py` builds many `SimpleNamespace` dependency bags: frontend, bridge, recording, sharing, history, processing, settings actions, playback, analysis, and region delete.
- `processing_deps` alone contains 40+ attributes.
- Editor workflow modules consume `deps: Any` broadly: `editor_processing.py`, `editor_special_transforms.py`, `editor_region_delete.py`, `editor_region_delete_worker.py`, `editor_analysis.py`, `editor_playback.py`, `editor_recording.py`, `editor_sharing.py`, `editor_history.py`, `editor_source_metadata.py`, and frontend adapter modules.
- `editor_callbacks.py` dynamically wraps many functions with dependency builders, so the dependency shape is only checked at runtime.

**SOLID impact**

| Principle | Assessment |
|---|---|
| ISP | High. Consumers receive wider bags than they need. |
| DIP | High. Dependency injection exists, but contracts are implicit strings on `SimpleNamespace`. |
| SRP | Medium. `editor_dependencies.py` is a central composition root, which is fine, but it also encodes every consumer interface without types. |

**Better solution than the original**

Do not create one massive `ProcessingDeps` protocol. That would preserve the current bag under a different name.

Use narrow, workflow-specific typed contracts:

- `StandardRenderDeps` for `editor_processing.render_and_replace_async` and helpers.
- `SpecialTransformDeps` for `editor_special_transforms` and `editor_special_transform_worker`.
- `RegionDeleteDeps` for `editor_region_delete` and `editor_region_delete_worker`.
- `PlaybackDeps`, `AnalysisDeps`, `RecordingDeps`, and `ShareDeps` for the other workflow groups.

Start with `Protocol` definitions in the consuming modules or a small `editor_deps_protocols.py`. Then update the corresponding builder return types. Tests can still pass simple fakes as long as they satisfy the protocol.

### 4.3 Frontend ambient globals - HIGH

The original review correctly noticed globals, but the list was incomplete and mixed legitimate adapter code with logic leaks.

**Legitimate adapter/global boundary**

These modules are allowed to touch WebView globals because they define or transport the cross-runtime contract:

- `settings_ui/src/lib/bridge.ts`
- `settings_ui/src/editor-inline/bridge.ts`
- `settings_ui/src/editor-inline/window-contract.ts`
- `settings_ui/src/editor-inline/runtime.ts`
- `settings_ui/src/editor-inline/test-contract.ts`
- `settings_ui/src/batch/bridge.ts`

**Questionable global reads/writes in otherwise testable logic**

| File | Concern |
|---|---|
| `settings_ui/src/lib/editor-toolbar-buttons.ts` | `commandButtons()` and `denoiseButtons()` read `window.__AQE_EDITOR_CONFIG__` directly. |
| `settings_ui/src/editor-inline/commands.ts` | `processingMessage()` reads config defaults directly. |
| `settings_ui/src/editor-inline/EditorControls.svelte` | Reads repeat defaults, visible buttons, and button modes directly from global config. |
| `settings_ui/src/editor-inline/SelectionToolbar.svelte` | Reads visible commands and button modes directly from global config. |
| `settings_ui/src/editor-inline/GraphVisualizer.svelte` | Reads `selectionMarkerShiftButtonsEnabled` directly from global config. |
| `settings_ui/src/editor-inline/SplitExtraFields.svelte` | Reads source filename from global config. |
| `settings_ui/src/editor-inline/split-button-state-defaults.ts` | Stores split-button state on `window.__aqeSplitButtonStates` and reads global config defaults. |
| `settings_ui/src/editor-inline/post-edit-playback.ts` | Reads pending playback and repeat defaults from global config/state. |
| `settings_ui/src/editor-inline/control-actions.ts` | Reads repeat defaults, active field, initial status/history state, and history globals. |
| `settings_ui/src/editor-inline/graph-actions.ts` | Reads/writes active field and pending graph-redraw globals; also reads source filenames from config. |
| `settings_ui/src/batch/batch-state.ts` | `initialBatchState()` reads `window.__AQE_BATCH_INITIAL_STATE__`. |
| `settings_ui/src/settings/settings-state.ts` | `initialState()` reads `window.__INITIAL_STATE__`. |

**SOLID impact**

| Principle | Assessment |
|---|---|
| DIP | High. Pure factories and state helpers depend on one injection mechanism. |
| SRP | Medium. Runtime wiring, browser globals, and UI logic are mixed. |
| ISP | Medium. Global contracts expose a large shared surface to many modules. |

**Better solution**

Create small runtime adapters and parameterize pure functions:

- `editor-runtime-config.ts`: `editorRuntimeConfig()`, `splitButtonDefaults(config)`, `visibleEditorButtons(config)`.
- `settings-initial-state.ts` and `batch-initial-state.ts`: the only places that read screen initial-state globals.
- Keep `window-contract.ts` as the only editor module that registers callable `window.__aqe*` functions.

Then change factories such as `commandButtons(config)` and `processingMessage(command, payload, config)` to accept config explicitly.

### 4.4 `diagnostics.py` health probes - MEDIUM-HIGH

The original point is valid. `build_deep_filter_health`, `build_rnnoise_health`, `build_dpdfnet_health`, `build_spleeter_health`, and `build_silero_vad_health` repeat the same algorithm:

1. Lazily import audio tool lookup helpers.
2. Resolve expected path/source.
3. Run a short subprocess probe with common encoding, timeout, and command kwargs.
4. Convert `OSError`, timeout, and non-zero returns into the same health shape.

The Spleeter and Silero probes already share some helper structure, which shows the direction but not the full abstraction.

**SOLID impact**

| Principle | Assessment |
|---|---|
| OCP | Medium-high. New tools require another builder clone. |
| SRP | Medium. Probe running, path resolution, source labeling, and result formatting are interleaved. |
| DIP | Low-medium. The direct `subprocess.run` call is acceptable in this import-safe runtime module, but should be behind a small helper for tests and consistency. |

**Better solution than the original**

Avoid a large generic framework with too many callbacks. Use two simple layers:

- `run_tool_probe(path, args, timeout_label, run_kwargs) -> ProbeResult | ToolHealthDict`
- `build_version_health(...)` and `build_help_health(...)` helpers for the two actual probe styles.

Keep per-tool functions as thin wrappers so external callers and tests do not churn.

### 4.5 Batch facade indirection - MEDIUM-HIGH

The original review called this a DIP violation. That is mostly correct, but the current code is more nuanced:

- `batch_operations.py` directly imports and re-exports several `audio_processor` functions.
- `batch_operation_processing.py` imports `make_output_filename` and `temp_final_path` directly from `audio_processor`, but still uses `_facade_attr()` to fetch `analyze_prosody_cached`, `render_converted_audio`, `render_size_reduced_audio`, and `render_audio` from `batch_operations`.
- `batch_operations_helpers.py` directly imports denoise renderers, but still lazy-loads `batch_operations` so tests can patch facade exports.

**Assessment**

The pattern is probably a compatibility/test seam, not accidental confusion. It still has real cost: dependencies are hidden, static analysis sees less, and graph output has intentional circular workarounds.

**Better solution**

Introduce an explicit `BatchRenderers`/`BatchAnalysisDeps` object passed into `process_graph_operation`, `process_transform_operation`, and `render_batch_denoise`. The production facade can build it from `audio_processor` and `prosody_cache`; tests can pass fakes. That removes `_facade_attr()` without losing testability.

### 4.6 Editor field replacement workflow duplication - MEDIUM-HIGH

The original review compared `replace_current_field_after_render` and `replace_current_field_after_noise_removal`. The similar pattern also exists in `replace_current_field_after_region_delete`.

Shared sequence:

1. Validate processing guard.
2. Persist generated media.
3. Resolve field index and current sound reference.
4. Replace the sound reference in field HTML.
5. Update session state/history.
6. Request playback/graph/history refresh.
7. Clear busy state or request redraw.

The duplication is not identical because standard render, special transform, and region delete each update session state differently. A single giant "replacement service" would become a new god function.

**Better solution**

Extract only the stable primitives:

- `persist_generated_media(...)`
- `replace_first_sound_reference_in_field(...)`
- `finish_media_replacement_ui(...)`

Keep workflow-specific session updates local unless they converge naturally.

### 4.7 `SplitButton.svelte` interface surface - MEDIUM

The original review said "parameter explosion" and recommended generic parameter binding. The concern is real, but the proposed generic binding is risky.

Current facts:

- `SplitButton.svelte` keeps 24 local state values.
- It passes a large prop/action surface into `SplitButtonMenu.svelte`.
- Some presenter and state behavior has already been extracted into `split-button-presenter.ts`, `split-button-state.ts`, `split-button-state-behavior.ts`, size-reduction helpers, graph helpers, and pause helpers.

**Assessment**

This is an ISP/component interface issue, not a pure SRP failure. The component coordinates a real UI control that has many options.

**Better solution**

Pass grouped value/action objects rather than inventing a generic binding engine:

- `splitValues`: current values for speed, volume, pause, denoise, conversion, size reduction, sharing, graph, recording.
- `splitActions`: the corresponding update functions.
- `splitUi`: open/default-saved/menu-title/primary metadata.

This shrinks the component boundary and keeps type safety.

### 4.8 `diagnostics_runtime.py` - MEDIUM

The original HIGH is too strong.

Current facts:

- The file is 364 lines and contains state, breadcrumbs, incident capture, support-report context, session cleanup, runtime file release, and test reset.
- Some storage/process-hook code is already split into `diagnostics_runtime_storage.py`.
- `capture_exception` and `record_frontend_error` duplicate incident construction enough to justify a helper.

**Assessment**

This module is cohesive around runtime diagnostics. It is broad, but not chaotic. Split only around stable seams:

- Incident construction/capture helper.
- Optional breadcrumb ring/state class extraction if the file grows.

Do not split into four modules as an immediate task unless related diagnostics work is already planned.

### 4.9 `audio_rendering.py` - LOW-MEDIUM

The original MEDIUM is somewhat overstated.

`audio_rendering.py` mixes render orchestration and output path helpers, but those helpers are tightly tied to render output naming and temp paths. `render_audio_region_deleted` and `render_audio_region_kept` are intentionally parallel and already share `_render_region_filter_complex`.

Possible cleanup when touched:

- Extract filename/temp-path helpers to `audio_render_paths.py`.
- Keep render functions explicit; a generic render-template abstraction would likely obscure more than it removes.

### 4.10 `audio_recording.py` - LOW-MEDIUM

The original MEDIUM should be lowered.

This module is import-safe and already lazy-loads Qt/Anki-specific pieces. It does mix `RecordingController`/`RecordingResult` with native backends, but the abstraction is small and local.

Split only if voice recording grows:

- `audio_recording.py`: protocol, result, errors.
- `audio_recording_native.py`: `NativeRecordingController` and backend implementations.

### 4.11 `reviewer_integration.py` - MEDIUM

The original point is partly valid but stale in one place: audio target detection is already partly extracted into `reviewer_audio_targets.py`.

Remaining concerns:

- Hook registration, adapter, visibility state, bridge wrapping, and current-side rendering are in one file.
- `_reviewer_editor_visible`, `_reviewer_editor_manual_override`, and `_EXPLICIT_PANEL_CARD_KEYS` are module globals.
- `_handle_reviewer_bridge_command()` directly calls `_handle_bridge_command(adapter, command)`.

Better solution:

- Extract `ReviewerEditorVisibility` state object and pure target/showing predicates first.
- Consider injecting the bridge handler into `register_reviewer_hooks()` only if tests or future reviewer modes need it.
- Do not split audio target logic again; it is already extracted.

### 4.12 `batch/batch-state.ts` - MEDIUM

The original HIGH is too strong, but the file is a good frontend DIP example.

Current concerns:

- Type definitions, fallback state, initial state read, form initialization, request building, and parameter clamping live together.
- `initialBatchState()` directly reads `window.__AQE_BATCH_INITIAL_STATE__`.
- `batchStartRequest()` has an operation-parameter mapping chain that will grow with operations.

Better solution:

- Move only the global read into `batch-initial-state.ts`.
- Move request construction into `batch-request-builder.ts` when adding the next operation.
- Keep fallback defaults near the state type until the generated contract or backend defaults can own them.

### 4.13 Generated contracts and `lib/types.ts` - LOW

The original review called `contracts.ts` a monolith and `lib/types.ts` a kitchen-sink barrel. Both are true in a narrow sense, but low priority.

Generated monoliths are not automatically design debt. A single generated contract file is often easier to verify and diff. Splitting it is worth doing only if:

- Bundle output shows meaningful cost.
- Imports routinely create circularity.
- Screen-specific generated files would simplify tests or ownership.

`lib/types.ts` is a convenience barrel. It should not grow arbitrary handwritten types, but splitting it now is not a high-value SOLID task.

### 4.14 `GraphVisualizer.svelte` - LOW-MEDIUM

The original MEDIUM is too strong.

The component is large because it is a DOM/SVG composition root. Most behavior is already delegated to modules such as audio clock, selection gestures, zoom actions, chorusing controller, viewport actions, and recording sync. The one real issue is direct config access for `selectionMarkerShiftButtonsEnabled`.

Better solution:

- Pass `selectionMarkerShiftButtonsEnabled` as a prop from `EditorControls.svelte` or a runtime config helper.
- Extract markup subcomponents only when a feature change makes the current SVG/DOM surface hard to test.

## 5. Additional Similar Issues Found

### 5.1 Frontend globals are a named architecture boundary but not enforced

There are many direct reads/writes of injected globals. Some are intended bridge points; others are leaks. The architecture should explicitly classify them.

Suggested classification:

- **Allowed writers/readers**: `bridge.ts`, `window-contract.ts`, `runtime.ts`, `test-contract.ts`, screen initial-state adapters.
- **Disallowed direct reads**: UI components, button factories, request builders, presenter functions, and pure state helpers.

This is more important than the original isolated comments about `editor-toolbar-buttons.ts` and `batch-state.ts`.

### 5.2 Editor dependency injection is broad across every workflow

This is not only `editor_processing.py`. The `deps: Any` pattern is repeated across analysis, playback, recording, region delete, sharing, history, source metadata, and frontend refresh modules. Fixing one consumer without typing the builder pattern will only move the problem.

### 5.3 Batch processors hide test seams behind lazy facade imports

`batch_operation_processing.py` and `batch_operations_helpers.py` use lazy imports from `batch_operations` even though they also directly import some `audio_processor` functions. The result is neither pure direct dependency nor explicit injection.

### 5.4 Line-count pressure has moved to frontend runtime code too

Current over-350-line production files, excluding vendored/user runtime files:

| File | Lines | Priority |
|---|---:|---|
| `contracts_generated.py` | 1285 | Generated; ignore for SOLID. |
| `settings_ui/src/lib/generated/contracts.ts` | 453 | Generated; low. |
| `settings_ui/src/editor-inline/playback-controller.ts` | 440 | Worth later review; not in original file. |
| `audio_rendering.py` | 399 | Low-medium. |
| `settings_ui/src/editor-inline/SplitValueOptions.svelte` | 393 | Worth later review; likely paired with SplitButton work. |
| `audio_tools.py` | 389 | Low; mostly repetitive tool lookup. |
| `editor_processing.py` | 383 | Medium because of replacement workflow and `deps: Any`. |
| `diagnostics.py` | 379 | Medium-high because of cloned probes. |
| `settings_ui/src/editor-inline/plot.ts` | 375 | Low unless graph behavior changes. |
| `reviewer_integration.py` | 370 | Medium. |
| `editor_playback.py` | 366 | Medium because it participates in `deps: Any`. |
| `editor_special_transforms.py` | 364 | Medium-high because of replacement workflow duplication. |
| `diagnostics_runtime.py` | 364 | Medium. |
| `settings_ui/src/editor-inline/visualizer-renderer.ts` | 363 | Worth later review; graph rendering cache/state. |
| `settings_ui/src/editor-inline/selection-gestures.ts` | 363 | Worth later review; gesture complexity. |
| `audio_processor.py` | 363 | High because of duplicated dependency construction. |
| `runtime_install.py` | 360 | Low; single workflow. |
| `settings_ui/src/editor-inline/SplitButton.svelte` | 359 | Medium; large component interface. |
| `audio_recording.py` | 358 | Low-medium. |
| `settings_ui/src/editor-inline/control-actions.ts` | 357 | Medium because of global state access. |
| `editor_recording.py` | 353 | Medium only if recording work is planned. |
| `browser_batch_runner.py` | 353 | Low; cohesive runner. |

Line count should remain a smell, not a work queue.

## 6. Architecture Rules Worth Adding

These rules would catch the highest-value issues without enforcing arbitrary file splits.

### 6.1 Frontend globals only in designated adapter modules

Rule: direct reads/writes of `window.__AQE_*`, `window.__aqe*`, and `globalThis.pycmd` are allowed only in explicit runtime/bridge modules:

- `settings_ui/src/lib/bridge.ts`
- `settings_ui/src/editor-inline/bridge.ts`
- `settings_ui/src/editor-inline/window-contract.ts`
- `settings_ui/src/editor-inline/runtime.ts`
- `settings_ui/src/editor-inline/test-contract.ts`
- `settings_ui/src/batch/bridge.ts`
- screen-specific initial-state adapter files

All other modules should receive config/state as parameters or props.

### 6.2 Shared `lib/bridge.ts` should be transport-only

Rule: `settings_ui/src/lib/bridge.ts` may export generic bridge transport primitives and shared envelope types only. Settings-specific commands and callback registration should move to `settings/bridge.ts`.

Current violation: `settingsSave`, `settingsCancel`, `settingsResetDefaults`, `settingsCheckMedia`, `settingsOpenRuntimeInstaller`, `sendAsyncCmd`, `copySupportReport`, and settings callback registration live in shared `lib`.

### 6.3 One audio dependency construction point

Rule: `audio_processor.py` should construct `AudioModuleDeps` in exactly one helper. `_sync_*_dependencies()` functions may select target modules, but they should not repeat the full dependency object.

This is small, testable, and avoids premature facade churn.

### 6.4 Editor workflow dependencies must be typed

Rule: new editor workflow functions should not accept untyped `deps: Any`. They should consume a narrow `Protocol` or dataclass. Existing `deps: Any` should be migrated opportunistically when touched.

This is more useful than a broad "no SimpleNamespace" ban because tests still benefit from lightweight fakes.

### 6.5 Batch processors should use explicit dependencies

Rule: `batch_operation_processing.py` and `batch_operations_helpers.py` should not lazy-load `batch_operations` to discover renderers. Batch render/analyze dependencies should be passed explicitly or imported directly from the owning modules.

### 6.6 Diagnostics probes should use shared probe helpers

Rule: new diagnostics health checks should not copy a full `build_*_health` subprocess pattern. They should use the shared probe runner/result formatter.

## 7. Prioritized Action Items

### Immediate

1. **Centralize audio dependency construction** in `audio_processor.py`.
   - Verify with a focused test that only one `AudioModuleDeps(` construction remains.
   - Impact: removes the highest-friction OCP issue without breaking facade compatibility.

2. **Introduce typed editor dependency protocols for one workflow first.**
   - Start with `RegionDeleteDeps` or `StandardRenderDeps`; both have clear worker/main-thread boundaries.
   - Impact: proves the pattern before touching every editor module.

3. **Create frontend runtime config adapters and parameterize toolbar factories.**
   - Move config reads out of `editor-toolbar-buttons.ts`, `commands.ts`, `EditorControls.svelte`, `SelectionToolbar.svelte`, and `GraphVisualizer.svelte` as a first slice.
   - Impact: removes the broadest frontend DIP leak.

4. **Refactor `diagnostics.py` probe execution.**
   - Keep public `build_*_health` functions.
   - Extract shared run/result helpers.
   - Impact: prevents the next runtime tool from adding another clone.

### Short-term

5. **Replace batch `_facade_attr()` with explicit render/analyze dependencies.**
   - Prefer a small `BatchOperationDeps` object over direct test monkeypatching through `batch_operations`.

6. **Extract stable editor media replacement primitives.**
   - Do not build one universal replacement service.
   - Share only persistence, sound-reference replacement, and final UI refresh helpers.

7. **Shrink `SplitButton.svelte`/`SplitButtonMenu.svelte` interface.**
   - Pass grouped value/action objects.
   - Avoid a generic binding framework.

8. **Move settings-specific commands out of shared `lib/bridge.ts`.**
   - Keep generic envelope transport in `lib`.
   - Put settings commands/callbacks under `settings`.

### Deferred

9. Split `diagnostics_runtime.py` only if diagnostics grows again.
10. Split `audio_recording.py` only if recording backends gain more platform branches.
11. Split generated contracts only with measured bundle/import benefit.
12. Extract `GraphVisualizer.svelte` layers only during graph feature work.
13. Review `playback-controller.ts`, `SplitValueOptions.svelte`, `selection-gestures.ts`, and `visualizer-renderer.ts` in a separate frontend architecture pass.

## 8. Original Findings Demoted Or Rejected

| Original finding | Decision |
|---|---|
| `audio_processor.py` should split facade into `_facade.py` immediately | Rejected as first step. Keep public facade; centralize dependency construction first. |
| `diagnostics_runtime.py` is HIGH and should split into four modules immediately | Demoted to MEDIUM. Cohesive enough; extract incident helper first. |
| `audio_rendering.py` needs a generic render template | Demoted. Explicit render functions are readable; only path helpers are candidates. |
| `audio_recording.py` has serious domain/Qt mixing | Demoted. It is import-safe and lazy-loads platform APIs; split only if it grows. |
| `SplitButton.svelte` needs generic parameter binding | Rejected. Grouped state/action props are safer and clearer. |
| `contracts.ts` should be split now | Demoted to LOW. Generated monolith is acceptable until measured pain appears. |
| `lib/types.ts` kitchen-sink barrel is a meaningful SOLID issue | Demoted to LOW. Watch it, but do not prioritize. |
| `GraphVisualizer.svelte` is a hub component needing immediate subcomponents | Demoted. It is a composition root with many extracted behavior modules already. |

## 9. Bottom Line

The architecture is better than the original review implied at the layer level, but it is not SOLID-clean. The main improvement areas are explicit dependency boundaries:

- Python: replace duplicated facade wiring and untyped editor dependency bags with narrow, typed contracts.
- TypeScript: make WebView globals a clearly enforced adapter boundary.
- Diagnostics/batch/editor replacement: remove clone growth and hidden facade indirection with small, explicit seams.

Do those before chasing generic file splitting.
