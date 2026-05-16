# Development Setup & Dependencies

## The Two-Python Setup

This repo uses two Python environments:

| Environment | Purpose |
|-------------|---------|
| System `python3` | Runs `scripts/dev.py` |
| Anki bundled Python | Runs pytest, ruff, mypy, import-linter, and other tooling |

Always go through `python3 scripts/dev.py ...`. The task runner discovers Anki's Python automatically and can be overridden with `ANKI_PYTHON` in `.env`.

## First-Time Setup

```bash
python3 scripts/dev.py setup
```

This:

- installs Python dev dependencies into Anki's Python
- creates the add-on symlink in `addons21/1000000002`
- runs `npm install` in `settings_ui/`

## Runtime Dependencies

Anki add-ons cannot rely on `pip install` at user runtime. Audio Quick Editor currently uses only the Python/Qt runtime bundled with Anki plus user-installed `ffmpeg`/`ffprobe` executables, so no Python runtime packages are vendored.

Noise removal uses DeepFilterNet's `deep-filter` executable. The repository bundles the pinned macOS arm64 binary at `addon/anki_audio_quick_editor/bin/deep-filter-0.5.6-aarch64-apple-darwin`; see `addon/anki_audio_quick_editor/bin/README.md` for the upstream release URL and checksum. Other platforms can still configure `deep_filter_path` or provide `deep-filter` on `PATH`.

Prosody visualization can use `praat-parselmouth` when it is already available in Anki's Python, but the shipped add-on does not require it. The required cross-platform path is the built-in ffmpeg/PCM fallback. A dry-run compatibility check on this machine resolved `praat-parselmouth 0.4.7` and `numpy 2.4.4` for Anki Python 3.13, but those packages were not installed or vendored.

Local ffmpeg setup:

- Installed with Homebrew: `ffmpeg 8.1.1`
- Binaries: `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`

## Dev Dependencies

Python dev dependencies live in two places and must stay in sync:

1. `scripts/dev.py` -> `DEV_DEPS`
2. `pyproject.toml` -> `[dependency-groups].dev`

## Frontend Dependencies

The settings UI uses Svelte 5 and Vite from `settings_ui/package.json`. Rebuild committed bundles after editing `.svelte` or `.ts` files:

```bash
python3 scripts/dev.py build
```
