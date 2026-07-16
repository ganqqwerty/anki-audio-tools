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

### Independent acoustic observation

State and media-element observations explain what playback intended to do; they
do not prove what the browser media pipeline emitted. Tests whose names claim
`audible`, `acoustic`, or emitted-PCM behavior must additionally use the
bounded capture helper in `e2e/audible_audio_capture.py` and evaluate the result
with the independent oracle under `settings_ui/tests/audible/`.

The oracle uses the synthetic `addressable-timecode.wav` fixture. Its coarse
50 ms tone frames locate a source region and its PRBS carrier refines source
position. Expected regions come from the test gesture, never from `currentTime`,
the graph cursor, or projected playback state. The current analysis trace is
sampled at roughly 10 ms intervals; raw PCM remains at the Web Audio sample
rate. This supports source-region and dropout assertions but is not a promise
of one-millisecond click-to-speaker timing.

The real-Anki adapter uses a test-only, CSP-approved static AudioWorklet. E2E
setup registers only `test_support/audio_probe_worklet.js` as a web export.
Captured PCM remains bounded and is transferred outside the WebView for the
verdict. The production command bridge never carries samples or capture
controls. Closing the temporary editor destroys the capture context after the
helper disconnects its nodes.

Acoustic assertions supplement, rather than replace, session transitions,
native media events, play-count budgets, and fallback checks. Silence,
unknown non-silent output, overlap, duplicate source ranges, unexpected
prefixes, and output after a declared stop are failures. The oracle's
carrier-free negative and 100 ms dropout tests must remain in place so capture
or matching changes cannot manufacture confidence.

### When addressable audio is required

Use addressable audio when behavior could be wrong at the speaker while the
session reducer, graph cursor, media events, play-call count, and `currentTime`
all remain plausible. In those cases telemetry is corroborating evidence, not
the verdict.

Addressable acoustic E2E coverage is required for changes affecting these
observable guarantees:

| Guarantee | Examples |
| --- | --- |
| Correct content | start position, end boundary, forbidden prefix/suffix, selected region |
| Stateful continuity | seek or cursor drag while playing, pause/reposition/resume, selection resize/replacement/clear |
| Bounded repetition | pass count, inter-pass silence, repeat disable, timer cancellation, terminal silence |
| Source lifetime | transform during playback, post-edit autoplay, note switch, source replacement, stale media-element prevention |
| Native decoding | WAV/MP3/OGG/M4A support, decode failure, browser media fallback |
| Negative audible behavior | no overlap, duplicate pass, dropout, old-source leak, delayed restart, or output after stop/failure/navigation |

One representative acoustic E2E path is sufficient when lower-level tests
exhaustively cover equivalent state-machine permutations. Add more acoustic
cases when browser timing, codec behavior, source replacement, or action order
changes the media-pipeline risk; do not mechanically duplicate every fake-driver
test.

Addressability is not required for tests limited to pure transition logic, DOM
or CSS projection, configuration persistence, control visibility, bridge
payload shape, or command dispatch. It becomes required as soon as such a test
claims that a particular interval was heard, that silence persisted, or that
old/duplicate audio was absent.

Every required acoustic E2E test must:

1. use a real Qt WebEngine media element and a trusted user gesture;
2. derive expected source regions from test inputs and gestures, never from
   playback telemetry;
3. install bounded PCM capture before the relevant gesture and evaluate it
   outside the WebView with the independent oracle;
4. assert positive output and relevant negative space, such as forbidden
   prefixes, repeat gaps, old-source absence, and terminal silence;
5. retain state/event/log assertions for diagnosis;
6. include `audible`, `acoustic`, or `emitted_pcm` in its name so Rule 36
   enforces the capture/oracle boundary.

Volume-only and other signal-preserving transforms may reuse the addressable
reference with explicit clipping/gain expectations. Pitch, tempo, trimming, or
other time/frequency-changing transforms require an independent transformed
reference or transform-aware oracle before making acoustic position claims.

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
