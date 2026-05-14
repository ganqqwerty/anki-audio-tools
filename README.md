# Anki Audio Quick Editor

Anki desktop add-on for quickly editing audio references from the note editor. It is optimized for short sentence-mining clips: trim edges, adjust speed, remove silence, and automatically apply each edit as a new MP3 while leaving original media untouched.

## What It Includes

- Inline Anki editor controls for fields containing `[sound:...]` references
- ffmpeg-backed MP3 rendering for each inline edit action
- Non-destructive save flow that writes a new media file and updates the field reference
- Settings dialog backed by `AnkiWebView` and a committed Svelte bundle
- Config defaults, JSON Schema validation, and deep-merge migration support
- Unit tests, architecture tests, and real-runtime e2e tests
- `scripts/dev.py` for setup, checks, builds, release, and e2e execution
- `.ankiaddon` packaging via `scripts/release.py`

## Requirements

- Anki 25.09 or later
- Python 3.13 as bundled by Anki
- `ffmpeg` and `ffprobe` available on PATH, or an explicit `ffmpeg_path` in settings
- Node.js 18+ for editing or rebuilding the settings UI

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

The local development add-on ID is `1000000002`.

## Development

- Runtime package: `addon/anki_audio_quick_editor/`
- Settings frontend: `settings_ui/`
- Build the settings bundle: `python3 scripts/dev.py build`
- Open the settings dialog from Anki: `Tools -> Anki Audio Quick Editor -> Settings`
- Edit audio from Anki by focusing a field containing `[sound:filename.mp3]` and using the injected inline controls.

## Release

```bash
python3 scripts/release.py
```

This validates the repo and produces `dist/anki-audio-quick-editor-<version>.ankiaddon`.
