# Architecture Problems — Dependency Graph Analysis

_Generated 2026-06-10 from `graphs-archive` + deep manual code review._

## 1. Executive Summary

The project's **formal architecture rules are clean**: no layer violations, no cross-screen direct imports, no import-safe core depending on UI adapters. The enforced boundaries (`architecture-report` + `import-linter` contracts) are working.

However, deep code review against SOLID principles reveals **13 modules with structural violations** and **3 intentional circular-dependency workarounds** that represent design debt. The Svelte/TS frontend has pervasive browser-global dependencies and a shared `lib/` that has accumulated settings-specific concerns.

**Top 3 priority issues:**
1. `audio_processor.py` — triple-role module (facade + DI builder + lazy proxy) with 287 lines of duplicated dependency wiring
2. `diagnostics.py` — 6 cloned health-check builders (~300 lines) that should be a single parameterized function
3. `lib/editor-toolbar-buttons.ts` — 340-line god module mixing types, button specs, denoise config, and runtime defaults; reads `window.__AQE_EDITOR_CONFIG__` directly

---

## 2. Methodology

The analysis combined:

1. **Automated graph generation** (`graphs-archive`) producing 782 cross-module relationships plus module catalogs for Python (140 modules) and Svelte/TS (166 modules)
2. **Existing tooling**: `architecture-report` (0 violations), `import-linter` (pass), `file-lines` (13 files > 350 lines)
3. **Deep manual code review** of all flagged files against SOLID principles
4. **Cross-referencing** relationship data against architecture layer rules

---

## 3. Formal Architecture Rules — Clean

All three explicit architecture rules enforced by `contracts/` pass without violations:

| Rule | Status |
|------|--------|
| Import-safe core must not import UI adapters | **Pass** |
| Settings backend must not import `editor_integration` | **Pass** |
| Batch operations must stay free of editor imports | **Pass** |

Cross-screen Svelte/TS dependencies also pass cleanly:
- Batch never imports from `editor-inline/` or `settings/`
- Settings never imports from `editor-inline/` or `batch/`
- Shared `lib/` never imports from any screen

### 3.1 Layer assignments

No "unclassified" modules in the graph — all 142 Python production modules have explicit architecture contract entries. The `unclassified` tag in the archive JSON refers to modules in sub-packages (`editor_frontend.*`) that legitimately sit as internal helpers within `ui_adapter`. No action needed.

### 3.2 Circular imports — 3 intentional patterns (acceptable but noted)

All three are mitigated via `importlib.import_module()` at call time (not module level). Each pair has explicit mutual `allowed_addon_deps` entries in contracts:

1. **`batch_operations.py` ↔ `batch_operation_processing.py`**: The processor calls `_facade_attr("render_audio")` to reach `audio_processor` functions re-exported through `batch_operations`. This creates a **DIP violation** — see §4.2.13.

2. **`audio_processor.py` ↔ `audio_processor_rendering_portal.py`**: Portal pattern. The rendering portal lazily imports `audio_processor` to access rendering functions defined there. Acceptable.

3. **`batch_operations.py` ↔ `batch_operations_helpers.py`**: Same `_facade_attr` pattern. Acceptable but could be resolved by having `batch_operations_helpers` import `audio_processor` directly.

---

## 4. SOLID Violations

### 4.1 Python — Priority findings

#### 4.1.1 `audio_processor.py` — Triple-role violation (HIGH)

| Principle | Violation |
|-----------|-----------|
| SRP | 3 roles: facade re-exporter (lines 1-74), dependency injection builder (lines 76-363), lazy-initialized proxy (lines 131-175) |
| DIP | 6 nearly identical `_sync_*_dependencies()` functions each construct a 17-field `AudioModuleDeps` with copy-pasted wiring |

**Evidence:** Lines 76-363 contain 6 `_sync_*_dependencies` builders, each ~45 lines, with `AudioModuleDeps(...)` blocks that differ only in the render function slot. Adding an 18th dependency touches 6 locations.

**Suggested refactoring:** Extract `_AudioDepsBuilder` into a separate module with a single builder. Move facade re-exports to a dedicated `_facade.py`.

---

#### 4.1.2 `diagnostics.py` — Cloned health-check builders (HIGH)

| Principle | Violation |
|-----------|-----------|
| SRP | 6 near-identical health check builders (~55 lines each, ~300 lines total) |
| OCP | Adding a 7th tool requires adding another ~55-line clone |
| DIP | No `ToolHealth` abstraction — each builder directly calls `subprocess.run` with hardcoded flags |

**Evidence:** `build_deep_filter_health` (lines 20-76) and `build_dpdfnet_health` (lines 139-196) share the same pattern: lazy import → find tool → run `--version` → parse → return dict. Only the tool name and `find_*` function differ.

**Suggested refactoring:** Introduce `ToolHealthProbe` dataclass with `tool_name`, `find_tool`, `version_arg`, `version_parser`, `source_fn` fields. Replace all 6 builders with a single `build_tool_health(probe)` function. Declare the 6 probes as configuration. Cuts ~260 lines.

---

#### 4.1.3 `diagnostics_runtime.py` — Six concerns in one module (HIGH)

| Principle | Violation |
|-----------|-----------|
| SRP | 7 distinct concerns: state singleton, breadcrumb ring buffer, exception capture, frontend error adapter, support report builder, log flushing, operation IDs |
| ISP | Callers of `new_operation_id` don't need breadcrumb ring buffer; callers of `record_breadcrumb` don't need crash log paths |

**Evidence:** `capture_exception` (lines 174-226) and `record_frontend_error` (229-266) share 80% structure (construct incident → update state → copy → return) but are implemented as two separate functions instead of one generic `_capture_incident` base.

**Suggested refactoring:** Split into 4 modules:
- `_diagnostics_state.py` — singleton class
- `_breadcrumbs.py` — ring buffer + operation IDs
- `_incident_capture.py` — unified `_capture_incident(boundary, builder)` used by both capture functions
- `_diagnostics_lifecycle.py` — `configure_runtime`, `release_runtime_files`

---

#### 4.1.4 `audio_rendering.py` — Mixed orchestration + utility (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | 6 `render_*` functions (orchestration) + 4 filename helpers (utility), ~250 + ~100 lines |
| OCP | Adding a new render type requires adding a new `render_*` function following the same template |

**Evidence:** `render_audio_region_deleted` (lines 199-222) and `render_audio_region_kept` (lines 249-272) are near-duplicates differing only in a single function call. All 6 render functions follow the same structural template.

**Suggested refactoring:** Extract `_audio_filename.py` for the 4 path helpers. Make render functions parameterize off a generic `render_tool_audio` template.

---

#### 4.1.5 `editor_dependencies.py` — Service locator anti-pattern (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| ISP | `processing_deps` packs 30 attributes into a `SimpleNamespace` — consumers that need 5 attributes get 30 |
| DIP | All consumers receive `deps: Any` with no type safety; concrete wiring replaces dependency injection |

**Evidence:** Lines 176-225 build `processing_deps` with 30 attributes. Any consumer importing this gets the full bag. The namespace has no interface contract.

**Suggested refactoring:** Define narrow `Protocol` classes: `ProcessingDeps`, `AnalysisDeps`, `PlaybackDeps`, etc. Each consumer declares its actual dependency shape. The builder still constructs everything, but consumers are typed against narrow protocols — improving testability.

---

#### 4.1.6 `audio_recording.py` — Domain types mixed with Qt code (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | 130 lines of pure Qt multimedia code (lines 229-358) mixed with domain types (RecordingController Protocol, RecordingResult dataclass) |

**Evidence:** `_QtAudioSourceRecorderBackend` (127 lines) and `_MacWavRecorderBackend` (44 lines) are platform adapters with no audio domain logic. They exist only to bridge Qt into a `RecordingController` interface.

**Suggested refactoring:** Keep `RecordingController` Protocol and `RecordingResult` in `audio_recording.py`. Move `NativeRecordingController`, `_QtAudioSourceRecorderBackend`, `_MacWavRecorderBackend` into `editor_recording.py` or `_recording_backends.py`.

---

#### 4.1.7 `editor_special_transforms.py` / `editor_conversion.py` — DRY + SRP (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | `editor_special_transforms.py` (364 lines): transform orchestration + field replacement + failure logging |
| SRP (cross-module) | `replace_current_field_after_noise_removal` (246-286) and `editor_processing.py:replace_current_field_after_render` (226-290) are structural near-duplicates |

**Suggested refactoring:** Extract shared field-replacement logic into `_transform_field_replacement.py`. Extract failure logging (lines 316-364) into `_transform_failure_logging.py`.

---

#### 4.1.8 `reviewer_integration.py` — Four concerns (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | Adapter class + Anki hook wiring + UI visibility state + audio target detection |
| DIP | Directly calls `_handle_bridge_command(adapter, command)` instead of receiving an injected bridge handler |

**Evidence:** Lines 350-355 use module-level mutable globals (`_reviewer_editor_visible`, `_reviewer_editor_manual_override`) that all 6 hook callbacks reference. Unit-testing the visibility toggle requires initializing all hook infrastructure.

**Suggested refactoring:** Extract `_reviewer_visibility.py` (~50 lines) and `_reviewer_audio_targets.py` (~50 lines). Inject bridge handler via `register_reviewer_hooks(..., bridge_handler: Callable)`.

---

#### 4.1.9 `batch_operations.py` — Re-export hub + lazy workaround (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| DIP | `batch_operation_processing.py` doesn't import `audio_processor` directly — it goes through `_facade_attr("render_audio")` which routes through `batch_operations.py`'s re-exports |
| SRP | `batch_operations.py` is both a public API module AND a re-export hub for 8 `audio_processor` functions |

**Suggested refactoring:** Remove the 8 re-exports from `batch_operations.py` `__all__`. Have `batch_operation_processing.py` import `audio_processor` and `prosody_cache` directly. Delete the `_facade_attr` helper.

---

#### 4.1.10 `editor_processing.py` — Orchestrator overload (LOW-MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | 3 roles: render orchestration + field replacement + re-exports (lines 49-61) |
| ISP | `deps: Any` has 30+ attributes; `processing_deps` builder is a service locator |

**Suggested refactoring:** Move re-exports to `editor_callbacks.py` or have callers import `editor_special_transforms` directly. Extract `_field_replacement.py` with `replace_current_field_after_render` and its helpers.

---

### 4.2 Python — Additional non-SOLID concerns

#### 4.2.1 Files exceeding 350-line limit

13 files exceed the project's soft limit. Most are 10-50 lines over and have reasonable cohesion. Highest-priority splits:

| File | Lines | Reason for concern |
|------|-------|--------------------|
| `audio_rendering.py` | 399 | Mixed orchestration + utility file roles |
| `audio_tools.py` | 389 | Repetitive `find_*` functions (acceptable SRP, just verbose) |
| `editor_processing.py` | 383 | Multi-role coordinator |
| `diagnostics.py` | 379 | Cloned health check builders |
| `reviewer_integration.py` | 370 | Mixed concerns |
| `editor_playback.py` | 366 | Tightly coupled playback orchestration |
| `editor_special_transforms.py` | 364 | Transform + field replacement + logging |
| `diagnostics_runtime.py` | 364 | 7 concerns in one module |
| `audio_processor.py` | 363 | Triple-role violation |
| `runtime_install.py` | 360 | Single concern, many steps (acceptably low priority) |
| `audio_recording.py` | 358 | Domain types + Qt code |
| `editor_recording.py` | 353 | Acceptable cohesion |
| `browser_batch_runner.py` | 353 | Acceptable cohesion |

#### 4.2.2 No wildcard imports found

Zero instances of `from ... import *`. Good practice maintained.

---

### 4.3 Svelte/TypeScript — Priority findings

#### 4.3.1 `lib/editor-toolbar-buttons.ts` — God module (HIGH)

| Principle | Violation |
|-----------|-----------|
| SRP | 4 concerns in 340 lines: types + button specs + denoise config + runtime defaults |
| DIP | Lines 118, 311 read `window.__AQE_EDITOR_CONFIG__` directly instead of accepting config as a parameter |

**Suggested refactoring:** Split into 3 files:
- `commands.ts` — `EditorCommand` union type + `ToolbarButtonSpec` + `EditorButtonDisplayMode`
- `button-specs.ts` — `commandButtons()` + `denoiseButtons()` factories, accepting config as parameter
- `button-defaults.ts` — `DEFAULT_VISIBLE_EDITOR_BUTTONS`, `DEFAULT_EDITOR_BUTTON_MODES`, `buttonDisplayMode()`

---

#### 4.3.2 `lib/bridge.ts` — Settings bias in shared lib (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | 3 layers: low-level transport (lines 14-45), settings commands (47-65), async callbacks (67-99) |
| ISP | `registerCallbacks()` merges async, save-error, and runtime-installer callbacks into one `BridgeCallbacks` — batch doesn't use any of them |

**Suggested refactoring:**
- Move transport core (`sendBridgeEnvelope`, `sendBridgeCommand`, `encodeBridgeCommand`) to `lib/bridge-transport.ts`
- Move settings commands to `settings/bridge.ts`
- Remove `registerCallbacks()` — each screen registers its own callbacks

---

#### 4.3.3 `batch/batch-state.ts` — SRP + DIP (HIGH)

| Principle | Violation |
|-----------|-----------|
| SRP | 4 concerns: type defs + static defaults + state initialization + request building |
| DIP | Line 156: `window.__AQE_BATCH_INITIAL_STATE__` read directly instead of being injected |

**Evidence:** Lines 61-153: 93-line `FALLBACK_BATCH_INITIAL_STATE` constant. Lines 209-258: 49-line `batchStartRequest()` with an if-else chain mapping form fields to request parameters.

**Suggested refactoring:** Split into `batch-types.ts`, `batch-defaults.ts`, `batch-form-factory.ts`, `batch-request-builder.ts`.

---

#### 4.3.4 `SplitButton.svelte` — Parameter explosion (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | 24 `$state` variables (lines 55-77) covering every possible split-button parameter; 140-line callback setup wire-up |

**Suggested refactoring:** Group parameters by category (speed, volume, denoise, pause, graph, size-reduction) into Svelte runes stores. Use a generic parameter binding mechanism.

---

#### 4.3.5 `lib/generated/contracts.ts` — Monolith coupling (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| ISP | Single 453-line file contains types for settings, batch, AND editor — any import touches all |

**Suggested refactoring:** Split the contract generator output into `settings-contracts.ts`, `batch-contracts.ts`, `editor-contracts.ts`, and `common-contracts.ts`.

---

#### 4.3.6 `lib/types.ts` — Kitchen-sink barrel (LOW)

| Principle | Violation |
|-----------|-----------|
| ISP | Re-exports 47 symbols — batch-only types (`BatchStartRequest`) coexist with settings-only and shared types |

**Suggested refactoring:** Split into `contracts-barrel.ts` (re-exports) and `async-bridge-types.ts` (locally defined bridge protocols). Encourage direct `contracts.ts` imports for specific types.

---

#### 4.3.7 `editor-inline/field-state-store.ts` — Mixed concerns (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | In-memory state storage (Map-based CRUD) + DOM parsing (reads `dataset` attributes from visualizer elements) |

**Evidence:** Lines 109-131 contain 7 private DOM-parsing helper functions (`playbackStateForDataset`, `playbackClockModeForDataset`, etc.) that have nothing to do with state storage.

**Suggested refactoring:** Extract DOM-parsing logic to `field-state-dom-reader.ts`.

---

#### 4.3.8 `GraphVisualizer.svelte` — Hub component (MEDIUM)

| Principle | Violation |
|-----------|-----------|
| SRP | Coordinates 6+ subsystems (graph layout, audio clock, zoom controls, selection gestures, chorusing markers, recording overlay, time viewport) in a single `onMount` |

**Suggested refactoring:** Extract `CursorOverlay.svelte`, `SelectionLayer.svelte`, `ChorusingMarkersLayer.svelte`. Use a `useGraphVisualizer()` composable for the mount orchestration.

---

### 4.4 Svelte/TS — Cross-cutting concerns

#### 4.4.1 Browser global dependencies — pervasive DIP violation

12 modules directly access `window.*` or `globalThis.*` without any abstraction:

| File | Global(s) accessed |
|------|-------------------|
| `lib/editor-toolbar-buttons.ts` | `window.__AQE_EDITOR_CONFIG__` |
| `lib/bridge.ts` | `globalThis.pycmd` |
| `batch/batch-state.ts` | `window.__AQE_BATCH_INITIAL_STATE__` |
| `editor-inline/commands.ts` | `window.__AQE_EDITOR_CONFIG__` |
| `editor-inline/bridge.ts` | 7 different `window.__aqe*` globals |
| `editor-inline/split-button-state-defaults.ts` | `window.__aqeSplitButtonStates`, `window.__AQE_EDITOR_CONFIG__` |
| `editor-inline/GraphVisualizer.svelte` | `window.__AQE_EDITOR_CONFIG__` |

None are injected or abstracted. This creates hard coupling between UI components and a specific injection mechanism.

#### 4.4.2 Code duplication

| Duplication | Locations |
|-------------|-----------|
| `formatDenoiseAlgorithm` | `lib/editor-toolbar-buttons.ts:110-115` AND `editor-inline/split-button-formatters.ts:7-12` |
| `formatPauseDetectionAlgorithm` | `lib/audio-operation-parameters.ts:101-104` AND `editor-inline/split-button-formatters.ts:23-25` |

---

## 5. Additional Architecture Rules to Add

The following rules should be codified into the architecture contracts to prevent regression:

### 5.1 `lib/bridge.ts` — No screen-specific callbacks or commands

**Rule:** `src/lib/bridge.ts` may only export generic transport primitives (`sendBridgeEnvelope`, `sendBridgeCommand`, `encodeBridgeCommand`). Settings-specific commands (`settingsSave`, `settingsCancel`, `settingsCheckMedia`, `settingsOpenRuntimeInstaller`, `sendAsyncCmd`, `copySupportReport`) and callback registration (`registerCallbacks`) must live in `settings/bridge.ts`.

**Rationale:** Prevents shared `lib/` from accumulating screen-specific code. Today only settings leaks in; tomorrow batch or a new screen might.

### 5.2 Browser globals — Inject, don't read directly

**Rule:** No TypeScript/Svelte module (except designated bridge files) may read `window.__AQE_*` or `globalThis.pycmd` directly. All configuration and bridge transport must be injected via function parameters or Svelte context.

**Rationale:** Direct global reads prevent unit testing and create hard coupling between UI logic and injection mechanism.

### 5.3 Monolithic generated contracts — Split output

**Rule:** The contract generator (`scripts/generate_contracts.py`) should output separate files: `settings-contracts.ts`, `batch-contracts.ts`, `editor-contracts.ts`, and `common-contracts.ts`.

**Rationale:** A 453-line monolith mixes types for all three screens.

### 5.4 `editor_dependencies.py` — Narrow protocols over `SimpleNamespace`

**Rule:** Consumers of editor dependency injection must declare their dependency shape via a `typing.Protocol` instead of receiving `deps: Any`.

**Rationale:** The current pattern gives every consumer a 30-attribute bag regardless of actual needs.

### 5.5 `lib/editor-toolbar-buttons.ts` — No config from globals

**Rule:** `commandButtons()` and `denoiseButtons()` must accept configuration as explicit parameters. Defaults derived from `window.__AQE_EDITOR_CONFIG__` are the caller's responsibility.

**Rationale:** Makes the button-spec factories testable and reusable without browser globals.

### 5.6 `diagnostics` module — Tool health via configuration

**Rule:** New tool health probes must be defined as declarative `ToolHealthProbe` data, not as new `build_*_health` functions.

**Rationale:** Prevents clone growth — today there are 6 builders, tomorrow could be 8.

---

## 6. Prioritized Action Items

### Immediate (architectural debt):

1. **Split `audio_processor.py`**: Extract DI builder into `_audio_deps_builder.py`, facade into `_facade.py` (removes 287 lines of duplicate wiring)
2. **Refactor `diagnostics.py`**: Replace 6 builders with 1 parameterized function + 6 probe configs (removes ~260 lines)
3. **Extract `diagnostics_runtime.py`** into 4 modules: state, breadcrumbs, incident capture, lifecycle
4. **Extract `lib/bridge.ts`** settings code into `settings/bridge.ts`

### Short-term (quality-of-life):

5. **Split `lib/editor-toolbar-buttons.ts`** into commands + button-specs + button-defaults
6. **Extract `batch-state.ts`** into types + defaults + form-factory + request-builder
7. **Split `reviewer_integration.py`**: Extract visibility module + audio targets module
8. **Extract field-replacement logic** from `editor_processing.py` and `editor_special_transforms.py` into shared `_transform_field_replacement.py`
9. **Type `deps` as Protocols** instead of `Any`/`SimpleNamespace`
10. **Remove `_facade_attr` workaround** in `batch_operation_processing.py` — import `audio_processor` directly

### Long-term (nice-to-have):

11. **Split `contracts.ts`** generation into per-screen output files
12. **Extract `GraphVisualizer.svelte`** sub-components
13. **Extract `SplitButton.svelte`** parameter groups into stores
14. **Extract `field-state-store.ts`** DOM readers into separate module
