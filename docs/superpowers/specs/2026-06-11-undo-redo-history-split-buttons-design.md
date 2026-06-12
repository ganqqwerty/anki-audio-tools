# Undo/Redo History Split Buttons Design

## Purpose

Undo and redo currently expose only one-step toolbar buttons. Users cannot see what they are about to restore, and a long edit session requires repeated clicks to reach an older state.

The design changes Undo and Redo into split buttons. The primary segment keeps the current one-step behavior. The menu segment shows available history entries for the current field, labeled by operation name or summary rather than filename, and lets the user jump directly to an older undo or redo state.

## User Guarantee

For the active editor field, the Undo and Redo menus list the same history that the buttons can execute. Selecting a menu row restores that row by applying the required number of undo or redo steps. If history changes, the editor becomes busy, or the selected row no longer applies, the add-on refuses safely and leaves the note unchanged.

The menu labels prioritize operation meaning over media names. A row should read like "Shorten pauses" or "Denoise" when that information is available. Filenames are fallback diagnostics, not the primary label.

## Configurable History Size

Add a schema-backed Settings value for editor history size. This setting controls how many undo and redo entries are retained for the active editor field and how many rows the split menus can show.

Initial behavior:

- Default: 100 entries.
- Minimum: 1 entry.
- Maximum: 100 entries.
- Values outside the range are clamped at the config boundary.
- Reducing the value prunes the oldest in-memory entries beyond the configured limit.
- Increasing the value affects future retained entries; it does not recover entries already pruned.

The setting is editor-scoped. It does not introduce Browser batch undo/redo, and it does not replace any future persistent-history retention policy.

## Settings And Config Contract

Add `editor_history_size` to the config schema, default config, generated contracts, settings initial state, and editor runtime config. The Settings dialog should expose it as a numeric editor control under the editor/toolbar area because it directly affects inline editor undo and redo behavior.

The Python config boundary should normalize the value before editor sessions consume it. Frontend Settings controls should also clamp input for immediate feedback, but Python remains the source of truth for runtime safety.

## Current System Context

The inline editor frontend stores per-field history availability through `window.__aqeSetHistoryAvailability`, currently as `canUndo` and `canRedo` booleans. Undo and redo render as plain `EditorToolbarButton` instances.

The Python editor session owns in-memory `undo_history` and `redo_history` stacks. Each `UndoEntry` stores an `AudioEditState`, filename, and `status_summary`. Standard persistent undo can also supply the latest available undo entry from SQLite when the in-memory stack is empty. Persistent redo is not available today.

History restoration already centralizes note replacement, post-edit playback, graph redraw, status reload, and toolbar availability sync in `editor_history.restore_history_entry` and the persistent undo helper. The split-button feature should reuse those paths instead of creating a separate restore implementation.

## UI Behavior

Undo and Redo become split buttons in the inline editor toolbar:

- Primary click runs the current one-step `aqe:undo` or `aqe:redo`.
- The menu button opens a field-local history menu.
- The menu lists newest entries first.
- The menu shows at most the configured history size per direction, with 100 as the hard upper bound.
- Each row shows a concise operation label.
- The menu closes after a row is selected.
- Buttons and menu rows are disabled while any editor operation is busy.
- Empty history keeps the primary action disabled and the menu unavailable.

The split buttons should follow the existing toolbar split-button styling and accessibility conventions. They should use the existing command icons, tooltip system, and `data-testid` patterns so frontend tests can target the primary button, menu trigger, popover, and rows.

## History Snapshot Contract

Add a richer history snapshot contract alongside the existing availability update. The frontend should retain a per-field structure equivalent to:

```typescript
type EditorHistoryMenuItem = {
  id: string;
  label: string;
};

type EditorHistorySnapshot = {
  canUndo: boolean;
  canRedo: boolean;
  undoItems: EditorHistoryMenuItem[];
  redoItems: EditorHistoryMenuItem[];
};
```

Python should send this snapshot whenever it currently syncs history availability:

- after editor controls mount,
- after a successful audio edit,
- after undo or redo,
- after a persistent undo availability check,
- after note or field reload retries.

Add `__aqeSetHistorySnapshot(ord, snapshot)` as the new runtime contract. Keep the existing `__aqeSetHistoryAvailability(ord, canUndo, canRedo)` function as a thin compatibility wrapper that writes an empty-item snapshot for tests and any older call sites during the migration.

Snapshot generation should apply the configured history size before sending data to the frontend. The frontend should still defensively cap rendered rows at 100.

## Label Source

Use `UndoEntry.status_summary` as the first label source for in-memory undo and redo items. It is already operation-oriented and avoids making generated filenames the visible contract.

If `status_summary` is empty, use a localized generic fallback:

- undo item fallback: "Previous edit"
- redo item fallback: "Restored edit"

Persistent undo rows should use `PersistentHistoryOperation.status_summary` with the same fallback rule. Persistent entries should be included only when they are executable according to the same checks used for persistent undo availability.

## Jump Command

Menu selection sends a payload command instead of overloading the one-step commands:

```typescript
{
  command: "aqe:history-jump",
  fieldOrd: number,
  direction: "undo" | "redo",
  steps: number
}
```

`steps` is one-based. Selecting the first undo row sends `steps: 1`, which is equivalent to one normal undo. Selecting the fifth undo row sends `steps: 5`, which applies five undo restores if all five remain valid.

Python validates:

- field ordinal is present and matches the current editor field target,
- direction is `undo` or `redo`,
- steps is an integer from 1 through the configured history size, never above 100,
- the editor session is not busy,
- enough history exists at execution time.

Invalid or stale requests should show the same kind of status feedback as current empty undo/redo attempts and must not mutate the note.

## Restore Semantics

History jump should reuse existing restore behavior step by step:

- Undo jump repeatedly restores from undo history and pushes current state to redo history.
- Redo jump repeatedly restores from redo history and pushes current state to undo history.
- A new successful audio edit still clears redo history.
- Undo and redo stacks prune oldest entries when they exceed the configured history size.
- The final restored state triggers the normal post-replacement playback, graph redraw, status, and selection reset behavior.
- Intermediate steps should avoid redundant editor reloads where practical, but correctness is more important than batching in the first implementation.

Persistent undo is only part of undo history when in-memory undo is empty and the persistent operation is executable. Persistent redo remains out of scope because the current project does not implement durable redo.

## Error Handling

Busy state blocks primary clicks and menu selection. If a jump request reaches Python while busy, Python reports the current processing state and does not change history or note fields.

If a selected row is stale because another command changed history before Python handles it, Python must confirm that the full requested step count exists before the first restore step runs. Otherwise it refuses without partial mutation.

If persistent undo becomes unavailable between menu render and selection, the command refuses through the existing persistent undo error/status path.

## Testing

Frontend tests:

- Undo and Redo render as split buttons when visible.
- Primary segments preserve one-step dispatch.
- Menu rows render from per-field history snapshots, newest first.
- Menus cap at the configured history size and never render more than 100 rows.
- Row clicks dispatch `aqe:history-jump` payloads with direction and one-based steps.
- Empty or busy history disables the relevant controls.
- History snapshots stay field-local.

Python unit/integration tests:

- History snapshot generation maps `status_summary` to labels and applies fallbacks.
- Snapshot generation caps each direction at the configured history size and never above 100.
- Config validation clamps history size to the 1 through 100 range.
- Settings UI edits persist `editor_history_size` and initialize from the schema-backed default.
- Undo and redo stacks prune oldest entries beyond the configured history size.
- Jump command decoding validates direction, steps, and field ordinal.
- Multi-step undo restores the selected older state and pushes intermediate current states to redo.
- Multi-step redo restores the selected newer state and pushes intermediate current states to undo.
- Busy jump requests are rejected without mutation.
- Stale or out-of-range jump requests are rejected without partial mutation.
- Persistent undo contributes an executable undo item only when current availability checks pass.

E2E coverage should include at least one real editor workflow that creates multiple audio edits, opens the Undo menu, jumps back more than one step, opens Redo, and jumps forward again.

## Out Of Scope

- Persistent redo.
- Showing filenames as primary row labels.
- Batch dialog undo or redo.
- Changing the existing non-destructive audio edit contract.
