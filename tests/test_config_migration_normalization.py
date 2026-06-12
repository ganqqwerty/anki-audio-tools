"""Tests for normalization and canonicalization behavior during migration."""

from __future__ import annotations

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)


class TestMigrateConfigNormalization:
    def test_clamps_editor_history_size(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "editor_history_size": 100,
        }

        low, low_changed = migrate_config({"editor_history_size": -3}, defaults)
        high, high_changed = migrate_config({"editor_history_size": 250}, defaults)
        non_numeric, non_numeric_changed = migrate_config({"editor_history_size": "many"}, defaults)

        assert low["editor_history_size"] == 1
        assert high["editor_history_size"] == 100
        assert non_numeric["editor_history_size"] == 100
        assert low_changed is True
        assert high_changed is True
        assert non_numeric_changed is True

    def test_normalizes_size_reduction_mode(self) -> None:
        user = {
            "_config_version": 20,
            "enabled": True,
            "size_reduction_mode": "tiny",
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "size_reduction_mode": "normal",
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["size_reduction_mode"] == "normal"
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_normalizes_size_reduction_encoder_params(self) -> None:
        user = {
            "_config_version": 20,
            "enabled": True,
            "size_reduction_mode": "gentle",
            "size_reduction_bitrate_kbps": 999,
            "size_reduction_sample_rate_hz": 12345,
            "size_reduction_channels": 7,
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "size_reduction_mode": "normal",
            "size_reduction_bitrate_kbps": 64,
            "size_reduction_sample_rate_hz": 32000,
            "size_reduction_channels": 1,
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["size_reduction_bitrate_kbps"] == 320
        assert migrated["size_reduction_sample_rate_hz"] == 12000
        assert migrated["size_reduction_channels"] == 2
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
