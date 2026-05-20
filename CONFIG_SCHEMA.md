# Config Schema Reference

Audio Quick Editor config lives in [`addon/anki_audio_quick_editor/config.json`](addon/anki_audio_quick_editor/config.json) and is validated by [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json).

## Fields

| Key | Type | Purpose |
|-----|------|---------|
| `_config_version` | integer | Schema version used by migrations |
| `enabled` | boolean | Master on/off flag for inline editor controls |
| `debug_logging` | boolean | Raises package logger verbosity |
| `show_ffmpeg_commands` | boolean | Shows the exact ffmpeg command in inline processing status when enabled |
| `repeat_playback_by_default` | boolean | Starts each mounted inline editor Repeat checkbox checked when enabled |
| `repeat_pause_seconds` | number | Default field-local pause between Repeat loop passes, from `0` to `10` seconds |
| `show_graph_by_default` | boolean | Automatically analyzes and opens inline graphs for all audio fields on note load when enabled |
| `manual_trim_small_ms` | integer | Default trim step for inline `-L` and `-R` controls |
| `manual_trim_large_ms` | integer | Reserved larger trim step for future shortcut modifiers |
| `speed_step` | number | Amount added or removed by Faster/Slower |
| `min_speed` | number | Lower bound for pitch-preserving speed changes |
| `max_speed` | number | Upper bound for pitch-preserving speed changes |
| `volume_step_db` | number | Decibel amount added or removed by Volume +/- |
| `min_volume_db` | number | Lower bound for manual gain changes |
| `max_volume_db` | number | Upper bound for manual gain changes |
| `internal_pause_silence_threshold_db` | integer | Silence threshold passed to ffmpeg `silencedetect` on DeepFilterNet-cleaned analysis audio |
| `internal_pause_threshold_ms` | integer | Internal silence duration that qualifies for pause speed-up |
| `internal_pause_target_gap_ms` | integer | Target duration for sped-up pause segments |
| `pause_aggressiveness` | string | Default user-facing Shorten Pauses split-button level: `gentle`, `normal`, or `aggressive` |
| `output_format` | string | Final output format; MVP supports only `mp3` |
| `ffmpeg_path` | string | Optional explicit path to `ffmpeg`; blank uses PATH |
| `deep_filter_path` | string | Optional explicit path to DeepFilterNet `deep-filter`; blank uses a bundled platform binary when available, then PATH |
| `deep_filter_post_filter` | boolean | Enables DeepFilterNet post-filtering for stronger noise suppression and pause-detection analysis |
| `dpdfnet_attn_limit_db` | number | Attenuation limit passed to DPDFNet `--attn-limit-db`; default is `12.0` dB |
| `denoise_algorithm` | string | Default cleanup split-button action: `standard` for DeepFilterNet, `rnnoise` for RNNoise, `dpdfnet` for bundled DPDFNet Lite, or `voice_only` for Sherpa Spleeter vocals extraction |

## Access Pattern

Read config through `mw.addonManager.getConfig(addon_id)` in Anki-facing modules. Merge defaults through `config_migration.migrate_config()` during startup.

Pause shortening uses the internal pause keys with DeepFilterNet as an analysis preprocessor. The user-facing `pause_aggressiveness` default maps to concrete threshold/target values when the editor split button sends a local override; persisted settings are not changed by per-field split-button selections. The persisted `repeat_pause_seconds` value is only the editor default; changes made in a repeat split-button menu are field-local and do not write back to config. DPDFNet denoise always uses the persisted `dpdfnet_attn_limit_db` value. Pause shortening stores retained provenance under `<addon_dir>/aqe_artifacts/<run_id>/`; this artifact location is not currently configurable.
