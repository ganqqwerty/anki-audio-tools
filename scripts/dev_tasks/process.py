"""Process execution helpers for the development task runner."""

from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from .process_support import (
    format_duration,
    format_exit_status,
    handle_idle_queue_wait,
    print_failed_output,
    print_run_header,
    start_output_reader,
)

ROOT = Path(__file__).resolve().parents[2]
_VERBOSE = False
_IDLE_TIMEOUT_S: float | None = None
_QUIET_TEST_OUTPUT: ContextVar[int] = ContextVar("_QUIET_TEST_OUTPUT", default=0)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def set_verbose(verbose: bool) -> None:
    global _VERBOSE
    _VERBOSE = verbose


def set_idle_timeout(timeout_s: float | None) -> None:
    global _IDLE_TIMEOUT_S
    _IDLE_TIMEOUT_S = timeout_s


def is_verbose() -> bool:
    return _VERBOSE


@contextmanager
def quiet_test_output() -> Iterator[None]:
    token = _QUIET_TEST_OUTPUT.set(_QUIET_TEST_OUTPUT.get() + 1)
    try:
        yield
    finally:
        _QUIET_TEST_OUTPUT.reset(token)


def is_quiet_test_output() -> bool:
    return _QUIET_TEST_OUTPUT.get() > 0


def _read_seconds_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else 0.0


def _format_duration(seconds: float) -> str:
    return format_duration(seconds)


def _print_run_header(
    rendered_cmd: str,
    run_cwd: Path,
    env: dict[str, str] | None,
    label: str | None,
    idle_warning_s: float,
    idle_timeout_s: float,
) -> None:
    print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s, idle_timeout_s)


def _resolve_run_settings(
    *,
    cwd: Path | None,
    env: dict[str, str] | None,
    idle_warning_s: float | None,
    idle_timeout_s: float | None,
) -> tuple[Path, dict[str, str] | None, float, float, float]:
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    resolved_idle_warning = idle_warning_s
    if resolved_idle_warning is None:
        resolved_idle_warning = _read_seconds_env("DEV_IDLE_WARNING_SECS", 30.0)
    resolved_idle_timeout = idle_timeout_s
    if resolved_idle_timeout is None:
        resolved_idle_timeout = (
            _IDLE_TIMEOUT_S
            if _IDLE_TIMEOUT_S is not None
            else _read_seconds_env("DEV_IDLE_TIMEOUT_SECS", 300.0)
        )
    terminate_grace_s = _read_seconds_env("DEV_TERMINATE_GRACE_SECS", 5.0)
    return run_cwd, merged_env, resolved_idle_warning, resolved_idle_timeout, terminate_grace_s


def _announce_run(
    *,
    rendered_cmd: str,
    run_cwd: Path,
    env: dict[str, str] | None,
    label: str | None,
    idle_warning_s: float,
    idle_timeout_s: float,
    quiet_mode: bool,
) -> None:
    if is_verbose():
        _print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s, idle_timeout_s)
    elif not quiet_mode:
        print(f"[dev] {label or rendered_cmd}")


def _wait_for_process_completion(
    *,
    output_queue: queue.Queue[str | None],
    process: subprocess.Popen[str],
    idle_warning_s: float,
    idle_timeout_s: float,
    terminate_grace_s: float,
    buffered_output: list[str] | None,
) -> bool:
    start = time.monotonic()
    last_output = start
    next_warning = start + idle_warning_s if idle_warning_s else float("inf")
    stream_closed = False
    interrupted_for_idle = False

    while True:
        should_break, timed_out, stream_closed, last_output, next_warning = handle_idle_queue_wait(
            output_queue=output_queue,
            process=process,
            start=start,
            last_output=last_output,
            next_warning=next_warning,
            stream_closed=stream_closed,
            idle_warning_s=idle_warning_s,
            idle_timeout_s=idle_timeout_s,
            terminate_grace_s=terminate_grace_s,
            stream_output=is_verbose(),
            buffered_output=buffered_output,
        )
        if should_break:
            return interrupted_for_idle
        if timed_out:
            interrupted_for_idle = True


def _run(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    idle_warning_s: float | None = None,
    idle_timeout_s: float | None = None,
    show_output_on_failure: bool = False,
) -> int:
    quiet_mode = is_quiet_test_output() and not is_verbose()
    run_cwd, merged_env, resolved_idle_warning, resolved_idle_timeout, terminate_grace_s = _resolve_run_settings(
        cwd=cwd,
        env=env,
        idle_warning_s=idle_warning_s,
        idle_timeout_s=idle_timeout_s,
    )
    rendered_cmd = shlex.join(str(part) for part in cmd)
    _announce_run(
        rendered_cmd=rendered_cmd,
        run_cwd=run_cwd,
        env=env,
        label=label,
        idle_warning_s=resolved_idle_warning,
        idle_timeout_s=resolved_idle_timeout,
        quiet_mode=quiet_mode,
    )

    process = subprocess.Popen(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    output_queue: queue.Queue[str | None] = queue.Queue()
    buffered_output: list[str] | None = [] if (quiet_mode or show_output_on_failure) and not is_verbose() else None
    reader = start_output_reader(process, output_queue)
    start = time.monotonic()
    interrupted_for_idle = _wait_for_process_completion(
        output_queue=output_queue,
        process=process,
        idle_warning_s=resolved_idle_warning,
        idle_timeout_s=resolved_idle_timeout,
        terminate_grace_s=terminate_grace_s,
        buffered_output=buffered_output,
    )

    rc = process.wait()
    reader.join(timeout=1)
    elapsed = time.monotonic() - start
    failure_output_available = False
    if rc != 0 and buffered_output is not None:
        failure_output_available = print_failed_output(
            "".join(buffered_output),
            label=label if quiet_mode else None,
        )
    status = format_exit_status(
        rc=rc,
        interrupted_for_idle=interrupted_for_idle,
        verbose=is_verbose(),
        failure_output_available=failure_output_available,
    )
    if not quiet_mode or rc != 0:
        print(f"[dev] {status} in {format_duration(elapsed)}")
    return rc


run_process = _run


def _run_capture(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    show_output_on_failure: bool = False,
) -> tuple[int, str]:
    quiet_mode = is_quiet_test_output() and not is_verbose()
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    rendered_cmd = shlex.join(str(part) for part in cmd)
    if is_verbose():
        _print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s=0.0, idle_timeout_s=0.0)
    elif not quiet_mode:
        print(f"[dev] {label or rendered_cmd}")

    start = time.monotonic()
    result = subprocess.run(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = result.stdout or ""
    if output and is_verbose():
        sys.stdout.write(output)
        sys.stdout.flush()
    elapsed = time.monotonic() - start
    failure_output_available = False
    if result.returncode != 0 and (quiet_mode or show_output_on_failure) and not is_verbose():
        failure_output_available = print_failed_output(
            output,
            label=label if quiet_mode else None,
        )
    status = format_exit_status(
        rc=result.returncode,
        interrupted_for_idle=False,
        verbose=is_verbose(),
        failure_output_available=failure_output_available,
    )
    if not quiet_mode or result.returncode != 0:
        print(f"[dev] {status} in {format_duration(elapsed)}")
    return result.returncode, output


run_capture = _run_capture
