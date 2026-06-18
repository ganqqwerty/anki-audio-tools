from __future__ import annotations

from types import SimpleNamespace

from scripts.dev_tasks import e2e_parallel, process
from scripts.dev_tasks.e2e_parallel import (
    E2EFileGroup,
    E2EShard,
    _collect_nodeids,
    _run_shard,
    collect_targets,
    group_nodeids_by_file,
    plan_shards,
    requested_worker_count,
)
from scripts.dev_tasks.process import set_verbose
from scripts.dev_tasks.pytest_runner import _pytest_args

SHARED_DESKTOP_TEST_FILES = {
    "e2e/test_editor_share_workflow.py",
    "e2e/test_settings_dialog_diagnostics.py",
    "e2e/test_settings_dialog_shell.py",
    "e2e/test_settings_hidden_warning.py",
    "e2e/test_settings_save_flows.py",
}


def _group(path: str, count: int) -> E2EFileGroup:
    return E2EFileGroup(path, tuple(f"{path}::test_{index}" for index in range(count)))


def test_plan_shards_balances_files_by_collected_item_count() -> None:
    shards = plan_shards(
        (
            _group("e2e/test_a.py", 10),
            _group("e2e/test_b.py", 8),
            _group("e2e/test_c.py", 3),
            _group("e2e/test_d.py", 1),
        ),
        worker_count=2,
    )

    assert tuple(shard.item_count for shard in shards) == (11, 11)
    assert {file for shard in shards for file in shard.files} == {
        "e2e/test_a.py",
        "e2e/test_b.py",
        "e2e/test_c.py",
        "e2e/test_d.py",
    }


def test_plan_shards_keeps_clipboard_files_in_shared_desktop_shard() -> None:
    shards = plan_shards(
        (
            *(_group(path, 2) for path in sorted(SHARED_DESKTOP_TEST_FILES)),
            _group("e2e/test_audio_processing_ffmpeg.py", 16),
            _group("e2e/test_editor_playback_workflow.py", 6),
        ),
        worker_count=3,
    )

    shared = next(shard for shard in shards if shard.name == "shared-desktop")
    assert set(shared.files) == SHARED_DESKTOP_TEST_FILES
    assert all(
        all(path not in shard.files for path in SHARED_DESKTOP_TEST_FILES)
        for shard in shards
        if shard.name != "shared-desktop"
    )


def test_shared_desktop_files_exist() -> None:
    assert set(e2e_parallel.SHARED_DESKTOP_FILES) == SHARED_DESKTOP_TEST_FILES
    assert [
        path
        for path in sorted(e2e_parallel.SHARED_DESKTOP_FILES)
        if not (e2e_parallel.ROOT / path).is_file()
    ] == []


def test_requested_worker_count_defaults_clamps_and_handles_invalid_env() -> None:
    assert requested_worker_count({}, shard_count=5) == 3
    assert requested_worker_count({}, shard_count=2) == 2
    assert requested_worker_count({"DEV_E2E_JOBS": "1"}, shard_count=5) == 1
    assert requested_worker_count({"DEV_E2E_JOBS": "99"}, shard_count=5) == 5
    assert requested_worker_count({"DEV_E2E_JOBS": "abc"}, shard_count=5) == 3
    assert requested_worker_count({"DEV_E2E_JOBS": "0"}, shard_count=5) == 3
    assert requested_worker_count({"DEV_E2E_JOBS": "-2"}, shard_count=5) == 3
    assert requested_worker_count({}, shard_count=0) == 0


def test_explicit_targets_restrict_collection_targets_and_shard_set() -> None:
    explicit_targets = ["e2e/test_audio_processing_ffmpeg.py"]
    nodeids = [
        "e2e/test_audio_processing_ffmpeg.py::test_trim_left_renders_shorter_recording",
        "e2e/test_audio_processing_ffmpeg.py::test_speed_up_renders_shorter_mp3",
        "2 tests collected in 0.01s",
    ]

    assert collect_targets([]) == ["e2e/"]
    assert collect_targets(explicit_targets) == explicit_targets
    assert group_nodeids_by_file(nodeids) == (
        E2EFileGroup(
            "e2e/test_audio_processing_ffmpeg.py",
            (
                "e2e/test_audio_processing_ffmpeg.py::test_speed_up_renders_shorter_mp3",
                "e2e/test_audio_processing_ffmpeg.py::test_trim_left_renders_shorter_recording",
            ),
        ),
    )


def test_collect_args_can_force_nodeid_output_when_dev_runner_is_verbose() -> None:
    set_verbose(True)
    try:
        args = _pytest_args(
            ["e2e/test_audio_processing_ffmpeg.py"],
            collect_only=True,
            force_quiet=True,
        )
    finally:
        set_verbose(False)

    assert "-q" in args
    assert "-vv" not in args
    assert "--collect-only" in args


def test_parallel_collection_shows_output_on_failure(monkeypatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_capture(_cmd, **kwargs):
        calls.append(kwargs)
        return 0, "e2e/test_audio_processing_ffmpeg.py::test_example\n"

    monkeypatch.setattr("scripts.dev_tasks.e2e_parallel._run_capture", fake_run_capture)

    nodeids = _collect_nodeids(
        tmp_path / "python",
        ["e2e/test_audio_processing_ffmpeg.py"],
        tmp_path / "cache",
    )

    assert nodeids == ("e2e/test_audio_processing_ffmpeg.py::test_example",)
    assert calls[0]["show_output_on_failure"] is True


def test_parallel_shard_run_shows_output_on_failure(monkeypatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []
    shard = E2EShard(
        "e2e-1",
        (
            E2EFileGroup(
                "e2e/test_audio_processing_ffmpeg.py",
                ("e2e/test_audio_processing_ffmpeg.py::test_example",),
            ),
        ),
    )

    def fake_run(_cmd, **kwargs):
        calls.append(kwargs)
        return 0

    monkeypatch.setattr("scripts.dev_tasks.e2e_parallel._run", fake_run)

    result = _run_shard(tmp_path / "python", shard)

    assert result.returncode == 0
    assert calls[0]["show_output_on_failure"] is True


def test_parallel_runner_stays_silent_on_success_in_quiet_mode(monkeypatch, tmp_path, capsys) -> None:
    shard = E2EShard(
        "e2e-1",
        (
            E2EFileGroup(
                "e2e/test_audio_processing_ffmpeg.py",
                ("e2e/test_audio_processing_ffmpeg.py::test_example",),
            ),
        ),
    )
    monkeypatch.setattr(e2e_parallel, "_find_anki_python", lambda: tmp_path / "python")
    monkeypatch.setattr(
        e2e_parallel,
        "_collect_nodeids",
        lambda *_args, **_kwargs: ("e2e/test_audio_processing_ffmpeg.py::test_example",),
    )
    monkeypatch.setattr(e2e_parallel, "plan_shards", lambda *_args, **_kwargs: (shard,))
    monkeypatch.setattr(
        e2e_parallel,
        "_run_shard",
        lambda *_args, **_kwargs: SimpleNamespace(
            name="e2e-1",
            returncode=0,
            rerun_command="python3 scripts/dev.py test-e2e-parallel e2e/test_audio_processing_ffmpeg.py",
        ),
    )

    with process.quiet_test_output():
        assert e2e_parallel.cmd_test_e2e_parallel([]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""


def test_parallel_shard_run_suppresses_completion_line_in_quiet_mode(
    monkeypatch, tmp_path, capsys
) -> None:
    shard = E2EShard(
        "e2e-1",
        (
            E2EFileGroup(
                "e2e/test_audio_processing_ffmpeg.py",
                ("e2e/test_audio_processing_ffmpeg.py::test_example",),
            ),
        ),
    )
    monkeypatch.setattr("scripts.dev_tasks.e2e_parallel._run", lambda *_args, **_kwargs: 0)

    with process.quiet_test_output():
        result = _run_shard(tmp_path / "python", shard)

    captured = capsys.readouterr()
    assert result.returncode == 0
    assert "completed in" not in captured.out


def test_parallel_runner_keeps_rerun_hints_when_quiet_run_fails(monkeypatch, tmp_path, capsys) -> None:
    shard = E2EShard(
        "e2e-1",
        (
            E2EFileGroup(
                "e2e/test_audio_processing_ffmpeg.py",
                ("e2e/test_audio_processing_ffmpeg.py::test_example",),
            ),
        ),
    )
    monkeypatch.setattr(e2e_parallel, "_find_anki_python", lambda: tmp_path / "python")
    monkeypatch.setattr(
        e2e_parallel,
        "_collect_nodeids",
        lambda *_args, **_kwargs: ("e2e/test_audio_processing_ffmpeg.py::test_example",),
    )
    monkeypatch.setattr(e2e_parallel, "plan_shards", lambda *_args, **_kwargs: (shard,))
    monkeypatch.setattr(
        e2e_parallel,
        "_run_shard",
        lambda *_args, **_kwargs: SimpleNamespace(
            name="e2e-1",
            returncode=1,
            rerun_command="python3 scripts/dev.py test-e2e-parallel e2e/test_audio_processing_ffmpeg.py",
        ),
    )

    with process.quiet_test_output():
        assert e2e_parallel.cmd_test_e2e_parallel([]) == 1

    captured = capsys.readouterr()
    assert "rerun e2e-1" in captured.out
    assert "all e2e shards passed" not in captured.out
