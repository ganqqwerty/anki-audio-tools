from __future__ import annotations

from pathlib import Path

from scripts.dev_scripts import quality, tooling
from scripts.dev_tasks import quality_tools

ANKI_PYTHON = str(Path("/anki/python"))


def test_lint_runs_safe_autofix_before_check(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(tooling, "find_anki_python", lambda: anki_python)
    monkeypatch.setattr(tooling, "run_process", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0)

    assert tooling.cmd_lint([]) == 0
    assert calls == [
        f"{ANKI_PYTHON} -m ruff check --fix",
        f"{ANKI_PYTHON} -m ruff check",
    ]


def test_lint_stops_when_safe_autofix_fails(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(tooling, "find_anki_python", lambda: anki_python)
    monkeypatch.setattr(tooling, "run_process", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 42)

    assert tooling.cmd_lint([]) == 42
    assert calls == [f"{ANKI_PYTHON} -m ruff check --fix"]


def test_arch_uses_windows_lint_imports_executable(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    anki_python = scripts_dir / "python.exe"
    lint_imports = scripts_dir / "lint-imports.exe"
    lint_imports.write_text("tool", encoding="utf-8")

    monkeypatch.setattr(tooling.os, "name", "nt")
    monkeypatch.setattr(tooling, "find_anki_python", lambda: anki_python)
    monkeypatch.setattr(tooling, "run_process", lambda cmd, **kwargs: calls.append((cmd, kwargs)) or 0)

    assert tooling.cmd_arch([]) == 0
    assert calls == [
        (
            [str(lint_imports)],
            {"env": {"PYTHONPATH": "addon"}, "label": "import-linter architecture check"},
        )
    ]


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
    monkeypatch.setattr(quality, "locale_catalog_violations", lambda: ["de.json missing keys: beta"])

    assert quality.cmd_i18n([]) == 1

    captured = capsys.readouterr()
    assert "FAIL: locale catalogs differ from en.json:" in captured.out
    assert "de.json missing keys: beta" in captured.out
