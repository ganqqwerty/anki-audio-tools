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
- Public release archives are thin. On first load, the add-on downloads the verified runtime pack for macOS arm64, macOS x86_64, or Windows x86_64.
- Optional advanced overrides: explicit `ffmpeg_path` and `deep_filter_path` settings still take precedence over managed runtime tools
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
python3 scripts/release.py --target all
python3 scripts/release.py --verify-runtime-urls
python3 scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>.ankiaddon
```

This validates the repo, regenerates contracts and webview bundles, stages
locked runtime payloads, builds platform runtime pack zips, writes version-pinned
runtime-pack metadata into `bin/runtime_manifest.json`, validates the thin add-on
archive, and produces `dist/anki-audio-quick-editor-<version>.ankiaddon`.
Public AnkiWeb releases should use `--target all`; `--target current` and
single-platform targets are for local/private validation.

`release-assets verify` checks presence and checksums by default. Add
`--diagnostics` when you also want current-host runtime probes before release
smoke or native acceptance.

Use `--upload-assets` to upload generated runtime packs with `gh release upload`,
or run the printed command manually when `gh` is unavailable. Use `--embed-runtime`
for local/offline validation builds that intentionally include runtime payloads in
the `.ankiaddon`.
