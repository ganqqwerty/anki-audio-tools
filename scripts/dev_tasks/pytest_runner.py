"""Pytest command helpers for the development task runner."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from .process import _read_seconds_env, _run
from .python_env import _find_anki_python

ROOT = Path(__file__).resolve().parents[2]


def _pytest_args(target: str, *, collect_only: bool = False) -> list[str]:
    target_args = [target]
    if target == "e2e/":
        target_args = ["--pyargs", "e2e"]
    args = [
        "pytest",
        *target_args,
        "-vv",
        "--durations=20",
        "-o",
        "console_output_style=progress-even-when-capture-no",
    ]
    if collect_only:
        args.append("--collect-only")
    else:
        args.extend(["-s", "--setup-show", "-o", "log_cli=true", "-o", "log_cli_level=INFO"])
    return args


def _probe_import_sequence(target: str, *, label: str, anki_python: Path) -> None:
    del label
    target_path = ROOT / target.rstrip("/")
    if not target_path.exists():
        return
    timeout_s = _read_seconds_env("DEV_IMPORT_PROBE_TIMEOUT_SECS", 15.0)
    conftests = sorted(target_path.rglob("conftest.py"))
    test_files = sorted(target_path.rglob("test_*.py"))
    if not conftests and not test_files:
        return

    helper_code = textwrap.dedent(
        """
        import importlib.util
        import os
        import sys
        from pathlib import Path

        root = Path(sys.argv[1])
        conftest_arg = sys.argv[2]
        target = Path(sys.argv[3])
        sys.path.insert(0, str(root))

        if conftest_arg:
            for index, raw_path in enumerate(conftest_arg.split(os.pathsep)):
                path = Path(raw_path)
                spec = importlib.util.spec_from_file_location(f"_probe_conftest_{index}", path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                assert spec.loader is not None
                spec.loader.exec_module(module)

        spec = importlib.util.spec_from_file_location(f"_probe_target_{target.stem}", target)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        print(f"[probe] imported {target}")
        """
    )
    conftest_str = os.pathsep.join(str(path) for path in conftests)
    for path in [*conftests, *test_files]:
        try:
            result = subprocess.run(
                [str(anki_python), "-c", helper_code, str(ROOT), conftest_str if path.name != "conftest.py" else "", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            print(f"[dev] probe TIMEOUT: {path.relative_to(ROOT)}", file=sys.stderr)
            return
        if result.returncode != 0:
            print(result.stderr.rstrip(), file=sys.stderr)
            return


def _run_pytest(target: str, *, label: str) -> int:
    anki_python = _find_anki_python()
    collect_warning_s = _read_seconds_env("DEV_PYTEST_COLLECT_WARNING_SECS", 10.0)
    collect_timeout_s = _read_seconds_env("DEV_PYTEST_COLLECT_TIMEOUT_SECS", 60.0)
    rc = _run(
        [str(anki_python), "-m", *_pytest_args(target, collect_only=True)],
        label=f"{label} (collect)",
        idle_warning_s=collect_warning_s,
        idle_timeout_s=collect_timeout_s,
    )
    if rc != 0:
        _probe_import_sequence(target, label=label, anki_python=anki_python)
        return rc
    return _run([str(anki_python), "-m", *_pytest_args(target)], label=f"{label} (run)")
