from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import MagicMock


class TestEditor:
    """Weakref-able editor test double for the runtime session store."""


@dataclass
class BarrierCall:
    """A controllable call site for tests that need a worker to pause mid-operation."""

    started: threading.Event = field(default_factory=threading.Event)
    release: threading.Event = field(default_factory=threading.Event)
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = field(default_factory=list)

    def wait_started(self, timeout: float = 2.0) -> None:
        assert self.started.wait(timeout), "worker did not reach the race barrier"

    def allow_completion(self) -> None:
        self.release.set()

    def block_until_released(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))
        self.started.set()
        assert self.release.wait(5.0), "test did not release the blocked worker"


class ImmediateThread:
    """Thread replacement that runs synchronously for unit tests."""

    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        self._target = target
        self.daemon = daemon

    def start(self) -> None:
        self._target()


class BackgroundThread:
    """Thread replacement that keeps a real thread but exposes it for joining."""

    started_threads: list[threading.Thread] = []

    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        self._thread = threading.Thread(target=target, daemon=daemon)
        self.started_threads.append(self._thread)

    def start(self) -> None:
        self._thread.start()


def reset_background_threads() -> None:
    BackgroundThread.started_threads.clear()


def join_background_threads(timeout: float = 2.0) -> None:
    for thread in list(BackgroundThread.started_threads):
        thread.join(timeout)
        assert not thread.is_alive(), "background race test worker did not finish"


def main_immediately(_owner: Any, callback: Callable[[], None]) -> None:
    callback()


def fake_media_manager(media_dir: Path) -> SimpleNamespace:
    def write_data(desired_name: str, data: bytes) -> str:
        (media_dir / desired_name).write_bytes(data)
        return desired_name

    return SimpleNamespace(
        dir=MagicMock(return_value=str(media_dir)),
        write_data=MagicMock(side_effect=write_data),
    )


def editor_with_media(media_dir: Path, field_html: str = "[sound:clip.mp3]") -> Any:
    editor = TestEditor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=[field_html])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=fake_media_manager(media_dir)),
    )
    return editor
