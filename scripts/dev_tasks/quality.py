"""Quality-check helper functions for the development task runner."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RADON_EXCLUDED_FILES = {
    "addon/anki_audio_quick_editor/contracts_generated.py",
}


def _radon_complexity_violations(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["radon output did not contain the expected file map"]
    failing_ranks = set("CDEF")
    violations: list[str] = []
    for raw_path, entries in sorted(report.items()):
        if not isinstance(entries, list):
            continue
        display_path = _radon_display_path(raw_path)
        if display_path in RADON_EXCLUDED_FILES:
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            rank = str(entry.get("rank", "")).upper()
            if rank not in failing_ranks:
                continue
            name = entry.get("name", "<unknown>")
            line = entry.get("lineno", "?")
            complexity = entry.get("complexity", "?")
            violations.append(f"{display_path}:{line} {name} rank={rank} complexity={complexity}")
    return violations


def _radon_maintainability_violations(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["radon maintainability output did not contain the expected file map"]
    violations: list[str] = []
    for raw_path, entry in sorted(report.items()):
        display_path = _radon_display_path(raw_path)
        if display_path in RADON_EXCLUDED_FILES:
            continue
        rank = entry.get("rank", "?") if isinstance(entry, dict) else "?"
        mi_score = entry.get("mi", "?") if isinstance(entry, dict) else "?"
        violations.append(f"{display_path} rank={rank} mi={mi_score}")
    return violations


def _radon_display_path(raw_path: object) -> str:
    path = Path(str(raw_path))
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _mutmut_fix_stats_prefix_mismatch() -> bool:
    stats_path = ROOT / "mutants" / "mutmut-stats.json"
    if not stats_path.is_file():
        return False

    meta_paths = sorted((ROOT / "mutants").glob("addon/anki_audio_quick_editor/*.py.meta"))
    if not meta_paths:
        return False

    try:
        stats = json.loads(stats_path.read_text())
        first_meta = json.loads(meta_paths[0].read_text())
    except json.JSONDecodeError:
        return False

    stats_keys = list(stats.get("tests_by_mangled_function_name", {}).keys())
    meta_keys = list(first_meta.get("exit_code_by_key", {}).keys())
    if not stats_keys or not meta_keys:
        return False

    source_prefix = "anki_audio_quick_editor."
    target_prefix = "addon.anki_audio_quick_editor."
    if not any(key.startswith(source_prefix) for key in stats_keys):
        return False
    if not any(key.startswith(target_prefix) for key in meta_keys):
        return False

    stats["tests_by_mangled_function_name"] = {
        (
            f"{target_prefix}{key[len(source_prefix):]}"
            if key.startswith(source_prefix)
            else key
        ): value
        for key, value in stats["tests_by_mangled_function_name"].items()
    }
    stats_path.write_text(json.dumps(stats, indent=4))
    return True
