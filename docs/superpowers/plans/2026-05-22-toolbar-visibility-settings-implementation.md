# Toolbar Visibility Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persisted settings control that lets users hide any top-level inline editor toolbar button, including Settings.

**Architecture:** Add `visible_editor_buttons` to schema-backed config, pass it through Python editor injection as `visibleEditorButtons`, and filter the Svelte editor toolbar by that list. Settings renders a toggleable copy of the toolbar from shared button metadata and saves the command list.

**Tech Stack:** Python 3.13 + pytest, JSON Schema + generated quicktype contracts, Svelte 5 + TypeScript + Vitest, Anki e2e through `scripts/dev.py`.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/config.schema.json` and `addon/anki_audio_quick_editor/config.json` to add `visible_editor_buttons`.
- Modify `addon/anki_audio_quick_editor/config_migration.py` to bump `CURRENT_CONFIG_VERSION`.
- Regenerate `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts`.
- Modify Python fixtures/tests that build full configs.
- Modify `addon/anki_audio_quick_editor/editor_ui.py` and `addon/anki_audio_quick_editor/editor_integration.py` to pass the list to the editor webview.
- Modify `settings_ui/src/editor-inline/types.ts`, `settings_ui/src/editor-inline/commands.ts`, and `settings_ui/src/editor-inline/EditorControls.svelte` for editor filtering.
- Create `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`.
- Modify `settings_ui/src/settings/GeneralSettingsPanel.svelte` and `settings_ui/src/settings/settings-state.ts` for settings UI/default state.
- Modify locale files for settings section strings.
- Add/update Vitest, pytest, and e2e coverage for the new behavior.

## Task 1: Config, Contracts, And Python Injection

- [ ] Add `visible_editor_buttons` to `config.schema.json` as a required array of known top-level `aqe:` command strings.
- [ ] Add the default full command list to `config.json`.
- [ ] Bump `CURRENT_CONFIG_VERSION` from `15` to `16`.
- [ ] Add migration/default tests in `tests/test_config_migration.py`, `tests/test_settings_state.py`, `tests/settings_command_fixtures.py`, and any e2e default config helper.
- [ ] Run `python3 scripts/dev.py contracts-generate`, then verify `python3 scripts/dev.py contracts-check`.
- [ ] Update `editor_ui.injection_script()` to accept `visible_editor_buttons` and embed `visibleEditorButtons`.
- [ ] Update `editor_integration._on_editor_will_load_note()` to pass `config.get("visible_editor_buttons", [])`.
- [ ] Update `tests/test_editor_ui.py` to verify the embedded list and fallback default.

## Task 2: Editor Frontend Filtering

- [ ] Extend `EditorRuntimeConfig` with `visibleEditorButtons?: EditorCommand[]`.
- [ ] Add a helper in `commands.ts` that returns the editor top-level command list and filters invalid/missing visibility values back to all buttons.
- [ ] Update `EditorControls.svelte` to render only visible top-level buttons while keeping Delete Region/Delete the rest outside the filter.
- [ ] Add Vitest coverage in `settings_ui/tests/editor-inline.integration.test.ts` that hides `aqe:settings` and verifies `[data-testid="aqe-button-0-settings"]` is absent while other visible buttons render.

## Task 3: Settings Toolbar Toggle UI

- [ ] Create `ToolbarVisibilitySettings.svelte` that receives `bind:config`, renders the settings copy of top-level buttons, toggles command membership in `config.visible_editor_buttons`, and marks off buttons with `aria-pressed="false"` plus a data state/class.
- [ ] Insert the component into `GeneralSettingsPanel.svelte` near other editor behavior settings.
- [ ] Add fallback defaults to `settings-state.ts`.
- [ ] Add locale keys for the section title, summary, and off-state label in all locale JSON files, using English source text where no translation is available.
- [ ] Add Vitest coverage in `settings_ui/tests/app.test.ts` for rendering the section, toggling Settings off, and saving a payload without `aqe:settings`.

## Task 4: E2E And Quality Gate

- [ ] Add an e2e test that configures `visible_editor_buttons` without `aqe:settings`, opens an editor, and verifies the Settings button is absent.
- [ ] Run targeted checks: `python3 scripts/dev.py config-schema`, `python3 scripts/dev.py contracts-check`, focused pytest files, and focused Vitest files.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e` before calling the feature complete.
- [ ] Use `$doc-maintain` review after schema changes and update docs only if stale user-facing docs need the new key documented.

