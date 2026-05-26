"""Tests for config deep-merge behavior."""

from __future__ import annotations

import copy

from anki_audio_quick_editor.config_migration import deep_merge


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
