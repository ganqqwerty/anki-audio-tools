"""Tests for versioned config migration behavior."""

from __future__ import annotations

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)


class TestMigrateConfig:
    def test_stamps_current_version(self) -> None:
        migrated, changed = migrate_config({}, {"enabled": True})
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_keeps_current_config_without_changes(self) -> None:
        config = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": False,
        }
        migrated, changed = migrate_config(config, config)
        assert migrated == config
        assert changed is False

    def test_picks_up_new_defaults(self) -> None:
        user = {"_config_version": 1, "enabled": False}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": False,
        }
        migrated, changed = migrate_config(user, defaults)
        assert migrated["enabled"] is False
        assert migrated["debug_logging"] is False
        assert changed is True

    def test_picks_up_deep_filter_post_filter_default(self) -> None:
        user = {"_config_version": 4, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "deep_filter_post_filter": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["deep_filter_post_filter"] is True
        assert changed is True

    def test_picks_up_pause_detection_defaults(self) -> None:
        user = {"_config_version": 5, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "pause_detection_algorithm": "silencedetect",
            "pause_silencedetect_threshold_db": -45,
            "pause_silencedetect_min_silence_seconds": 0.30,
            "pause_silencedetect_min_speech_seconds": 0.10,
            "pause_silencedetect_preprocess_denoise": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["pause_detection_algorithm"] == "silencedetect"
        assert migrated["pause_silencedetect_threshold_db"] == -45
        assert migrated["pause_silencedetect_min_silence_seconds"] == 0.30
        assert migrated["pause_silencedetect_min_speech_seconds"] == 0.10
        assert migrated["pause_silencedetect_preprocess_denoise"] is True
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_repeat_playback_default(self) -> None:
        user = {"_config_version": 7, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "repeat_playback_by_default": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["repeat_playback_by_default"] is True
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_repeat_pause_default(self) -> None:
        user = {"_config_version": 10, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "repeat_pause_seconds": 0.0,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["repeat_pause_seconds"] == 0.0
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_share_target_default(self) -> None:
        user = {"_config_version": 20, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "share_target": "litterbox",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["share_target"] == "litterbox"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_show_graph_default(self) -> None:
        user = {"_config_version": 8, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "show_graph_by_default": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["show_graph_by_default"] is True
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_visible_editor_buttons_default(self) -> None:
        user = {"_config_version": 15, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings"]
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_removes_stale_visible_editor_buttons(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": ["aqe:play", "aqe:share", "aqe:settings"],
        }
        user = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": ["aqe:play", "aqe:record-voice", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings"]

    def test_picks_up_editor_button_modes_default(self) -> None:
        user = {"_config_version": 18, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "editor_button_modes": {
                "aqe:play": "text",
                "aqe:settings": "text",
            },
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["editor_button_modes"] == {
            "aqe:play": "text",
            "aqe:settings": "text",
        }
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_normalizes_editor_button_modes(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "editor_button_modes": {
                "aqe:play": "text",
                "aqe:settings": "text",
            },
        }
        user = {
            "_config_version": 18,
            "editor_button_modes": {
                "aqe:play": "icon",
                "aqe:settings": "wide",
                "aqe:unknown": "icon",
            },
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["editor_button_modes"] == {
            "aqe:play": "icon",
            "aqe:settings": "text",
        }

    def test_picks_up_graph_display_defaults(self) -> None:
        user = {"_config_version": 11, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "graph_voice_range": "general",
            "graph_recording_condition": "auto",
            "graph_smoothness": "very_smooth",
            "graph_connect_short_dropouts_ms": 240,
            "graph_voice_lock": "balanced",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["graph_voice_range"] == "general"
        assert migrated["graph_recording_condition"] == "auto"
        assert migrated["graph_smoothness"] == "very_smooth"
        assert migrated["graph_connect_short_dropouts_ms"] == 240
        assert migrated["graph_voice_lock"] == "balanced"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_snaps_legacy_dpdfnet_attenuation_to_supported_aggressiveness(self) -> None:
        user = {
            "_config_version": 13,
            "enabled": True,
            "dpdfnet_attn_limit_db": 8.5,
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "dpdfnet_attn_limit_db": 12.0,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["dpdfnet_attn_limit_db"] == 6.0
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_pitch_hum_mode_default(self) -> None:
        user = {"_config_version": 14, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "pitch_hum_mode": "direct",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["pitch_hum_mode"] == "direct"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_normalizes_output_format(self) -> None:
        user = {
            "_config_version": 15,
            "enabled": True,
            "output_format": " FLAC ",
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "output_format": "mp3",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["output_format"] == "flac"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_snaps_unknown_output_format_to_default(self) -> None:
        user = {
            "_config_version": 15,
            "enabled": True,
            "output_format": "aac",
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "output_format": "mp3",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["output_format"] == "source"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_snaps_unknown_pause_detection_algorithm_to_default(self) -> None:
        user = {
            "_config_version": 15,
            "enabled": True,
            "pause_detection_algorithm": "unknown",
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "pause_detection_algorithm": "silencedetect",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["pause_detection_algorithm"] == "silencedetect"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_current_version_only_marks_change_when_defaults_add_values(self) -> None:
        user = {"_config_version": CURRENT_CONFIG_VERSION, "enabled": False}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": False,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert migrated["enabled"] is False
        assert migrated["debug_logging"] is False
        assert changed is True
