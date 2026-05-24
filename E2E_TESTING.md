# E2E Testing

The e2e suite runs the real add-on inside a live Anki runtime using `aqt._run(exec=False)`.

## What It Verifies

- the Tools menu entry exists
- the settings action opens the settings dialog
- the settings HTML includes initial state
- saving settings writes config
- the renamed add-on package loads under the local numeric add-on ID
- ffmpeg trims/speeds generated audio to shorter durations when `ffmpeg` and `ffprobe` are installed
- final rendered MP3 files can be written to Anki media without overwriting the original source file

## How It Works

- `ANKI_BASE` points at a temporary directory for the test session
- the add-on is symlinked under `addons21/1000000002`
- modules are aliased so `anki_audio_quick_editor.*` resolves to the same module objects Anki loaded as `1000000002.*`

## Playback Interval Tests

Playback tests patch Anki's `av_player` with a fake recorder that captures `play_tags()`, `seek_relative()`, `stop_and_clear_queue()`, and `toggle_pause()`. This makes cursor playback observable without needing audible output.

Asserting that `seek_relative()` was called is not enough because the bug class is about the effective interval AQE asks Anki to play. Cursor playback now prepares a temporary `aqe_playback_*__from_<ms>ms_*.mp3` segment and plays that from zero, so the fake recorder maps the temp filename and ffprobe duration back to the original-file interval.

Use about `±75 ms` tolerance for cursor and seek assertions. That leaves room for SVG coordinate rounding, timer jitter, and Qt event-loop scheduling while still catching flipped intervals such as `0%-30%` instead of `70%-100%`.

## Run It

```bash
python3 scripts/dev.py test-e2e
```

Run this command through `scripts/dev.py`, not bare `pytest e2e`, after frontend changes. The dev runner rebuilds the committed settings/editor webview bundles before Anki starts. Bare pytest can pass or fail against stale JavaScript because Anki loads `addon/anki_audio_quick_editor/templates/**`, not `settings_ui/src/**`.

If an e2e run leaves bundle diffs, inspect and commit them with the source change. That churn usually means the previous committed bundles were stale or the build was not run before the test.

## Inline Editor Lifecycle Gotchas

The injected editor frontend schedules immediate and delayed scans so controls appear after Anki finishes rendering editor fields. That makes lifecycle bugs look strange: an old delayed scan can remount controls after a note reload, undo, or processing command if disposal does not cancel it.

When changing editor field replacement, undo, processing, or frontend runtime mounting, preserve these rules:

- Python should call `window.__aqeEditorDispose && window.__aqeEditorDispose()` before mutating/reloading fields that may contain existing AQE controls.
- Frontend runtime disposal should cancel delayed scan timers and remove orphaned `.aqe-mount-host` / `.aqe-controls` nodes.
- Rescans should keep a busy or already-rendered graph for the same field source, but they should not leave duplicate hidden visualizers behind.
- Add or update jsdom integration tests in `settings_ui/tests/editor-inline.integration.test.ts` before relying only on e2e. They are faster and can deterministically catch orphan controls and canceled delayed scans.

Symptoms of this class of bug include two visualizers for one field, a hidden old visualizer receiving playback/graph state, buttons becoming enabled during processing, or graph state reverting shortly after an apparently successful e2e step.

When changing inline editor toolbar commands or quick settings, update [`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`](EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md) with the corresponding e2e behavior source and any intentional exceptions.
