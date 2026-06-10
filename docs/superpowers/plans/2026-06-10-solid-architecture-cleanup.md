# SOLID Architecture Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the SOLID architecture review into small, verifiable refactors that reduce hidden dependency wiring, untyped dependency bags, frontend ambient globals, cloned diagnostics probes, and batch facade indirection.

**Architecture:** Keep public compatibility facades stable while moving hidden dependencies behind explicit builders, typed protocols, and narrow runtime adapters. Each task must preserve behavior first, add a regression or architecture test, and only then simplify the implementation. Avoid broad file splitting unless a task directly needs the split.

**Tech Stack:** Python 3.13 Anki add-on runtime, pytest, import-linter-backed architecture tests, Svelte 5, TypeScript, Vitest, existing `scripts/dev.py` quality gates.

---

## Source Review

Primary review document: `docs/reviews/2026-06-10-architecture-problems-ds.md`

The codes below are intentionally stable. Use them in branch names, commits, review comments, and follow-up issues.

## Code Registry

| Problem | Priority | Solution | Changes | Additional tests |
|---|---:|---|---|---|
| `P-AUD-001` duplicated `AudioModuleDeps(...)` construction in `audio_processor.py` | Immediate | `S-AUD-001` centralize audio dependency construction | `C-AUD-001`, `C-AUD-002` | `T-AUD-001`, `T-AUD-002` |
| `P-EDT-001` untyped editor workflow dependency bags | Immediate | `S-EDT-001` introduce typed workflow protocols one workflow at a time | `C-EDT-001`, `C-EDT-002` | `T-EDT-001`, `T-EDT-002` |
| `P-FE-001` editor config globals leak into pure frontend logic | Immediate | `S-FE-001` add runtime config adapters and parameterized factories | `C-FE-001`, `C-FE-002`, `C-FE-003` | `T-FE-001`, `T-FE-002`, `T-FE-003` |
| `P-DIA-001` cloned diagnostics health probe logic | Immediate | `S-DIA-001` extract shared probe runners and result formatting | `C-DIA-001`, `C-DIA-002` | `T-DIA-001`, `T-DIA-002` |
| `P-BAT-001` batch processors hide dependencies behind lazy facade lookup | Short-term | `S-BAT-001` pass explicit batch render/analyze dependencies | `C-BAT-001`, `C-BAT-002` | `T-BAT-001`, `T-BAT-002` |
| `P-REP-001` editor media replacement workflows duplicate stable steps | Short-term | `S-REP-001` extract stable replacement primitives only | `C-REP-001`, `C-REP-002` | `T-REP-001`, `T-REP-002` |
| `P-BRG-001` shared `lib/bridge.ts` contains settings-specific commands | Short-term | `S-BRG-001` split transport from settings bridge commands | `C-BRG-001`, `C-BRG-002` | `T-BRG-001`, `T-BRG-002` |
| `P-SPL-001` `SplitButton.svelte` and `SplitButtonMenu.svelte` have a large value/action prop surface | Deferred unless split-button work is active | `S-SPL-001` pass grouped value/action objects | `C-SPL-001` | `T-SPL-001` |

## Execution Rules

- Implement tasks in order unless a maintainer explicitly selects a short-term task first.
- Keep one task per commit.
- Preserve public function names unless a task explicitly says to remove them.
- Run the focused verification listed in each task before committing.
- Before claiming the plan is fully implemented, run `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e`.
- If full check or e2e is not run before a commit, mention that in the commit body.

## File Structure

### Python Audio Facade

- Modify `addon/anki_audio_quick_editor/audio_processor.py`
  Add one `_audio_module_deps()` helper and use it from each `_sync_*_dependencies()` function.

- Add `tests/test_architecture/test_rule28_audio_processor_facade_wiring.py`
  Enforce one `AudioModuleDeps(...)` construction and keep the facade wiring shape explicit.

### Python Editor Dependencies

- Add `addon/anki_audio_quick_editor/editor_deps_protocols.py`
  Define narrow `Protocol` types for workflow dependency bags, starting with `RegionDeleteDeps`.

- Modify `addon/anki_audio_quick_editor/editor_dependencies.py`
  Return `RegionDeleteDeps` from `region_delete_deps(...)`.

- Modify `addon/anki_audio_quick_editor/editor_region_delete.py`
  Replace `deps: Any` with `RegionDeleteDeps` for region-delete entry points and helpers.

- Modify `addon/anki_audio_quick_editor/editor_region_delete_worker.py`
  Replace `deps: Any` with `RegionDeleteDeps` for worker functions.

- Add `tests/test_architecture/test_rule29_editor_dependency_protocols.py`
  Enforce that migrated region-delete modules no longer accept `deps: Any`.

### Frontend Runtime Config Boundary

- Add `settings_ui/src/editor-inline/editor-runtime-config.ts`
  Provide the only editor-inline runtime config reader plus pure config accessors.

- Add `settings_ui/tests/editor-runtime-config.test.ts`
  Cover config fallback and accessors.

- Modify `settings_ui/src/lib/editor-toolbar-buttons.ts`
  Make `commandButtons(...)`, `toolbarButtons(...)`, and `denoiseButtons(...)` accept explicit config-like values.

- Modify `settings_ui/src/editor-inline/commands.ts`
  Make `processingMessage(...)` accept explicit config-like values.

- Modify `settings_ui/src/editor-inline/EditorControls.svelte`
  Read config through `editorRuntimeConfig()` once and pass values into child components/factories.

- Modify `settings_ui/src/editor-inline/SelectionToolbar.svelte`
  Receive visible commands and button modes as props instead of reading global config.

- Modify `settings_ui/src/editor-inline/GraphVisualizer.svelte`
  Receive `selectionMarkerShiftButtonsEnabled` as a prop.

- Modify `settings_ui/src/editor-inline/SplitExtraFields.svelte`
  Receive source filename as an explicit prop from the parent component.

- Add `settings_ui/tests/editor-runtime-config-boundary.test.ts`
  Scan selected frontend files for disallowed `window.__AQE_EDITOR_CONFIG__` reads.

### Diagnostics Health Probes

- Modify `addon/anki_audio_quick_editor/diagnostics.py`
  Extract shared subprocess probe and health dict helpers while keeping current public `build_*_health` functions.

- Modify `tests/test_diagnostics.py`
  Add direct helper coverage for timeout and non-zero probe result shaping.

- Modify `tests/test_diagnostics_bundled_tools.py`
  Keep bundled-tool behavior coverage passing through the refactor.

### Batch Operation Dependencies

- Modify `addon/anki_audio_quick_editor/batch_operation_processing.py`
  Add explicit dependency dataclasses/protocols and remove `_facade_attr(...)`.

- Modify `addon/anki_audio_quick_editor/batch_operations.py`
  Build production batch dependencies and pass them into graph/transform processors.

- Modify `addon/anki_audio_quick_editor/batch_operations_helpers.py`
  Pass renderers explicitly to `render_batch_denoise(...)` and remove lazy facade lookup.

- Modify `tests/test_batch_conversion.py`, `tests/test_batch_denoise.py`, `tests/test_batch_visualization.py`
  Preserve behavior while asserting fake dependencies can be passed directly.

- Add `tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py`
  Enforce no `import_module(".batch_operations"` in batch processor/helper modules.

### Editor Media Replacement Primitives

- Add `addon/anki_audio_quick_editor/editor_media_replacement.py`
  Hold stable primitives for generated-media persistence, sound-reference replacement, and UI finish calls.

- Modify `addon/anki_audio_quick_editor/editor_processing.py`
  Use primitives from `editor_media_replacement.py` where behavior is identical.

- Modify `addon/anki_audio_quick_editor/editor_special_transforms.py`
  Use primitives from `editor_media_replacement.py` for special-transform field replacement.

- Modify `addon/anki_audio_quick_editor/editor_region_delete.py`
  Use primitives only for identical persistence/reference replacement steps.

- Add `tests/test_editor_media_replacement.py`
  Unit-test the new primitives.

### Frontend Bridge Split

- Add `settings_ui/src/lib/bridge-transport.ts`
  Move generic bridge envelope encoding and transport into this file.

- Add `settings_ui/src/settings/bridge.ts`
  Move settings commands and settings callback registration here.

- Modify `settings_ui/src/lib/bridge.ts`
  Keep only a one-release compatibility re-export for generic transport APIs.

- Move `settings_ui/src/lib/async-jobs.ts` to `settings_ui/src/settings/async-jobs.ts`
  Import settings async command transport from `./bridge.js`.

- Modify `settings_ui/src/settings/SettingsApp.svelte`
  Import settings commands from `./bridge.js`.

- Split or update `settings_ui/tests/bridge.test.ts`
  Keep transport tests under `bridge.test.ts`; add settings command tests in `settings-bridge.test.ts`.

## Tasks

### Task AUD-001: Centralize Audio Facade Dependency Construction

**Problem:** `P-AUD-001`  
**Solution:** `S-AUD-001`  
**Changes:** `C-AUD-001`, `C-AUD-002`  
**Tests:** `T-AUD-001`, `T-AUD-002`

**Files:**
- Modify: `addon/anki_audio_quick_editor/audio_processor.py`
- Add: `tests/test_architecture/test_rule28_audio_processor_facade_wiring.py`

- [ ] **Step AUD-001.1: Add failing architecture test `T-AUD-001`**

Create `tests/test_architecture/test_rule28_audio_processor_facade_wiring.py`:

```python
"""Rule 28: audio processor facade has one dependency construction point."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR


def test_audio_processor_constructs_audio_module_deps_once() -> None:
    text = (ADDON_DIR / "audio_processor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)

    constructions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "AudioModuleDeps"
    ]

    assert len(constructions) == 1


def test_audio_processor_sync_functions_use_shared_builder() -> None:
    text = (ADDON_DIR / "audio_processor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    sync_names = {
        "_sync_tool_dependencies",
        "_sync_external_dependencies",
        "_sync_pause_dependencies",
        "_sync_rendering_dependencies",
        "_sync_noise_dependencies",
        "_sync_pitch_hum_dependencies",
    }

    calls_by_function: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in sync_names:
            calls_by_function[node.name] = sum(
                1
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "_audio_module_deps"
            )

    assert calls_by_function == {name: 1 for name in sync_names}
```

- [ ] **Step AUD-001.2: Run focused test and confirm failure**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule28_audio_processor_facade_wiring.py -q
```

Expected: FAIL because there are currently six `AudioModuleDeps(...)` constructions and no `_audio_module_deps()` helper.

- [ ] **Step AUD-001.3: Implement `C-AUD-001`**

In `addon/anki_audio_quick_editor/audio_processor.py`, add one helper directly after `_bundled_deep_filter_path()`:

```python
def _audio_module_deps() -> AudioModuleDeps:
    return AudioModuleDeps(
        find_ffmpeg=find_ffmpeg,
        find_ffprobe=find_ffprobe,
        find_deep_filter=find_deep_filter,
        find_rnnoise_bundle=find_rnnoise_bundle,
        find_dpdfnet_bundle=find_dpdfnet_bundle,
        find_spleeter_bundle=find_spleeter_bundle,
        find_silero_vad_bundle=find_silero_vad_bundle,
        probe_duration_ms=probe_duration_ms,
        probe_audio_metadata=probe_audio_metadata,
        build_audio_filters=build_audio_filters,
        build_convert_audio_command=build_convert_audio_command,
        build_size_reduction_audio_command=build_size_reduction_audio_command,
        resolve_output_policy=resolve_output_policy,
        render_external_error_message=_render_external_error_message,
        run_external_command=_run_external_command,
        external_command_run_kwargs=_external_command_run_kwargs,
        make_playback_segment_filename=make_playback_segment_filename,
        render_pause_removal_pipeline_audio=_render_pause_removal_pipeline_audio,
        bundled_deep_filter_path=_bundled_deep_filter_path,
    )
```

- [ ] **Step AUD-001.4: Implement `C-AUD-002`**

Replace each repeated `AudioModuleDeps(...)` argument inside `_sync_*_dependencies()` with `_audio_module_deps()`. Example target shape:

```python
def _sync_rendering_dependencies() -> None:
    sync_rendering_dependencies(
        _audio_rendering,
        _audio_module_deps(),
    )
```

Use this same pattern for all six sync functions listed in `T-AUD-001`.

- [ ] **Step AUD-001.5: Run focused tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule28_audio_processor_facade_wiring.py tests/test_audio_tools.py tests/test_audio_rendering_convert.py tests/test_audio_rendering_regions.py -q
```

Expected: PASS.

- [ ] **Step AUD-001.6: Commit**

Commit message:

```bash
git add addon/anki_audio_quick_editor/audio_processor.py tests/test_architecture/test_rule28_audio_processor_facade_wiring.py
git commit -m "Centralize audio facade dependency wiring" -m "The audio processor facade needs to stay public for compatibility, but repeated AudioModuleDeps construction made every dependency addition touch six sync paths. A single builder preserves the facade while reducing OCP friction and gives architecture tests one explicit invariant. Focused audio facade and rendering tests were run; full check and e2e routines were not run."
```

### Task EDT-001: Add Region Delete Dependency Protocol

**Problem:** `P-EDT-001`  
**Solution:** `S-EDT-001`  
**Changes:** `C-EDT-001`, `C-EDT-002`  
**Tests:** `T-EDT-001`, `T-EDT-002`

**Files:**
- Add: `addon/anki_audio_quick_editor/editor_deps_protocols.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete_worker.py`
- Add: `tests/test_architecture/test_rule29_editor_dependency_protocols.py`

- [ ] **Step EDT-001.1: Add failing architecture test `T-EDT-001`**

Create `tests/test_architecture/test_rule29_editor_dependency_protocols.py`:

```python
"""Rule 29: migrated editor workflows use typed dependency protocols."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR


MIGRATED_FILES = (
    "editor_region_delete.py",
    "editor_region_delete_worker.py",
)


def test_region_delete_workflow_does_not_accept_untyped_deps_any() -> None:
    violations: list[str] = []
    for relative in MIGRATED_FILES:
        path = ADDON_DIR / relative
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.arg != "deps":
                    continue
                annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
                if annotation in {"", "Any"}:
                    violations.append(f"{relative}:{node.lineno}:{node.name}")

    assert violations == []
```

- [ ] **Step EDT-001.2: Run focused test and confirm failure**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule29_editor_dependency_protocols.py -q
```

Expected: FAIL with region-delete functions that still annotate `deps: Any`.

- [ ] **Step EDT-001.3: Implement `C-EDT-001`**

Create `addon/anki_audio_quick_editor/editor_deps_protocols.py`:

```python
"""Typed dependency contracts for editor workflow modules."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol


class RegionDeleteDeps(Protocol):
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    current_media_path: Callable[[Any], tuple[Any, Path]]
    delete_selection_with_request: Callable[[Any, Any], None]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_history_availability: Callable[..., None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    eval_with_callback: Callable[..., None]
    format_ffmpeg_command: Callable[[tuple[str, ...]], str]
    is_busy: Callable[[Any], bool]
    main: Callable[[Any, Callable[[], None]], None]
    make_output_filename: Callable[..., str]
    render_audio_region_deleted: Callable[..., Any]
    render_audio_region_kept: Callable[..., Any]
    render_failed: Callable[..., None]
    replace_current_field_after_region_delete: Callable[..., None]
    request_history_availability_after_edit: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    request_graph_redraw: Callable[..., None]
    resolve_requested_field_media: Callable[..., Any]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    set_busy_for_field: Callable[..., None]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]
    temp_final_path: Callable[[str], Path]
    threading: Any
```

- [ ] **Step EDT-001.4: Implement `C-EDT-002`**

Update imports and annotations:

- In `editor_dependencies.py`, import `RegionDeleteDeps` and change `region_delete_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace` to `region_delete_deps(callbacks: Any, frontend_callbacks: Any) -> RegionDeleteDeps`.
- Keep the `SimpleNamespace(...)` attributes returned by `region_delete_deps(...)` unchanged.
- In `editor_region_delete.py`, import `RegionDeleteDeps` and change every region-delete `deps: Any` parameter to `deps: RegionDeleteDeps`.
- In `editor_region_delete_worker.py`, import `RegionDeleteDeps` and change every region-delete `deps: Any` parameter to `deps: RegionDeleteDeps`.

Apply `RegionDeleteDeps` to every `deps` parameter in `editor_region_delete.py` and `editor_region_delete_worker.py`.

- [ ] **Step EDT-001.5: Run focused tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule29_editor_dependency_protocols.py tests/test_editor_region_delete_integration.py -q
python3 scripts/dev.py typecheck
```

Expected: PASS.

- [ ] **Step EDT-001.6: Commit**

Commit message:

```bash
git add addon/anki_audio_quick_editor/editor_deps_protocols.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_region_delete.py addon/anki_audio_quick_editor/editor_region_delete_worker.py tests/test_architecture/test_rule29_editor_dependency_protocols.py
git commit -m "Type region delete editor dependencies" -m "The editor dependency-injection seam is useful for tests, but untyped deps bags make workflow contracts implicit. Region delete has a clear worker boundary, so it is the first slice converted to a Protocol-backed dependency shape without changing runtime behavior. Focused region-delete, architecture, and typecheck commands were run; full check and e2e routines were not run."
```

### Task FE-001: Add Editor Runtime Config Boundary

**Problem:** `P-FE-001`  
**Solution:** `S-FE-001`  
**Changes:** `C-FE-001`, `C-FE-002`, `C-FE-003`  
**Tests:** `T-FE-001`, `T-FE-002`, `T-FE-003`

**Files:**
- Add: `settings_ui/src/editor-inline/editor-runtime-config.ts`
- Add: `settings_ui/tests/editor-runtime-config.test.ts`
- Add: `settings_ui/tests/editor-runtime-config-boundary.test.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/SelectionToolbar.svelte`
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`
- Modify: `settings_ui/src/editor-inline/SplitExtraFields.svelte`
- Modify related frontend tests that instantiate changed components.

- [ ] **Step FE-001.1: Add failing pure config tests `T-FE-001`**

Create `settings_ui/tests/editor-runtime-config.test.ts`:

```typescript
import { afterEach, describe, expect, it } from "vitest";
import {
  editorButtonModes,
  editorRuntimeConfig,
  repeatPlaybackByDefault,
  selectionMarkerShiftButtonsEnabled,
  splitButtonDefaults,
  visibleEditorButtons,
} from "../src/editor-inline/editor-runtime-config.js";

describe("editor runtime config adapter", () => {
  afterEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
  });

  it("returns a safe fallback when Python has not injected config yet", () => {
    expect(editorRuntimeConfig()).toEqual({ audioFieldIndices: [] });
    expect(repeatPlaybackByDefault(editorRuntimeConfig())).toBe(false);
    expect(selectionMarkerShiftButtonsEnabled(editorRuntimeConfig())).toBe(false);
    expect(visibleEditorButtons(editorRuntimeConfig())).toBeUndefined();
    expect(editorButtonModes(editorRuntimeConfig())).toBeUndefined();
    expect(splitButtonDefaults(editorRuntimeConfig())).toEqual({});
  });

  it("returns injected config and stable derived values", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      editorButtonModes: { "aqe:play": "icon" },
      repeatPlaybackByDefault: true,
      selectionMarkerShiftButtonsEnabled: true,
      splitButtonDefaults: { outputFormat: "mp3", repeatPauseSeconds: 1.5 },
      visibleEditorButtons: ["aqe:play", "aqe:analyze"],
    };

    const config = editorRuntimeConfig();

    expect(config.audioFieldIndices).toEqual([0]);
    expect(repeatPlaybackByDefault(config)).toBe(true);
    expect(selectionMarkerShiftButtonsEnabled(config)).toBe(true);
    expect(visibleEditorButtons(config)).toEqual(["aqe:play", "aqe:analyze"]);
    expect(editorButtonModes(config)).toEqual({ "aqe:play": "icon" });
    expect(splitButtonDefaults(config)).toEqual({ outputFormat: "mp3", repeatPauseSeconds: 1.5 });
  });
});
```

- [ ] **Step FE-001.2: Add failing boundary scan `T-FE-002`**

Create `settings_ui/tests/editor-runtime-config-boundary.test.ts`:

```typescript
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();

const disallowedEditorConfigReaders = [
  "src/lib/editor-toolbar-buttons.ts",
  "src/editor-inline/commands.ts",
  "src/editor-inline/EditorControls.svelte",
  "src/editor-inline/SelectionToolbar.svelte",
  "src/editor-inline/GraphVisualizer.svelte",
  "src/editor-inline/SplitExtraFields.svelte",
];

describe("editor runtime config boundary", () => {
  it.each(disallowedEditorConfigReaders)("%s does not read window.__AQE_EDITOR_CONFIG__ directly", (relativePath) => {
    const source = readFileSync(join(projectRoot, relativePath), "utf8");

    expect(source).not.toContain("window.__AQE_EDITOR_CONFIG__");
  });
});
```

- [ ] **Step FE-001.3: Run focused frontend tests and confirm failure**

Run:

```bash
cd settings_ui
npm run test -- editor-runtime-config.test.ts editor-runtime-config-boundary.test.ts
```

Expected: FAIL because the adapter file does not exist and the listed files currently read `window.__AQE_EDITOR_CONFIG__`.

- [ ] **Step FE-001.4: Implement `C-FE-001`**

Create `settings_ui/src/editor-inline/editor-runtime-config.ts`:

```typescript
import type { EditorRuntimeConfig } from "./types.js";

const FALLBACK_EDITOR_RUNTIME_CONFIG: EditorRuntimeConfig = { audioFieldIndices: [] };

export function editorRuntimeConfig(): EditorRuntimeConfig {
  return window.__AQE_EDITOR_CONFIG__ ?? FALLBACK_EDITOR_RUNTIME_CONFIG;
}

export function splitButtonDefaults(config: EditorRuntimeConfig): NonNullable<EditorRuntimeConfig["splitButtonDefaults"]> {
  return config.splitButtonDefaults ?? {};
}

export function repeatPlaybackByDefault(config: EditorRuntimeConfig): boolean {
  return config.repeatPlaybackByDefault === true;
}

export function selectionMarkerShiftButtonsEnabled(config: EditorRuntimeConfig): boolean {
  return config.selectionMarkerShiftButtonsEnabled === true;
}

export function visibleEditorButtons(config: EditorRuntimeConfig): EditorRuntimeConfig["visibleEditorButtons"] {
  return config.visibleEditorButtons;
}

export function editorButtonModes(config: EditorRuntimeConfig): EditorRuntimeConfig["editorButtonModes"] {
  return config.editorButtonModes;
}

export function audioFieldSource(config: EditorRuntimeConfig, ord: number): string | null {
  return config.audioFieldSources?.[ord] ?? null;
}
```

- [ ] **Step FE-001.5: Implement `C-FE-002`**

Modify `settings_ui/src/lib/editor-toolbar-buttons.ts` so `commandButtons`, `toolbarButtons`, and `denoiseButtons` accept an optional config-like object.

Add this interface near the toolbar button factory functions:

```typescript
export interface EditorToolbarRuntimeConfig {
  splitButtonDefaults?: {
    dpdfnetAttnLimitDb?: number;
    outputFormat?: unknown;
    sizeReductionMode?: unknown;
  };
}
```

Update `commandButtons`, `toolbarButtons`, and `denoiseButtons` so each function accepts `config: EditorToolbarRuntimeConfig = {}` and still returns `readonly ToolbarButtonSpec[]`.

Inside `commandButtons(...)`, derive `outputFormat` and `sizeReductionMode` from `config.splitButtonDefaults` and keep the current returned button array unchanged except for replacing direct global config reads with those local constants.

Inside `denoiseButtons(...)`, derive `dpdfnetAttnLimitDb` from `config.splitButtonDefaults?.dpdfnetAttnLimitDb ?? 12` and keep the current returned button array unchanged except for replacing direct global config reads with that local constant.

Keep all existing buttons, labels, icons, and titles unchanged.

- [ ] **Step FE-001.6: Implement `C-FE-003`**

Update editor-inline consumers:

```svelte
<!-- settings_ui/src/editor-inline/EditorControls.svelte -->
<script lang="ts">
  import {
    editorButtonModes,
    editorRuntimeConfig,
    repeatPlaybackByDefault,
    splitButtonDefaults,
    visibleEditorButtons,
  } from "./editor-runtime-config.js";

  const runtimeConfig = editorRuntimeConfig();
  const defaults = splitButtonDefaults(runtimeConfig);
  const repeatDefault = repeatPlaybackByDefault(runtimeConfig);
  const repeatPauseDefault = defaults.repeatPauseSeconds ?? 0;
  const buttons = visibleToolbarButtons(
    toolbarButtons(runtimeConfig),
    visibleEditorButtons(runtimeConfig),
  );
  const buttonModes = editorButtonModes(runtimeConfig);
</script>
```

Pass `buttonModes`, `visibleEditorButtons`, `selectionMarkerShiftButtonsEnabled`, and `sourceFilename` as props to child components instead of reading globals in those children. Preserve existing rendered output and test IDs.

- [ ] **Step FE-001.7: Run focused frontend tests**

Run:

```bash
cd settings_ui
npm run test -- editor-runtime-config.test.ts editor-runtime-config-boundary.test.ts editor-toolbar-render-items.test.ts editor-toolbar-visibility.test.ts editor-inline.integration.toolbar-configuration.behavior.ts editor-inline.selection-toolbar.integration.test.ts
```

Expected: PASS.

- [ ] **Step FE-001.8: Commit**

Commit message:

```bash
git add settings_ui/src/editor-inline/editor-runtime-config.ts settings_ui/src/lib/editor-toolbar-buttons.ts settings_ui/src/editor-inline/commands.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/SelectionToolbar.svelte settings_ui/src/editor-inline/GraphVisualizer.svelte settings_ui/src/editor-inline/SplitExtraFields.svelte settings_ui/tests/editor-runtime-config.test.ts settings_ui/tests/editor-runtime-config-boundary.test.ts settings_ui/tests/editor-toolbar-render-items.test.ts settings_ui/tests/editor-toolbar-visibility.test.ts settings_ui/tests/editor-inline.integration.toolbar-configuration.behavior.ts settings_ui/tests/editor-inline.selection-toolbar.integration.test.ts
git commit -m "Isolate editor runtime config reads" -m "Toolbar and graph UI logic should not depend directly on Python's global injection object. A small runtime config adapter keeps the WebView boundary explicit while parameterized factories remain unit-testable outside the browser-global setup. Focused frontend tests were run; full check and e2e routines were not run."
```

### Task DIA-001: Extract Diagnostics Probe Helpers

**Problem:** `P-DIA-001`  
**Solution:** `S-DIA-001`  
**Changes:** `C-DIA-001`, `C-DIA-002`  
**Tests:** `T-DIA-001`, `T-DIA-002`

**Files:**
- Modify: `addon/anki_audio_quick_editor/diagnostics.py`
- Modify: `tests/test_diagnostics.py`
- Modify: `tests/test_diagnostics_bundled_tools.py`

- [ ] **Step DIA-001.1: Add direct helper tests `T-DIA-001`**

Append to `tests/test_diagnostics.py`:

```python
def test_run_tool_probe_timeout_returns_health(monkeypatch) -> None:
    diagnostics = import_runtime_addon_module(".diagnostics")

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["tool", "--version"], timeout=10)

    monkeypatch.setattr(diagnostics.subprocess, "run", fake_run)

    result = diagnostics._run_tool_probe(
        Path("/tmp/tool"),
        ("--version",),
        source="managed",
        run_kwargs={},
        timeout_error="tool --version timed out.",
    )

    assert result == {
        "available": False,
        "path": "/tmp/tool",
        "source": "managed",
        "version": "",
        "error": "tool --version timed out.",
    }


def test_health_from_probe_result_uses_stderr_on_failure() -> None:
    diagnostics = import_runtime_addon_module(".diagnostics")
    result = SimpleNamespace(returncode=2, stdout="", stderr="bad arch")

    health = diagnostics._health_from_probe_result(
        Path("/tmp/tool"),
        source="bundled",
        result=result,
        failure_error="tool --version failed.",
    )

    assert health == {
        "available": False,
        "path": "/tmp/tool",
        "source": "bundled",
        "version": "",
        "error": "bad arch",
    }
```

Ensure `subprocess`, `Path`, and `SimpleNamespace` are imported in the test file.

- [ ] **Step DIA-001.2: Run focused diagnostics tests and confirm failure**

Run:

```bash
python3 scripts/dev.py test -- tests/test_diagnostics.py::test_run_tool_probe_timeout_returns_health tests/test_diagnostics.py::test_health_from_probe_result_uses_stderr_on_failure -q
```

Expected: FAIL because `_run_tool_probe` and `_health_from_probe_result` do not exist yet.

- [ ] **Step DIA-001.3: Implement `C-DIA-001`**

In `addon/anki_audio_quick_editor/diagnostics.py`, add:

```python
def _run_tool_probe(
    tool_path: Any,
    args: tuple[str, ...],
    *,
    source: str,
    run_kwargs: dict[str, Any],
    timeout_error: str,
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    command = [str(tool_path), *args]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            encoding=EXTERNAL_COMMAND_TEXT_ENCODING,
            errors=EXTERNAL_COMMAND_TEXT_ERRORS,
            timeout=10,
            **run_kwargs,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(tool_path),
            "source": source,
            "version": "",
            "error": _diagnostic_error_message(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(tool_path),
            "source": source,
            "version": "",
            "error": timeout_error,
        }


def _health_from_probe_result(
    tool_path: Any,
    *,
    source: str,
    result: subprocess.CompletedProcess[str],
    failure_error: str,
    version_parser: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    probe_output = (result.stdout or result.stderr).strip()
    parser = version_parser or (lambda output: output)
    version = parser(probe_output)
    return {
        "available": result.returncode == 0,
        "path": str(tool_path),
        "source": source,
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else probe_output or failure_error,
    }
```

Add `Callable` to the existing imports from `typing` or `collections.abc`.

- [ ] **Step DIA-001.4: Implement `C-DIA-002`**

Refactor each public builder to call the helpers:

- `build_deep_filter_health(...)` uses `_run_tool_probe(deep_filter_path, ("--version",), source=source, run_kwargs=_external_command_run_kwargs(), timeout_error="deep-filter --version timed out.")`.
- `build_rnnoise_health()` uses `_run_tool_probe(rnnoise_path, ("--version",), source=_managed_or_bundled_source(rnnoise_path), run_kwargs=_external_command_run_kwargs(), timeout_error="rnnoise --version timed out.")`.
- `build_dpdfnet_health()` uses `_run_tool_probe(dpdfnet_path, ("--version",), source=_managed_or_bundled_source(dpdfnet_path), run_kwargs=_external_command_run_kwargs(), timeout_error="dpdfnet --version timed out.")`.
- `build_spleeter_health()` uses `_run_tool_probe(spleeter_path, ("--help",), source=_managed_or_bundled_source(spleeter_path), run_kwargs=_external_command_run_kwargs(), timeout_error="sherpa-spleeter --help timed out.")` and passes `version_parser=_spleeter_probe_summary`.
- `build_silero_vad_health()` uses `_run_tool_probe(silero_path, ("--help",), source=_managed_or_bundled_source(silero_path), run_kwargs=_external_command_run_kwargs(), timeout_error="silero-vad --help timed out.")` and passes `version_parser=_silero_probe_summary`.

Delete `_run_spleeter_help_probe(...)` and `_run_silero_help_probe(...)` after their callers are migrated.

- [ ] **Step DIA-001.5: Run diagnostics tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_diagnostics.py tests/test_diagnostics_bundled_tools.py tests/test_settings_commands_diagnostics_health.py -q
```

Expected: PASS.

- [ ] **Step DIA-001.6: Commit**

Commit message:

```bash
git add addon/anki_audio_quick_editor/diagnostics.py tests/test_diagnostics.py tests/test_diagnostics_bundled_tools.py
git commit -m "Share diagnostics tool probe execution" -m "Runtime health checks all run the same subprocess probe and shape the same health payload, but each tool carried its own timeout and failure branches. Shared probe helpers keep per-tool public builders stable while preventing clone growth as runtime tools expand. Focused diagnostics tests were run; full check and e2e routines were not run."
```

### Task BAT-001: Replace Batch Lazy Facade Lookup

**Problem:** `P-BAT-001`  
**Solution:** `S-BAT-001`  
**Changes:** `C-BAT-001`, `C-BAT-002`  
**Tests:** `T-BAT-001`, `T-BAT-002`

**Files:**
- Modify: `addon/anki_audio_quick_editor/batch_operation_processing.py`
- Modify: `addon/anki_audio_quick_editor/batch_operations.py`
- Modify: `addon/anki_audio_quick_editor/batch_operations_helpers.py`
- Add: `tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py`
- Modify: `tests/test_batch_conversion.py`
- Modify: `tests/test_batch_denoise.py`
- Modify: `tests/test_batch_visualization.py`

- [ ] **Step BAT-001.1: Add failing architecture test `T-BAT-001`**

Create `tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py`:

```python
"""Rule 30: batch processors use explicit dependencies, not lazy facade lookup."""

from __future__ import annotations

from .conftest import ADDON_DIR


def test_batch_processing_modules_do_not_lazy_load_batch_facade() -> None:
    violations: list[str] = []
    for relative in ("batch_operation_processing.py", "batch_operations_helpers.py"):
        text = (ADDON_DIR / relative).read_text(encoding="utf-8")
        if 'import_module(".batch_operations"' in text or "_facade_attr(" in text:
            violations.append(relative)

    assert violations == []
```

- [ ] **Step BAT-001.2: Run focused test and confirm failure**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py -q
```

Expected: FAIL because both batch processing modules currently use lazy facade lookup.

- [ ] **Step BAT-001.3: Implement `C-BAT-001`**

In `batch_operation_processing.py`, add explicit dependency shapes:

```python
@dataclass(frozen=True)
class BatchOperationDeps:
    analyze_prosody_cached: Callable[..., Any]
    render_audio: Callable[..., Any]
    render_converted_audio: Callable[..., Any]
    render_size_reduced_audio: Callable[..., Any]
    render_batch_denoise: Callable[..., Any]
```

Update function signatures:

- Add keyword-only `deps: BatchOperationDeps` to `process_graph_operation(...)` after `append_image_reference`.
- In `process_graph_operation(...)`, replace `_facade_attr("analyze_prosody_cached")(source_path, config)` with `deps.analyze_prosody_cached(source_path, config)`.

- Add keyword-only `deps: BatchOperationDeps` to `process_transform_operation(...)` after `operation_id`.
- In the convert branch, replace `_facade_attr("render_converted_audio")` with `deps.render_converted_audio`.
- In the reduce-size branch, replace `_facade_attr("render_size_reduced_audio")` with `deps.render_size_reduced_audio`.
- In the denoise branch, replace the imported `render_batch_denoise(...)` call with `deps.render_batch_denoise(source_path, effective_config, output_path)`.
- In the general transform branch, replace `_facade_attr("render_audio")` with `deps.render_audio`.

Remove `_facade_attr(...)` and the `import_module` import from `batch_operation_processing.py`.

- [ ] **Step BAT-001.4: Implement `C-BAT-002`**

In `batch_operations.py`, build production deps once:

```python
def _batch_operation_deps() -> BatchOperationDeps:
    return BatchOperationDeps(
        analyze_prosody_cached=analyze_prosody_cached,
        render_audio=render_audio,
        render_converted_audio=render_converted_audio,
        render_size_reduced_audio=render_size_reduced_audio,
        render_batch_denoise=render_batch_denoise,
    )
```

Pass `deps=_batch_operation_deps()` into `process_graph_operation(...)` and `process_transform_operation(...)`.

In `batch_operations_helpers.py`, change `render_batch_denoise(...)` to accept an optional renderer map:

```python
BatchDenoiseRenderers = Mapping[str, Callable[..., AudioProcessingResult]]


def render_batch_denoise(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path,
    renderers: BatchDenoiseRenderers | None = None,
) -> AudioProcessingResult:
    resolved_renderers = renderers or {
        "standard": render_noise_reduced_audio,
        "rnnoise": render_rnnoise_audio,
        "dpdfnet": render_dpdfnet_audio,
        "voice_only": render_voice_only_audio,
    }
    return resolved_renderers.get(config.denoise_algorithm, render_noise_reduced_audio)(
        source_path,
        config,
        output_path=output_path,
    )
```

Remove lazy facade lookup from `skipped_batch_note(...)` by importing `BatchNoteResult` directly from `batch_operation_types`.

- [ ] **Step BAT-001.5: Add behavior test `T-BAT-002`**

Add imports to `tests/test_batch_conversion.py`:

```python
from anki_audio_quick_editor.batch_operation_processing import (
    BatchOperationDeps,
    process_transform_operation,
)
from anki_audio_quick_editor.sound_refs import SoundReference
```

Add this test to `tests/test_batch_conversion.py`:


```python
def test_process_transform_operation_uses_explicit_render_deps(tmp_path: Path) -> None:
    source_path = tmp_path / "clip.wav"
    source_path.write_bytes(b"audio")
    source_html = "before [sound:clip.wav] after"
    tag = "[sound:clip.wav]"
    tag_start = source_html.index(tag)
    selection = SoundReference(
        tag=tag,
        filename="clip.wav",
        start=tag_start,
        end=tag_start + len(tag),
    )
    note = BatchNoteSnapshot(10, "Basic", {"Audio": source_html})
    calls: list[tuple[str, str, str]] = []
    writes: list[tuple[str, bytes]] = []

    def fake_render_converted_audio(*args, **kwargs):
        output_path = kwargs["output_path"]
        assert output_path is not None
        output_path.write_bytes(b"converted")
        calls.append(("convert", args[0].name, output_path.suffix))

    deps = BatchOperationDeps(
        analyze_prosody_cached=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("graph renderer should not run")
        ),
        render_audio=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("default renderer should not run")
        ),
        render_converted_audio=fake_render_converted_audio,
        render_size_reduced_audio=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("size renderer should not run")
        ),
        render_batch_denoise=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("denoise renderer should not run")
        ),
    )

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_transform_operation(
        note,
        request=BatchRunRequest(
            operation=OP_CONVERT,
            source_field="Audio",
            parameters=AudioOperationParameters(target_format="flac"),
        ),
        source_html=source_html,
        source_path=source_path,
        selection=selection,
        audio_filename="clip.wav",
        config=AudioProcessingConfig(output_format="mp3"),
        media_writer=media_writer,
        artifact_root=None,
        operation_id="test-op",
        deps=deps,
    )

    assert result.status == "written"
    assert result.written_filename is not None
    assert calls == [("convert", "clip.wav", ".flac")]
    assert writes == [(result.written_filename, b"converted")]
```

- [ ] **Step BAT-001.6: Run focused batch tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py tests/test_batch_conversion.py tests/test_batch_denoise.py tests/test_batch_visualization.py -q
```

Expected: PASS.

- [ ] **Step BAT-001.7: Commit**

Commit message:

```bash
git add addon/anki_audio_quick_editor/batch_operation_processing.py addon/anki_audio_quick_editor/batch_operations.py addon/anki_audio_quick_editor/batch_operations_helpers.py tests/test_architecture/test_rule30_batch_no_lazy_facade_lookup.py tests/test_batch_conversion.py tests/test_batch_denoise.py tests/test_batch_visualization.py
git commit -m "Make batch operation dependencies explicit" -m "Batch processing used lazy facade lookup to preserve monkeypatch seams, which hid render and analysis dependencies from static inspection. Passing explicit batch deps keeps tests injectable while removing circular facade discovery from core processing. Focused batch and architecture tests were run; full check and e2e routines were not run."
```

### Task REP-001: Extract Stable Editor Media Replacement Primitives

**Problem:** `P-REP-001`  
**Solution:** `S-REP-001`  
**Changes:** `C-REP-001`, `C-REP-002`  
**Tests:** `T-REP-001`, `T-REP-002`

**Files:**
- Add: `addon/anki_audio_quick_editor/editor_media_replacement.py`
- Add: `tests/test_editor_media_replacement.py`
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_special_transforms.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`

- [ ] **Step REP-001.1: Add primitive tests `T-REP-001`**

Create `tests/test_editor_media_replacement.py`:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from anki_audio_quick_editor.errors import AudioProcessingError


def test_persist_generated_media_uses_writer_when_output_path_exists(tmp_path: Path) -> None:
    output_path = tmp_path / "rendered.mp3"
    output_path.write_bytes(b"audio")
    calls: list[tuple[str, Path]] = []

    def write_generated_media(editor, desired_name: str, path: Path) -> str:
        calls.append((desired_name, path))
        return "saved.mp3"

    deps = SimpleNamespace(write_generated_media=write_generated_media)

    saved = persist_generated_media(object(), "desired.mp3", output_path, deps)

    assert saved == "saved.mp3"
    assert calls == [("desired.mp3", output_path)]


def test_persist_generated_media_keeps_existing_name_without_output_path() -> None:
    deps = SimpleNamespace(write_generated_media=lambda *_args: "unexpected.mp3")

    assert persist_generated_media(object(), "already-saved.mp3", None, deps) == "already-saved.mp3"


def test_replace_first_sound_reference_in_field_replaces_selected_audio() -> None:
    note = SimpleNamespace(fields=["before [sound:old.mp3] after"])
    editor = SimpleNamespace(note=note)

    old_html, new_html, old_filename = replace_first_sound_reference_in_field(
        editor,
        field_index=0,
        saved_name="new.mp3",
        missing_message="missing",
    )

    assert old_html == "before [sound:old.mp3] after"
    assert new_html == "before [sound:new.mp3] after"
    assert old_filename == "old.mp3"
    assert note.fields[0] == "before [sound:new.mp3] after"


def test_replace_first_sound_reference_in_field_raises_for_missing_audio() -> None:
    editor = SimpleNamespace(note=SimpleNamespace(fields=["plain text"]))

    with pytest.raises(AudioProcessingError, match="missing"):
        replace_first_sound_reference_in_field(
            editor,
            field_index=0,
            saved_name="new.mp3",
            missing_message="missing",
        )
```

- [ ] **Step REP-001.2: Run primitive tests and confirm failure**

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_media_replacement.py -q
```

Expected: FAIL because `editor_media_replacement.py` does not exist.

- [ ] **Step REP-001.3: Implement `C-REP-001`**

Create `addon/anki_audio_quick_editor/editor_media_replacement.py`:

```python
"""Shared primitives for editor media replacement workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import AudioProcessingError
from .sound_refs import replace_sound_reference, select_first_sound_reference


def persist_generated_media(
    editor: Any,
    saved_name: str,
    output_path: Path | None,
    deps: Any,
) -> str:
    """Persist generated media when a worker returned a temp path."""
    if output_path is None:
        return saved_name
    return deps.write_generated_media(editor, saved_name, output_path)


def replace_first_sound_reference_in_field(
    editor: Any,
    *,
    field_index: int,
    saved_name: str,
    missing_message: str,
) -> tuple[str, str, str]:
    """Replace the first sound reference in a field and return old/new details."""
    old_field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(old_field_html)
    if selection.selected is None:
        raise AudioProcessingError(missing_message)
    old_filename = selection.selected.filename
    editor.note.fields[field_index] = replace_sound_reference(
        old_field_html,
        selection.selected,
        saved_name,
    )
    return old_field_html, editor.note.fields[field_index], old_filename
```

- [ ] **Step REP-001.4: Implement `C-REP-002`**

Replace identical code in:

- `editor_processing._persist_standard_render_output(...)`
- `editor_processing.replace_current_field_after_render(...)`
- `editor_special_transforms.replace_current_field_after_noise_removal(...)`
- `editor_region_delete.replace_current_field_after_region_delete(...)`

Use the new primitives only where behavior is identical. Keep workflow-specific session updates in their existing modules.

- [ ] **Step REP-001.5: Run focused editor replacement tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_media_replacement.py tests/test_editor_post_edit_playback.py tests/test_editor_region_delete_integration.py tests/test_editor_noise_reduction_callbacks.py tests/test_editor_pitch_hum_callbacks.py -q
```

Expected: PASS.

- [ ] **Step REP-001.6: Commit**

Commit message:

```bash
git add addon/anki_audio_quick_editor/editor_media_replacement.py addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_special_transforms.py addon/anki_audio_quick_editor/editor_region_delete.py tests/test_editor_media_replacement.py
git commit -m "Share editor media replacement primitives" -m "Standard render, special transforms, and region delete all persist generated media and replace the first sound reference, but their session updates differ. Extracting only the stable primitives reduces duplication without forcing a generic replacement service over workflow-specific behavior. Focused editor replacement tests were run; full check and e2e routines were not run."
```

### Task BRG-001: Split Shared Bridge Transport From Settings Commands

**Problem:** `P-BRG-001`  
**Solution:** `S-BRG-001`  
**Changes:** `C-BRG-001`, `C-BRG-002`  
**Tests:** `T-BRG-001`, `T-BRG-002`

**Files:**
- Add: `settings_ui/src/lib/bridge-transport.ts`
- Add: `settings_ui/src/settings/bridge.ts`
- Modify: `settings_ui/src/lib/bridge.ts`
- Modify: `settings_ui/src/lib/external-links.ts`
- Modify: `settings_ui/src/lib/logger.ts`
- Move: `settings_ui/src/lib/async-jobs.ts` to `settings_ui/src/settings/async-jobs.ts`
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/tests/bridge.test.ts`
- Add: `settings_ui/tests/settings-bridge.test.ts`

- [ ] **Step BRG-001.1: Add transport/settings test split `T-BRG-001`**

Move settings-command assertions from `settings_ui/tests/bridge.test.ts` into a new `settings_ui/tests/settings-bridge.test.ts`. Keep only transport assertions in `bridge.test.ts`.

New test import target:

```typescript
import {
  copySupportReport,
  registerCallbacks,
  sendAsyncCmd,
  settingsCancel,
  settingsCheckMedia,
  settingsOpenRuntimeInstaller,
  settingsResetDefaults,
  settingsSave,
} from "../src/settings/bridge.js";
```

Keep all existing expected bridge envelopes unchanged.

- [ ] **Step BRG-001.2: Add boundary test `T-BRG-002`**

Append to `settings_ui/tests/settings-bridge.test.ts`:

```typescript
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";

const projectRoot = cwd();

it("keeps settings command names out of the shared bridge transport module", () => {
  const source = readFileSync(join(projectRoot, "src/lib/bridge-transport.ts"), "utf8");

  expect(source).not.toContain("settings.save");
  expect(source).not.toContain("settings.cancel");
  expect(source).not.toContain("settings.reset_defaults");
  expect(source).not.toContain("settings.check_media");
  expect(source).not.toContain("settings.open_runtime_installer");
  expect(source).not.toContain("settings.async");
  expect(source).not.toContain("support.copy_report");
});
```

- [ ] **Step BRG-001.3: Run focused tests and confirm failure**

Run:

```bash
cd settings_ui
npm run test -- bridge.test.ts settings-bridge.test.ts
```

Expected: FAIL because `settings/bridge.ts` and `lib/bridge-transport.ts` do not exist yet.

- [ ] **Step BRG-001.4: Implement `C-BRG-001`**

Create `settings_ui/src/lib/bridge-transport.ts`:

```typescript
const BRIDGE_RETRY_DELAY_MS = 25;
const BRIDGE_MAX_ATTEMPTS = 40;

function bridgeSender(): ((cmd: string) => void) | null {
  return typeof globalThis.pycmd === "function" ? globalThis.pycmd : null;
}

export interface BridgeEnvelope<TPayload = unknown> {
  command: string;
  payload?: TPayload;
}

export function sendBridgeCommand(command: string, attempt = 0): void {
  const sender = bridgeSender();
  if (sender) {
    sender(command);
    return;
  }
  if (attempt >= BRIDGE_MAX_ATTEMPTS) {
    return;
  }
  window.setTimeout(() => sendBridgeCommand(command, attempt + 1), BRIDGE_RETRY_DELAY_MS);
}

export function encodeBridgeCommand<TPayload>(command: string, payload?: TPayload): string {
  const envelope: BridgeEnvelope<TPayload> = { command };
  if (payload !== undefined) {
    envelope.payload = payload;
  }
  return `bridge:${JSON.stringify(envelope)}`;
}

export function sendBridgeEnvelope<TPayload>(command: string, payload?: TPayload): void {
  sendBridgeCommand(encodeBridgeCommand(command, payload));
}

declare global {
  var pycmd: ((cmd: string) => void) | undefined;
}
```

Update generic consumers:

- `settings_ui/src/lib/external-links.ts` imports `sendBridgeEnvelope` from `./bridge-transport.js`.
- `settings_ui/src/lib/logger.ts` imports `sendBridgeEnvelope` from `./bridge-transport.js`.

- [ ] **Step BRG-001.5: Implement `C-BRG-002`**

Create `settings_ui/src/settings/bridge.ts` with the settings-specific functions currently in `settings_ui/src/lib/bridge.ts`. Import `sendBridgeEnvelope` from `../lib/bridge-transport.js`.

Update `settings_ui/src/settings/SettingsApp.svelte` to import settings commands from `./bridge.js`.

Move `settings_ui/src/lib/async-jobs.ts` to `settings_ui/src/settings/async-jobs.ts` because async jobs are settings-only today. Update `SettingsApp.svelte` to import async job helpers from `./async-jobs.js`. Update the moved file to import `sendAsyncCmd` from `./bridge.js`.

After migration, make `settings_ui/src/lib/bridge.ts` a compatibility wrapper:

```typescript
export {
  encodeBridgeCommand,
  sendBridgeCommand,
  sendBridgeEnvelope,
  type BridgeEnvelope,
} from "./bridge-transport.js";
```

- [ ] **Step BRG-001.6: Run focused tests**

Run:

```bash
cd settings_ui
npm run test -- bridge.test.ts settings-bridge.test.ts app.diagnostics.test.ts app.settings.test.ts logger.test.ts error-message.test.ts
```

Expected: PASS.

- [ ] **Step BRG-001.7: Commit**

Commit message:

```bash
git add settings_ui/src/lib/bridge-transport.ts settings_ui/src/settings/bridge.ts settings_ui/src/lib/bridge.ts settings_ui/src/lib/external-links.ts settings_ui/src/lib/logger.ts settings_ui/src/lib/async-jobs.ts settings_ui/src/settings/async-jobs.ts settings_ui/src/settings/SettingsApp.svelte settings_ui/tests/bridge.test.ts settings_ui/tests/settings-bridge.test.ts settings_ui/tests/app.diagnostics.test.ts settings_ui/tests/app.settings.test.ts
git commit -m "Split settings bridge commands from shared transport" -m "The shared bridge module should be a generic WebView transport boundary, but it had accumulated settings-only command and callback APIs. Moving those APIs under settings keeps lib reusable for other screens while preserving bridge envelope behavior. Focused frontend bridge and settings tests were run; full check and e2e routines were not run."
```

## Deferred Backlog

### Task SPL-001: Group Split Button Value And Action Props

**Problem:** `P-SPL-001`  
**Solution:** `S-SPL-001`  
**Changes:** `C-SPL-001`  
**Tests:** `T-SPL-001`

Start this only when touching split-button behavior.

Implementation shape:

- Add exported interfaces near `settings_ui/src/editor-inline/SplitButton.svelte` or in a new `split-button-view-model.ts`:
  - `SplitButtonValues`
  - `SplitButtonActions`
  - `SplitButtonUiState`
- Modify `SplitButtonMenu.svelte` to receive `values`, `actions`, and `ui` instead of dozens of individual props.
- Keep `SplitButton.svelte` as the owner of local runes state for the first pass.

Focused verification:

```bash
cd settings_ui
npm run test -- editor-inline.command-splits.integration.test.ts editor-inline.split-menu-content.integration.test.ts editor-inline.recording.integration.test.ts
```

### Task REV-001: Extract Reviewer Visibility State

Problem code: `P-REV-001`  
Solution code: `S-REV-001`

Start this only when touching reviewer editor behavior.

Implementation shape:

- Add `addon/anki_audio_quick_editor/reviewer_visibility.py`.
- Move `_reviewer_editor_visible`, `_reviewer_editor_manual_override`, `_reviewer_editor_requested(...)`, `_reviewer_editor_currently_shown(...)`, and `_reviewer_editor_action_enabled(...)` behavior into a small state object.
- Keep bridge wrapping and adapter logic in `reviewer_integration.py`.

Focused verification:

```bash
python3 scripts/dev.py test -- tests/test_reviewer_integration_bridge_and_adapter.py tests/test_reviewer_integration_card_targets.py -q
```

### Task DIA-RT-001: Extract Diagnostics Incident Capture Helper

Problem code: `P-DIA-RT-001`  
Solution code: `S-DIA-RT-001`

Start this only when diagnostics runtime changes again.

Implementation shape:

- Add `_build_incident(...)` in `diagnostics_runtime.py` first.
- Make `capture_exception(...)` and `record_frontend_error(...)` call it.
- Split a new module only if the helper grows beyond incident construction.

Focused verification:

```bash
python3 scripts/dev.py test -- tests/test_diagnostics_runtime.py -q
```

## Final Verification

Run these after all immediate and short-term tasks are complete:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

Expected: both commands PASS.

If a task was intentionally skipped, record the skipped task code and reason in the implementation summary.

## Handoff Checklist

- [ ] `T-AUD-001` and `T-AUD-002` pass.
- [ ] `T-EDT-001` and `T-EDT-002` pass.
- [ ] `T-FE-001`, `T-FE-002`, and `T-FE-003` pass.
- [ ] `T-DIA-001` and `T-DIA-002` pass.
- [ ] `T-BAT-001` and `T-BAT-002` pass.
- [ ] `T-REP-001` and `T-REP-002` pass.
- [ ] `T-BRG-001` and `T-BRG-002` pass.
- [ ] Full `python3 scripts/dev.py check` passes.
- [ ] Full `python3 scripts/dev.py test-e2e` passes.
