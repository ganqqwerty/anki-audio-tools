# Architecture

## Overview

Anki Audio Quick Editor keeps a tested Anki shell and adds focused inline and batch audio workflows:

- a thin `__init__.py` bootstrap
- centralized config migration
- isolated collection/database helpers
- a Svelte settings UI delivered through `AnkiWebView`
- Anki-import-safe sound-reference, edit-state, and ffmpeg helpers
- Anki-import-safe prosody analysis, caching, SVG rendering, and batch decision helpers
- thin Anki editor integration for inline controls, playback, automatic media replacement, visualization, and Undo
- thin Anki Browser integration for selected-note batch visualization generation

## Runtime Layers

| Layer | Modules | Responsibility |
|-------|---------|----------------|
| Entry point | `__init__.py` | Startup hook registration, menu setup, config action |
| Anki-import-safe helpers | `_version.py`, `audio_processor.py`, `audio_state.py`, `batch_visualization.py`, `config_migration.py`, `db_helpers.py`, `editor_actions.py`, `editor_ui.py`, `errors.py`, `prosody_analyzer.py`, `prosody_cache.py`, `prosody_fallback.py`, `prosody_praat.py`, `prosody_svg.py`, `prosody_types.py`, `settings_state.py`, `sound_refs.py` | Logic without module-level Anki imports |
| UI modules | `browser_integration.py`, `editor_integration.py` | User-facing behavior that touches Anki Browser/editor, media, playback, task, and Qt APIs |
| Settings shell | `settings/__init__.py` | `QDialog` + `AnkiWebView` host only |
| Settings backend | `settings/commands.py`, `settings/initial_state.py` | Bridge dispatch and startup state |

## Bootstrap Hooks

`__init__.py` registers these startup callbacks on `gui_hooks.main_window_did_init`:

- `_migrate_config`
- `_setup_file_logging`
- `_apply_log_level`
- `_setup_editor_integration`
- `_setup_browser_integration`
- `_setup_menu`

`editor_integration.py` registers editor hooks for field control injection and bridge commands. `browser_integration.py` registers `browser_menus_did_init` and `browser_will_show_context_menu` so the batch action is available from the Browser Cards menu and row context menu.

## Editor Flow

1. `__init__.py` registers editor integration during `main_window_did_init`.
2. `editor_integration.py` attaches `aqe:*` bridge commands on `editor_did_init`.
3. `editor_ui.py` injects compact controls near fields containing supported `[sound:...]` tags through `editor_will_load_note`.
4. Controls mount a compact SVG prosody visualizer and request async analysis for the current referenced media.
5. `prosody_analyzer.py` uses optional Parselmouth/Praat when available and falls back to ffmpeg-decoded PCM pitch/intensity analysis otherwise.
6. Processing button presses update an `AudioEditState` for the current field and render a new MP3 with `audio_processor.py`.
7. `editor_integration.py` writes the result through Anki's media manager and replaces the first supported sound reference in the field.
8. Playback uses Anki's audio player against the latest generated reference, stopping any previous playback first and seeking to the visualizer cursor when set.
9. Undo restores the previous generated reference and edit state without deleting generated media.

## Browser Batch Visualization Flow

1. `browser_integration.py` adds `Generate Audio Visualizations...` to the Browser Cards menu and context menu.
2. The Browser selection is deduplicated to note IDs before processing.
3. The dialog builds source and target field combos from the union of selected-note fields, grouped by note type. The selected value is the field name, so shared field names apply across note types.
4. Batch execution runs with `mw.taskman.run_in_background(..., uses_collection=True)` and posts progress/log updates back to the main thread.
5. `batch_visualization.py` handles import-safe per-note decisions: missing source/target fields, empty source fields, and unsupported sound references are skips; missing media and analysis/render/write/update exceptions are failures.
6. Only the first supported `[sound:...]` reference in the source field is used. The generated SVG is written to Anki media and appended to the target field as an `<img>` reference.
7. `prosody_cache.py` shares cached analysis between editor and batch paths, while `prosody_svg.py` renders deterministic UTF-8 SVG media using the current pitch/intensity style.
8. Successful updates are merged into one custom Anki undo entry where Anki supports it. Cancellation stops before the next note, leaving completed writes intact.

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

## Import-Linter Contracts

| Contract | Source modules | Forbidden modules |
|----------|----------------|-------------------|
| `import-safe-no-upper-layers` | Import-safe helper modules, including batch visualization and prosody rendering/cache modules | Browser/editor UI modules and settings backend modules |
| `settings-backend-no-ui` | `settings.commands`, `settings.initial_state` | `editor_integration` |

## Enforced Rules

- Anki-import-safe modules must not import `aqt` or `anki` at module level.
- Thin Browser/editor/settings runtime modules keep Anki/Qt imports inside function boundaries where practical.
- Python bridge command registration and injected editor UI commands must stay in sync.
- Optional analysis dependencies such as Parselmouth must stay isolated to their backend module and never become package-level imports.
- Collection/database access must stay inside `db_helpers.py`.
- The settings shell must stay a thin `QDialog` + `AnkiWebView` wrapper.
- Every production module must be classified into a layer.
- Leaf modules must stay safe to import without dragging in runtime side effects.
