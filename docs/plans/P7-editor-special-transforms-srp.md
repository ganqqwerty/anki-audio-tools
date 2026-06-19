# P7: Refactor `editor_special_transforms.py` — Single Responsibility

**Status**: Implemented core SRP split; deeper per-transform-family split superseded
**Date**: 2026-06-17
**Implemented**: 2026-06-18
**Problem source**: `docs/reviews/2026-06-09-architecture-problems.md` P7

---

## Implementation Note

The core split is implemented in the runtime package:

- `editor_special_transforms.py` now owns transform entry-point dispatch only.
- `editor_transform_orchestration.py` owns shared async transform orchestration.
- `editor_transform_post_processing.py` owns post-edit media replacement.
- `editor_transform_failure_support.py` owns transform diagnostics.
- `editor_special_transform_worker.py` remains the worker boundary.

`replace_current_field_after_special_transform` is the production callback name. `replace_current_field_after_noise_removal` remains as a compatibility alias for existing imports and dependency consumers.

## 1. Problem Analysis

### 1.1 What the file does today

`editor_special_transforms.py` (358 lines) contains **four distinct responsibilities** tangled into one module:

| Responsibility | Functions | Lines (approx) |
|---|---|---|
| **A. Transform entry points** | `denoise_standard_async`, `reduce_size_async`, `rnnoise_async`, `dpdfnet_async`, `voice_only_async`, `pitch_hum_async`, `_pitch_hum_renderer` | 53–167 (115 lines) |
| **B. Core orchestration** | `run_special_audio_transform_async`, `_special_transform_config` | 170–246 (77 lines) |
| **C. Post-edit media replacement** | `replace_current_field_after_noise_removal`, `_replace_noise_reduction_session_state` | 249–307 (59 lines) |
| **D. Failure diagnostics** | `record_rnnoise_failure_context`, `record_dpdfnet_failure_context`, `record_spleeter_failure_context`, `log_special_transform_failure` | 310–358 (49 lines) |

These four concerns have **different reasons to change**:

- **A** changes when a new transform is added or an existing one's parameters change.
- **B** changes when session lifecycle, threading model, or guard semantics evolve.
- **C** changes when the media replacement / editor reload workflow evolves (shared with `editor_processing.py` and `editor_region_delete.py`).
- **D** changes when support diagnostics, failure logging format, or incident recording changes.

### 1.2 Concrete harms

1. **Misleading name**: `replace_current_field_after_noise_removal` is not specific to noise removal — it's the generic post-edit replacement path for all special transforms. The name was inherited from an earlier design where the file only handled denoise.

2. **Coupling through re-exports**: `editor_processing.py` re-exports 12 symbols from this module (lines 55–66). That file is 360 lines itself and also has SRP issues. The re-export pattern hides the real dependency graph — callers think they depend on `editor_processing` but actually depend on `editor_special_transforms`.

3. **Test coupling**: Two test files (`test_editor_noise_reduction_callbacks.py`, `test_editor_async_race_guards.py`) import directly from `editor_special_transforms`. Architecture tests (`test_rule32_editor_solid_guardrails.py`, `test_rule27_editor_reload_status_lifecycle.py`) reference the module by name in allowlists. Any rename or split requires touching these.

4. **Adding a transform is error-prone**: To add a new special transform, a developer must:
   - Add an entry point function in the top section
   - Understand that `run_special_audio_transform_async` in the middle is the shared orchestrator
   - Know that `replace_current_field_after_noise_removal` at the bottom is the callback (despite its name)
   - Add a failure context recorder at the bottom if the new transform has specific diagnostics
   - Update `editor_processing.py` re-exports
   - Update `editor_deps_protocols.py` if the new transform needs a new deps method

   The file gives no structural signal about which section to modify.

5. **Orchestration is hard to test in isolation**: `run_special_audio_transform_async` is the most complex function (60 lines of session guard setup, breadcrumb logging, threading). It's currently only testable through the entry-point wrappers, not directly.

### 1.3 What is NOT a problem

- The entry points (A) are fine as thin wrappers — that's their job.
- The worker (`editor_special_transform_worker.py`, 170 lines) is already correctly separated.
- The dependency injection pattern through `ProcessingDeps` is sound; the issue is module organization, not the DI approach.

---

## 2. Refactoring Strategy

### 2.1 Guiding principles

- **Each new module gets one reason to change.**
- **Preserve all public names via re-exports** during transition (zero-flag-day approach). `editor_processing.py` continues to re-export; callers don't break.
- **Move, don't rewrite.** The logic is correct; we're reorganizing, not changing behavior.
- **Run `python3 scripts/dev.py check` after each phase.** Each phase is independently shippable.

### 2.2 Target structure after refactoring

```
editor_special_transforms.py          # Entry points only (A) — slim dispatch module (~120 lines)
editor_transform_orchestration.py     # Core orchestration (B) — session setup, threading, guards (~80 lines)
editor_transform_post_processing.py   # Post-edit replacement (C) — media persist, field replace, session state (~65 lines)
editor_transform_failure_support.py   # Failure diagnostics (D) — context recorders, failure logging (~55 lines)
editor_special_transform_worker.py    # Already exists, unchanged (~170 lines)
editor_processing.py                  # Re-exports updated to point at new modules
```

---

## 3. Phased Execution

### Phase 1: Extract failure diagnostics (low risk, self-contained)

**New file**: `addon/anki_audio_quick_editor/editor_transform_failure_support.py`

**Move these functions**:
- `record_rnnoise_failure_context` (lines 310–318)
- `record_dpdfnet_failure_context` (lines 321–329)
- `record_spleeter_failure_context` (lines 332–340)
- `log_special_transform_failure` (lines 343–358)

**Imports the new module needs**:
```python
from .permission_guidance import message_with_permission_guidance
from .support import (
    format_denoise_support_log_block,
    format_spleeter_support_log_block,
    latest_denoise_support_incident,
    latest_spleeter_support_incident,
    record_latest_denoise_support_incident,
    record_latest_spleeter_support_incident,
)
```

**Update `editor_special_transforms.py`**:
- Remove the moved functions.
- Remove the now-unused imports from `.support` and `.permission_guidance`.
- Add re-exports at the bottom for backward compatibility:
  ```python
  from .editor_transform_failure_support import (
      record_rnnoise_failure_context,
      record_dpdfnet_failure_context,
      record_spleeter_failure_context,
      log_special_transform_failure,
  )
  ```

**Update `editor_processing.py`**: No change needed — it already re-exports from `editor_special_transforms`, and the re-exports above keep the chain intact.

**Update architecture contract** (`tests/test_architecture/contract_editor/processing.py`):
- Add `editor_transform_failure_support` to the contract map with the same layer and appropriate allowed deps.

**Update architecture tests**:
- `test_rule32_editor_solid_guardrails.py`: Add `editor_transform_failure_support.py` to `EDITOR_RENDER_REPLACEMENT_WORKFLOWS` if it touches media replacement (it doesn't — skip).
- `test_rule29_editor_dependency_protocols.py`: Add to the allowlist if needed.

**Verify**: `python3 scripts/dev.py check`

---

### Phase 2: Extract post-edit media replacement (medium risk, cross-cutting)

**New file**: `addon/anki_audio_quick_editor/editor_transform_post_processing.py`

**Move these functions**:
- `replace_current_field_after_noise_removal` (lines 249–286)
- `_replace_noise_reduction_session_state` (lines 289–307)

**Rename during move**: `replace_current_field_after_noise_removal` → `replace_current_field_after_special_transform`. The old name is misleading — this function handles ALL special transforms, not just noise removal. Keep a re-export alias in `editor_special_transforms.py` for backward compatibility.

**Imports the new module needs**:
```python
from .audio_state import AudioEditState, AudioProcessingConfig
from .editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from .editor_processing_shared import (
    cancel_graph_analysis_for_processing,
    request_history_availability_after_edit,
    resolved_field_index,
    sync_history_availability,
)
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    clear_processing_for_stale_guard,
    processing_guard_matches_editor,
)
from .media_paths import existing_media_file_path
```

**Update `editor_special_transforms.py`**:
- Remove the moved functions and their now-unused imports.
- Add re-exports:
  ```python
  from .editor_transform_post_processing import (
      replace_current_field_after_noise_removal,
      replace_current_field_after_special_transform,
  )
  ```

**Update `editor_special_transform_worker.py`**:
- Change `_schedule_special_transform_finish` to import from the new module:
  ```python
  from .editor_transform_post_processing import replace_current_field_after_special_transform
  ```
  But since it calls through `deps.replace_current_field_after_noise_removal`, no change is needed in the worker itself. The deps protocol binding handles the routing.

**Update `editor_deps_protocols.py`**:
- The protocol field `replace_current_field_after_noise_removal` keeps its name for now (protocol rename is a separate concern). The implementation just moves.

**Update `editor_processing.py`**:
- The re-export `replace_current_field_after_noise_removal = _special_transforms.replace_current_field_after_noise_removal` continues to work via the re-export chain.

**Update architecture contract**: Add `editor_transform_post_processing` with appropriate deps.

**Update tests**:
- `test_editor_noise_reduction_callbacks.py`: Update import to use the new module directly (preferred) or leave as-is since the re-export chain works.

**Verify**: `python3 scripts/dev.py check`

---

### Phase 3: Extract core orchestration (medium risk, most complex)

**New file**: `addon/anki_audio_quick_editor/editor_transform_orchestration.py`

**Move these functions**:
- `run_special_audio_transform_async` (lines 170–231)
- `_special_transform_config` (lines 234–246)

**Imports the new module needs**:
```python
from .audio_formats import DEFAULT_OUTPUT_FORMAT
from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import new_operation_id, record_breadcrumb
from .editor_actions import EditorCommandPayload, processing_config_for_command
from .editor_processing_shared import cancel_graph_analysis_for_processing
from .editor_session import begin_processing_guard
from .editor_special_transform_worker import run_special_transform_worker
from .editor_status import command_status_summary
from .i18n import t
from .prosody_settings import config_with_graph_settings
```

**Update `editor_special_transforms.py`**:
- Remove the moved functions.
- Import from the new module:
  ```python
  from .editor_transform_orchestration import run_special_audio_transform_async
  ```
- All entry points now delegate to this imported function.

**Update `editor_processing.py`**:
- The re-export `run_special_audio_transform_async = _special_transforms.run_special_audio_transform_async` continues to work.

**Update tests**:
- `test_editor_async_race_guards.py`: Imports `run_special_audio_transform_async` from `editor_special_transforms`. Update to import from `editor_transform_orchestration` directly, or leave as-is via re-export.

**Verify**: `python3 scripts/dev.py check`

---

### Phase 4: Clean up `editor_processing.py` re-exports (low risk, housekeeping)

After phases 1–3, `editor_processing.py` still re-exports everything through `editor_special_transforms.py`, which in turn re-exports from the new modules. This double-hop is functional but confusing.

**Update `editor_processing.py`** to import directly from the new modules where it makes sense:

```python
from .editor_transform_failure_support import (
    log_special_transform_failure,
    record_dpdfnet_failure_context,
    record_rnnoise_failure_context,
    record_spleeter_failure_context,
)
from .editor_transform_orchestration import run_special_audio_transform_async
from .editor_transform_post_processing import replace_current_field_after_noise_removal
```

Keep the entry-point re-exports (denoise_standard_async, etc.) going through `editor_special_transforms` since that's their home module.

**Remove stale re-exports** from `editor_special_transforms.py` that are no longer needed (the functions now live in their own modules and are imported directly by consumers).

**Verify**: `python3 scripts/dev.py check`

---

## 4. Dependency Graph: Before vs After

### Before
```
editor_callbacks.py
  └─ editor_processing.py (re-exports 12 symbols)
       └─ editor_special_transforms.py (all 4 concerns, 358 lines)
            └─ editor_special_transform_worker.py (background thread)
```

### After
```
editor_callbacks.py
  └─ editor_processing.py (re-exports from multiple focused modules)
       ├─ editor_special_transforms.py (entry points only, ~120 lines)
       ├─ editor_transform_orchestration.py (session + threading, ~80 lines)
       ├─ editor_transform_post_processing.py (media replacement, ~65 lines)
       └─ editor_transform_failure_support.py (diagnostics, ~55 lines)
            └─ editor_special_transform_worker.py (background thread, unchanged)
```

---

## 5. Risk Assessment

| Phase | Risk | Mitigation |
|---|---|---|
| 1 (failure diagnostics) | Low — pure extraction, no behavior change | Re-exports preserve all call sites |
| 2 (post-processing) | Medium — rename `replace_current_field_after_noise_removal` is a behavior-adjacent change | Keep old name as re-export alias; update deps protocol name separately |
| 3 (orchestration) | Medium — `run_special_audio_transform_async` is the most complex function | Move verbatim, no logic changes; existing tests cover the path |
| 4 (re-export cleanup) | Low — import path changes only | Architecture tests catch any broken boundary |

---

## 6. Test Impact

| Test file | Phase affected | Change needed |
|---|---|---|
| `test_editor_noise_reduction_callbacks.py` | Phase 2 | Update import path (or leave via re-export) |
| `test_editor_async_race_guards.py` | Phase 3 | Update import path (or leave via re-export) |
| `test_rule32_editor_solid_guardrails.py` | Phase 2 | Add new module to workflow list |
| `test_rule29_editor_dependency_protocols.py` | Phase 1 | Add new module to allowlist |
| `test_rule27_editor_reload_status_lifecycle.py` | Phase 2 | Add new module to allowlist |
| `contract_editor/processing.py` | Phases 1–3 | Add contract entries for new modules |

---

## 7. Success Criteria

- [x] `editor_special_transforms.py` contains only entry-point dispatch functions.
- [x] Shared orchestration, post-processing, and diagnostics each live in focused modules.
- [x] Existing import compatibility is preserved for the old post-processing name.
- [x] `replace_current_field_after_noise_removal` is renamed to `replace_current_field_after_special_transform` with a backward-compatible alias.
- [ ] Full verification remains tied to the branch-level QC gate recorded with the implementing commit.
- [ ] A deeper transform-family split, if still desired, should be planned as separate follow-up work.
