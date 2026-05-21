"""Tests for config_migration.py."""

from __future__ import annotations

import copy

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    deep_merge,
    migrate_config,
)


class TestDeepMerge:
    def test_empty_user_returns_defaults(self) -> None:
        defaults = {"enabled": True, "flags": {"debug": False}}
        assert deep_merge(defaults, {}) == defaults

    def test_nested_user_values_override_defaults(self) -> None:
        defaults = {"flags": {"debug": False, "verbose": False}}
        user = {"flags": {"debug": True}}
        assert deep_merge(defaults, user) == {"flags": {"debug": True, "verbose": False}}

    def test_unknown_user_keys_are_preserved(self) -> None:
        result = deep_merge({"enabled": True}, {"custom": {"x": 1}})
        assert result["custom"] == {"x": 1}

    def test_scalar_user_value_replaces_nested_default(self) -> None:
        defaults = {"flags": {"debug": False, "verbose": False}}
        assert deep_merge(defaults, {"flags": "manual"}) == {"flags": "manual"}

    def test_inputs_are_not_mutated(self) -> None:
        defaults = {"flags": {"debug": False}}
        user = {"flags": {"debug": True}}
        defaults_copy = copy.deepcopy(defaults)
        user_copy = copy.deepcopy(user)
        deep_merge(defaults, user)
        assert defaults == defaults_copy
        assert user == user_copy

    def test_result_does_not_share_nested_defaults_or_user_values(self) -> None:
        defaults = {"flags": {"debug": False}, "nested": {"levels": [1, 2]}}
        user = {"custom": {"items": ["a", "b"]}}

        result = deep_merge(defaults, user)
        result["flags"]["debug"] = True
        result["nested"]["levels"].append(3)
        result["custom"]["items"].append("c")

        assert defaults == {"flags": {"debug": False}, "nested": {"levels": [1, 2]}}
        assert user == {"custom": {"items": ["a", "b"]}}


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

    def test_picks_up_deep_filter_defaults(self) -> None:
        user = {"_config_version": 4, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "deep_filter_path": "",
            "deep_filter_post_filter": True,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["deep_filter_path"] == ""
        assert migrated["deep_filter_post_filter"] is True
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
            "repeat_playback_by_default": False,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["repeat_playback_by_default"] is False
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

    def test_picks_up_show_graph_default(self) -> None:
        user = {"_config_version": 8, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "show_graph_by_default": False,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["show_graph_by_default"] is False
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

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
