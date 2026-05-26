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

    def test_removes_deep_filter_path_from_unsupported_config(self) -> None:
        user = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "deep_filter_path": "/custom/deep-filter",
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert "deep_filter_path" not in migrated
        assert changed is True

    def test_picks_up_internal_pause_silence_threshold_default(self) -> None:
        user = {"_config_version": 5, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "internal_pause_silence_threshold_db": -45,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["internal_pause_silence_threshold_db"] == -45
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

    def test_migrates_legacy_speed_volume_defaults_to_factor_ranges(self) -> None:
        user = {
            "_config_version": 21,
            "speed_step": 0.05,
            "min_speed": 0.75,
            "max_speed": 1.5,
            "volume_step_db": 3.0,
            "min_volume_db": -24.0,
            "max_volume_db": 24.0,
            "show_graph_by_default": False,
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "speed_step": 1.5,
            "min_speed": 0.2,
            "max_speed": 5.0,
            "volume_step_db": 15.0,
            "min_volume_db": -40.0,
            "max_volume_db": 40.0,
            "show_graph_by_default": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["speed_step"] == 1.5
        assert migrated["min_speed"] == 0.2
        assert migrated["max_speed"] == 5.0
        assert migrated["volume_step_db"] == 15.0
        assert migrated["min_volume_db"] == -40.0
        assert migrated["max_volume_db"] == 40.0
        assert migrated["show_graph_by_default"] is True
        assert changed is True

    def test_migrates_custom_legacy_speed_step_to_factor(self) -> None:
        user = {
            "_config_version": 21,
            "speed_step": 0.2,
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "speed_step": 1.5,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["speed_step"] == 1.2
        assert changed is True

    def test_picks_up_visible_editor_buttons_default(self) -> None:
        user = {"_config_version": 15, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings", "aqe:share"]
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_adds_share_button_to_visible_editor_buttons_when_missing(self) -> None:
        defaults = {
            "_config_version": 19,
            "visible_editor_buttons": ["aqe:play", "aqe:show-file", "aqe:share", "aqe:settings"],
        }
        user = {
            "_config_version": 17,
            "visible_editor_buttons": ["aqe:play", "aqe:show-file", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert migrated["visible_editor_buttons"] == [
            "aqe:play",
            "aqe:show-file",
            "aqe:share",
            "aqe:settings",
        ]

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

        assert migrated["output_format"] == "mp3"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_removes_deleted_edge_silence_keys(self) -> None:
        user = {
            "_config_version": 6,
            "enabled": True,
            "edge_silence_threshold_db": -35,
            "edge_silence_min_ms": 100,
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert "edge_silence_threshold_db" not in migrated
        assert "edge_silence_min_ms" not in migrated
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
