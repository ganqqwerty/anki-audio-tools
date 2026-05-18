from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks import file_lines


def test_scan_python_file_lengths_reports_warnings_and_errors(tmp_path: Path) -> None:
    root = tmp_path
    addon = root / "addon" / "anki_audio_quick_editor"
    tests_dir = root / "tests"
    addon.mkdir(parents=True)
    tests_dir.mkdir()
    warning_file = addon / "warning.py"
    error_file = tests_dir / "error.py"
    ok_file = addon / "ok.py"
    warning_file.write_text("pass\n" * 401)
    error_file.write_text("pass\n" * 501)
    ok_file.write_text("pass\n" * 400)

    report = file_lines.scan_python_file_lengths(root)

    assert [(item.relative_path, item.lines) for item in report.warnings] == [
        ("addon/anki_audio_quick_editor/warning.py", 401),
    ]
    assert [(item.relative_path, item.lines) for item in report.errors] == [
        ("tests/error.py", 501),
    ]
    assert report.exit_code == 1


def test_scan_python_file_lengths_ignores_generated_and_runtime_artifacts(tmp_path: Path) -> None:
    root = tmp_path
    generated = root / "addon" / "anki_audio_quick_editor" / "contracts_generated.py"
    template = root / "addon" / "anki_audio_quick_editor" / "templates" / "settings" / "bundle.py"
    cache_file = root / "tests" / "__pycache__" / "cached.py"
    generated.parent.mkdir(parents=True)
    template.parent.mkdir(parents=True)
    cache_file.parent.mkdir(parents=True)
    for path in (generated, template, cache_file):
        path.write_text("pass\n" * 700)

    report = file_lines.scan_python_file_lengths(root)

    assert report.warnings == []
    assert report.errors == []
    assert report.exit_code == 0


def test_generated_python_file_predicate_is_explicit(tmp_path: Path) -> None:
    root = tmp_path

    assert file_lines.is_generated_python_file(
        root,
        root / "addon" / "anki_audio_quick_editor" / "contracts_generated.py",
    )
    assert not file_lines.is_generated_python_file(
        root,
        root / "addon" / "anki_audio_quick_editor" / "audio_processor.py",
    )


def test_format_python_file_length_report_includes_warning_and_failure(tmp_path: Path) -> None:
    root = tmp_path
    addon = root / "addon" / "anki_audio_quick_editor"
    addon.mkdir(parents=True)
    (addon / "warning.py").write_text("pass\n" * 401)
    (addon / "error.py").write_text("pass\n" * 501)

    report = file_lines.scan_python_file_lengths(root)

    assert file_lines.format_python_file_length_report(report).splitlines() == [
        "WARNING: 1 Python file(s) exceed 400 lines:",
        "  addon/anki_audio_quick_editor/warning.py: 401",
        "ERROR: 1 Python file(s) exceed 500 lines:",
        "  addon/anki_audio_quick_editor/error.py: 501",
    ]
