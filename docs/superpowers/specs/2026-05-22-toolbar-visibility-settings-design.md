# Toolbar Visibility Settings Design

## Goal

Let users reduce inline editor toolbar clutter by choosing which top-level Audio Quick Editor buttons are visible. The selected direction is that every top-level button is hideable, including Settings.

## Scope

In scope:

- A settings panel copy of the editor toolbar.
- Click-to-toggle visibility for every top-level editor button.
- Off buttons shown with a distinct muted danger color in settings.
- Persisted button visibility in the add-on config.
- Editor toolbar rendering filtered by the persisted visibility list.
- Tests for migration/defaults, settings save, settings UI behavior, editor config injection, and editor rendering.

Out of scope:

- Per-note or per-field button visibility.
- Reordering buttons.
- Hiding contextual graph-region buttons such as Delete Region and Delete the rest.
- Changing bridge command semantics or audio processing behavior.

## UX

The General settings tab includes an "Editor toolbar buttons" section. It renders a compact copy of the editor toolbar using the same command labels and icon vocabulary. Clicking a button toggles it on or off. Enabled buttons use the normal button style; disabled buttons remain visible in settings but use a muted danger/off state and `aria-pressed="false"`.

Saving settings applies the new visibility to later editor loads. Existing open editor controls may keep their current toolbar until the note/editor is refreshed, matching existing settings behavior for editor defaults.

Because the selected policy makes every button hideable, users can hide Settings from the editor toolbar. They can still open settings from the Anki add-on menu.

## Data Model

Add a config key:

```json
"visible_editor_buttons": [
  "aqe:play",
  "aqe:analyze",
  "aqe:show-file",
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
]
```

The list stores top-level editor command IDs. Defaults include every current top-level button so existing installs do not lose buttons after migration.

The editor frontend receives this list as `window.__AQE_EDITOR_CONFIG__.visibleEditorButtons`. If the list is missing or not an array at runtime, the frontend falls back to all known buttons. An empty array is valid and hides every top-level toolbar button.

## Architecture

Config schema remains the source of truth. Updating the schema requires regenerating Python and TypeScript contracts. Python migration only needs the existing default merge plus a config version bump.

The frontend should share button metadata instead of duplicating labels manually. The existing `commandButtons()` list remains the source for editor top-level buttons. Settings gets a small component that renders the same metadata in toggle mode, with a settings-safe copy of the denoise top-level button inserted after Shorten Pauses to match the editor toolbar.

The editor filtering stays in `settings_ui/src/editor-inline/EditorControls.svelte` or a small adjacent helper. It filters top-level buttons before rendering. Contextual region buttons remain outside this filter because they are shown only when graph selection state requires them.

Python passes `visible_editor_buttons` through `editor_integration.py` into `editor_ui.injection_script()`, which serializes it as `visibleEditorButtons`.

## Testing

Required tests:

- Python config migration picks up the new default and stamps the new config version.
- Settings initial-state fixture and settings save fixture accept the new key.
- Config schema and generated contracts stay in sync.
- Settings Svelte tests verify the toolbar visibility section renders, toggling Settings off is allowed, off buttons are color/state marked, and save payload includes the updated list.
- Editor Svelte tests verify hidden buttons are not rendered, including Settings.
- `tests/test_editor_ui.py` verifies `injection_script()` embeds `visibleEditorButtons`.
- A focused e2e test verifies hiding Settings in config removes it from a later editor load.
