"""Import-safe runtime diagnostic helpers."""

from __future__ import annotations

import subprocess  # nosec B404
from typing import Any


def build_deep_filter_health(config: dict[str, Any]) -> dict[str, Any]:
    """Return DeepFilterNet executable availability and version details."""
    from .audio_processor import (
        _external_command_run_kwargs,
        find_deep_filter,
        tool_source_label,
    )

    configured_path = str(config.get("deep_filter_path", ""))
    try:
        deep_filter_path = find_deep_filter(configured_path)
    except Exception as exc:
        return {
            "available": False,
            "path": configured_path,
            "source": "config" if configured_path else "",
            "version": "",
            "error": str(exc),
        }
    source = tool_source_label(deep_filter_path, configured_path=configured_path)

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
            "error": str(exc),
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

    expected_path = expected_bundled_tool_path("rnnoise-cli")
    try:
        rnnoise_path = find_rnnoise_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_path) if expected_path is not None else "",
            "source": "bundled" if expected_path is not None else "",
            "version": "",
            "error": str(exc),
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
            "source": "bundled",
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(rnnoise_path),
            "source": "bundled",
            "version": "",
            "error": "rnnoise-cli --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(rnnoise_path),
        "source": "bundled",
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

    expected_path = expected_bundled_tool_path("dpdfnet")
    try:
        dpdfnet_path = find_dpdfnet_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_path) if expected_path is not None else "",
            "source": "bundled" if expected_path is not None else "",
            "version": "",
            "error": str(exc),
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
            "source": "bundled",
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(dpdfnet_path),
            "source": "bundled",
            "version": "",
            "error": "dpdfnet --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(dpdfnet_path),
        "source": "bundled",
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

    expected_path = expected_bundled_tool_path("sherpa-spleeter")
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
        "source": "bundled",
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else probe_output or "sherpa-spleeter --help failed.",
    }


def _missing_bundled_spleeter_health(expected_path: Any, exc: Exception) -> dict[str, Any]:
    return {
        "available": False,
        "path": str(expected_path) if expected_path is not None else "",
        "source": "bundled" if expected_path is not None else "",
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
            "source": "bundled",
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
