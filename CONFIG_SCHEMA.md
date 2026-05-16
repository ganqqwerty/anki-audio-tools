# Config Schema Reference

Audio Quick Editor config lives in [`addon/anki_audio_quick_editor/config.json`](addon/anki_audio_quick_editor/config.json) and is validated by [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json).

## Fields

| Key | Type | Purpose |
|-----|------|---------|
| `_config_version` | integer | Schema version used by migrations |
| `enabled` | boolean | Master on/off flag for inline editor controls |
| `debug_logging` | boolean | Raises package logger verbosity |
| `show_ffmpeg_commands` | boolean | Shows the exact ffmpeg command in inline processing status when enabled |
| `manual_trim_small_ms` | integer | Default trim step for inline `-L` and `-R` controls |
| `manual_trim_large_ms` | integer | Reserved larger trim step for future shortcut modifiers |
| `speed_step` | number | Amount added or removed by Faster/Slower |
| `min_speed` | number | Lower bound for pitch-preserving speed changes |
| `max_speed` | number | Upper bound for pitch-preserving speed changes |
| `volume_step_db` | number | Decibel amount added or removed by Volume +/- |
| `min_volume_db` | number | Lower bound for manual gain changes |
| `max_volume_db` | number | Upper bound for manual gain changes |
| `edge_silence_threshold_db` | integer | Silence threshold used by leading/trailing edge trim |
| `edge_silence_min_ms` | integer | Minimum leading/trailing silence duration to trim |
| `internal_pause_silence_threshold_db` | integer | Silence threshold passed to ffmpeg `silencedetect` on DeepFilterNet-cleaned analysis audio |
| `internal_pause_threshold_ms` | integer | Internal silence duration that qualifies for pause speed-up |
| `internal_pause_target_gap_ms` | integer | Target duration for sped-up pause segments |
| `output_format` | string | Final output format; MVP supports only `mp3` |
| `ffmpeg_path` | string | Optional explicit path to `ffmpeg`; blank uses PATH |
| `deep_filter_path` | string | Optional explicit path to DeepFilterNet `deep-filter`; blank uses a bundled platform binary when available, then PATH |
| `deep_filter_post_filter` | boolean | Enables DeepFilterNet post-filtering for stronger noise suppression and pause-detection analysis |

## Access Pattern

Read config through `mw.addonManager.getConfig(addon_id)` in Anki-facing modules. Merge defaults through `config_migration.migrate_config()` during startup.

Pause shortening uses the existing internal pause keys with DeepFilterNet as an analysis preprocessor. It stores retained provenance under `<addon_dir>/aqe_artifacts/<run_id>/`; this artifact location is not currently configurable.
