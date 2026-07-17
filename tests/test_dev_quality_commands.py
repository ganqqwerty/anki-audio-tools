from __future__ import annotations

from pathlib import Path

from scripts.dev_scripts import quality


def test_architecture_detector_mutation_group_is_focused_and_runnable(monkeypatch) -> None:
    calls: list[tuple[list[str], str]] = []

    monkeypatch.setattr(quality.sys, "platform", "linux")
    monkeypatch.setattr(quality, "find_anki_python", lambda: Path("/anki/python"))
    monkeypatch.setattr(
        quality,
        "run_process",
        lambda command, *, label, **_kwargs: calls.append((command, label)) or 0,
    )

    assert quality.cmd_muttest(["group", "architecture"]) == 0
    assert calls == [
        (
            [
                "/anki/python",
                "-m",
                "mutmut",
                "run",
                "tests.test_architecture.inspection*",
                "scripts.graphs.python_modules*",
            ],
            "mutmut mutation testing",
        )
    ]


def test_recorder_mutation_group_uses_fork_safe_macos_worker(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    monkeypatch.setattr(quality.sys, "platform", "darwin")
    monkeypatch.setattr(quality, "find_anki_python", lambda: Path("/anki/python"))
    monkeypatch.setattr(
        quality,
        "run_process",
        lambda command, *, env=None, **_kwargs: calls.append((command, env)) or 0,
    )

    assert quality.cmd_muttest(["group", "recorder"]) == 0
    assert calls == [
        (
            [
                "/anki/python",
                "-m",
                "mutmut",
                "run",
                "--max-children",
                "1",
                "addon.anki_audio_quick_editor.recorder.model*",
                "addon.anki_audio_quick_editor.recorder.service*",
                "addon.anki_audio_quick_editor.recorder.validation*",
            ],
            {"OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES"},
        )
    ]
