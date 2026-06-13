"""Rule 28: audio processor facade has one dependency construction point."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR


def test_audio_processor_constructs_audio_module_deps_once() -> None:
    text = (ADDON_DIR / "audio_processor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)

    constructions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "AudioModuleDeps"
    ]

    assert len(constructions) == 1


def test_audio_processor_sync_functions_use_shared_builder() -> None:
    text = (ADDON_DIR / "audio_processor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    sync_names = {
        "_sync_tool_dependencies",
        "_sync_external_dependencies",
        "_sync_pause_dependencies",
        "_sync_rendering_dependencies",
        "_sync_noise_dependencies",
        "_sync_pitch_hum_dependencies",
    }

    calls_by_function: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in sync_names:
            calls_by_function[node.name] = sum(
                1
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "_audio_module_deps"
            )

    assert calls_by_function == {name: 1 for name in sync_names}
