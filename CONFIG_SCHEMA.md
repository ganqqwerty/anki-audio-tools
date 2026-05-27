# Config Schema Reference

Audio Quick Editor config lives in [`addon/anki_audio_quick_editor/config.json`](addon/anki_audio_quick_editor/config.json) and is validated by [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json).

## Fields

| Key | Type | Purpose |
|-----|------|---------|
| `_config_version` | integer | Schema version used by migrations |
| `enabled` | boolean | Master on/off flag for inline editor controls |
| `debug_logging` | boolean | Raises package logger verbosity |
| `show_ffmpeg_commands` | boolean | Shows debug command details for external tools in inline processing status when enabled |
| `repeat_playback_by_default` | boolean | Starts each mounted inline editor Repeat checkbox checked when enabled |
| `repeat_pause_seconds` | number | Default field-local pause between Repeat loop passes, from `0` to `10` seconds |
| `share_target` | string | Default Share split-button upload target: `catbox` or `litterbox` |
| `show_graph_by_default` | boolean | Automatically analyzes and opens inline graphs for all audio fields on note load when enabled |
| `visible_editor_buttons` | string array | Ordered list of top-level inline editor button commands to render; removing a command hides that button |
| `editor_button_modes` | object | Per-command display mode map for inline editor buttons: `icon` or `text` |
| `graph_voice_range` | string | Default voice range hint for graph pitch extraction: `bass`, `low`, `general`, `high`, or `child` |
| `graph_recording_condition` | string | Default recording condition hint for graph analysis: `auto`, `very_noisy`, `noisy`, `normal`, `clean`, or `studio` |
| `graph_smoothness` | string | Default graph smoothing level: `raw`, `balanced`, `smooth`, or `very_smooth` |
| `graph_connect_short_dropouts_ms` | integer | Maximum short voicing dropout, in milliseconds, that graph rendering reconnects |
| `graph_voice_lock` | string | Default pitch track stability preference: `loose`, `balanced`, or `stable` |
| `speed_step` | number | Amount added or removed by Faster/Slower |
| `min_speed` | number | Lower bound for pitch-preserving speed changes |
| `max_speed` | number | Upper bound for pitch-preserving speed changes |
| `volume_step_db` | number | Decibel amount added or removed by Volume +/- |
| `min_volume_db` | number | Lower bound for manual gain changes |
| `max_volume_db` | number | Upper bound for manual gain changes |
| `pause_aggressiveness` | string | Default user-facing Shorten Pauses split-button level: `gentle`, `normal`, or `aggressive` |
| `pause_detection_algorithm` | string | Default pause detection backend: `silencedetect` or `silero_vad` |
| `pause_silencedetect_threshold_db` | number | ffmpeg `silencedetect` threshold in dB for the Silencedetect detector |
| `pause_silencedetect_min_silence_seconds` | number | Minimum removable silence duration for Silencedetect |
| `pause_silencedetect_min_speech_seconds` | number | Minimum non-silence island that Silencedetect keeps separate instead of merging adjacent pauses |
| `pause_silencedetect_preprocess_denoise` | boolean | Runs DPDFNet denoise before Silencedetect analysis; final rendering still uses original audio |
| `pause_silero_threshold` | number | Silero VAD speech probability threshold from `0` to `1` |
| `pause_silero_min_silence_seconds` | number | Minimum removable pause duration for Silero VAD |
| `pause_silero_min_speech_seconds` | number | Minimum speech island that Silero VAD keeps separate instead of merging adjacent pauses |
| `pause_silero_preprocess_denoise` | boolean | Runs DPDFNet denoise before Silero VAD analysis; final rendering still uses original audio |
| `output_format` | string | Default target for Convert operations: `mp3`, `m4a`, `wav`, or `flac` |
| `ffmpeg_path` | string | Explicit path to `ffmpeg`, prefilled from the current platform default |
| `deep_filter_post_filter` | boolean | Enables DeepFilterNet post-filtering for stronger Standard denoise output |
| `dpdfnet_attn_limit_db` | number | Discrete DPDFNet aggressiveness value passed as `--attn-limit-db`: `6.0` gentle, `12.0` normal, or `18.0` aggressive |
| `denoise_algorithm` | string | Default cleanup split-button action: `standard` for DeepFilterNet, `rnnoise` for RNNoise, `dpdfnet` for bundled DPDFNet Lite, or `voice_only` for Sherpa Spleeter vocals extraction |
| `pitch_hum_mode` | string | Default Pitch Hum split-button mode: `direct` or `pitch_tier` |

## Access Pattern

Read config through `mw.addonManager.getConfig(addon_id)` in Anki-facing modules. Merge defaults through `config_migration.migrate_config()` during startup.

Pause shortening has one persisted detector choice plus algorithm-specific advanced parameter defaults. The user-facing `pause_aggressiveness` value is a preset layer over those advanced values; Settings, editor quick settings, and Browser Bulk can also send operation-local active values as `pause_threshold`, `pause_min_silence_seconds`, `pause_min_speech_seconds`, and `pause_preprocess_denoise`. Operation-local values do not mutate persisted config. Both Silencedetect and Silero VAD can optionally denoise detector input with DPDFNet, but final edits are always rendered from the original working audio. Detected pauses are omitted/cut from the output rather than sped up to a target gap. The persisted `repeat_pause_seconds`, `share_target`, `output_format`, and `editor_button_modes` values are only editor defaults; changes made in split-button menus are field-local until promoted to defaults and do not otherwise write back to config. Batch operations can also send operation-local target format, denoise, and pause values. The persisted `visible_editor_buttons` value controls later editor toolbar renders; an empty list hides every top-level toolbar button, including Settings. DPDFNet denoise uses the persisted `dpdfnet_attn_limit_db` value by default, and editor or batch DPDFNet selections can send an operation-local override. Pause shortening stores retained provenance under `<addon_dir>/aqe_artifacts/<run_id>/`; this artifact location is not currently configurable.

For the full mapping from persisted defaults to editor buttons, field-local quick settings, generated files, and editor/batch parity expectations, see [`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`](EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md).
