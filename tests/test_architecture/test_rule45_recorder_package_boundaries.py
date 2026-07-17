"""Rule 45: recorder model, service, and native effects keep strict boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

from .inspection import detect_side_effects_from_source

ROOT = Path(__file__).resolve().parents[2]
RECORDER = ROOT / "addon/anki_audio_quick_editor/recorder"


def test_recorder_model_is_import_safe_and_effect_free() -> None:
    source = (RECORDER / "model.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imports == {"__future__", "dataclasses", "pathlib", "typing"}
    assert detect_side_effects_from_source(source) == set()


def test_recorder_validation_is_import_safe_and_effect_free() -> None:
    source = (RECORDER / "validation.py").read_text(encoding="utf-8")
    assert detect_side_effects_from_source(source) == set()


def test_native_adapter_modules_are_not_imported_by_the_model_or_service() -> None:
    for name in ("model.py", "service.py"):
        source = (RECORDER / name).read_text(encoding="utf-8")
        assert "native_backend" not in source
        assert "native_macos" not in source
        assert "native_qt" not in source
