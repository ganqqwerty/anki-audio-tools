# Undo/Redo History Split Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build configurable editor undo/redo history split buttons that show operation-named history entries and jump directly to the selected undo or redo depth.

**Architecture:** Add a schema-backed `editor_history_size` setting, make Python editor history expose per-field snapshots, and render Undo/Redo through a dedicated Svelte split button that consumes those snapshots. Keep existing one-step `aqe:undo`/`aqe:redo` behavior as the primary action, and add `aqe:history-jump` as the menu-selection payload command.

**Tech Stack:** Python 3.13 Anki add-on code, Svelte 5 + TypeScript editor/settings UI, generated JSON contracts, Vitest frontend tests, pytest backend tests, `scripts/dev.py` quality commands.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/config.schema.json`: add required integer `editor_history_size`, min 1, max 100.
- Modify `addon/anki_audio_quick_editor/config.json`: default `editor_history_size` to `100`.
- Modify `addon/anki_audio_quick_editor/audio_state.py`: add `editor_history_size` to `AudioProcessingConfig` and clamp it in `from_config`.
- Modify `addon/anki_audio_quick_editor/config_migration.py`: normalize merged `editor_history_size`.
- Regenerate `settings_ui/src/lib/generated/contracts.ts` and `addon/anki_audio_quick_editor/contracts_generated.py` with `python3 scripts/dev.py contracts-generate`.
- Modify `settings_ui/src/settings/settings-state.ts`, `settings_ui/tests/settings-app-helpers.ts`, and `settings_ui/tests/settings-state.test.ts`: add default config coverage for `editor_history_size`.
- Modify `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`: expose the setting in the Undo and Redo toolbar cards with `UnitNumberInput`.
- Modify locale JSON files under `addon/anki_audio_quick_editor/locales/`: add labels for the setting and history menu fallback rows.
- Modify `addon/anki_audio_quick_editor/editor_session.py`: add history size clamping constants/helpers, cap `UndoHistory`, and expose snapshot-friendly item data.
- Create `addon/anki_audio_quick_editor/editor_history_snapshot.py`: build history snapshots for frontend delivery.
- Modify `addon/anki_audio_quick_editor/editor_history.py`: sync snapshots instead of booleans, add `history_jump`, and validate jump requests before mutation.
- Modify `addon/anki_audio_quick_editor/editor_actions.py`: decode `direction` and `steps` for `aqe:history-jump`.
- Modify `addon/anki_audio_quick_editor/editor_bridge.py`, `editor_dependencies.py`, `editor_callbacks.py`: route `aqe:history-jump` through the non-processing command path.
- Modify `addon/anki_audio_quick_editor/editor_frontend/refresh.py` and `editor_frontend_callbacks.py`: add `eval_history_snapshot`, `history_snapshot_expression`, and retry scheduling based on snapshots; keep `__aqeSetHistoryAvailability` compatibility.
- Modify `addon/anki_audio_quick_editor/editor_webview_injection.py` and `editor_ui.py`: inject `initialHistorySnapshotsByField` and `editorHistorySize`.
- Modify `settings_ui/src/editor-inline/editor-runtime-types.ts`, `globals.d.ts`, `window-contract.ts`, `control-actions.ts`, and `types.ts`: add history snapshot types and window API.
- Create `settings_ui/src/editor-inline/HistorySplitButton.svelte`: render the Undo/Redo split button and history menu.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: route `aqe:undo` and `aqe:redo` through `HistorySplitButton`.
- Modify `settings_ui/src/editor-inline/command-actions.ts`: ensure `aqe:history-jump` uses post-edit playback intent and normal busy blocking.
- Add/update tests in `tests/`, `settings_ui/tests/`, and one e2e workflow.

## Task 1: Config And Settings Surface

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/audio_state.py`
- Modify: `addon/anki_audio_quick_editor/config_migration.py`
- Modify: `tests/test_contract_generation.py`
- Modify: `tests/test_config_migration_defaults.py`
- Modify: `tests/test_config_migration_normalization.py`
- Modify: `tests/test_audio_state.py`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `settings_ui/tests/settings-app-helpers.ts`
- Modify: `settings_ui/tests/settings-state.test.ts`
- Modify: `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`
- Modify: `settings_ui/tests/app.settings.test.ts`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`

- [x] **Step 1: Write failing Python config tests**

Add this to `tests/test_contract_generation.py` inside `test_composed_contract_schema_uses_config_schema_source`:

```python
    assert "editor_history_size" in config["properties"]
    assert "editor_history_size" in config["required"]
    assert config["properties"]["editor_history_size"]["minimum"] == 1
    assert config["properties"]["editor_history_size"]["maximum"] == 100
```

Add this to `tests/test_config_migration_defaults.py` in `TestMigrateConfigDefaults`:

```python
    def test_picks_up_editor_history_size_default(self) -> None:
        user = {"_config_version": 2, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "editor_history_size": 100,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["editor_history_size"] == 100
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True
```

Add this to `tests/test_config_migration_normalization.py`:

```python
def test_clamps_editor_history_size() -> None:
    defaults = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "enabled": True,
        "editor_history_size": 100,
    }

    low, low_changed = migrate_config({"editor_history_size": -3}, defaults)
    high, high_changed = migrate_config({"editor_history_size": 250}, defaults)
    non_numeric, non_numeric_changed = migrate_config({"editor_history_size": "many"}, defaults)

    assert low["editor_history_size"] == 1
    assert high["editor_history_size"] == 100
    assert non_numeric["editor_history_size"] == 100
    assert low_changed is True
    assert high_changed is True
    assert non_numeric_changed is True
```

Add this to `tests/test_audio_state.py`:

```python
def test_audio_processing_config_clamps_editor_history_size() -> None:
    assert AudioProcessingConfig.from_config({"editor_history_size": 5}).editor_history_size == 5
    assert AudioProcessingConfig.from_config({"editor_history_size": 0}).editor_history_size == 1
    assert AudioProcessingConfig.from_config({"editor_history_size": 500}).editor_history_size == 100
    assert AudioProcessingConfig.from_config({"editor_history_size": "many"}).editor_history_size == 100
```

- [x] **Step 2: Run failing Python config tests**

Run:

```bash
python3 -m pytest tests/test_contract_generation.py::test_composed_contract_schema_uses_config_schema_source tests/test_config_migration_defaults.py::TestMigrateConfigDefaults::test_picks_up_editor_history_size_default tests/test_config_migration_normalization.py::test_clamps_editor_history_size tests/test_audio_state.py::test_audio_processing_config_clamps_editor_history_size -q
```

Expected: failures mention missing `editor_history_size`, missing clamp behavior, or missing `AudioProcessingConfig.editor_history_size`.

- [x] **Step 3: Implement config schema, defaults, and normalization**

In `addon/anki_audio_quick_editor/config.schema.json`, add `"editor_history_size"` to `required` after `selection_marker_shift_buttons_enabled`, and add:

```json
    "editor_history_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
```

In `addon/anki_audio_quick_editor/config.json`, add:

```json
  "editor_history_size": 100,
```

Place it near the other editor settings, after `"selection_marker_shift_buttons_enabled": false`.

In `addon/anki_audio_quick_editor/audio_state.py`, add constants near `ConfigValue`:

```python
MIN_EDITOR_HISTORY_SIZE = 1
MAX_EDITOR_HISTORY_SIZE = 100
DEFAULT_EDITOR_HISTORY_SIZE = 100
```

Add the dataclass field:

```python
    editor_history_size: int = DEFAULT_EDITOR_HISTORY_SIZE
```

Add the helper before `AudioProcessingConfig` or after it:

```python
def normalize_editor_history_size(value: object) -> int:
    """Return a supported per-field editor history size."""
    if isinstance(value, bool):
        return DEFAULT_EDITOR_HISTORY_SIZE
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_EDITOR_HISTORY_SIZE
    return min(MAX_EDITOR_HISTORY_SIZE, max(MIN_EDITOR_HISTORY_SIZE, parsed))
```

Add this to `AudioProcessingConfig.from_config(...)`:

```python
            editor_history_size=normalize_editor_history_size(
                config.get("editor_history_size", cls.editor_history_size)
            ),
```

In `addon/anki_audio_quick_editor/config_migration.py`, import the helper:

```python
from .audio_state import normalize_editor_history_size
```

Add this call in `_apply_post_merge_migrations` before visible-button normalization:

```python
    changed = _normalize_editor_history_size_setting(merged) or changed
```

Add this helper:

```python
def _normalize_editor_history_size_setting(merged: dict[str, Any]) -> bool:
    if "editor_history_size" not in merged:
        return False
    normalized = normalize_editor_history_size(merged.get("editor_history_size"))
    if merged.get("editor_history_size") == normalized:
        return False
    merged["editor_history_size"] = normalized
    return True
```

- [x] **Step 4: Run Python config tests until they pass**

Run:

```bash
python3 -m pytest tests/test_contract_generation.py::test_composed_contract_schema_uses_config_schema_source tests/test_config_migration_defaults.py::TestMigrateConfigDefaults::test_picks_up_editor_history_size_default tests/test_config_migration_normalization.py::test_clamps_editor_history_size tests/test_audio_state.py::test_audio_processing_config_clamps_editor_history_size -q
```

Expected: all selected tests pass.

- [x] **Step 5: Write failing settings UI tests**

In `settings_ui/tests/settings-state.test.ts`, add `editor_history_size: 100` to the local `config` object.

Add this test:

```typescript
  it("preserves editor history size when building a save payload", () => {
    expect(saveConfigPayload({
      ...config,
      editor_history_size: 25,
    }).editor_history_size).toBe(25);
  });
```

In `settings_ui/tests/settings-app-helpers.ts`, add `editor_history_size: 100` to `defaultConfig`.

In `settings_ui/tests/app.settings.test.ts`, add this test:

```typescript
  it("saves editor history size from undo settings", async () => {
    setInitialState();

    render(App);
    await fireEvent.input(screen.getByTestId("editor-history-size"), {
      target: { value: "25" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ editor_history_size: number }>("settings.save");
    expect(config.editor_history_size).toBe(25);
  });
```

- [x] **Step 6: Run failing settings UI tests**

Run:

```bash
cd settings_ui && npm test -- settings-state.test.ts app.settings.test.ts
```

Expected: TypeScript or test failures mention missing `editor_history_size` in generated `Config`, missing input, or missing test id.

- [x] **Step 7: Implement settings UI and generated contracts**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: `settings_ui/src/lib/generated/contracts.ts` and `addon/anki_audio_quick_editor/contracts_generated.py` include `editor_history_size`.

In `settings_ui/src/settings/settings-state.ts`, add:

```typescript
    editor_history_size: 100,
```

In `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`, add an Undo/Redo branch before the final Settings branch:

```svelte
{:else if command === "aqe:undo" || command === "aqe:redo"}
  <label class="settings-field">
    <span>{t("settings.editor_history_size")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="editor-history-size"
      min="1"
      max="100"
      step="1"
      bind:value={config.editor_history_size}
    />
  </label>
```

In each locale JSON file, add translations for:

```json
  "settings.editor_history_size": "Undo/redo history entries",
  "editor.history.undo_empty_label": "Previous edit",
  "editor.history.redo_empty_label": "Restored edit",
  "editor.history.menu_title": "{label} history",
  "editor.history.jump_to": "{label}"
```

For non-English catalogs, use English text if no translation is available; the catalog fallback still keeps keys explicit and testable.

- [x] **Step 8: Run settings tests until they pass**

Run:

```bash
cd settings_ui && npm test -- settings-state.test.ts app.settings.test.ts
```

Expected: selected tests pass.

- [x] **Step 9: Commit Task 1**

```bash
git add addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/audio_state.py addon/anki_audio_quick_editor/config_migration.py addon/anki_audio_quick_editor/contracts_generated.py addon/anki_audio_quick_editor/locales/*.json settings_ui/src/lib/generated/contracts.ts settings_ui/src/settings/settings-state.ts settings_ui/src/settings/ToolbarPanelSettingsFields.svelte settings_ui/tests/settings-app-helpers.ts settings_ui/tests/settings-state.test.ts settings_ui/tests/app.settings.test.ts tests/test_contract_generation.py tests/test_config_migration_defaults.py tests/test_config_migration_normalization.py tests/test_audio_state.py
git commit -m "Add configurable editor history size" -m "Undo and redo history menus need a user-controlled retention limit so long edit sessions can expose enough history without unbounded per-field stacks. This adds a schema-backed setting, clamps it at the config boundary, and surfaces it in the editor toolbar settings so runtime history behavior has one validated source of truth." -m "Full check and e2e routines were not run yet; this task ran targeted config and settings tests only."
```

## Task 2: Backend History Snapshots And Stack Limit

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Create: `addon/anki_audio_quick_editor/editor_history_snapshot.py`
- Modify: `addon/anki_audio_quick_editor/editor_history.py`
- Modify: `addon/anki_audio_quick_editor/editor_frontend/refresh.py`
- Modify: `addon/anki_audio_quick_editor/editor_frontend_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_webview_injection.py`
- Modify: `addon/anki_audio_quick_editor/editor_ui.py`
- Modify: `tests/test_editor_integration.py`
- Create or modify: `tests/test_editor_history_snapshot.py`

- [x] **Step 1: Write failing backend snapshot tests**

Create `tests/test_editor_history_snapshot.py`:

```python
from __future__ import annotations

from types import SimpleNamespace

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_history_snapshot import history_snapshot_for_field
from anki_audio_quick_editor.editor_session import EditorSession, UndoHistory


def test_history_snapshot_uses_status_summaries_and_caps_items() -> None:
    session = EditorSession(field_index=0)
    for index in range(4):
        session.undo_history.push(
            AudioEditState(f"source-{index}.mp3"),
            f"source-{index}.mp3",
            status_summary=f"Operation {index}",
        )
    session.redo_history.push(AudioEditState("redo.mp3"), "redo.mp3", status_summary="")

    snapshot = history_snapshot_for_field(
        SimpleNamespace(note=SimpleNamespace(id=123)),
        field_index=0,
        session=session,
        history_size=3,
        can_persistent_undo=lambda _editor, _field_index: False,
        latest_persistent_undo_item=lambda _editor, _field_index: None,
    )

    assert snapshot == {
        "canUndo": True,
        "canRedo": True,
        "undoItems": [
            {"id": "undo:1", "label": "Operation 3"},
            {"id": "undo:2", "label": "Operation 2"},
            {"id": "undo:3", "label": "Operation 1"},
        ],
        "redoItems": [
            {"id": "redo:1", "label": "Restored edit"},
        ],
    }


def test_history_snapshot_includes_persistent_undo_when_session_empty() -> None:
    snapshot = history_snapshot_for_field(
        SimpleNamespace(note=SimpleNamespace(id=123)),
        field_index=0,
        session=EditorSession(field_index=0),
        history_size=100,
        can_persistent_undo=lambda _editor, _field_index: True,
        latest_persistent_undo_item=lambda _editor, _field_index: {"id": "persistent:42", "label": "Shorten pauses"},
    )

    assert snapshot["canUndo"] is True
    assert snapshot["undoItems"] == [{"id": "persistent:42", "label": "Shorten pauses"}]
    assert snapshot["redoItems"] == []


def test_undo_history_prunes_oldest_entries_to_limit() -> None:
    history = UndoHistory(max_entries=3)
    for index in range(5):
        history.push(AudioEditState(f"source-{index}.mp3"), f"source-{index}.mp3")

    assert [entry.filename for entry in history.entries] == [
        "source-2.mp3",
        "source-3.mp3",
        "source-4.mp3",
    ]
```

- [x] **Step 2: Run failing backend snapshot tests**

Run:

```bash
python3 -m pytest tests/test_editor_history_snapshot.py -q
```

Expected: failures mention missing `editor_history_snapshot`, missing `UndoHistory.max_entries`, or incorrect snapshot behavior.

- [x] **Step 3: Implement capped `UndoHistory`**

In `addon/anki_audio_quick_editor/editor_session.py`, import the constants:

```python
from .audio_state import AudioEditState, DEFAULT_EDITOR_HISTORY_SIZE, normalize_editor_history_size
```

Change `UndoHistory`:

```python
@dataclass
class UndoHistory:
    """Undo stack for generated audio references."""

    entries: list[UndoEntry] = field(default_factory=list)
    max_entries: int = DEFAULT_EDITOR_HISTORY_SIZE

    def set_max_entries(self, value: object) -> None:
        """Apply a new stack limit and prune oldest entries."""
        self.max_entries = normalize_editor_history_size(value)
        self._prune()

    def push(
        self,
        state: AudioEditState | None,
        filename: str | None,
        status_summary: str = "",
    ) -> None:
        """Remember the current generated/reference state before rendering."""
        if state is not None and filename:
            self.entries.append(UndoEntry(state, filename, status_summary=status_summary))
            self._prune()

    def pop(self) -> UndoEntry | None:
        """Return the previous state to restore, if one exists."""
        return self.entries.pop() if self.entries else None

    def clear(self) -> None:
        """Drop history when switching fields or source media."""
        self.entries.clear()

    def _prune(self) -> None:
        overflow = len(self.entries) - self.max_entries
        if overflow > 0:
            del self.entries[:overflow]
```

- [x] **Step 4: Implement history snapshot builder**

Create `addon/anki_audio_quick_editor/editor_history_snapshot.py`:

```python
"""Editor history snapshot payloads for inline undo/redo menus."""

from __future__ import annotations

from typing import Any, Callable, TypedDict

from .audio_state import normalize_editor_history_size
from .editor_session import EditorSession, UndoEntry


class HistoryMenuItem(TypedDict):
    id: str
    label: str


class HistorySnapshot(TypedDict):
    canUndo: bool
    canRedo: bool
    undoItems: list[HistoryMenuItem]
    redoItems: list[HistoryMenuItem]


PersistentItemGetter = Callable[[Any, int], HistoryMenuItem | None]
PersistentAvailability = Callable[[Any, int], bool]


def history_snapshot_for_field(
    editor: Any,
    *,
    field_index: int | None,
    session: EditorSession | None,
    history_size: object,
    can_persistent_undo: PersistentAvailability,
    latest_persistent_undo_item: PersistentItemGetter,
) -> HistorySnapshot:
    """Return current executable undo/redo history for one editor field."""
    limit = normalize_editor_history_size(history_size)
    undo_items: list[HistoryMenuItem] = []
    redo_items: list[HistoryMenuItem] = []
    if field_index is not None and session is not None and session.field_index == field_index:
        session.undo_history.set_max_entries(limit)
        session.redo_history.set_max_entries(limit)
        undo_items = _items_from_entries("undo", session.undo_history.entries, limit, "Previous edit")
        redo_items = _items_from_entries("redo", session.redo_history.entries, limit, "Restored edit")
    if field_index is not None and not undo_items and can_persistent_undo(editor, int(field_index)):
        persistent_item = latest_persistent_undo_item(editor, int(field_index))
        if persistent_item is not None:
            undo_items = [persistent_item]
    return {
        "canUndo": bool(undo_items),
        "canRedo": bool(redo_items),
        "undoItems": undo_items,
        "redoItems": redo_items,
    }


def empty_history_snapshot() -> HistorySnapshot:
    """Return an empty snapshot for compatibility wrappers."""
    return {"canUndo": False, "canRedo": False, "undoItems": [], "redoItems": []}


def _items_from_entries(
    prefix: str,
    entries: list[UndoEntry],
    limit: int,
    fallback: str,
) -> list[HistoryMenuItem]:
    return [
        {"id": f"{prefix}:{index}", "label": entry.status_summary.strip() or fallback}
        for index, entry in enumerate(reversed(entries[-limit:]), start=1)
    ]
```

- [x] **Step 5: Add persistent latest item seam**

In `addon/anki_audio_quick_editor/editor_persistent_undo.py`, add:

```python
def latest_persistent_undo_item(editor: Any, field_index: int | None) -> dict[str, str] | None:
    """Return a frontend menu item for the latest executable persistent undo."""
    try:
        operation = _latest_for_field(editor, field_index)
    except PersistentHistoryUnavailableError:
        return None
    if operation is None or field_index is None:
        return None
    if not _old_media_available(editor, operation):
        return None
    field_html = editor.note.fields[int(field_index)]
    if _restored_field_html(field_html, operation) is None:
        return None
    return {
        "id": f"persistent:{operation.id}",
        "label": operation.status_summary.strip() or t("editor.history.undo_empty_label"),
    }
```

In `addon/anki_audio_quick_editor/editor_callbacks.py`, expose it:

```python
_latest_persistent_undo_item = editor_persistent_undo.latest_persistent_undo_item
```

In `addon/anki_audio_quick_editor/editor_dependencies.py`, add to `history_deps`:

```python
        latest_persistent_undo_item=callbacks.latest_persistent_undo_item,
        config=editor_runtime.config,
```

- [x] **Step 6: Route snapshots through frontend refresh**

In `addon/anki_audio_quick_editor/editor_frontend/refresh.py`, add:

```python
def eval_history_snapshot(
    editor: Any,
    field_index: int | None,
    snapshot: dict[str, object],
) -> None:
    """Update undo/redo history details for a specific editor field."""
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetHistorySnapshot && window.__aqeSetHistorySnapshot("
        f"{json.dumps(int(field_index))}, {json.dumps(snapshot)})"
    )
```

Keep `eval_history_availability` as a wrapper:

```python
def eval_history_availability(
    editor: Any,
    field_index: int | None,
    can_undo: bool,
    can_redo: bool,
) -> None:
    """Update undo/redo availability for compatibility callers."""
    eval_history_snapshot(
        editor,
        field_index,
        {
            "canUndo": bool(can_undo),
            "canRedo": bool(can_redo),
            "undoItems": [],
            "redoItems": [],
        },
    )
```

Add:

```python
def history_snapshot_expression(field_index: int, snapshot: dict[str, object]) -> str:
    """Return the frontend expression that reapplies undo/redo history details."""
    return (
        "(() => {"
        "if (!window.__aqeSetHistorySnapshot) return false;"
        "window.__aqeScan && window.__aqeScan();"
        "window.__aqeSetHistorySnapshot("
        f"{json.dumps(int(field_index))}, {json.dumps(snapshot)}"
        ");"
        "return true;"
        "})()"
    )
```

Update the scheduling functions to accept a snapshot dictionary and call `history_snapshot_expression`. Leave `history_availability_expression(...)` as a wrapper that builds an empty-item snapshot.

- [x] **Step 7: Build snapshots from `editor_history` sync points**

In `addon/anki_audio_quick_editor/editor_history.py`, import:

```python
from .audio_state import DEFAULT_EDITOR_HISTORY_SIZE
from .editor_history_snapshot import HistorySnapshot, history_snapshot_for_field
```

Add:

```python
def history_snapshot(editor: Any, session: EditorSession, deps: Any) -> HistorySnapshot:
    """Return the current history snapshot for the session field."""
    config = deps.config(editor) if hasattr(deps, "config") else {}
    return history_snapshot_for_field(
        editor,
        field_index=session.field_index,
        session=session,
        history_size=config.get("editor_history_size", DEFAULT_EDITOR_HISTORY_SIZE),
        can_persistent_undo=deps.can_persistent_undo,
        latest_persistent_undo_item=deps.latest_persistent_undo_item,
    )
```

Change `sync_history_availability` to:

```python
def sync_history_availability(editor: Any, session: EditorSession, deps: Any) -> None:
    """Reflect current undo/redo history into the editor toolbar."""
    deps.eval_history_snapshot(editor, session.field_index, history_snapshot(editor, session, deps))
```

Change `request_history_availability_after_edit` to pass the same snapshot to `deps.request_history_snapshot_after_edit`.

- [x] **Step 8: Inject initial snapshots**

In `addon/anki_audio_quick_editor/editor_ui.py`, rename the parameter to `initial_history_snapshots_by_field` and set:

```python
        "initialHistorySnapshotsByField": initial_history_snapshots_by_field or {},
        "editorHistorySize": int(editor_history_size),
```

Retain `initialHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }>` in `EditorRuntimeConfig` as a compatibility input, and make `applyInitialHistoryAvailabilityForOrd` convert it into an empty-item snapshot after checking `initialHistorySnapshotsByField`.

In `addon/anki_audio_quick_editor/editor_webview_injection.py`, replace `_initial_history_availability_by_field` with `_initial_history_snapshots_by_field` that calls `history_snapshot_for_field(...)` for every audio field.

- [x] **Step 9: Run backend snapshot tests until they pass**

Run:

```bash
python3 -m pytest tests/test_editor_history_snapshot.py tests/test_editor_integration.py::test_editor_undo_and_redo_restore_audio_references_without_processing -q
```

Expected: selected tests pass after updating existing assertions from `__aqeSetHistoryAvailability` to `__aqeSetHistorySnapshot`.

- [x] **Step 10: Commit Task 2**

```bash
git add addon/anki_audio_quick_editor/editor_session.py addon/anki_audio_quick_editor/editor_history_snapshot.py addon/anki_audio_quick_editor/editor_history.py addon/anki_audio_quick_editor/editor_persistent_undo.py addon/anki_audio_quick_editor/editor_frontend/refresh.py addon/anki_audio_quick_editor/editor_frontend_callbacks.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_callbacks.py addon/anki_audio_quick_editor/editor_webview_injection.py addon/anki_audio_quick_editor/editor_ui.py tests/test_editor_history_snapshot.py tests/test_editor_integration.py
git commit -m "Expose editor history snapshots" -m "Undo and redo split menus need operation labels and exact per-field availability, not only booleans. This adds capped history stacks and a snapshot payload so the frontend can render executable history rows while preserving compatibility for older availability calls." -m "Full check and e2e routines were not run yet; this task ran targeted backend history tests only."
```

## Task 3: History Jump Command

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_history.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `tests/test_editor_actions.py`
- Modify: `tests/test_editor_integration.py`

- [x] **Step 1: Write failing command decoding tests**

In `tests/test_editor_actions.py`, add:

```python
def test_decode_history_jump_payload() -> None:
    payload = decode_editor_command_payload(
        '{"command":"aqe:history-jump","fieldOrd":2,"direction":"undo","steps":5}'
    )

    assert payload.command == "aqe:history-jump"
    assert payload.field_ord == 2
    assert payload.history_direction == "undo"
    assert payload.history_steps == 5


def test_decode_history_jump_rejects_invalid_values() -> None:
    payload = decode_editor_command_payload(
        '{"command":"aqe:history-jump","direction":"sideways","steps":0}'
    )

    assert payload.history_direction is None
    assert payload.history_steps is None
```

- [x] **Step 2: Write failing multi-step integration tests**

In `tests/test_editor_integration.py`, add a helper near existing editor history tests:

```python
def _history_editor(tmp_path: Path) -> tuple[object, EditorSession]:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    for name in ["clip0.mp3", "clip1.mp3", "clip2.mp3", "clip3.mp3"]:
        (media_dir / name).write_bytes(name.encode("utf-8"))

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip3.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(getConfig=lambda _addon: {"editor_history_size": 100}),
    )
    session = EditorSession(
        state=AudioEditState("clip3.mp3"),
        field_index=0,
        current_filename="clip3.mp3",
        status_summary="Third edit",
    )
    session.undo_history.push(AudioEditState("clip0.mp3"), "clip0.mp3", status_summary="Original")
    session.undo_history.push(AudioEditState("clip1.mp3"), "clip1.mp3", status_summary="First edit")
    session.undo_history.push(AudioEditState("clip2.mp3"), "clip2.mp3", status_summary="Second edit")
    SESSIONS[editor] = session
    return editor, session
```

Add:

```python
def test_history_jump_undo_restores_selected_depth(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":2}')

    assert editor.note.fields == ["[sound:clip1.mp3]"]
    assert session.current_filename == "clip1.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip0.mp3"]
    assert [entry.filename for entry in session.redo_history.entries] == ["clip3.mp3", "clip2.mp3"]


def test_history_jump_rejects_out_of_range_without_partial_restore(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":20}')

    assert editor.note.fields == ["[sound:clip3.mp3]"]
    assert session.current_filename == "clip3.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip0.mp3", "clip1.mp3", "clip2.mp3"]
    assert session.redo_history.entries == []
```

- [x] **Step 3: Run failing jump tests**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py::test_decode_history_jump_payload tests/test_editor_actions.py::test_decode_history_jump_rejects_invalid_values tests/test_editor_integration.py::test_history_jump_undo_restores_selected_depth tests/test_editor_integration.py::test_history_jump_rejects_out_of_range_without_partial_restore -q
```

Expected: failures mention missing payload fields or missing command handling.

- [x] **Step 4: Decode history jump payload**

In `addon/anki_audio_quick_editor/editor_actions.py`, add:

```python
CMD_HISTORY_JUMP = "aqe:history-jump"
HistoryDirection = str
```

Add `CMD_HISTORY_JUMP` to `BRIDGE_COMMANDS`.

Add fields to `EditorCommandPayload`:

```python
    history_direction: HistoryDirection | None = None
    history_steps: int | None = None
```

Add helper:

```python
def _history_direction_or_none(value: Any) -> str | None:
    return value if value in {"undo", "redo"} else None
```

Add to `decode_editor_command_payload`:

```python
        history_direction=_history_direction_or_none(raw_payload.get("direction")),
        history_steps=_int_or_none(raw_payload.get("steps")),
```

- [x] **Step 5: Implement jump validation and restoration**

In `addon/anki_audio_quick_editor/editor_history.py`, add:

```python
def history_jump(editor: Any, payload: Any, deps: Any) -> None:
    """Restore a selected undo/redo history depth."""
    session, _source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    field_ord = getattr(payload, "field_ord", None)
    if field_ord is None or int(field_ord) != int(deps.current_field_index(editor)):
        deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
        return
    direction = getattr(payload, "history_direction", None)
    steps = getattr(payload, "history_steps", None)
    config = deps.config(editor)
    max_steps = normalize_editor_history_size(config.get("editor_history_size", DEFAULT_EDITOR_HISTORY_SIZE))
    if direction not in {"undo", "redo"} or not isinstance(steps, int) or steps < 1 or steps > max_steps:
        deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
        return
    stack = session.undo_history if direction == "undo" else session.redo_history
    if len(stack.entries) < steps:
        deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
        return
    for index in range(steps):
        entry = stack.pop()
        if entry is None:
            deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
            return
        deps.restore_history_entry(
            editor,
            session,
            entry,
            redo_current=direction == "undo",
            status=undo_status_message(entry) if direction == "undo" else redo_status_message(entry),
            suppress_reload=index < steps - 1,
        )
```

Do not add batching or `suppress_reload` in this implementation. The initial stack-length validation prevents partial mutation, and repeated restore calls may reuse the existing reload behavior.

Add locale key to all catalogs:

```json
  "editor.status.history_selection_unavailable": "That history item is no longer available."
```

- [x] **Step 6: Route command through bridge dependencies**

In `addon/anki_audio_quick_editor/editor_bridge.py`, add to imports:

```python
    CMD_HISTORY_JUMP,
```

Add to `handle_payload_command`:

```python
        CMD_HISTORY_JUMP: lambda: deps.history_jump(editor, payload),
```

In `addon/anki_audio_quick_editor/editor_dependencies.py`, add to `bridge_deps`:

```python
        history_jump=callbacks.history_jump,
```

In `addon/anki_audio_quick_editor/editor_callbacks.py`, expose:

```python
_history_jump = _with_deps(editor_history.history_jump, _history_deps)
```

- [x] **Step 7: Run jump tests until they pass**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py::test_decode_history_jump_payload tests/test_editor_actions.py::test_decode_history_jump_rejects_invalid_values tests/test_editor_integration.py::test_history_jump_undo_restores_selected_depth tests/test_editor_integration.py::test_history_jump_rejects_out_of_range_without_partial_restore -q
```

Expected: selected tests pass.

- [x] **Step 8: Commit Task 3**

```bash
git add addon/anki_audio_quick_editor/editor_actions.py addon/anki_audio_quick_editor/editor_bridge.py addon/anki_audio_quick_editor/editor_history.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_callbacks.py addon/anki_audio_quick_editor/locales/*.json tests/test_editor_actions.py tests/test_editor_integration.py
git commit -m "Add editor history jump command" -m "Undo and redo menus need to restore a selected history depth atomically instead of replaying user clicks from the frontend. This adds a validated payload command that checks field, direction, configured limit, and stack depth before mutation, preserving existing restore behavior for the final state." -m "Full check and e2e routines were not run yet; this task ran targeted bridge and editor history tests only."
```

## Task 4: Frontend History Split Buttons

**Files:**
- Modify: `settings_ui/src/editor-inline/editor-runtime-types.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/globals.d.ts`
- Modify: `settings_ui/src/editor-inline/window-contract.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/command-actions.ts`
- Create: `settings_ui/src/editor-inline/HistorySplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/tests/editor-inline.window-contract.test.ts`
- Modify: `settings_ui/tests/editor-inline.integration.toolbar-controls.behavior.ts`

- [x] **Step 1: Write failing frontend split-button tests**

In `settings_ui/tests/editor-inline.integration.toolbar-controls.behavior.ts`, replace the first test with snapshot-aware expectations and add a menu test:

```typescript
  it("disables undo and redo until history snapshots become available and updates their tooltips", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const undoButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-undo"]')!;
    const redoButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-redo"]')!;

    expect(undoButton).toBeDisabled();
    expect(redoButton).toBeDisabled();

    window.__aqeSetHistorySnapshot?.(0, {
      canUndo: true,
      canRedo: false,
      undoItems: [{ id: "undo:1", label: "Shorten pauses" }],
      redoItems: [],
    });

    expect(undoButton).not.toBeDisabled();
    expect(redoButton).toBeDisabled();
  });

  it("opens undo history and dispatches a one-based history jump payload", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetHistorySnapshot?.(0, {
      canUndo: true,
      canRedo: false,
      undoItems: [
        { id: "undo:1", label: "Denoise" },
        { id: "undo:2", label: "Shorten pauses" },
      ],
      redoItems: [],
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-undo-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-history-0-undo-2"]')!.click();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:history-jump",
      direction: "undo",
      fieldOrd: 0,
      steps: 2,
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });
```

Update `settings_ui/tests/editor-inline.window-contract.test.ts` expected names to include:

```typescript
      "__aqeSetHistorySnapshot",
```

- [x] **Step 2: Run failing frontend tests**

Run:

```bash
cd settings_ui && npm test -- editor-inline.integration.toolbar-controls.behavior.ts editor-inline.window-contract.test.ts
```

Expected: failures mention missing `__aqeSetHistorySnapshot`, missing split menu, or missing `aqe-history` row.

- [x] **Step 3: Add frontend history types and state**

In `settings_ui/src/editor-inline/editor-runtime-types.ts`, add:

```typescript
export interface EditorHistoryMenuItem {
  id: string;
  label: string;
}

export interface EditorHistorySnapshot {
  canRedo: boolean;
  canUndo: boolean;
  redoItems: EditorHistoryMenuItem[];
  undoItems: EditorHistoryMenuItem[];
}
```

Change `initialHistoryAvailabilityByField` to:

```typescript
  initialHistorySnapshotsByField?: Record<number, EditorHistorySnapshot>;
  editorHistorySize?: number;
```

Keep `initialHistoryAvailabilityByField` as optional during migration if existing tests rely on it.

In `settings_ui/src/editor-inline/types.ts`, export `EditorHistoryMenuItem` and `EditorHistorySnapshot`.

In `settings_ui/src/editor-inline/globals.d.ts`, change:

```typescript
    __aqeHistorySnapshotsByField?: Record<number, EditorHistorySnapshot> | undefined;
    __aqeSetHistorySnapshot?: ((ord: number, snapshot: EditorHistorySnapshot) => void) | undefined;
```

Keep `__aqeSetHistoryAvailability` declared as compatibility.

- [x] **Step 4: Implement snapshot actions**

In `settings_ui/src/editor-inline/control-actions.ts`, add helper:

```typescript
export function emptyHistorySnapshot(): EditorHistorySnapshot {
  return { canRedo: false, canUndo: false, redoItems: [], undoItems: [] };
}
```

Add:

```typescript
export function setHistorySnapshot(ord: number, snapshot: EditorHistorySnapshot): void {
  if (!window.__aqeHistorySnapshotsByField) {
    window.__aqeHistorySnapshotsByField = {};
  }
  const limit = Math.min(100, Math.max(1, Math.trunc(editorRuntimeConfig().editorHistorySize ?? 100)));
  window.__aqeHistorySnapshotsByField[ord] = {
    canRedo: !!snapshot.canRedo,
    canUndo: !!snapshot.canUndo,
    redoItems: snapshot.redoItems.slice(0, limit),
    undoItems: snapshot.undoItems.slice(0, limit),
  };
  const controls = controlsForOrd(ord);
  if (controls) {
    controls.dataset.aqeCanUndo = snapshot.canUndo ? "true" : "false";
    controls.dataset.aqeCanRedo = snapshot.canRedo ? "true" : "false";
  }
  updateHistoryButtonState(ord, "aqe:undo");
  updateHistoryButtonState(ord, "aqe:redo");
  syncRecordingControls(ord);
}

export function setHistoryAvailability(ord: number, canUndo: boolean, canRedo: boolean): void {
  setHistorySnapshot(ord, {
    canRedo: !!canRedo,
    canUndo: !!canUndo,
    redoItems: [],
    undoItems: [],
  });
}

export function historySnapshot(ord: number): EditorHistorySnapshot {
  return window.__aqeHistorySnapshotsByField?.[ord] ?? emptyHistorySnapshot();
}
```

Update `historyAvailability` to read from `historySnapshot(ord)`.

Update `applyInitialHistoryAvailabilityForOrd` to consume `initialHistorySnapshotsByField` first:

```typescript
  const initialSnapshot = editorRuntimeConfig().initialHistorySnapshotsByField?.[ord];
  if (initialSnapshot) {
    setHistorySnapshot(ord, initialSnapshot);
    delete editorRuntimeConfig().initialHistorySnapshotsByField?.[ord];
    return;
  }
```

- [x] **Step 5: Install window contract**

In `settings_ui/src/editor-inline/window-contract.ts`, import `setHistorySnapshot`, add `"__aqeSetHistorySnapshot"` to `EDITOR_WINDOW_CONTRACT_NAMES`, and add:

```typescript
  window.__aqeSetHistorySnapshot = setHistorySnapshot;
```

- [x] **Step 6: Create `HistorySplitButton.svelte`**

Create `settings_ui/src/editor-inline/HistorySplitButton.svelte`:

```svelte
<script lang="ts">
  import { Popover } from "bits-ui";
  import { t } from "../lib/i18n.js";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitButtonPrimary from "./SplitButtonPrimary.svelte";
  import { send } from "./actions.js";
  import { historySnapshot } from "./control-actions.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import type { ButtonSpec, EditorHistoryMenuItem, FieldTarget } from "./types.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";

  const {
    button,
    disabledTitle,
    displayMode,
    target,
  }: {
    button: ButtonSpec;
    disabledTitle?: string;
    displayMode: EditorButtonDisplayMode;
    target: FieldTarget;
  } = $props();

  let open = $state(false);
  const direction = $derived(button.command === "aqe:redo" ? "redo" : "undo");
  const slug = $derived(COMMAND_SLUGS[button.command]);
  const snapshot = $derived(historySnapshot(target.ord));
  const items = $derived(direction === "undo" ? snapshot.undoItems : snapshot.redoItems);
  const available = $derived(direction === "undo" ? snapshot.canUndo : snapshot.canRedo);
  const primaryDisabled = $derived(!available);
  const primaryTitle = $derived(button.title);
  const menuTitle = $derived(t("editor.history.menu_title", { label: button.label }));

  function dispatchPrimary(): void {
    send(button.command, target.node, target.ord);
  }

  function dispatchJump(index: number): void {
    open = false;
    send("aqe:history-jump", target.node, target.ord, {
      command: "aqe:history-jump",
      direction,
      fieldOrd: target.ord,
      steps: index + 1,
    });
  }

  function rowLabel(item: EditorHistoryMenuItem): string {
    return item.label || (direction === "undo" ? t("editor.history.undo_empty_label") : t("editor.history.redo_empty_label"));
  }
</script>

<Popover.Root bind:open>
  <span class="aqe-split-button">
    <SplitButtonPrimary
      ariaLabel={primaryTitle}
      command={button.command}
      disabled={primaryDisabled}
      disabledReason={disabledTitle}
      {displayMode}
      icon={button.icon}
      label={button.label}
      onClick={dispatchPrimary}
      ord={target.ord}
      primaryClass="aqe-button aqe-split-primary"
      slug={slug}
      title={primaryTitle}
    />
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-aqe-tooltip-content={menuTitle}
      data-testid={`aqe-split-${target.ord}-${slug}-menu`}
      disabled={!available || items.length === 0}
      aria-label={menuTitle}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-ui-root aqe-split-popover aqe-history-split-popover"
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-${slug}-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow class="aqe-split-popover-arrow" height={8} width={16} />
      <div class="aqe-history-menu" role="menu" aria-label={menuTitle}>
        {#each items as item, index (item.id)}
          <button
            class="aqe-history-menu-item"
            data-testid={`aqe-history-${target.ord}-${direction}-${index + 1}`}
            role="menuitem"
            type="button"
            onclick={() => dispatchJump(index)}
          >
            {rowLabel(item)}
          </button>
        {/each}
      </div>
    </Popover.Content>
  </span>
</Popover.Root>
```

Add minimal styles in the component or shared editor CSS:

```css
.aqe-history-menu {
  display: grid;
  gap: 2px;
  max-height: 280px;
  overflow: auto;
  min-width: 180px;
}

.aqe-history-menu-item {
  background: transparent;
  border: 0;
  color: inherit;
  font: inherit;
  padding: 6px 8px;
  text-align: left;
  width: 100%;
}

.aqe-history-menu-item:hover,
.aqe-history-menu-item:focus-visible {
  background: var(--button-hover-bg, rgba(127, 127, 127, 0.14));
}
```

- [x] **Step 7: Use history split buttons in `EditorControls.svelte`**

Import:

```svelte
  import HistorySplitButton from "./HistorySplitButton.svelte";
```

Add a render branch before generic split buttons:

```svelte
      {:else if item.button.command === "aqe:undo" || item.button.command === "aqe:redo"}
        <HistorySplitButton
          button={item.button}
          displayMode={buttonDisplayMode(item.button.command, buttonModes)}
          disabledTitle={disabledTitle(item.button.command)}
          {target}
        />
```

Keep `initialButtonDisabled` for compatibility with plain buttons, but Undo/Redo should no longer hit the plain `EditorToolbarButton` branch.

- [x] **Step 8: Ensure history jump participates in post-edit playback intent**

In `settings_ui/src/editor-inline/command-actions.ts`, update `shouldPlayAfterSuccessfulEdit`:

```typescript
function shouldPlayAfterSuccessfulEdit(command: EditorCommand): boolean {
  return PROCESSING_COMMANDS.has(command) || command === "aqe:undo" || command === "aqe:redo" || command === "aqe:history-jump";
}
```

In `settings_ui/src/editor-inline/editor-runtime-types.ts`, change the payload command type to include the jump command without adding it to toolbar button visibility:

```typescript
export interface EditorCommandPayload {
  command: EditorCommand | "aqe:history-jump" | "aqe:open-url" | "aqe:post-edit-playback-ready";
  direction?: "undo" | "redo";
  fieldOrd?: number;
  generation?: number;
  steps?: number;
```

- [x] **Step 9: Run frontend history tests until they pass**

Run:

```bash
cd settings_ui && npm test -- editor-inline.integration.toolbar-controls.behavior.ts editor-inline.window-contract.test.ts
```

Expected: selected tests pass.

- [x] **Step 10: Commit Task 4**

```bash
git add settings_ui/src/editor-inline/editor-runtime-types.ts settings_ui/src/editor-inline/types.ts settings_ui/src/editor-inline/globals.d.ts settings_ui/src/editor-inline/window-contract.ts settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/command-actions.ts settings_ui/src/editor-inline/HistorySplitButton.svelte settings_ui/src/editor-inline/EditorControls.svelte settings_ui/tests/editor-inline.window-contract.test.ts settings_ui/tests/editor-inline.integration.toolbar-controls.behavior.ts
git commit -m "Render undo redo history split buttons" -m "Users need visible operation history at the undo and redo controls, while primary clicks must remain fast one-step actions. This adds snapshot-backed split buttons that render field-local history rows and dispatch validated jump payloads without changing the existing toolbar visibility model." -m "Full check and e2e routines were not run yet; this task ran targeted frontend history tests only."
```

## Task 5: Integration, E2E, And Documentation Sync

**Files:**
- Modify: `e2e/test_editor_processing_workflow.py`
- Modify: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`

- [x] **Step 1: Add or update e2e coverage**

Add these helpers near `_button_selector` usage in `e2e/test_editor_processing_workflow.py`:

```python
def _history_menu_selector(direction: str, steps: int, ord_: int = 0) -> str:
    return f'[data-testid="aqe-history-{ord_}-{direction}-{steps}"]'
```

Add this test after `test_processing_undo_redo_and_new_edit_clears_redo`:

```python
def test_processing_history_split_buttons_jump_multiple_steps(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_history_split_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, editor_history_size=100)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)

        first_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            source.name,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Increased speed to x1.5.",
            timeout=10.0,
        )
        second_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            first_generated,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Increased volume by 15 dB.",
            timeout=10.0,
        )
        third_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:slower",
            second_generated,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Decreased speed to x0.67.",
            timeout=10.0,
        )

        click_selector(editor.web, '[data-testid="aqe-split-0-undo-menu"]', timeout=5.0)
        wait_for_selector(editor.web, _history_menu_selector("undo", 2), timeout=5.0)
        undo_labels = wait_for_js_condition(
            editor.web,
            """
            Array.from(document.querySelectorAll('[data-testid^="aqe-history-0-undo-"]'))
              .map((node) => node.textContent)
            """,
            lambda labels: len(labels) >= 2,
            timeout=5.0,
        )
        assert undo_labels[:2] == ["Increased volume by 15 dB.", "Increased speed to x1.5."]
        click_selector(editor.web, _history_menu_selector("undo", 2), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == first_generated,
            timeout=5.0,
            message="Undo history jump did not restore the selected generated reference",
        )

        click_selector(editor.web, '[data-testid="aqe-split-0-redo-menu"]', timeout=5.0)
        wait_for_selector(editor.web, _history_menu_selector("redo", 2), timeout=5.0)
        click_selector(editor.web, _history_menu_selector("redo", 2), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == third_generated,
            timeout=5.0,
            message="Redo history jump did not restore the latest generated reference",
        )
    finally:
        editor.set_note(None)
        parent.close()
```

- [x] **Step 2: Update behavior rules doc**

In `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`, update:

```markdown
| Plain modification buttons | `aqe:delete-selection`, `aqe:delete-rest` |
| History split buttons | `aqe:undo`, `aqe:redo` |
```

In the Undo And Redo section, add:

```markdown
- Undo and redo render as split buttons: primary restores one step, and the menu lists the configured number of previous or redoable operation summaries up to the hard cap of 100.
- Selecting a history menu item applies the required number of undo or redo steps only after Python validates the full requested depth.
- The editor history size setting controls in-memory undo/redo retention and menu row count.
```

- [x] **Step 3: Run focused frontend, backend, and contract checks**

Run:

```bash
python3 scripts/dev.py contracts-check
python3 -m pytest tests/test_editor_history_snapshot.py tests/test_editor_actions.py tests/test_editor_integration.py tests/test_config_migration_defaults.py tests/test_config_migration_normalization.py tests/test_audio_state.py tests/test_contract_generation.py -q
cd settings_ui && npm test -- editor-inline.integration.toolbar-controls.behavior.ts editor-inline.window-contract.test.ts app.settings.test.ts settings-state.test.ts
```

Expected: all focused checks pass.

- [x] **Step 4: Run full reusable QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: full check passes. If it fails, fix only failures related to this feature and rerun the failing command.

- [x] **Step 5: Run e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: e2e passes, including the new history split-button workflow.

- [x] **Step 6: Commit Task 5**

```bash
git add e2e/test_editor_processing_workflow.py EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md
git commit -m "Verify undo redo history split workflow" -m "The split-button history feature changes a core editor recovery path, so it needs real editor coverage and updated behavior rules. This records the jump workflow in e2e and keeps the modification-button contract aligned with the new configurable history behavior." -m "Full check and e2e routines were run for this workflow."
```

## Final Verification

- [x] Run:

```bash
git status --short
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

- [x] Confirm `git status --short` contains only intentional changes before any final commit or PR.
- [x] If `python3 scripts/dev.py check` or `python3 scripts/dev.py test-e2e` cannot be run, the final commit message body must explicitly mention that full check and e2e routines were not run and why.

## Self-Review Notes

Spec coverage:

- Split primary behavior is covered by Task 4.
- History menu rows, labels, per-field snapshots, and max 100 cap are covered by Tasks 2 and 4.
- Configurable history size is covered by Task 1 and enforced by Task 2.
- Jump command validation and no partial mutation are covered by Task 3.
- Persistent undo menu contribution is covered by Task 2.
- Tests and e2e coverage are covered by Tasks 1 through 5.

Placeholder scan:

- No `TBD`, `TODO`, or unspecified implementation steps are intentionally left in this plan.

Type consistency:

- The plan uses `editor_history_size` for persisted config, `editorHistorySize` for runtime frontend config, `EditorHistorySnapshot` for frontend state, and `HistorySnapshot` for Python payloads.
