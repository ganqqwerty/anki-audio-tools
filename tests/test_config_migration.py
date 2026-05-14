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

    def test_inputs_are_not_mutated(self) -> None:
        defaults = {"flags": {"debug": False}}
        user = {"flags": {"debug": True}}
        defaults_copy = copy.deepcopy(defaults)
        user_copy = copy.deepcopy(user)
        deep_merge(defaults, user)
        assert defaults == defaults_copy
        assert user == user_copy


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
