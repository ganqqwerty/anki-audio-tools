"""Rule 33: editor field state is canonical, not rebuilt from DOM."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
EDITOR_INLINE = ROOT / "settings_ui" / "src" / "editor-inline"
FIELD_STATE_STORE = EDITOR_INLINE / "field-state-store.ts"
HTML_AUDIO_PORT = EDITOR_INLINE / "html-audio-session-audio-element.ts"
HTML_AUDIO_PORT_EVENTS = EDITOR_INLINE / "html-audio-session-port-events.ts"

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

AQE_SOURCE_FILENAME_DATASET_FILES = {
    "dom-selectors.ts",
    "field-controller.ts",
    "field-state-dom-sync.ts",
    "graph-actions.ts",
    "runtime.ts",
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


def test_aqe_source_filename_dataset_is_limited_to_discovery_and_projection() -> None:
    violations: list[str] = []
    for path in sorted(EDITOR_INLINE.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        if path.name in AQE_SOURCE_FILENAME_DATASET_FILES:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if ".dataset.aqeSourceFilename" in stripped:
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: {stripped}")

    assert violations == [], "\n".join(violations)


def test_audio_clock_event_callbacks_carry_media_event_facts() -> None:
    source = HTML_AUDIO_PORT.read_text(encoding="utf-8")

    assert "onEnded: (ord: number, identity: TransportAttemptIdentity, cursorMs: number) => void;" in source
    assert "onAudioError: (" in source
    assert "mediaErrorCode: number | null," in source
    assert "mediaResponseStatus: number | null," in source
    assert "const mediaErrorCode = audio.error?.code ?? null;" in source
    assert "mediaResponseStatusFor(failedSrc).then(report)" in source
    assert (
        "callbacks.onAudioError(ord, identity, audioCurrentTimeMs(audio), mediaErrorCode, mediaResponseStatus);"
        in source
    )


def test_audio_clock_playback_event_callbacks_do_not_re_read_field_state() -> None:
    source = HTML_AUDIO_PORT_EVENTS.read_text(encoding="utf-8")
    violations: list[str] = []
    for callback_name in ("onAudioError", "onEnded"):
        body = _object_method_body(source, callback_name)
        if "readFieldState(" in body:
            violations.append(
                f"{HTML_AUDIO_PORT_EVENTS.relative_to(ROOT)}:{callback_name} re-reads field state"
            )

    assert violations == [], "\n".join(violations)


def _object_method_body(source: str, method_name: str) -> str:
    marker = f"{method_name}("
    start = source.find(marker)
    assert start >= 0, f"{method_name} callback not found"
    brace = source.find("{", start)
    assert brace >= 0, f"{method_name} callback body not found"
    depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace:index + 1]
    raise AssertionError(f"{method_name} callback body is not balanced")
