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
