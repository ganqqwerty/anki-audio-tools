"""Tests for development quality-gate helpers."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.quality import (
    _radon_maintainability_violations,
    format_locale_catalog_report,
    locale_catalog_violations,
)


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


def test_locale_catalog_violations_report_missing_and_extra_keys(tmp_path: Path) -> None:
    locale_dir = tmp_path / "locales"
    locale_dir.mkdir()
    (locale_dir / "en.json").write_text('{"alpha":"A","beta":"B"}', encoding="utf-8")
    (locale_dir / "de.json").write_text('{"alpha":"A","gamma":"C"}', encoding="utf-8")

    assert locale_catalog_violations(locale_dir) == [
        "de.json missing keys: beta",
        "de.json extra keys: gamma",
    ]


def test_format_locale_catalog_report_lists_each_violation() -> None:
    report = format_locale_catalog_report([
        "de.json missing keys: beta",
        "de.json extra keys: gamma",
    ])

    assert report == (
        "FAIL: locale catalogs differ from en.json:\n"
        "  de.json missing keys: beta\n"
        "  de.json extra keys: gamma"
    )
