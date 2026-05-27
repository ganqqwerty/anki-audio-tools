"""Process execution helpers for the development task runner."""

from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_VERBOSE = False


def set_verbose(verbose: bool) -> None:
    global _VERBOSE
    _VERBOSE = verbose


def is_verbose() -> bool:
    return _VERBOSE


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
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _display_env_value(key: str, value: str) -> str:
    sensitive_markers = ("TOKEN", "PASSWORD", "SECRET", "KEY")
    if any(marker in key.upper() for marker in sensitive_markers):
        return "<redacted>"
    return value


def _print_run_header(
    rendered_cmd: str,
    run_cwd: Path,
    env: dict[str, str] | None,
    label: str | None,
    idle_warning_s: float,
    idle_timeout_s: float,
) -> None:
    print(f"\n[dev] {label or 'running command'}")
    print(f"[dev] cwd: {run_cwd}")
    print(f"[dev] cmd: {rendered_cmd}")
    if env:
        print("[dev] env: " + ", ".join(f"{key}={_display_env_value(key, value)}" for key, value in sorted(env.items())))
    print("[dev] output: live")
    if idle_warning_s:
        print(f"[dev] idle warning: {_format_duration(idle_warning_s)} without output")
    if idle_timeout_s:
        print(f"[dev] idle timeout: {_format_duration(idle_timeout_s)} without output")


def _handle_idle_warning(
    *,
    now: float,
    start: float,
    last_output: float,
    next_warning: float,
    idle_warning_s: float,
) -> float:
    if idle_warning_s and now >= next_warning:
        idle_for = now - last_output
        print(
            f"[dev] still waiting: no output for {_format_duration(idle_for)} "
            f"(elapsed {_format_duration(now - start)})"
        )
        return now + idle_warning_s
    return next_warning


def _terminate_process_after_idle(process: subprocess.Popen[str], *, idle_for: float, terminate_grace_s: float) -> None:
    print(
        f"[dev] idle timeout reached after {_format_duration(idle_for)}; terminating command...",
        file=sys.stderr,
    )
    process.terminate()
    try:
        process.wait(timeout=terminate_grace_s)
    except subprocess.TimeoutExpired:
        process.kill()


def _format_exit_status(
    *,
    rc: int,
    interrupted_for_idle: bool,
    verbose: bool,
    failure_output_available: bool = False,
) -> str:
    if interrupted_for_idle:
        status = "FAILED: terminated after idle timeout"
    elif rc == 0:
        status = "finished with exit code 0"
    else:
        status = f"FAILED with exit code {rc}"
    if rc != 0 and not verbose and not failure_output_available:
        status = f"{status}; rerun with --verbose for output"
    return status


def _handle_idle_queue_wait(
    *,
    output_queue: queue.Queue[str | None],
    process: subprocess.Popen[str],
    start: float,
    last_output: float,
    next_warning: float,
    stream_closed: bool,
    idle_warning_s: float,
    idle_timeout_s: float,
    terminate_grace_s: float,
    stream_output: bool,
    buffered_output: list[str] | None,
) -> tuple[bool, bool, bool, float, float]:
    try:
        line = output_queue.get(timeout=1)
    except queue.Empty:
        now = time.monotonic()
        idle_for = now - last_output
        next_warning = _handle_idle_warning(
            now=now,
            start=start,
            last_output=last_output,
            next_warning=next_warning,
            idle_warning_s=idle_warning_s,
        )
        if idle_timeout_s and idle_for >= idle_timeout_s and process.poll() is None:
            _terminate_process_after_idle(process, idle_for=idle_for, terminate_grace_s=terminate_grace_s)
            return False, True, stream_closed, last_output, next_warning
        if stream_closed and process.poll() is not None:
            return True, False, stream_closed, last_output, next_warning
        return False, False, stream_closed, last_output, next_warning
    if line is None:
        if process.poll() is not None:
            return True, False, True, last_output, next_warning
        return False, False, True, last_output, next_warning
    if stream_output:
        sys.stdout.write(line)
        sys.stdout.flush()
    elif buffered_output is not None:
        buffered_output.append(line)
    last_output = time.monotonic()
    next_warning = last_output + idle_warning_s if idle_warning_s else float("inf")
    return False, False, stream_closed, last_output, next_warning


def _print_failed_output(output: str) -> bool:
    if not output:
        return False
    print("[dev] output from failed command:")
    sys.stdout.write(output)
    if not output.endswith("\n"):
        print()
    return True


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
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    if idle_warning_s is None:
        idle_warning_s = _read_seconds_env("DEV_IDLE_WARNING_SECS", 30.0)
    if idle_timeout_s is None:
        idle_timeout_s = _read_seconds_env("DEV_IDLE_TIMEOUT_SECS", 300.0)
    terminate_grace_s = _read_seconds_env("DEV_TERMINATE_GRACE_SECS", 5.0)
    rendered_cmd = shlex.join(str(part) for part in cmd)
    if is_verbose():
        _print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s, idle_timeout_s)
    else:
        print(f"[dev] {label or rendered_cmd}")

    process = subprocess.Popen(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    output_queue: queue.Queue[str | None] = queue.Queue()

    def _pump_output() -> None:
        try:
            for line in iter(process.stdout.readline, ""):
                output_queue.put(line)
        finally:
            process.stdout.close()
            output_queue.put(None)

    reader = threading.Thread(target=_pump_output, daemon=True)
    reader.start()

    start = time.monotonic()
    last_output = start
    next_warning = start + idle_warning_s if idle_warning_s else float("inf")
    stream_closed = False
    interrupted_for_idle = False
    buffered_output: list[str] | None = [] if show_output_on_failure and not is_verbose() else None

    while True:
        should_break, timed_out, stream_closed, last_output, next_warning = _handle_idle_queue_wait(
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
        if timed_out:
            interrupted_for_idle = True
            continue
        if should_break:
            break

    rc = process.wait()
    reader.join(timeout=1)
    elapsed = time.monotonic() - start
    failure_output_available = False
    if rc != 0 and buffered_output is not None:
        failure_output_available = _print_failed_output("".join(buffered_output))
    status = _format_exit_status(
        rc=rc,
        interrupted_for_idle=interrupted_for_idle,
        verbose=is_verbose(),
        failure_output_available=failure_output_available,
    )
    print(f"[dev] {status} in {_format_duration(elapsed)}")
    return rc


def _run_capture(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    show_output_on_failure: bool = False,
) -> tuple[int, str]:
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    rendered_cmd = shlex.join(str(part) for part in cmd)
    if is_verbose():
        _print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s=0.0, idle_timeout_s=0.0)
    else:
        print(f"[dev] {label or rendered_cmd}")

    start = time.monotonic()
    result = subprocess.run(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = result.stdout or ""
    if output and is_verbose():
        sys.stdout.write(output)
        sys.stdout.flush()
    elapsed = time.monotonic() - start
    failure_output_available = False
    if result.returncode != 0 and show_output_on_failure and not is_verbose():
        failure_output_available = _print_failed_output(output)
    status = _format_exit_status(
        rc=result.returncode,
        interrupted_for_idle=False,
        verbose=is_verbose(),
        failure_output_available=failure_output_available,
    )
    print(f"[dev] {status} in {_format_duration(elapsed)}")
    return result.returncode, output
