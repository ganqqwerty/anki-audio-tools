"""Rule 47: lifecycle bridge payloads are schema-owned generated values."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts/communication.schema.json"
BRIDGE = ROOT / "addon/anki_audio_quick_editor/editor_lifecycle_bridge.py"


def test_lifecycle_variants_are_owned_by_the_communication_schema() -> None:
    definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["definitions"]
    assert {
        "PendingEditorIntent",
        "EditorIntentReceipt",
        "RecorderCommand",
        "RecorderSnapshot",
        "SourceMutationCommand",
    } <= definitions.keys()
    for name in (
        "PendingEditorIntent",
        "EditorIntentReceipt",
        "RecorderSnapshot",
        "SourceMutationCommand",
    ):
        assert definitions[name].get("additionalProperties") is False
    for variant in definitions["RecorderCommand"]["oneOf"]:
        referenced = variant["$ref"].removeprefix("#/definitions/")
        assert definitions[referenced].get("additionalProperties") is False


def test_lifecycle_bridge_decodes_generated_types_at_ingress() -> None:
    source = BRIDGE.read_text(encoding="utf-8")
    assert "EditorIntentReceipt.from_dict(command.payload)" in source
    assert "RecorderCommand.from_dict(command.payload)" in source
    assert "SourceMutationCommand.from_dict(command.payload)" in source
    assert "command.payload[" not in source
    assert "command.payload.get(" not in source
