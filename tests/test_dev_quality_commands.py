from __future__ import annotations

from pathlib import Path

import scripts.dev as dev
from scripts.dev_tasks import quality_tools


def test_lint_runs_safe_autofix_before_check(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(dev, "_find_anki_python", lambda: anki_python)
    monkeypatch.setattr(dev, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0)

    assert dev.cmd_lint() == 0
    assert calls == [
        "/anki/python -m ruff check --fix",
        "/anki/python -m ruff check",
    ]


def test_lint_stops_when_safe_autofix_fails(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(dev, "_find_anki_python", lambda: anki_python)
    monkeypatch.setattr(dev, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 42)

    assert dev.cmd_lint() == 42
    assert calls == ["/anki/python -m ruff check --fix"]


def test_qodana_runs_with_committed_config(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(
        quality_tools.shutil,
        "which",
        lambda name: "/usr/local/bin/qodana" if name == "qodana" else None,
    )
    monkeypatch.setattr(
        quality_tools,
        "_run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or 0,
    )

    assert quality_tools.cmd_qodana() == 0
    assert calls == [
        (
            [
                "/usr/local/bin/qodana",
                "--disable-update-checks",
                "scan",
                "--config",
                "qodana.yaml",
                "--project-dir",
                str(quality_tools.ROOT),
                "--print-problems",
            ],
            {"label": "qodana code quality"},
        )
    ]


def test_qodana_reports_missing_cli(monkeypatch, capsys) -> None:
    monkeypatch.setattr(quality_tools.shutil, "which", lambda name: None)

    assert quality_tools.cmd_qodana() == 1

    captured = capsys.readouterr()
    assert "qodana not found" in captured.err


def test_cmd_i18n_reports_failures(monkeypatch, capsys) -> None:
    monkeypatch.setattr(dev, "locale_catalog_violations", lambda: ["de.json missing keys: beta"])

    assert dev.cmd_i18n() == 1

    captured = capsys.readouterr()
    assert "FAIL: locale catalogs differ from en.json:" in captured.out
    assert "de.json missing keys: beta" in captured.out
