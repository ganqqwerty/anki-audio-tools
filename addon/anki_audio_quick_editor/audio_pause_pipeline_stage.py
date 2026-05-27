"""External stage execution for pause-removal pipelines."""

from __future__ import annotations

import shlex
import subprocess  # nosec B404
import time
from collections.abc import Callable

from .audio_external import _render_external_error_message, _run_external_command
from .errors import AudioProcessingError
from .support import build_command_record


def run_pipeline_stage(
    name: str,
    command: tuple[str, ...],
    launch_error_message: str,
    failure_message: str,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if on_command:
        on_command(command)
    started = time.monotonic()
    stage: dict[str, object] = {
        "name": name,
        "argv": list(command),
        "command": shlex.join(command),
    }
    try:
        result = _run_external_command(
            command,
            launch_error_message,
            timeout_seconds=timeout_seconds,
            env=env,
        )
    except AudioProcessingError as exc:
        stage["duration_seconds"] = round(time.monotonic() - started, 6)
        stage["launch_error"] = str(exc)
        stages.append(stage)
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise

    stage.update(
        {
            "duration_seconds": round(time.monotonic() - started, 6),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    )
    stages.append(stage)
    attempted_commands.append(
        build_command_record(
            command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    )
    if result.returncode != 0:
        raise AudioProcessingError(_render_external_error_message(result, failure_message))
    return result
