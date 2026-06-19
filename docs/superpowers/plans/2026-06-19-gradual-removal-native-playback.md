completely get rid of native playback and always use html playback. Make sure the transition passes controllably, secure tests, prepare phases.

I checked the current playback paths with Codegraph. Here is the migration plan.

**Assumption**

“Native playback” means Anki `av_player` playback for editor/reviewer audio and learner recording playback. It does not include native microphone recording unless you also want to remove voice recording capture.

**Current State**

Key native paths are in [editor_playback.py](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/addon/anki_audio_quick_editor/editor_playback.py:35), [editor_playback_request.py](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/addon/anki_audio_quick_editor/editor_playback_request.py:1), and [editor_recording.py](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/addon/anki_audio_quick_editor/editor_recording.py:239).

Frontend still models `"native"` in [playback-actions.ts](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/settings_ui/src/editor-inline/playback-actions.ts:1), [playback-controller.ts](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/settings_ui/src/editor-inline/playback-controller.ts:1), and [editor-playback-types.ts](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/settings_ui/src/editor-inline/editor-playback-types.ts:1). HTML playback already exists through the hidden audio clock in [GraphVisualizer.svelte](/Users/iuriikatkov/.codex/worktrees/0a43/anki-audio-tools/settings_ui/src/editor-inline/GraphVisualizer.svelte:144).

**Recommended Approach**

Use a phased HTML-only migration, not a big-bang delete. First add guards/tests that make native playback visible, then switch frontend behavior, then simplify backend, then delete dead native code.

1. **Phase 0: Lock Scope And Add Guards**
    - Add an architecture test forbidding production editor playback imports/calls to `aqt.sound.av_player`, `anki.sound.SoundOrVideoTag`, `play_tags`, and playback `toggle_pause`.
    - Keep any temporary allowlist only for code being removed in later phases.
    - Convert e2e native playback helpers into leak detectors: native playback should fail tests unless a phase explicitly allows it.

2. **Phase 1: Make Source Audio Frontend HTML-Only**
    - Change `playbackEngineFor()` to always return `"html"` for editor source playback.
    - Remove “HTML failed, fall back to native” behavior from `startEditorHtmlPlayback()`.
    - On HTML play rejection, stop cleanly and show a warning/status; do not enqueue a native request.
    - Ensure no-graph playback still uses the hidden `<audio>` source configured from the Python-provided filename.

3. **Phase 2: Make Python Playback Backend State-Only**
    - Normalize missing/legacy `engine: "native"` requests to HTML or reject them with diagnostics.
    - Remove `start_playback_from_cursor()`, `playback_segment_ready()`, `playback_segment_failed()`, `toggle_native_pause_resume()`, and playback temp-segment dependency wiring.
    - Remove `render_playback_segment` from `PlaybackDeps` if it becomes playback-only dead code.
    - Keep Python responsible for validation, session state, busy/status updates, and missing-media errors.

4. **Phase 3: Move Learner Recording Playback To HTML**
    - Add a learner audio clock or generalized audio-clock target for the learner recording media filename already published by `eval_learner_recording_state()`.
    - Keep Python validating the recording belongs to the current session, then trigger frontend HTML play/pause via `web.eval(json.dumps(...))`.
    - Remove learner `av_player.play_tags()` and `toggle_pause()` from `editor_recording.py`.

5. **Phase 4: Delete Native Playback Contract Surface**
    - Remove `"native"` from TypeScript playback engine types and test contracts.
    - Update Vitest/e2e expectations from native playback to HTML playback or controlled HTML failure.
    - Delete obsolete native playback rendering tests, or move only still-used rendering utility tests elsewhere.
    - Remove stale docs/messages mentioning native playback fallback.

6. **Phase 5: Final Verification Gate**
    - Focused frontend: `python3 scripts/dev.py test-svelte`
    - Focused Python: playback, cursor, recording, bridge, architecture tests.
    - Focused e2e: editor playback, selected-region playback, post-edit playback, repeat playback, no-graph playback, learner recording comparison.
    - Full gate: `python3 scripts/dev.py check`
    - Runtime gate: `python3 scripts/dev.py test-e2e-parallel`, then `python3 scripts/dev.py test-e2e`.

**Critical Test Updates**

Replace current tests expecting native fallback, especially:
- `e2e/test_editor_region_loop_graph_repeat_workflow.py`
- `e2e/test_editor_region_loop_playback_one_shot_workflow.py`
- `e2e/test_editor_playback_workflow.py`
- `e2e/test_editor_voice_recording_comparison_workflow.py`
- `tests/test_editor_playback_state_playback.py`
- `tests/test_editor_playback_state_cursor.py`
- `settings_ui/tests/editor-inline.playback.integration.test.ts`

Add explicit assertions that:
- `av_player.play_tags()` is never called for editor source playback.
- HTML play rejection does not enqueue native fallback.
- selected-region, repeat, pause/resume, post-edit, and no-graph playback remain HTML-owned.
- learner recording playback uses HTML and updates playback status correctly.
- media filenames are encoded through `mediaUrlForFilename()` and no absolute local paths are exposed to JS.

No files were changed; this is the migration plan only.
