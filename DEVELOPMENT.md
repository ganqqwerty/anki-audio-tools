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
