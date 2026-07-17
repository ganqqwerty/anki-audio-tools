"""Rule 46: only RecorderService stores and operates the native controller handle."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / "addon/anki_audio_quick_editor"
SERVICE = ADDON / "recorder/service.py"


def test_native_controller_storage_is_private_to_recorder_service() -> None:
    owners = []
    for path in sorted(ADDON.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(node, ast.Attribute) and node.attr == "_controller" for node in ast.walk(tree)):
            owners.append(path.relative_to(ROOT).as_posix())
    assert owners == ["addon/anki_audio_quick_editor/recorder/service.py"]


def test_recorder_service_does_not_expose_the_handle() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert "controller" not in public_methods
    assert "stop_requested" in public_methods
    assert "cancel_if_owner" in public_methods
    assert "dispose" in public_methods
