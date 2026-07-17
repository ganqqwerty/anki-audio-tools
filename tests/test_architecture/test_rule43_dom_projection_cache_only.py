"""Rule 43: deleted DOM behavioral state cannot return."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR_INLINE = ROOT / "settings_ui/src/editor-inline"

DELETED_DOM_STATE = {
    "__aqeAudioClockAvailable",
    "__aqeAudioClockFallback",
    "__aqeAudioClockLastSeekedMs",
    "__aqeClockHandlersInstalled",
    "__aqeChorusingState",
    "__aqeHtmlAudioFailureReason",
    "__aqeHtmlAudioMediaErrorCode",
    "__aqeHtmlAudioMediaResponseStatus",
    "__aqeRecordCountdownTimer",
    "__aqeRecordingCursorFrame",
    "__aqeRecordingStartedAt",
    "__aqeRepeatPauseOverlayTimer",
}


def test_deleted_dom_behavior_fields_stay_absent() -> None:
    violations = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        source = path.read_text(encoding="utf-8")
        for field in DELETED_DOM_STATE:
            if field in source:
                violations.append(f"{path.relative_to(ROOT)}: {field}")
    assert violations == []
