# Graph Split Menu Design

## Goal

Update the inline editor graph split menu so the graph-specific options use clearer control types and labels without changing the underlying graph setting payloads.

## Approved UI

- Remove the graph split popover summary sentence that starts with `Current settings: ...`.
- Reorder graph options to:
  1. `Speaker's voice`
  2. `Voice lock`
  3. `Smoothness`
  4. `Connect short dropouts`
  5. `Recording condition`
- Replace the current range sliders for `Speaker's voice`, `Voice lock`, and `Smoothness` with single-select button groups.
- Keep `Connect short dropouts` as the existing numeric slider.
- Move `Recording condition` to the last position in the menu.

## Labels

`Speaker's voice` uses the existing `GraphVoiceRange` values with these updated visible captions:

- `bass` -> `Bass voice`
- `low` -> `Low voice`
- `general` -> `Normal voice`
- `high` -> `High voice`
- `child` -> `Child/falcetto`

`Smoothness` keeps the existing option set and wording:

- `Raw`
- `Balanced`
- `Smooth`
- `Very smooth`

`Voice lock` keeps the existing option set and wording:

- `Loose`
- `Balanced`
- `Stable`

## Behavior

- Button groups must behave like radio groups: exactly one option is selected at a time.
- Selecting a graph option must still update the same field-local split state used by the graph command payload.
- The graph primary button title and split-menu title may still reflect the current field-local value summary. Only the popover description summary line is removed.

## Files In Scope

- `settings_ui/src/editor-inline/GraphSplitOptions.svelte`
- `settings_ui/src/editor-inline/SplitButton.svelte`
- `settings_ui/src/editor-inline/styles/split-popovers.css`
- `settings_ui/src/lib/i18n.ts`
- `addon/anki_audio_quick_editor/locales/en.json`
- `settings_ui/tests/editor-inline.command-splits.integration.test.ts`
- `settings_ui/tests/split-button-state.test.ts`

## Testing

- Update integration coverage so graph split controls are exercised through the new button-group selectors and ordering.
- Update label-format tests for the renamed voice-range captions.
