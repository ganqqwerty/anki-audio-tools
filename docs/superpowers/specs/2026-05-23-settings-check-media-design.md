# Settings Check Media Design

## Goal

Add a `Check Media` button to the Settings dialog's Diagnostics tab so users can open Anki's built-in media check and cleanup window without leaving add-on settings.

## Scope

In scope:

- A new Diagnostics-tab button labeled `Check Media`.
- A dedicated settings bridge command for this action.
- Python settings-command handling that calls Anki's built-in media check entry point.
- Focused frontend and backend tests for the new button and command dispatch.

Out of scope:

- Recreating Anki's media check UI inside the add-on.
- Custom progress reporting or result rendering inside the settings webview.
- New cleanup behavior beyond what Anki already provides in its stock media check flow.

## UX

The Diagnostics tab keeps its existing action row and adds a secondary `Check Media` button alongside the current diagnostics actions.

Clicking the button immediately opens Anki's built-in `Check Media` flow. That stock flow remains responsible for its own progress UI, report dialog, and cleanup actions such as deleting unused files, restoring trash, or emptying trash.

The add-on settings UI does not display an additional success message, progress state, or embedded report for this action. The user-visible feedback is the standard Anki window.

## Architecture

The frontend uses a simple one-off bridge command instead of the existing `settings.async` job path. The action does not need an add-on-managed async wrapper because Anki's own media checker already starts its background work and presents the standard dialogs.

The new bridge command name is `settings.check_media`.

`settings_ui/src/lib/bridge.ts` adds a small helper that sends this command. `settings_ui/src/settings/DiagnosticsPanel.svelte` receives a callback prop and wires the new button to that helper through `SettingsApp.svelte`.

`addon/anki_audio_quick_editor/settings/commands.py` handles `settings.check_media` and calls `aqt.mediacheck.check_media_db(mw)`. This keeps the implementation explicit and aligned with Anki's installed API instead of routing through menu actions or duplicating media-check logic.

## Files In Scope

- `settings_ui/src/lib/bridge.ts`
- `settings_ui/src/settings/SettingsApp.svelte`
- `settings_ui/src/settings/DiagnosticsPanel.svelte`
- `settings_ui/tests/bridge.test.ts`
- `settings_ui/tests/app.test.ts`
- `addon/anki_audio_quick_editor/settings/commands.py`
- `tests/test_settings_commands_diagnostics.py`

## Testing

- Add a bridge helper test that verifies `settings.check_media` serializes into the shared `bridge:` JSON envelope.
- Add a settings app test that switches to the Diagnostics tab, clicks `Check Media`, and verifies the bridge command was sent.
- Add a Python settings-command test that verifies `handle_settings_command()` dispatches `settings.check_media` to Anki's built-in `check_media_db(mw)` entry point.

## Acceptance Criteria

- The Diagnostics tab shows a `Check Media` button.
- Clicking the button opens Anki's built-in media check/cleanup flow.
- No new add-on-owned progress or report UI is introduced for this action.
- The focused frontend and backend tests cover the command wiring.
