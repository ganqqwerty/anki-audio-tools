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

## Run It

```bash
python3 scripts/dev.py test-e2e
```
