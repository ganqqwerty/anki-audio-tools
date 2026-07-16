"""Parallel e2e shard runner for local Anki runtime tests."""

from __future__ import annotations

import ast
import concurrent.futures
import os
import secrets
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from scripts.dev_tasks.process import (
    _format_duration,
    _run,
    _run_capture,
    is_quiet_test_output,
    is_verbose,
)
from scripts.dev_tasks.pytest_runner import _pytest_args
from scripts.dev_tasks.python_env import _find_anki_python

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_E2E_JOBS = 3
COLLECTION_TIMEOUT_S = 60.0
SHARED_DESKTOP_CAPABILITIES = (
    "QApplication.clipboard",
    "AUDIBLE_",
    "audible_capture",
    "enable_audible_worklet",
    "anki_mw.reviewer",
    "moveToState(\"review\")",
    "moveToState('review')",
)


@dataclass(frozen=True)
class E2EFileGroup:
    path: str
    nodeids: tuple[str, ...]
    shared_desktop: bool = False

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
        E2EFileGroup(
            path,
            tuple(sorted(grouped[path])),
            shared_desktop=_has_module_marker(path, "shared_desktop"),
        )
        for path in sorted(grouped)
    )


def unclassified_shared_desktop_files(paths: Sequence[str]) -> tuple[str, ...]:
    unclassified: list[str] = []
    for path in paths:
        source_path = ROOT / path
        if not source_path.is_file():
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(capability in source for capability in SHARED_DESKTOP_CAPABILITIES) and not _has_module_marker(
            path, "shared_desktop"
        ):
            unclassified.append(path)
    return tuple(sorted(unclassified))


def plan_shards(file_groups: Sequence[E2EFileGroup], worker_count: int) -> tuple[E2EShard, ...]:
    groups = tuple(sorted(file_groups, key=lambda group: group.path))
    if worker_count <= 0 or not groups:
        return ()
    if worker_count == 1:
        return (E2EShard("e2e-1", groups),)

    shared_groups = tuple(group for group in groups if group.shared_desktop)
    regular_groups = tuple(group for group in groups if not group.shared_desktop)
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


def _emit_parallel_status(message: str, *, force: bool = False) -> None:
    if force or is_verbose() or not is_quiet_test_output():
        print(message)


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
        [group for group in file_groups if not group.shared_desktop]
    ) + (1 if any(group.shared_desktop for group in file_groups) else 0)
    worker_count = requested_worker_count(os.environ, potential_shards)
    shards = plan_shards(file_groups, worker_count)
    if not shards:
        _emit_parallel_status("[dev] no e2e tests collected", force=True)
        return 1

    total_items = sum(shard.item_count for shard in shards)
    _emit_parallel_status(
        f"[dev] e2e parallel: {total_items} item(s), "
        f"{len(shards)} shard(s), {worker_count} worker(s), platform={sys.platform}"
    )
    for shard in shards:
        _emit_parallel_status(
            f"[dev] shard {shard.name}: {shard.item_count} item(s), "
            f"{', '.join(shard.files)}"
        )

    seed = _random_seed(os.environ)
    _emit_parallel_status(f"[dev] pytest-randomly seed: {seed}")
    results: list[_ShardResult] = []
    if worker_count == 1:
        results = [_run_shard(anki_python, shard, seed) for shard in shards]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(lambda shard: _run_shard(anki_python, shard, seed), shards))

    failed = [result for result in results if result.returncode != 0]
    if failed:
        _emit_parallel_status(f"[dev] {len(failed)} e2e shard(s) failed", force=True)
        for result in failed:
            _emit_parallel_status(f"[dev] rerun {result.name}: {result.rerun_command}", force=True)
        return 1
    _emit_parallel_status("[dev] all e2e shards passed")
    return 0


def _collect_nodeids(anki_python: Path, targets: Sequence[str], cache_dir: Path) -> tuple[str, ...] | None:
    rc, output = _run_capture(
        [
            str(anki_python),
            "-m",
            *_pytest_args(targets, collect_only=True, cache_dir=cache_dir, force_quiet=True),
        ],
        label="python e2e tests (parallel collect)",
        show_output_on_failure=True,
        absolute_timeout_s=COLLECTION_TIMEOUT_S,
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
    failed_nodeids: tuple[str, ...] = ()


def _run_shard(anki_python: Path, shard: E2EShard, seed: int | None = None) -> _ShardResult:
    resolved_seed = _random_seed(os.environ) if seed is None else seed
    cache_dir = Path(tempfile.mkdtemp(prefix=f"aqe-{shard.name}-pytest-cache-"))
    report_dir = ROOT / "e2e-artifacts" / "shards"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{shard.name}-junit.xml"
    report_path.unlink(missing_ok=True)
    start = time.monotonic()
    try:
        label = f"python e2e tests: {shard.name}"
        rc = _run(
            [
                str(anki_python),
                "-m",
                *_pytest_args(shard.nodeids, cache_dir=cache_dir),
                f"--randomly-seed={resolved_seed}",
                f"--junitxml={report_path}",
            ],
            label=label,
            show_output_on_failure=True,
        )
        failed_nodeids = _failed_nodeids(report_path)
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
    elapsed = _format_duration(time.monotonic() - start)
    _emit_parallel_status(f"[dev] shard {shard.name} completed in {elapsed}")
    return _ShardResult(
        shard.name,
        rc,
        _rerun_command(shard, resolved_seed, failed_nodeids),
        failed_nodeids,
    )


def _has_module_marker(path: str, marker: str) -> bool:
    source_path = ROOT / path
    if not source_path.is_file():
        return False
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=path)
    expected = ("pytest", "mark", marker)
    return any(_attribute_parts(node) == expected for node in ast.walk(tree))


def _attribute_parts(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return tuple(reversed(parts))


def _random_seed(env: Mapping[str, str]) -> int:
    configured = env.get("DEV_E2E_RANDOM_SEED")
    if configured is not None:
        try:
            return int(configured)
        except ValueError:
            pass
    return secrets.randbelow(2**32)


def _nodeid_file(nodeid: str) -> str:
    raw_path = nodeid.split("::", 1)[0]
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _failed_nodeids(report_path: Path) -> tuple[str, ...]:
    if not report_path.is_file():
        return ()
    try:
        root = ElementTree.parse(report_path).getroot()
    except (ElementTree.ParseError, OSError):
        return ()
    failed: list[str] = []
    for case in root.iter("testcase"):
        if case.find("failure") is None and case.find("error") is None:
            continue
        path = case.get("file")
        name = case.get("name")
        classname = case.get("classname", "")
        if not path and classname.startswith("e2e."):
            path = classname.replace(".", "/") + ".py"
        if not path or not name:
            continue
        class_parts = classname.split(".")
        class_suffix = class_parts[-1] if class_parts and class_parts[-1][:1].isupper() else ""
        suffix = f"::{class_suffix}" if class_suffix else ""
        failed.append(f"{Path(path).as_posix()}{suffix}::{name}")
    return tuple(sorted(set(failed)))


def _rerun_command(
    shard: E2EShard,
    seed: int,
    failed_nodeids: Sequence[str] = (),
) -> str:
    targets = tuple(failed_nodeids) or shard.nodeids
    return (
        f"DEV_E2E_RANDOM_SEED={seed} python3 scripts/dev.py test-e2e-parallel "
        + " ".join(targets)
    )
