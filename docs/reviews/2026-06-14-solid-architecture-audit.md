# SOLID Architecture Audit

Date: 2026-06-14

Fresh independent audit of Python and Svelte/TypeScript subprojects against SOLID principles and architectural cleanliness. Prior reviews (`2026-06-09-architecture-problems.md`, `2026-06-10-architecture-problems-ds.md`) are referenced where findings overlap but this document is independently derived from source reading.

---

## Executive Summary

The project has strong **formal layer enforcement** — import-linter contracts and architecture tests prevent illegal cross-layer imports. However, within those layers, several SOLID violations create friction for future development. The most impactful problems are:

1. **Untyped dependency injection bags** (`deps: Any` / `SimpleNamespace`) across all Python editor workflows — an ISP and DIP problem that makes every editor module brittle to change.
2. **DOM-as-state in the frontend** — 23+ `dataset` attributes serve as the runtime state machine for the inline editor, violating SRP and making state transitions untestable without a browser.
3. **Duplicated dependency wiring** in the audio facade — OCP violation that requires touching every `_sync_*` block when adding one field to `AudioModuleDeps`.
4. **Ambient global reads** in frontend logic modules — DIP violation where pure UI/state code directly reads `window.__AQE_*` instead of receiving config through parameters.

---

## Python Subproject

### 1. Untyped Dependency Bags — HIGH (ISP + DIP)

**Files:** `editor_dependencies.py` (367 lines), `editor_callbacks.py` (290 lines), `editor_processing.py`, `editor_special_transforms.py`, `editor_region_delete.py`, `editor_playback.py`, `editor_analysis.py`, `editor_recording.py`, `editor_sharing.py`, `editor_history.py`

**Problem:** Every editor workflow function receives `deps: Any` — an untyped `SimpleNamespace` built by `editor_dependencies.py`. The `processing_deps` bag alone has 40+ attributes. `editor_dependencies.py` builds 10 separate dependency bags (bridge, processing, playback, analysis, recording, sharing, history, settings actions, region delete, frontend), each as a `SimpleNamespace` with no type contract.

```python
# editor_dependencies.py:189 — processing_deps has 40+ untyped attributes
def processing_deps(callbacks, frontend_callbacks) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_root=...,
        can_persistent_undo=...,
        config=...,
        current_field_audio_missing=...,
        # ... 36 more attributes
    )
```

`editor_callbacks.py` wraps every function with `_with_deps(func, deps_builder)` — a runtime-only binding that hides the dependency shape from static analysis:

```python
# editor_callbacks.py:153
_update_state_and_render = _with_deps(editor_processing.update_state_and_render, _processing_deps)
```

**Why this is bad for future development:**
- **ISP violation:** Every consumer receives 40+ attributes when it typically needs 5-10. Adding an attribute to one bag silently changes the interface for all consumers.
- **DIP violation:** The dependency "contract" is implicit string attributes on `SimpleNamespace`. A typo (`deps.eval_statu` instead of `deps.eval_status`) fails only at runtime.
- **Discoverability:** A new developer cannot determine what a function needs by reading its signature. They must read the function body and trace every `deps.*` access.
- **Refactoring cost:** Changing the name of one dependency attribute requires searching every function that uses the bag, not just the builder.

**Recommendation:** Introduce narrow `Protocol` definitions per workflow (`StandardRenderDeps`, `PlaybackDeps`, `AnalysisDeps`, etc.) in `editor_deps_protocols.py`. `RegionDeleteDeps` already exists as a typed protocol — extend the pattern. Keep `SimpleNamespace` for test fakes but type the consuming functions.

---

### 2. Audio Facade Dependency Wiring — HIGH (OCP + DIP)

**Files:** `audio_processor.py` (267 lines), `audio_processor_runtime.py`, `audio_processor_rendering_portal.py`

**Problem:** `audio_processor.py` is a backward-compatible facade that re-exports symbols from 8 implementation modules. It constructs `AudioModuleDeps` (a 19-field dataclass) in 6 separate `_sync_*_dependencies()` functions, each repeating nearly identical construction:

```python
# audio_processor.py:80-101 — one of 6 nearly identical builders
def _audio_module_deps() -> AudioModuleDeps:
    return AudioModuleDeps(
        find_ffmpeg=find_ffmpeg,
        find_ffprobe=find_ffprobe,
        find_deep_filter=find_deep_filter,
        # ... 16 more fields
    )
```

The `_sync_*` functions then inject dependencies into implementation modules via `audio_processor_runtime.py`, which uses `setattr()` with `cast(Any, module)`:

```python
# audio_processor_runtime.py pattern
setattr(module, "subprocess", deps.subprocess)  # type: ignore
```

**Why this is bad for future development:**
- **OCP violation:** Adding one field to `AudioModuleDeps` requires updating all 6 construction blocks. Forgetting one causes a runtime `AttributeError` in the unpatched module.
- **DIP violation:** Implementation modules (`audio_rendering`, `audio_noise_reduction`, etc.) receive dependencies through module-global mutation, not constructor injection. The injection is invisible to type checkers.
- **Fragility:** If any code path calls a rendering function before `_sync_*` runs, the result is an opaque `AttributeError` with no diagnostic about missing injection.

**Recommendation:** Centralize into one `_audio_module_deps()` helper (already partially exists). Have all `_sync_*` functions call it. Replace module-global `setattr` injection with explicit `configure(deps)` functions on each module that validate required attributes at call time.

---

### 3. EditorSession Mutable State Bag — HIGH (SRP)

**File:** `editor_session.py` (358 lines)

**Problem:** `EditorSession` is a mutable dataclass with 35 fields spanning 6 distinct concerns:

| Concern | Fields |
|---------|--------|
| Note identity | `note_id`, `state`, `field_index`, `current_filename` |
| Undo/redo | `undo_history`, `redo_history` |
| Processing | `processing`, `processing_generation` |
| Playback | `playback_active`, `playback_paused`, `playback_preparing`, `playback_generation`, `cursor_ms`, `temp_playback_path` |
| Graph/analysis | `analysis_busy`, `analysis_busy_fields`, `analysis_generation`, `graph_active_fields`, `visualized_filename`, `visualized_duration_ms`, `visualized_*_by_field` |
| Learner recording | `learner_recording` (20+ sub-fields), `learner_recording_controller` |
| Post-edit playback | `post_edit_playback_generation`, `pending_post_edit_playback_*` |
| Status | `next_status_summary`, `status_summary`, `pending_status` |

`reset_for_note_load()` manually resets 25+ fields — any new field added to `EditorSession` that needs resetting must be manually added to this function.

**Why this is bad for future development:**
- **SRP violation:** One object owns undo history, playback state, graph analysis state, learner recording state, and processing guards. These are independent concerns that happen to share an editor lifetime.
- **No invariant enforcement:** Nothing guarantees `processing=True` implies `playback_active=False`, or that `learner_recording.status="recording"` implies `processing=False`.
- **Silent drift:** Adding a field to `EditorSession` without updating `reset_for_note_load()`, `clear_processing_for_stale_guard()`, or `begin_processing_guard()` causes stale state bugs that are hard to diagnose.

**Recommendation:** Split into focused state objects: `ProcessingState`, `PlaybackState`, `GraphAnalysisState`, `LearnerRecordingState`. Compose them in `EditorSession`. Each sub-object owns its own reset logic.

---

### 4. Editor Callbacks Indirection Layer — MEDIUM-HIGH (SRP)

**Files:** `editor_callbacks.py` (290 lines), `editor_frontend_callbacks.py` (311 lines)

**Problem:** `editor_callbacks.py` exists solely to wire dependency bags to functions. It contains 60+ module-level assignments of the form:

```python
_handle_bridge_command = _with_deps(editor_bridge.handle_bridge_command, _bridge_deps)
_update_state_and_render = _with_deps(editor_processing.update_state_and_render, _processing_deps)
_play = _with_deps(editor_playback.play, _playback_deps)
# ... 50+ more
```

`editor_frontend_callbacks.py` is a parallel layer that wraps frontend eval functions with their own dependency builders.

**Why this is bad for future development:**
- Every new editor function requires a wiring line in `editor_callbacks.py` AND a corresponding entry in the dependency builder.
- The `_exports()` function dynamically collects all `_`-prefixed module-level callables via `globals()` — a metaprogramming pattern that defeats static analysis and IDE navigation.
- The two-layer wrapping (`_with_deps` → `_deps` → `_exports`) makes call chains hard to trace during debugging.

**Recommendation:** Consider a lighter composition root pattern. The current approach works for testability but the `_exports()` metaprogramming should be replaced with explicit namespace construction.

---

### 5. Diagnostics Probe Duplication — MEDIUM (OCP)

**File:** `diagnostics.py` (312 lines)

**Problem:** `build_deep_filter_health`, `build_rnnoise_health`, `build_dpdfnet_health`, `build_spleeter_health`, and `build_silero_vad_health` repeat the same algorithm:
1. Resolve expected path via lazy import
2. Run subprocess probe with common timeout/encoding
3. Convert `OSError`, timeout, and non-zero exit into the same health shape

Each function is 30-50 lines of nearly identical structure with different tool names and probe arguments.

**Why this is bad for future development:**
- **OCP violation:** Adding a new runtime tool requires copying another 40-line health check function.
- Bug fixes in probe error handling must be applied to 5+ functions.

**Recommendation:** Extract `run_tool_probe(path, args, timeout, label)` → `ToolProbeResult` and `build_version_health(probe_fn, ...)` / `build_help_health(probe_fn, ...)` helpers. Keep per-tool functions as thin wrappers.

---

### 6. Editor Field Replacement Workflow Duplication — MEDIUM (DRY)

**Files:** `editor_processing.py:228-288`, `editor_special_transforms.py` (replace_current_field_after_noise_removal), `editor_region_delete.py` (replace_current_field_after_region_delete)

**Problem:** Three "replace field after X" functions share a 7-step pattern:
1. Validate processing guard
2. Persist generated media
3. Resolve field index
4. Replace sound reference in field HTML
5. Update session state and undo history
6. Request playback/graph/history refresh
7. Clear busy state or request redraw

The steps are similar but not identical — each has different session state updates.

**Why this is bad for future development:**
- Adding a new post-replacement behavior (e.g., a new UI refresh step) must be applied to all three functions.
- The subtle differences between the three make it easy to accidentally apply a change from one to another that doesn't share that behavior.

**Recommendation:** Extract stable primitives (`persist_generated_media`, `replace_first_sound_reference_in_field`, `finish_media_replacement_ui`) without creating a single "replacement service" god function.

---

### 7. Config Key Propagation — MEDIUM (DRY)

**Files:** `config.schema.json`, `config.json`, `editor_webview_injection.py:88-126`, `config_migration.py`, `settings_ui/src/`

**Problem:** `editor_webview_injection.py` contains a manually maintained `split_button_defaults` dict with ~30 config keys. This dict does not derive from the schema or generated contracts — it is a parallel source of truth. Adding a config key requires touching:
1. `config.schema.json`
2. `config.json`
3. `editor_webview_injection.py` (split_button_defaults)
4. `config_migration.py`
5. Settings UI source
6. E2E test helpers

**Why this is bad for future development:**
- Forgetting step 3 means the editor doesn't receive the new default, but no test catches it until an e2e scenario exercises the path.
- The manual dict drifts from the schema over time.

**Recommendation:** Generate the injection dict from the schema or from a shared config-defaults module. The generated contracts already exist for Python/TypeScript boundary — extend the pattern to the injection surface.

---

### 8. Error System Fragmentation — LOW-MEDIUM (SRP)

**Files:** `errors.py`, `error_codes.py`, `contracts_generated.py` (UserFacingError)

**Problem:** Three overlapping error systems:
- `errors.py`: Python exception hierarchy (12 subclasses of `AudioQuickEditorError`)
- `error_codes.py`: `UserFacingError` dataclass with stable string codes and help URLs
- `contracts_generated.py`: Generated `UserFacingError` for JSON serialization

A `MissingFfmpegError` exception does not automatically produce a `UserFacingError` with a help URL.

**Why this is bad for future development:**
- New error conditions must be added to multiple systems.
- The mapping between exception types and user-facing error codes is manual and can drift.

---

## Svelte/TypeScript Subproject

### 9. DOM-as-State — HIGH (SRP + Testability)

**Files:** `control-actions.ts` (399 lines), `playback-controller.ts` (372 lines), `selection-gestures.ts` (363 lines), `graph-actions.ts` (292 lines), `field-state-dom-sync.ts`

**Problem:** The inline editor frontend stores its source of truth in DOM `dataset` attributes. Key state encoded as stringly-typed DOM attributes:

| State | DOM attribute |
|-------|--------------|
| Busy | `document.body.dataset.aqeBusy` |
| Playback state | `button.dataset.aqeButtonState` |
| History availability | `controls.dataset.aqeCanUndo`, `controls.dataset.aqeCanRedo` |
| Source filename | `controls.dataset.aqeSourceFilename` |
| Status message/kind | `status.dataset.stableMessage`, `status.dataset.stableKind` |
| Visualizer state | `visualizer.dataset.aqeTargetDurationMs` |

`control-actions.ts` functions like `setControlsBusy()` mutate `document.body.dataset` and then query all buttons to update their disabled state:

```typescript
export function setControlsBusy(ord, busy, message, command): void {
    document.body.dataset.aqeBusy = busy ? "true" : "false";
    document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
        controls.dataset.busy = busy ? "true" : "false";
    });
    allButtons().forEach((button) => {
        updateButtonDisabledState(button);
    });
}
```

**Why this is bad for future development:**
- **SRP violation:** DOM elements serve as both UI presentation and state storage. Changing the DOM structure (e.g., removing a wrapper div) can break state propagation.
- **Untestable:** Pure state transitions cannot be tested without `jsdom` or a real browser. Every test must mount a full DOM.
- **Stringly typed:** `dataset.aqeBusy = "true"` has no type safety. A typo in the attribute name silently fails.
- **Implicit coupling:** Any module can read `document.body.dataset.aqeBusy` — there is no central state owner.

**Recommendation:** Introduce a typed `EditorFieldStateStore` (already partially exists as `field-state-store.ts` and `field-state.ts`) as the source of truth. Keep DOM dataset as a derived view for CSS, not as the canonical state. The prior review noted this was planned but never completed.

---

### 10. Ambient Global Config Reads — HIGH (DIP)

**Files:** `editor-toolbar-buttons.ts`, `commands.ts`, `EditorControls.svelte`, `SelectionToolbar.svelte`, `GraphVisualizer.svelte`, `split-button-state-defaults.ts`, `control-actions.ts`, `graph-actions.ts`

**Problem:** Pure logic modules directly read injected globals instead of receiving config through parameters:

```typescript
// editor-toolbar-buttons.ts — reads global config directly
export function commandButtons(): ButtonSpec[] {
    const config = window.__AQE_EDITOR_CONFIG__;
    // ...
}
```

```typescript
// EditorControls.svelte — reads config directly
const runtimeConfig = editorRuntimeConfig();
const defaults = splitButtonDefaults(runtimeConfig);
```

`editor-runtime-config.ts` exists as a thin adapter but most modules bypass it and read `window.__AQE_EDITOR_CONFIG__` directly.

**Why this is bad for future development:**
- **DIP violation:** Pure factories and state helpers depend on a global injection mechanism rather than explicit parameters.
- **Test coupling:** Tests must mock `window.__AQE_EDITOR_CONFIG__` before importing any module that reads it, or the import fails.
- **Hidden dependencies:** Reading `commandButtons()` tells you nothing about its config requirements.

**Recommendation:** Route all config reads through `editor-runtime-config.ts` adapters. Make `commandButtons(config)`, `processingMessage(command, payload, config)`, and similar factories accept config explicitly. The adapter pattern already exists — enforce it consistently.

---

### 11. SplitButton Component Interface — MEDIUM (ISP)

**File:** `SplitButton.svelte` (373 lines), `SplitButtonMenu.svelte` (288 lines)

**Problem:** `SplitButton.svelte` manages 24+ local state values and passes a large prop/action surface into `SplitButtonMenu.svelte`. The component coordinates:
- Primary action dispatch
- Quick-settings popover state
- Value formatting for 15+ parameter types
- Field-local state persistence
- Promote-default behavior
- Menu open/close lifecycle

**Why this is bad for future development:**
- **ISP violation:** The component receives props for every possible split-button variant (speed, volume, pause, denoise, convert, share, graph, recording, pitch hum) even though each instance uses only 2-3.
- Adding a new split-button parameter type requires threading it through the full component chain.

**Recommendation:** Pass grouped value/action objects (`splitValues`, `splitActions`, `splitUi`) instead of individual props. Avoid a generic binding framework — typed objects are safer.

---

### 12. Shared `lib/bridge.ts` Contains Settings-Specific Commands — MEDIUM (SRP)

**File:** `settings_ui/src/lib/bridge.ts`

**Problem:** The shared `lib/bridge.ts` contains settings-specific commands (`settingsSave`, `settingsCancel`, `settingsResetDefaults`, `settingsCheckMedia`, `settingsOpenRuntimeInstaller`, `sendAsyncCmd`, `copySupportReport`) alongside generic bridge transport primitives.

**Why this is bad for future development:**
- **SRP violation:** The "shared" bridge library is not actually shared — it contains settings-specific logic that editor and batch modules don't use.
- Adding a new settings command requires editing the shared library rather than a settings-specific module.

**Recommendation:** Move settings-specific commands to `settings/bridge.ts`. Keep only generic envelope transport and shared types in `lib/bridge.ts`.

---

### 13. Frontend Module Proliferation — LOW-MEDIUM (Maintainability)

**Directory:** `settings_ui/src/editor-inline/` (108 files, ~14,000 lines)

**Problem:** The `actions.ts` barrel was previously split into 14 focused modules (`actions.ts`, `actions-playback.ts`, `actions-selection.ts`, `actions-audio-clock.ts`, etc.), but the split created a dense web of cross-imports. The `split-button-state*` namespace alone has 6 files:
- `split-button-state.ts` (barrel)
- `split-button-state-core.ts` (364 lines)
- `split-button-state-behavior.ts` (349 lines)
- `split-button-state-defaults.ts`
- `split-button-state-setters.ts`
- `split-button-state-commands.ts`

**Why this is bad for future development:**
- Navigating the split-button subsystem requires understanding which of 6 files owns which concern.
- The barrel re-exports hide the actual module boundaries from import analysis.
- Some modules are purely re-export barrels that add import indirection without adding clarity.

**Recommendation:** Consolidate where the split created more navigation cost than clarity. Keep barrels honest — if a barrel re-exports 90% of one module, the barrel is unnecessary overhead.

---

## Cross-Cutting Concerns

### 14. Three Overlapping Contract Systems — MEDIUM (DRY)

**Systems:**
1. Python architecture contracts (`tests/test_architecture/contract_*.py`, ~1,300 lines)
2. JSON Schema communication contracts (`contracts/communication.schema.json`)
3. Editor modification button behavior rules (`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`, 269 lines of prose)

**Problem:** These three systems enforce rules across overlapping domains but are maintained independently. Adding a new editor command requires updating:
- Python architecture contract (allowed imports/side effects)
- TypeScript bridge command list (`editor_actions.py:62-105` + `commands.ts`)
- JSON schema (if structured payload)
- Behavior rules markdown
- Architecture sync test

**Why this is bad for future development:**
- The markdown document is prose, not executable — it drifts from actual behavior.
- Contract test failures are cryptic ("module X classified in layer Y cannot import module Z") because contracts are per-module, not per-intent.
- The cost of adding a cross-boundary feature is 5+ file changes before any tests pass.

---

### 15. `editor_frontend/` vs `editor_frontend_callbacks.py` Naming — LOW (Clarity)

**Files:** `editor_frontend/` (package, 6 files), `editor_frontend_callbacks.py` (sibling module)

**Problem:** The `editor_frontend/` package and `editor_frontend_callbacks.py` are siblings with related but distinct responsibilities. `editor_frontend_callbacks.py` imports from `editor_frontend` (the package). The naming implies containment but the structure implies siblinghood.

**Why this is bad for future development:** New developers must discover that `editor_frontend_callbacks.py` is not inside the `editor_frontend/` package despite the naming.

---

## Prioritized Recommendations

### Immediate (blocks safe feature development)

| # | Action | Impact |
|---|--------|--------|
| 1 | Type one editor dependency bag (start with `RegionDeleteDeps` extension to `StandardRenderDeps`) | Proves the pattern; removes highest-friction ISP violation |
| 2 | Centralize `AudioModuleDeps` construction in `audio_processor.py` to one helper | Eliminates the OCP cliff for adding audio tools |
| 3 | Route all frontend config reads through `editor-runtime-config.ts` adapters | Removes broadest frontend DIP leak |

### Short-term (reduces maintenance friction)

| # | Action | Impact |
|---|--------|--------|
| 4 | Extract `EditorSession` sub-objects for processing, playback, graph, recording | Enables independent state reset logic and invariant enforcement |
| 5 | Refactor diagnostics probes to share a common runner | Prevents the next runtime tool from adding another 40-line clone |
| 6 | Extract stable editor media replacement primitives | Reduces triplicated post-replacement workflow |
| 7 | Move settings commands out of shared `lib/bridge.ts` | Clean SRP boundary for bridge modules |
| 8 | Make `split_button_defaults` derive from schema or shared config module | Reduces 6+ touch points per config key to 3 |

### Deferred (address during related feature work)

| # | Action | Impact |
|---|--------|--------|
| 9 | Introduce typed `EditorFieldStateStore` as source of truth (not DOM dataset) | Eliminates stringly-typed state, enables pure-function testing |
| 10 | Consolidate split-button-state modules where split created more navigation cost than clarity | Reduces module count without losing separation |
| 11 | Replace `_exports()` metaprogramming in `editor_callbacks.py` with explicit namespace construction | Improves static analysis and IDE navigation |
| 12 | Unify error system mapping (exceptions → user-facing codes) | Reduces manual mapping drift |

---

## What Is Working Well

- **Layer enforcement is solid.** Import-linter contracts prevent illegal cross-layer imports. The 5-layer model (Entry point → Import-safe core → UI adapters → Settings shell → Settings backend) is clean.
- **Shared operations are well-defined.** `audio_operations.py` is the single source of truth for batch/editor operation semantics. Editor bridge strings map to shared operations through `editor_actions.py`.
- **Contract-driven architecture** is a strong foundation. Every production module has an executable contract entry. The system catches import violations early.
- **Non-destructive media** is consistently enforced. Generated files never overwrite originals. Undo/redo history is well-structured.
- **The Svelte frontend has good component decomposition** at the visual level — `SplitButton`, `PlaySplitButton`, `HistorySplitButton`, `PresetSplitButton`, `ChorusingSplitButton` are cleanly separated. The problem is in the state management layer beneath them, not the component tree.
