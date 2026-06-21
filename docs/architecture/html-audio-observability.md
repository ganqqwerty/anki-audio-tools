# HTML Audio Observability Contract

This is the canonical source for HTML audio playback observability. Other
documents should link here instead of duplicating transition logging, invariant,
or e2e-observation checklists.

## Scope

This contract covers inline editor browser playback driven by the HTML audio
session model: source playback, selected repeat playback, post-edit autoplay,
and learner recording playback.

The session state is the behavioral source of truth. Browser audio element
state, graph state, field state, and runtime DOM state are observations or UI
projections unless they are converted into explicit session events.

## Why This Exists

The 2026-06 post-edit repeat failure was not visible from sound/no-sound checks
alone. The audio element started and played to `ended`, but a duplicate
post-edit readiness notification moved the session from `starting` back to
`post_edit_waiting` and then `ready`. When the audio element ended, frontend
playback state was already `stopped`, so repeat was skipped.

The useful evidence was the ordered correlation between:

- session transitions and emitted effects
- post-edit readiness notifications
- browser audio element lifecycle events
- projected field playback state at `ended`

Future playback diagnostics must preserve that correlation.

## Required Logs

Log state-machine transitions at event granularity, never per animation frame.
Each transition log must include:

- field ordinal
- source filename
- event type and important event payload
- from-state kind and to-state kind
- request source, cursor, end, loop, region mode, and reset cursor when present
- post-edit generation and source kind when present
- emitted effect types

Log browser audio lifecycle events that can affect state:

- source configured or cleared
- metadata loaded or timed out
- play requested, resolved, or rejected
- native `playing`, `pause`, `ended`, and `error`

Audio lifecycle logs should include field ordinal, `src`, `readyState`,
`currentTimeMs`, `durationMs`, `paused`, and `ended` when available.

Log post-edit bridge lifecycle events:

- pending intent remembered
- readiness checked
- post-edit ready dispatched
- duplicate ready suppressed
- post-edit playback start requested
- playback start result

## Suspicious Invariants

These conditions should be logged as warnings or covered by tests whenever the
code path is touched:

- `PlayResolved` arrives when the session is not `starting`.
- `BoundaryReached` is ignored while repeat is enabled.
- `ended` fires while repeat is enabled but projected playback state is not
  `playing`.
- An active post-edit session for the same request moves back to
  `post_edit_waiting`.
- Session source filename and audio element `src` disagree.
- A generated post-edit source starts playback without an explicit session
  source or post-edit intent.
- A transform finishes with `Browser audio is unavailable` when a generated
  audio file was successfully created.

## Test Observation Contract

Playback e2e tests should observe behavior and state correlation, not only
sound presence. For transform, post-edit, repeat, and cursor workflows, prefer
assertions that cover:

- requested browser play count
- absence of unexpected native or external player playback
- active source filename
- session state kind when observable
- repeat enabled/disabled state
- cursor progress and cursor reset at loop/completion
- absence of `Browser audio is unavailable`
- no extra playback after the expected count or after processing starts

Use pure reducer tests for impossible transition orderings. Use integration
tests for projection and effect execution. Use real Anki e2e for Qt WebEngine
timing, metadata, and `HTMLAudioElement.play()` promise interleavings.

## Logging Budget

Do not log high-frequency animation frames, pointer movement, or progress ticks.
The observable unit is a state transition, browser audio lifecycle event, bridge
message, or warning-worthy invariant.

When a temporary investigation needs noisier logging, remove it or downgrade it
after the bug has a deterministic test.

## Debugging Workflow

For playback bugs, reconstruct one field ordinal as an ordered timeline:

1. `SourceConfigured` / source element setup.
2. Metadata or graph readiness event.
3. `StartRequested` and `PlayAudio` effect.
4. Audio element `play_requested`, `playing`, and `play_resolved`.
5. `PlayResolved` transition into `playing`.
6. Boundary, `ended`, or error event.
7. Repeat/restart/complete transition.

If browser audio and session state disagree, fix the first transition that made
the session state stop matching the active audio element. Do not patch the later
symptom first.
