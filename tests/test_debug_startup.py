from __future__ import annotations

import sys

import anki_audio_quick_editor as addon


def test_debug_anki_does_not_make_debugpy_a_required_startup_dependency(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG_ANKI", "1")
    monkeypatch.setitem(sys.modules, "debugpy", None)
    warnings: list[str] = []
    monkeypatch.setattr(addon.logger, "warning", lambda message, *args: warnings.append(message % args))

    addon._maybe_attach_debugger(wait_for_client=False)

    assert warnings == ["DEBUG_ANKI is set, but debugpy is not installed; continuing without debugger."]
