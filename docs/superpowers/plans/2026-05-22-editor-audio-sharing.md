# Editor Audio Sharing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an inline editor `Share` action that uploads the current audio file to Catbox or Litterbox, copies the returned URL to the clipboard, and leaves the note’s local sound reference unchanged.

**Architecture:** Extend the existing editor split-button command payload path with one new non-processing command, `aqe:share`, carrying a field-local `shareTarget`. Implement HTTP upload in a dedicated stdlib-only backend module and keep Anki/Qt clipboard, busy-state, and status handling in a separate editor adapter module so network and UI side effects remain isolated.

**Tech Stack:** Python 3.13 Anki add-on runtime, stdlib `urllib.request`, Qt clipboard APIs, Svelte 5 + TypeScript, pytest, Vitest, Anki e2e tests, executable architecture contracts.

---

## File Structure

Create:

- `addon/anki_audio_quick_editor/file_sharing.py`: stdlib multipart upload boundary for Catbox and Litterbox.
- `addon/anki_audio_quick_editor/editor_sharing.py`: editor adapter for current-file sharing, clipboard copy, and status reporting.
- `tests/test_file_sharing.py`: pure backend tests for request construction, response parsing, and failure mapping.
- `tests/test_editor_sharing.py`: editor adapter tests for busy-state handling, clipboard success, clipboard fallback, and worker failures.
- `e2e/test_editor_share_workflow.py`: editor share end-to-end coverage with a fake uploader boundary.

Modify:

- `addon/anki_audio_quick_editor/editor_actions.py`: add `CMD_SHARE`, payload decoding, and `share_target` validation.
- `addon/anki_audio_quick_editor/editor_bridge.py`: route `aqe:share` as a non-processing command carrying payload data.
- `addon/anki_audio_quick_editor/editor_callbacks.py`: export wrapped sharing callbacks.
- `addon/anki_audio_quick_editor/editor_dependencies.py`: add a dedicated sharing dependency namespace.
- `addon/anki_audio_quick_editor/editor_integration.py`: expose the wrapped share callback through the facade.
- `addon/anki_audio_quick_editor/config.schema.json`: allow `aqe:share` in `visible_editor_buttons`.
- `addon/anki_audio_quick_editor/config.json`: add `aqe:share` to default visible buttons and bump `_config_version`.
- `addon/anki_audio_quick_editor/config_migration.py`: bump config version and append `aqe:share` when the existing toolbar list lacks it.
- `addon/anki_audio_quick_editor/locales/en.json`, `de.json`, `ja.json`, `ru.json`, `vi.json`, `zh_CN.json`, `zh_TW.json`: add editor share labels and status messages.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`: add `aqe:share` metadata, default placement, and slug.
- `settings_ui/src/lib/icon-types.ts`: add one share icon name.
- `settings_ui/src/lib/CommandIcon.svelte`: render the new share icon.
- `settings_ui/src/lib/i18n.ts`: add frontend fallback strings for share labels, titles, host names, and busy messages.
- `settings_ui/src/editor-inline/types.ts`: add `ShareTarget` and `EditorCommandPayload.shareTarget`, plus field-local share state.
- `settings_ui/src/editor-inline/commands.ts`: mark share as a busy async command and provide host-specific busy text.
- `settings_ui/src/editor-inline/command-actions.ts`: set busy state for share without treating it as an audio edit.
- `settings_ui/src/editor-inline/split-button-state.ts`: store field-local share target and build `aqe:share` payloads.
- `settings_ui/src/editor-inline/SplitButton.svelte`: suppress the save-default affordance for the share popover.
- `settings_ui/src/editor-inline/SplitValueOptions.svelte`: render Catbox/Litterbox preset options for `aqe:share`.
- `e2e/editor_note_helpers.py`: include `aqe:share` in default visible buttons.
- `tests/test_config_migration.py`: cover toolbar migration adding `aqe:share`.
- `tests/test_editor_actions.py`: cover payload decoding and registration for `aqe:share`.
- `tests/test_editor_bridge_commands.py`: cover bridge routing into the share adapter.
- `tests/test_editor_ui.py`: assert injected editor config and source scan expose `aqe:share`.
- `tests/test_settings_state.py`, `tests/test_settings_initial_state.py`, `tests/settings_command_fixtures.py`: keep visible-toolbar fixtures in sync.
- `settings_ui/tests/app.test.ts`: keep toolbar visibility settings coverage in sync.
- `settings_ui/tests/editor-inline.integration.test.ts`: assert the share split button renders in the default toolbar.
- `settings_ui/tests/split-button-state.test.ts`: cover share target state and payload creation.
- `settings_ui/tests/editor-inline.command-splits.integration.test.ts`: cover share preset selection and payload dispatch.
- `tests/test_architecture/contract_editor.py`: add `editor_sharing` and allow its dependencies and side effects.
- `tests/test_architecture/test_rule21_broad_exception_allowlist.py`: allowlist the background share worker boundary if it uses a broad worker-exit catch.

---

### Task 1: Add The `aqe:share` Command Surface And Toolbar Wiring

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config_migration.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/lib/icon-types.ts`
- Modify: `settings_ui/src/lib/CommandIcon.svelte`
- Modify: `settings_ui/src/lib/i18n.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `tests/test_config_migration.py`
- Modify: `tests/test_editor_actions.py`
- Modify: `tests/test_editor_ui.py`
- Modify: `tests/test_settings_state.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/settings_command_fixtures.py`
- Modify: `settings_ui/tests/app.test.ts`
- Modify: `settings_ui/tests/editor-inline.integration.test.ts`
- Modify: `e2e/editor_note_helpers.py`

- [ ] **Step 1: Write the failing payload, migration, and default-toolbar tests**

Add to `tests/test_editor_actions.py`:

```python
def test_decode_command_accepts_share_target_payload() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:share","fieldOrd":0,"shareTarget":"litterbox"}'
    )

    assert decoded.command == "aqe:share"
    assert decoded.field_ord == 0
    assert decoded.share_target == "litterbox"


def test_share_command_is_registered_but_not_processing() -> None:
    assert "aqe:share" in BRIDGE_COMMANDS
    assert "aqe:share" not in PROCESSING_COMMANDS
```

Add to `tests/test_config_migration.py`:

```python
    def test_adds_share_button_to_visible_editor_buttons_when_missing(self) -> None:
        defaults = {
            "_config_version": 18,
            "visible_editor_buttons": ["aqe:play", "aqe:show-file", "aqe:share", "aqe:settings"],
        }
        user = {
            "_config_version": 17,
            "visible_editor_buttons": ["aqe:play", "aqe:show-file", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["_config_version"] == 18
        assert migrated["visible_editor_buttons"] == [
            "aqe:play",
            "aqe:show-file",
            "aqe:share",
            "aqe:settings",
        ]
```

Add to `settings_ui/tests/editor-inline.integration.test.ts`:

```ts
  it("mounts the share split button in the default toolbar", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const shareButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share"]');
    const shareMenuButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-menu"]');

    expect(shareButton).toBeInTheDocument();
    expect(shareMenuButton).toBeInTheDocument();
    expect(shareButton).toHaveAttribute("aria-label", "Upload the current audio and copy a public link");
  });
```

- [ ] **Step 2: Run the focused tests to confirm the surface is missing**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_actions.py tests/test_config_migration.py
python3 scripts/dev.py test-svelte -- --run settings_ui/tests/editor-inline.integration.test.ts
```

Expected:

- Python tests fail because `EditorCommandPayload` does not expose `share_target`, `BRIDGE_COMMANDS` does not contain `aqe:share`, and config migration leaves old toolbar arrays untouched.
- Svelte test fails because `[data-testid="aqe-button-0-share"]` does not exist.

- [ ] **Step 3: Add the command constant, payload field, and toolbar metadata**

Modify `addon/anki_audio_quick_editor/editor_actions.py`:

```python
CMD_SHARE = "aqe:share"
```

Add `CMD_SHARE` to `BRIDGE_COMMANDS` next to `"aqe:show-file"`:

```python
    "aqe:show-file",
    CMD_SHARE,
    CMD_SLOWER,
```

Extend the payload dataclass and decoder:

```python
@dataclass(frozen=True)
class EditorCommandPayload:
    """Normalized editor bridge command data."""

    command: str
    field_ord: int | None = None
    overrides: EditorCommandOverrides = EditorCommandOverrides()
    graph_settings: dict[str, object] | None = None
    share_target: str | None = None


def _share_target_or_none(value: Any) -> str | None:
    text = str(value)
    return text if text in {"catbox", "litterbox"} else None
```

Wire it into `decode_editor_command_payload()`:

```python
    return EditorCommandPayload(
        command=command,
        field_ord=_int_or_none(raw_payload.get("fieldOrd")),
        overrides=_overrides_from_raw(raw_payload.get("overrides")),
        graph_settings=_graph_settings_from_raw(raw_payload.get("graphSettings")),
        share_target=_share_target_or_none(raw_payload.get("shareTarget")),
    )
```

Modify `settings_ui/src/lib/editor-toolbar-buttons.ts`:

```ts
export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:show-file"
  | "aqe:share"
  | "aqe:convert"
  | "aqe:delete-selection"
  | "aqe:delete-rest"
  | "aqe:remove-pauses"
  | "aqe:denoise-standard"
  | "aqe:rnnoise"
  | "aqe:dpdfnet"
  | "aqe:voice-only"
  | "aqe:pitch-hum"
  | "aqe:slower"
  | "aqe:faster"
  | "aqe:volume-down"
  | "aqe:volume-up"
  | "aqe:undo"
  | "aqe:redo"
  | "aqe:settings";
```

Add the new default placement and button spec:

```ts
export const DEFAULT_VISIBLE_EDITOR_BUTTONS = [
  "aqe:play",
  "aqe:analyze",
  "aqe:show-file",
  "aqe:share",
  "aqe:convert",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:pitch-hum",
  "aqe:slower",
  "aqe:faster",
  "aqe:volume-down",
  "aqe:volume-up",
  "aqe:undo",
  "aqe:redo",
  "aqe:settings",
] as const satisfies readonly EditorCommand[];
```

```ts
    {
      command: "aqe:share",
      icon: "share-2",
      iconOnly: true,
      label: t("editor.command.share.label"),
      title: t("editor.command.share.title"),
    },
```

Add the slug:

```ts
  "aqe:share": "share",
```

Modify `settings_ui/src/lib/icon-types.ts`:

```ts
  | "share-2"
```

Modify `settings_ui/src/lib/CommandIcon.svelte`:

```svelte
  import Share2 from "@lucide/svelte/icons/share-2";
```

```svelte
  {:else if icon === "share-2"}
    <Share2 {size} {strokeWidth} />
```

Modify `settings_ui/src/editor-inline/types.ts`:

```ts
export type ShareTarget = "catbox" | "litterbox";
```

```ts
export interface EditorCommandPayload {
  command: EditorCommand;
  fieldOrd: number;
  overrides?: {
    denoiseAlgorithm?: DenoiseAlgorithm;
    dpdfnetAttnLimitDb?: number;
    pauseAggressiveness?: "gentle" | "normal" | "aggressive";
    pitchHumMode?: PitchHumMode;
    speedStep?: number;
    targetFormat?: OutputFormatValue;
    volumeStepDb?: number;
  };
  graphSettings?: GraphSettings;
  shareTarget?: ShareTarget;
}
```

- [ ] **Step 4: Update visible-button defaults, migration, and localization strings**

Modify `addon/anki_audio_quick_editor/config.schema.json` inside `visible_editor_buttons.items.enum`:

```json
          "aqe:play",
          "aqe:analyze",
          "aqe:show-file",
          "aqe:share",
          "aqe:convert",
          "aqe:remove-pauses",
          "aqe:denoise-standard",
          "aqe:pitch-hum",
          "aqe:slower",
          "aqe:faster",
          "aqe:volume-down",
          "aqe:volume-up",
          "aqe:undo",
          "aqe:redo",
          "aqe:settings"
```

Modify `addon/anki_audio_quick_editor/config.json`:

```json
  "_config_version": 18,
```

```json
  "visible_editor_buttons": [
    "aqe:play",
    "aqe:analyze",
    "aqe:show-file",
    "aqe:share",
    "aqe:convert",
    "aqe:remove-pauses",
    "aqe:denoise-standard",
    "aqe:pitch-hum",
    "aqe:slower",
    "aqe:faster",
    "aqe:volume-down",
    "aqe:volume-up",
    "aqe:undo",
    "aqe:redo",
    "aqe:settings"
  ],
```

Modify `addon/anki_audio_quick_editor/config_migration.py`:

```python
CURRENT_CONFIG_VERSION = 18
```

Add migration logic before the version stamp:

```python
    visible_buttons = merged.get("visible_editor_buttons")
    if isinstance(visible_buttons, list) and "aqe:share" not in visible_buttons:
        try:
            show_file_index = visible_buttons.index("aqe:show-file")
        except ValueError:
            visible_buttons.append("aqe:share")
        else:
            visible_buttons.insert(show_file_index + 1, "aqe:share")
        changed = True
```

Modify `settings_ui/src/lib/i18n.ts`:

```ts
  "editor.command.share.label": "Share",
  "editor.command.share.title": "Upload the current audio and copy a public link",
  "editor.share.target.catbox": "Catbox",
  "editor.share.target.litterbox": "Litterbox (3 days)",
  "editor.status.sharing_catbox": "Sharing to Catbox",
  "editor.status.sharing_litterbox": "Sharing to Litterbox",
```

Modify `addon/anki_audio_quick_editor/locales/en.json`:

```json
  "editor.command.share.label": "Share",
  "editor.command.share.title": "Upload the current audio and copy a public link",
  "editor.status.shared_catbox": "Copied Catbox link for {filename}",
  "editor.status.shared_litterbox": "Copied Litterbox link for {filename}",
  "editor.status.share_clipboard_unavailable": "Uploaded {filename}: {url}",
  "editor.status.share_invalid_target": "Unsupported share target.",
  "editor.status.share_failed": "Share failed: {error}",
```

Mirror the same keys into `de.json`, `ja.json`, `ru.json`, `vi.json`, `zh_CN.json`, and `zh_TW.json` using the English strings for now so runtime lookups stay in sync.

Keep visible-button fixtures in sync in:

- `tests/test_settings_state.py`
- `tests/test_settings_initial_state.py`
- `tests/settings_command_fixtures.py`
- `settings_ui/tests/app.test.ts`
- `e2e/editor_note_helpers.py`

Use the same insertion point immediately after `"aqe:show-file"`.

- [ ] **Step 5: Re-run the focused tests and commit**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_actions.py tests/test_config_migration.py tests/test_editor_ui.py tests/test_settings_state.py tests/test_settings_initial_state.py
python3 scripts/dev.py test-svelte -- --run settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/app.test.ts
```

Expected: PASS.

Commit:

```bash
git add addon/anki_audio_quick_editor/editor_actions.py addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config_migration.py addon/anki_audio_quick_editor/locales/en.json addon/anki_audio_quick_editor/locales/de.json addon/anki_audio_quick_editor/locales/ja.json addon/anki_audio_quick_editor/locales/ru.json addon/anki_audio_quick_editor/locales/vi.json addon/anki_audio_quick_editor/locales/zh_CN.json addon/anki_audio_quick_editor/locales/zh_TW.json settings_ui/src/lib/editor-toolbar-buttons.ts settings_ui/src/lib/icon-types.ts settings_ui/src/lib/CommandIcon.svelte settings_ui/src/lib/i18n.ts settings_ui/src/editor-inline/types.ts tests/test_config_migration.py tests/test_editor_actions.py tests/test_editor_ui.py tests/test_settings_state.py tests/test_settings_initial_state.py tests/settings_command_fixtures.py settings_ui/tests/app.test.ts settings_ui/tests/editor-inline.integration.test.ts e2e/editor_note_helpers.py
git commit -m "feat: add editor share command surface"
```

---

### Task 2: Add Field-Local Share Split-Button State And Frontend Dispatch

**Files:**
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/SplitValueOptions.svelte`
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/command-actions.ts`
- Modify: `settings_ui/tests/split-button-state.test.ts`
- Modify: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`

- [ ] **Step 1: Write the failing split-state and command-dispatch tests**

Add to `settings_ui/tests/split-button-state.test.ts`:

```ts
import { setShareTargetForField } from "../src/editor-inline/split-button-state.js";
```

```ts
  it("builds share payloads from field-local share target state", () => {
    setShareTargetForField(0, "litterbox");

    expect(buildSplitCommandPayload("aqe:share", 0)).toEqual({
      command: "aqe:share",
      fieldOrd: 0,
      shareTarget: "litterbox",
    });
  });

  it("keeps share target isolated per field", () => {
    setShareTargetForField(0, "litterbox");

    expect(getSplitButtonState(0).shareTarget).toBe("litterbox");
    expect(getSplitButtonState(1).shareTarget).toBe("catbox");
  });
```

Add to `settings_ui/tests/editor-inline.command-splits.integration.test.ts`:

```ts
  it("dispatches share commands with the selected host and no save-default button", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-menu"]')!.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-split-0-share-save-default"]')).toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-preset-litterbox"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:share",
      fieldOrd: 0,
      shareTarget: "litterbox",
    });
  });
```

- [ ] **Step 2: Run the focused frontend tests to verify share state is missing**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings_ui/tests/split-button-state.test.ts settings_ui/tests/editor-inline.command-splits.integration.test.ts
```

Expected: FAIL because `setShareTargetForField()` does not exist, `buildSplitCommandPayload()` ignores `aqe:share`, and the share popover UI has no host presets.

- [ ] **Step 3: Add field-local share target state and split-popover UI**

Modify `settings_ui/src/editor-inline/split-button-state.ts`:

```ts
import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
  ShareTarget,
  SplitButtonDefaults,
} from "./types.js";
```

Add a formatter and state initializer:

```ts
export function formatShareTarget(value: ShareTarget): string {
  return value === "litterbox" ? t("editor.share.target.litterbox") : t("editor.share.target.catbox");
}
```

Inside `getSplitButtonState()` repair missing runtime state and seed new state:

```ts
    if (!("shareTarget" in existing)) {
      existing.shareTarget = "catbox";
    }
```

```ts
    shareTarget: "catbox",
```

Add a setter:

```ts
export function setShareTargetForField(ord: number, value: ShareTarget): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.shareTarget = value;
  return state;
}
```

Add the payload branch:

```ts
  if (command === "aqe:share") {
    return {
      command,
      fieldOrd: ord,
      shareTarget: state.shareTarget,
    };
  }
```

Modify `settings_ui/src/editor-inline/types.ts`:

```ts
export interface FieldSplitButtonState {
  defaultDenoiseAlgorithm: DenoiseAlgorithm;
  defaultGraphConnectShortDropoutsMs: number;
  defaultGraphRecordingCondition: GraphRecordingCondition;
  defaultGraphSmoothness: GraphSmoothness;
  defaultGraphVoiceLock: GraphVoiceLock;
  defaultGraphVoiceRange: GraphVoiceRange;
  defaultOutputFormat: OutputFormatValue;
  defaultPauseAggressiveness: "gentle" | "normal" | "aggressive";
  defaultDpdfnetAttnLimitDb: number;
  defaultPitchHumMode: PitchHumMode;
  defaultRepeatPauseSeconds: number;
  defaultSpeedStep: number;
  defaultVolumeStepDb: number;
  denoiseAlgorithm: DenoiseAlgorithm;
  denoiseEdited: boolean;
  dpdfnetAttnLimitDb: number;
  dpdfnetEdited: boolean;
  graphConnectShortDropoutsMs: number;
  graphEdited: boolean;
  graphRecordingCondition: GraphRecordingCondition;
  graphSmoothness: GraphSmoothness;
  graphVoiceLock: GraphVoiceLock;
  graphVoiceRange: GraphVoiceRange;
  outputFormat: OutputFormatValue;
  outputFormatEdited: boolean;
  pauseAggressiveness: "gentle" | "normal" | "aggressive";
  pauseEdited: boolean;
  pitchHumEdited: boolean;
  pitchHumMode: PitchHumMode;
  repeatPauseEdited: boolean;
  repeatPauseSeconds: number;
  shareTarget: ShareTarget;
  speedEdited: boolean;
  speedStep: number;
  volumeEdited: boolean;
  volumeStepDb: number;
}
```

Modify `settings_ui/src/editor-inline/SplitButton.svelte` so the share popover does not render the save-default action:

```svelte
  import type { FieldTarget, ShareTarget } from "./types.js";
```

```svelte
        <SplitValueOptions
          {button}
          denoiseAlgorithm={denoiseAlgorithm}
          onChange={() => void updatePopoverPlacement()}
          onDenoiseAlgorithm={applyDenoiseAlgorithm}
          onDpdfnetAttnLimitDb={applyDpdfnetAttnLimitDb}
          onOutputFormat={applyOutputFormat}
          onPauseAggressiveness={applyPauseAggressiveness}
          onPitchHumMode={applyPitchHumMode}
          onSaveDefault={saveCurrentDefaults}
          onShareTarget={applyShareTarget}
          onSpeedStep={applySpeedStep}
          onVolumeStep={applyVolumeStep}
          pauseAggressiveness={pauseAggressiveness}
          dpdfnetAttnLimitDb={dpdfnetAttnLimitDb}
          outputFormat={outputFormat}
          pitchHumMode={pitchHumMode}
          saveDefaultSaved={defaultSaved}
          shareTarget={shareTarget}
          showSaveDefault={button.command !== "aqe:share"}
          speedStep={speedStep}
          targetOrd={target.ord}
          volumeStepDb={volumeStepDb}
        />
```

Extend the existing `syncFromState()` body and add the setter:

```svelte
  let shareTarget = $state<ShareTarget>("catbox");

  function syncFromState(state: FieldSplitButtonState): void {
    shareTarget = state.shareTarget;
  }

  function applyShareTarget(value: ShareTarget): void {
    shareTarget = setShareTargetForField(target.ord, value).shareTarget;
  }
```

Modify `settings_ui/src/editor-inline/SplitValueOptions.svelte`:

```svelte
  import {
    formatDenoiseAlgorithm,
    formatDpdfnetAggressiveness,
    formatOutputFormat,
    formatPauseAggressiveness,
    formatPitchHumMode,
    formatShareTarget,
    formatSpeedStep,
    formatVolumeDb,
  } from "./split-button-state.js";
  import type { ButtonSpec, FieldSplitButtonState, ShareTarget } from "./types.js";
```

Add props and option handling:

```svelte
  const {
    button,
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    onChange,
    onDenoiseAlgorithm,
    onDpdfnetAttnLimitDb,
    onOutputFormat,
    onPauseAggressiveness,
    onPitchHumMode,
    onSaveDefault,
    onShareTarget,
    onSpeedStep,
    onVolumeStep,
    pauseAggressiveness,
    outputFormat,
    pitchHumMode,
    saveDefaultSaved,
    shareTarget,
    showSaveDefault,
    speedStep,
    targetOrd,
    volumeStepDb,
  }: {
    button: ButtonSpec;
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    onChange: () => void;
    onDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
    onDpdfnetAttnLimitDb: (value: number) => void;
    onOutputFormat: (value: OutputFormatValue) => void;
    onPauseAggressiveness: (value: "gentle" | "normal" | "aggressive") => void;
    onPitchHumMode: (value: PitchHumMode) => void;
    onSaveDefault: () => void;
    onShareTarget: (value: ShareTarget) => void;
    onSpeedStep: (value: number) => void;
    onVolumeStep: (value: number) => void;
    pauseAggressiveness: "gentle" | "normal" | "aggressive";
    outputFormat: OutputFormatValue;
    pitchHumMode: PitchHumMode;
    saveDefaultSaved: boolean;
    shareTarget: ShareTarget;
    showSaveDefault: boolean;
    speedStep: number;
    targetOrd: number;
    volumeStepDb: number;
  } = $props();
```

```svelte
    if (button.command === "aqe:share") return formatShareTarget(shareTarget);
```

```svelte
    if (button.command === "aqe:share") return ["catbox", "litterbox"];
```

```svelte
    if (value === "catbox") return t("editor.share.target.catbox");
    if (value === "litterbox") return t("editor.share.target.litterbox");
```

```svelte
    if (value === "catbox" || value === "litterbox") onShareTarget(value);
```

Guard the save-default button:

```svelte
  {#if showSaveDefault}
    <SplitDefaultSaveButton
      onSave={onSaveDefault}
      saved={saveDefaultSaved}
      testId={`aqe-split-${targetOrd}-${slug}-save-default`}
    />
  {/if}
```

- [ ] **Step 4: Mark share as a busy async command without treating it as an edit**

Modify `settings_ui/src/editor-inline/commands.ts`:

```ts
export const BUSY_COMMANDS = new Set<EditorCommand>([
  ...PROCESSING_COMMANDS,
  "aqe:share",
]);
```

Extend `processingMessage()`:

```ts
  if (command === "aqe:share") {
    const shareTarget = payload?.shareTarget ?? "catbox";
    return shareTarget === "litterbox"
      ? `${t("editor.status.sharing_litterbox")}...`
      : `${t("editor.status.sharing_catbox")}...`;
  }
```

Modify `settings_ui/src/editor-inline/command-actions.ts`:

```ts
import { BUSY_COMMANDS, PROCESSING_COMMANDS, processingMessage } from "./commands.js";
```

```ts
  if (BUSY_COMMANDS.has(command)) {
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command, payload));
  }

  const effectivePayload = payload ?? (
    command === "aqe:pitch-hum" || command === "aqe:share"
      ? buildSplitCommandPayload(command, ord)
      : undefined
  );
```

Keep playback-after-edit unchanged:

```ts
function shouldPlayAfterSuccessfulEdit(command: EditorCommand): boolean {
  return PROCESSING_COMMANDS.has(command) || command === "aqe:undo" || command === "aqe:redo";
}
```

- [ ] **Step 5: Re-run the frontend tests and commit**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings_ui/tests/split-button-state.test.ts settings_ui/tests/editor-inline.command-splits.integration.test.ts settings_ui/tests/editor-inline.integration.test.ts
```

Expected: PASS.

Commit:

```bash
git add settings_ui/src/editor-inline/split-button-state.ts settings_ui/src/editor-inline/SplitButton.svelte settings_ui/src/editor-inline/SplitValueOptions.svelte settings_ui/src/editor-inline/commands.ts settings_ui/src/editor-inline/command-actions.ts settings_ui/tests/split-button-state.test.ts settings_ui/tests/editor-inline.command-splits.integration.test.ts settings_ui/tests/editor-inline.integration.test.ts
git commit -m "feat: add share split button host selection"
```

---

### Task 3: Implement The Catbox/Litterbox Upload Backend

**Files:**
- Create: `addon/anki_audio_quick_editor/file_sharing.py`
- Create: `tests/test_file_sharing.py`

- [ ] **Step 1: Write the failing backend tests for request building and failure mapping**

Create `tests/test_file_sharing.py`:

```python
from __future__ import annotations

import io
import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from anki_audio_quick_editor.file_sharing import (
    CATBOX_UPLOAD_URL,
    LITTERBOX_RETENTION,
    LITTERBOX_UPLOAD_URL,
    FileSharingError,
    upload_file,
)


class _Response:
    def __init__(self, text: str) -> None:
        self._text = text

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._text.encode("utf-8")


def test_upload_file_posts_to_catbox_without_retention(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: float):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["content_type"] = request.headers["Content-Type"]
        captured["body"] = request.data
        return _Response("https://files.catbox.moe/share123.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    result = upload_file(source, "catbox")

    assert result == "https://files.catbox.moe/share123.mp3"
    assert captured["url"] == CATBOX_UPLOAD_URL
    assert captured["timeout"] == 60.0
    assert b'name=\"reqtype\"' in captured["body"]
    assert b"fileupload" in captured["body"]
    assert b'name=\"fileToUpload\"; filename=\"clip.mp3\"' in captured["body"]
    assert b'name=\"time\"' not in captured["body"]


def test_upload_file_posts_to_litterbox_with_fixed_72h_retention(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: float):
        captured["url"] = request.full_url
        captured["body"] = request.data
        return _Response("https://litterbox.catbox.moe/abc123/clip.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    result = upload_file(source, "litterbox")

    assert result == "https://litterbox.catbox.moe/abc123/clip.mp3"
    assert captured["url"] == LITTERBOX_UPLOAD_URL
    assert LITTERBOX_RETENTION == "72h"
    assert b'name=\"time\"' in captured["body"]
    assert b"72h" in captured["body"]


def test_upload_file_rejects_non_url_response(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    monkeypatch.setattr(
        "anki_audio_quick_editor.file_sharing.urllib.request.urlopen",
        lambda request, *, timeout: _Response("nope"),
    )

    with pytest.raises(FileSharingError, match="Unexpected upload response: nope"):
        upload_file(source, "catbox")


def test_upload_file_maps_timeout_to_file_sharing_error(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    def fake_urlopen(request: urllib.request.Request, *, timeout: float):
        raise socket.timeout("timed out")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    with pytest.raises(FileSharingError, match="Upload timed out"):
        upload_file(source, "catbox")


def test_upload_file_maps_http_errors_to_file_sharing_error(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    def fake_urlopen(request: urllib.request.Request, *, timeout: float):
        raise urllib.error.HTTPError(
            request.full_url,
            503,
            "service unavailable",
            hdrs={},
            fp=io.BytesIO(b"slow down"),
        )

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    with pytest.raises(FileSharingError, match="Upload failed with HTTP 503: slow down"):
        upload_file(source, "catbox")
```

- [ ] **Step 2: Run the new backend tests to confirm the module is missing**

Run:

```bash
python3 scripts/dev.py test tests/test_file_sharing.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'anki_audio_quick_editor.file_sharing'`.

- [ ] **Step 3: Implement the stdlib upload module**

Create `addon/anki_audio_quick_editor/file_sharing.py`:

```python
"""Stdlib-only file upload helpers for Catbox and Litterbox."""

from __future__ import annotations

import mimetypes
import socket
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Final

CATBOX_UPLOAD_URL: Final[str] = "https://catbox.moe/user/api.php"
LITTERBOX_UPLOAD_URL: Final[str] = "https://litterbox.catbox.moe/resources/internals/api.php"
LITTERBOX_RETENTION: Final[str] = "72h"
DEFAULT_TIMEOUT_SECONDS: Final[float] = 60.0


class FileSharingError(RuntimeError):
    """Raised when a remote upload cannot be completed."""


def upload_file(path: Path, target: str, timeout_s: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Upload ``path`` to the requested host and return the direct URL."""
    file_path = Path(path)
    if target not in {"catbox", "litterbox"}:
        raise FileSharingError(f"Unsupported share target: {target}")
    if not file_path.is_file():
        raise FileSharingError(f"Missing upload file: {file_path}")

    fields = [("reqtype", "fileupload")]
    url = CATBOX_UPLOAD_URL
    if target == "litterbox":
        url = LITTERBOX_UPLOAD_URL
        fields.append(("time", LITTERBOX_RETENTION))

    content_type, body = _multipart_body(fields, file_path)
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "User-Agent": "anki-audio-quick-editor/1"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw_text = response.read().decode("utf-8", errors="replace").strip()
    except socket.timeout as exc:
        raise FileSharingError("Upload timed out") from exc
    except urllib.error.HTTPError as exc:
        message = _http_error_message(exc)
        raise FileSharingError(f"Upload failed with HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise FileSharingError(f"Upload failed: {reason}") from exc
    except OSError as exc:
        raise FileSharingError(f"Upload failed: {exc}") from exc

    if not raw_text.startswith("https://"):
        raise FileSharingError(f"Unexpected upload response: {raw_text}")
    return raw_text


def _multipart_body(fields: list[tuple[str, str]], path: Path) -> tuple[str, bytes]:
    boundary = f"----aqe-{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )
    parts.append(f"--{boundary}\r\n".encode("utf-8"))
    parts.append(
        (
            f'Content-Disposition: form-data; name="fileToUpload"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return f"multipart/form-data; boundary={boundary}", b"".join(parts)


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except OSError:
        body = ""
    return body or exc.reason or "unknown error"
```

- [ ] **Step 4: Add one more strict-target test and verify no account/userhash path sneaks in**

Append to `tests/test_file_sharing.py`:

```python
def test_upload_file_rejects_unknown_target_before_network(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    with pytest.raises(FileSharingError, match="Unsupported share target: somewhere"):
        upload_file(source, "somewhere")
```

This keeps the host choice strictly limited to `catbox` and `litterbox` and avoids accidental `userhash` or settings-driven upload modes.

- [ ] **Step 5: Re-run the backend tests and commit**

Run:

```bash
python3 scripts/dev.py test tests/test_file_sharing.py
```

Expected: PASS.

Commit:

```bash
git add addon/anki_audio_quick_editor/file_sharing.py tests/test_file_sharing.py
git commit -m "feat: add catbox upload backend"
```

---

### Task 4: Wire Editor Sharing Through The Bridge, Clipboard, And Architecture Contracts

**Files:**
- Create: `addon/anki_audio_quick_editor/editor_sharing.py`
- Create: `tests/test_editor_sharing.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Modify: `tests/test_editor_bridge_commands.py`
- Modify: `tests/test_architecture/contract_editor.py`
- Modify: `tests/test_architecture/test_rule21_broad_exception_allowlist.py`

- [ ] **Step 1: Write the failing editor adapter and bridge tests**

Create `tests/test_editor_sharing.py`:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_actions import EditorCommandPayload
from anki_audio_quick_editor.editor_sharing import finish_shared_audio, share_current_audio_file


def test_share_current_audio_file_rejects_invalid_target_without_upload(tmp_path: Path) -> None:
    editor = SimpleNamespace(currentField=0, web=MagicMock(), mw=MagicMock())
    session = SimpleNamespace(processing=False, analysis_busy=False, analysis_busy_fields=set(), playback_preparing=False)
    statuses: list[tuple[str, str]] = []

    deps = SimpleNamespace(
        current_media_path=lambda _editor: (session, tmp_path / "clip.mp3"),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=lambda _session: False,
        main=lambda _editor, callback: callback(),
        set_busy=lambda *_args, **_kwargs: None,
        still_processing_message="Still processing. Please wait.",
        threading=SimpleNamespace(Thread=lambda target, daemon: SimpleNamespace(start=target)),
        upload_file=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not upload")),
    )

    share_current_audio_file(editor, EditorCommandPayload(command="aqe:share", field_ord=0), deps)

    assert statuses == [("Unsupported share target.", "error")]


def test_finish_shared_audio_copies_url_to_clipboard_and_reports_success() -> None:
    from aqt.qt import QApplication

    editor = SimpleNamespace(web=MagicMock())
    clipboard = MagicMock()
    statuses: list[tuple[str, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    QApplication.clipboard.return_value = clipboard
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        t=lambda key, values=None: {
            "editor.status.shared_catbox": f"Copied Catbox link for {values['filename']}",
            "editor.status.share_clipboard_unavailable": f"Uploaded {values['filename']}: {values['url']}",
        }[key],
    )

    finish_shared_audio(editor, "catbox", "clip.mp3", "https://files.catbox.moe/share123.mp3", deps)

    clipboard.setText.assert_called_once_with("https://files.catbox.moe/share123.mp3")
    assert statuses == [("Copied Catbox link for clip.mp3", "info")]
    assert busy_calls[-1] == (False, "", "")


def test_finish_shared_audio_falls_back_to_status_when_clipboard_is_unavailable() -> None:
    from aqt.qt import QApplication

    editor = SimpleNamespace(web=MagicMock())
    statuses: list[tuple[str, str]] = []

    QApplication.clipboard.return_value = None
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        logger=MagicMock(),
        set_busy=lambda *_args, **_kwargs: None,
        t=lambda key, values=None: {
            "editor.status.shared_litterbox": f"Copied Litterbox link for {values['filename']}",
            "editor.status.share_clipboard_unavailable": f"Uploaded {values['filename']}: {values['url']}",
        }[key],
    )

    finish_shared_audio(
        editor,
        "litterbox",
        "clip.mp3",
        "https://litterbox.catbox.moe/abc123/clip.mp3",
        deps,
    )

    assert statuses == [("Uploaded clip.mp3: https://litterbox.catbox.moe/abc123/clip.mp3", "warning")]
```

Add to `tests/test_editor_bridge_commands.py`:

```python
def test_bridge_routes_share_payload_to_editor_sharing(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._share_current_audio_file",
        lambda _editor, payload: called.update(editor=_editor, payload=payload),
    )

    _handle_bridge_command(
        editor,
        '{"command":"aqe:share","fieldOrd":0,"shareTarget":"catbox"}',
    )

    assert called["editor"] is editor
    assert called["payload"].share_target == "catbox"
```

- [ ] **Step 2: Run the focused tests to confirm the editor adapter is missing**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_sharing.py tests/test_editor_bridge_commands.py
```

Expected: FAIL because `editor_sharing.py` does not exist and bridge routing has no share branch.

- [ ] **Step 3: Implement the editor sharing adapter and wire it through the callback facade**

Create `addon/anki_audio_quick_editor/editor_sharing.py`:

```python
"""Editor adapter for Catbox/Litterbox sharing."""

from __future__ import annotations

import logging
import threading
from typing import Any

from .diagnostics_runtime import capture_exception, new_operation_id
from .editor_actions import EditorCommandPayload, decode_editor_command_payload

logger = logging.getLogger(__name__)


def share_current_audio_file(
    editor: Any,
    command: str | EditorCommandPayload,
    deps: Any,
) -> None:
    """Upload the current editor audio file and copy the resulting URL."""
    payload = decode_editor_command_payload(command)
    if payload.share_target not in {"catbox", "litterbox"}:
        deps.set_busy(editor, False)
        deps.eval_status(editor, deps.t("editor.status.share_invalid_target"), kind="error")
        return

    session, media_path = deps.current_media_path(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return

    operation_id = new_operation_id("editor-share")
    message_key = (
        "editor.status.sharing_litterbox"
        if payload.share_target == "litterbox"
        else "editor.status.sharing_catbox"
    )
    deps.set_busy(editor, True, deps.t(message_key), payload.command)

    def _run() -> None:
        try:
            url = deps.upload_file(media_path, payload.share_target)
            deps.main(
                editor,
                lambda: deps.finish_shared_audio(
                    editor,
                    payload.share_target,
                    media_path.name,
                    url,
                ),
            )
        except Exception as exc:  # pragma: no cover - worker boundary
            capture_exception(
                "editor.worker.share",
                exc,
                operation="editor.share",
                operation_id=operation_id,
                user_message=str(exc),
                context={"filename": media_path.name, "share_target": payload.share_target},
                log=logger,
            )
            deps.main(
                editor,
                lambda: deps.share_failed(editor, str(exc)),
            )

    threading.Thread(target=_run, daemon=True).start()


def finish_shared_audio(
    editor: Any,
    share_target: str,
    filename: str,
    url: str,
    deps: Any,
) -> None:
    """Finalize a successful upload on the main thread."""
    from aqt.qt import QApplication

    clipboard = QApplication.clipboard()
    if clipboard is None:
        deps.logger.warning("share_current_audio_file: clipboard unavailable")
        deps.eval_status(
            editor,
            deps.t("editor.status.share_clipboard_unavailable", {"filename": filename, "url": url}),
            kind="warning",
        )
        deps.set_busy(editor, False)
        return

    clipboard.setText(url)
    success_key = (
        "editor.status.shared_litterbox"
        if share_target == "litterbox"
        else "editor.status.shared_catbox"
    )
    deps.eval_status(editor, deps.t(success_key, {"filename": filename}), kind="info")
    deps.set_busy(editor, False)


def share_failed(editor: Any, error: str, deps: Any) -> None:
    """Clear the busy state after a failed upload."""
    deps.set_busy(editor, False)
    deps.eval_status(editor, deps.t("editor.status.share_failed", {"error": error}), kind="error")
```

Modify `addon/anki_audio_quick_editor/editor_dependencies.py`:

```python
def share_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime
    from .file_sharing import upload_file
    from .i18n import t

    return SimpleNamespace(
        current_media_path=editor_runtime.current_media_path,
        eval_status=frontend_callbacks.eval_status,
        finish_shared_audio=callbacks.finish_shared_audio,
        is_busy=editor_runtime.is_busy,
        logger=logging.getLogger("anki_audio_quick_editor.editor_sharing"),
        main=frontend_callbacks.main,
        set_busy=frontend_callbacks.set_busy,
        share_failed=callbacks.share_failed,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        t=t,
        upload_file=upload_file,
    )
```

Add the missing import at the top of `editor_dependencies.py`:

```python
import logging
```

Modify `addon/anki_audio_quick_editor/editor_callbacks.py`:

```python
from . import (
    editor_analysis,
    editor_bridge,
    editor_dependencies,
    editor_frontend_callbacks,
    editor_history,
    editor_playback,
    editor_processing,
    editor_region_delete,
    editor_runtime,
    editor_settings_actions,
    editor_sharing,
    editor_split_defaults,
)
```

Add a dependency builder:

```python
def _share_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.share_deps)
```

Publish the wrapped helpers:

```python
_share_current_audio_file = _with_deps(editor_sharing.share_current_audio_file, _share_deps)
_finish_shared_audio = _with_deps(editor_sharing.finish_shared_audio, _share_deps)
_share_failed = _with_deps(editor_sharing.share_failed, _share_deps)
```

Modify `addon/anki_audio_quick_editor/editor_integration.py`:

```python
_share_current_audio_file = editor_callbacks._share_current_audio_file
_finish_shared_audio = editor_callbacks._finish_shared_audio
_share_failed = editor_callbacks._share_failed
```

Modify `addon/anki_audio_quick_editor/editor_dependencies.py` bridge deps:

```python
        share_current_audio_file=callbacks.share_current_audio_file,
```

Modify `addon/anki_audio_quick_editor/editor_bridge.py`:

```python
from .editor_actions import (
    CMD_ANALYZE_FIELD,
    CMD_COMMAND_PAYLOAD,
    CMD_CONVERT,
    CMD_DELETE_REST,
    CMD_DELETE_SELECTION,
    CMD_DENOISE_STANDARD,
    CMD_DPDFNET,
    CMD_PITCH_HUM,
    CMD_REDO,
    CMD_RNNOISE,
    CMD_SAVE_SPLIT_DEFAULTS,
    CMD_SETTINGS,
    CMD_SHARE,
    CMD_VOICE_ONLY,
    EditorCommandPayload,
    decode_editor_command_payload,
)
```

Add the share branch before the generic handler map:

```python
    if payload.command == CMD_SHARE:
        deps.share_current_audio_file(editor, payload)
        return True
```

- [ ] **Step 4: Register the new module in architecture contracts**

Modify `tests/test_architecture/contract_editor.py`:

```python
    "editor_sharing": contract(
        "editor_sharing",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("diagnostics_runtime", "editor_actions"),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.THREAD_SPAWN,
            SideEffect.WEB_EVAL,
        ),
        allow_any_anki_imports=True,
    ),
```

Expand the `editor_dependencies` contract so `share_deps()` can legally import the upload boundary and translator:

```python
    "editor_dependencies": contract(
        "editor_dependencies",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_processor",
            "editor_media",
            "editor_runtime",
            "file_sharing",
            "i18n",
            "prosody_cache",
            "support",
        ),
    ),
```

Allow `editor_callbacks` and `editor_integration` to depend on `editor_sharing`:

```python
            "editor_sharing",
```

Modify `tests/test_architecture/test_rule21_broad_exception_allowlist.py`:

```python
    BroadExceptionAllowance(
        "editor_sharing",
        "share_current_audio_file._run",
        1,
        "Background upload worker boundary reports Catbox/Litterbox failures on the main thread.",
    ),
```

Run the architecture-focused tests:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule3_editor_bridge_contract.py tests/test_architecture/test_rule15_all_modules_have_contracts.py tests/test_architecture/test_rule18_contract_driven_side_effect_policy.py tests/test_architecture/test_rule21_broad_exception_allowlist.py
```

Expected: PASS after the module contract and allowlist are added.

- [ ] **Step 5: Re-run the Python integration tests and commit**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_sharing.py tests/test_editor_bridge_commands.py tests/test_editor_actions.py
```

Expected: PASS.

Commit:

```bash
git add addon/anki_audio_quick_editor/editor_sharing.py addon/anki_audio_quick_editor/editor_bridge.py addon/anki_audio_quick_editor/editor_callbacks.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_integration.py tests/test_editor_sharing.py tests/test_editor_bridge_commands.py tests/test_architecture/contract_editor.py tests/test_architecture/test_rule21_broad_exception_allowlist.py
git commit -m "feat: wire editor audio sharing"
```

---

### Task 5: Add End-To-End Coverage And Run The Full Quality Gates

**Files:**
- Create: `e2e/test_editor_share_workflow.py`

- [ ] **Step 1: Write the failing e2e coverage with a fake uploader boundary**

Create `e2e/test_editor_share_workflow.py`:

```python
"""E2E tests for editor audio sharing."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _three_audio_field_note,
)
from e2e.helpers import click_selector, generate_tone, wait_for_condition, wait_for_selector
from e2e.test_editor_processing_split_buttons_workflow import _split_menu_selector


def _share_preset_selector(target: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-split-{ord_}-share-preset-{target}"]'


def test_share_button_uploads_to_catbox_then_litterbox_without_mutating_note(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    from aqt.qt import QApplication
    from anki_audio_quick_editor import file_sharing

    uploads: list[tuple[str, str]] = []

    def fake_upload(path: Path, target: str, timeout_s: float = 60.0) -> str:
        uploads.append((path.name, target))
        if target == "litterbox":
            return "https://litterbox.catbox.moe/abc123/clip.mp3"
        return "https://files.catbox.moe/share123.mp3"

    monkeypatch.setattr(file_sharing, "upload_file", fake_upload)

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_share_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    note = _basic_audio_note(anki_mw, source.name)
    original_field = note.fields[0]
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:share"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:share"), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == "https://files.catbox.moe/share123.mp3",
            timeout=5.0,
            message="Catbox share did not copy the expected URL",
        )

        click_selector(editor.web, _split_menu_selector("aqe:share"), timeout=5.0)
        click_selector(editor.web, _share_preset_selector("litterbox"), timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:share"), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == "https://litterbox.catbox.moe/abc123/clip.mp3",
            timeout=5.0,
            message="Litterbox share did not copy the expected URL",
        )

        assert uploads == [
            (source.name, "catbox"),
            (source.name, "litterbox"),
        ]
        assert note.fields[0] == original_field
    finally:
        editor.set_note(None)
        parent.close()


def test_share_target_state_is_isolated_per_field(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    from aqt.qt import QApplication
    from anki_audio_quick_editor import file_sharing

    uploads: list[tuple[str, str]] = []

    monkeypatch.setattr(
        file_sharing,
        "upload_file",
        lambda path, target, timeout_s=60.0: uploads.append((path.name, target)) or f"https://example.invalid/{target}/{path.name}",
    )

    media_dir = Path(anki_mw.col.media.dir())
    one = media_dir / "editor_share_one.wav"
    two = media_dir / "editor_share_two.wav"
    three = media_dir / "editor_share_three.wav"
    generate_tone(ffmpeg_config, one, duration_s=0.5)
    generate_tone(ffmpeg_config, two, duration_s=0.5)
    generate_tone(ffmpeg_config, three, duration_s=0.5)
    note = _three_audio_field_note(anki_mw, (one.name, two.name, three.name))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:share", 0), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:share", 0), timeout=5.0)
        click_selector(editor.web, _share_preset_selector("litterbox", 0), timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:share", 0), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == f"https://example.invalid/litterbox/{one.name}",
            timeout=5.0,
            message="Field 0 did not retain the Litterbox selection",
        )

        click_selector(editor.web, _button_selector("aqe:share", 1), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == f"https://example.invalid/catbox/{two.name}",
            timeout=5.0,
            message="Field 1 should still use the default Catbox target",
        )

        assert uploads == [
            (one.name, "litterbox"),
            (two.name, "catbox"),
        ]
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 2: Run the focused e2e tests to confirm the new workflow is not implemented**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_share_workflow.py
```

Expected: FAIL because the share button, payload route, and clipboard-copy behavior are not fully wired.

- [ ] **Step 3: Keep the e2e toolbar default fixture aligned with the new command**

Confirm `e2e/editor_note_helpers.py` contains:

```python
DEFAULT_VISIBLE_EDITOR_BUTTONS = (
    "aqe:play",
    "aqe:analyze",
    "aqe:show-file",
    "aqe:share",
    "aqe:convert",
    "aqe:remove-pauses",
    "aqe:denoise-standard",
    "aqe:pitch-hum",
    "aqe:slower",
    "aqe:faster",
    "aqe:volume-down",
    "aqe:volume-up",
    "aqe:undo",
    "aqe:redo",
    "aqe:settings",
)
```

- [ ] **Step 4: Run the focused e2e workflow, then the full quality gates**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_share_workflow.py
python3 scripts/dev.py config-schema
python3 scripts/dev.py test-svelte
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

Expected:

- Focused e2e share workflow passes.
- `config-schema`, `test-svelte`, and `check` pass.
- Final `python3 scripts/dev.py test-e2e` passes. The feature is not complete until this passes.

- [ ] **Step 5: Commit the end-to-end coverage**

Commit:

```bash
git add e2e/test_editor_share_workflow.py
git commit -m "test: cover editor audio sharing"
```

---

## Self-Review Checklist

- `aqe:share` is present in Python bridge registration, toolbar metadata, default visible-button lists, and migration logic.
- Share uses the existing `aqe:command-payload` path and does not add a new bridge protocol.
- Litterbox retention is fixed to `72h` and not persisted in config.
- Share does not mutate note HTML, media references, undo history, or shared audio operations.
- Only `file_sharing.py` owns HTTP upload details.
- Only `editor_sharing.py` owns share-specific clipboard and status coordination.
- No automated tests call live Catbox or Litterbox services.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-22-editor-audio-sharing.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
