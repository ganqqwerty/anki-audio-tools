"""Rule 48: deleted playback mirror, handshake, queue, and clock surfaces stay deleted."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / "addon/anki_audio_quick_editor"
EDITOR_INLINE = ROOT / "settings_ui/src/editor-inline"

DELETED_FILES = {
    ADDON / "editor_playback.py",
    ADDON / "editor_playback_bounds.py",
    ADDON / "editor_playback_request.py",
    EDITOR_INLINE / "audio-clock.ts",
    EDITOR_INLINE / "playback-controller.ts",
    EDITOR_INLINE / "playback-request-dispatch.ts",
    EDITOR_INLINE / "selection-auto-advance-controller.ts",
}

TOMBSTONES = {
    "aqe:play-ended",
    "aqe:stop-playback",
    "__aqeGetPlaybackRequest",
    "__aqeLastPlaybackRequest",
    "__aqePendingPlaybackRequest",
    "__aqeSetPlaybackState",
    "__aqeStopEditorPlayback",
    "AUDIO_CLOCK_READINESS_CHANGED_EVENT",
    "PLAYBACK_RECOVERY_REQUESTED_EVENT",
    "sourceBoundaryHandler",
    "post_edit_waiting",
}


def test_legacy_playback_files_stay_deleted() -> None:
    assert {path.relative_to(ROOT).as_posix() for path in DELETED_FILES if path.exists()} == set()


def test_legacy_playback_symbols_stay_absent_from_production() -> None:
    violations = []
    paths = sorted(ADDON.rglob("*.py")) + sorted(EDITOR_INLINE.rglob("*.ts"))
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for tombstone in TOMBSTONES:
            if tombstone in source:
                violations.append(f"{path.relative_to(ROOT)}: {tombstone}")
    assert violations == []


def test_python_playback_state_mirror_stays_absent() -> None:
    violations = []
    for path in sorted(ADDON.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "PlaybackState" in source:
            violations.append(path.relative_to(ROOT).as_posix())
    assert violations == []
