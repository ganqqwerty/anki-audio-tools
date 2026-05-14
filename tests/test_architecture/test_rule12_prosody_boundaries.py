"""Rule 12: prosody analysis stays import-safe and backend-isolated."""

from __future__ import annotations

from .conftest import ADDON_DIR, get_all_imports, get_module_level_imports


def test_parselmouth_import_is_isolated_to_praat_backend_functions() -> None:
    offenders: list[str] = []
    for path in ADDON_DIR.glob("*.py"):
        relative = path.relative_to(ADDON_DIR).as_posix()
        if relative == "prosody_praat.py":
            assert "parselmouth" not in get_module_level_imports(path)
            continue
        if "parselmouth" in get_all_imports(path):
            offenders.append(relative)

    assert offenders == []
