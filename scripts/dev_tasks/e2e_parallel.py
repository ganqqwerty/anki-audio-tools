"""Parallel e2e shard runner for local Anki runtime tests."""

from __future__ import annotations

import concurrent.futures
import os
import shutil
import tempfile
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from scripts.dev_tasks.process import _format_duration, _run, _run_capture
from scripts.dev_tasks.pytest_runner import _pytest_args
from scripts.dev_tasks.python_env import _find_anki_python

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_E2E_JOBS = 3
SHARED_DESKTOP_FILES = frozenset(
    {
        "e2e/test_settings_dialog.py",
        "e2e/test_editor_share_workflow.py",
    }
)


@dataclass(frozen=True)
class E2EFileGroup:
    path: str
    nodeids: tuple[str, ...]

    @property
    def item_count(self) -> int:
        return len(self.nodeids)


@dataclass(frozen=True)
class E2EShard:
    name: str
    file_groups: tuple[E2EFileGroup, ...]

    @property
    def files(self) -> tuple[str, ...]:
        return tuple(group.path for group in self.file_groups)

    @property
    def nodeids(self) -> tuple[str, ...]:
        return tuple(nodeid for group in self.file_groups for nodeid in group.nodeids)

    @property
    def item_count(self) -> int:
        return sum(group.item_count for group in self.file_groups)


@dataclass
class _MutableShard:
    name: str
    file_groups: list[E2EFileGroup]

    @property
    def item_count(self) -> int:
        return sum(group.item_count for group in self.file_groups)

    def freeze(self) -> E2EShard:
        return E2EShard(self.name, tuple(sorted(self.file_groups, key=lambda group: group.path)))


def collect_targets(command_args: Sequence[str]) -> list[str]:
    return list(command_args) if command_args else ["e2e/"]


def requested_worker_count(env: Mapping[str, str], shard_count: int) -> int:
    if shard_count <= 0:
        return 0
    raw = env.get("DEV_E2E_JOBS")
    try:
        requested = DEFAULT_E2E_JOBS if raw is None else int(raw)
    except ValueError:
        requested = DEFAULT_E2E_JOBS
    if requested < 1:
        requested = DEFAULT_E2E_JOBS
    return max(1, min(requested, shard_count))


def group_nodeids_by_file(nodeids: Sequence[str]) -> tuple[E2EFileGroup, ...]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for nodeid in nodeids:
        if "::" not in nodeid:
            continue
        grouped[_nodeid_file(nodeid)].append(nodeid)
    return tuple(
        E2EFileGroup(path, tuple(sorted(grouped[path])))
        for path in sorted(grouped)
    )


def plan_shards(file_groups: Sequence[E2EFileGroup], worker_count: int) -> tuple[E2EShard, ...]:
    groups = tuple(sorted(file_groups, key=lambda group: group.path))
    if worker_count <= 0 or not groups:
        return ()
    if worker_count == 1:
        return (E2EShard("e2e-1", groups),)

    shared_groups = tuple(group for group in groups if group.path in SHARED_DESKTOP_FILES)
    regular_groups = tuple(group for group in groups if group.path not in SHARED_DESKTOP_FILES)
    shard_count = min(worker_count, len(regular_groups) + (1 if shared_groups else 0))

    shards: list[E2EShard] = []
    regular_shard_count = shard_count - (1 if shared_groups else 0)
    if regular_shard_count > 0:
        regular_shards = [
            _MutableShard(f"e2e-{index}", [])
            for index in range(1, regular_shard_count + 1)
        ]
        for group in sorted(regular_groups, key=lambda item: (-item.item_count, item.path)):
            target = min(
                regular_shards,
                key=lambda shard: (shard.item_count, len(shard.file_groups), shard.name),
            )
            target.file_groups.append(group)
        shards.extend(shard.freeze() for shard in regular_shards if shard.file_groups)

    if shared_groups:
        shards.append(E2EShard("shared-desktop", shared_groups))
    return tuple(shards)


def cmd_test_e2e_parallel(command_args: Sequence[str]) -> int:
    anki_python = _find_anki_python()
    collect_cache_dir = Path(tempfile.mkdtemp(prefix="aqe-e2e-collect-cache-"))
    try:
        targets = collect_targets(command_args)
        nodeids = _collect_nodeids(anki_python, targets, collect_cache_dir)
    finally:
        shutil.rmtree(collect_cache_dir, ignore_errors=True)
    if nodeids is None:
        return 1

    file_groups = group_nodeids_by_file(nodeids)
    potential_shards = len(
        [group for group in file_groups if group.path not in SHARED_DESKTOP_FILES]
    ) + (1 if any(group.path in SHARED_DESKTOP_FILES for group in file_groups) else 0)
    worker_count = requested_worker_count(os.environ, potential_shards)
    shards = plan_shards(file_groups, worker_count)
    if not shards:
        print("[dev] no e2e tests collected")
        return 1

    total_items = sum(shard.item_count for shard in shards)
    print(
        f"[dev] e2e parallel: {total_items} item(s), "
        f"{len(shards)} shard(s), {worker_count} worker(s)"
    )
    for shard in shards:
        print(
            f"[dev] shard {shard.name}: {shard.item_count} item(s), "
            f"{', '.join(shard.files)}"
        )

    results: list[_ShardResult] = []
    if worker_count == 1:
        results = [_run_shard(anki_python, shard) for shard in shards]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(lambda shard: _run_shard(anki_python, shard), shards))

    failed = [result for result in results if result.returncode != 0]
    if failed:
        print(f"[dev] {len(failed)} e2e shard(s) failed")
        for result in failed:
            print(f"[dev] rerun {result.name}: {result.rerun_command}")
        return 1
    print("[dev] all e2e shards passed")
    return 0


def _collect_nodeids(anki_python: Path, targets: Sequence[str], cache_dir: Path) -> tuple[str, ...] | None:
    rc, output = _run_capture(
        [
            str(anki_python),
            "-m",
            *_pytest_args(targets, collect_only=True, cache_dir=cache_dir, force_quiet=True),
        ],
        label="python e2e tests (parallel collect)",
    )
    if rc != 0:
        return None
    return tuple(
        line.strip()
        for line in output.splitlines()
        if line.startswith("e2e/") and "::" in line
    )


@dataclass(frozen=True)
class _ShardResult:
    name: str
    returncode: int
    rerun_command: str


def _run_shard(anki_python: Path, shard: E2EShard) -> _ShardResult:
    cache_dir = Path(tempfile.mkdtemp(prefix=f"aqe-{shard.name}-pytest-cache-"))
    start = time.monotonic()
    try:
        label = f"python e2e tests: {shard.name}"
        rc = _run(
            [str(anki_python), "-m", *_pytest_args(shard.nodeids, cache_dir=cache_dir)],
            label=label,
        )
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
    elapsed = _format_duration(time.monotonic() - start)
    print(f"[dev] shard {shard.name} completed in {elapsed}")
    return _ShardResult(shard.name, rc, _rerun_command(shard))


def _nodeid_file(nodeid: str) -> str:
    raw_path = nodeid.split("::", 1)[0]
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _rerun_command(shard: E2EShard) -> str:
    return "python3 scripts/dev.py test-e2e-parallel " + " ".join(shard.files)
