"""Tests for default migration behavior."""

from __future__ import annotations

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)


class TestMigrateConfigDefaults:
    def test_stamps_current_version(self) -> None:
        migrated, changed = migrate_config({}, {"enabled": True})
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_keeps_current_config_without_changes(self) -> None:
        config = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": True,
        }
        migrated, changed = migrate_config(config, config)
        assert migrated == config
        assert changed is False

    def test_picks_up_new_defaults(self) -> None:
        user = {"_config_version": 1, "enabled": False}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": True,
        }
        migrated, changed = migrate_config(user, defaults)
        assert migrated["enabled"] is False
        assert migrated["debug_logging"] is True
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

    def test_picks_up_chorusing_defaults(self) -> None:
        user = {"_config_version": 20, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "chorusing_pause_seconds": 0.0,
            "chorusing_auto_advance_by_default": False,
            "chorusing_auto_advance_repeats": 3,
            "chorusing_marker_interval_ms": 500,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["chorusing_pause_seconds"] == 0.0
        assert migrated["chorusing_auto_advance_by_default"] is False
        assert migrated["chorusing_auto_advance_repeats"] == 3
        assert migrated["chorusing_marker_interval_ms"] == 500
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

    def test_picks_up_selection_marker_shift_button_default(self) -> None:
        user = {"_config_version": 20, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "selection_marker_shift_buttons_enabled": False,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["selection_marker_shift_buttons_enabled"] is False
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_picks_up_editor_history_size_default(self) -> None:
        user = {"_config_version": 2, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "editor_history_size": 100,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["editor_history_size"] == 100
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

    def test_picks_up_audio_trigger_rules_default(self) -> None:
        user = {"_config_version": CURRENT_CONFIG_VERSION, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "audio_trigger_rules": [],
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["audio_trigger_rules"] == []
        assert changed is True

    def test_current_version_only_marks_change_when_defaults_add_values(self) -> None:
        user = {"_config_version": CURRENT_CONFIG_VERSION, "enabled": False}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "debug_logging": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert migrated["enabled"] is False
        assert migrated["debug_logging"] is True
        assert changed is True
