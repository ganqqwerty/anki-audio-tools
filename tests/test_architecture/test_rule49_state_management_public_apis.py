"""Rule 49: state-management packages expose public APIs without private cycles."""

from pathlib import Path

from .inspection import collect_private_cross_module_imports

ROOT = Path(__file__).resolve().parents[2]


def test_public_frontend_entries_do_not_export_reducer_internals() -> None:
    transport = (ROOT / "settings_ui/src/editor-inline/transport/index.ts").read_text(
        encoding="utf-8"
    )
    practice = (ROOT / "settings_ui/src/editor-inline/practice/index.ts").read_text(
        encoding="utf-8"
    )
    assert "reduce" not in transport
    assert "reduce" not in practice
    assert "html-audio-session-machine" not in transport
    assert "native" not in practice.lower()


def test_python_state_management_has_no_private_cross_module_imports() -> None:
    violations = [
        item
        for item in collect_private_cross_module_imports()
        if item[0].startswith("recorder") or item[1].startswith("recorder")
    ]
    assert violations == []
