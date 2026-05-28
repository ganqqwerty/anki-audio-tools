"""Import-safe runtime diagnostic helpers."""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from .error_codes import AQE_RUNTIME_ASSET_MISSING, format_coded_message
from .permission_guidance import (
    external_tool_error_message,
    message_with_permission_guidance,
)


def build_deep_filter_health(_config: dict[str, Any]) -> dict[str, Any]:
    """Return DeepFilterNet executable availability and version details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        find_deep_filter,
        tool_source_label,
    )

    try:
        deep_filter_path = find_deep_filter()
    except Exception as exc:
        return {
            "available": False,
            "path": "",
            "source": "",
            "version": "",
            "error": _diagnostic_error_message(exc),
        }
    source = tool_source_label(deep_filter_path, configured_path="")

    command = (str(deep_filter_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "source": source,
            "version": "",
            "error": _diagnostic_error_message(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "source": source,
            "version": "",
            "error": "deep-filter --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(deep_filter_path),
        "source": source,
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "deep-filter --version failed.",
    }


def build_rnnoise_health() -> dict[str, Any]:
    """Return bundled RNNoise availability and version details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        expected_bundled_tool_path,
        find_rnnoise_bundle,
    )
    from .audio_tools import expected_managed_tool_path

    expected_path = expected_managed_tool_path("rnnoise-cli") or expected_bundled_tool_path("rnnoise-cli")
    try:
        rnnoise_path = find_rnnoise_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_path) if expected_path is not None else "",
            "source": _runtime_source_for_expected_path(expected_path),
            "version": "",
            "error": _diagnostic_error_message(exc),
        }

    command = (str(rnnoise_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(rnnoise_path),
            "source": _managed_or_bundled_source(rnnoise_path),
            "version": "",
            "error": _diagnostic_error_message(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(rnnoise_path),
            "source": _managed_or_bundled_source(rnnoise_path),
            "version": "",
            "error": "rnnoise-cli --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(rnnoise_path),
        "source": _managed_or_bundled_source(rnnoise_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "rnnoise-cli --version failed.",
    }


def build_dpdfnet_health() -> dict[str, Any]:
    """Return bundled DPDFNet availability and version details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        expected_bundled_tool_path,
        find_dpdfnet_bundle,
    )
    from .audio_tools import expected_managed_tool_path

    expected_path = expected_managed_tool_path("dpdfnet") or expected_bundled_tool_path("dpdfnet")
    try:
        dpdfnet_path = find_dpdfnet_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_path) if expected_path is not None else "",
            "source": _runtime_source_for_expected_path(expected_path),
            "version": "",
            "error": _diagnostic_error_message(exc),
        }

    command = (str(dpdfnet_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(dpdfnet_path),
            "source": _managed_or_bundled_source(dpdfnet_path),
            "version": "",
            "error": _diagnostic_error_message(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(dpdfnet_path),
            "source": _managed_or_bundled_source(dpdfnet_path),
            "version": "",
            "error": "dpdfnet --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(dpdfnet_path),
        "source": _managed_or_bundled_source(dpdfnet_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "dpdfnet --version failed.",
    }


def build_spleeter_health() -> dict[str, Any]:
    """Return bundled Sherpa Spleeter availability and version details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        expected_bundled_tool_path,
        find_spleeter_bundle,
    )
    from .audio_tools import expected_managed_tool_path

    expected_path = expected_managed_tool_path("sherpa-spleeter") or expected_bundled_tool_path("sherpa-spleeter")
    try:
        spleeter_path, _, _ = find_spleeter_bundle()
    except Exception as exc:
        return _missing_bundled_spleeter_health(expected_path, exc)

    result = _run_spleeter_help_probe(spleeter_path, _external_command_run_kwargs())
    if isinstance(result, dict):
        return result

    probe_output = (result.stdout or result.stderr).strip()
    version = _spleeter_probe_summary(probe_output)
    return {
        "available": result.returncode == 0,
        "path": str(spleeter_path),
        "source": _managed_or_bundled_source(spleeter_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else probe_output or "sherpa-spleeter --help failed.",
    }


def build_silero_vad_health() -> dict[str, Any]:
    """Return bundled Silero VAD availability and probe details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        expected_bundled_tool_path,
        find_silero_vad_bundle,
    )
    from .audio_tools import expected_managed_tool_path

    expected_path = expected_managed_tool_path("silero-vad") or expected_bundled_tool_path("silero-vad")
    try:
        silero_path, _ = find_silero_vad_bundle()
    except Exception as exc:
        return _missing_bundled_silero_health(expected_path, exc)

    result = _run_silero_help_probe(silero_path, _external_command_run_kwargs())
    if isinstance(result, dict):
        return result

    probe_output = (result.stdout or result.stderr).strip()
    version = _silero_probe_summary(probe_output)
    return {
        "available": result.returncode == 0,
        "path": str(silero_path),
        "source": _managed_or_bundled_source(silero_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else probe_output or "silero-vad --help failed.",
    }


def _missing_bundled_silero_health(expected_path: Any, exc: Exception) -> dict[str, Any]:
    return {
        "available": False,
        "path": str(expected_path) if expected_path is not None else "",
        "source": _runtime_source_for_expected_path(expected_path),
        "version": "",
        "error": str(exc),
    }


def _run_silero_help_probe(
    silero_path: Any,
    run_kwargs: dict[str, Any],
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    try:
        return subprocess.run(
            [str(silero_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **run_kwargs,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(silero_path),
            "source": _managed_or_bundled_source(silero_path),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(silero_path),
            "source": _managed_or_bundled_source(silero_path),
            "version": "",
            "error": "silero-vad --help timed out.",
        }


def _silero_probe_summary(probe_output: str) -> str:
    return next(
        (line.strip() for line in probe_output.splitlines() if "vad in sherpa-onnx" in line.lower()),
        "",
    ) or next((line.strip() for line in probe_output.splitlines() if line.strip()), "")


def _missing_bundled_spleeter_health(expected_path: Any, exc: Exception) -> dict[str, Any]:
    return {
        "available": False,
        "path": str(expected_path) if expected_path is not None else "",
        "source": _runtime_source_for_expected_path(expected_path),
        "version": "",
        "error": str(exc),
    }


def _run_spleeter_help_probe(
    spleeter_path: Any,
    run_kwargs: dict[str, Any],
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    try:
        return subprocess.run(
            [str(spleeter_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **run_kwargs,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(spleeter_path),
            "source": _managed_or_bundled_source(spleeter_path),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(spleeter_path),
            "source": "bundled",
            "version": "",
            "error": "sherpa-spleeter --help timed out.",
        }


def _spleeter_probe_summary(probe_output: str) -> str:
    return next(
        (line.strip() for line in probe_output.splitlines() if "source separation" in line.lower()),
        "",
    ) or next((line.strip() for line in probe_output.splitlines() if line.strip()), "")


def _runtime_source_for_expected_path(path: Any) -> str:
    if path is None:
        return ""
    return _managed_or_bundled_source(path)


def _managed_or_bundled_source(path: Any) -> str:
    from . import runtime_manager
    from .audio_tools import PACKAGE_DIR

    try:
        Path(path).relative_to(runtime_manager.runtime_base_dir(PACKAGE_DIR))
    except (TypeError, ValueError):
        return "bundled"
    return runtime_manager.RUNTIME_SOURCE_MANAGED


def _diagnostic_error_message(exc: BaseException) -> str:
    message = message_with_permission_guidance(str(exc), exc)
    message = external_tool_error_message(message, tool_name="runtime tool")
    return format_coded_message(AQE_RUNTIME_ASSET_MISSING, message)
