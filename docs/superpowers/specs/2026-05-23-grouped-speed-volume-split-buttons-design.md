# Grouped Speed And Volume Split Buttons Design

## Goal

Replace the duplicate split-menu triggers for `volume` and `speed` editor actions with one shared split menu per pair while keeping both primary action buttons.

## Scope

In scope:

- Render `volume-down`, `volume-up`, and one shared `volume` split-menu trigger as a single visual group.
- Render `slower`, `faster`, and one shared `speed` split-menu trigger as a single visual group.
- Apply shared menu edits to both commands in the group.
- Save promoted defaults from the shared menu back to the existing `volume_step_db` and `speed_step` settings.
- Add focused frontend tests and broader E2E coverage for grouped behavior.

Out of scope:

- Reworking other split-button groups such as play, graph, convert, share, pause, or denoise.
- Changing the stored settings schema or the payload shape for speed and volume commands.
- Hiding either primary action button.

## UX

Toolbar layout:

- Volume renders as `[Volume -][Volume +][Options]`.
- Speed renders as `[Slower][Faster][Options]`.
- The shared menu button stays visually attached to the two primary buttons.

Interaction rules:

- Clicking either primary button still runs only that command.
- Clicking the shared menu opens one popover for the whole group.
- Editing the group value changes the field-local `volumeStepDb` or `speedStep`.
- The next click on either primary button in the same group uses the updated field-local value.
- Promoting defaults from the shared menu updates the existing matching setting and refreshes untouched fields the same way current split menus do.

## State Model

No new state bucket is needed.

- Volume grouping continues to use the existing per-field `volumeStepDb` and `volumeEdited` state.
- Speed grouping continues to use the existing per-field `speedStep` and `speedEdited` state.
- Payload builders keep deriving overrides from the command being executed, so `volume-up` and `volume-down` still dispatch different commands with the same shared numeric override.

## Rendering Approach

Keep the existing split-popover logic and reuse it for grouped menus.

- Introduce a grouped rendering path in the inline editor toolbar for the `volume` and `speed` pairs only.
- Render the two primary buttons separately from the shared menu trigger.
- Reuse one popover instance per group, keyed to a stable group slug such as `volume` or `speed`.
- Keep the existing per-command slugs for the primary buttons so busy-state wiring, help text, selectors, and button titles stay stable.

## Testing

Required coverage:

- Frontend integration tests proving the grouped menu exists once per pair and still updates payloads for both commands.
- Frontend popover tests proving the grouped menu exposes the expected grouped test IDs.
- E2E tests proving:
  - the grouped menu defaults come from settings,
  - editing the grouped menu affects both commands in the pair,
  - saving defaults from the grouped menu updates the existing setting key,
  - local grouped edits do not mutate settings unless save-default is pressed,
  - multi-field field-local isolation still holds with grouped menus.
