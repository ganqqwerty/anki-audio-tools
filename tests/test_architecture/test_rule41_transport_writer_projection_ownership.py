"""Rule 41: transport writes stay in the controller and views consume projections."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR_INLINE = ROOT / "settings_ui/src/editor-inline"


def test_transport_reducer_has_one_production_caller() -> None:
    callers = []
    for path in sorted(EDITOR_INLINE.rglob("*.ts")):
        if path.name == "html-audio-session-machine.ts":
            continue
        if "transitionHtmlAudioSession(" in path.read_text(encoding="utf-8"):
            callers.append(path.relative_to(ROOT).as_posix())
    assert callers == ["settings_ui/src/editor-inline/html-audio-session-controller.ts"]


def test_transport_writer_has_structural_frontend_canaries() -> None:
    source = (ROOT / "settings_ui/tests/state-management-architecture.test.ts").read_text(
        encoding="utf-8"
    )
    assert "Rule 41 / SM-A03" in source
    assert "sessionStates.set" in source
