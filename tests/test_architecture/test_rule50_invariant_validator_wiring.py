"""Rule 50: production controllers cannot bypass state/resource validators."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSPORT = ROOT / "settings_ui/src/editor-inline/html-audio-session-controller.ts"
TRANSPORT_EVENT_QUEUE = ROOT / "settings_ui/src/editor-inline/html-audio-session-event-queue.ts"
TRANSPORT_INVARIANTS = ROOT / "settings_ui/src/editor-inline/html-audio-session-invariants.ts"
RECORDER = ROOT / "addon/anki_audio_quick_editor/recorder/service.py"


def test_transport_validators_wrap_the_effect_batch() -> None:
    source = TRANSPORT.read_text(encoding="utf-8")
    queue_source = TRANSPORT_EVENT_QUEUE.read_text(encoding="utf-8")
    effects = source.index("eventDispatcher.executeEffects(ord, transition.effects")
    assert source.index("validateTransportState(transition.state)") < effects
    assert source.index("validateTransportOwnership(sessionStates)") < effects
    assert source.index("validateTransportResources(transition.state") > effects
    assert "for (const effect of effects)" in queue_source
    assert 'logger.error("transport.invariant_failed"' in TRANSPORT_INVARIANTS.read_text(
        encoding="utf-8"
    )


def test_recorder_service_validates_every_accepted_state_assignment() -> None:
    source = RECORDER.read_text(encoding="utf-8")
    assert "validate_recorder_state(self.state)" in source
    assert "state_owns_handle(self.state) != (self._controller is not None)" in source
    tree = ast.parse(source)
    missing = []
    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
        ]
        reduces = any(
            isinstance(call.func, ast.Name) and call.func.id == "reduce_recorder"
            for call in calls
        )
        validates = any(
            isinstance(call.func, ast.Attribute) and call.func.attr == "_assert_valid"
            for call in calls
        )
        if reduces and not validates:
            missing.append(function.name)
    assert missing == []
