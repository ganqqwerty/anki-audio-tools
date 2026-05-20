"""Tests for development quality-gate helpers."""

from __future__ import annotations

from scripts.dev_tasks.quality import _radon_maintainability_violations


def test_radon_maintainability_ignores_generated_contracts() -> None:
    report = {
        "addon/anki_audio_quick_editor/contracts_generated.py": {
            "mi": 1.27,
            "rank": "C",
        },
        "addon/anki_audio_quick_editor/browser_dialog.py": {
            "mi": 4.5,
            "rank": "C",
        },
    }

    assert _radon_maintainability_violations(report) == [
        "addon/anki_audio_quick_editor/browser_dialog.py rank=C mi=4.5"
    ]
