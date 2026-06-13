"""Preflight helpers for direct e2e pytest runs."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from scripts.dev_tasks.frontend import cmd_build_ui

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_E2E_RUNTIME_ARTIFACTS = (
    ROOT / "addon" / "anki_audio_quick_editor" / "contracts_generated.py",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "settings" / "settings_bundle.js",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "settings" / "settings_bundle.css",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "editor" / "editor_bundle.js",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "editor" / "editor_bundle.css",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "batch" / "batch_bundle.js",
    ROOT / "addon" / "anki_audio_quick_editor" / "templates" / "batch" / "batch_bundle.css",
)


def missing_e2e_runtime_artifacts(
    required_paths: Sequence[Path] = REQUIRED_E2E_RUNTIME_ARTIFACTS,
) -> tuple[Path, ...]:
    """Return missing or empty generated runtime artifacts required by e2e."""
    return tuple(path for path in required_paths if not path.is_file() or path.stat().st_size <= 0)


def ensure_e2e_runtime_artifacts(
    *,
    build_ui: Callable[[], int] = cmd_build_ui,
    required_paths: Sequence[Path] = REQUIRED_E2E_RUNTIME_ARTIFACTS,
) -> None:
    """Build generated runtime artifacts when direct pytest starts without them."""
    missing = missing_e2e_runtime_artifacts(required_paths)
    if not missing:
        return
    rc = build_ui()
    if rc != 0:
        raise RuntimeError(
            "Missing generated e2e runtime artifacts and automatic build failed: "
            f"{_format_paths(missing)}. Run: python3 scripts/dev.py build-ui"
        )
    remaining = missing_e2e_runtime_artifacts(required_paths)
    if remaining:
        raise RuntimeError(
            "Generated e2e runtime artifacts are still missing after build-ui: "
            f"{_format_paths(remaining)}"
        )


def _format_paths(paths: Sequence[Path]) -> str:
    formatted: list[str] = []
    for path in paths:
        try:
            formatted.append(str(path.relative_to(ROOT)))
        except ValueError:
            formatted.append(str(path))
    return ", ".join(formatted)
