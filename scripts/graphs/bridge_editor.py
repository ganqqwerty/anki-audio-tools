"""Editor bridge Mermaid diagram generators."""

from __future__ import annotations

from scripts.graphs.common import SETTINGS_UI_SRC, _parse_ts_bridge_commands


def _editor_fields() -> list[tuple[str, str, list[str]]]:
    """Return editor command categories as (subgraph_id, label, commands) tuples."""
    return [
        (
            "ProcessingCommands",
            "Processing Commands<br/>(update_state_and_render)",
            [
                "aqe:slower",
                "aqe:faster",
                "aqe:volume-down",
                "aqe:volume-up",
                "aqe:remove-pauses",
            ],
        ),
        (
            "NonProcessingCommands",
            "Non-Processing Commands",
            [
                "aqe:play",
                "aqe:stop-playback",
                "aqe:play-ended",
                "aqe:undo",
                "aqe:redo",
                "aqe:scan",
                "aqe:analyze",
                "aqe:analyze-field",
                "aqe:set-cursor",
                "aqe:settings",
                "aqe:show-file",
                "aqe:open-url",
                "aqe:frontend-log",
                "aqe:command-payload",
            ],
        ),
        (
            "RecordingCommands",
            "Recording Commands",
            [
                "aqe:record-voice",
                "aqe:stop-recording",
                "aqe:play-recording",
                "aqe:show-recording-file",
                "aqe:share-recording",
            ],
        ),
        (
            "DenoiseCommands",
            "Denoise Commands",
            [
                "aqe:denoise-standard",
                "aqe:rnnoise",
                "aqe:dpdfnet",
                "aqe:voice-only",
            ],
        ),
        (
            "PayloadCommands",
            "Payload Commands",
            [
                "aqe:convert",
                "aqe:reduce-size",
                "aqe:pitch-hum",
                "aqe:share",
                "aqe:post-edit-playback-ready",
                "aqe:delete-selection",
                "aqe:delete-rest",
                "aqe:save-split-defaults",
                "aqe:source-metadata",
            ],
        ),
        (
            "ChorusCommands",
            "Chorusing Commands",
            [
                "aqe:chorusing-practice",
                "aqe:chorusing-previous",
                "aqe:chorusing-next",
            ],
        ),
    ]


def _editor_bridge_dispatch(fields: list[tuple[str, str, list[str]]]) -> str:
    """Render Mermaid subgraphs for editor command categories."""
    lines: list[str] = []
    for subgraph_id, label, commands in fields:
        lines.append(f'    subgraph {subgraph_id}["{label}"]')
        for cmd in commands:
            slug = cmd.replace(":", "_").replace("-", "_")
            lines.append(f'        {slug}["{cmd}"]')
        lines.append("    end")
        lines.append("")
    return "\n".join(lines)


def _editor_py_bridge() -> str:
    """Render Mermaid subgraph for Python editor handlers and dispatch arrows."""
    lines: list[str] = []
    lines.append("    subgraph Handlers[\"Python Handlers\"]")
    lines.append("        editor_bridge[\"handle_bridge_command()\"]")
    lines.append("        non_proc[\"handle_non_processing_command()\"]")
    lines.append("        payload_handler[\"handle_payload_command()\"]")
    lines.append("        update[\"update_state_and_render()\"]")
    lines.append("    end")
    lines.append("")
    lines.append("    aqe_slower --> update")
    lines.append("    aqe_faster --> update")
    lines.append("    aqe_volume_down --> update")
    lines.append("    aqe_volume_up --> update")
    lines.append("    aqe_remove_pauses --> update")
    lines.append("")
    lines.append("    aqe_play --> non_proc")
    lines.append("    aqe_stop_playback --> non_proc")
    lines.append("    aqe_denoise_standard --> non_proc")
    lines.append("    aqe_convert --> payload_handler")
    return "\n".join(lines)


def _editor_ts_bridge() -> str:
    """Parse editor TypeScript bridge commands (informational, not rendered in diagram)."""
    _parse_ts_bridge_commands(SETTINGS_UI_SRC / "editor-inline" / "bridge.ts")
    return ""


def _editor_diagram(fields: list[tuple[str, str, list[str]]]) -> str:
    """Assemble the full editor bridge messages diagram."""
    lines = [
        "flowchart TD",
        "",
        _editor_bridge_dispatch(fields),
        _editor_py_bridge(),
    ]
    return "\n".join(lines)


def _build_editor() -> str:
    """Generate the editor bridge messages Mermaid diagram."""
    fields = _editor_fields()
    return _editor_diagram(fields)
