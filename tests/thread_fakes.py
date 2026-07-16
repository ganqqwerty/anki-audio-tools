"""Shared deterministic thread doubles for unit/component tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


class ImmediateThread:
    """Thread-compatible double that executes its target exactly once on start()."""

    def __init__(
        self,
        target: Callable[..., Any],
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
        daemon: bool = False,
        name: str | None = None,
    ) -> None:
        self._target = target
        self._args = tuple(args)
        self._kwargs = dict(kwargs or {})
        self.daemon = daemon
        self.name = name
        self._started = False

    def start(self) -> None:
        if self._started:
            raise RuntimeError("threads can only be started once")
        self._started = True
        self._target(*self._args, **self._kwargs)

    def join(self, timeout: float | None = None) -> None:
        del timeout

    def is_alive(self) -> bool:
        return False
