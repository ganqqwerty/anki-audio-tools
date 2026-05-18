# Anki Audio Quick Editor

Anki desktop add-on for quickly editing audio references from the note editor. It is optimized for short sentence-mining clips: trim edges, adjust speed, shorten long pauses, and automatically apply each edit as a new MP3 while leaving original media untouched.

## What It Includes

- Inline Anki editor controls for fields containing `[sound:...]` references
- Inline prosody visualization with pitch, intensity, and a draggable playback start cursor
- ffmpeg-backed MP3 rendering for each inline edit action
- DeepFilterNet-assisted pause detection with retained debug artifacts for pause shortening
- Non-destructive save flow that writes a new media file and updates the field reference
- Settings dialog and inline editor controls backed by committed Svelte/TypeScript bundles
- Config defaults, JSON Schema validation, and deep-merge migration support
- Unit tests, architecture tests, and real-runtime e2e tests
- `scripts/dev.py` for setup, checks, builds, release, and e2e execution
- `.ankiaddon` packaging via `scripts/release.py`

## Requirements

- Anki 25.09 or later
- Python 3.13 as bundled by Anki
- `ffmpeg` and `ffprobe` available on PATH, or an explicit `ffmpeg_path` in settings
- DeepFilterNet's `deep-filter` for pause shortening and noise removal; macOS arm64 uses the bundled binary, other platforms can configure `deep_filter_path` or provide it on PATH
- RNNoise denoising uses a bundled macOS arm64 executable; other platforms currently show a clear unsupported-runtime diagnostic for that model
- Optional: `praat-parselmouth` in Anki's Python for preferred pitch/intensity analysis; the add-on falls back to ffmpeg-decoded PCM without it
- Node.js 18+ for editing or rebuilding the settings/editor frontend bundles

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

The local development add-on ID is `1000000002`.

## Development

- Runtime package: `addon/anki_audio_quick_editor/`
- Settings and editor frontend source: `settings_ui/`
- Build the committed frontend bundles: `python3 scripts/dev.py build`
- Open the settings dialog from Anki: `Tools -> Anki Audio Quick Editor -> Settings`
- Edit audio from Anki by focusing a field containing a supported sound reference such as `[sound:filename.m4a]`; edits are saved as new MP3 files.

## Release

```bash
python3 scripts/release.py
```

This validates the repo and produces `dist/anki-audio-quick-editor-<version>.ankiaddon`.
