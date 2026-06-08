from __future__ import annotations

from pathlib import Path

DEEP_FILTER = str(Path("/addon/bin/deep-filter"))
DPDFNET = str(Path("/addon/bin/macos-arm64/dpdfnet"))
RNNOISE = str(Path("/addon/bin/macos-arm64/rnnoise-cli"))
SILERO_VAD = str(Path("/addon/bin/macos-arm64/silero-vad"))
SPLEETER = str(Path("/addon/bin/macos-arm64/sherpa-spleeter"))


class _ImmediateThread:
    def __init__(self, target, args=(), kwargs=None, daemon=True):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self) -> None:
        self._target(*self._args, **self._kwargs)

    def join(self, _timeout=None) -> None:
        return None

    def is_alive(self) -> bool:
        return False
