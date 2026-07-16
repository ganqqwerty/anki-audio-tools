from __future__ import annotations

from types import SimpleNamespace

from scripts.dev_tasks import e2e_parallel, process
from scripts.dev_tasks.e2e_parallel import (
    E2EFileGroup,
    E2EShard,
    _collect_nodeids,
    _failed_nodeids,
    _has_module_marker,
    _random_seed,
    _rerun_command,
    _run_shard,
    collect_targets,
    group_nodeids_by_file,
    plan_shards,
    requested_worker_count,
    unclassified_shared_desktop_files,
)
from scripts.dev_tasks.process import set_verbose
from scripts.dev_tasks.pytest_runner import _pytest_args

SHARED_DESKTOP_TEST_FILES = {
    "e2e/test_edit_current_filtered_deck_workflow.py",
    "e2e/test_editor_audible_playback_interactions_workflow.py",
    "e2e/test_editor_audible_playback_workflow.py",
    "e2e/test_editor_share_workflow.py",
    "e2e/test_reviewer_audio_editor_workflow_answer_actions.py",
    "e2e/test_reviewer_audio_editor_workflow_template_filters.py",
    "e2e/test_settings_dialog_diagnostics.py",
    "e2e/test_settings_dialog_shell.py",
    "e2e/test_settings_hidden_warning.py",
    "e2e/test_settings_save_flows.py",
}


def _group(path: str, count: int, *, shared_desktop: bool = False) -> E2EFileGroup:
    return E2EFileGroup(
        path,
        tuple(f"{path}::test_{index}" for index in range(count)),
        shared_desktop=shared_desktop,
    )


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
            *(
                _group(path, 2, shared_desktop=True)
                for path in sorted(SHARED_DESKTOP_TEST_FILES)
            ),
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


def test_shared_desktop_files_are_discovered_from_module_markers() -> None:
    assert {
        path
        for path in SHARED_DESKTOP_TEST_FILES
        if _has_module_marker(path, "shared_desktop")
    } == SHARED_DESKTOP_TEST_FILES


def test_grouping_projects_shared_desktop_marker_from_source() -> None:
    path = "e2e/test_settings_dialog_shell.py"

    assert group_nodeids_by_file([f"{path}::test_example"]) == (
        E2EFileGroup(path, (f"{path}::test_example",), shared_desktop=True),
    )


def test_shared_desktop_capabilities_cannot_enter_regular_shards_unclassified() -> None:
    paths = [
        path.relative_to(e2e_parallel.ROOT).as_posix()
        for path in (e2e_parallel.ROOT / "e2e").glob("test_*.py")
    ]

    assert unclassified_shared_desktop_files(paths) == ()


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
    assert calls[0]["absolute_timeout_s"] == e2e_parallel.COLLECTION_TIMEOUT_S


def test_parallel_shard_run_shows_output_on_failure(monkeypatch, tmp_path) -> None:
    commands: list[list[str]] = []
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

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        calls.append(kwargs)
        return 0

    monkeypatch.setattr("scripts.dev_tasks.e2e_parallel._run", fake_run)

    result = _run_shard(tmp_path / "python", shard)

    assert result.returncode == 0
    assert calls[0]["show_output_on_failure"] is True
    assert any(arg.startswith("--randomly-seed=") for arg in commands[0])


def test_seed_is_configurable_and_rerun_uses_exact_nodeids() -> None:
    shard = E2EShard(
        "e2e-1",
        (
            E2EFileGroup(
                "e2e/test_audio_processing_ffmpeg.py",
                (
                    "e2e/test_audio_processing_ffmpeg.py::test_first",
                    "e2e/test_audio_processing_ffmpeg.py::test_second",
                ),
            ),
        ),
    )

    assert _random_seed({"DEV_E2E_RANDOM_SEED": "8128"}) == 8128
    assert _rerun_command(shard, 8128) == (
        "DEV_E2E_RANDOM_SEED=8128 python3 scripts/dev.py test-e2e-parallel "
        "e2e/test_audio_processing_ffmpeg.py::test_first "
        "e2e/test_audio_processing_ffmpeg.py::test_second"
    )


def test_junit_failure_report_produces_exact_failed_nodeids(tmp_path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite>
  <testcase classname="e2e.test_audio.TestPlayback" name="test_ok" file="e2e/test_audio.py" />
  <testcase classname="e2e.test_audio.TestPlayback" name="test_failed[param]" file="e2e/test_audio.py"><failure /></testcase>
  <testcase classname="e2e.test_other" name="test_error" file="e2e/test_other.py"><error /></testcase>
</testsuite></testsuites>
""",
        encoding="utf-8",
    )

    assert _failed_nodeids(report) == (
        "e2e/test_audio.py::TestPlayback::test_failed[param]",
        "e2e/test_other.py::test_error",
    )


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
