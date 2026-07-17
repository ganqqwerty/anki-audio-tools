"""Rule 44: every transport event has an exhaustive identity policy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "settings_ui/src/editor-inline/transport/event-policy.ts"
TYPES = ROOT / "settings_ui/src/editor-inline/html-audio-session-types.ts"


def test_transport_identity_policy_is_compiler_exhaustive() -> None:
    policy = POLICY.read_text(encoding="utf-8")
    assert 'satisfies Record<HtmlAudioSessionEvent["type"], TransportIdentityScope>' in policy
    assert 'TransportIdentityScope = "runtime" | "source" | "attempt"' in policy
    assert "program" not in policy


def test_post_edit_delivery_is_not_a_transport_event() -> None:
    source = TYPES.read_text(encoding="utf-8")
    for tombstone in (
        "post_edit_waiting",
        "PostEditAutoplayRequested",
        "GraphRenderedForSource",
        "PostEditReadyConfirmed",
    ):
        assert tombstone not in source
