"""Rule 40: HTML media/readiness capabilities have one structural owner check."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_RULES = ROOT / "settings_ui/tests/state-management-architecture.test.ts"


def test_html_audio_capability_rule_is_in_the_frontend_gate() -> None:
    source = FRONTEND_RULES.read_text(encoding="utf-8")
    assert "Rule 40 / SM-A02" in source
    assert "mediaCapabilities" in source
    assert "benign" not in source  # the fixtures prove behavior instead of using a waiver
    assert (ROOT / "settings_ui/src/editor-inline/html-audio-session-audio-element.ts").is_file()
