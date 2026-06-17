# P6 Resolution Plan: Decompose `editor_session.py` Mutable State Bag

**Problem:** `EditorSession` is a 35-field mutable dataclass with no invariant enforcement, mutated by 20+ files. Any function with a reference can write any field.

**Goal:** Reduce blast radius of mutations, enforce domain invariants at runtime, and eliminate the copy-pasted "post-render replacement" pattern.

---

## Current State

- 35 attributes spanning 8 distinct domains
- 20+ files mutate `EditorSession` fields directly
- 4 near-identical `_replace_*_session_state` functions across `editor_processing.py`, `editor_region_delete.py`, `editor_special_transforms.py`, `editor_history.py`
- 2 different `stop_session_playback` functions with different behavior
- No invariant enforcement — implicit rules exist only in code comments and developer knowledge

### Attribute-to-Domain Mapping

| Domain | Attributes | Primary Writers |
|--------|-----------|----------------|
| Identity | `note_id` | 3 files |
| Audio Edit | `state`, `field_index`, `current_filename`, `source_mtime_ns`, `cursor_ms` | 7 files |
| Undo/Redo | `undo_history`, `redo_history` | 6 files |
| Processing | `processing`, `processing_generation`, `next_status_summary` | 10 files |
| Analysis | `analysis_busy`, `analysis_busy_fields`, `analysis_generation`, `analysis_generations_by_field` | 4 files |
| Graph/Viz | `graph_active_fields`, `visualized_filename`, `visualized_duration_ms`, `visualized_filenames_by_field`, `visualized_durations_by_field` | 6 files |
| Playback | `playback_active`, `playback_paused`, `playback_preparing`, `preserve_status_during_playback`, `playback_generation`, `temp_playback_path` | 5 files |
| Post-Edit Playback | `post_edit_playback_generation`, `pending_post_edit_playback_*` (4 fields) | 8 files |
| Status | `status_summary`, `pending_status` | 7 files |
| Learner Recording | `learner_recording`, `learner_recording_controller` | 4 files |

---

## Invariant Catalog

Every invariant below is currently enforced by convention (caller discipline) rather than by type or method. The refactoring must make each one structurally enforced or assertion-guarded.

### Cross-domain invariants

| ID | Invariant | Current enforcement | Evidence |
|----|-----------|-------------------|---------|
| X1 | `processing=True` → `playback_active=False` and `playback_paused=False` | Every caller that sets `processing=True` immediately clears both playback flags (7 call sites) | `editor_processing.py:120-121`, `editor_special_transforms.py:203-204`, `editor_region_delete.py:155-156`, `editor_presets.py:76-77`, `editor_settings_actions.py:73-74` |
| X2 | `playback_active=True` → `processing=False` | Every playback entry checks `is_busy()` which includes `processing` | `editor_playback.py:139`, `editor_playback_request.py` |
| X3 | `processing=True` → `analysis_busy=False` and `analysis_busy_fields` empty | Every processing entry calls `cancel_graph_analysis_for_processing` before setting `processing=True` | `editor_processing.py:78`, `editor_special_transforms.py:191`, `editor_region_delete.py` (via `delete_selection_with_request`), `editor_presets.py:65` |
| X4 | `undo_history.push(current_state)` happens before any overwrite of `state`/`current_filename` | Every `_replace_*_session_state` function pushes first | `editor_processing.py:321`, `editor_region_delete.py:299`, `editor_special_transforms.py:299`, `editor_history.py:202-212` |
| X5 | `redo_history.clear()` happens on every new user edit (not on undo/redo) | All `_replace_*_session_state` functions clear redo; undo/redo paths push to the opposite stack | Same files as X4 |
| X6 | `post_edit_playback_generation` bumps on every edit | Every edit path increments it | 8 call sites across processing, region delete, special transforms, history, persistent undo, presets |

### Single-domain invariants

| ID | Invariant | Current enforcement |
|----|-----------|-------------------|
| D1 | `analysis_busy == bool(analysis_busy_fields)` | `begin_field_analysis` sets busy=True after add; `end_field_analysis` sets busy=bool(fields) after discard; `cancel_graph_analysis_for_processing` clears both |
| D2 | `processing_generation` is monotonically increasing | Only modified by `begin_processing_guard` (+1), `invalidate_processing_guard` (+1), and `reset_for_note_load` (+1) |
| D3 | `learner_recording.generation` is monotonically increasing | `begin_learner_recording_state` and `clear_learner_recording_state` both bump by +1 |
| D4 | `playback_generation` is monotonically increasing | Only bumped by `stop_session_playback` and `start_playback_from_cursor` |
| D5 | `graph_active_fields` accumulates; only cleared on note change | Added by `begin_field_analysis`; cleared only in `reset_for_note_load` |
| D6 | `temp_playback_path` is set in `playback_segment_ready` and cleared in `cleanup_temp_playback` | Explicit set/clear pair |

### Invariants that SHOULD hold but are NOT enforced

| ID | Gap | Risk |
|----|-----|------|
| G1 | Nothing prevents `processing=True` and `playback_active=True` simultaneously if a caller forgets the clearing pattern | Session stuck or undefined behavior |
| G2 | `pending_status` is never explicitly consumed after injection — relies on `reset_for_note_load` to eventually clear | Stale status re-injected on unexpected editor reload |
| G3 | `temp_playback_path` cleanup depends on explicit `stop_session_playback` — WeakKeyDictionary GC does not trigger it | Temp file leak on editor close without explicit stop |
| G4 | Processing entry guard is caller-side (`if session.processing: return`) — no centralized check | A new entry point that forgets the guard allows concurrent processing |

---

## Plan

### Phase 0: Add characterization tests (prerequisite)

Before changing any structure, lock down current behavior with characterization tests that exercise the mutation patterns through the real API surface.

**Tests to write:**
1. **Processing lifecycle (X1, X4, X5, X6)** — `begin_processing_guard` → render → `_replace_standard_render_session_state` → verify undo pushed (X4), redo cleared (X5), processing=False, playback flags cleared (X1), post_edit_playback_generation bumped (X6).
2. **Undo/redo roundtrip (X4, X5)** — push state A, push state B, undo → verify redo gets B (X4 push semantics), undo again → verify redo gets A, redo → verify state restores B. Verify redo is NOT cleared on undo/redo paths (X5 only applies to new edits).
3. **Stale guard invalidation (D2)** — begin guard, invalidate, check `is_current_processing_guard` returns False. Verify generation only increases.
4. **Analysis busy invariant (D1)** — begin analysis on field 0, begin on field 1, end field 0 → verify `analysis_busy` still True, end field 1 → verify `analysis_busy` False. Verify `cancel_graph_analysis_for_processing` clears both.
5. **Post-render replacement pattern (X1, X4, X5, X6)** — verify all 3 `_replace_*` functions (processing, region delete, noise reduction) produce identical field state for the common subset AND all enforce X1 (playback cleared), X4 (undo pushed), X5 (redo cleared), X6 (post-edit bumped).
6. **Playback lifecycle (D4)** — start → pause → resume → stop, verify generation only increases (monotonic).
7. **Learner recording lifecycle (D3)** — begin → complete → play → stop → clear, verify generation only increases.
8. **Processing-playback mutual exclusion (X1, X2)** — verify that `is_busy()` returns True when processing is active, and that every code path that sets `processing=True` also clears playback flags.
9. **Graph active fields accumulation (D5)** — verify `graph_active_fields` grows across multiple analyses but is cleared on `reset_for_note_load`.

**Location:** `tests/test_editor_session.py`

**Verification:** `python3 scripts/dev.py test -- test_editor_session`

---

### Phase 1: Extract domain sub-state dataclasses with invariant enforcement

Split `EditorSession` into domain objects. Each domain enforces its own invariants through methods, not raw field assignment. Cross-domain invariants (X1-X6) are enforced by `EditorSession`-level methods that coordinate domains.

#### Domain sub-state classes

```python
@dataclass
class ProcessingState:
    """Owns invariant D2 (monotonic generation)."""
    active: bool = False
    generation: int = 0
    next_status_summary: str = ""

    def begin_guard(self, field_index: int) -> int:
        """Start a processing guard. Returns new generation. Enforces D2."""
        self.generation += 1
        return self.generation

    def invalidate(self) -> None:
        """Invalidate outstanding guards. Enforces D2."""
        self.generation += 1

    def reset_generation(self) -> None:
        """Bump generation on note load. Enforces D2."""
        self.generation += 1


@dataclass
class PlaybackState:
    """Owns invariant D4 (monotonic generation)."""
    active: bool = False
    paused: bool = False
    preparing: bool = False
    generation: int = 0
    temp_path: Path | None = None
    preserve_status: bool = False

    def stop(self, *, cleanup_temp: Callable[[Path], None] | None = None) -> None:
        """Stop playback and bump generation. Enforces D4."""
        self.generation += 1
        self.preparing = False
        self.active = False
        self.paused = False
        self.preserve_status = False
        if self.temp_path is not None and cleanup_temp is not None:
            cleanup_temp(self.temp_path)
        self.temp_path = None


@dataclass
class AnalysisState:
    """Owns invariant D1 (busy == bool(busy_fields)) and D5 (graph_active_fields accumulates)."""
    busy: bool = False
    busy_fields: set[int] = field(default_factory=set)
    generation: int = 0
    generations_by_field: dict[int, int] = field(default_factory=dict)
    graph_active_fields: set[int] = field(default_factory=set)

    def begin_field(self, field_index: int, filename: str,
                    filenames_by_field: dict[int, str],
                    durations_by_field: dict[int, int]) -> int:
        """Start analysis for a field. Enforces D1, D5."""
        self.generation += 1
        generation = self.generation
        self.generations_by_field[field_index] = generation
        self.busy_fields.add(field_index)
        self.busy = True  # D1: set after add
        self.graph_active_fields.add(field_index)  # D5: accumulate
        filenames_by_field[field_index] = filename
        durations_by_field.pop(field_index, None)
        return generation

    def end_field(self, field_index: int) -> None:
        """Clear analysis for a field. Enforces D1."""
        self.busy_fields.discard(field_index)
        self.generations_by_field.pop(field_index, None)
        self.busy = bool(self.busy_fields)  # D1: recalculate

    def cancel_all(self) -> None:
        """Cancel all analysis (e.g., before processing). Enforces D1."""
        self.generation += 1
        self.generations_by_field.clear()
        self.busy_fields.clear()
        self.busy = False  # D1: cleared

    def reset(self) -> None:
        """Full reset on note load. Enforces D1, D5."""
        self.generation += 1
        self.busy = False
        self.busy_fields.clear()
        self.generations_by_field.clear()
        self.graph_active_fields.clear()


@dataclass
class GraphVisualizationState:
    """Per-field graph visualization metadata."""
    visualized_filename: str | None = None
    visualized_duration_ms: int | None = None
    filenames_by_field: dict[int, str] = field(default_factory=dict)
    durations_by_field: dict[int, int] = field(default_factory=dict)

    def clear_field(self, field_index: int | None) -> bool:
        """Clear visualization for a field. Returns whether redraw was needed."""
        needs_redraw = (
            field_index is not None
            and (field_index in self.filenames_by_field or self.visualized_filename is not None)
        )
        if needs_redraw:
            self.visualized_filename = None
            self.visualized_duration_ms = None
            self.filenames_by_field.pop(field_index, None)
            self.durations_by_field.pop(field_index, None)
        return needs_redraw

    def reset(self) -> None:
        """Full reset on note load."""
        self.visualized_filename = None
        self.visualized_duration_ms = None
        self.filenames_by_field.clear()
        self.durations_by_field.clear()


@dataclass
class PostEditPlaybackState:
    """Tracks pending post-edit auto-playback."""
    generation: int = 0
    pending_field_index: int | None = None
    pending_generation: int | None = None
    pending_requires_graph_redraw: bool = False
    pending_source_filename: str | None = None

    def bump(self) -> None:
        """Signal a new edit that should trigger auto-playback. Enforces D6."""
        self.generation += 1

    def reset(self) -> None:
        """Clear pending state on note load."""
        self.generation += 1
        self.pending_field_index = None
        self.pending_generation = None
        self.pending_requires_graph_redraw = False
        self.pending_source_filename = None
```

#### EditorSession composition with cross-domain coordination

```python
@dataclass
class EditorSession:
    note_id: int | None = None
    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    source_mtime_ns: int | None = None
    cursor_ms: int = 0
    undo_history: UndoHistory = field(default_factory=UndoHistory)
    redo_history: UndoHistory = field(default_factory=UndoHistory)
    processing: ProcessingState = field(default_factory=ProcessingState)
    analysis: AnalysisState = field(default_factory=AnalysisState)
    graph: GraphVisualizationState = field(default_factory=GraphVisualizationState)
    playback: PlaybackState = field(default_factory=PlaybackState)
    post_edit_playback: PostEditPlaybackState = field(default_factory=PostEditPlaybackState)
    status_summary: str = ""
    next_status_summary: str = ""
    pending_status: PendingEditorStatus | None = None
    learner_recording: LearnerRecordingState = field(default_factory=LearnerRecordingState)
    learner_recording_controller: Any = None
```

#### Cross-domain coordination methods on EditorSession

```python
def stop_all_playback(self, *, cleanup_temp: Callable | None = None,
                       stop_learner: Callable | None = None) -> None:
    """Stop main + learner playback. Called by editor_runtime.py. Enforces X1."""
    self.playback.stop(cleanup_temp=cleanup_temp)
    if stop_learner is not None:
        stop_learner(self)


def apply_edit_result(
    self,
    new_state: AudioEditState,
    new_filename: str,
    new_status_summary: str,
    *,
    update_source_mtime: bool = False,
    new_source_mtime: int | None = None,
    clear_visualization: bool = False,
) -> bool:
    """Apply a completed edit. Enforces X1, X4, X5, X6. Returns whether graph needs redraw."""
    # X4: push before overwrite
    self.undo_history.push(self.state, self.current_filename, self.status_summary)
    # X5: clear redo on new edit
    self.redo_history.clear()
    self.state = new_state
    self.current_filename = new_filename
    self.field_index = self.field_index  # keep current
    self.status_summary = new_status_summary
    self.next_status_summary = ""
    # X1: processing → clear playback
    self.processing.active = False
    self.cursor_ms = 0
    self.playback.active = False
    self.playback.paused = False
    # X6: bump post-edit generation
    self.post_edit_playback.bump()
    if update_source_mtime:
        self.source_mtime_ns = new_source_mtime
    should_redraw = False
    if clear_visualization:
        should_redraw = self.graph.clear_field(self.field_index)
    else:
        should_redraw = (
            self.field_index in self.analysis.graph_active_fields
            or self.graph.visualized_filename is not None
        )
    return should_redraw
```

**Migration:** Mechanical rename across all 20+ files:
- `session.processing` → `session.processing.active`
- `session.processing_generation` → `session.processing.generation`
- `session.next_status_summary` → `session.processing.next_status_summary`
- `session.analysis_busy` → `session.analysis.busy`
- `session.analysis_busy_fields` → `session.analysis.busy_fields`
- `session.analysis_generation` → `session.analysis.generation`
- `session.analysis_generations_by_field` → `session.analysis.generations_by_field`
- `session.graph_active_fields` → `session.analysis.graph_active_fields`
- `session.playback_active` → `session.playback.active`
- `session.playback_paused` → `session.playback.paused`
- `session.playback_preparing` → `session.playback.preparing`
- `session.playback_generation` → `session.playback.generation`
- `session.temp_playback_path` → `session.playback.temp_path`
- `session.preserve_status_during_playback` → `session.playback.preserve_status`
- `session.post_edit_playback_generation` → `session.post_edit_playback.generation`
- `session.pending_post_edit_playback_*` → `session.post_edit_playback.pending_*`
- `session.visualized_filename` → `session.graph.visualized_filename`
- `session.visualized_duration_ms` → `session.graph.visualized_duration_ms`
- `session.visualized_filenames_by_field` → `session.graph.filenames_by_field`
- `session.visualized_durations_by_field` → `session.graph.durations_by_field`

**Note:** `graph_active_fields` moves into `AnalysisState` because it is only written by analysis functions and read by edit-completion functions to decide graph redraw. It is not a graph-display concern — it is an "analysis has happened" marker.

**Verification:** `python3 scripts/dev.py check`

---

### Phase 2: Migrate callers to `apply_edit_result`

Phase 1 defines `EditorSession.apply_edit_result()`. This phase migrates the 3 callers that have near-identical `_replace_*_session_state` functions. `editor_history.py:restore_history_entry` is excluded because it has different push semantics (pushes to the opposite stack on undo vs redo).

**Migrations:**

```python
# editor_processing.py — _replace_standard_render_session_state becomes:
def _replace_standard_render_session_state(session, field_index, saved_name, updated_state):
    if session is None:
        return False
    session.field_index = field_index
    return session.apply_edit_result(
        updated_state, saved_name,
        session.processing.next_status_summary or session.status_summary,
    )

# editor_region_delete.py — _replace_region_delete_session_state becomes:
def _replace_region_delete_session_state(editor, session, field_index, saved_name, request):
    if session is None:
        return False
    session.field_index = field_index
    saved_path = existing_media_file_path(Path(editor.mw.col.media.dir()), saved_name)
    mtime = saved_path.stat().st_mtime_ns if saved_path is not None else None
    return session.apply_edit_result(
        AudioEditState(source_file=saved_name), saved_name,
        region_operation_status_summary(request),
        update_source_mtime=True, new_source_mtime=mtime,
    )

# editor_special_transforms.py — _replace_noise_reduction_session_state becomes:
def _replace_noise_reduction_session_state(editor, session, field_index, saved_name):
    if session is None:
        return False
    session.field_index = field_index
    saved_path = existing_media_file_path(Path(editor.mw.col.media.dir()), saved_name)
    mtime = saved_path.stat().st_mtime_ns if saved_path is not None else None
    return session.apply_edit_result(
        AudioEditState(source_file=saved_name), saved_name,
        session.processing.next_status_summary or session.status_summary,
        update_source_mtime=True, new_source_mtime=mtime,
        clear_visualization=True,
    )
```

Each caller reduces from ~15 lines of field-by-field mutation to ~5 lines. The invariants (X1, X4, X5, X6) are now enforced by `apply_edit_result` rather than by caller discipline.

**Verification:** `python3 scripts/dev.py check`

---

### Phase 3: Consolidate playback stop

Two `stop_session_playback` functions exist:

| Location | Behavior |
|----------|----------|
| `editor_playback.py` | Clears playback flags + `preserve_status`, cleans temp path |
| `editor_runtime.py` | Same + resets learner playback state |

Consolidate into `PlaybackState.stop()` and `EditorSession.stop_all_playback()`:

```python
class PlaybackState:
    def stop(self) -> None:
        self.generation += 1
        self.preparing = False
        self.active = False
        self.paused = False
        self.preserve_status = False
        if self.temp_path:
            # cleanup logic
            self.temp_path = None

class EditorSession:
    def stop_all_playback(self) -> None:
        self.playback.stop()
        self.reset_learner_playback_state()
```

`editor_playback.py` calls `session.playback.stop()`. `editor_runtime.py` calls `session.stop_all_playback()`.

**Verification:** `python3 scripts/dev.py check`

---

### Phase 4: Add runtime invariant assertions (defensive, not blocking)

Add debug-mode assertions that fire during development and tests, covering the cross-domain invariants that cannot be enforced by individual domain objects alone.

```python
def _assert_invariants(self) -> None:
    """Debug-only cross-domain invariant checks. No-op with python -O."""
    if not __debug__:
        return
    # X1: processing ↔ playback mutual exclusion
    assert not (self.processing.active and self.playback.active), \
        "X1 violated: processing and playback cannot both be active"
    assert not (self.processing.active and self.playback.paused), \
        "X1 violated: processing and playback-paused cannot both be active"
    # X2: playback implies not-processing (symmetric check)
    assert not (self.playback.active and self.processing.active), \
        "X2 violated: playback active while processing"
    # D1: analysis busy consistency
    assert self.analysis.busy == bool(self.analysis.busy_fields), \
        "D1 violated: analysis_busy must match busy_fields membership"
```

Call `_assert_invariants()` at the end of:
- `apply_edit_result` — verifies X1, X5 after every edit
- `stop_all_playback` — verifies X1 after playback stop
- `reset_for_note_load` — verifies clean state after note switch
- `ProcessingState.begin_guard` — verifies X1 before processing starts (via EditorSession wrapper)

These fire only under `python -O`-free runs (development and tests). Production builds with `python -O` skip them entirely.

**Verification:** `python3 scripts/dev.py test -- test_editor_session`

---

### Phase 5: Update architecture contracts

Update `tests/test_architecture/contract_editor/` to reflect the new structure:

1. Update import contract for `editor_session.py` — it now exports domain sub-state types.
2. Add a contract rule: domain sub-state dataclasses (`ProcessingState`, `PlaybackState`, etc.) are only mutated through their own methods or through `EditorSession` methods, not by external direct field assignment.
3. Update Rule 33 / Rule 34 references if any exist for editor session.

**Verification:** `python3 scripts/dev.py check`

---

## Execution Order

```
Phase 0: characterization tests     → verify: python3 scripts/dev.py test -- test_editor_session
Phase 1: extract domain sub-states  → verify: python3 scripts/dev.py check
Phase 2: consolidate replace pattern → verify: python3 scripts/dev.py check
Phase 3: consolidate playback stop   → verify: python3 scripts/dev.py check
Phase 4: runtime invariant asserts   → verify: python3 scripts/dev.py test -- test_editor_session
Phase 5: update architecture contracts → verify: python3 scripts/dev.py check
```

Each phase is independently committable. Phase 0 has zero production code changes. Phases 1-4 are incremental and each leaves the codebase in a passing state.

---

## What This Does NOT Address

- **P1 (DOM-as-state):** This plan only affects the Python side. The frontend state problem is separate.
- **UndoHistory mutability:** `UndoHistory` remains a mutable dataclass with list internals. Making it truly immutable would require a persistent data structure, which is out of scope.
- **Thread safety:** All mutations remain single-threaded (main thread via `deps.main()`). The generation-based guard system stays as-is.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Mechanical rename misses an attribute | Medium | Grep for each attribute name across the codebase before and after Phase 1 |
| Sub-state extraction breaks pickle/serialization | Low | EditorSession is never pickled (WeakKeyDictionary keyed by editor, not serialized) |
| New invariant assertions cause false positives | Low | Assertions are debug-only; existing code already maintains these invariants implicitly |
| `apply_edit_result` signature grows over time | Medium | Use keyword-only args; the existing variation surface is small (2 booleans + 1 optional int) |
