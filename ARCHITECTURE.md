# Architecture

## Overview

Anki Audio Quick Editor keeps a tested Anki shell and adds a focused inline audio-editing pipeline:

- a thin `__init__.py` bootstrap
- centralized config migration
- isolated collection/database helpers
- a Svelte settings UI delivered through `AnkiWebView`
- Anki-import-safe sound-reference, edit-state, and ffmpeg helpers
- thin Anki editor integration for inline controls, playback, automatic media replacement, and Undo

## Runtime Layers

| Layer | Modules | Responsibility |
|-------|---------|----------------|
| Entry point | `__init__.py` | Startup hook registration, menu setup, config action |
| Anki-import-safe helpers | `_version.py`, `audio_processor.py`, `audio_state.py`, `config_migration.py`, `db_helpers.py`, `editor_actions.py`, `editor_ui.py`, `errors.py`, `settings_state.py`, `sound_refs.py` | Logic without module-level Anki imports |
| UI modules | `editor_integration.py` | User-facing behavior that touches Anki editor, media, playback, and task APIs |
| Settings shell | `settings/__init__.py` | `QDialog` + `AnkiWebView` host only |
| Settings backend | `settings/commands.py`, `settings/initial_state.py` | Bridge dispatch and startup state |

## Editor Flow

1. `__init__.py` registers editor integration during `main_window_did_init`.
2. `editor_integration.py` attaches `aqe:*` bridge commands on `editor_did_init`.
3. `editor_ui.py` injects compact controls near fields containing supported `[sound:...]` tags through `editor_will_load_note`.
4. Processing button presses update an `AudioEditState` for the current field and render a new MP3 with `audio_processor.py`.
5. `editor_integration.py` writes the result through Anki's media manager and replaces the first supported sound reference in the field.
6. Playback uses Anki's audio player against the latest generated reference, stopping any previous playback first.
7. Undo restores the previous generated reference and edit state without deleting generated media.

## Settings Flow

1. Python renders HTML containing `window.__INITIAL_STATE__`.
2. The committed `settings_bundle.js` mounts the Svelte app.
3. The app sends commands through `pycmd(...)`.
4. `settings/commands.py` handles save/reset/log/async operations.
5. Python sends async completion events back via `webview.eval(...)`.

## Config

Config defaults are stored in `config.json` and migrated into user config:

```json
{
  "_config_version": 3,
  "enabled": true,
  "debug_logging": false,
  "show_ffmpeg_commands": false,
  "manual_trim_small_ms": 100,
  "manual_trim_large_ms": 500,
  "speed_step": 0.05,
  "min_speed": 0.75,
  "max_speed": 1.5,
  "edge_silence_threshold_db": -35,
  "edge_silence_min_ms": 100,
  "internal_pause_threshold_ms": 300,
  "internal_pause_target_gap_ms": 100,
  "output_format": "mp3",
  "ffmpeg_path": ""
}
```

`config_migration.py` deep-merges defaults into user config and stamps the current schema version.

## Enforced Rules

- Anki-import-safe modules must not import `aqt` or `anki` at module level.
- Thin editor/settings runtime modules keep Anki imports inside function boundaries where practical.
- Python bridge command registration and injected editor UI commands must stay in sync.
- Collection/database access must stay inside `db_helpers.py`.
- The settings shell must stay a thin `QDialog` + `AnkiWebView` wrapper.
- Every production module must be classified into a layer.
- Leaf modules must stay safe to import without dragging in runtime side effects.
