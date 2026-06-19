"""Rule 38: frontend playback behavior stays inside known owner modules."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR_INLINE = ROOT / "settings_ui" / "src" / "editor-inline"

LEGACY_FRONTEND_PLAYBACK_OWNER_ALLOWLIST = {
    "settings_ui/src/editor-inline/actions-playback.ts",
    "settings_ui/src/editor-inline/actions-selection.ts",
    "settings_ui/src/editor-inline/audio-clock.ts",
    "settings_ui/src/editor-inline/chorusing-controller.ts",
    "settings_ui/src/editor-inline/graph-countdown-overlay.ts",
    "settings_ui/src/editor-inline/playback-actions.ts",
    "settings_ui/src/editor-inline/playback-controller.ts",
    "settings_ui/src/editor-inline/playback-controller-frame.ts",
    "settings_ui/src/editor-inline/playback-controller-state.ts",
    "settings_ui/src/editor-inline/playback-engine-decision.ts",
    "settings_ui/src/editor-inline/playback-html-fallback.ts",
    "settings_ui/src/editor-inline/playback-model.ts",
    "settings_ui/src/editor-inline/post-edit-playback.ts",
}

STATE_TRANSITION_ALLOWED = {
    "settings_ui/src/editor-inline/source-playback-machine.ts",
    "settings_ui/src/editor-inline/learner-recording-playback-machine.ts",
}

SOURCE_AUDIO_OPERATION_ALLOWED = {
    "settings_ui/src/editor-inline/source-playback-controller.ts",
    "settings_ui/src/editor-inline/learner-recording-playback.ts",
}

TEST_SUPPORT_ALLOWLIST = {
    "settings_ui/src/editor-inline/test-contract.ts",
}

AUDIO_OPERATION_PATTERNS = (
    ".play()",
    ".pause()",
    ".load()",
    "currentTime =",
)

TIMER_OPERATION_PATTERNS = (
    "setTimeout(",
    "clearTimeout(",
)

TRANSITION_PATTERNS = (
    "playbackState ===",
    "playback.state ===",
    "learnerPlaybackStatus ===",
    'engine === "native"',
    'engine: "native"',
    "fallback_to_native",
)

PLAYBACK_FILE_TERMS = (
    "playback",
    "audio-clock",
    "chorusing-controller",
    "actions-selection",
    "actions-playback",
)


def test_frontend_playback_audio_operations_are_quarantined() -> None:
    violations: list[str] = []

    for path in _editor_inline_sources():
        relative = path.relative_to(ROOT).as_posix()
        if relative in LEGACY_FRONTEND_PLAYBACK_OWNER_ALLOWLIST | SOURCE_AUDIO_OPERATION_ALLOWED | TEST_SUPPORT_ALLOWLIST:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for pattern in AUDIO_OPERATION_PATTERNS:
                if pattern in stripped:
                    violations.append(f"{relative}:{line_no}: {pattern}: {stripped}")
            if _is_playback_file(path):
                for pattern in TIMER_OPERATION_PATTERNS:
                    if pattern in stripped:
                        violations.append(f"{relative}:{line_no}: {pattern}: {stripped}")

    assert violations == [], (
        "Frontend playback audio element operations and playback timers must stay "
        "inside the quarantined legacy owners until the source/learner playback "
        "controllers replace them.\n"
        + "\n".join(violations)
    )


def test_frontend_playback_transitions_are_quarantined() -> None:
    violations: list[str] = []

    for path in _editor_inline_sources():
        relative = path.relative_to(ROOT).as_posix()
        if relative in LEGACY_FRONTEND_PLAYBACK_OWNER_ALLOWLIST | STATE_TRANSITION_ALLOWED | TEST_SUPPORT_ALLOWLIST:
            continue
        if not _is_playback_file(path):
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for pattern in TRANSITION_PATTERNS:
                if pattern in stripped:
                    violations.append(f"{relative}:{line_no}: {pattern}: {stripped}")

    assert violations == [], (
        "Frontend playback state transitions must stay inside the quarantined legacy "
        "owners until the pure playback machines replace them.\n"
        + "\n".join(violations)
    )


def _editor_inline_sources() -> list[Path]:
    return [
        path
        for path in sorted(EDITOR_INLINE.rglob("*"))
        if path.suffix in {".svelte", ".ts"}
    ]


def _is_playback_file(path: Path) -> bool:
    relative = path.relative_to(EDITOR_INLINE).as_posix()
    return any(term in relative for term in PLAYBACK_FILE_TERMS)
