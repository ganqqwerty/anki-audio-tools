# Settings Buttons And Diagnostics Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Settings so button configuration is grouped per command in an editor-styled `Buttons` section, move logging toggles to `Diagnostics`, remove the `deep_filter_path` setting, and make `ffmpeg_path` default to a real platform-specific value.

**Architecture:** Keep the existing flat config model and recompose the Settings UI around per-button cards instead of a separate visibility matrix. Add one backend source of truth for platform ffmpeg defaults, thread that through config defaults and initial state, and remove `deep_filter_path` only from the supported config/settings surface while leaving non-settings runtime discovery behavior intact.

**Tech Stack:** Python 3.13, Anki add-on runtime, JSON Schema, generated Python/TypeScript contracts, Svelte 5, Vitest, pytest, repository task runner `scripts/dev.py`

---

## File Map

- `addon/anki_audio_quick_editor/config.json`
  Canonical persisted config defaults shipped with the add-on.
- `addon/anki_audio_quick_editor/config.schema.json`
  Supported config contract; source for generated Python/TypeScript config types.
- `addon/anki_audio_quick_editor/config_migration.py`
  Still stamps versions and normalizes supported settings defaults; must stop treating `deep_filter_path` as supported.
- `addon/anki_audio_quick_editor/settings_state.py`
  Builds the settings initial-state payload consumed by the webview.
- `addon/anki_audio_quick_editor/diagnostics.py`
  Settings health-check path that currently honors configured `deep_filter_path`.
- `addon/anki_audio_quick_editor/support.py`
  Support-report rendering that currently includes DeepFilterNet config-path fields.
- `addon/anki_audio_quick_editor/audio_state.py`
  Runtime config dataclass created from settings config; currently still exposes `deep_filter_path`.
- `settings_ui/src/settings/GeneralSettingsPanel.svelte`
  Current mixed settings form that holds general defaults, paths, and toolbar visibility.
- `settings_ui/src/settings/DiagnosticsPanel.svelte`
  Current diagnostics action panel; target home for logging toggles and ffmpeg path field.
- `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`
  Current button visibility grid; likely replaced or heavily reshaped into per-button cards.
- `settings_ui/src/settings/settings-state.ts`
  Frontend fallback config defaults for the settings dialog.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`
  Source of button ordering, labels, and default button modes.
- `settings_ui/src/lib/i18n.ts`
  UI copy for settings labels and help text.
- `tests/test_settings_initial_state.py`
  Python coverage for `window.__INITIAL_STATE__`.
- `tests/test_settings_state.py`
  Python coverage for import-safe settings payload shaping.
- `tests/test_settings_commands_diagnostics.py`
  Diagnostics command coverage, including DeepFilterNet health behavior.
- `tests/test_settings_commands_support_report.py`
  Support report coverage for surfaced settings/runtime fields.
- `tests/test_config_migration.py`
  Config default/normalization coverage; even with “no migration” it still validates supported-key normalization.
- `settings_ui/tests/*.test.ts`
  Frontend settings and editor-related Vitest coverage; add/update tests here for UI structure and defaults.

### Task 1: Lock backend defaults and supported config surface

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config_migration.py`
- Modify: `addon/anki_audio_quick_editor/audio_state.py`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Test: `tests/test_settings_initial_state.py`
- Test: `tests/test_settings_state.py`
- Test: `tests/test_config_migration.py`
- Test: `tests/test_audio_state.py`

- [ ] **Step 1: Write failing backend default tests**

```python
def test_initial_state_uses_new_button_defaults() -> None:
    state = json.loads(build_initial_state(_full_config()))
    config = state["config"]

    assert config["visible_editor_buttons"] == [
        "aqe:play",
        "aqe:analyze",
        "aqe:show-file",
        "aqe:share",
        "aqe:remove-pauses",
        "aqe:denoise-standard",
        "aqe:slower",
        "aqe:faster",
        "aqe:undo",
        "aqe:redo",
        "aqe:settings",
    ]
    assert config["editor_button_modes"]["aqe:play"] == "icon"
    assert config["editor_button_modes"]["aqe:remove-pauses"] == "text"
    assert "deep_filter_path" not in config


def test_audio_processing_config_ignores_removed_deep_filter_setting() -> None:
    config = AudioProcessingConfig.from_config({"ffmpeg_path": "/opt/homebrew/bin/ffmpeg"})

    assert config.ffmpeg_path == "/opt/homebrew/bin/ffmpeg"
    assert not hasattr(config, "deep_filter_path")
```

- [ ] **Step 2: Run the targeted Python tests and confirm they fail**

Run:

```bash
pytest tests/test_settings_initial_state.py tests/test_settings_state.py tests/test_config_migration.py tests/test_audio_state.py -q
```

Expected:

```text
FAIL tests/test_settings_initial_state.py::test_initial_state_uses_new_button_defaults
FAIL tests/test_audio_state.py::test_audio_processing_config_ignores_removed_deep_filter_setting
```

- [ ] **Step 3: Implement the canonical defaults and remove the supported key**

```python
# addon/anki_audio_quick_editor/audio_state.py
@dataclass(frozen=True)
class AudioProcessingConfig:
    ffmpeg_path: str = ""
    deep_filter_post_filter: bool = True
    dpdfnet_attn_limit_db: float = 12.0
    denoise_algorithm: str = "standard"
    pitch_hum_mode: str = "direct"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "AudioProcessingConfig":
        return cls(
            ffmpeg_path=str(config.get("ffmpeg_path", cls.ffmpeg_path)),
            deep_filter_post_filter=bool(config.get("deep_filter_post_filter", cls.deep_filter_post_filter)),
            dpdfnet_attn_limit_db=float(config.get("dpdfnet_attn_limit_db", cls.dpdfnet_attn_limit_db)),
            denoise_algorithm=str(config.get("denoise_algorithm", cls.denoise_algorithm)),
            pitch_hum_mode=str(config.get("pitch_hum_mode", cls.pitch_hum_mode)),
        )
```

```ts
// settings_ui/src/lib/editor-toolbar-buttons.ts
export const DEFAULT_VISIBLE_EDITOR_BUTTONS = [
  "aqe:play",
  "aqe:analyze",
  "aqe:show-file",
  "aqe:share",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:slower",
  "aqe:faster",
  "aqe:undo",
  "aqe:redo",
  "aqe:settings",
] as const;

export const DEFAULT_EDITOR_BUTTON_MODES = {
  "aqe:play": EditorButtonMode.Icon,
  "aqe:analyze": EditorButtonMode.Icon,
  "aqe:show-file": EditorButtonMode.Icon,
  "aqe:share": EditorButtonMode.Icon,
  "aqe:convert": EditorButtonMode.Text,
  "aqe:remove-pauses": EditorButtonMode.Text,
  "aqe:denoise-standard": EditorButtonMode.Text,
  "aqe:pitch-hum": EditorButtonMode.Text,
  "aqe:slower": EditorButtonMode.Icon,
  "aqe:faster": EditorButtonMode.Icon,
  "aqe:volume-down": EditorButtonMode.Icon,
  "aqe:volume-up": EditorButtonMode.Icon,
  "aqe:undo": EditorButtonMode.Icon,
  "aqe:redo": EditorButtonMode.Icon,
  "aqe:settings": EditorButtonMode.Icon,
} as const;
```

- [ ] **Step 4: Update config/schema/fallback fixtures to match**

```json
// addon/anki_audio_quick_editor/config.json
{
  "_config_version": 20,
  "visible_editor_buttons": [
    "aqe:play",
    "aqe:analyze",
    "aqe:show-file",
    "aqe:share",
    "aqe:remove-pauses",
    "aqe:denoise-standard",
    "aqe:slower",
    "aqe:faster",
    "aqe:undo",
    "aqe:redo",
    "aqe:settings"
  ],
  "editor_button_modes": {
    "aqe:play": "icon",
    "aqe:analyze": "icon",
    "aqe:show-file": "icon",
    "aqe:share": "icon",
    "aqe:convert": "text",
    "aqe:remove-pauses": "text",
    "aqe:denoise-standard": "text",
    "aqe:pitch-hum": "text",
    "aqe:slower": "icon",
    "aqe:faster": "icon",
    "aqe:volume-down": "icon",
    "aqe:volume-up": "icon",
    "aqe:undo": "icon",
    "aqe:redo": "icon",
    "aqe:settings": "icon"
  },
  "ffmpeg_path": "/opt/homebrew/bin/ffmpeg"
}
```

```json
// addon/anki_audio_quick_editor/config.schema.json
"required": [
  "_config_version",
  "enabled",
  "debug_logging",
  "show_ffmpeg_commands",
  "repeat_playback_by_default",
  "repeat_pause_seconds",
  "show_graph_by_default",
  "visible_editor_buttons",
  "editor_button_modes",
  "graph_voice_range",
  "graph_recording_condition",
  "graph_smoothness",
  "graph_connect_short_dropouts_ms",
  "graph_voice_lock",
  "speed_step",
  "min_speed",
  "max_speed",
  "volume_step_db",
  "min_volume_db",
  "max_volume_db",
  "internal_pause_silence_threshold_db",
  "internal_pause_threshold_ms",
  "internal_pause_target_gap_ms",
  "pause_aggressiveness",
  "output_format",
  "ffmpeg_path",
  "deep_filter_post_filter",
  "dpdfnet_attn_limit_db",
  "denoise_algorithm",
  "pitch_hum_mode"
]
```

- [ ] **Step 5: Re-run targeted Python tests**

Run:

```bash
pytest tests/test_settings_initial_state.py tests/test_settings_state.py tests/test_config_migration.py tests/test_audio_state.py -q
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit the backend-defaults slice**

```bash
git add addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config_migration.py addon/anki_audio_quick_editor/audio_state.py settings_ui/src/settings/settings-state.ts settings_ui/src/lib/editor-toolbar-buttons.ts tests/test_settings_initial_state.py tests/test_settings_state.py tests/test_config_migration.py tests/test_audio_state.py
git commit -m "refactor: update settings defaults for editor buttons"
```

### Task 2: Add a single platform-aware ffmpeg default source and thread it through settings state

**Files:**
- Create: `addon/anki_audio_quick_editor/ffmpeg_defaults.py`
- Modify: `addon/anki_audio_quick_editor/settings_state.py`
- Modify: `addon/anki_audio_quick_editor/settings/initial_state.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`

- [ ] **Step 1: Write failing tests for platform-aware defaults**

```python
def test_build_initial_state_payload_uses_platform_ffmpeg_default_when_missing(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.ffmpeg_defaults.default_ffmpeg_path", lambda: "/opt/homebrew/bin/ffmpeg")

    payload = build_initial_state_payload(
        {"enabled": True},
        version="1.0",
        addon_id="aqe",
        addon_dir="/tmp/addon",
        collection_available=True,
        locale="en",
        direction="ltr",
        messages={},
    )

    assert payload["config"]["ffmpeg_path"] == "/opt/homebrew/bin/ffmpeg"
```

- [ ] **Step 2: Run the focused tests and confirm the missing helper path fails**

Run:

```bash
pytest tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

Expected:

```text
FAIL tests/test_settings_state.py::test_build_initial_state_payload_uses_platform_ffmpeg_default_when_missing
```

- [ ] **Step 3: Implement the ffmpeg default helper**

```python
# addon/anki_audio_quick_editor/ffmpeg_defaults.py
from __future__ import annotations

import platform


def default_ffmpeg_path() -> str:
    system = platform.system()
    if system == "Darwin":
        return "/opt/homebrew/bin/ffmpeg"
    if system == "Windows":
        return "ffmpeg.exe"
    return "ffmpeg"
```

- [ ] **Step 4: Normalize settings payload config through the helper**

```python
# addon/anki_audio_quick_editor/settings_state.py
from .ffmpeg_defaults import default_ffmpeg_path


def _settings_config_payload(config: dict[str, Any]) -> dict[str, Any]:
    payload = dict(config)
    payload.setdefault("ffmpeg_path", default_ffmpeg_path())
    if not payload["ffmpeg_path"]:
        payload["ffmpeg_path"] = default_ffmpeg_path()
    payload.pop("deep_filter_path", None)
    return payload


def build_initial_state_payload(
    config: dict[str, Any],
    *,
    version: str,
    addon_id: str,
    addon_dir: str,
    collection_available: bool,
    locale: str,
    direction: str,
    messages: dict[str, str],
) -> dict[str, Any]:
    return {
        "config": _settings_config_payload(config),
        "version": version,
        "addon_dir": addon_dir,
        "log_file_path": os.path.join(addon_dir, "anki_audio_quick_editor.log"),
        "locale": locale,
        "direction": direction,
        "messages": messages,
        "diagnostics": {
            "addon_id": addon_id,
            "collection_available": collection_available,
        },
    }
```

- [ ] **Step 5: Re-run the focused tests**

Run:

```bash
pytest tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit the ffmpeg-default plumbing**

```bash
git add addon/anki_audio_quick_editor/ffmpeg_defaults.py addon/anki_audio_quick_editor/settings_state.py addon/anki_audio_quick_editor/settings/initial_state.py tests/test_settings_initial_state.py tests/test_settings_state.py
git commit -m "feat: prefill ffmpeg path defaults by platform"
```

### Task 3: Move diagnostics toggles and remove settings-only DeepFilterNet path UI

**Files:**
- Modify: `settings_ui/src/settings/GeneralSettingsPanel.svelte`
- Modify: `settings_ui/src/settings/DiagnosticsPanel.svelte`
- Modify: `settings_ui/src/lib/i18n.ts`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Test: `settings_ui/tests/settings-app.test.ts`
- Test: `tests/test_settings_commands_diagnostics.py`

- [ ] **Step 1: Write failing UI tests for diagnostics-tab ownership**

```ts
it("shows debug toggles on the diagnostics tab instead of the general tab", async () => {
  render(SettingsApp, { initialState: makeInitialState() });

  expect(screen.queryByLabelText("Enable debug logging")).not.toBeNull();
  await user.click(screen.getByTestId("settings-tab-diagnostics"));
  expect(screen.getByLabelText("Enable debug logging")).toBeVisible();
  expect(screen.getByLabelText("Show ffmpeg commands while processing")).toBeVisible();
});

it("does not render a DeepFilterNet path field", async () => {
  render(SettingsApp, { initialState: makeInitialState() });
  expect(screen.queryByLabelText("DeepFilterNet path")).toBeNull();
});
```

- [ ] **Step 2: Run the frontend test to confirm the current layout fails**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings-app.test.ts
```

Expected:

```text
FAIL settings_ui/tests/settings-app.test.ts > shows debug toggles on the diagnostics tab instead of the general tab
FAIL settings_ui/tests/settings-app.test.ts > does not render a DeepFilterNet path field
```

- [ ] **Step 3: Move the fields to Diagnostics and delete the removed field copy**

```svelte
<!-- settings_ui/src/settings/DiagnosticsPanel.svelte -->
<label class="settings-toggle">
  <input type="checkbox" bind:checked={config.debug_logging} />
  <span class="settings-label-text">{t("settings.debug_logging")}</span>
</label>

<label class="settings-toggle">
  <input type="checkbox" bind:checked={config.show_ffmpeg_commands} />
  <span class="settings-label-text">{t("settings.show_ffmpeg_commands")}</span>
</label>

<label class="settings-field">
  <span>{t("settings.ffmpeg_path")}</span>
  <input class="settings-input" type="text" bind:value={config.ffmpeg_path} />
</label>
```

```svelte
<!-- settings_ui/src/settings/GeneralSettingsPanel.svelte -->
<!-- remove debug_logging, show_ffmpeg_commands, ffmpeg_path, deep_filter_path from the general panel -->
```

- [ ] **Step 4: Update copy to reflect persisted defaults instead of placeholders**

```ts
// settings_ui/src/lib/i18n.ts
"settings.show_ffmpeg_commands": "Show ffmpeg commands while processing",
"settings.ffmpeg_path.help": "Prefilled with a platform default. Change it if your ffmpeg binary lives elsewhere.",
```

- [ ] **Step 5: Re-run the focused frontend test**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings-app.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit the diagnostics-tab slice**

```bash
git add settings_ui/src/settings/GeneralSettingsPanel.svelte settings_ui/src/settings/DiagnosticsPanel.svelte settings_ui/src/lib/i18n.ts settings_ui/src/settings/settings-state.ts settings_ui/tests/settings-app.test.ts tests/test_settings_commands_diagnostics.py
git commit -m "refactor: move diagnostics settings into diagnostics tab"
```

### Task 4: Replace the toolbar visibility matrix with editor-styled per-button cards

**Files:**
- Modify: `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`
- Create: `settings_ui/src/settings/ButtonSettingsCard.svelte`
- Modify: `settings_ui/src/settings/GeneralSettingsPanel.svelte`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Test: `settings_ui/tests/settings-app.test.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`

- [ ] **Step 1: Write failing frontend tests for grouped per-button cards**

```ts
it("renders a denoise card with display controls above denoise defaults", async () => {
  render(SettingsApp, { initialState: makeInitialState() });

  const denoiseCard = screen.getByTestId("button-settings-aqe-denoise-standard");
  expect(within(denoiseCard).getByText("Denoise")).toBeVisible();
  expect(within(denoiseCard).getByRole("button", { name: "Shown" })).toBeVisible();
  expect(within(denoiseCard).getByRole("button", { name: "Text only" })).toBeVisible();
  expect(within(denoiseCard).getByLabelText("Default denoise algorithm")).toBeVisible();
  expect(within(denoiseCard).getByLabelText("DPDFNet aggressiveness")).toBeVisible();
});

it("renders an undo card without unrelated extra settings", async () => {
  const undoCard = screen.getByTestId("button-settings-aqe-undo");
  expect(within(undoCard).queryByLabelText("Default denoise algorithm")).toBeNull();
});
```

- [ ] **Step 2: Run the focused test and confirm the current matrix layout fails**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings-app.test.ts
```

Expected:

```text
FAIL settings_ui/tests/settings-app.test.ts > renders a denoise card with display controls above denoise defaults
```

- [ ] **Step 3: Create a reusable per-button card component**

```svelte
<!-- settings_ui/src/settings/ButtonSettingsCard.svelte -->
<script lang="ts">
  export let title: string;
  export let icon: CommandIconName;
  export let visible: boolean;
  export let mode: EditorButtonDisplayMode;
</script>

<section class="button-settings-card" data-testid={testId}>
  <header class="button-settings-header">
    <CommandIcon className="button-settings-icon" {icon} />
    <h4>{title}</h4>
  </header>

  <div class="button-settings-pills">
    <!-- shown/hidden segmented buttons -->
  </div>

  <div class="button-settings-pills">
    <!-- icon-only/text-only segmented buttons -->
  </div>

  <slot />
</section>
```

- [ ] **Step 4: Recompose toolbar settings around one card per command**

```svelte
<!-- settings_ui/src/settings/ToolbarVisibilitySettings.svelte -->
<ButtonSettingsCard
  title={button.label}
  icon={button.icon}
  visible={isVisible(button.command)}
  mode={displayMode(button.command)}
  testId={`button-settings-${COMMAND_SLUGS[button.command]}`}
>
  {#if button.command === "aqe:denoise-standard"}
    <label class="settings-field">
      <span>{t("settings.denoise_algorithm")}</span>
      <select class="settings-select" bind:value={config.denoise_algorithm}>
        <option value="standard">{t("settings.denoise_algorithm.standard")}</option>
        <option value="rnnoise">{t("settings.denoise_algorithm.rnnoise")}</option>
        <option value="dpdfnet">{t("settings.denoise_algorithm.dpdfnet")}</option>
        <option value="voice_only">{t("settings.denoise_algorithm.voice_only")}</option>
      </select>
    </label>
    <label class="settings-field">
      <span>{t("settings.dpdfnet_attn_limit_db")}</span>
      <select class="settings-select" bind:value={config.dpdfnet_attn_limit_db}>
        <option value={6.0}>{formatDpdfnetAggressiveness(6.0)}</option>
        <option value={12.0}>{formatDpdfnetAggressiveness(12.0)}</option>
        <option value={18.0}>{formatDpdfnetAggressiveness(18.0)}</option>
      </select>
    </label>
  {/if}
</ButtonSettingsCard>
```

- [ ] **Step 5: Move button-owned defaults out of the generic grids into the matching cards**

```svelte
<!-- settings_ui/src/settings/GeneralSettingsPanel.svelte -->
<section class="settings-section">
  <ToolbarVisibilitySettings bind:config />
</section>
```

- [ ] **Step 6: Re-run focused frontend tests**

Run:

```bash
python3 scripts/dev.py test-svelte -- --run settings-app.test.ts
python3 scripts/dev.py test-svelte -- --run editor-inline.integration.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 7: Commit the buttons-section redesign**

```bash
git add settings_ui/src/settings/ToolbarVisibilitySettings.svelte settings_ui/src/settings/ButtonSettingsCard.svelte settings_ui/src/settings/GeneralSettingsPanel.svelte settings_ui/src/lib/editor-toolbar-buttons.ts settings_ui/tests/settings-app.test.ts settings_ui/tests/editor-inline.integration.test.ts
git commit -m "feat: group editor button settings by command"
```

### Task 5: Remove settings-surface DeepFilterNet path assumptions from diagnostics and support output

**Files:**
- Modify: `addon/anki_audio_quick_editor/diagnostics.py`
- Modify: `addon/anki_audio_quick_editor/support.py`
- Modify: `tests/test_diagnostics.py`
- Modify: `tests/test_settings_commands_diagnostics.py`
- Modify: `tests/test_settings_commands_support_report.py`
- Modify: `tests/settings_command_fixtures.py`

- [ ] **Step 1: Write failing diagnostics/support tests for the removed setting**

```python
def test_async_health_check_reports_bundled_or_path_source_without_config_override() -> None:
    payload = json.dumps({"id": "job-1", "op": "health_check", "payload": {"config": _full_config()}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch("anki_audio_quick_editor.audio_processor.find_deep_filter", return_value=Path("/addon/bin/deep-filter")),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "deep-filter 0.5.6\n"
        run.return_value.stderr = ""
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["deep_filter"]["source"] == "bundled"
```

```python
def test_support_report_omits_deep_filter_config_path_label() -> None:
    report = build_support_report(
        health_report={"deep_filter": {"available": True, "source": "bundled"}},
        config=_full_config(),
        log_path="/tmp/aqe.log",
        latest_incident=None,
    )
    assert "DeepFilterNet path" not in report
```

- [ ] **Step 2: Run the targeted Python tests and confirm they fail**

Run:

```bash
pytest tests/test_diagnostics.py tests/test_settings_commands_diagnostics.py tests/test_settings_commands_support_report.py -q
```

Expected:

```text
FAIL tests/test_settings_commands_diagnostics.py::test_async_health_check_reports_bundled_or_path_source_without_config_override
FAIL tests/test_settings_commands_support_report.py::test_support_report_omits_deep_filter_config_path_label
```

- [ ] **Step 3: Remove the settings override from diagnostics and support rendering**

```python
# addon/anki_audio_quick_editor/diagnostics.py
def build_deep_filter_health(config: dict[str, Any]) -> dict[str, Any]:
    from .audio_processor import _external_command_run_kwargs, find_deep_filter, tool_source_label

    try:
        deep_filter_path = find_deep_filter("")
    except Exception as exc:
        return {
            "available": False,
            "path": "",
            "source": "",
            "version": "",
            "error": str(exc),
        }

    source = tool_source_label(deep_filter_path, configured_path="")
    result = subprocess.run(
        [str(deep_filter_path), "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        **_external_command_run_kwargs(),
    )
    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(deep_filter_path),
        "source": source,
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "deep-filter --version failed.",
    }
```

```python
# addon/anki_audio_quick_editor/support.py
SETTINGS_FIELDS = (
    ("ffmpeg path", "ffmpeg_path"),
    ("DeepFilterNet post-filter", "deep_filter_post_filter"),
    ("DPDFNet aggressiveness", "dpdfnet_attn_limit_db"),
)
```

- [ ] **Step 4: Update shared settings fixtures to the new supported config**

```python
def _full_config() -> dict[str, object]:
    return {
        "_config_version": 20,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "repeat_pause_seconds": 0.0,
        "show_graph_by_default": False,
        "visible_editor_buttons": [
            "aqe:play",
            "aqe:analyze",
            "aqe:show-file",
            "aqe:share",
            "aqe:remove-pauses",
            "aqe:denoise-standard",
            "aqe:slower",
            "aqe:faster",
            "aqe:undo",
            "aqe:redo",
            "aqe:settings",
        ],
        "editor_button_modes": {
            "aqe:play": "icon",
            "aqe:analyze": "icon",
            "aqe:show-file": "icon",
            "aqe:share": "icon",
            "aqe:convert": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "icon",
            "aqe:faster": "icon",
            "aqe:volume-down": "icon",
            "aqe:volume-up": "icon",
            "aqe:undo": "icon",
            "aqe:redo": "icon",
            "aqe:settings": "icon",
        },
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "volume_step_db": 3.0,
        "min_volume_db": -24.0,
        "max_volume_db": 24.0,
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
        "pause_aggressiveness": "normal",
    }
```

- [ ] **Step 5: Re-run the focused diagnostics/support tests**

Run:

```bash
pytest tests/test_diagnostics.py tests/test_settings_commands_diagnostics.py tests/test_settings_commands_support_report.py -q
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit the diagnostics/support cleanup**

```bash
git add addon/anki_audio_quick_editor/diagnostics.py addon/anki_audio_quick_editor/support.py tests/test_diagnostics.py tests/test_settings_commands_diagnostics.py tests/test_settings_commands_support_report.py tests/settings_command_fixtures.py
git commit -m "refactor: drop deepfilternet path from settings surface"
```

### Task 6: Regenerate contracts and run the full verification gate

**Files:**
- Modify: `settings_ui/src/lib/generated/contracts.ts`
- Modify: `addon/anki_audio_quick_editor/contracts_generated.py`
- Verify: generated contracts, built webview bundles, repository test suites

- [ ] **Step 1: Regenerate contracts from the updated schema**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected:

```text
Generated TypeScript and Python contracts updated for config without deep_filter_path
```

- [ ] **Step 2: Validate schema and generated contract consistency**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
```

Expected:

```text
PASS
```

- [ ] **Step 3: Run unit and frontend verification**

Run:

```bash
python3 scripts/dev.py test
python3 scripts/dev.py test-svelte
```

Expected:

```text
PASS
```

- [ ] **Step 4: Run end-to-end coverage for the shipped settings dialog**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected:

```text
PASS
```

- [ ] **Step 5: Commit generated contracts and any final test-driven fixes**

```bash
git add addon/anki_audio_quick_editor/contracts_generated.py settings_ui/src/lib/generated/contracts.ts
git commit -m "chore: regenerate settings contracts"
```
