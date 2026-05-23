# Settings Check Media Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `Check Media` button to the Settings dialog Diagnostics tab that opens Anki's built-in media check and cleanup flow.

**Architecture:** Keep the frontend thin: add a diagnostics button that sends a dedicated `settings.check_media` bridge command. Handle that command in `addon/anki_audio_quick_editor/settings/commands.py` and call `aqt.mediacheck.check_media_db(mw)` so Anki's stock progress and cleanup UI remains the only feedback surface.

**Tech Stack:** Python 3.13 + pytest/e2e via `scripts/dev.py`, Svelte 5 + TypeScript + Vitest, Anki 25.09 runtime APIs.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/settings/commands.py` to dispatch `settings.check_media`.
- Modify `tests/test_settings_commands_diagnostics.py` to add the backend command test.
- Modify `settings_ui/src/lib/bridge.ts` to export a `settingsCheckMedia()` helper.
- Modify `settings_ui/src/settings/SettingsApp.svelte` to pass a diagnostics callback for the new action.
- Modify `settings_ui/src/settings/DiagnosticsPanel.svelte` to render the new button and `data-testid`.
- Modify `settings_ui/tests/bridge.test.ts` and `settings_ui/tests/app.test.ts` to cover the helper and Diagnostics tab click path.
- Modify `addon/anki_audio_quick_editor/locales/en.json`, `addon/anki_audio_quick_editor/locales/de.json`, and `addon/anki_audio_quick_editor/locales/zh_CN.json` to add `diagnostics.check_media`.
- Modify `e2e/test_settings_dialog.py` to verify the Diagnostics-tab button triggers the stock Anki media-check entry point.

### Task 1: Backend Settings Command Dispatch

**Files:**
- Modify: `tests/test_settings_commands_diagnostics.py`
- Modify: `addon/anki_audio_quick_editor/settings/commands.py`

- [ ] **Step 1: Add the failing backend test**

```python
def test_check_media_command_opens_anki_media_checker() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    with patch("aqt.mediacheck.check_media_db") as check_media_db:
        assert handle_settings_command(
            'bridge:{"command":"settings.check_media"}',
            eval_fn,
            dialog,
        ) is True

    check_media_db.assert_called_once()
    assert dialog.accepted is False
    assert dialog.rejected is False
```

- [ ] **Step 2: Run the focused backend test and confirm the red state**

Run: `python3 scripts/dev.py test tests/test_settings_commands_diagnostics.py`

Expected: FAIL because `handle_settings_command()` does not yet recognize `settings.check_media`.

- [ ] **Step 3: Implement the minimal backend dispatch**

```python
def handle_settings_command(
    cmd: str,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> bool:
    ...
    if command_name in {"settings.check_media", "settings_check_media"}:
        _handle_check_media()
        return True
    ...


def _handle_check_media() -> None:
    from aqt import mw
    from aqt.mediacheck import check_media_db

    check_media_db(mw)
```

Keep this path synchronous from the add-on's point of view. Do not route it through `settings.async`, and do not mutate `dialog`, `healthMessage`, or `diagnosticsMessage`.

- [ ] **Step 4: Re-run the focused backend test**

Run: `python3 scripts/dev.py test tests/test_settings_commands_diagnostics.py`

Expected: PASS with the new test green and no regressions in the existing diagnostics command tests.

- [ ] **Step 5: Run the Anki API compatibility gate**

Run: `python3 scripts/dev.py test-anki-api`

Expected: PASS, confirming the new `aqt.mediacheck.check_media_db` dependency is valid against the installed Anki runtime.

### Task 2: Diagnostics Button, Bridge Helper, And Localized Label

**Files:**
- Modify: `settings_ui/tests/bridge.test.ts`
- Modify: `settings_ui/tests/app.test.ts`
- Modify: `settings_ui/src/lib/bridge.ts`
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/src/settings/DiagnosticsPanel.svelte`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`

- [ ] **Step 1: Add the failing frontend tests**

In `settings_ui/tests/bridge.test.ts`, add:

```ts
import {
  copySupportReport,
  encodeBridgeCommand,
  registerCallbacks,
  sendAsyncCmd,
  sendBridgeCommand,
  settingsCancel,
  settingsCheckMedia,
  settingsResetDefaults,
  settingsSave,
} from "../src/lib/bridge.js";

...

  it("sends settings.check_media", () => {
    settingsCheckMedia();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.check_media"}');
  });
```

In `settings_ui/tests/app.test.ts`, add:

```ts
  it("opens Check Media from diagnostics", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Check Media" }));

    expect(bridgeEnvelopes()).toContainEqual({ command: "settings.check_media" });
  });
```

- [ ] **Step 2: Run the focused frontend tests and confirm the red state**

Run: `npm --prefix settings_ui test -- tests/bridge.test.ts tests/app.test.ts`

Expected: FAIL because `settingsCheckMedia()` does not exist yet and the Diagnostics tab does not render a `Check Media` button.

- [ ] **Step 3: Implement the frontend wiring and locale keys**

In `settings_ui/src/lib/bridge.ts`, add:

```ts
export function settingsCheckMedia(): void {
  sendBridgeEnvelope("settings.check_media");
}
```

In `settings_ui/src/settings/SettingsApp.svelte`, import and pass the callback:

```ts
  import {
    copySupportReport,
    registerCallbacks,
    settingsCancel,
    settingsCheckMedia,
    settingsResetDefaults,
    settingsSave,
  } from "$lib/bridge.js";
```

```svelte
      <DiagnosticsPanel
        initialState={initialState}
        healthMessage={healthMessage}
        healthReport={healthReport}
        healthProgress={healthProgress}
        diagnosticsMessage={diagnosticsMessage}
        onRunHealthCheck={runHealthCheck}
        onCheckMedia={settingsCheckMedia}
        onCopySupportReport={copyLatestSupportReport}
        onShowLogFile={showLogFile}
      />
```

In `settings_ui/src/settings/DiagnosticsPanel.svelte`, add the prop and button:

```ts
  let {
    initialState,
    healthMessage,
    healthReport,
    healthProgress,
    diagnosticsMessage,
    onRunHealthCheck,
    onCheckMedia,
    onCopySupportReport,
    onShowLogFile,
  }: {
    diagnosticsMessage: string;
    healthMessage: string;
    healthProgress: AsyncProgressPayload | null;
    healthReport: HealthReport | null;
    initialState: InitialState;
    onCopySupportReport: DiagnosticsAction;
    onCheckMedia: DiagnosticsAction;
    onRunHealthCheck: DiagnosticsAction;
    onShowLogFile: DiagnosticsAction;
  } = $props();
```

```svelte
    <button
      type="button"
      class="settings-button"
      data-testid="check-media"
      onclick={onCheckMedia}
    >
      {t("diagnostics.check_media")}
    </button>
```

Add locale keys:

```json
"diagnostics.check_media": "Check Media"
```

```json
"diagnostics.check_media": "Medien prüfen"
```

```json
"diagnostics.check_media": "检查媒体"
```

Keep the button a normal secondary diagnostics action. Do not add any new Svelte state for progress or result text.

- [ ] **Step 4: Re-run the focused frontend tests**

Run: `npm --prefix settings_ui test -- tests/bridge.test.ts tests/app.test.ts`

Expected: PASS with the new bridge helper covered and the Diagnostics tab click path sending `settings.check_media`.

### Task 3: E2E Coverage And Final Verification

**Files:**
- Modify: `e2e/test_settings_dialog.py`

- [ ] **Step 1: Add the focused e2e regression test**

Append a new test near the other Diagnostics-tab coverage:

```python
def test_diagnostics_can_open_check_media(anki_mw) -> None:
    dialog = _open_settings_dialog(anki_mw)

    with patch("aqt.mediacheck.check_media_db") as check_media_db:
        click_selector(dialog, '[data-testid="settings-tab-diagnostics"]', timeout=5.0)
        click_selector(dialog, '[data-testid="check-media"]', timeout=5.0)
        wait_for_condition(lambda: check_media_db.called, timeout=5.0)

    check_media_db.assert_called_once_with(anki_mw)
```

This test verifies the Settings dialog wiring only. It should not try to drive the native Anki media-check dialog itself.

- [ ] **Step 2: Run the focused e2e test**

Run: `python3 scripts/dev.py test-e2e e2e/test_settings_dialog.py`

Expected: PASS with the new Diagnostics-tab button covered through the real Anki runtime after the frontend bundle rebuild.

- [ ] **Step 3: Run the repo completion gates**

Run: `python3 scripts/dev.py check`

Expected: PASS, including frontend rebuild, lint, typecheck, architecture checks, Anki API compatibility, Python tests, coverage, and `test-svelte`.

Run: `python3 scripts/dev.py test-e2e`

Expected: PASS. Per repository rules, do not call the feature complete until the full e2e suite is green.

- [ ] **Step 4: Create the feature commit after verification**

Run:

```bash
git add addon/anki_audio_quick_editor/settings/commands.py \
  addon/anki_audio_quick_editor/locales/en.json \
  addon/anki_audio_quick_editor/locales/de.json \
  addon/anki_audio_quick_editor/locales/zh_CN.json \
  settings_ui/src/lib/bridge.ts \
  settings_ui/src/settings/SettingsApp.svelte \
  settings_ui/src/settings/DiagnosticsPanel.svelte \
  settings_ui/tests/bridge.test.ts \
  settings_ui/tests/app.test.ts \
  tests/test_settings_commands_diagnostics.py \
  e2e/test_settings_dialog.py
git commit -m "feat: add settings check media action"
```

Expected: one commit containing the backend dispatch, diagnostics button, localized label, and test coverage.
