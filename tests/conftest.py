"""Pytest fixtures for the import-safe Anki test environment."""

from __future__ import annotations

import pytest

from tests.anki_test_mocks import reset_static_mock_modules


@pytest.fixture(autouse=True)
def _reset_anki_test_mocks() -> None:
    """Reset stable aqt mocks so tests do not leak state into each other."""
    reset_static_mock_modules()
