# Audible Playback Observability Handoff for the Mother Repository

## Purpose

This document is a self-contained implementation plan for adding **audible-output playback tests** to the mother repository:

- mother repository: `/Users/iuriikatkov/IdeaProjects/anki-audio-tools`
- historical source baseline used by the standalone extraction: commit `8f25fb39c0c0a3808ee950eb21f2edeca3a02b35`
- playback model at that baseline: `settings_ui/src/editor-inline/playback-model.ts`
- reference implementation: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice`

The programmer implementing this plan should work from the mother repository's current branch. The pinned commit is useful for historical and semantic comparison; it is not an instruction to reset current work.

The goal is stronger than proving that the UI requested playback or that an `HTMLAudioElement` clock advanced. The tests must independently observe the PCM signal emitted by the real browser media pipeline and answer:

1. Was output actually audible/non-silent?
2. Which source-time region was emitted?
3. Were region boundaries, pause gaps, resumes, repeats, interruptions, and error silence correct?
4. Did the emitted waveform contain a dropout, leak, overlap, or false restart that application state did not report?

The reference implementation was created in a standalone Electron extraction, but its fixture, oracle, contract model, impairment tests, and artifact design are deliberately adapter-independent. Only the capture and UI-driving layers need to be adapted to Anki and Qt WebEngine.

## Existing Mother-Repository Foothold

Do not build a second E2E framework. Extend the current real-Anki harness.

The mother repository already provides:

- real Anki and Qt startup in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/conftest.py`;
- editor creation helpers in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/editor_note_helpers.py`;
- JavaScript execution and polling helpers in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/helpers.py`;
- graph gestures in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/editor_graph_helpers.py`;
- selected-region helpers in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/editor_region_loop_helpers.py`;
- real-media tests and a trusted Qt click helper in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/test_editor_real_media_repeat_workflow.py`;
- generated-audio helpers in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/e2e/editor_audio_generation_helpers.py`;
- an explicit architecture rule preventing fake audio drivers from making real browser-media claims in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/tests/test_architecture/test_rule36_e2e_real_audio_policy.py`;
- the canonical state/logging contract in `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/docs/architecture/html-audio-observability.md`.

In particular, `_trusted_click_selector()` already maps the DOM element's coordinates into the Qt WebView and calls `QTest.mouseClick`. This is important because a suspended `AudioContext` normally has to be resumed from a trusted user gesture. The existing `_install_real_audio_probe()` observes real `play()`, `pause()`, media events, browser errors, and unwanted backend/native playback. Preserve those observations and add independent PCM capture beside them.

Most existing playback E2E tests use `_install_html_audio_test_driver()`. Those tests remain valuable for fast UI/state coverage, but they are not acoustic evidence. New audible-output tests must use the real `<audio>` element and must comply with Rule 36.

## What the Reference Implementation Contains

Start with these documents:

- original implementation plan: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/docs/plans/audible-playback-observability-plan.md`
- resulting architecture: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/docs/architecture/html-audio-observability.md`
- E2E commands and environment: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/E2E_TESTING.md`

The implementation is split into five reusable pieces:

| Piece                       | Reference                                                                                                                                                                   | Reuse guidance                                                                                       |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Deterministic audio fixture | `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/scripts/addressable_audio_fixture.py`                                                                                    | Reuse or port essentially unchanged. It has no Electron dependency.                                  |
| Fixture build/checksums     | `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/scripts/generate_fixtures.py` and `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/manifest.json` | Adapt to the mother repo's fixture-generation conventions and managed ffmpeg lookup.                 |
| Acoustic oracle             | `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audio-oracle.ts` plus the `audio-*` support modules                                                   | Reuse the algorithms. Decide whether to execute them in TypeScript or port them carefully to Python. |
| Scenario contract           | `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audible-contract.ts`                                                                                  | Reuse the data model and verdict semantics. Keep expectations independent of application state.      |
| PCM capture                 | `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audio-output-probe.ts`, `audio-output-probe-browser.ts`, and `audio-probe-worklet.js`                 | Adapt to Anki's Qt WebEngine, CSP, resource loading, and Python↔JavaScript transfer constraints.     |

The reference scenario suites are:

- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/specs/audible-playback.spec.ts`
- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/specs/audible-playback-lifecycle.spec.ts`
- optional system-output smoke test: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/specs/audible-system-loopback.spec.ts`

## The Addressable Audio Fixture

### Why ordinary tones are insufficient

A constant sine wave proves only that some sound exists. It cannot distinguish a seek to 2 seconds from a seek to 7 seconds, a correct resume from a restart, or an old-source leak from intended output. The reference fixture encodes source time continuously so the oracle can infer emitted source position from arbitrary captured windows.

### Files available for immediate use

The already-generated fixtures are:

- WAV master: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/addressable-timecode.wav`
- MP3: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/addressable-timecode.mp3`
- OGG/Vorbis: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/addressable-timecode.ogg`
- M4A/AAC: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/addressable-timecode.m4a`
- machine-readable parameters and checksums: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/fixtures/audio/manifest.json`

Expected SHA-256 checksums at the time of this handoff:

| File | SHA-256                                                            |
| ---- | ------------------------------------------------------------------ |
| WAV  | `0db620128ebf9ce6d11aaa2ec8b4c8d81e2c1a9996210244ea0f9322a218dd67` |
| MP3  | `213514a0bd167a5f5942f1742aa16f9970e55b9fd16c3883b89fd3e20fa7fdb2` |
| OGG  | `546fd8855be7013360b0c5619f39b77b4cb8e8d24d1f91454b23aebf2b23ed5e` |
| M4A  | `a249b4899a38b44ccbbf4e50537a8342808d8de89176fae8e03e7a06d25940ef` |

Copying these files into the mother repo is reasonable if repository policy allows binary fixtures. If they are copied, also copy the manifest and preserve generator provenance. Prefer regeneration over editing binary data.

### Signal format

The master is a 10-second, mono, 48 kHz, signed PCM16 WAV. It contains 200 address frames of 50 ms each. Each frame contains:

- four octal digits encoded by one tone chosen from each of four banks;
- a carrier-coded fine-position signal used for reliable correlation;
- a low-level 800→1400 Hz chirp at every whole second as a human/debugging landmark;
- raised-cosine shaping to avoid hard discontinuities;
- a final peak normalized to -3 dBFS.

Tone banks are:

- digit 1: 600–1300 Hz in 100 Hz increments;
- digit 2: 1700–2400 Hz;
- digit 3: 2900–3600 Hz;
- digit 4: 4100–4800 Hz.

The fine-position carrier uses:

- algorithm identifier: `prbs31-x31-x28-1-bpsk-raised-cosine-v1`;
- seed: `0x05EED123` (`99537187` decimal);
- carrier center: 6000 Hz;
- chip rate: 1200 Hz;
- 40 samples per chip at 48 kHz;
- nominal carrier band: 4800–7200 Hz.

Compressed variants must be encoded from the exact same WAV master. This allows the same expected source-time contract to be applied to WAV, MP3, OGG, and M4A while tolerating codec delay and waveform distortion in the oracle.

Regenerate the reference fixtures from the standalone repository with:

```bash
cd /Users/iuriikatkov/IdeaProjects/shadowing-pratice
python3 scripts/generate_fixtures.py
```

`PRACTICE_FIXTURE_FFMPEG` can override the ffmpeg executable there. In the mother repo, integrate generation with its managed ffmpeg mechanism rather than assuming `ffmpeg` is on `PATH`.

## Oracle Design

### Input and output

The oracle consumes:

- bounded mono PCM from the capture adapter;
- the actual capture sample rate;
- timing metadata such as capture start, worklet frame indices, and gaps;
- the fixture manifest;
- a contract declared from test inputs.

It produces a time-ordered trace at approximately 10 ms intervals. Each sample is classified as:

- silence;
- known fixture source position with confidence;
- unknown/non-silent signal;
- discontinuity/dropout metadata when applicable.

The contract layer reduces that trace to emitted segments and compares them to expected source-time intervals, silence gaps, repeats, forbidden prefixes, and continuity requirements.

### Confidence safety invariant

The coarse tone code is only a frame locator. It is **not proof that the fixture carrier is present**, and it is not accurate enough to supply arbitrary fine position.

An early implementation used the maximum of raw correlation confidence and coarse-tone confidence. A signal containing only the four correct tones, but no PRBS carrier, was then falsely classified as a known source position. The fixed oracle:

1. regenerates the expected PRBS carrier from the manifest;
2. band-pass filters both reference and captured windows around the carrier band;
3. uses carrier-specific correlation to establish content identity and fine position;
4. uses the tone code only to narrow the search frame.

This invariant must survive any Python port or simplification. Include the carrier-free coded-tone negative test before trusting the oracle.

Reference files:

- main oracle: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audio-oracle.ts`
- public types: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audio-oracle-types.ts`
- signal operations: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-signal.ts`
- frame decoding: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-timecode.ts`
- matching: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-match-engine.ts` and `audio-window-matcher.ts`
- segment derivation: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-segments.ts`
- adversarial tests: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audio-oracle.test.ts`

### Required oracle tests

Before connecting the oracle to Anki, verify it independently against synthetic impairments:

1. clean fixture playback is located correctly;
2. leading and trailing silence do not change source position;
3. gain reduction and moderate noise retain a correct match;
4. sample-rate differences/resampling remain locatable;
5. compressed fixture variants remain locatable within codec tolerance;
6. a short transition gap can be repaired only when bracketed by continuous source positions;
7. a 100 ms dropout remains visible and fails a continuity contract;
8. an unrelated tone is classified unknown, not as the fixture;
9. carrier-free but correctly frame-coded tones are classified unknown;
10. overlapping or mixed source regions are not silently accepted as a clean segment.

The reference oracle repairs only short, bracketed continuity gaps and caps the repair threshold at 50 ms. Do not increase this merely to make tests green; a 100 ms dropout is an intended independent detection case.

The carrier FIR reference is cached by acoustic reference, sample rate, and length. Keep equivalent caching if tests are slow. V8 coverage instrumentation made the reference oracle suite need a 15-second timeout even though normal execution was much faster.

## Contract Model

The acoustic contract must be created from the scenario's setup and user action, never from the application's reported cursor, selection, playback state, or audio `currentTime`. Those values are useful correlated diagnostics, but using them as expected output makes the app its own oracle.

Reference files:

- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audible-contract.ts`
- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audible-contract-types.ts`
- orchestration example: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/audible-playback-harness.ts`

Each expected segment should be able to declare:

- expected fixture identity;
- expected source start and end;
- whether the segment must be continuous;
- allowed start/end source-position error;
- required or forbidden silence before/after it;
- minimum and maximum gap to the adjacent segment;
- forbidden source regions, such as a leaked prefix;
- whether unknown non-silent output is a failure.

Support independent `startPositionToleranceMs` and `endPositionToleranceMs`. Test-runner contention and observation timing affect endpoints differently; loosening both sides with one broad tolerance can hide a wrong start.

For cancellation and resume, prefer a relational assertion such as “the resumed segment begins no more than 150 ms after the interrupted segment ended.” A fixed expected wall-clock source start is brittle because real media may advance slightly between the last observation and the trusted gesture.

Always analyze and write metrics before asserting probe health. Silence is a core regression and still needs a useful artifact bundle; throwing “no samples” before producing diagnostics defeats the purpose of observability.

## Capture Adapter for Qt WebEngine

### Preferred Tier A route

First attempt to reuse this signal path inside the real editor WebView:

```text
real HTMLMediaElement
  -> captureStream()
  -> MediaStreamAudioSourceNode
  -> AudioWorkletNode
  -> bounded mono Float32 PCM blocks
  -> test-only extraction to Python
  -> acoustic oracle
```

The reference worklet averages all input channels arithmetically into mono, posts bounded PCM blocks with `currentFrame`, and stops after a per-test cap (5 seconds by default). It records audio-context state, output timestamps when available, channel counts, nonzero sample counts, and RMS. Capture is installed before the trusted Play click while the context remains suspended; the same trusted Qt click resumes the context and starts playback.

Do not use `AnalyserNode` as the primary oracle. It provides visualization bins, not a gap-free PCM stream with enough temporal evidence for source-position and dropout assertions.

### Feasibility spike—do this before porting the full suite

Add one temporary or focused E2E test using the current real-media harness and the addressable WAV. It should:

1. open the editor with the fixture copied into the test collection media directory;
2. locate `[data-testid="aqe-audio-clock-0"]`;
3. report support for `audio.captureStream`, `AudioContext`, `AudioWorkletNode`, `audioContext.audioWorklet`, and context state;
4. load a worklet without changing the production bundle or bridge;
5. install capture before playback;
6. use `_trusted_click_selector(editor, _button_selector("aqe:play"))`;
7. collect roughly 500 ms of samples;
8. confirm nonzero sample count and sensible RMS;
9. confirm the captured samples can be moved out of the WebView without truncation;
10. cleanly disconnect nodes, close the context, pause the element, clear its source, and close the editor.

Test worklet-loading approaches in this order:

1. a test-only URL/resource exposed through the existing editor WebView resource mechanism;
2. a `Blob` URL created by injected test JavaScript;
3. a compact inline worklet source passed by the test harness.

Do not add a production IPC/bridge method merely for E2E capture. If CSP or Qt resource policy blocks all test-only worklet routes, document the exact failure and choose the fallback below.

### Fallback routes

If `captureStream()` is unavailable but Web Audio is available, use:

```text
HTMLMediaElement
  -> MediaElementAudioSourceNode
  -> AudioWorkletNode
  -> PCM capture
```

Ensure this graph does not mute the user's actual output. Connect an audible path to `audioContext.destination` if routing the media element through Web Audio removes its normal output. Add a canary proving that the capture graph itself does not change playback timing or volume.

If AudioWorklet is unavailable but ScriptProcessor is available, a short-lived test-only ScriptProcessor fallback may be acceptable, but record the higher timing risk and keep the 100 ms dropout test as a canary. Do not weaken dropout expectations to accommodate an unreliable adapter.

If Qt WebEngine cannot provide PCM reliably, keep the exact fixture, oracle, and contracts but implement system-output loopback capture. That becomes the primary acoustic adapter rather than an excuse to replace acoustic assertions with element-state assertions.

### Moving PCM from JavaScript to Python

Avoid one enormous JSON array. It is slow and may exceed Qt WebChannel or JavaScript result limits. Recommended approaches:

- capture a bounded number of samples;
- transfer chunks as base64-encoded Float32 bytes or signed PCM16 bytes;
- include `sequence`, `firstFrame`, `sampleRate`, `channelCount`, and `sampleCount` per chunk;
- verify sequence continuity and total sample count in Python;
- preserve raw Float32 until analysis when practical;
- do not use the add-on's production command bridge for sample transport.

The existing `run_js`/`wait_for_js_condition` helpers can poll chunk metadata and fetch bounded chunks from a test-only global. Clear each transferred chunk to keep WebView memory bounded.

## Proposed Mother-Repository Layout

Follow mother-repository naming conventions, but a reasonable starting layout is:

```text
e2e/
  fixtures/audio/
    addressable-timecode.wav
    addressable-timecode.mp3
    addressable-timecode.ogg
    addressable-timecode.m4a
    addressable-timecode.manifest.json
  audible_audio_capture.py
  audible_audio_contract.py
  audible_audio_oracle.py
  audible_audio_artifacts.py
  test_editor_audible_playback_workflow.py
  test_editor_audible_playback_lifecycle_workflow.py
  test_editor_audible_system_output_workflow.py
settings_ui/
  tests/ or test-only build assets/
    audio-probe-worklet.js
tests/
  test_audible_audio_oracle.py
```

An alternative is to keep the oracle in TypeScript under `settings_ui/tests` and invoke it with Node from pytest. Prefer that only if it substantially reduces porting risk and the test command can package diagnostics cleanly. The verdict must remain outside the WebView under test.

Do not put acoustic fixtures under Anki user media permanently. Each E2E test should copy them into the isolated collection media directory and let the test fixture clean up the temporary profile.

## Test-First Integration Phases

### Phase 1: fixture and oracle, no Anki

1. Import or port the generator and manifest.
2. Add deterministic checksum verification.
3. Import or port the oracle and contract model.
4. Port all adversarial/impairment tests, especially the carrier-free negative test and 100 ms dropout test.
5. Produce a small CLI or test helper that analyzes an arbitrary PCM/WAV capture and emits JSON metrics.

Exit criterion: the oracle locates clean/compressed fixture windows and rejects all negative fixtures without accessing any application state.

### Phase 2: one real-WebView capture canary

1. Reuse `_open_real_media_editor`, `_wait_for_real_audio_ready`, `_install_real_audio_probe`, `_trusted_click_selector`, and `_stop_real_audio_playback` from the existing real-media test.
2. Capture a 0–1 second WAV playback.
3. Verify the oracle reports a continuous source segment starting near zero.
4. Attach metrics on success and the full diagnostic bundle on failure.
5. Run the canary repeatedly and under `test-e2e-parallel`.

Exit criterion: at least 20 sequential and 10 parallel attempts produce no false silence, no missing chunks, and stable source-position bounds.

### Phase 3: essential semantic scenarios

Implement WAV selected-region playback, positioned play, live reposition, pause/reposition/resume, selected repeat with a real pause gap, repeat-off terminal silence, and media failure first. These exercise all essential verdict shapes: bounded segment, transition, silence gap, repeated segment, timer cancellation, and persistent silence.

Exit criterion: failures identify the emitted source region from acoustic evidence and provide enough artifacts to distinguish app bug, browser seek bug, and probe failure.

### Phase 4: codec matrix and interaction edge cases

Add MP3 and supported OGG/M4A scenarios. A codec that Qt WebEngine intentionally cannot decode should have an explicit failure/silence contract, not a copied “must play” contract. Complete selection replacement/clear/resize, cancelled gestures, repeat-wait interruption, chorusing auto-advance, processing during playback, note/source replacement, and old-source leak coverage. Add transformation-output claims only after the oracle has independent transformation-aware fixtures or models.

Exit criterion: every supported codec has a nonzero acoustic canary and each unsupported codec has a deterministic readiness/error plus silence verdict.

### Phase 5: optional system-output Tier B

Add a small opt-in smoke suite that records the actual selected output device or a configured virtual loopback device. Keep it disabled by default but make misconfiguration a hard error once explicitly enabled.

Exit criterion: CI or a documented local job can prove that the end-to-end device path emits the addressable fixture, without recording arbitrary user audio.

## Scenario Matrix

The reference scenarios are only the starting point. The mother repository already has a much richer interaction surface, and the acoustic suite should upgrade the highest-risk existing E2E workflows instead of creating ten isolated happy-path tests.

### Existing tests that should gain acoustic coverage

Keep the existing fast fake-driver tests. Add focused real-media acoustic companions, or parameterize their reusable action helpers, for the following cases.

| Existing E2E coverage | What state-only coverage cannot prove | Acoustic upgrade |
| --- | --- | --- |
| `test_editor_playback_workflow.py` and `test_editor_playback_resume_behavior.py` | A cursor can move to 70% and the media clock can report 70% while the decoded output begins at zero, resumes from a stale seek, or briefly leaks the old position. | Cover play from zero, play from a positioned cursor, drag while playing, and pause-drag-play. Assert decoded source-time start, discontinuity shape, forbidden prefix, and bounded silence during the gesture. |
| `test_editor_region_loop_playback_one_shot_workflow.py` | The selected UI region and stop event do not prove that sound began and ended at those boundaries. | Make selected WAV and MP3 playback the first semantic canaries. Require a single continuous selected interval, silence after its end, and no second pass. |
| `test_editor_region_loop_playback_repeat_workflow.py` and `test_editor_region_loop_playback_repeat_interactions_workflow.py` | Forced media boundaries and reducer state do not prove audible passes, real pause gaps, restart position, or eventual termination. | Observe at least three complete passes, configured gaps, exact per-pass source starts/ends, pause/resume behavior, repeat disable behavior, and a hard upper bound on all later non-silent output. |
| `test_editor_region_resize_workflow.py` | The session can adopt resized bounds while the old pass remains audible or two media starts overlap. | Capture pointer-down interruption, silence during drag, restart after commit, and the new start/end boundaries. Test start-edge and end-edge changes separately because their contracts differ. |
| `test_editor_selection_marker_shift_workflow.py` | “Playback remains running” does not establish whether an extended end is honored without restart, duplication, or a gap. | When the end marker moves later, require continuous sound through the old end to the new end. When the start moves during playback, specify whether the current pass is immutable or restarts, then assert that exact transition acoustically. |
| `test_editor_selection_toolbar_workflow.py` | The graph Play/Pause and selection-toolbar Play/Pause buttons may project the same state while driving different seek or pause behavior. | Run the same selection contract through both entry points and compare emitted segments, pause silence, resume point, stop boundary, and absence of double-starts. |
| `test_editor_region_loop_resume_workflow.py` | Resume flags and cursors do not distinguish continue, restart-at-selection, restart-at-zero, or a hidden extra pass. | Add selected-repeat pause/restart, full-repeat resume, hidden-graph repeat, and selected non-repeat completion tests with explicit acoustic semantics for each. |
| `test_editor_chorusing_playback_workflow.py` and `test_editor_chorusing_auto_advance_pause_workflow.py` | Marker indices and repeat counters can advance while audible playback remains stuck on the same suffix or loops forever. | Decode every emitted suffix in order. Assert the configured number of repetitions, the transition gap, the newly selected start, and terminal silence after the final suffix. |
| `test_editor_post_edit_playback_workflow.py`, `test_editor_processing_workflow.py`, and the processing-during-repeat test | A generated filename and “playing” state do not prove that the old source stopped or the new source became audible. | Give pre-edit and post-edit fixtures distinguishable acoustic identities. Require old-source silence during processing, no old-source leak after replacement, exactly one autoplay of the new source, and no survival of the prior repeat timer. |
| `test_editor_graph_zoom_advanced_workflow.py` | Cursor follow and viewport restoration do not prove that zoom/scroll gestures leave audio untouched. | While playing a known interval, zoom and horizontally scroll without seeking. Require source-time continuity and forbid gaps/restarts; then verify the normal completion boundary. |
| missing-media, rejected-play, M4A decode-error, note-switch, and stale-render race workflows | Error UI and stale-work guards do not prove output stopped, especially when a previous source was already playing or a repeat timer was queued. | Begin with known audible output, trigger the failure/navigation/race, and require prompt terminal silence with no old source, unknown output, delayed autoplay, or queued repeat afterward. |

### Required interaction-chain scenarios

Each row is one user story and should usually remain one capture session. Splitting a chain into independent tests can hide stale timers, old media elements, and source leaks that only survive from the preceding action.

| Scenario | User action chain | Independent acoustic contract |
| --- | --- | --- |
| Positioned play | Move stopped cursor to 20%, press graph Play. Repeat at 70% and with the selection-toolbar Play button. | The first known sample begins near the requested source position; no zero-prefix, previous-position burst, or duplicate start is allowed. |
| Live cursor reposition | Start near 1 s, let sound advance, pointer-down at 6 s, drag, and release. | The old segment stops promptly at gesture start; the gesture interval has bounded silence; exactly one new segment begins near 6 s after commit. Forbid overlap, a zero-prefix, and any later continuation of the abandoned segment. |
| Cancelled cursor gesture | Start playback, begin a cursor drag, then cancel via the actual supported cancellation route. | The interruption is silent and bounded. The resumed segment is relationally continuous with the pre-gesture segment and neither resets to zero nor jumps to the uncommitted draft position. |
| Pause, reposition, resume | Play, pause, wait long enough to expose hidden repeat, move cursor while paused, wait again, press Play. | Silence begins promptly at pause and continues through reposition. Reposition alone emits nothing. Resume starts once at the committed cursor (or selection start where product semantics require restart), not the old paused point or zero. |
| Selection created during full playback | Begin full-file playback, shift-drag a new region, then release. | Specify and assert the product rule: either current pass remains immutable until its boundary or playback restarts once at the new selection. Never accept a hybrid containing old continuation plus new selected playback. |
| Selection replacement during repeat | Repeat selection A, then replace it with disjoint selection B while A is audible and allow multiple boundaries. | A stops promptly; B starts once according to the gesture rule; every later pass is B. Forbid any queued return to A and forbid mixed A/B overlap. |
| Selection clear during repeat | Begin selected repeat, clear selection during a pass, and observe beyond both the old selected end and full-file end. | The in-flight pass honors its immutable captured end. Subsequent behavior follows the declared product rule (full-file repeat or repeat cancellation), with no extension of the current pass and no stale selected restart. |
| Resize end later while playing | Play a selection and move its end past the old end. | If playback intentionally restarts on commit, require one restart at selection start and continuity to the new end. Explicitly forbid stopping at the old end, playing both sessions, or silently continuing an old request with stale bounds. |
| Resize start while paused/repeating | Pause selected playback, move the start edge, enable repeat, and resume through two passes. | No sound during resize. Both resumed passes begin at the new start and end at the current end; the old start is a forbidden region. |
| Marker-shift extends current pass | Start selection playback, shift its end to the next marker before the old boundary. | Sound remains source-time continuous through the former boundary and ends at the new boundary, without a restart, gap, or duplicate frames, matching the current test's “keeps playback running” intent. |
| Disable repeat mid-pass | During pass N, turn Repeat off and wait well beyond the next possible pass. | Pass N finishes at its captured end, followed by terminal silence. No repeat-wait timer may start another pass. Include a maximum emitted-segment count and a postcondition observation window. |
| Pause during repeat wait | Reach the configured silent repeat gap, press Pause, wait beyond the original timer, then resume. | The gap remains silent indefinitely while paused; the expired timer emits nothing. Resume creates exactly one pass at the selected start—never two from the old timer plus the user action. |
| Re-enable/toggle repeat rapidly | Toggle repeat off/on around a boundary or during the repeat gap. | At most one next pass begins. Require monotonic segment numbering and a minimum separation so duplicate concurrent starts cannot be merged into a valid-looking segment. |
| Finite chorusing auto-advance | Configure suffix markers, `repeatCount = N`, pause gap, and auto-advance; run until completion. | For each suffix, observe exactly N copies with correct start/end and gaps, then the next suffix in the declared order. Require terminal silence and cap total passes so “stuck forever on one suffix” fails quickly. |
| Chorusing manual navigation during playback | While auto-advance/repeat is active, click next/previous and edit markers. | The audible sequence switches once to the newly chosen suffix; counters reset as specified; removed markers never reappear acoustically from an old queued request. |
| Transform during playback | Start a selected or repeating pass, apply Volume/Speed/Pitch/Filter, wait for processing and autoplay. | Old output stops promptly and stays silent during processing. Exactly one new-source segment follows readiness. No old repeat callback, old decoded buffer, or simultaneous old/new output is allowed. |
| Consecutive transforms | Start playback, apply transform A, then apply transform B as soon as allowed. | Acoustic identities occur only in committed order; stale completion of A cannot replace or autoplay over B. After B starts, A and the original are forbidden. |
| Note/field/source switch | Play or wait between repeats, then change note, field audio, or hide/close the editor. | Prompt terminal silence from the abandoned source. No delayed repeat, post-edit autoplay, or old-source event may produce later sound. |
| Real media error after prior sound | Start a known playable source, then replace it with missing/unsupported/corrupt media and press Play or let autoplay proceed. | The known source stops, failure interval is silent, unknown non-silent output fails, and observation continues past any configured repeat/post-edit timer. |

### Repeat termination and anti-hang assertions

“Played at least twice” is insufficient for repeat tests. Every repeat scenario must declare all of the following:

- minimum and maximum pass count;
- per-pass source start/end and continuity;
- minimum and maximum inter-pass silence;
- whether a user action applies to the in-flight pass or only the next pass;
- an absolute capture deadline and a shorter “no new sound after stop” observation window;
- forbidden output after Pause, Repeat-off, editor close, source replacement, processing start, and terminal auto-advance completion;
- duplicate-start detection, including two substantially overlapping copies of the same fixture region;
- timer ownership: a timer created before a state change must not produce sound afterward unless the contract explicitly preserves it.

Use a fixture long enough that actions can occur far from natural boundaries, and choose disjoint, widely separated regions (for example A = 1.0–2.0 s and B = 6.0–7.0 s). This makes old-region leakage unmistakable. Do not use only adjacent selections: a stale 50–100 ms continuation can then look like an acceptable boundary tolerance.

### Transformation-aware fixture strategy

The unmodified addressable fixture is directly useful for selection, seeking, pause, resume, repeat, volume changes, and transformations that preserve its identifying frequencies. Transformation tests need additional care:

- **Volume/gain:** retain the same source-position contract and add relative RMS/gain bounds. Do not treat RMS alone as content identity.
- **Speed/tempo:** decode source position against capture time and assert the expected slope as well as start/end. A faster result should traverse more source milliseconds per emitted second without skipping backward, duplicating a prefix, or exceeding the selected source boundary.
- **Trim/delete/keep-region:** use the edit parameters to construct an independent piecewise source-time mapping. The expected mapping comes from the gesture contract, not from the generated file duration or graph state.
- **Pitch shift and frequency-selective filters:** the current frequency-coded oracle may reject a correct transformed signal because its tone banks and PRBS carrier move or attenuate. Before claiming coverage, either add a transformation-aware reference decoder with parameters declared from the user action, or add a second robust time-address channel whose identity survives the supported transformation range. Never bless the add-on's generated file as the expected reference.
- **New-source identity:** where feasible, encode a fixture-generation nonce or use independently generated source families so the oracle can distinguish original, transform A, and transform B. Source filenames and application state remain diagnostics, not acoustic proof.

Add oracle-level tests for every claimed transformation range, including correct transformed output, wrong transform amount, unchanged old output, mixed old/new output, truncated output, and a time-correct but identity-unknown signal.

For all scenarios, retain the mother repo's existing assertions about:

- real HTML playback engine;
- browser readiness and native `MediaError` facts;
- requested browser play count;
- absence of backend/native/external-player fallback;
- session and projected field state;
- cursor and repeat behavior.

The acoustic verdict supplements those assertions. It does not replace state-transition diagnostics.

## Playback Delivery Risks to Probe

The standalone implementation exposed a real defect that state-only tests missed: selected MP3 playback audibly began at zero even though the app believed it had sought to the selected start. The Electron custom protocol used `net.fetch(file:)`, did not honor media Range requests, and reported no useful seekable interval.

The standalone fix is recorded in:

- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/apps/desktop/main/audio-protocol.ts`;
- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/apps/desktop/renderer/src/media-playback-preparation.ts`.

Do not copy that Electron-specific fix into Anki. Instead, use the new tests to characterize the mother repository's actual delivery path. Capture these facts in diagnostics:

- resolved audio `src`/`currentSrc`;
- `duration`, `readyState`, and `networkState`;
- `seekable.length` and every seekable range;
- requested target time, `currentTime` immediately after assignment, and `currentTime` on `seeked`;
- whether assigning/loading a source resets `currentTime` to zero;
- media events and `play()` promise resolution/rejection;
- codec/container and browser error code/message.

If a supported codec cannot seek correctly before playback, the likely robust sequence is: configure source, await metadata, assign `currentTime`, await `seeked`, verify the settled time, retry only within a bounded policy, and then call `play()`. Let the failing acoustic test justify any production change.

## Threshold and Timing Guidance

Treat thresholds as part of the test design, not arbitrary retry knobs.

- Calibrate on the clean WAV canary first.
- Derive MP3/OGG/M4A tolerances separately because encoder delay and decoder behavior differ.
- Keep source-position tolerances separate from wall-clock action timing.
- Keep start and end tolerances independently configurable.
- Do not accept unknown non-silent output merely because RMS is high.
- Keep silence detection below fixture level but above observed capture noise.
- Keep the short continuity repair threshold at or below 50 ms.
- Preserve a 100 ms dropout negative test.
- Bound every capture and every wait; a hung audio graph must not hang pytest.
- Run repeated parallel E2E attempts before widening a tolerance.

The Electron reference passed all acoustic scenarios repeatedly under multiple workers, but the full default nine-worker suite initially exposed contention around narrow observation endpoints. The eventual fix used scenario-specific endpoint tolerances, not broad global relaxation. A serial full suite passed 143 tests with one opt-in system-loopback skip at that point; those counts describe the reference repository only and are not mother-repo acceptance numbers.

## Artifacts and Diagnosis

Write lightweight metrics on every run. On acoustic or probe failure, attach:

- `audible-metrics.json`;
- `captured-output.wav`;
- `expected-output.wav` synthesized from the declared contract;
- `source-position-trace.json`;
- `audible-timeline.png` showing silence/known/unknown regions and expected segments;
- `spectrogram.png`;
- `diagnosis.txt` with the first violated contract, capture metadata, browser media facts, and probe health.

Reference implementations:

- artifact assembly: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-artifacts.ts`
- artifact file helpers: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-files.ts`
- timeline/spectrogram image generation: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/audio-artifact-images.ts`
- PNG writer: `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/support/png-raster.ts`

The artifact writer must also run for silence and capture failures. Include the existing real-audio probe's recent media-event timeline beside acoustic output so a programmer can align `play`, `seeked`, `pause`, `ended`, and session transitions with what was emitted.

Keep artifacts test-local. Never capture learner recordings or arbitrary user/system audio in the default suite. The addressable synthetic fixture is the only intended content. Do not send PCM, canonical media paths, or capture controls through a production bridge.

## System-Output Tier B

Tier A proves the decoded media signal in the WebView graph. It may not prove that the operating system or selected physical device rendered it. A small opt-in Tier B test can cover that final path.

The reference adapter and configuration are:

- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/system-output-loopback-config.ts`
- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/system-output-loopback.ts`
- `/Users/iuriikatkov/IdeaProjects/shadowing-pratice/tests/e2e/fixtures/system-output-loopback.test.ts`

Reference environment variables use the prefix `PRACTICE_E2E_SYSTEM_LOOPBACK`. In the mother repo, choose an `AQE_E2E_...` namespace and document:

- enable flag;
- input device name;
- ffmpeg input arguments as a JSON array, excluding `-i`;
- selected ffmpeg executable;
- sample rate, capture duration, ready timeout, and stop timeout.

When disabled, the test should skip. Once explicitly enabled, a missing device, executable, or malformed configuration must fail loudly. The reference implementation did not provision or execute a device-backed CI job, so do not present it as proven infrastructure.

On macOS, a virtual loopback device or aggregate device will probably be needed. Ensure the test records only during the bounded synthetic-fixture action and restores/does not mutate the user's normal device configuration.

## Architecture and Policy Updates

Extend `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/tests/test_architecture/test_rule36_e2e_real_audio_policy.py` so audible-output tests cannot accidentally install `_install_html_audio_test_driver` or another fake clock. Consider adding an explicit marker/helper naming convention such as `audible_output` and enforcing that such tests call the real capture adapter.

Update the mother architecture document rather than duplicating its logging contract. Add a section describing:

- state observation versus independent acoustic observation;
- the addressable fixture and oracle trust boundary;
- Tier A versus Tier B claims;
- test-only capture and privacy constraints;
- artifact names and retention policy.

If new WebView resources or test-only hooks affect bundling, read and update `/Users/iuriikatkov/IdeaProjects/anki-audio-tools/WEBVIEW_AND_TEMPLATES.md` as required. Do not weaken frontend state-store boundaries or use DOM datasets as canonical behavior.

## Verification Commands

Use the mother repository's normal workflow. During development, run the narrowest relevant tests first; before declaring completion, run both reusable QC and real Anki E2E.

Suggested sequence:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools

# Oracle/contract unit tests only (adjust path after choosing layout)
python3 -m pytest tests/test_audible_audio_oracle.py -q

# Focused real-Anki acoustic tests
python3 -m pytest e2e/test_editor_audible_playback_workflow.py -q
python3 -m pytest e2e/test_editor_audible_playback_lifecycle_workflow.py -q

# Repository gates
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel

# Confirm serial behavior as final verification or if parallel-only failures occur
python3 scripts/dev.py test-e2e
```

The exact direct pytest invocation may need the repository's E2E preflight/build wrapper. Prefer `scripts/dev.py` when it prepares runtime artifacts or bundles needed by the WebView.

Repeat the focused acoustic suite enough times to establish stability. A useful acceptance target is 20 serial repetitions and at least 10 runs through the parallel runner without a false acoustic failure.

## Definition of Done

The work is complete when:

- fixture generation is deterministic and checksums are verified;
- the oracle passes clean, codec, noise, resampling, carrier-free, unrelated-signal, short-gap, and 100 ms dropout tests;
- a real Anki/Qt WebView capture canary identifies emitted fixture source time;
- WAV and every claimed supported compressed format have acoustic coverage;
- the required interaction-chain scenarios above are covered according to the phased priority, with any deferred transformation-aware cases explicitly tracked rather than weakened;
- repeat tests prove both correct passes and correct termination with maximum pass counts, bounded gaps, timer-cancellation assertions, and post-stop silence windows;
- cursor, selection replacement/clear/resize, marker navigation, processing, note/source replacement, and error transitions forbid old-region and old-source leakage;
- expected output is declared independently from application state;
- fake drivers cannot satisfy real-media or audible-output tests;
- bounded capture cleanup works after pass, failure, and timeout;
- metrics are emitted every run and the full diagnostic bundle is emitted on failure, including silence;
- no production bridge transports PCM or exposes test-only capture controls;
- focused tests are stable serially and in parallel;
- `python3 scripts/dev.py check` passes;
- `python3 scripts/dev.py test-e2e-parallel` passes;
- `python3 scripts/dev.py test-e2e` passes, or any intentionally unrun verification is stated in the commit body.

## Commit Guidance

Follow the mother repository's commit policy: short imperative subject, with a body explaining why acoustic evidence is needed, how it changes confidence in playback behavior, the test/runtime impact, and any verification not run.

An example intent—not a required exact message—is:

```text
Verify editor playback from emitted audio

State and media-clock assertions could pass while users heard the wrong source
region or silence. Add an addressable fixture, an independent acoustic oracle,
and real-WebView capture so selection, seeking, repeat, and resume behavior are
validated from emitted PCM.

The capture remains test-only and bounded; production bridges and user media are
unchanged. Failure artifacts now distinguish probe failures, browser seek/decode
issues, and playback-state regressions.
```

## Explicit Non-Goals

- Do not replace reducer, integration, or existing real-media state tests.
- Do not assert microphone input or learner-recording content.
- Do not create a production audio-capture API for tests.
- Do not make system loopback mandatory for ordinary local QC until reliable infrastructure exists.
- Do not treat element `currentTime`, graph cursor position, `play()` calls, or RMS alone as proof of correct audible playback.
- Do not weaken codec behavior or security/CSP policy merely to load a probe.
- Do not copy Electron protocol code into the Anki add-on without evidence that Anki's delivery path has the same defect.

## First Working Session Checklist

1. Read the mother `AGENTS.md`, `WEBVIEW_AND_TEMPLATES.md`, and current HTML audio observability document.
2. Run the existing real-media repeat E2E test unchanged to confirm the environment.
3. Copy or regenerate the addressable WAV and manifest in a temporary test location.
4. Implement the Qt WebEngine capability spike and trusted-gesture capture canary.
5. Decide TypeScript reuse versus Python oracle port only after capture is proven.
6. Port oracle negative tests before adding many product scenarios.
7. Implement WAV selected playback end to end, including failure artifacts.
8. Add MP3 selected playback next; it is the highest-value pre-play seek check.
9. Expand through the scenario matrix and codec policy.
10. Run repeated serial/parallel verification before calibrating final tolerances.

The central rule is simple: application state explains what the code intended, while the independent acoustic trace proves what the media pipeline emitted. Keep both, and never derive one from the other.
