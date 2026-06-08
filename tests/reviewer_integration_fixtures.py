"""Shared fixtures and fakes for reviewer integration tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt
import pytest

from anki_audio_quick_editor import reviewer_integration


class FakeNote:
    def __init__(self, fields: list[str], note_id: int = 123) -> None:
        self.fields = fields
        self.id = note_id
        self.field_names = ["Front", "Back"][: len(fields)]

    def keys(self) -> list[str]:
        return self.field_names


@pytest.fixture(autouse=True)
def _reset_reviewer_visibility(monkeypatch) -> None:
    monkeypatch.setattr(reviewer_integration, "mw", aqt.mw)
    monkeypatch.setattr(reviewer_integration, "_reviewer_editor_visible", True)
    monkeypatch.setattr(reviewer_integration, "_reviewer_editor_manual_override", False)
    reviewer_integration._ADAPTERS.clear()
    reviewer_integration._EXPLICIT_PANEL_CARD_KEYS.clear()
    aqt.mw.reviewer = None


class FakeCard:
    def __init__(self, note: FakeNote) -> None:
        self._note = note
        self.id = note.id + 1000
        self.loaded = False

    def note(self, reload: bool = False) -> FakeNote:
        del reload
        return self._note

    def load(self) -> None:
        self.loaded = True

    def question_av_tags(self) -> list[object]:
        return [SimpleNamespace(filename="first.mp3")]

    def answer_av_tags(self) -> list[object]:
        return [SimpleNamespace(filename="second.wav")]


class FakeRenderedAudioCard(FakeCard):
    def question_av_tags(self) -> list[object]:
        return []

    def answer_av_tags(self) -> list[object]:
        return []


class FakeWeb:
    def __init__(self) -> None:
        self.onBridgeCmd = MagicMock(return_value="delegated")
        self.bridge_command = None
        self.evals: list[str] = []

    def set_bridge_command(self, func, context) -> None:
        del context
        self.bridge_command = func
        self.onBridgeCmd = func

    def eval(self, js: str) -> None:
        self.evals.append(js)


class FakeAction:
    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled = True
        self.triggered = object()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt API
        self.enabled = enabled

    def setText(self, label: str) -> None:  # noqa: N802 - Qt API
        self.label = label


class FakeMenu:
    def __init__(self) -> None:
        self.actions: list[FakeAction] = []
        self.separator_count = 0

    def addAction(self, label: str) -> FakeAction:  # noqa: N802 - Qt API
        action = FakeAction(label)
        self.actions.append(action)
        return action

    def addSeparator(self) -> None:  # noqa: N802 - Qt API
        self.separator_count += 1
