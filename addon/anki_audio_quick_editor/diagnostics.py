"""Import-safe runtime diagnostic helpers."""

from __future__ import annotations

import subprocess
from typing import Any


def build_deep_filter_health(config: dict[str, Any]) -> dict[str, Any]:
    """Return DeepFilterNet executable availability and version details."""
    from .audio_processor import find_deep_filter

    configured_path = str(config.get("deep_filter_path", ""))
    try:
        deep_filter_path = find_deep_filter(configured_path)
    except Exception as exc:
        return {
            "available": False,
            "path": configured_path,
            "version": "",
            "error": str(exc),
        }

    command = (str(deep_filter_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "version": "",
            "error": "deep-filter --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(deep_filter_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "deep-filter --version failed.",
    }


def build_sidon_health() -> dict[str, Any]:
    """Return bundled Sidon availability and version details."""
    from .audio_processor import (
        expected_bundled_sidon_dir,
        expected_bundled_sidon_model_dir,
        find_sidon_bundle,
    )

    expected_dir = expected_bundled_sidon_dir()
    expected_model_dir = expected_bundled_sidon_model_dir()
    try:
        sidon_path, model_dir = find_sidon_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_dir / "bin" / "sidon-cli") if expected_dir is not None else "",
            "model_dir": str(expected_model_dir) if expected_model_dir is not None else "",
            "version": "",
            "error": str(exc),
        }

    command = (str(sidon_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(sidon_path),
            "model_dir": str(model_dir),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(sidon_path),
            "model_dir": str(model_dir),
            "version": "",
            "error": "sidon-cli --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(sidon_path),
        "model_dir": str(model_dir),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "sidon-cli --version failed.",
    }


def build_mp_senet_health() -> dict[str, Any]:
    """Return bundled MP-SENet availability and version details."""
    from .audio_processor import (
        expected_bundled_mp_senet_dir,
        expected_bundled_mp_senet_model_path,
        find_mp_senet_bundle,
    )

    expected_dir = expected_bundled_mp_senet_dir()
    expected_model_path = expected_bundled_mp_senet_model_path()
    try:
        mp_senet_path, model_path = find_mp_senet_bundle()
    except Exception as exc:
        return {
            "available": False,
            "path": str(expected_dir / "bin" / "mp-senet-cli") if expected_dir is not None else "",
            "model_path": str(expected_model_path) if expected_model_path is not None else "",
            "version": "",
            "error": str(exc),
        }

    command = (str(mp_senet_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(mp_senet_path),
            "model_path": str(model_path),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(mp_senet_path),
            "model_path": str(model_path),
            "version": "",
            "error": "mp-senet-cli --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(mp_senet_path),
        "model_path": str(model_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "mp-senet-cli --version failed.",
    }
