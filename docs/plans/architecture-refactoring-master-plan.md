# Architecture Refactoring Master Plan

Date: 2026-06-17
Source: `docs/reviews/2026-06-09-architecture-problems.md` (22 issues, 4 tiers)

## Overview

This plan addresses all 22 architecture problems from the 2026-06-09 audit. Problems are grouped into 6 phases ordered by dependency — earlier phases unblock later ones. Each phase lists the problems it resolves, the concrete changes required, the tests to write, and the verification gate.

**Guiding principles:**
- Test-first: write characterization tests before changing behavior
- Phase independence: each phase produces a shippable, test-passing state
- No flag days: every change is incremental and reversible
- P6 is pre-planned (`docs/plans/P6-editor-session-state-bag-resolution.md`) — this plan defers to it

## Phase Dependency Graph

```
Phase 0 (Foundation)
  ├── L3 Test anti-patterns
  ├── D2 Migration validation
  └── M6 Naming collision
      │
Phase 1 (Module Splits)
  ├── P5 diagnostics_runtime.py split
  ├── P7 editor_special_transforms.py split
  └── M4 Error system unification
      │
Phase 2 (State Management)          ← highest risk, highest value
  ├── P6 EditorSession decomposition (pre-planned)
  └── P1 Frontend DOM-as-state → typed state
      │
Phase 3 (Architecture Simplification)
  ├── P2 Type the DI system
  ├── L5 Split audio_processor.py facade
  └── P3 Slim editor_integration.py
      │
Phase 4 (Developer Experience)
  ├── P4 + M1 Unify contract systems
  ├── M2 Config key propagation automation
  ├── L4 Split generated contracts
  └── M5 Pause parameter simplification
      │
Phase 5 (Documentation & Process)
  ├── D1 Structural architecture doc
  ├── D3 Superpowers docs cleanup
  └── L2 Release pipeline simplification
```

---

## Phase 0: Foundation & Safety Net

**Goal:** Remove obstacles that block later phases. Low risk, high leverage.

**Problems resolved:** L3, D2, M6

### 0.1 Fix frontend test anti-patterns (L3)

**Why first:** P1 (DOM-as-state refactor) will break every test that asserts on `window.__aqePending*` globals or mutates `dataset` attributes. Fix these tests now so Phase 2 doesn't require simultaneous test + architecture changes.

**Source:** `docs/reviews/2026-06-07-test-anti-pattern-audit.md`

**Changes:**
1. Catalog every test file that asserts on private `window.__aqe*` globals or DOM `dataset` attributes
2. For each test:
   - Replace `window.__aqePending*` assertions with assertions on observable behavior (UI state, playback state, event emissions)
   - Replace exact SVG path assertions with semantic assertions (e.g., "graph has N data points" not "path starts with M 0,100")
   - Replace mock-call-only warning checks with behavior + warning assertions
3. For e2e tests that mutate private globals to stage scenarios:
   - Replace with proper setup via the public API (bridge commands, settings changes)
   - If a scenario can't be staged publicly, add a test-only bridge command (tagged `[data-testid]`) rather than reaching into internals

**Tests to write:**
- For each refactored test: verify it still exercises the same code path by temporarily breaking the feature and confirming the test fails
- Add a new architecture test (`test_rule_no_private_window_globals.py`) that greps test files for `window.__aqe` assertions and fails if found

**Verification:** `python3 scripts/dev.py test` passes. New architecture test passes. No test file contains `window.__aqe` assertions except the architecture test itself.

**Estimated effort:** 2-3 days

### 0.2 Add migration validation tests (D2)

**Why now:** Config schema changes happen frequently. Without migration validation, a schema bump without migration code produces silent runtime failures.

**Changes:**
1. Create `tests/test_config_migration.py` with:
   - Test that loads every historical config version and runs migration to current
   - Test that asserts all required keys from `config.schema.json` are present after migration
   - Test that asserts `_config_version` matches current schema version after migration
2. Add a `scripts/dev.py config-migration-test` command

**Tests to write:**
- `test_migration_from_v0_to_current_produces_valid_config`
- `test_migration_preserves_user_overrides`
- `test_migration_adds_new_required_keys`
- `test_migration_removes_deprecated_keys`

**Verification:** `python3 scripts/dev.py config-migration-test` passes. Migration test runs as part of `check`.

**Estimated effort:** 1 day

### 0.3 Fix naming collision (M6)

**Why now:** Trivial change, removes confusion for anyone reading the codebase.

**Changes:**
1. Rename `editor_frontend_callbacks.py` → `editor_frontend_bridge_callbacks.py` (or move into `editor_frontend/` package as `bridge_callbacks.py`)
2. Update all imports (grep for `editor_frontend_callbacks`)
3. Update architecture contracts if they reference the module name

**Tests to verify:** `python3 scripts/dev.py check` passes. No import errors.

**Estimated effort:** 0.5 day

---

## Phase 1: Module Splits

**Goal:** Decompose god modules into focused, independently testable units. No behavioral changes — pure structural refactoring.

**Problems resolved:** P5, P7, M4

### 1.1 Split `diagnostics_runtime.py` (P5)

**Why:** 21 modules import this file. Splitting it reduces the blast radius of any diagnostics change and makes each concern independently testable.

**Current responsibilities (8 concerns):**
1. Session state management
2. Breadcrumb ring
3. Exception capture
4. Frontend error ingestion
5. Operation ID generation
6. Support report assembly
7. Debug-mode configuration
8. Dirty-session marker logic

**Proposed split:**
| New module | Concerns | Lines (est.) |
|------------|----------|--------------|
| `diagnostics_session.py` | Session state, dirty-session marker | ~60 |
| `diagnostics_breadcrumbs.py` | Breadcrumb ring, recording | ~80 |
| `diagnostics_capture.py` | Exception capture, frontend error ingestion | ~70 |
| `diagnostics_operations.py` | Operation ID generation | ~30 |
| `diagnostics_report.py` | Support report assembly | ~80 |
| `diagnostics_config.py` | Debug-mode configuration | ~30 |
| `diagnostics_runtime.py` | Re-export facade (backward compat) | ~40 |

**Migration strategy:**
1. Create new modules with extracted functions
2. Keep `diagnostics_runtime.py` as a re-export facade (imports from new modules, re-exports all public symbols)
3. Gradually update importers to import from specific modules
4. Remove facade when all importers migrated

**Tests to write:**
- Unit tests for each new module in isolation
- Integration test that verifies the re-export facade exposes all original symbols
- Architecture contract updates for new modules

**Verification:** `python3 scripts/dev.py check` passes. All 21 importers work. Support report still generates correctly.

**Estimated effort:** 2-3 days

### 1.2 Split `editor_special_transforms.py` (P7)

**Why:** 8 unrelated operations in one file. Each has different preconditions, tools, and error modes.

**Current operations:**
1. Standard denoise
2. RNNoise denoise
3. DPDFNet denoise
4. Voice-only extraction
5. Pitch/hum synthesis
6. Format conversion
7. Pause removal
8. Size reduction

**Proposed split:**
| New module | Operations |
|------------|-----------|
| `editor_transforms_denoise.py` | Standard, RNNoise, DPDFNet denoise |
| `editor_transforms_extraction.py` | Voice-only extraction |
| `editor_transforms_pitch.py` | Pitch/hum synthesis |
| `editor_transforms_format.py` | Format conversion, size reduction |
| `editor_transforms_pause.py` | Pause removal |
| `editor_special_transforms.py` | Re-export facade + shared render/cleanup |

**Tests to write:**
- Unit tests for each transform module
- Integration tests for the facade
- Architecture contract for each new module

**Verification:** `python3 scripts/dev.py check` passes. All editor operations work.

**Estimated effort:** 2 days

### 1.3 Unify error systems (M4)

**Why:** Three overlapping error systems (`errors.py`, `error_codes.py`, `contracts_generated.py`) create confusion. Unifying them makes error handling consistent.

**Changes:**
1. Add `to_user_facing_error()` method to each `AudioQuickEditorError` subclass that returns a `UserFacingError` with code, message, and help URL
2. Remove duplicate `UserFacingError` from `contracts_generated.py` — use `error_codes.UserFacingError` as single source
3. Update `diagnostics_runtime.py` (or `diagnostics_capture.py` post-1.1) to automatically create breadcrumbs when exceptions are caught
4. Add `help_url` field to exception hierarchy

**Tests to write:**
- Test that every `AudioQuickEditorError` subclass produces a valid `UserFacingError`
- Test that exception → UserFacingError → JSON roundtrips correctly
- Test that diagnostics automatically records incidents for caught exceptions

**Verification:** `python3 scripts/dev.py check` passes. Error popup shows help URLs.

**Estimated effort:** 1-2 days

---

## Phase 2: State Management

**Goal:** Replace implicit, stringly-typed state with explicit, typed state machines. This is the highest-risk phase — it touches the most code and requires the most testing.

**Problems resolved:** P6, P1

### 2.1 EditorSession decomposition (P6)

**Status:** Pre-planned. See `docs/plans/P6-editor-session-state-bag-resolution.md`.

**Summary of the 6-phase plan:**
0. Characterization tests ✅ (completed 2026-06-17)
1. Extract 5 domain sub-state dataclasses
2. Consolidate 4 `_replace_*_session_state` functions
3. Consolidate 2 `stop_session_playback` functions
4. Debug-only `_assert_invariants()`
5. Update architecture contracts

**This plan defers entirely to the P6 plan.** No additional work needed here except ensuring Phase 0 and Phase 1 are complete first (diagnostics split reduces coupling to EditorSession).

**Estimated effort:** Per P6 plan

### 2.2 Frontend DOM-as-state → typed state (P1)

**Why:** 14,000 lines of TypeScript using 23+ DOM `dataset` attributes as state. This is the single highest-risk architectural debt.

**Prerequisites:** Phase 0.1 (test anti-patterns fixed)

**Strategy:** Incremental migration, one state domain at a time.

**Step 1: Define typed state stores**
Create Svelte stores for each state domain:
```
settings_ui/src/editor-inline/stores/
  playback-store.ts      # playback state (playing, paused, stopped, engine, cursor)
  selection-store.ts     # selection state (start, end, region mode)
  graph-store.ts         # graph state (active, analyzing, data points)
  busy-store.ts          # busy state (processing, recording)
  cursor-store.ts        # cursor state (position, committed)
  field-store.ts         # per-field state (index, audio detected, mounted)
```

Each store:
- Is a Svelte `writable` or derived store
- Has typed interface (no strings)
- Has `reset()` method for note change
- Emits change events for cross-module coordination

**Step 2: Migrate one module at a time**
Order (from least coupled to most coupled):
1. `graph-actions.ts` → uses `graph-store.ts`
2. `selection-gestures.ts` → uses `selection-store.ts`
3. `control-actions.ts` → uses `busy-store.ts`, `cursor-store.ts`
4. `playback-controller.ts` → uses `playback-store.ts`

For each module:
1. Add store imports
2. Replace `dataset.xxx` reads with `store.get()` or `$store`
3. Replace `dataset.xxx` writes with `store.set()` or `store.update()`
4. Keep `dataset` writes as derived projections (CSS/Anki DOM discovery) — never as source of truth
5. Write unit tests for store logic (no jsdom needed)

**Step 3: Remove dataset as source of truth**
- Audit remaining `dataset` reads — they should all be CSS selectors or Anki DOM discovery
- Remove `dataset` writes that are now redundant
- Add architecture test: `test_rule_no_dataset_as_state_source.py` that greps for `dataset` writes in non-CSS contexts

**Step 4: Update architecture contracts**
- Update Rule 33/34 (behavioral state must live in typed stores)
- Update frontend contract to require store-based state management

**Tests to write:**
- Unit tests for each store (pure logic, no DOM)
- Integration tests for store interactions (playback + cursor coordination)
- E2e tests refactored to assert on store state instead of dataset
- Architecture test enforcing no dataset-as-source-of-truth

**Verification:** `python3 scripts/dev.py check` passes. `python3 scripts/dev.py test-e2e-parallel` passes. No `dataset` writes in non-CSS contexts.

**Estimated effort:** 2-3 weeks (largest phase)

---

## Phase 3: Architecture Simplification

**Goal:** Type the dependency injection system and slim down god modules.

**Problems resolved:** P2, L5, P3

### 3.1 Type the DI system (P2)

**Why:** `cast(Any, module)` + `setattr()` is fragile and untyped. Typed DI makes the dependency graph explicit.

**Changes:**
1. Define `AudioDeps` Protocol/TypedDict with all injected attributes:
   ```python
   class AudioDeps(Protocol):
       subprocess: ModuleType
       tempfile: ModuleType
       uuid: ModuleType
       shutil: ModuleType
   ```
2. Replace `cast(Any, module)` with typed injection:
   ```python
   def inject_audio_deps(module: Any, deps: AudioDeps) -> None:
       for attr in AudioDeps.__annotations__:
           setattr(module, attr, getattr(deps, attr))
   ```
3. Add runtime guard: assert all required attributes are set before first use
4. Add architecture test: verify injected modules have all required attributes

**Tests to write:**
- Test that injection sets all required attributes
- Test that accessing unset attribute raises clear error
- Test that architecture contract enforces typed injection

**Verification:** `python3 scripts/dev.py check` passes. All audio operations work.

**Estimated effort:** 2 days

### 3.2 Split `audio_processor.py` facade (L5)

**Why:** 12 `_sync_*_dependencies()` calls mixed with operation orchestration. Tool discovery should be separate.

**Changes:**
1. Extract `audio_tool_discovery.py` with all `find_*` functions
2. Extract `audio_dependency_sync.py` with all `_sync_*_dependencies()` functions
3. Keep `audio_processor.py` as thin facade (operation orchestration only)
4. Update architecture contracts

**Tests to write:**
- Unit tests for tool discovery
- Unit tests for dependency sync
- Integration tests for facade

**Verification:** `python3 scripts/dev.py check` passes.

**Estimated effort:** 1-2 days

### 3.3 Slim `editor_integration.py` (P3)

**Why:** 40 imports and 180 re-exports is not "thin." The bottleneck exists because Anki hook registration must happen through a single entry point.

**Changes:**
1. Keep `editor_integration.py` as the hook registration entry point (required by Anki)
2. Move re-exports to explicit `__all__` list (already done? verify)
3. Create `editor_commands.py` that handles bridge command routing (extract from integration)
4. Create `editor_hooks.py` that handles Anki hook registration (extract from integration)
5. `editor_integration.py` becomes: import hooks + commands, register hooks, done

**Tests to write:**
- Architecture test: `editor_integration.py` imports < 10 modules
- Architecture test: bridge commands are routed through `editor_commands.py`

**Verification:** `python3 scripts/dev.py check` passes. Editor hooks still register.

**Estimated effort:** 1-2 days

---

## Phase 4: Developer Experience

**Goal:** Reduce the number of touch points for common changes. Make the codebase easier to navigate.

**Problems resolved:** P4, M1, M2, L4, M5

### 4.1 Unify contract systems (P4 + M1)

**Why:** Three overlapping contract systems (Python architecture, JSON Schema, behavior rules) require 5+ touch points for new features.

**Changes:**
1. Make `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md` executable:
   - Convert prose rules to architecture tests in `tests/test_architecture/`
   - Keep the markdown as documentation, but the tests are the source of truth
2. Consolidate Python architecture contracts:
   - Group by intent (editor, audio, core, ui) rather than per-module
   - Add a `contract_registry.py` that maps modules to contracts (one lookup, not 8 files)
3. Add a `scripts/dev.py contract-check` command that validates all three systems are consistent

**Tests to write:**
- Architecture test that verifies contract registry covers all modules
- Architecture test that verifies JSON Schema ↔ Python contract consistency
- Architecture test that verifies behavior rules ↔ implementation consistency

**Verification:** `python3 scripts/dev.py contract-check` passes. Adding a new command requires touching < 3 places.

**Estimated effort:** 3-4 days

### 4.2 Config key propagation automation (M2)

**Why:** 6+ touch points per config key. The `split_button_defaults` dict is a parallel source of truth.

**Changes:**
1. Generate `split_button_defaults` from `config.schema.json`:
   - Add a `scripts/dev.py generate-injection-defaults` command
   - Output: Python dict + TypeScript interface
2. Auto-generate `config_migration.py` entries from schema version diff:
   - Add a `scripts/dev.py generate-migration` command
3. Update contract generation to include config keys in TypeScript types

**Tests to write:**
- Test that generated defaults match schema
- Test that generated migration handles version bump

**Verification:** `python3 scripts/dev.py check` passes. Adding a config key requires touching 2 places (schema + UI).

**Estimated effort:** 2-3 days

### 4.3 Split generated contracts (L4)

**Why:** 1,181-line single file is hard to review and imports everything at startup.

**Changes:**
1. Update contract generation to produce multiple files:
   - `contracts_generated/enums.py` (13 enums)
   - `contracts_generated/editor.py` (editor-related dataclasses)
   - `contracts_generated/audio.py` (audio-related dataclasses)
   - `contracts_generated/settings.py` (settings-related dataclasses)
   - `contracts_generated/__init__.py` (re-export all)
2. Keep backward compatibility: `from contracts_generated import X` still works

**Tests to verify:** `python3 scripts/dev.py contracts-check` passes. All imports work.

**Estimated effort:** 1 day

### 4.4 Simplify pause parameters (M5)

**Why:** Two detectors × 4 params × 3 layers = parameter routing across 5+ modules.

**Changes:**
1. Define `PauseDetectorConfig` as a discriminated union:
   ```python
   @dataclass
   class SilencedetectConfig:
       threshold: float
       min_silence: float
   
   @dataclass
   class SileroVadConfig:
       threshold: float
       min_speech: float
       preprocess_denoise: bool
   
   PauseDetectorConfig = SilencedetectConfig | SileroVadConfig
   ```
2. Replace `split_button_defaults` pause entries with single config object
3. Update editor injection, batch metadata, and pipeline to use unified config
4. Add architecture test: pause config is a single object, not scattered params

**Tests to write:**
- Unit tests for each detector config
- Integration test: config → pipeline → detector
- Architecture test: no scattered pause params

**Verification:** `python3 scripts/dev.py check` passes. Pause-shortening works with both detectors.

**Estimated effort:** 1-2 days

---

## Phase 5: Documentation & Process

**Goal:** Make documentation structural and release process safer.

**Problems resolved:** D1, D3, L2

### 5.1 Make architecture doc structural (D1)

**Changes:**
1. Add a "Rules" section to `ARCHITECTURE.md` that lists the top 10 architecture rules with references to the enforcing test
2. Keep the descriptive sections but add cross-references to contract files
3. Add a "How to add a new module" guide with the required contract updates

**Verification:** `python3 scripts/dev.py doc-maintain` produces no drift.

**Estimated effort:** 1 day

### 5.2 Organize superpowers docs (D3)

**Changes:**
1. Add status prefix to each plan/spec filename:
   - `[completed]` — implemented and shipped
   - `[in-progress]` — actively being worked on
   - `[abandoned]` — decided against
   - `[planned]` — not started
2. Add a `docs/superpowers/INDEX.md` that lists all plans/specs with status
3. Archive completed plans older than 30 days

**Verification:** INDEX.md is accurate. No orphaned plans.

**Estimated effort:** 0.5 day

### 5.3 Simplify release pipeline (L2)

**Changes:**
1. Add `scripts/dev.py release-precheck` command that:
   - Verifies version consistency across 3 files
   - Verifies runtime packs exist
   - Verifies wheels are valid
   - Runs full QC
2. Add `scripts/dev.py release-build` command that:
   - Runs precheck
   - Builds thin archive
   - Runs smoke test
3. Reduce manual steps from 16+ to 3 (precheck, build, publish)

**Tests to write:**
- Test that precheck catches version mismatches
- Test that precheck catches missing runtime packs
- Test that build produces valid archive

**Verification:** `python3 scripts/dev.py release-precheck` passes. Release requires 3 commands.

**Estimated effort:** 2 days

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|-----------|
| 0 | Low | Test-only changes, no behavior change |
| 1 | Low | Module splits with re-export facades, no behavior change |
| 2 | **High** | Incremental migration, one state domain at a time. P6 already has characterization tests. P1 requires test anti-patterns fixed first. |
| 3 | Medium | Typed DI is additive. Facade split is structural. |
| 4 | Medium | Contract unification requires careful migration. Config automation is safe. |
| 5 | Low | Documentation and process changes. |

## Estimated Total Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| 0 | 3.5-4.5 days | None |
| 1 | 5-7 days | Phase 0 |
| 2 | 3-4 weeks | Phase 0.1, Phase 1.1 |
| 3 | 5-7 days | Phase 1 |
| 4 | 7-10 days | Phase 3 |
| 5 | 3.5 days | None (parallel with Phase 4) |

**Total: ~6-8 weeks** for a single developer. Phases 0 and 5 can run in parallel with other phases.

## Success Criteria

After all phases complete:
1. No test file asserts on private `window.__aqe*` globals
2. No module uses `cast(Any, module)` for DI
3. `editor_integration.py` imports < 10 modules
4. All contract systems are consistent and checkable via single command
5. Adding a config key requires touching < 3 places
6. Adding a new audio operation requires touching < 2 files
7. `diagnostics_runtime.py` is < 100 lines (re-export facade)
8. Frontend state is managed via typed Svelte stores, not DOM `dataset`
9. `python3 scripts/dev.py check` passes with zero warnings
10. `python3 scripts/dev.py test-e2e-parallel` passes
