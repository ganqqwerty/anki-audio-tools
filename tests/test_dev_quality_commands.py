from __future__ import annotations

from pathlib import Path

from scripts.dev_scripts import quality


def test_architecture_detector_mutation_group_is_focused_and_runnable(monkeypatch) -> None:
    calls: list[tuple[list[str], str]] = []

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
