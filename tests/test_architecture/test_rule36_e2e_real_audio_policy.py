"""Rule 36: browser media e2e tests must not use the fake audio driver."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E2E_ROOT = ROOT / "e2e"

FAKE_AUDIO_DRIVER_CALLS = {
    "_install_html_audio_test_driver",
    "_open_tone_editor",
}

REAL_AUDIO_TEST_NAME_TERMS = {
    "aac",
    "browser_audio",
    "codec",
    "m4a",
    "media_error",
    "ogg",
    "opus",
    "play_rejected",
    "real_media",
    "vorbis",
}

BROWSER_MEDIA_FACT_TERMS = {
    "MediaError": "inspects native browser media error objects",
    "audio.error": "inspects native browser media errors",
    "audio.load": "drives native browser loading",
    "audio.pause =": "replaces native browser pause()",
    "audio.play =": "replaces native browser play()",
    "audioClockReady": "asserts audio-clock readiness",
    "audioPlaybackTestDriver": "asserts fake-vs-real audio driver state",
    "audio_error": "asserts browser audio readiness failure",
    "audio_load_failed": "asserts browser audio load failure",
    "audio_pause_failed": "asserts browser audio pause failure",
    "audio_play_rejected": "asserts browser audio play rejection",
    "audio_seek_failed": "asserts browser audio seek failure",
    "errorCode": "asserts native browser media error code",
    "htmlAudioReadiness": "asserts browser audio readiness",
    "loadedmetadata": "drives native browser metadata events",
    "metadata_timeout": "asserts browser metadata timeout",
    "playCalls": "counts native browser play() calls",
    "readyState": "inspects native browser media readiness",
}


def test_e2e_real_browser_audio_coverage_does_not_use_fake_audio_driver() -> None:
    violations: list[str] = []

    for path in sorted(E2E_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for function in _function_nodes(tree):
            fake_calls = sorted(_fake_audio_driver_calls(function))
            if not fake_calls:
                continue

            source_segment = ast.get_source_segment(source, function) or ""
            name_matches = sorted(
                term
                for term in REAL_AUDIO_TEST_NAME_TERMS
                if term in function.name.lower()
            )
            fact_matches = {
                term: reason
                for term, reason in BROWSER_MEDIA_FACT_TERMS.items()
                if term in source_segment
            }
            if not name_matches and not fact_matches:
                continue

            details = _format_violation_details(name_matches, fact_matches)
            violations.append(
                f"{path.relative_to(ROOT)}:{function.lineno}: {function.name} "
                f"uses fake audio driver via {', '.join(fake_calls)} while {details}"
            )

    assert violations == [], (
        "E2E tests that cover browser media readiness, codec/container behavior, "
        "native MediaError facts, repeat decoder behavior, or play/pause rejection "
        "must use a real WebView audio element. The fake HTML audio driver is only "
        "valid for UI and graph state tests.\n"
        + "\n".join(violations)
    )


def _function_nodes(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def _fake_audio_driver_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        call_name = _call_name(node.func)
        if call_name in FAKE_AUDIO_DRIVER_CALLS:
            calls.add(call_name)
    return calls


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _format_violation_details(name_matches: list[str], fact_matches: dict[str, str]) -> str:
    details: list[str] = []
    if name_matches:
        details.append("test name declares real audio coverage: " + ", ".join(name_matches))
    details.extend(f"{term}: {reason}" for term, reason in sorted(fact_matches.items()))
    return "; ".join(details)
