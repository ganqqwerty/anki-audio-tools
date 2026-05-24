"""Check-phase orchestration for the dev task runner."""

from __future__ import annotations

import concurrent.futures
import os
import sys
import traceback
from collections.abc import Callable

from scripts.dev_tasks.process import is_verbose

CheckStep = tuple[str, Callable[[], int]]


def cmd_check(
    *,
    cmd_config_schema: Callable[[], int],
    cmd_contracts_generate: Callable[[], int],
    cmd_contracts_check: Callable[[], int],
    cmd_build_ui: Callable[[], int],
    cmd_lint: Callable[[], int],
    cmd_i18n: Callable[[], int],
    cmd_architecture_report: Callable[[], int],
    cmd_file_lines: Callable[[], int],
    run_typecheck: Callable[[], int],
    cmd_security: Callable[[], int],
    cmd_deadcode: Callable[[], int],
    cmd_deps: Callable[[], int],
    cmd_quality_metrics: Callable[[], int],
    cmd_qodana: Callable[[], int],
    cmd_arch: Callable[[], int],
    cmd_test_anki_api: Callable[[], int],
    run_test_targets: Callable[[], int],
    cmd_coverage: Callable[[], int],
    cmd_typecheck: Callable[[], int],
    cmd_test: Callable[[], int],
    cmd_test_svelte: Callable[[], int],
) -> int:
    preflight_steps = [
        ("config-schema", cmd_config_schema),
        ("contracts-generate", cmd_contracts_generate),
        ("contracts-check", cmd_contracts_check),
        ("build-ui", cmd_build_ui),
        ("lint", cmd_lint),
        ("i18n", cmd_i18n),
    ]
    if is_verbose():
        phases = _check_post_preflight_groups(
            contracts_prepared=False,
            cmd_architecture_report=cmd_architecture_report,
            cmd_file_lines=cmd_file_lines,
            run_typecheck=run_typecheck,
            cmd_security=cmd_security,
            cmd_deadcode=cmd_deadcode,
            cmd_deps=cmd_deps,
            cmd_quality_metrics=cmd_quality_metrics,
            cmd_qodana=cmd_qodana,
            cmd_arch=cmd_arch,
            cmd_test_anki_api=cmd_test_anki_api,
            run_test_targets=run_test_targets,
            cmd_coverage=cmd_coverage,
            cmd_typecheck=cmd_typecheck,
            cmd_test=cmd_test,
            cmd_test_svelte=cmd_test_svelte,
        )
        steps = [*preflight_steps, *(step for _phase_name, phase_steps in phases for step in phase_steps)]
        failed = _run_check_steps_sequential(steps)
    else:
        failed = _run_check_steps_sequential(preflight_steps)
        failed_preflight = set(failed)
        contracts_prepared = "contracts-generate" not in failed_preflight and "contracts-check" not in failed_preflight
        phases = _check_post_preflight_groups(
            contracts_prepared=contracts_prepared,
            cmd_architecture_report=cmd_architecture_report,
            cmd_file_lines=cmd_file_lines,
            run_typecheck=run_typecheck,
            cmd_security=cmd_security,
            cmd_deadcode=cmd_deadcode,
            cmd_deps=cmd_deps,
            cmd_quality_metrics=cmd_quality_metrics,
            cmd_qodana=cmd_qodana,
            cmd_arch=cmd_arch,
            cmd_test_anki_api=cmd_test_anki_api,
            run_test_targets=run_test_targets,
            cmd_coverage=cmd_coverage,
            cmd_typecheck=cmd_typecheck,
            cmd_test=cmd_test,
            cmd_test_svelte=cmd_test_svelte,
        )
        steps = [*preflight_steps, *(step for _phase_name, phase_steps in phases for step in phase_steps)]
        for phase_name, phase_steps in phases:
            failed.extend(_run_check_steps_parallel(phase_steps) if phase_name == "parallel" else _run_check_steps_sequential(phase_steps))
    failed = [name for name, _func in steps if name in set(failed)]
    if is_verbose():
        print(f"\n{'=' * 60}")
    print(f"[dev] {len(failed)} check step(s) failed: {', '.join(failed)}" if failed else "[dev] all check steps passed")
    if is_verbose():
        print(f"{'=' * 60}")
    return 1 if failed else 0


def _check_post_preflight_groups(
    *,
    contracts_prepared: bool,
    cmd_architecture_report: Callable[[], int],
    cmd_file_lines: Callable[[], int],
    run_typecheck: Callable[[], int],
    cmd_security: Callable[[], int],
    cmd_deadcode: Callable[[], int],
    cmd_deps: Callable[[], int],
    cmd_quality_metrics: Callable[[], int],
    cmd_qodana: Callable[[], int],
    cmd_arch: Callable[[], int],
    cmd_test_anki_api: Callable[[], int],
    run_test_targets: Callable[[], int],
    cmd_coverage: Callable[[], int],
    cmd_typecheck: Callable[[], int],
    cmd_test: Callable[[], int],
    cmd_test_svelte: Callable[[], int],
) -> list[tuple[str, list[CheckStep]]]:
    parallel_steps: list[CheckStep] = [("architecture-report", cmd_architecture_report), ("file-lines", cmd_file_lines)]
    if contracts_prepared:
        parallel_steps.append(("typecheck", run_typecheck))
    parallel_steps.extend(
        [
            ("security", cmd_security),
            ("deadcode", cmd_deadcode),
            ("deps", cmd_deps),
            ("complexity", cmd_quality_metrics),
            ("qodana", cmd_qodana),
            ("arch", cmd_arch),
            ("test-anki-api", cmd_test_anki_api),
        ]
    )
    if contracts_prepared:
        parallel_steps.append(("test", run_test_targets))
    parallel_steps.append(("coverage", cmd_coverage))
    tail_steps = [("test-svelte", cmd_test_svelte)] if contracts_prepared else [("typecheck", cmd_typecheck), ("test", cmd_test), ("test-svelte", cmd_test_svelte)]
    return [("parallel", parallel_steps), ("tail", tail_steps)]


def _check_worker_count(step_count: int) -> int:
    default_workers = 4
    raw = os.environ.get("DEV_CHECK_JOBS")
    if raw is None:
        return max(1, min(default_workers, step_count))
    try:
        workers = int(raw)
    except ValueError:
        workers = default_workers
    return max(1, min(workers, step_count))


def _run_check_steps_sequential(steps: list[CheckStep]) -> list[str]:
    failed: list[str] = []
    total_steps = len(steps)
    for index, (name, func) in enumerate(steps, start=1):
        print(f"\n{'=' * 60}\n  Step {index}/{total_steps}: {name}\n{'=' * 60}\n" if is_verbose() else f"[dev] check {index}/{total_steps}: {name}")
        rc = _run_check_step(name, func)
        if rc != 0:
            failed.append(name)
            print(f"[dev] FAILED: {name}")
    return failed


def _run_check_steps_parallel(steps: list[CheckStep]) -> list[str]:
    if not steps:
        return []
    workers = _check_worker_count(len(steps))
    print(f"[dev] check parallel phase: {len(steps)} step(s), {workers} worker(s)")
    failed: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_name = {executor.submit(_run_check_step, name, func): name for name, func in steps}
        results: dict[str, int] = {}
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            rc = future.result()
            results[name] = rc
            if rc != 0:
                failed.append(name)
                print(f"[dev] FAILED: {name}")
    return [name for name, _func in steps if results.get(name, 0) != 0]


def _run_check_step(name: str, func: Callable[[], int]) -> int:
    try:
        return func()
    except Exception as exc:
        print(f"[dev] exception in check step {name}: {exc}", file=sys.stderr)
        if is_verbose():
            traceback.print_exc()
        return 1
