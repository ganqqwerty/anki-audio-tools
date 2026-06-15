"""Rule 34: editor control/runtime state is canonical, not read from DOM."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
EDITOR_INLINE = ROOT / "settings_ui" / "src" / "editor-inline"

DOM_STATE_PROJECTION_FILES = {
    "control-actions.ts",
    "control-status-renderer.ts",
    "recording-actions-state.ts",
    "visualizer-runtime-state.ts",
}

DOM_STATE_TEST_READ_FILES = {
    "test-contract.ts",
}

CANONICAL_DOM_STATE_DATASET_FIELDS = {
    "aqeCanRedo",
    "aqeCanUndo",
    "aqeBusy",
    "busy",
    "learnerDurationMs",
    "learnerRecordingFailureMessage",
    "learnerRecordingGeneration",
    "learnerRecordingMediaFilename",
    "learnerPlaybackStatus",
    "learnerRecordingStatus",
    "learnerStartCursorMs",
    "playStartedAt",
    "playStartMs",
    "playbackLoop",
    "playbackResetCursorMs",
    "preserveStatusOnPlaybackEnd",
    "repeatPauseSeconds",
    "repeatPauseWaiting",
    "stableKind",
    "stableMessage",
    "stableUserError",
    "targetDurationMs",
    "viewportEndMs",
    "viewportStartMs",
}


def test_production_editor_code_uses_typed_control_state_not_dom_dataset() -> None:
    violations: list[str] = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        if path.name in DOM_STATE_TEST_READ_FILES:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for field in CANONICAL_DOM_STATE_DATASET_FIELDS:
                if f".dataset.{field}" in stripped:
                    if path.name in DOM_STATE_PROJECTION_FILES and _is_dataset_projection_write(stripped, field):
                        continue
                    violations.append(f"{path.relative_to(ROOT)}:{line_no}: {stripped}")

    assert violations == [], "\n".join(violations)


def test_busy_projection_is_owned_by_control_actions() -> None:
    violations: list[str] = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        if path.name == "control-actions.ts":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if "document.body.dataset.aqeBusy" in stripped:
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: {stripped}")

    assert violations == [], "\n".join(violations)


def _is_dataset_projection_write(stripped_line: str, field: str) -> bool:
    token = f".dataset.{field}"
    suffix = stripped_line.split(token, 1)[1].lstrip()
    if suffix.startswith("="):
        return True
    return stripped_line.startswith("delete ") and suffix.startswith(";")
