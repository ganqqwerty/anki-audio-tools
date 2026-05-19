from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON_SOURCE_ROOTS = (
    ROOT / "addon" / "anki_audio_quick_editor",
    ROOT / "anki_api_contract",
    ROOT / "e2e",
    ROOT / "scripts",
    ROOT / "tests",
)


def test_unused_import_suppressions_are_not_allowed() -> None:
    suppression_marker = "no" + "qa"
    unused_import_rule = "F" + "401"
    blanket_ruff_suppression = "# ruff: " + suppression_marker
    offenders: list[str] = []
    for source_root in PYTHON_SOURCE_ROOTS:
        for path in source_root.rglob("*.py"):
            if "vendor" in path.parts:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if (suppression_marker in line and unused_import_rule in line) or stripped == blanket_ruff_suppression:
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}")

    assert offenders == []
