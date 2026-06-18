# Playback State Machine Risk Audit

Date: 2026-06-18

This document catalogs the remaining backend playback state-machine problems after the editor session split. It is not an implementation plan. It explains why the remaining direct playback-state writes are risky and how they affect testing, operations, and future maintenance.

## Summary

The Python editor backend now has a focused `PlaybackState` object, but most playback transitions are still implicit. `PlaybackState.stop()` is centralized, while start, pause, prepare, ready, failure, HTML playback, cursor restart, media reset, and settings reload paths still write combinations of `active`, `paused`, `preparing`, `generation`, `temp_path`, and `preserve_status` directly.

The result is a state machine by convention. Each caller has to remember the correct field bundle for a transition. That works while every path is maintained carefully, but the invariants are not encoded in the state object.

## Current Model

Backend playback state is represented by these fields in `addon/anki_audio_quick_editor/editor_session_state.py`:

- `active`: some playback flow is considered active.
- `paused`: playback is paused.
- `preparing`: a native segment render is in progress.
- `generation`: invalidates stale native segment callbacks.
- `temp_path`: temporary rendered playback segment path.
- `preserve_status`: suppresses normal playback status replacement, mainly for post-edit playback.

The effective states are boolean combinations:

- Stopped: `active=False`, `paused=False`, `preparing=False`.
- Native direct playing: `active=True`, `paused=False`, `preparing=False`.
- Native segment preparing: `active=True`, `paused=False`, `preparing=True`.
- Native segment playing: `active=True`, `paused=False`, `preparing=False`, `temp_path` set.
- HTML playing: `active=True`, `paused=False`, `preparing=False`.
- HTML paused: `active=True`, `paused=True`, `preparing=False`.

Only segment preparation is treated as busy by `editor_runtime.is_busy()`. Plain active playback is intentionally not busy.

## Remaining Direct Writes

Important production paths still mutate playback fields directly:

- `editor_playback.py`: native direct start, segment preparation, segment ready, segment failure, temporary segment cleanup, and HTML cursor restart.
- `editor_playback_request.py`: native pause/resume plus frontend-owned HTML playback start/pause.
- `editor_session.py`: processing and note-load reset paths clear only selected playback flags.
- `editor_runtime.py`: media reset and runtime stop paths overlap with session-level cleanup.
- `editor_settings_actions.py`: settings-save reload clears playback preparation after stopping playback.

These writes are not inherently wrong, but they make each caller responsible for the same transition invariants.

## Risk Areas

### Partial state updates

Several transitions require multiple fields to move together. For example, a start transition must normally set `active=True`, `paused=False`, clear `preparing`, and set `preserve_status` based on the request source. If one path omits one field, the session can enter an impossible or misleading state.

Concrete examples:

- Native direct playback sets `active`, `paused`, and `preserve_status`.
- Native segment preparation increments `generation` and sets `preparing`, `active`, `paused`, and `preserve_status`.
- Segment ready clears `preparing`, stores `temp_path`, and marks playback active.
- Segment failure clears `preparing`, `active`, and `paused`.
- HTML pause/start manually writes similar bundles in a different module.

Because these bundles are open-coded, new playback behavior can easily update only the visible flag and miss a hidden invariant.

### Ambiguous meaning of `active`

`active=True` means both "currently playing" and "preparing to play". The system distinguishes those cases with `preparing`, and only `preparing` contributes to `is_busy()`.

That behavior is deliberate, but it is easy to misread. A caller that checks only `active` cannot tell whether audio is playing, paused, HTML-owned, or still rendering. A caller that sets `active=True` without setting `preparing` may accidentally bypass busy handling.

### Split stop semantics

There are two `stop_session_playback()` implementations:

- `editor_playback.stop_session_playback(session, deps)` stops playback, stops audio, and cleans temporary playback files.
- `editor_runtime.stop_session_playback(session)` also resets learner playback state.

Both are valid in their current contexts, but the shared name hides different side effects. A future caller can pick the wrong one and either skip learner playback reset or reset more state than intended.

### Generation policy is implicit

`generation` protects native segment rendering from stale worker callbacks. It is bumped by stop paths and before segment preparation. Segment ready/failure callbacks compare their captured generation to the current one.

The policy is correct in spirit, but not self-documenting:

- Tests assert exact generation counts, so implementation details leak into test expectations.
- Segment failure does not bump generation; that assumes the worker reports only one terminal callback for a generation.
- Generic stop operations invalidate native segment callbacks even when the stop was not related to segment rendering.

These choices may be acceptable, but they should be encoded behind named transitions instead of repeated as call-site discipline.

### Temporary file lifecycle is coupled to caller discipline

`temp_path` is set when a rendered segment becomes active and cleared during cleanup. The file deletion side effect lives outside `PlaybackState.stop()` because it needs filesystem work.

That split is reasonable, but it means callers must remember to pair state transitions with cleanup. Missed cleanup can leave temporary playback directories behind; early cleanup can delete a segment still expected by playback.

### Status preservation is a hidden playback mode

`preserve_status` changes whether playback overwrites editor status text. It matters most for post-edit playback, where the edit result status should remain visible.

Today the request source is reduced to this boolean. After that point the code no longer knows whether status is being preserved because of post-edit playback or another future source. A stale `preserve_status=True` can suppress useful playback/error status; a missed `True` can overwrite the edit status.

### HTML and native playback share flags but not semantics

Native playback can involve Anki audio, temporary segment rendering, generation checks, and filesystem cleanup. HTML playback is frontend-owned and mostly updates backend bookkeeping.

Both write the same fields. This keeps the frontend/backend interface small, but it under-describes the actual state. For example, `active=True, paused=False, preparing=False` can mean native direct playback, native rendered segment playback, HTML playback, or HTML cursor restart.

## Testing Impact

The existing tests provide useful characterization coverage, especially for stale segment cleanup, busy behavior, HTML playback, cursor restart, and post-edit playback status preservation. The problem is that many tests assert raw field combinations and exact generation values.

That creates three forms of friction:

- Refactors become noisy because changing how state is represented breaks many tests even when behavior is unchanged.
- Tests encode implementation details, such as exact generation increments, instead of named transition outcomes.
- Invalid combinations are not impossible by construction; tests only cover the paths that already exist.

A cleaner state API would let production code use named transitions and let tests assert behavior like "segment preparation started", "HTML playback paused", "stale segment ignored", or "stop invalidated pending segment callbacks".

## Performance And Operational Impact

This is not a hot-path CPU performance problem. The state writes themselves are cheap.

The operational risks are about correctness and cleanup:

- Stale `preparing=True` can make the editor appear busy after playback should be done.
- Missed temp cleanup can leave generated playback files/directories on disk.
- Incorrect generation handling can let stale worker callbacks affect current playback or force unnecessary cleanup.
- Incorrect `preserve_status` can hide important user-visible status or overwrite edit-result status.
- Split stop semantics can leave learner playback UI state out of sync with backend playback state.

These failures would be reported as stuck controls, confusing status text, playback UI desynchronization, audio continuing after a reset, or accumulated temporary files.

## Why Cleanup Matters

The current implementation works because callers follow unwritten rules. The risk is that playback behavior is already spread across request handling, native playback, HTML playback, cursor updates, processing resets, media resets, settings reload, and learner recording interaction.

Centralizing the remaining playback-only writes behind explicit transition helpers would make those rules executable:

- One place defines legal state combinations.
- Callers describe intent instead of field mechanics.
- Tests can focus on transitions and outcomes.
- Future playback features can extend the model without copying field bundles.

