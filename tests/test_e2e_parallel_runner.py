from __future__ import annotations

from scripts.dev_tasks.e2e_parallel import (
    E2EFileGroup,
    collect_targets,
    group_nodeids_by_file,
    plan_shards,
    requested_worker_count,
)
from scripts.dev_tasks.process import set_verbose
from scripts.dev_tasks.pytest_runner import _pytest_args


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
            _group("e2e/test_settings_dialog.py", 11),
            _group("e2e/test_editor_share_workflow.py", 3),
            _group("e2e/test_audio_processing_ffmpeg.py", 16),
            _group("e2e/test_editor_playback_workflow.py", 6),
        ),
        worker_count=3,
    )

    shared = next(shard for shard in shards if shard.name == "shared-desktop")
    assert set(shared.files) == {
        "e2e/test_settings_dialog.py",
        "e2e/test_editor_share_workflow.py",
    }
    assert all(
        "e2e/test_settings_dialog.py" not in shard.files
        and "e2e/test_editor_share_workflow.py" not in shard.files
        for shard in shards
        if shard.name != "shared-desktop"
    )


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
