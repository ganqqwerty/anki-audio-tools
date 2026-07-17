"""Rule 38: frontend playback behavior stays inside known owner modules."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR_INLINE = ROOT / "settings_ui" / "src" / "editor-inline"

PURE_FRONTEND_TRANSITION_OWNER_ALLOWLIST = {
    "settings_ui/src/editor-inline/playback-model.ts",
}

STATE_TRANSITION_ALLOWED: set[str] = set()

SOURCE_AUDIO_OPERATION_ALLOWED = {
    "settings_ui/src/editor-inline/html-audio-session-audio-element.ts",
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
        if relative in SOURCE_AUDIO_OPERATION_ALLOWED | TEST_SUPPORT_ALLOWLIST:
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
        "inside the shared HTML session controller or quarantined legacy owners.\n"
        + "\n".join(violations)
    )


def test_frontend_playback_transitions_are_quarantined() -> None:
    violations: list[str] = []

    for path in _editor_inline_sources():
        relative = path.relative_to(ROOT).as_posix()
        if relative in PURE_FRONTEND_TRANSITION_OWNER_ALLOWLIST | STATE_TRANSITION_ALLOWED | TEST_SUPPORT_ALLOWLIST:
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
        "owners and pure playback machines.\n"
        + "\n".join(violations)
    )


def test_frontend_playback_allowances_exist_and_are_used() -> None:
    allowance_patterns = {
        **{
            relative: AUDIO_OPERATION_PATTERNS
            + (TIMER_OPERATION_PATTERNS if _is_playback_file(ROOT / relative) else ())
            for relative in SOURCE_AUDIO_OPERATION_ALLOWED
            | TEST_SUPPORT_ALLOWLIST
        },
        **{
            relative: TRANSITION_PATTERNS
            for relative in PURE_FRONTEND_TRANSITION_OWNER_ALLOWLIST
            | STATE_TRANSITION_ALLOWED
        },
    }
    violations: list[str] = []

    for relative, patterns in sorted(allowance_patterns.items()):
        path = ROOT / relative
        if not path.is_file():
            violations.append(f"{relative}: allowance names a missing file")
            continue
        source = path.read_text(encoding="utf-8")
        if not any(pattern in source for pattern in patterns):
            violations.append(f"{relative}: allowance is unused")

    assert violations == [], "Rule 38 allowances must be exact and bidirectional.\n" + "\n".join(violations)


def _editor_inline_sources() -> list[Path]:
    return [
        path
        for path in sorted(EDITOR_INLINE.rglob("*"))
        if path.suffix in {".svelte", ".ts"}
    ]


def _is_playback_file(path: Path) -> bool:
    relative = path.relative_to(EDITOR_INLINE).as_posix()
    return any(term in relative for term in PLAYBACK_FILE_TERMS)
