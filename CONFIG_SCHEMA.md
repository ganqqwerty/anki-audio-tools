# Config Schema Reference

Audio Quick Editor config lives in [`addon/anki_audio_quick_editor/config.json`](addon/anki_audio_quick_editor/config.json) and is validated by [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json).

## Fields

Fields are explained in the schema and should not be druplicated here. When a new key is added, make sure not to have contracts too liberal, and restrict datatypes where needed.

## Access Pattern

Read config through `mw.addonManager.getConfig(addon_id)` in Anki-facing modules. Merge defaults through `config_migration.migrate_config()` during startup.

Pause shortening has one persisted detector choice plus algorithm-specific advanced parameter defaults. The user-facing `pause_aggressiveness` value is a preset layer over those advanced values; Settings, editor quick settings, and Browser Bulk can also send operation-local active values as `pause_threshold`, `pause_min_silence_seconds`, `pause_min_speech_seconds`, and `pause_preprocess_denoise`. Operation-local values do not mutate persisted config. Both Silencedetect and Silero VAD can optionally denoise detector input with DPDFNet, but final edits are always rendered from the original working audio. Detected pauses are omitted/cut from the output rather than sped up to a target gap. The persisted `repeat_pause_seconds`, `share_target`, `output_format`, and `editor_button_modes` values are only editor defaults; changes made in split-button menus are field-local until promoted to defaults and do not otherwise write back to config. Batch operations can also send operation-local target format, denoise, and pause values. The persisted `visible_editor_buttons` value controls later editor panel command renders, including main toolbar commands and selection delete actions; an empty list hides every configurable panel command button, including Settings. `aqe:record-voice` and `aqe:play-recording` are normalized as one Record / Play yours panel: either command in the list shows both, and hiding the panel removes both. DPDFNet denoise uses the persisted `dpdfnet_attn_limit_db` value by default, and editor or batch DPDFNet selections can send an operation-local override. Pause shortening stores retained provenance under `<addon_dir>/aqe_artifacts/<run_id>/`; this artifact location is not currently configurable.

For the full mapping from persisted defaults to editor buttons, field-local quick settings, generated files, and editor/batch parity expectations, see [`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`](EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md).
