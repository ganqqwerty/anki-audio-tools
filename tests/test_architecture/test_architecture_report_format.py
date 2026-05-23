"""Text formatting expectations for the shared architecture report."""

from __future__ import annotations

from . import inspection


def test_format_architecture_report_text_is_concise_when_clean(monkeypatch) -> None:
    monkeypatch.setattr(
        inspection,
        "build_architecture_report",
        lambda: {
            "modules": [
                {
                    "module": "alpha",
                    "layer": "import_safe_core",
                    "addon_deps": [],
                    "side_effects": [],
                    "module_level_anki_imports": [],
                    "any_anki_imports": [],
                    "violations": [],
                }
            ],
            "violations": [],
        },
    )

    assert inspection.format_architecture_report_text() == (
        "PASS: architecture report is clean (1 modules, 0 violations)."
    )


def test_format_architecture_report_text_only_shows_problem_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        inspection,
        "build_architecture_report",
        lambda: {
            "modules": [
                {
                    "module": "alpha",
                    "layer": "import_safe_core",
                    "addon_deps": [],
                    "side_effects": [],
                    "module_level_anki_imports": [],
                    "any_anki_imports": [],
                    "violations": [],
                },
                {
                    "module": "beta",
                    "layer": "ui_adapter",
                    "addon_deps": ["gamma"],
                    "side_effects": ["web_eval"],
                    "module_level_anki_imports": [],
                    "any_anki_imports": ["aqt"],
                    "violations": [{"kind": "anki_import", "detail": "unexpected aqt import"}],
                },
            ],
            "violations": [{"module": "beta", "kind": "anki_import", "detail": "unexpected aqt import"}],
        },
    )

    assert inspection.format_architecture_report_text().splitlines() == [
        "Architecture Report",
        "",
        "beta [ui_adapter]",
        "  addon deps: gamma",
        "  side effects: web_eval",
        "  anki imports: module-level=-; anywhere=aqt",
        "  VIOLATION anki_import: unexpected aqt import",
        "",
        "Summary: 2 modules, 1 violations.",
    ]
