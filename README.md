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
- Release archives bundle `ffmpeg`, `ffprobe`, DeepFilterNet, and RNNoise runtimes for macOS arm64, macOS x86_64, and Windows x86_64
- Optional advanced overrides: explicit `ffmpeg_path` and `deep_filter_path` settings still take precedence over bundled tools
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
python3 scripts/dev.py release-assets verify --target all
python3 scripts/dev.py release-assets verify --target current --diagnostics
python3 scripts/release.py --target current
python3 scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>-<target>.ankiaddon
```

This validates the repo, regenerates contracts and webview bundles, stages
tracked non-FFmpeg runtime payloads plus cached `ffmpeg`/`ffprobe`, validates
the archive manifest, and produces a platform-targeted archive such as
`dist/anki-audio-quick-editor-<version>-macos-arm64.ankiaddon`. Universal
archives remain available with `--target all`, but the third-party FFmpeg
payload makes them too large for the normal release size gate unless an explicit
`--allow-large-archive` reason is supplied.

`release-assets verify` checks presence and checksums by default. Add
`--diagnostics` when you also want current-host runtime probes before release
smoke or native acceptance.
