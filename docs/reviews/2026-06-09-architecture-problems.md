# Architecture Problems Audit

Date: 2026-06-09

This document catalogs structural problems in the codebase. It is not a refactoring plan. It itemizes issues by severity, with concrete file references and root causes.

## Tier 1: Structural Risk

### P1. DOM-as-state in the inline editor frontend

**Files:** `settings_ui/src/editor-inline/playback-controller.ts`, `selection-gestures.ts`, `graph-actions.ts`, `control-actions.ts`

**Problem:** The inline editor frontend stores its source of truth in DOM `dataset` attributes. Playback state, selection state, graph state, busy state, and cursor state are all encoded as strings on `HTMLElement.dataset`. The `actions.ts` barrel was split into 14 focused modules, but the underlying state management was never migrated away from DOM dataset. Identified in `archive/FRONTEND_ARCHITECTURE_REFACTOR_PLAN.md` (lines 323-349) but the planned `EditorFieldState` typed state layer was never implemented.

**Consequences:**
- State transitions are stringly typed and implicitly coupled to DOM reads/writes.
- Pure state logic cannot be tested without jsdom.
- CSS can observe state through dataset, making structural DOM changes visible to style rules.
- Cross-module state coherence is unenforced (no invariant that paused playback requires a non-null cursor).

**Why it matters:** This is the highest-risk architectural debt in the codebase — 14,000 lines of frontend code containing 23+ dataset attributes that collectively represent the runtime state machine for every mounted audio field. A wrong `dataset` write in one module can leave another module's state assertion silently broken.

---

### P2. Dependency injection into audio modules is untyped and fragile

**Files:** `audio_processor.py:25-295`, `audio_processor_runtime.py`, `audio_commands.py`, `audio_rendering.py`, `audio_noise_reduction.py`, `audio_pitch_hum.py`, `audio_external.py`

**Problem:** The audio subsystem uses an explicit dependency-injection pattern where modules like `audio_rendering.py` declare `subprocess`, `tempfile`, `uuid`, and `shutil` as module-level attributes expecting injection. `audio_processor_runtime.py` uses `cast(Any, module)` + `setattr()` to inject these. This is undocumented by any contract or test — the contract system only enforces that these modules don't import stdlib themselves, not that they receive injection before use.

**Consequences:**
- If any code path accesses `audio_rendering.subprocess` before `_sync_rendering_dependencies()` runs, the result is an opaque `AttributeError` with no diagnostic about missing injection.
- `cast(Any, ...)` suppresses all type checking at injection points.
- New developers cannot discover the contract by reading the modules alone — the injection happens in `audio_processor.py` with no runtime guard or registration check.

**Root cause:** The pattern was introduced to keep audio modules import-safe (no `subprocess` at module level). It achieved that goal but at the cost of making the runtime dependency graph implicit.

---

### P3. `editor_integration.py` is a god module despite the refactor

**File:** `editor_integration.py` (240 lines)

**Problem:** `editor_integration.py` imports 40 internal modules and re-exports ~180 symbols. It is the sole public entry point for all editor hook registration and bridge command routing. It sets a module-level `_SETTINGS_OPENER` global via `register_editor_hooks()` and assigns directly to `editor_runtime.SETTINGS_OPENER`.

**Consequences:**
- Every change to editor bridge commands, callbacks, processing, or frontend UI must route through this file.
- The re-export pattern means `editor_callbacks`, `editor_processing`, `editor_frontend_callbacks`, `editor_bridge`, `editor_media`, `editor_webview_injection`, and `editor_session` are all exposed through a single module's namespace.
- The docstring claims "Thin Anki editor integration" but 40 imports and 180 re-exports is not thin.

**Why it survived the refactor:** The frontend refactor split the TypeScript side. The Python editor subsystem was reorganized into `editor_frontend/` (6 files), but `editor_integration.py` remains the bottleneck because Anki hook registration must happen through a single entry point.

---

### P4. Three overlapping contract systems

**Systems:**
1. Python architecture contracts (`tests/test_architecture/contract_*.py`, 1,300 lines)
2. JSON Schema communication contracts (`contracts/communication.schema.json`, 556 lines)
3. Editor modification button behavior rules (`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`, 265 lines of prose)

**Problem:** These three systems enforce rules across overlapping domains (bridge commands, operation semantics, allowed imports, side effects, button behavior) but are maintained independently. A new editor command requires updates to the Python contract, the TypeScript bridge command list, the JSON schema (if it carries structured payloads), the behavior rules document, AND the architecture test that checks bridge command sync (Rule 3).

**Consequences:**
- Adding a feature that crosses Python/TypeScript boundary requires touching 5+ places before any tests pass.
- The markdown document is prose, not executable. It can and will drift from actual behavior.
- Contract test failures are cryptic — "module X classified in layer Y cannot import module Z" — because the contracts are atomized per-module rather than per-intent.

---

### P5. `diagnostics_runtime.py` is a god module

**File:** `diagnostics_runtime.py` (364 lines)

**Problem:** This module is imported by 21 other modules (the most widely used internal dependency). It single-handedly owns: session state management, breadcrumb ring, exception capture, frontend error ingestion, operation ID generation, support report assembly, debug-mode configuration, and dirty-session marker logic.

**Consequences:**
- Breadcrumb recording, exception capture, and session state are distinct concerns sharing one namespace.
- Any change to the diagnostics data model forces a review of 21 importing modules.
- The support report builder is coupled to the in-memory breadcrumb ring implementation rather than a stable query interface.

---

### P6. `editor_session.py` is a mutable state bag

**File:** `editor_session.py` (340 lines)

**Problem:** The `EditorSession` dataclass has 35 attributes spanning undo history, redo history, processing guard, playback state, learner recording state, region delete requests, and pending editor status. It is mutated by functions in `editor_runtime.py`, `editor_webview_injection.py`, `editor_callbacks.py`, `editor_processing.py`, and `editor_persistent_undo.py`.

**Consequences:**
- No invariant enforcement across the 35 fields (e.g., nothing guarantees `processing.active` implies `playback_active is False`).
- Any function with a reference to the session can mutate any field.
- `UndoHistory` is a mutable dataclass with `push`, `pop`, and `clear` methods — it carries mutable list state inside an otherwise dataclass-shaped object.

---

### P7. `editor_special_transforms.py` violates single responsibility

**File:** `editor_special_transforms.py` (364 lines)

**Problem:** This module handles 8 distinct audio operations: standard denoise, RNNoise denoise, DPDFNet denoise, voice-only extraction, pitch/hum synthesis, format conversion, pause removal, and size reduction. Each operation has different preconditions, tool dependencies, error modes, and output handling.

**Consequences:**
- Adding a new denoise algorithm (or a new special transform) forces developers to navigate 8 unrelated operation implementations to find the right insertion point.
- Error handling for each operation is mixed in the same try/except blocks.
- Operation-specific parameter validation is interleaved with generic render/cleanup logic.

---

## Tier 2: Maintainability Friction

### M1. Contract maintenance overhead

**Files:** `tests/test_architecture/contract_audio.py`, `contract_core.py`, `contract_ui.py`, `contract_editor/core.py`, `contract_editor/integration.py`, `contract_editor/operations.py`, `contract_editor/processing.py`, `contract_editor/frontend.py`

**Problem:** Every production module has an explicit declarative contract listing allowed dependencies, allowed side effects, and forbidden import prefixes. The contract system (~1,300 lines) is the source of truth; the architecture document says "Keep [contracts.py] authoritative and keep [ARCHITECTURE.md] descriptive."

**Consequences:**
- Adding a new import to any module can fail the architecture test suite if the contract wasn't updated.
- New developers hit contract violation test failures and must navigate 8 contract files to find the right entry.
- The contract system cannot be audited automatically for correctness — a module could import a disallowed dependency and the contract would still pass if no test observes it.

**Mitigation in place:** `test_rule5_all_modules_classified.py` and `test_rule15_all_modules_have_contracts.py` ensure coverage completeness. But the per-module atomicity makes changes high-friction.

---

### M2. Config key propagation requires 6+ touch points

**Problem:** Adding or renaming a config key requires updates to:
1. `config.schema.json` (schema validation)
2. `config.json` (default value)
3. `contracts/communication.schema.json` (contract generation merge target)
4. `config_migration.py` (deep-merge migration logic)
5. `editor_webview_injection.py` (split_button_defaults dict with ~30 entries)
6. `settings_ui/src/` (Svelte settings UI)
7. `e2e/` default config helpers
8. TypeScript types via contract generation (automatic if steps 1-3 are correct)

**Root cause:** The `split_button_defaults` dict in `editor_webview_injection.py:88-126` is a manual enumeration of ~30 config keys. It does not derive from the schema or generated contracts — it's a parallel source of truth.

---

### M3. Frontend-to-Python size asymmetry

**Lines of code:**
- Python addon runtime: ~24,400 lines (126 files)
- TypeScript/Svelte frontend: ~21,200 lines (165 files)
- Editor-inline alone: ~14,000 lines (108 files)

**Problem:** The frontend is nearly as large as the Python runtime. The editor-inline subdirectory is 2x the size of the entire Python audio subsystem. This asymmetry means frontend refactoring costs dominate feature work.

**Why it matters:** The frontend was already partially refactored (`actions.ts` → 14 modules), but the state management problem (P1) remains. Continuing to add features to this architecture without addressing P1 will compound the cost of any future refactor.

---

### M4. The dual error system

**Files:** `errors.py` (53 lines), `error_codes.py` (69 lines), `contracts_generated.py` (UserFacingError dataclass)

**Problem:**
- `errors.py` defines an exception hierarchy (`AudioQuickEditorError` → 12 subclasses) for Python raise/catch.
- `error_codes.py` defines a `UserFacingError` dataclass with stable string codes (`AQE-MEDIA-001`, etc.) and help URLs for user-visible diagnostics.
- `contracts_generated.py` has its own `UserFacingError` dataclass for JSON serialization.
- `diagnostics_runtime.py` adds a third layer: breadcrumbs, operation IDs, incident recording, and support report context.

These systems overlap but are not unified. A `MissingFfmpegError` exception does not automatically produce a `UserFacingError` with a help URL or a diagnostics incident.

---

### M5. Pause-shortening parameter complexity

**Files:** `audio_pause_settings.py`, `audio_pipeline.py`, `audio_operation_params.py`, `audio_processor.py`, `editor_webview_injection.py`

**Problem:** The pause-shortening operation has two detectors (Silencedetect, Silero VAD), each with 4 algorithm-specific parameters (threshold, min_silence, min_speech, preprocess_denoise), plus a shared aggressiveness preset layer, plus operation-local overrides that avoid mutating persisted config, plus detector-specific command construction, plus interval post-processing (merging, filtering, inversion).

**Consequences:**
- Parameter routing crosses 5+ modules for a single user operation.
- The aggressiveness preset → advanced params mapping is a lookup table that must stay consistent between editor settings UI, editor injection, batch metadata, and Python pipeline construction.
- Adding a third detector would require parallel 4-param entries across the entire chain.

---

### M6. editor_frontend/ module naming collision

**Files:** `editor_frontend/` (6 files), `editor_frontend_callbacks.py` (separate file)

**Problem:** The `editor_frontend/` package and `editor_frontend_callbacks.py` are sibling modules with related but distinct responsibilities. `editor_frontend_callbacks.py` imports from `editor_frontend` (the package). The naming implies `editor_frontend_callbacks` is related to `editor_frontend` but it's not inside the package.

---

## Tier 3: Latent Risks

### L1. Runtime manifest adds failure surface to first install

**Files:** `runtime_manager.py`, `runtime_manifest.py`, `runtime_installer_dialog.py`, `runtime_release.lock.json`

**Problem:** The add-on ships "thin" — it downloads ~15-30 MB of native runtime tools on first install. This requires a working network connection, GitHub API/release asset availability, SHA-256 verification, zip extraction, executable permission setting, and platform-specific binary selection.

**Consequences:**
- First-run failure modes include: offline installer, GitHub rate limiting, corrupted downloads, permission errors, and platform detection failures.
- The runtime installer dialog is a Qt UI with progress feedback that must handle cancellation, retry, and partial state recovery.
- The entire runtime management subsystem (~1,500 lines) exists solely because the add-on is thin rather than bundled.

**Mitigation:** The managed runtime approach is intentional (thin releases, platform matrix coverage, versioned runtime packs). The complexity is not accidental, but it is structural debt.

---

### L2. Release pipeline complexity

**Files:** `scripts/release.py`, `scripts/release_runtime_cli.py`, `scripts/dev.py`

**Problem:** A public release requires 16+ manual steps: bump versions in 3 files, verify runtime packs, verify wheels, build runtime packs, upload to GitHub, verify uploads, build thin archive, smoke test, native acceptance on each platform. The release documentation in `DEVELOPMENT.md` warns "runtime-vN tags [are] immutable" — there is no undo.

**Consequences:**
- Missing one step produces a broken published artifact with no automated recovery.
- Only the primary maintainer can reasonably execute a release.
- The `--skip-quality-checks` flag exists but can produce an archive missing generated contracts or webview bundles.

---

### L3. Frontend test anti-patterns persist after audit

**Files:** Listed in `docs/reviews/2026-06-07-test-anti-pattern-audit.md`

**Problem:** The audit (2026-06-07) found tests that assert private `window.__aqePending*` globals, exact SVG path content, mock-call-only warning checks, and e2e tests that mutate private `window.__aqe*` state to stage scenarios. The audit was documented but the tests were not fixed.

**Consequences:**
- Refactoring the frontend state layer (P1) will break these tests because they assert on the exact internal state storage mechanism.
- E2e tests that mutate private globals can pass even when the real user workflow is broken.

---

### L4. The generated contracts file is a single 1,181-line Python file

**File:** `contracts_generated.py` (1,181+ lines)

**Problem:** Every schema change regenerates this file in its entirety. It contains 13 enums and dozens of dataclass definitions. It is the single largest Python file in the addon, all auto-generated from a 556-line JSON schema.

**Consequences:**
- Code review of schema changes must include reviewing the generated output for correctness.
- Git diffs on this file are large and unreadable.
- Import-time cost of loading all contract types is paid even when only a subset is needed.

---

### L5. `audio_processor.py` is a facade with 12 sync functions

**File:** `audio_processor.py` (295 lines)

**Problem:** `audio_processor.py` acts as the public API for all audio operations but internally contains 12 `_sync_*_dependencies()` calls spread across find-tool and render functions. Mixing tool discovery, dependency injection, and operation orchestration in one module violates single responsibility.

**Consequences:**
- New audio modules following the DI pattern must add their sync function to this file.
- The find-tool functions (`find_ffmpeg`, `find_deep_filter`, etc.) are coupled to the runtime manager and configured paths but live in the audio processor facade rather than a dedicated tool-discovery module.

---

## Tier 4: Documentation and Process

### D1. ARCHITECTURE.md is descriptive but not structural

**File:** `ARCHITECTURE.md` (169 lines)

**Problem:** The architecture document says "Keep [contracts.py] authoritative and keep this document descriptive." This means the document describes what the contracts enforce but does not itself define any rules. A reader trying to understand the architecture must cross-reference the document, the contract files, and the inspection engine.

---

### D2. No automated migration validation

**Problem:** `config_migration.py` performs deep-merge migration of config when `_config_version` changes. There is no automated test that ensures migration code matches the schema version stamp or that all required keys are handled. A schema change without corresponding migration code will produce config with missing keys at runtime.

---

### D3. docs/superpowers/ directory structure obscures current state

**Files:** `docs/superpowers/plans/` (30 files), `docs/superpowers/specs/` (30 files)

**Problem:** Plans and specs are dated files (e.g., `2026-05-18-editor-split-buttons-implementation.md`). There is no indicator of which plans are completed, which are in progress, and which were abandoned. The files serve as historical record but do not help a newcomer understand what the codebase currently does.

---

## Summary Table

| ID | Issue | Severity | Affected Lines | Root Cause |
|----|-------|----------|---------------|------------|
| P1 | DOM-as-frontend-state | Critical | ~14,000 TS | Refactor halted before state layer |
| P2 | Untyped DI into audio modules | High | ~1,000 Python + ~2,000 audio | Ad-hoc DI without runtime guards |
| P3 | God editor_integration.py | High | 240 + 40 deps | Single hook registration entry point |
| P4 | Three overlapping contract systems | High | ~2,100 total | Organic growth without unification |
| P5 | God diagnostics_runtime.py | High | 364 + 21 importers | Single module for all diagnostics |
| P6 | Mutable session state bag | Medium | 340 + 5 writers | No state invariants |
| P7 | Special transforms god module | Medium | 364 | 8 operations in one file |
| M1 | Contract maintenance overhead | Medium | ~1,300 contracts | Atomic per-module contracts |
| M2 | 6+ touch points per config key | Medium | ~500 total | Manual split_button_defaults dict |
| M3 | Frontend-to-Python size asymmetry | Medium | 21K / 24K lines | Feature-rich inline editor |
| M4 | Dual error system | Medium | ~150 lines | Separate exception vs. user-facing paths |
| M5 | Pause parameter complexity | Low | ~800 lines | Two detectors × 4 params × 3 layers |
| M6 | editor_frontend naming collision | Low | 2 files | Package + sibling module ambiguity |
| L1 | Runtime install failure surface | Low | ~1,500 runtime mgmt | Thin release architecture |
| L2 | Complex release pipeline | Low | 3 scripts | Multi-target native runtime packs |
| L3 | Unfixed test anti-patterns | Low | ~10 test files | Audit without remediation |
| L4 | Monolithic generated contracts | Low | 1,181 lines | Single-file quicktype output |
| L5 | Facade with mixed concerns | Low | 295 lines | DI + discovery + orchestration |
| D1 | Descriptive-only architecture doc | Info | 169 lines | Intentional design choice |
| D2 | No migration validation | Info | N/A | Missing automation |
| D3 | Opaque superpowers docs | Info | 60 files | No completion tracking |
