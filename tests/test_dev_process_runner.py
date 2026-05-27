from __future__ import annotations

import sys
from pathlib import Path

from scripts.dev_tasks import process


def test_process_run_suppresses_subprocess_output_by_default(capsys) -> None:
    process.set_verbose(False)

    rc = process._run([sys.executable, "-c", "print('hidden subprocess output')"], label="sample command")

    captured = capsys.readouterr()
    assert rc == 0
    assert "sample command" in captured.out
    assert "hidden subprocess output" not in captured.out


def test_process_run_reports_failure_as_failure(capsys) -> None:
    process.set_verbose(False)

    rc = process._run([sys.executable, "-c", "raise SystemExit(7)"], label="failing command")

    captured = capsys.readouterr()
    assert rc == 7
    assert "FAILED with exit code 7" in captured.out
    assert "finished with exit code 7" not in captured.out


def test_process_run_can_show_subprocess_output_only_on_failure(capsys) -> None:
    process.set_verbose(False)

    success_rc = process._run(
        [sys.executable, "-c", "print('hidden success output')"],
        label="passing command",
        show_output_on_failure=True,
    )
    failure_rc = process._run(
        [sys.executable, "-c", "print('shown failure output'); raise SystemExit(9)"],
        label="failing command",
        show_output_on_failure=True,
    )

    captured = capsys.readouterr()
    assert success_rc == 0
    assert failure_rc == 9
    assert "hidden success output" not in captured.out
    assert "shown failure output" in captured.out
    assert "output from failed command" in captured.out
    assert "rerun with --verbose" not in captured.out


def test_process_run_capture_can_show_captured_output_on_failure(capsys) -> None:
    process.set_verbose(False)

    rc, output = process._run_capture(
        [sys.executable, "-c", "print('captured failure output'); raise SystemExit(5)"],
        label="captured failing command",
        show_output_on_failure=True,
    )

    captured = capsys.readouterr()
    assert rc == 5
    assert "captured failure output" in output
    assert "captured failure output" in captured.out
    assert "rerun with --verbose" not in captured.out


def test_process_run_pytest_failure_output_omits_passing_case_capture(capsys, tmp_path: Path) -> None:
    process.set_verbose(False)
    test_file = tmp_path / "test_capture.py"
    test_file.write_text(
        """
def test_case_1():
    print("case 1 detail")


def test_case_5():
    print("case 5 detail")
    assert False
""".lstrip(),
        encoding="utf-8",
    )

    rc = process._run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--tb=short",
            "--show-capture=all",
            str(test_file),
        ],
        cwd=tmp_path,
        label="sample pytest failure",
        show_output_on_failure=True,
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "case 5 detail" in captured.out
    assert "case 1 detail" not in captured.out


def test_process_run_streams_subprocess_output_in_verbose_mode(capsys) -> None:
    process.set_verbose(True)

    try:
        rc = process._run([sys.executable, "-c", "print('visible subprocess output')"], label="sample command")
    finally:
        process.set_verbose(False)

    captured = capsys.readouterr()
    assert rc == 0
    assert "visible subprocess output" in captured.out
