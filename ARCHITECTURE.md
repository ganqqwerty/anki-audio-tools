# Architecture

## Overview

Anki Audio Quick Editor keeps the human-facing architecture doc short and puts the executable source of truth in code:

- architecture contracts live in `tests/test_architecture/contracts.py`
- architecture observations and reporting live in `tests/test_architecture/inspection.py`
- pass/fail enforcement happens through `tests/test_architecture/*.py`, `python3 scripts/dev.py architecture-report`, and `python3 scripts/dev.py arch`
- GitNexus is useful for discovery and blast-radius review, but it is not the enforcement source of truth

## Runtime Layers

| Layer | Responsibility |
|-------|---------|----------------|
| Entry point | Startup hook registration, menu setup, config action |
| Import-safe core | Logic that stays safe to inspect and test without loading Anki runtime objects |
| UI adapters | User-facing Browser/editor behavior that touches Anki, Qt, playback, taskman, and media APIs |
| Settings shell | Thin `QDialog` + `AnkiWebView` host only |
| Settings backend | Bridge dispatch and startup state |

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
3. `editor_ui.py` injects the committed editor Svelte bundle near fields containing supported `[sound:...]` tags through `editor_will_load_note`.
4. The editor bundle mounts one compact Svelte control surface per audio field, including an SVG prosody visualizer, and requests async analysis for the current referenced media.
5. `prosody_analyzer.py` uses optional Parselmouth/Praat when available and falls back to ffmpeg-decoded PCM pitch/intensity analysis otherwise.
6. Processing button presses update an `AudioEditState` for the current field, including manual trim, speed, volume, and pause-shortening edits, then render a new MP3 with `audio_processor.py`.
7. Special transform controls call bundled or configured external denoisers through `audio_processor.py`, including DeepFilterNet and RNNoise.
8. `editor_integration.py` writes the result through Anki's media manager and replaces the first supported sound reference in the field.
9. Playback uses Anki's audio player against the latest generated reference, stopping any previous playback first and seeking to the visualizer cursor when set.
10. Undo restores the previous generated reference and edit state without deleting generated media.

## Batchable Operations

Shared batchable operations live in `audio_operations.py` and are the only supported cross-UI operation source of truth:

- `graph`
- `remove_pauses` (`Shorten Pauses` in the UI)
- `slower`
- `faster`
- `volume_down`
- `volume_up`

Rules:

- New batch-capable behavior must be introduced as an import-safe shared operation before it is wired into the editor bridge or Browser dialog.
- Editor bridge strings such as `aqe:faster` are adapter concerns only and must map into shared operations through `editor_actions.py`.
- Browser batch workflows and editor processing must share the same operation semantics for all transform operations.
- Batch runs are single-operation only. Users compose multi-step workflows by running separate jobs sequentially.
- Non-graph batch operations replace the first supported sound reference in the source field with a new generated audio file.
- `graph` remains special: it analyzes the selected source field and appends an SVG reference to a chosen target field.

## Pause Shortening Pipeline

The shared `remove_pauses` operation is DeepFilterNet-assisted and speeds long pauses instead of deleting audio chunks.

1. `audio_processor.py` remains the side-effect boundary for ffmpeg, DeepFilterNet, and artifact filesystem writes.
2. `audio_pipeline.py` is import-safe planning code for parsing `silencedetect` output, building pause timelines, generating filter scripts, and naming retained runs.
3. Editor and Browser adapters pass `<addon_dir>/aqe_artifacts` into `render_audio(...)` so each pause-shortening run keeps its own provenance directory.
4. The pipeline renders `01_working_original.wav` from the original source with manual trims, prepares `02_analysis_input_48k_mono.wav`, runs DeepFilterNet into `03_deep_filter_output/`, detects silence on the cleaned analysis audio, and renders the final MP3 from `01_working_original.wav`.
5. The artifact directory retains the working WAV, analysis WAV, DeepFilter output, raw silence metadata, parsed interval JSON, timeline JSON, generated `filter_complex` script, final MP3 copy, and `manifest.json`.
6. DeepFilterNet is required for this operation. Failures keep the partial artifact directory, record a pause-pipeline support incident, and leave the note unchanged.

## Browser Batch Operations Flow

1. `browser_integration.py` adds `Run Audio Batch Operation...` to the Browser Cards menu and context menu.
2. The Browser selection is deduplicated to note IDs before processing.
3. The dialog builds one operation selector plus source and target field combos from the union of selected-note fields, grouped by note type. The selected value is the field name, so shared field names apply across note types.
4. Source field selection is always required. Target field selection is required only for `graph`.
5. Batch execution runs with `mw.taskman.run_in_background(..., uses_collection=True)` and posts progress/log updates back to the main thread.
6. `batch_operations.py` handles import-safe per-note decisions: missing required fields, empty source fields, and unsupported sound references are skips; missing media and analysis/render/write/update exceptions are failures.
7. For transform operations, only the first supported `[sound:...]` reference in the source field is used. The transformed audio is written to Anki media and replaces that source-field reference in place.
8. For `graph`, the generated SVG is written to Anki media and appended to the chosen target field as an `<img>` reference.
9. `prosody_cache.py` shares cached analysis between editor and batch paths, while `prosody_svg.py` renders deterministic UTF-8 SVG media using the current pitch/intensity style.
10. Successful updates are merged into one custom Anki undo entry where Anki supports it. Cancellation stops before the next note, leaving completed writes intact.

## Settings Flow

1. Python renders HTML containing `window.__INITIAL_STATE__`.
2. The committed `settings_bundle.js` mounts the settings Svelte app.
3. The app sends commands through `pycmd(...)`.
4. `settings/commands.py` handles save/reset/log/async operations.
5. Python sends async completion events back via `webview.eval(...)`.

## Config

Config defaults are stored in `config.json` and migrated into user config:

```json
{
  "_config_version": 11,
  "enabled": true,
  "debug_logging": false,
  "show_ffmpeg_commands": false,
  "repeat_playback_by_default": false,
  "repeat_pause_seconds": 0.0,
  "show_graph_by_default": false,
  "manual_trim_small_ms": 100,
  "manual_trim_large_ms": 500,
  "speed_step": 0.05,
  "min_speed": 0.75,
  "max_speed": 1.5,
  "volume_step_db": 3.0,
  "min_volume_db": -24.0,
  "max_volume_db": 24.0,
  "internal_pause_silence_threshold_db": -45,
  "internal_pause_threshold_ms": 300,
  "internal_pause_target_gap_ms": 100,
  "pause_aggressiveness": "normal",
  "output_format": "mp3",
  "ffmpeg_path": "",
  "deep_filter_path": "",
  "deep_filter_post_filter": true,
  "denoise_algorithm": "standard"
}
```

`config_migration.py` deep-merges defaults into user config and stamps the current schema version.
Editor split-button choices are field-local runtime overrides. Settings provide defaults for trim amount, volume step, speed step, repeat pause, pause aggressiveness, and denoise algorithm, but changing a split-button value in one editor field does not write back to persisted config or other fields.

## Source Of Truth

Use these commands when changing architecture or boundaries:

- `python3 scripts/dev.py architecture-report`
- `python3 scripts/dev.py arch`
- `python3 scripts/dev.py test`
- `python3 scripts/dev.py test-e2e`

The canonical module contracts and allowed side effects are defined in `tests/test_architecture/contracts.py`. Keep this file authoritative and keep this document descriptive.

## Import-Linter Contracts

| Contract | Source modules | Forbidden modules |
|----------|----------------|-------------------|
| `import-safe-no-upper-layers` | Import-safe helper modules, including batch visualization and prosody rendering/cache modules | Browser/editor UI modules and settings backend modules |
| `settings-backend-no-ui` | `settings.commands`, `settings.initial_state` | `editor_integration` |

## Enforced Rules

- Import policy, addon dependency policy, and side-effect policy are enforced by executable module contracts.
- Python bridge command registration and injected editor UI commands must stay in sync.
- Editor TypeScript/Svelte source is part of that bridge-command sync check, not only Python injection code.
- Shared batch operations must stay free of editor bridge strings and editor-adapter imports.
- Optional analysis dependencies such as Parselmouth must stay isolated to their backend module and never become package-level imports.
- The settings shell must stay a thin `QDialog` + `AnkiWebView` wrapper.
- Every production module must have an executable contract entry.
- Broad exception handlers must stay in the function-qualified architecture allowlist with a reason.
