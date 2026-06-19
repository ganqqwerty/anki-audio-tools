"""Rule 37: editor playback does not use Anki native playback APIs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"

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
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for pattern in BANNED_PATTERNS:
                if pattern in stripped:
                    violations.append(f"{relative}:{line_no}: {pattern}: {stripped}")

    assert violations == [], (
        "Editor playback must not call Anki native playback APIs.\n"
        + "\n".join(violations)
    )
