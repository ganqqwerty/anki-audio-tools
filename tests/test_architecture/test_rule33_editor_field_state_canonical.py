"""Rule 33: editor field state is canonical, not rebuilt from DOM."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
EDITOR_INLINE = ROOT / "settings_ui" / "src" / "editor-inline"
FIELD_STATE_STORE = EDITOR_INLINE / "field-state-store.ts"

ALLOWED_FIELD_STATE_STORE_DATASET_LINES = {
    "target.dataset.progressMs = String(rounded);",
}

CANONICAL_FIELD_STATE_DATASET_FIELDS = {
    "anchorMs",
    "analyzerName",
    "cursorMs",
    "durationMs",
    "graphActive",
    "graphBusy",
    "hasTrack",
    "playbackEndMs",
    "playbackEngine",
    "playbackRegionMode",
    "playbackStartMs",
    "playbackState",
    "progressMs",
    "progressClockMode",
    "repeatEnabled",
    "resumeRequiresRestart",
    "selectionActive",
    "selectionDraftActive",
    "selectionDraftEndMs",
    "selectionDraftStartMs",
    "selectionEndMs",
    "selectionStartMs",
    "sourceFilename",
}

FIELD_STATE_PROJECTION_FILES = {
    "field-state-dom-sync.ts",
    "field-state-store.ts",
    "test-contract.ts",
}


def test_field_state_store_does_not_read_field_state_from_dom() -> None:
    violations: list[str] = []
    for line_no, line in enumerate(FIELD_STATE_STORE.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if ".dataset." in stripped and stripped not in ALLOWED_FIELD_STATE_STORE_DATASET_LINES:
            violations.append(f"field-state-store.ts:{line_no}: {stripped}")

    assert violations == [], "\n".join(violations)


def test_production_editor_code_does_not_invalidate_field_state_cache() -> None:
    violations: list[str] = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        if path.name == "field-state-store.ts":
            continue
        source = path.read_text(encoding="utf-8")
        if "invalidateFieldState" in source:
            violations.append(str(path.relative_to(ROOT)))

    assert violations == [], "\n".join(violations)


def test_production_editor_code_does_not_read_canonical_field_state_from_dataset() -> None:
    violations: list[str] = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        if path.name in FIELD_STATE_PROJECTION_FILES:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for field in CANONICAL_FIELD_STATE_DATASET_FIELDS:
                if f".dataset.{field}" in stripped:
                    violations.append(f"{path.relative_to(ROOT)}:{line_no}: {stripped}")

    assert violations == [], "\n".join(violations)
