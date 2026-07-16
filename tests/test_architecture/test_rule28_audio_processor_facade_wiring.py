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


def test_audio_processor_has_one_public_typed_dependency_installation_seam() -> None:
    text = (ADDON_DIR / "audio_processor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    installers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "install_audio_dependencies"
    ]
    assert len(installers) == 1
    assert any(
        isinstance(node, ast.Name) and node.id == "audio_module_dependencies"
        for node in ast.walk(installers[0])
    )
    assert not any(
        isinstance(node, ast.FunctionDef) and node.name.startswith("_sync_")
        for node in ast.walk(tree)
    )
