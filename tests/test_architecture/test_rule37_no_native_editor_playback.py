"""Rule 37: native editor playback stays quarantined during HTML-only migration."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"

LEGACY_NATIVE_PLAYBACK_ALLOWLIST = {
    "addon/anki_audio_quick_editor/editor_playback.py",
    "addon/anki_audio_quick_editor/editor_playback_request.py",
    "addon/anki_audio_quick_editor/editor_recording.py",
}

BANNED_PATTERNS = (
    "from aqt.sound import av_player",
    "aqt.sound.av_player",
    "av_player.play_tags",
    "av_player.toggle_pause",
    "av_player.stop_and_clear_queue",
    "from anki.sound import SoundOrVideoTag",
    "SoundOrVideoTag(",
)


def test_native_editor_playback_apis_are_quarantined() -> None:
    violations: list[str] = []

    for path in sorted(ADDON_DIR.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in LEGACY_NATIVE_PLAYBACK_ALLOWLIST:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for pattern in BANNED_PATTERNS:
                if pattern in stripped:
                    violations.append(f"{relative}:{line_no}: {pattern}: {stripped}")

    assert violations == [], (
        "Native editor playback APIs may only remain in the temporary legacy "
        "playback allowlist while source and learner playback move to HTML audio.\n"
        + "\n".join(violations)
    )
