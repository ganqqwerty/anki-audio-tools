"""Output and idle-time helpers for dev-task subprocess execution."""

from __future__ import annotations

import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


def format_duration(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def display_env_value(key: str, value: str) -> str:
    sensitive_markers = ("TOKEN", "PASSWORD", "SECRET", "KEY")
    if any(marker in key.upper() for marker in sensitive_markers):
        return "<redacted>"
    return value


def print_run_header(
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
        rendered_env = ", ".join(
            f"{key}={display_env_value(key, value)}"
            for key, value in sorted(env.items())
        )
        print(f"[dev] env: {rendered_env}")
    print("[dev] output: live")
    if idle_warning_s:
        print(f"[dev] idle warning: {format_duration(idle_warning_s)} without output")
    if idle_timeout_s:
        print(f"[dev] idle timeout: {format_duration(idle_timeout_s)} without output")


def handle_idle_warning(
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
            f"[dev] still waiting: no output for {format_duration(idle_for)} "
            f"(elapsed {format_duration(now - start)})"
        )
        return now + idle_warning_s
    return next_warning


def terminate_process_tree(
    process: subprocess.Popen[str],
    *,
    reason: str,
    terminate_grace_s: float,
) -> None:
    print(f"[dev] {reason}; terminating command process tree...", file=sys.stderr)
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (PermissionError, ProcessLookupError):
            return
    elif os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T"],
            check=False,
            capture_output=True,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=terminate_grace_s)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
            )
        else:
            process.kill()
    if os.name == "posix":
        deadline = time.monotonic() + terminate_grace_s
        while time.monotonic() < deadline:
            try:
                os.killpg(process.pid, 0)
            except (PermissionError, ProcessLookupError):
                break
            time.sleep(0.01)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def process_group_exists(process: subprocess.Popen[str]) -> bool:
    if os.name != "posix":
        return True
    try:
        os.killpg(process.pid, 0)
    except (PermissionError, ProcessLookupError):
        return False
    return True


def format_exit_status(
    *,
    rc: int,
    interrupted_for_idle: bool,
    verbose: bool,
    failure_output_available: bool = False,
) -> str:
    if interrupted_for_idle:
        status = "FAILED: terminated after timeout"
    elif rc == 0:
        status = "finished with exit code 0"
    else:
        status = f"FAILED with exit code {rc}"
    if rc != 0 and not verbose and not failure_output_available:
        status = f"{status}; rerun with --verbose for output"
    return status


def handle_idle_queue_wait(
    *,
    output_queue: queue.Queue[str | None],
    process: subprocess.Popen[str],
    start: float,
    last_output: float,
    next_warning: float,
    stream_closed: bool,
    idle_warning_s: float,
    idle_timeout_s: float,
    absolute_timeout_s: float,
    terminate_grace_s: float,
    stream_output: bool,
    buffered_output: list[str] | None,
) -> tuple[bool, bool, bool, float, float]:
    elapsed = time.monotonic() - start
    if process.poll() is not None:
        while True:
            try:
                pending = output_queue.get_nowait()
            except queue.Empty:
                break
            if pending is None:
                stream_closed = True
                continue
            if stream_output:
                sys.stdout.write(pending)
            elif buffered_output is not None:
                buffered_output.append(pending)
        if stream_output:
            sys.stdout.flush()
        if not stream_closed and process_group_exists(process):
            terminate_process_tree(
                process,
                reason="command exited while descendants still held its output pipe",
                terminate_grace_s=terminate_grace_s,
            )
        return True, False, stream_closed, last_output, next_warning
    if absolute_timeout_s and elapsed >= absolute_timeout_s and process.poll() is None:
        terminate_process_tree(
            process,
            reason=f"absolute timeout reached after {format_duration(elapsed)}",
            terminate_grace_s=terminate_grace_s,
        )
        return False, True, stream_closed, last_output, next_warning
    try:
        line = output_queue.get(timeout=1)
    except queue.Empty:
        now = time.monotonic()
        idle_for = now - last_output
        next_warning = handle_idle_warning(
            now=now,
            start=start,
            last_output=last_output,
            next_warning=next_warning,
            idle_warning_s=idle_warning_s,
        )
        if idle_timeout_s and idle_for >= idle_timeout_s and process.poll() is None:
            terminate_process_tree(
                process,
                reason=f"idle timeout reached after {format_duration(idle_for)}",
                terminate_grace_s=terminate_grace_s,
            )
            return False, True, stream_closed, last_output, next_warning
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


def print_failed_output(output: str, *, label: str | None = None) -> bool:
    if label is not None:
        print(f"[dev] {label}")
    if not output:
        return False
    print("[dev] output from failed command:")
    sys.stdout.write(output)
    if not output.endswith("\n"):
        print()
    return True


def start_output_reader(
    process: subprocess.Popen[str],
    output_queue: queue.Queue[str | None],
) -> threading.Thread:
    assert process.stdout is not None

    def _pump_output() -> None:
        try:
            for line in iter(process.stdout.readline, ""):
                output_queue.put(line)
        finally:
            process.stdout.close()
            output_queue.put(None)

    reader = threading.Thread(target=_pump_output, daemon=True)
    reader.start()
    return reader
