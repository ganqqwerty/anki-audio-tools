from __future__ import annotations

import pytest

from tests.thread_fakes import ImmediateThread


def test_immediate_thread_preserves_arguments_and_runs_once() -> None:
    calls: list[tuple[int, str]] = []
    thread = ImmediateThread(
        lambda number, *, label: calls.append((number, label)),
        args=(3,),
        kwargs={"label": "done"},
        daemon=True,
        name="worker",
    )

    thread.start()

    assert calls == [(3, "done")]
    assert thread.daemon is True
    assert thread.name == "worker"
    assert thread.is_alive() is False
    thread.join(0.1)
    with pytest.raises(RuntimeError, match="only be started once"):
        thread.start()
