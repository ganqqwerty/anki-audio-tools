"""Pytest fixtures for the import-safe Anki test environment."""

from __future__ import annotations

import pytest

from tests.anki_test_mocks import reset_static_mock_modules


@pytest.fixture(autouse=True)
def _reset_anki_test_mocks() -> None:
    """Reset stable aqt mocks so tests do not leak state into each other."""
    reset_static_mock_modules()


@pytest.fixture(autouse=True)
def _isolate_managed_runtime_from_unit_tool_discovery(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep unit tests independent from any downloaded runtime in the worktree."""
    if request.node.get_closest_marker("allow_managed_runtime"):
        return

    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.managed_tool_path", lambda _tool_name: None)
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.expected_managed_tool_path", lambda _tool_name: None)
