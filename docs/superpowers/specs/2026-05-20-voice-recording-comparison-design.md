# Voice Recording Comparison Design

## Status

Approved for implementation planning on 2026-05-20.

## Context

The editor already renders a target prosody graph for audio fields and supports cursor-synchronized playback. The new feature adds learner practice on top of that existing graph: the learner records their own voice for the same duration as the target audio, then sees their pitch contour compared with the target.

Anki 25.09 records voice natively through `aqt.sound`. It uses a native macOS helper on Apple Silicon and PyQt `QAudioSource` elsewhere. The add-on should follow that native recorder path instead of relying on WebView `MediaRecorder`, because microphone permissions and browser API support inside Anki WebEngine are a higher risk.

## Goals

- Let a learner imitate the target speaker's pitch rises, pauses, and rhythm.
- Record exactly one whole-clip attempt at a time, with the recording duration based on the target graph duration.
- Overlay the learner pitch on the existing target graph.
- Keep target pitch and target intensity visible.
- Do not show learner intensity.
- Let the learner replay the latest recording from the same editor control surface.
- Save the learner recording as Anki media, but do not insert it into the note field.

## Non-Goals

- No similarity scoring.
- No pass/fail feedback.
- No multiple-attempt history.
- No selected-region recording.
- No target audio playback during recording.
- No note-field insertion for learner recordings.
- No persistent learner recording UI beyond the current editor session state.

## Architecture

The feature should extend the existing editor graph flow.

The target graph remains the prerequisite. Once target analysis succeeds for a field, the editor control surface enables recording for that field. The frontend sends a record request through the editor bridge. Python owns the recording lifecycle, media write, analysis, stale callback protection, and playback target.

Recording should use an add-on adapter modeled on Anki's native recorder behavior rather than calling `aqt.sound.record_audio()` directly. The public Anki helper opens a modal save/cancel dialog and is designed for user-stopped recordings. This feature needs a fixed-duration, editor-integrated recorder. The adapter should reuse the same underlying strategy:

- Native macOS helper where Anki uses it.
- `QAudioSource` and the default audio input device elsewhere.
- WAV output suitable for the existing prosody analyzer.
- Anki-style permission and device failure handling.

The visible recording window starts only after countdown completes and the recorder is ready. Any recorder startup padding or quiescence handling should happen outside the learner's visible fixed-duration window so the resulting attempt corresponds to the target duration as closely as the platform recorder allows.

After recording stops, Python imports or writes the learner file into Anki media with an add-on-specific generated filename. The field content is not changed. Python then analyzes the learner media through the existing prosody analyzer/cache path and returns a learner prosody payload to the frontend. The frontend draws only the learner pitch contour on the existing target plot.

## User Flow

1. The user clicks `Graph`, or the graph appears by default if configured.
2. When the target graph is ready, `Record` becomes available for that field.
3. The user clicks `Record`.
4. The UI shows a short countdown.
5. Recording begins after the countdown and runs for the target duration.
6. Target audio does not play during recording.
7. The plot stays visible and the cursor advances across the target timeline during recording.
8. When the target duration elapses, recording stops automatically.
9. The UI shows an analyzing state.
10. The learner pitch appears on the same plot as a second line.
11. `Play yours` becomes available and plays the latest learner attempt.
12. Re-recording clears the learner overlay at countdown start and replaces the latest attempt after analysis succeeds.

## Visual Design

Use one plot, not stacked graphs.

The target graph keeps the existing target pitch and intensity presentation. The learner attempt adds a distinct pitch line on the same time axis. Learner intensity is not rendered. The line style should make the learner contour easy to distinguish in light and dark themes without overwhelming the target graph, for example a contrasting color and/or dashed stroke.

Recording controls should stay compact and consistent with the existing inline editor toolbar. The first version should add a `Record` action and a separate `Play yours` action rather than changing the behavior of the existing target `Play` button.

## State And Data

Recording state is per editor field and separate from audio edit history.

The editor session should track:

- recording status: idle, countdown, recording, stopping, analyzing, ready, failed
- target duration used for the recording window
- current recording generation id for stale callback protection
- latest learner media filename and path
- latest learner prosody track
- failure message, if recording or analysis fails

Python is the source of truth for recording lifecycle, media filenames, and analysis completion. The frontend stores UI state and normalized graph tracks only.

Re-recording replaces the current session's learner overlay and latest learner playback target. Older learner media files are left in Anki media; cleanup is Anki's responsibility.

## Bridge And Playback

The editor bridge needs commands for:

- starting a learner recording for a graph-ready field
- receiving recording lifecycle updates from Python
- receiving learner analysis completion/failure
- playing the latest learner recording

`Play yours` should use the latest learner media path or filename tracked by Python. It should stop conflicting target playback before starting learner playback. Target playback remains handled by the existing `Play` action.

Bridge payloads should be schema-backed if they cross the Python/TypeScript boundary as structured data.

## Errors And Edge Cases

- If no target graph is ready, recording is unavailable.
- If target duration is missing or zero, recording does not start and the UI shows an error.
- If target playback is active, it stops before recording starts.
- If the recorder cannot start, no microphone exists, or OS permission is denied, the UI shows an Anki-style error and leaves the target graph intact.
- If the user changes note or field while recording or analyzing, stale callbacks are ignored.
- If recording produces an empty or invalid file, the target graph stays intact and no learner overlay is drawn.
- If learner analysis fails, the target graph stays intact. A valid recorded file may remain playable, but no learner overlay is drawn.
- Re-recording clears the previous learner overlay at countdown start and replaces the latest learner playback target only after a valid new recording is available.

## Testing

Testing should cover multiple integration levels.

- Unit tests for pure state transitions, stale generation handling, target-duration validation, filename generation, and payload normalization.
- Python integration tests for the editor bridge path with a fake recorder and fake analyzer: a record request starts a session, auto-stop completion writes or imports learner media, analysis completion returns the overlay payload, and stale callbacks are ignored.
- Media/analyzer integration tests with a small WAV fixture to confirm recorded WAV-like input can be analyzed into the same prosody payload shape as target audio.
- Frontend integration tests for the editor Svelte runtime: graph-ready state enables `Record`, countdown/recording/analyzing/ready states render correctly, learner pitch overlays without learner intensity, and `Play yours` is disabled/enabled correctly.
- Bridge contract tests to keep new Python bridge commands and TypeScript command wiring synchronized.
- E2E tests with a fake recorder dependency for the full editor workflow without requiring a real microphone in CI.
- A manual or local hardware gate for real Anki/Qt microphone capture, because CI cannot reliably provide a usable microphone or OS permission state.

## Implementation Notes

The implementation plan should start with a small recorder spike against Anki 25.09 APIs. The spike should prove fixed-duration native capture can run without Anki's modal `RecordDialog`, produce a WAV file, stop cleanly, and pass that file into the existing prosody analyzer. If the adapter cannot safely reuse Anki internals, the fallback is a small add-on-owned `QAudioSource` recorder with matching behavior and explicit compatibility tests.
