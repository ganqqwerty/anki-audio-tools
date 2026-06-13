# Selection Marker Shift Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in inline-editor overlay that lets users move either selection edge to the previous or next chorusing marker with edge-mounted triangle buttons, while preserving existing selection, playback, zoom, and marker-editing behavior.

**Architecture:** Keep the feature inside the existing inline-editor frontend and config pipeline. Persist one UI-only toggle through config/settings/runtime injection, add a pure marker-shift resolver, render four HTML overlay buttons beside the selection edges, and route successful clicks through the existing selection mutation path with playback restart behavior aligned to resize handles.

**Tech Stack:** Python add-on config/runtime plumbing, generated JSON contracts, Svelte 5 + TypeScript inline editor, existing Bits-based tooltip wrapper, Vitest/jsdom frontend tests, pytest Python tests, and real Anki/Qt e2e tests via `python3 scripts/dev.py test-e2e`.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/config.schema.json`: add the persisted `selection_marker_shift_buttons_enabled` boolean to the config schema.
- Modify `addon/anki_audio_quick_editor/config.json`: add the default value `false`.
- Modify `addon/anki_audio_quick_editor/editor_ui.py`: inject the toggle into `window.__AQE_EDITOR_CONFIG__` as `selectionMarkerShiftButtonsEnabled`.
- Modify `addon/anki_audio_quick_editor/editor_webview_injection.py`: pass the persisted config value into `editor_ui.injection_script(...)`.
- Modify `addon/anki_audio_quick_editor/locales/en.json`, `de.json`, `ja.json`, `ru.json`, `vi.json`, `zh_CN.json`, `zh_TW.json`: add the setting label and button/disabled tooltip strings with matching keys in every locale.
- Modify `settings_ui/src/settings/settings-state.ts`: add the fallback config key with default `false`.
- Modify `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`: expose a single checkbox under the `aqe:analyze` panel.
- Modify `settings_ui/src/editor-inline/types.ts`: extend `EditorRuntimeConfig` and `GraphStateForTest` with the new runtime flag and shift-button test-state fields.
- Add `settings_ui/src/editor-inline/selection-marker-shift.ts`: pure resolver for previous/next marker targets, validity, and disabled reasons.
- Add `settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte`: static overlay markup for the four triangle buttons.
- Add `settings_ui/src/editor-inline/selection-shift-buttons-state.ts`: DOM synchronization for button visibility, disabled state, tooltip content, and narrow-band hiding.
- Modify `settings_ui/src/editor-inline/GraphVisualizer.svelte`: stamp the runtime flag onto the visualizer DOM and mount the new overlay component beside `SelectionToolbar`.
- Modify `settings_ui/src/editor-inline/visualizer-selection-renderer.ts`: publish edge visibility/narrow-band geometry and position the four buttons.
- Modify `settings_ui/src/editor-inline/selection-toolbar-state.ts`: fold shift-button syncing into the existing overlay sync surface.
- Modify `settings_ui/src/editor-inline/chorusing-dom.ts`: refresh shift-button availability when markers change.
- Modify `settings_ui/src/editor-inline/actions.ts`: add the ord-based button action and reuse existing selection mutation/playback infrastructure.
- Modify `settings_ui/src/editor-inline/styles/selection.css`: style the new buttons, triangle glyphs, hover emphasis, hidden-inner behavior, and disabled state.
- Modify `settings_ui/src/editor-inline/test-contract.ts`: expose visibility, disabled state, tooltip content, and positions for the four shift buttons.
- Modify `settings_ui/tests/editor-inline.integration.helpers.ts`: add helpers for querying/clicking shift buttons and adding/removing chorusing markers in tests.
- Add `settings_ui/tests/editor-inline.selection-marker-shift.test.ts`: unit coverage for the pure resolver.
- Modify `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`: geometry/narrow-band/reset coverage.
- Add `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`: interaction coverage for visibility, disabled tooltips, marker edits, and playback-aligned clicks.
- Modify `tests/test_contract_generation.py`, `tests/test_editor_ui.py`, `tests/test_settings_initial_state.py`, `tests/test_settings_state.py`, `tests/test_config_migration.py`, `tests/settings_command_fixtures.py`, `tests/test_settings_commands_save.py`: cover schema, defaults, runtime injection, save payloads, and migration defaults.
- Modify `settings_ui/tests/settings-state.test.ts`, `settings_ui/tests/app.test.ts`, `settings_ui/tests/settings-app-helpers.ts`, `settings_ui/tests/bridge.test.ts`, `settings_ui/tests/async-jobs.test.ts`: update full config fixtures and settings save assertions.
- Modify `e2e/editor_graph_helpers.py` and `e2e/editor_region_loop_helpers.py`: expose shift-button state and add helpers for live button clicks and marker-row edits.
- Modify `e2e/test_editor_graph_workflow.py`: verify settings-save refresh updates the current editor surface.
- Add `e2e/test_editor_selection_marker_shift_buttons_workflow.py`: live end-to-end coverage for visibility, clicking, narrow-band hiding, marker add/remove recalculation, and boundary protection.

## Baseline Requirements

- The approved design spec is `docs/superpowers/specs/2026-06-06-selection-marker-shift-buttons-design.md`.
- Keep the new toggle out of `settings_ui/src/editor-inline/graph-settings.ts` and out of every graph-analysis request payload.
- Keep the button overlay purely opt-in. Default behavior for existing users must remain unchanged.
- Route successful button clicks through the existing committed-selection path so redraw, playback-region state, selection events, toolbar sync, and chorusing updates stay coherent.
- Match resize semantics for playback:
  - if playback was `playing`, restart the committed selection from the new selection start
  - if playback was `paused`, keep it paused and set `resumeRequiresRestart`
  - if playback was `stopped`, just commit the new selection

### Task 1: Persist the Toggle Through Settings and Runtime

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/editor_ui.py`
- Modify: `addon/anki_audio_quick_editor/editor_webview_injection.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/tests/settings-state.test.ts`
- Modify: `settings_ui/tests/app.test.ts`
- Modify: `settings_ui/tests/settings-app-helpers.ts`
- Modify: `settings_ui/tests/bridge.test.ts`
- Modify: `settings_ui/tests/async-jobs.test.ts`
- Modify: `tests/test_contract_generation.py`
- Modify: `tests/test_editor_ui.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`
- Modify: `tests/test_config_migration.py`
- Modify: `tests/settings_command_fixtures.py`
- Modify: `tests/test_settings_commands_save.py`
- Test: `tests/test_contract_generation.py`
- Test: `tests/test_editor_ui.py`
- Test: `tests/test_settings_initial_state.py`
- Test: `tests/test_settings_state.py`
- Test: `tests/test_config_migration.py`
- Test: `settings_ui/tests/settings-state.test.ts`
- Test: `settings_ui/tests/app.test.ts`

- [ ] **Step 1: Add failing schema/settings/runtime tests**

Extend the existing contract/injection tests before touching implementation:

```py
# tests/test_contract_generation.py
assert "selection_marker_shift_buttons_enabled" in config["properties"]
```

```py
# tests/test_editor_ui.py
def test_injection_script_embeds_selection_marker_shift_toggle() -> None:
    script = injection_script([0], selection_marker_shift_buttons_enabled=False)
    assert _embedded_config(script)["selectionMarkerShiftButtonsEnabled"] is False
```

```py
# tests/test_config_migration.py
def test_picks_up_selection_marker_shift_button_default(self) -> None:
    user = {"_config_version": 20, "enabled": True}
    defaults = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "enabled": True,
        "selection_marker_shift_buttons_enabled": False,
    }

    migrated, changed = migrate_config(user, defaults)

    assert migrated["selection_marker_shift_buttons_enabled"] is False
    assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
    assert changed is True
```

Add the new key to the full-config fixtures in:

```text
tests/test_settings_initial_state.py
tests/test_settings_state.py
tests/settings_command_fixtures.py
settings_ui/tests/settings-state.test.ts
settings_ui/tests/settings-app-helpers.ts
settings_ui/tests/bridge.test.ts
settings_ui/tests/async-jobs.test.ts
settings_ui/tests/app.test.ts
```

Place it beside `show_graph_by_default`:

```ts
selection_marker_shift_buttons_enabled: false,
```

Also add one settings-save assertion in `settings_ui/tests/settings-state.test.ts`:

```ts
it("preserves the selection marker shift toggle when building a save payload", () => {
  expect(saveConfigPayload({
    ...config,
    selection_marker_shift_buttons_enabled: true,
  }).selection_marker_shift_buttons_enabled).toBe(true);
});
```

- [ ] **Step 2: Run the focused config/runtime tests and verify they fail**

Run:

```bash
python3 -m pytest \
  tests/test_contract_generation.py \
  tests/test_editor_ui.py \
  tests/test_settings_initial_state.py \
  tests/test_settings_state.py \
  tests/test_config_migration.py -q
cd settings_ui && npm run test -- settings-state.test.ts app.test.ts bridge.test.ts async-jobs.test.ts
```

Expected: FAIL because the config schema, runtime injection, and TypeScript config fixtures do not yet know `selection_marker_shift_buttons_enabled`.

- [ ] **Step 3: Implement the persisted toggle, the settings checkbox, and the runtime flag**

Add the schema/default:

```json
// addon/anki_audio_quick_editor/config.schema.json
"selection_marker_shift_buttons_enabled": {
  "type": "boolean"
},
```

```json
// addon/anki_audio_quick_editor/config.json
"selection_marker_shift_buttons_enabled": false,
```

Add the fallback config key:

```ts
// settings_ui/src/settings/settings-state.ts
selection_marker_shift_buttons_enabled: false,
```

Expose the checkbox in the existing `aqe:analyze` settings panel, above the analysis-only graph options:

```svelte
{:else if command === "aqe:analyze"}
  <label class="settings-toggle">
    <input
      data-testid="selection-marker-shift-buttons-enabled"
      type="checkbox"
      bind:checked={config.selection_marker_shift_buttons_enabled}
    />
    <span class="settings-label-text">{t("settings.selection_marker_shift_buttons_enabled")}</span>
  </label>
  <label class="settings-toggle">
    <input
      data-testid="show-graph-by-default"
      type="checkbox"
      bind:checked={config.show_graph_by_default}
    />
    <span class="settings-label-text">{t("settings.show_graph_by_default")}</span>
  </label>
  <GraphSettingsFields bind:config />
```

Extend the editor runtime type:

```ts
export interface EditorRuntimeConfig {
  audioFieldIndices: number[];
  audioFieldSources?: Record<number, string>;
  direction?: "ltr" | "rtl";
  initialHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }>;
  initialStatusByField?: Record<number, { kind?: string; message: string }>;
  locale?: string;
  messages?: Record<string, string>;
  pendingPostEditPlayback?: {
    fieldOrd: number;
    generation: number;
    requireGraphRedraw?: boolean;
    sourceFilename?: string;
  } | null;
  repeatPlaybackByDefault?: boolean;
  selectionMarkerShiftButtonsEnabled?: boolean;
  showGraphByDefault?: boolean;
  splitButtonDefaults?: SplitButtonDefaults;
  visibleEditorButtons?: EditorCommand[];
  editorButtonModes?: EditorButtonModes;
}
```

Inject the runtime value from Python:

```py
# addon/anki_audio_quick_editor/editor_ui.py
def injection_script(
    audio_field_indices: list[int] | None = None,
    *,
    audio_field_metadata: dict[int, dict[str, int | None]] | None = None,
    audio_field_sources: dict[int, str] | None = None,
    initial_history_availability_by_field: dict[int, dict[str, bool]] | None = None,
    initial_status_by_field: dict[int, dict[str, str]] | None = None,
    repeat_playback_by_default: bool = True,
    selection_marker_shift_buttons_enabled: bool = False,
    show_graph_by_default: bool = True,
    split_button_defaults: dict[str, object] | None = None,
    pending_post_edit_playback: dict[str, object] | None = None,
    visible_editor_buttons: list[str] | None = None,
    editor_button_modes: dict[str, str] | None = None,
) -> str:
    config = {
        "audioFieldIndices": audio_field_indices or [],
        "audioFieldMetadata": audio_field_metadata or {},
        "audioFieldSources": audio_field_sources or {},
        "initialHistoryAvailabilityByField": initial_history_availability_by_field or {},
        "initialStatusByField": initial_status_by_field or {},
        "pendingPostEditPlayback": pending_post_edit_playback,
        "repeatPlaybackByDefault": bool(repeat_playback_by_default),
        "selectionMarkerShiftButtonsEnabled": bool(selection_marker_shift_buttons_enabled),
        "showGraphByDefault": bool(show_graph_by_default),
        "visibleEditorButtons": visible_editor_buttons,
        "editorButtonModes": editor_button_modes,
        "splitButtonDefaults": split_button_defaults
        or {
            "volumeStepDb": 15.0,
            "speedStep": 1.5,
            "shareTarget": "litterbox",
            "repeatPauseSeconds": 0.0,
            "voiceRecordingCountdownSeconds": 0,
            "pauseAggressiveness": "normal",
            "pauseDetectionAlgorithm": "silencedetect",
            "pauseSilencedetectThresholdDb": -45.0,
            "pauseSilencedetectMinSilenceSeconds": 0.30,
            "pauseSilencedetectMinSpeechSeconds": 0.10,
            "pauseSilencedetectPreprocessDenoise": True,
            "pauseSileroThreshold": 0.50,
            "pauseSileroMinSilenceSeconds": 0.45,
            "pauseSileroMinSpeechSeconds": 0.10,
            "pauseSileroPreprocessDenoise": False,
            "outputFormat": "mp3",
            "sizeReductionMode": "normal",
            "sizeReductionBitrateKbps": 64,
            "sizeReductionSampleRateHz": 32000,
            "sizeReductionChannels": 1,
            "denoiseAlgorithm": "standard",
            "pitchHumMode": "direct",
            "dpdfnetAttnLimitDb": 12.0,
            "graphVoiceRange": "general",
            "graphRecordingCondition": "auto",
            "graphSmoothness": "very_smooth",
            "graphConnectShortDropoutsMs": 240,
            "graphVoiceLock": "balanced",
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": i18n["messages"],
    }
```

```py
# addon/anki_audio_quick_editor/editor_webview_injection.py
return injection_script(
    list(audio_field_sources),
    audio_field_metadata={},
    audio_field_sources=audio_field_sources,
    initial_history_availability_by_field=_initial_history_availability_by_field(
        editor,
        note,
        _SESSIONS.get(editor),
    ),
    initial_status_by_field=_initial_status_by_field(_SESSIONS.get(editor)),
    pending_post_edit_playback=_pending_post_edit_playback(editor),
    repeat_playback_by_default=bool(config.get("repeat_playback_by_default", True)),
    selection_marker_shift_buttons_enabled=bool(
        config.get("selection_marker_shift_buttons_enabled", False)
    ),
    show_graph_by_default=bool(config.get("show_graph_by_default", True)),
    visible_editor_buttons=[str(command) for command in visible_editor_buttons],
    editor_button_modes={
        str(command): str(mode)
        for command, mode in editor_button_modes.items()
        if isinstance(command, str) and isinstance(mode, str)
    },
    split_button_defaults={
        "volumeStepDb": float(config.get("volume_step_db", 15.0)),
        "speedStep": float(config.get("speed_step", 1.5)),
        "repeatPauseSeconds": float(config.get("repeat_pause_seconds", 0.0)),
        "voiceRecordingCountdownSeconds": int(
            config.get("voice_recording_countdown_seconds", 0)
        ),
        "shareTarget": str(config.get("share_target", "litterbox")),
        "pauseAggressiveness": str(config.get("pause_aggressiveness", "normal")),
        "pauseDetectionAlgorithm": str(
            config.get("pause_detection_algorithm", "silencedetect")
        ),
        "pauseSilencedetectThresholdDb": float(
            config.get("pause_silencedetect_threshold_db", -45.0)
        ),
        "pauseSilencedetectMinSilenceSeconds": float(
            config.get("pause_silencedetect_min_silence_seconds", 0.30)
        ),
        "pauseSilencedetectMinSpeechSeconds": float(
            config.get("pause_silencedetect_min_speech_seconds", 0.10)
        ),
        "pauseSilencedetectPreprocessDenoise": bool(
            config.get("pause_silencedetect_preprocess_denoise", True)
        ),
        "pauseSileroThreshold": float(config.get("pause_silero_threshold", 0.50)),
        "pauseSileroMinSilenceSeconds": float(
            config.get("pause_silero_min_silence_seconds", 0.45)
        ),
        "pauseSileroMinSpeechSeconds": float(
            config.get("pause_silero_min_speech_seconds", 0.10)
        ),
        "pauseSileroPreprocessDenoise": bool(
            config.get("pause_silero_preprocess_denoise", False)
        ),
        "denoiseAlgorithm": str(config.get("denoise_algorithm", "standard")),
        "pitchHumMode": str(config.get("pitch_hum_mode", "direct")),
        "outputFormat": str(config.get("output_format", "source")),
        "sizeReductionMode": str(config.get("size_reduction_mode", "normal")),
        "sizeReductionBitrateKbps": int(config.get("size_reduction_bitrate_kbps", 64)),
        "sizeReductionSampleRateHz": int(
            config.get("size_reduction_sample_rate_hz", 32000)
        ),
        "sizeReductionChannels": int(config.get("size_reduction_channels", 1)),
        "dpdfnetAttnLimitDb": float(config.get("dpdfnet_attn_limit_db", 12.0)),
        "graphVoiceRange": str(config.get("graph_voice_range", "general")),
        "graphRecordingCondition": str(config.get("graph_recording_condition", "auto")),
        "graphSmoothness": str(config.get("graph_smoothness", "very_smooth")),
        "graphConnectShortDropoutsMs": int(
            config.get("graph_connect_short_dropouts_ms", 240)
        ),
        "graphVoiceLock": str(config.get("graph_voice_lock", "balanced")),
    },
)
```

Add the English locale strings, then add the same keys with translated text to `de.json`, `ja.json`, `ru.json`, `vi.json`, `zh_CN.json`, and `zh_TW.json` without copying the English strings:

```json
"settings.selection_marker_shift_buttons_enabled": "Show selection marker shift buttons",
"editor.selection_shift.start_previous": "Move selection start to previous marker",
"editor.selection_shift.start_next": "Move selection start to next marker",
"editor.selection_shift.end_previous": "Move selection end to previous marker",
"editor.selection_shift.end_next": "Move selection end to next marker",
"editor.selection_shift.disabled.no_previous": "No earlier marker is available.",
"editor.selection_shift.disabled.no_next": "No later marker is available.",
"editor.selection_shift.disabled.crosses_other_edge": "That marker would cross the other selection edge.",
"editor.selection_shift.disabled.too_short": "That marker would make the selection too short."
```

Finally, update every full-config fixture returned by:

```bash
rg -l "show_graph_by_default" tests settings_ui/tests e2e
```

Add `selection_marker_shift_buttons_enabled: false` (or the Python dict equivalent) beside the existing `show_graph_by_default` field in each full-config fixture.

- [ ] **Step 4: Regenerate contracts instead of hand-editing generated files**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: regenerated `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts` include the new config property.

- [ ] **Step 5: Run the focused config, i18n, and contract checks**

Run:

```bash
python3 -m pytest \
  tests/test_contract_generation.py \
  tests/test_editor_ui.py \
  tests/test_settings_initial_state.py \
  tests/test_settings_state.py \
  tests/test_config_migration.py \
  tests/test_settings_commands_save.py \
  tests/test_i18n.py -q
python3 scripts/dev.py contracts-check
cd settings_ui && npm run test -- settings-state.test.ts app.test.ts bridge.test.ts async-jobs.test.ts
```

Expected: PASS. The new setting should exist in the schema, fixtures, runtime injection payload, save payloads, generated contracts, and locale catalogs.

- [ ] **Step 6: Commit Task 1**

```bash
git add \
  addon/anki_audio_quick_editor/config.schema.json \
  addon/anki_audio_quick_editor/config.json \
  addon/anki_audio_quick_editor/contracts_generated.py \
  addon/anki_audio_quick_editor/editor_ui.py \
  addon/anki_audio_quick_editor/editor_webview_injection.py \
  addon/anki_audio_quick_editor/locales/*.json \
  settings_ui/src/lib/generated/contracts.ts \
  settings_ui/src/settings/settings-state.ts \
  settings_ui/src/settings/ToolbarPanelSettingsFields.svelte \
  settings_ui/src/editor-inline/types.ts \
  tests/test_contract_generation.py \
  tests/test_editor_ui.py \
  tests/test_settings_initial_state.py \
  tests/test_settings_state.py \
  tests/test_config_migration.py \
  tests/settings_command_fixtures.py \
  tests/test_settings_commands_save.py \
  settings_ui/tests/settings-state.test.ts \
  settings_ui/tests/app.test.ts \
  settings_ui/tests/settings-app-helpers.ts \
  settings_ui/tests/bridge.test.ts \
  settings_ui/tests/async-jobs.test.ts
git commit -m "Persist selection marker-shift toggle through settings and runtime" \
  -m "Thread the new UI-only toggle from config defaults through the settings dialog and inline editor injection so later overlay work can read a typed runtime flag without contaminating graph-analysis payloads. This keeps existing users on the current default behavior while making current-editor refreshes and saved config round-trips deterministic. Full check and e2e not run yet; verified with focused config, contract, and i18n tests."
```

### Task 2: Add the Pure Marker-Shift Resolver

**Files:**
- Add: `settings_ui/src/editor-inline/selection-marker-shift.ts`
- Add: `settings_ui/tests/editor-inline.selection-marker-shift.test.ts`
- Test: `settings_ui/tests/editor-inline.selection-marker-shift.test.ts`

- [ ] **Step 1: Write failing unit tests for marker target resolution and disabled reasons**

Create `settings_ui/tests/editor-inline.selection-marker-shift.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { resolveSelectionMarkerShift } from "../src/editor-inline/selection-marker-shift.js";

describe("selection marker shift resolver", () => {
  it("resolves the nearest marker in each direction for either edge", () => {
    const selection = { startMs: 300, endMs: 800 };
    const markers = [0, 333, 667, 900];

    expect(resolveSelectionMarkerShift(selection, markers, "start", "previous", 1000)).toMatchObject({
      enabled: true,
      targetMarkerMs: 0,
      nextSelection: { startMs: 0, endMs: 800 },
    });
    expect(resolveSelectionMarkerShift(selection, markers, "start", "next", 1000)).toMatchObject({
      enabled: true,
      targetMarkerMs: 333,
      nextSelection: { startMs: 333, endMs: 800 },
    });
    expect(resolveSelectionMarkerShift(selection, markers, "end", "previous", 1000)).toMatchObject({
      enabled: true,
      targetMarkerMs: 667,
      nextSelection: { startMs: 300, endMs: 667 },
    });
    expect(resolveSelectionMarkerShift(selection, markers, "end", "next", 1000)).toMatchObject({
      enabled: true,
      targetMarkerMs: 900,
      nextSelection: { startMs: 300, endMs: 900 },
    });
  });

  it("returns no-marker disabled reasons when a direction has no eligible marker", () => {
    expect(resolveSelectionMarkerShift(
      { startMs: 0, endMs: 600 },
      [0, 333, 667],
      "start",
      "previous",
      1000,
    )).toMatchObject({
      enabled: false,
      disabledReason: "no_previous_marker",
      nextSelection: null,
      targetMarkerMs: null,
    });

    expect(resolveSelectionMarkerShift(
      { startMs: 300, endMs: 900 },
      [0, 333, 667],
      "end",
      "next",
      1000,
    )).toMatchObject({
      enabled: false,
      disabledReason: "no_next_marker",
      nextSelection: null,
      targetMarkerMs: null,
    });
  });

  it("rejects exact marker moves that would make the selection too short", () => {
    expect(resolveSelectionMarkerShift(
      { startMs: 300, endMs: 700 },
      [667],
      "start",
      "next",
      1000,
    )).toMatchObject({
      enabled: false,
      disabledReason: "too_short",
      nextSelection: null,
      targetMarkerMs: 667,
    });
  });

  it("rejects exact marker moves that would cross the opposite edge", () => {
    expect(resolveSelectionMarkerShift(
      { startMs: 300, endMs: 700 },
      [700, 900],
      "start",
      "next",
      1000,
    )).toMatchObject({
      enabled: false,
      disabledReason: "crosses_other_edge",
      nextSelection: null,
      targetMarkerMs: 700,
    });
  });

  it("normalizes duplicate and fractional markers before resolving a move", () => {
    expect(resolveSelectionMarkerShift(
      { startMs: 450, endMs: 900 },
      [100.2, 100.4, 333.49, 333.51, 666.6],
      "start",
      "previous",
      1000,
    )).toMatchObject({
      enabled: true,
      targetMarkerMs: 334,
      nextSelection: { startMs: 334, endMs: 900 },
    });
  });
});
```

- [ ] **Step 2: Run the new unit test and verify it fails**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.selection-marker-shift.test.ts
```

Expected: FAIL because `selection-marker-shift.ts` does not exist yet.

- [ ] **Step 3: Implement the pure resolver**

Create `settings_ui/src/editor-inline/selection-marker-shift.ts`:

```ts
import { MIN_SELECTION_DURATION_MS, type SelectionRange } from "./selection-state.js";

export type SelectionMarkerShiftDirection = "next" | "previous";
export type SelectionMarkerShiftEdge = "end" | "start";
export type SelectionMarkerShiftDisabledReason =
  | "crosses_other_edge"
  | "no_next_marker"
  | "no_previous_marker"
  | "too_short";

export interface SelectionMarkerShiftResolution {
  disabledReason: SelectionMarkerShiftDisabledReason | null;
  enabled: boolean;
  nextSelection: SelectionRange | null;
  targetMarkerMs: number | null;
}

export function resolveSelectionMarkerShift(
  selection: SelectionRange,
  markersMs: readonly number[],
  edge: SelectionMarkerShiftEdge,
  direction: SelectionMarkerShiftDirection,
  durationMs: number,
): SelectionMarkerShiftResolution {
  const duration = Math.max(0, Math.round(Number(durationMs) || 0));
  const normalizedMarkers = normalizeMarkers(markersMs, duration);
  const targetMarkerMs = findTargetMarker(selection, normalizedMarkers, edge, direction);
  if (targetMarkerMs === null) {
    return {
      disabledReason: direction === "previous" ? "no_previous_marker" : "no_next_marker",
      enabled: false,
      nextSelection: null,
      targetMarkerMs: null,
    };
  }

  if (edge === "start" && targetMarkerMs >= selection.endMs) {
    return disabled("crosses_other_edge", targetMarkerMs);
  }
  if (edge === "end" && targetMarkerMs <= selection.startMs) {
    return disabled("crosses_other_edge", targetMarkerMs);
  }
  if (edge === "start" && selection.endMs - targetMarkerMs < MIN_SELECTION_DURATION_MS) {
    return disabled("too_short", targetMarkerMs);
  }
  if (edge === "end" && targetMarkerMs - selection.startMs < MIN_SELECTION_DURATION_MS) {
    return disabled("too_short", targetMarkerMs);
  }

  return {
    disabledReason: null,
    enabled: true,
    nextSelection: edge === "start"
      ? { startMs: targetMarkerMs, endMs: selection.endMs }
      : { startMs: selection.startMs, endMs: targetMarkerMs },
    targetMarkerMs,
  };
}

function disabled(
  disabledReason: SelectionMarkerShiftDisabledReason,
  targetMarkerMs: number,
): SelectionMarkerShiftResolution {
  return {
    disabledReason,
    enabled: false,
    nextSelection: null,
    targetMarkerMs,
  };
}

function findTargetMarker(
  selection: SelectionRange,
  markersMs: readonly number[],
  edge: SelectionMarkerShiftEdge,
  direction: SelectionMarkerShiftDirection,
): number | null {
  const edgeMs = edge === "start" ? selection.startMs : selection.endMs;
  if (direction === "previous") {
    for (let index = markersMs.length - 1; index >= 0; index -= 1) {
      if (markersMs[index] < edgeMs) return markersMs[index];
    }
    return null;
  }
  for (const markerMs of markersMs) {
    if (markerMs > edgeMs) return markerMs;
  }
  return null;
}

function normalizeMarkers(markersMs: readonly number[], durationMs: number): number[] {
  return Array.from(new Set(
    markersMs
      .filter((markerMs) => Number.isFinite(markerMs))
      .map((markerMs) => Math.round(markerMs))
      .filter((markerMs) => markerMs >= 0 && markerMs <= durationMs),
  )).sort((left, right) => left - right);
}
```

- [ ] **Step 4: Run the resolver unit test and verify it passes**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.selection-marker-shift.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add \
  settings_ui/src/editor-inline/selection-marker-shift.ts \
  settings_ui/tests/editor-inline.selection-marker-shift.test.ts
git commit -m "Add a pure selection marker-shift resolver" \
  -m "Isolate previous/next marker targeting, exact validity checks, and disabled reasons in a pure helper so overlay state and click actions share one source of truth. This avoids geometry code duplicating marker math and keeps the later playback-wiring task small and testable. Full check and e2e not run yet; verified with the dedicated Vitest unit suite."
```

### Task 3: Render the Overlay Buttons and Synchronize State

**Files:**
- Add: `settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte`
- Add: `settings_ui/src/editor-inline/selection-shift-buttons-state.ts`
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`
- Modify: `settings_ui/src/editor-inline/visualizer-selection-renderer.ts`
- Modify: `settings_ui/src/editor-inline/selection-toolbar-state.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-dom.ts`
- Modify: `settings_ui/src/editor-inline/styles/selection.css`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Modify: `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`
- Modify: `settings_ui/tests/editor-inline.integration.helpers.ts`
- Add: `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`
- Test: `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`

- [ ] **Step 1: Write failing renderer and integration tests for button visibility, geometry, and tooltips**

Add test-contract fields in `settings_ui/src/editor-inline/types.ts` first so the new test file can compile against the intended state:

```ts
selectionShiftStartPreviousDisabled: boolean;
selectionShiftStartPreviousHidden: boolean;
selectionShiftStartPreviousTooltip: string;
selectionShiftStartNextDisabled: boolean;
selectionShiftStartNextHidden: boolean;
selectionShiftStartNextTooltip: string;
selectionShiftEndPreviousDisabled: boolean;
selectionShiftEndPreviousHidden: boolean;
selectionShiftEndPreviousTooltip: string;
selectionShiftEndNextDisabled: boolean;
selectionShiftEndNextHidden: boolean;
selectionShiftEndNextTooltip: string;
```

Extend `settings_ui/tests/editor-inline.visualizer-renderer.test.ts` with two focused assertions:

```ts
it("publishes overlay geometry for shift buttons and hides the inner pair when the band is narrow", () => {
  const visualizer = mountVisualizer(voicedTrack);
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot")!;
  setSvgBounds(visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg")!, 620);

  renderSelection(visualizer, { startMs: 200, endMs: 700, mode: "selection" }, null);

  expect(wrapper.dataset.selectionOverlayReady).toBe("true");
  expect(wrapper.dataset.selectionShiftHideInner).toBe("false");
  expect(wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-start-previous")?.style.left).toMatch(/px$/);
  expect(wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-end-next")?.style.left).toMatch(/px$/);

  renderSelection(visualizer, { startMs: 490, endMs: 520, mode: "selection" }, null);

  expect(wrapper.dataset.selectionShiftHideInner).toBe("true");
});

it("clears shift-button overlay geometry when the selection disappears", () => {
  const visualizer = mountVisualizer(voicedTrack);
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot")!;
  setSvgBounds(visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg")!, 620);

  renderSelection(visualizer, { startMs: 200, endMs: 700, mode: "selection" }, null);
  renderSelection(visualizer, null, null);

  expect(wrapper.dataset.selectionOverlayReady).toBe("false");
  expect(wrapper.dataset.selectionShiftHideInner).toBeUndefined();
  expect(wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-start-previous")?.style.left).toBe("");
});
```

Create `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`:

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { setControlsBusy, setSelectionDraft } from "../src/editor-inline/actions.js";
import {
  clickChorusingMarkerRail,
  dragGraphSelection,
  muteConsole,
  renderFields,
  selectionShiftButton,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection marker shift buttons", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("shows visible-edge buttons only when the toggle is on and a committed selection exists", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    window.__aqeSetVisualizer?.(0, track, 100);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftStartPreviousHidden: true,
      selectionShiftEndNextHidden: true,
    });

    dragGraphSelection(svg, 0.2, 0.8);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftStartPreviousHidden: false,
      selectionShiftStartNextHidden: false,
      selectionShiftEndPreviousHidden: false,
      selectionShiftEndNextHidden: false,
      selectionShiftStartPreviousTooltip: "Move selection start to previous marker",
      selectionShiftEndNextTooltip: "Move selection end to next marker",
    });
  });

  it("hides the inner pair for narrow bands and hides buttons during draft selection", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    window.__aqeSetVisualizer?.(0, track, 100);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.49, 0.53);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftStartPreviousHidden: false,
      selectionShiftStartNextHidden: true,
      selectionShiftEndPreviousHidden: true,
      selectionShiftEndNextHidden: false,
    });

    const visualizer = document.querySelector<HTMLElement>('.aqe-visualizer[data-aqe-field-ord="0"]')!;
    setSelectionDraft(visualizer as never, 100, 500);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftStartPreviousHidden: true,
      selectionShiftEndNextHidden: true,
    });
  });

  it("recomputes button availability after marker edits and disables visible buttons while busy", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
    window.__aqeSetVisualizer?.(0, track, 100);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.8);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftEndNextDisabled: true,
      selectionShiftEndNextTooltip: "Move selection end to next marker\n\nNo later marker is available.",
    });

    clickChorusingMarkerRail(svg, 0.9);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionShiftEndNextDisabled: false,
      selectionShiftEndNextTooltip: "Move selection end to next marker",
    });

    setControlsBusy(0, true, "Analyzing...", "aqe:analyze");
    expect(selectionShiftButton("end", "next")).toBeDisabled();
    expect(window.__aqeGraphStateForTest?.(0)?.selectionShiftEndNextTooltip).toContain("Editor is busy.");
  });
});
```

- [ ] **Step 2: Run the renderer/integration tests and verify they fail**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.visualizer-renderer.test.ts editor-inline.selection-marker-shift.integration.test.ts
```

Expected: FAIL because the overlay component, geometry publication, and test-contract fields do not exist yet.

- [ ] **Step 3: Add the overlay component, geometry publication, state sync, and styles**

Create `settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte`:

```svelte
<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  const buttons = [
    { edge: "start", direction: "previous" },
    { edge: "start", direction: "next" },
    { edge: "end", direction: "previous" },
    { edge: "end", direction: "next" },
  ] as const;
</script>

{#each buttons as button}
  <AqeTooltip side="bottom">
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class={`aqe-button aqe-selection-shift-button aqe-selection-shift-button-${button.edge}-${button.direction} aqe-tooltip-target`}
        data-aqe-selection-shift-edge={button.edge}
        data-aqe-selection-shift-direction={button.direction}
        data-testid={`aqe-selection-shift-${button.edge}-${button.direction}-${target.ord}`}
        aria-label=""
        hidden
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
      >
        <span
          class={`aqe-selection-shift-triangle aqe-selection-shift-triangle-${button.direction}`}
          aria-hidden="true"
        ></span>
      </button>
    {/snippet}
  </AqeTooltip>
{/each}
```

Mount it in `GraphVisualizer.svelte` and stamp the runtime flag on the visualizer:

```svelte
  import SelectionMarkerShiftButtons from "./SelectionMarkerShiftButtons.svelte";
```

Add this attribute to the existing visualizer root:

```svelte
data-selection-marker-shift-buttons-enabled={
  window.__AQE_EDITOR_CONFIG__?.selectionMarkerShiftButtonsEnabled === true ? "true" : "false"
}
```

Mount the new overlay inside `.aqe-visualizer-plot`, immediately before `SelectionToolbar`:

```svelte
    <SelectionMarkerShiftButtons {target} />
    <SelectionToolbar {target} />
```

Add the state sync module `settings_ui/src/editor-inline/selection-shift-buttons-state.ts`:

```ts
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import { draftSelectionForVisualizer, selectionForVisualizer } from "./selection-controller.js";
import {
  resolveSelectionMarkerShift,
  type SelectionMarkerShiftDirection,
  type SelectionMarkerShiftDisabledReason,
  type SelectionMarkerShiftEdge,
} from "./selection-marker-shift.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import type { VisualizerElement } from "./types.js";

export function syncSelectionShiftButtons(visualizer: VisualizerElement): void {
  const buttonsEnabled = visualizer.dataset.selectionMarkerShiftButtonsEnabled === "true";
  const hasTrack = visualizer.dataset.hasTrack === "true";
  const busy = document.body.dataset.aqeBusy === "true" || visualizer.dataset.graphBusy === "true";
  const selection = selectionForVisualizer(visualizer);
  const draftSelection = draftSelectionForVisualizer(visualizer);
  const markersMs = chorusingControlsForVisualizer(visualizer).markersMs;
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  const hideInner = wrapper?.dataset.selectionShiftHideInner === "true";
  const startVisible = wrapper?.dataset.selectionShiftStartVisible === "true";
  const endVisible = wrapper?.dataset.selectionShiftEndVisible === "true";

  if (!buttonsEnabled || !hasTrack || !selection || draftSelection) {
    syncHidden(visualizer);
    return;
  }

  syncOne(visualizer, "start", "previous", startVisible, false, busy, selection, markersMs);
  syncOne(visualizer, "start", "next", startVisible, hideInner, busy, selection, markersMs);
  syncOne(visualizer, "end", "previous", endVisible, hideInner, busy, selection, markersMs);
  syncOne(visualizer, "end", "next", endVisible, false, busy, selection, markersMs);
}

function syncOne(
  visualizer: VisualizerElement,
  edge: SelectionMarkerShiftEdge,
  direction: SelectionMarkerShiftDirection,
  edgeVisible: boolean,
  hideForNarrowBand: boolean,
  busy: boolean,
  selection: { startMs: number; endMs: number },
  markersMs: readonly number[],
): void {
  const button = visualizer.querySelector<HTMLButtonElement>(
    `.aqe-selection-shift-button-${edge}-${direction}`,
  );
  if (!button) return;
  const hidden = !edgeVisible || hideForNarrowBand;
  button.hidden = hidden;
  if (hidden) return;

  const baseTitle = titleFor(edge, direction);
  const resolution = resolveSelectionMarkerShift(
    selection,
    markersMs,
    edge,
    direction,
    readVisualizerTargetDurationMs(visualizer),
  );
  const disabledReason = busy
    ? t("tooltip.disabled.editor_busy")
    : reasonText(resolution.disabledReason);

  button.disabled = busy || !resolution.enabled;
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
  setButtonTooltipContent(button, tooltipWithDisabledClarification(baseTitle, disabledReason));
}

function syncHidden(visualizer: VisualizerElement): void {
  visualizer.querySelectorAll<HTMLButtonElement>(".aqe-selection-shift-button").forEach((button) => {
    button.hidden = true;
    button.disabled = true;
    button.setAttribute("aria-disabled", "true");
    setButtonTooltipContent(button, "");
  });
}

function titleFor(edge: SelectionMarkerShiftEdge, direction: SelectionMarkerShiftDirection): string {
  if (edge === "start" && direction === "previous") return t("editor.selection_shift.start_previous");
  if (edge === "start" && direction === "next") return t("editor.selection_shift.start_next");
  if (edge === "end" && direction === "previous") return t("editor.selection_shift.end_previous");
  return t("editor.selection_shift.end_next");
}

function reasonText(reason: SelectionMarkerShiftDisabledReason | null): string | undefined {
  if (reason === "no_previous_marker") return t("editor.selection_shift.disabled.no_previous");
  if (reason === "no_next_marker") return t("editor.selection_shift.disabled.no_next");
  if (reason === "crosses_other_edge") return t("editor.selection_shift.disabled.crosses_other_edge");
  if (reason === "too_short") return t("editor.selection_shift.disabled.too_short");
  return undefined;
}
```

Extend `renderSelection(...)` in `visualizer-selection-renderer.ts` to publish per-edge visibility, narrow-band state, and positions. Add these constants near `SELECTION_TOOLBAR_RIGHT_OFFSET_PX`, then add the dataset/position updates inside `setSelectionOverlayGeometry(...)`:

```ts
const SHIFT_BUTTON_SIZE_PX = 18;
const SHIFT_BUTTON_GAP_PX = 3;
const SHIFT_BUTTON_Y_OFFSET_PX = 18;
const SHIFT_BUTTON_HIDE_INNER_THRESHOLD_PX = 42;
wrapper.dataset.selectionShiftStartVisible = actualStartVisible ? "true" : "false";
wrapper.dataset.selectionShiftEndVisible = actualEndVisible ? "true" : "false";
wrapper.dataset.selectionShiftHideInner = (endPx - startPx) < SHIFT_BUTTON_HIDE_INNER_THRESHOLD_PX ? "true" : "false";

const shiftButtonTopPx = Math.max(plotTopPx, plotBottomPx - SHIFT_BUTTON_Y_OFFSET_PX);
setOverlayNodePosition(
  wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-start-previous"),
  startPx - SHIFT_BUTTON_SIZE_PX - SHIFT_BUTTON_GAP_PX,
  shiftButtonTopPx,
);
setOverlayNodePosition(
  wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-start-next"),
  startPx + SHIFT_BUTTON_GAP_PX,
  shiftButtonTopPx,
);
setOverlayNodePosition(
  wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-end-previous"),
  endPx - SHIFT_BUTTON_SIZE_PX - SHIFT_BUTTON_GAP_PX,
  shiftButtonTopPx,
);
setOverlayNodePosition(
  wrapper.querySelector<HTMLElement>(".aqe-selection-shift-button-end-next"),
  endPx + SHIFT_BUTTON_GAP_PX,
  shiftButtonTopPx,
);
```

Clear the new dataset/style state in `clearSelectionOverlayGeometry(...)`.

Hook the new sync into existing flows:

```ts
// settings_ui/src/editor-inline/selection-toolbar-state.ts
import { syncSelectionShiftButtons } from "./selection-shift-buttons-state.js";

export function syncSelectionToolbar(visualizer: VisualizerElement): void {
  syncSelectionShiftButtons(visualizer);
  const toolbar = toolbarFor(visualizer);
  const availability = regionDeleteAvailabilityFor(visualizer);
  const busy = anyBusy() || visualizer.dataset.graphBusy === "true";
  const hasTrack = visualizer.dataset.hasTrack === "true";
  const draftActive = draftSelectionForVisualizer(visualizer) !== null;

  syncSelectionToolbarButtons(visualizer, busy, availability.valid);
  const available = hasTrack && availability.hasSelection && !draftActive && !busy;
  if (!available) {
    hideToolbar(toolbar);
    setSelectionToolbarPreview(visualizer, "none");
    return;
  }

  if (toolbar) {
    toolbar.hidden = false;
    toolbar.setAttribute("aria-hidden", "false");
  }
}
```

```ts
// settings_ui/src/editor-inline/chorusing-dom.ts
import { syncSelectionToolbar } from "./selection-toolbar-state.js";

export function writeChorusingState(visualizer: VisualizerElement, state: ChorusingState): void {
  visualizer.__aqeChorusingState = state;
  visualizer.dataset.chorusingState = state.practiceState;
  visualizer.dataset.chorusingBaseStartMs = state.baseRegion ? String(Math.round(state.baseRegion.startMs)) : "";
  visualizer.dataset.chorusingBaseEndMs = state.baseRegion ? String(Math.round(state.baseRegion.endMs)) : "";
  visualizer.dataset.chorusingMarkersMs = state.markersMs.join(",");
  visualizer.dataset.chorusingActiveMarkerIndex = state.activeMarkerIndex === null ? "" : String(state.activeMarkerIndex);
  renderChorusingMarkerRow(visualizer);
  syncSelectionToolbar(visualizer);
}
```

Add helper queries in `settings_ui/tests/editor-inline.integration.helpers.ts`:

```ts
export function selectionShiftButton(
  edge: "end" | "start",
  direction: "next" | "previous",
  ord = 0,
): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(
    `[data-testid="aqe-selection-shift-${edge}-${direction}-${ord}"]`,
  )!;
}

export function clickChorusingMarkerRail(svg: SVGSVGElement, ratio: number): void {
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-chorusing-marker-row-0"]')!;
  const target = row.getAttribute("aria-hidden") === "true"
    ? document.querySelector<HTMLElement>(".aqe-chorusing-marker-hitbox")!
    : row;
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const clientX = graphClientX(svg, ratio);
  target.dispatchEvent(new EventCtor("pointerdown", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
  window.dispatchEvent(new EventCtor("pointerup", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
}
```

Style the buttons in `settings_ui/src/editor-inline/styles/selection.css`:

```css
.aqe-selection-shift-button,
.aqe-ui-root .aqe-selection-shift-button {
  align-items: center;
  background: var(--aqe-surface-color);
  border: 1px solid var(--aqe-border-color);
  border-radius: 999px;
  box-shadow: 0 3px 10px rgb(0 0 0 / 18%);
  display: inline-flex;
  height: 18px;
  justify-content: center;
  min-height: 18px;
  min-width: 18px;
  padding: 0;
  position: absolute;
  width: 18px;
  z-index: 2147483647;
}

.aqe-selection-shift-button:hover {
  filter: drop-shadow(0 0 5px var(--aqe-resize-halo));
}

.aqe-selection-shift-button[hidden] {
  display: none;
}

.aqe-selection-shift-button[disabled] {
  cursor: default;
  opacity: 0.55;
}

.aqe-selection-shift-triangle {
  display: block;
  height: 0;
  width: 0;
}

.aqe-selection-shift-triangle-previous {
  border-bottom: 5px solid transparent;
  border-right: 7px solid currentColor;
  border-top: 5px solid transparent;
  margin-left: -1px;
}

.aqe-selection-shift-triangle-next {
  border-bottom: 5px solid transparent;
  border-left: 7px solid currentColor;
  border-top: 5px solid transparent;
  margin-right: -1px;
}
```

- [ ] **Step 4: Expose the new state through the frontend test contract**

In `settings_ui/src/editor-inline/test-contract.ts`, read the four buttons and return the new fields:

```ts
const shiftStartPrevious = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-shift-button-start-previous");
const shiftStartNext = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-shift-button-start-next");
const shiftEndPrevious = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-shift-button-end-previous");
const shiftEndNext = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-shift-button-end-next");
```

```ts
selectionShiftStartPreviousDisabled: !!shiftStartPrevious?.disabled,
selectionShiftStartPreviousHidden: shiftStartPrevious ? !!shiftStartPrevious.hidden : true,
selectionShiftStartPreviousTooltip: shiftStartPrevious?.getAttribute("data-aqe-tooltip-content") || "",
selectionShiftStartNextDisabled: !!shiftStartNext?.disabled,
selectionShiftStartNextHidden: shiftStartNext ? !!shiftStartNext.hidden : true,
selectionShiftStartNextTooltip: shiftStartNext?.getAttribute("data-aqe-tooltip-content") || "",
selectionShiftEndPreviousDisabled: !!shiftEndPrevious?.disabled,
selectionShiftEndPreviousHidden: shiftEndPrevious ? !!shiftEndPrevious.hidden : true,
selectionShiftEndPreviousTooltip: shiftEndPrevious?.getAttribute("data-aqe-tooltip-content") || "",
selectionShiftEndNextDisabled: !!shiftEndNext?.disabled,
selectionShiftEndNextHidden: shiftEndNext ? !!shiftEndNext.hidden : true,
selectionShiftEndNextTooltip: shiftEndNext?.getAttribute("data-aqe-tooltip-content") || "",
```

- [ ] **Step 5: Run the renderer/integration tests and verify they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.visualizer-renderer.test.ts editor-inline.selection-marker-shift.integration.test.ts
```

Expected: PASS. The overlay buttons should exist, publish geometry, hide the inner pair for narrow selections, disappear for drafts, and update disabled tooltips when markers or busy state change.

- [ ] **Step 6: Commit Task 3**

```bash
git add \
  settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte \
  settings_ui/src/editor-inline/selection-shift-buttons-state.ts \
  settings_ui/src/editor-inline/GraphVisualizer.svelte \
  settings_ui/src/editor-inline/visualizer-selection-renderer.ts \
  settings_ui/src/editor-inline/selection-toolbar-state.ts \
  settings_ui/src/editor-inline/chorusing-dom.ts \
  settings_ui/src/editor-inline/styles/selection.css \
  settings_ui/src/editor-inline/types.ts \
  settings_ui/src/editor-inline/test-contract.ts \
  settings_ui/tests/editor-inline.visualizer-renderer.test.ts \
  settings_ui/tests/editor-inline.integration.helpers.ts \
  settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts
git commit -m "Render selection marker-shift button overlays" \
  -m "Add the four edge-mounted triangle buttons as HTML overlays, publish their geometry from the selection renderer, and synchronize visibility/disabled tooltip state from current selection and marker data. This keeps overlay concerns separate from click behavior while making narrow-band hiding, viewport clipping, and test-contract assertions deterministic. Full check and e2e not run yet; verified with focused renderer and frontend integration tests."
```

### Task 4: Wire Clicks Through Committed Selection Mutation and Playback

**Files:**
- Modify: `settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte`
- Modify: `settings_ui/src/editor-inline/actions.ts`
- Modify: `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts`

- [ ] **Step 1: Add failing integration tests for click behavior and playback alignment**

Extend `settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts` with these tests:

```ts
it("moves both selection edges to neighboring markers without changing the opposite edge", async () => {
  initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  window.__aqeSetVisualizer?.(0, track, 100);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  clickChorusingMarkerRail(svg, 0.9);
  dragGraphSelection(svg, 0.2, 0.8);

  selectionShiftButton("start", "previous").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    selectionStartMs: 0,
    selectionEndMs: 800,
    cursorMs: 0,
    playbackStartMs: 0,
    playbackEndMs: 800,
  });

  selectionShiftButton("start", "next").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    selectionStartMs: 333,
    selectionEndMs: 800,
    cursorMs: 333,
  });

  selectionShiftButton("end", "previous").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    selectionStartMs: 333,
    selectionEndMs: 667,
    cursorMs: 333,
  });

  selectionShiftButton("end", "next").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    selectionStartMs: 333,
    selectionEndMs: 900,
    cursorMs: 333,
  });
});

it("disables exact marker moves that would make the selection too short", async () => {
  initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  window.__aqeSetVisualizer?.(0, track, 100);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  clickChorusingMarkerRail(svg, 0.69);
  dragGraphSelection(svg, 0.3, 0.7);

  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    selectionShiftStartNextDisabled: true,
    selectionShiftStartNextTooltip: "Move selection start to next marker\n\nThat marker would make the selection too short.",
  });
});

it("restarts playing selections from the new start and keeps paused selections paused", async () => {
  initializeEditorRuntime({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  scan({ audioFieldIndices: [0], selectionMarkerShiftButtonsEnabled: true });
  window.__aqeSetVisualizer?.(0, track, 100);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  clickChorusingMarkerRail(svg, 0.9);
  dragGraphSelection(svg, 0.2, 0.8);
  prepareHtmlAudio();
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-play-0"]')!.click();
  await Promise.resolve();

  selectionShiftButton("start", "next").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    playbackState: "playing",
    selectionStartMs: 333,
    playbackStartMs: 333,
    playbackEndMs: 800,
    cursorMs: 333,
  });

  document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-play-0"]')!.click();
  await Promise.resolve();
  selectionShiftButton("end", "next").click();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    playbackState: "paused",
    resumeRequiresRestart: true,
    selectionEndMs: 900,
  });
});
```

- [ ] **Step 2: Run the click/playback integration test and verify it fails**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.selection-marker-shift.integration.test.ts
```

Expected: FAIL because the buttons do not yet invoke any selection mutation path.

- [ ] **Step 3: Add the ord-based button action and hook the buttons up**

Wire the buttons in `SelectionMarkerShiftButtons.svelte`:

```svelte
  import { shiftSelectionEdgeByMarkerForOrd } from "./actions.js";
```

```svelte
      <button
        {...props}
        type="button"
        class={`aqe-button aqe-selection-shift-button aqe-selection-shift-button-${button.edge}-${button.direction} aqe-tooltip-target`}
        data-aqe-selection-shift-edge={button.edge}
        data-aqe-selection-shift-direction={button.direction}
        data-testid={`aqe-selection-shift-${button.edge}-${button.direction}-${target.ord}`}
        aria-label=""
        hidden
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => shiftSelectionEdgeByMarkerForOrd(target.ord, button.edge, button.direction)}
      >
```

Add the action in `settings_ui/src/editor-inline/actions.ts`:

```ts
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import {
  resolveSelectionMarkerShift,
  type SelectionMarkerShiftDirection,
  type SelectionMarkerShiftEdge,
} from "./selection-marker-shift.js";
import { setVisualizerResumeRequiresRestart } from "./visualizer-state.js";
```

```ts
export function shiftSelectionEdgeByMarkerForOrd(
  ord: number,
  edge: SelectionMarkerShiftEdge,
  direction: SelectionMarkerShiftDirection,
): boolean {
  visualizerForOrd(ord)?.focus();
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const selection = selectionForVisualizer(visualizer);
  if (!selection) return false;

  const resolution = resolveSelectionMarkerShift(
    selection,
    chorusingControlsForVisualizer(visualizer).markersMs,
    edge,
    direction,
    readVisualizerTargetDurationMs(visualizer),
  );
  if (!resolution.enabled || !resolution.nextSelection) return false;

  const previousPlaybackState = playbackStateFor(visualizer);
  if (previousPlaybackState === "playing") {
    stopProgressClock(visualizer, { clearEngine: false });
  }

  const selected = setSelection(
    visualizer,
    resolution.nextSelection.startMs,
    resolution.nextSelection.endMs,
    { origin: "user" },
  );
  if (!selected) return false;

  if (previousPlaybackState === "paused") {
    setVisualizerResumeRequiresRestart(visualizer, true);
  }
  if (previousPlaybackState === "playing") {
    startEditorHtmlPlayback(
      visualizer,
      playbackRequestForStart(visualizer, ord, resolution.nextSelection.startMs, "html"),
    );
  }
  return true;
}
```

Keep the existing `setSelection(...)` path as the only committed-selection writer. Do not set dataset fields manually here.

- [ ] **Step 4: Run the click/playback integration tests and verify they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.selection-marker-shift.integration.test.ts
```

Expected: PASS. Clicking the overlay buttons should move the correct edge to real markers, refuse invalid exact moves, restart active playback from the new selection start, and leave paused playback paused with `resumeRequiresRestart`.

- [ ] **Step 5: Commit Task 4**

```bash
git add \
  settings_ui/src/editor-inline/SelectionMarkerShiftButtons.svelte \
  settings_ui/src/editor-inline/actions.ts \
  settings_ui/tests/editor-inline.selection-marker-shift.integration.test.ts
git commit -m "Route selection marker-shift clicks through committed selection updates" \
  -m "Hook the new edge buttons into the existing committed-selection mutation path and mirror resize playback semantics so live playback restarts from the new selection start while paused playback stays paused but requires restart. This keeps redraw, playback region state, selection events, and cursor behavior aligned with the rest of the editor. Full check and e2e not run yet; verified with the dedicated frontend integration suite."
```

### Task 5: Add Python and E2E Coverage, Then Run the Full Gates

**Files:**
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/editor_region_loop_helpers.py`
- Modify: `e2e/test_editor_graph_workflow.py`
- Add: `e2e/test_editor_selection_marker_shift_buttons_workflow.py`
- Test: `e2e/test_editor_graph_workflow.py`
- Test: `e2e/test_editor_selection_marker_shift_buttons_workflow.py`

- [ ] **Step 1: Add failing live-workflow tests and e2e helpers**

Extend `e2e/editor_region_loop_helpers.py` with reusable click helpers:

```py
def _selection_shift_button_selector(edge: str, direction: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-selection-shift-{edge}-{direction}-{ord_}"]'


def _click_selection_shift_button(editor, edge: str, direction: str, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        _graph_state_js(ord_),
        lambda state: state is not None and state[f"selectionShift{edge.title()}{direction.title()}Hidden"] is False,
        timeout=5.0,
    )
    click_selector(editor.web, _selection_shift_button_selector(edge, direction, ord_), timeout=5.0)


def _click_marker_rail(editor, ratio: float, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const ord = {ord_};
          const ratio = {ratio};
          const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"]`);
          const svg = visualizer?.querySelector(".aqe-visualizer-svg");
          const row = visualizer?.querySelector(".aqe-chorusing-marker-row");
          if (!svg || !row) return false;
          const rect = svg.getBoundingClientRect();
          const plot = {{ width: 620, left: 44, right: 10 }};
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const x = plotLeft + plotWidth * ratio;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          row.dispatchEvent(new EventCtor("pointerdown", {{
            bubbles: true,
            clientX: x,
            clientY: rect.top - 6,
          }}));
          window.dispatchEvent(new EventCtor("pointerup", {{
            bubbles: true,
            clientX: x,
            clientY: rect.top - 6,
          }}));
          return true;
        }})()
        """,
    )
```

Create `e2e/test_editor_selection_marker_shift_buttons_workflow.py`:

```py
"""E2E tests for selection marker-shift buttons in the live editor."""

from __future__ import annotations

from e2e.editor_graph_helpers import _graph_state_js, _wait_for_visualizer_track
from e2e.editor_region_loop_helpers import (
    _click_marker_rail,
    _click_selection_shift_button,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)


def test_selection_shift_buttons_move_edges_between_live_markers(anki_mw, ffmpeg_config) -> None:
    _, source, _, editor, parent, _ = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_selection_shift_buttons_source.wav",
        1.0,
        selection_marker_shift_buttons_enabled=True,
        show_graph_by_default=True,
    )
    try:
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == source.name)
        _click_marker_rail(editor, 0.9)
        _shift_drag_region(editor, 0.2, 0.8)

        _click_selection_shift_button(editor, "start", "previous")
        _state(editor, lambda state: state["selectionStartMs"] == 0 and state["selectionEndMs"] == 800)

        _click_selection_shift_button(editor, "start", "next")
        _state(editor, lambda state: state["selectionStartMs"] == 333 and state["selectionEndMs"] == 800)

        _click_selection_shift_button(editor, "end", "previous")
        _state(editor, lambda state: state["selectionStartMs"] == 333 and state["selectionEndMs"] == 667)

        _click_selection_shift_button(editor, "end", "next")
        _state(editor, lambda state: state["selectionStartMs"] == 333 and state["selectionEndMs"] == 900)
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_shift_buttons_hide_inner_pair_and_recompute_after_marker_edits(anki_mw, ffmpeg_config) -> None:
    _, _, _, editor, parent, _ = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_selection_shift_buttons_narrow.wav",
        1.0,
        selection_marker_shift_buttons_enabled=True,
        show_graph_by_default=True,
    )
    try:
        _shift_drag_region(editor, 0.49, 0.53)
        _state(editor, lambda state: (
            state["selectionShiftStartPreviousHidden"] is False
            and state["selectionShiftStartNextHidden"] is True
            and state["selectionShiftEndPreviousHidden"] is True
            and state["selectionShiftEndNextHidden"] is False
        ))

        _shift_drag_region(editor, 0.2, 0.8)
        _state(editor, lambda state: state["selectionShiftEndNextDisabled"] is True)
        _click_marker_rail(editor, 0.9)
        _state(editor, lambda state: state["selectionShiftEndNextDisabled"] is False)
        _click_marker_rail(editor, 0.9)
        _state(editor, lambda state: state["selectionShiftEndNextDisabled"] is True)
    finally:
        editor.set_note(None)
        parent.close()
```

Add a current-editor settings-refresh test to `e2e/test_editor_graph_workflow.py`:

```py
def test_editor_settings_save_refreshes_current_editor_selection_shift_toggle(
    anki_mw,
    ffmpeg_config,
) -> None:
    runtime_addon = import_runtime_addon_module()
    settings_dialog = import_runtime_addon_module(".settings").SettingsDialog
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_shift_toggle.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        show_graph_by_default=True,
        selection_marker_shift_buttons_enabled=False,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == source.name, timeout=15.0)
        run_js(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
              const rect = svg.getBoundingClientRect();
              const plot = { width: 620, left: 44, right: 10 };
              const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
              const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              const startX = plotLeft + plotWidth * 0.2;
              const endX = plotLeft + plotWidth * 0.8;
              svg.dispatchEvent(new EventCtor("pointerdown", {
                bubbles: true,
                clientX: startX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor("pointermove", {
                bubbles: true,
                clientX: endX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor("pointerup", {
                bubbles: true,
                clientX: endX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              return true;
            })()
            """,
        )
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionShiftStartPreviousHidden"] is True,
            timeout=5.0,
        )

        click_selector(editor.web, _button_selector("aqe:settings"), timeout=5.0)
        QApplication.processEvents()
        wait_for_condition(
            lambda: isinstance(runtime_addon._settings_dialog, settings_dialog)
            and runtime_addon._settings_dialog.isVisible(),
            timeout=5.0,
        )
        dialog = runtime_addon._settings_dialog
        checkbox_selector = '[data-testid="selection-marker-shift-buttons-enabled"]'
        save_selector = '[data-testid="settings-save"]'
        wait_for_js_condition(
            dialog,
            f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
            lambda value: value is False,
            timeout=5.0,
        )
        click_selector(dialog, checkbox_selector, timeout=5.0)

        with patch.object(
            anki_mw.addonManager,
            "writeConfig",
            wraps=anki_mw.addonManager.writeConfig,
        ) as mock_write:
            click_selector(dialog, save_selector, timeout=5.0)
            wait_for_condition(lambda: mock_write.called, timeout=5.0)

        saved_config = mock_write.call_args.args[1]
        assert saved_config["selection_marker_shift_buttons_enabled"] is True
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionActive"] is False,
            timeout=10.0,
        )
        run_js(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
              const rect = svg.getBoundingClientRect();
              const plot = { width: 620, left: 44, right: 10 };
              const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
              const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              const startX = plotLeft + plotWidth * 0.2;
              const endX = plotLeft + plotWidth * 0.8;
              svg.dispatchEvent(new EventCtor("pointerdown", {
                bubbles: true,
                clientX: startX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor("pointermove", {
                bubbles: true,
                clientX: endX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor("pointerup", {
                bubbles: true,
                clientX: endX,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              return true;
            })()
            """,
        )
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["selectionShiftStartPreviousHidden"] is False
            and state["selectionShiftEndNextHidden"] is False,
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 2: Run the live e2e suite and verify the new tests fail**

Run:

```bash
python3 scripts/dev.py test-e2e --verbose
```

Expected: FAIL with the new selection-marker-shift e2e assertions. The failure should be in the new workflow coverage rather than in unrelated existing flows.

- [ ] **Step 3: Finish the e2e helper state exposure and fix any missing refresh assertions**

Extend `e2e/editor_graph_helpers.py` so `_visualizer_js(...)` reads the new fields from the existing frontend test contract:

```py
const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(ord) : null;
return {
selectionActive: visualizer.dataset.selectionActive === "true",
selectionStartMs: visualizer.dataset.selectionStartMs ? Number(visualizer.dataset.selectionStartMs) : null,
selectionEndMs: visualizer.dataset.selectionEndMs ? Number(visualizer.dataset.selectionEndMs) : null,
selectionShiftStartPreviousDisabled: state ? state.selectionShiftStartPreviousDisabled : true,
selectionShiftStartPreviousHidden: state ? state.selectionShiftStartPreviousHidden : true,
selectionShiftStartPreviousTooltip: state ? state.selectionShiftStartPreviousTooltip : "",
selectionShiftStartNextDisabled: state ? state.selectionShiftStartNextDisabled : true,
selectionShiftStartNextHidden: state ? state.selectionShiftStartNextHidden : true,
selectionShiftStartNextTooltip: state ? state.selectionShiftStartNextTooltip : "",
selectionShiftEndPreviousDisabled: state ? state.selectionShiftEndPreviousDisabled : true,
selectionShiftEndPreviousHidden: state ? state.selectionShiftEndPreviousHidden : true,
selectionShiftEndPreviousTooltip: state ? state.selectionShiftEndPreviousTooltip : "",
selectionShiftEndNextDisabled: state ? state.selectionShiftEndNextDisabled : true,
selectionShiftEndNextHidden: state ? state.selectionShiftEndNextHidden : true,
selectionShiftEndNextTooltip: state ? state.selectionShiftEndNextTooltip : "",
}
```

The settings-dialog body in `test_editor_settings_save_refreshes_current_editor_selection_shift_toggle(...)` should target:

```py
checkbox_selector = '[data-testid="selection-marker-shift-buttons-enabled"]'
save_selector = '[data-testid="settings-save"]'
```

After saving, recreate the selection if the editor reload clears it, then assert:

```py
wait_for_js_condition(
    editor.web,
    _graph_state_js(),
    lambda state: state is not None
    and state["selectionActive"] is True
    and state["selectionShiftStartPreviousHidden"] is False
    and state["selectionShiftEndNextHidden"] is False,
    timeout=10.0,
)
```

- [ ] **Step 4: Run the focused e2e coverage, then the full repository gates**

Run:

```bash
python3 -m pytest \
  e2e/test_editor_graph_workflow.py::test_editor_settings_save_refreshes_current_editor_selection_shift_toggle \
  e2e/test_editor_selection_marker_shift_buttons_workflow.py -q
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

Expected: PASS. The focused e2e cases should prove the live editor behavior, `check` should stay green, and the full `test-e2e` run should confirm the feature did not regress existing editor workflows.

- [ ] **Step 5: Commit Task 5**

```bash
git add \
  e2e/editor_graph_helpers.py \
  e2e/editor_region_loop_helpers.py \
  e2e/test_editor_graph_workflow.py \
  e2e/test_editor_selection_marker_shift_buttons_workflow.py
git commit -m "Cover selection marker-shift buttons with live editor workflows" \
  -m "Add real Anki/Qt coverage for the new edge buttons so settings-save refresh, live marker edits, narrow-band hiding, and boundary protection are validated in the same environment users run. This closes the loop on the feature by proving the overlay behaves correctly after reloads and under real editor interactions. Verified with python3 scripts/dev.py check and python3 scripts/dev.py test-e2e."
```
