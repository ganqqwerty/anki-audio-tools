"""Settings, batch, and window-contract bridge Mermaid diagram generators."""

from __future__ import annotations

from scripts.graphs.common import (
    ADDON,
    SETTINGS_UI_SRC,
    _parse_if_name_chain,
    _parse_ts_bridge_commands,
    _parse_window_contract,
)


def _settings_ts_commands() -> list[str]:
    """Parse TypeScript bridge commands from settings and batch bridge files."""
    commands: list[str] = []
    for ts_file in ("lib/bridge.ts", "batch/bridge.ts"):
        commands.extend(_parse_ts_bridge_commands(SETTINGS_UI_SRC / ts_file))
    return sorted(set(commands))


def _settings_py_commands() -> tuple[dict[str, str], dict[str, str]]:
    """Parse Python bridge handlers for settings and batch from source."""
    settings_handlers = _parse_if_name_chain(ADDON / "settings" / "commands.py")
    batch_handlers = _parse_if_name_chain(ADDON / "browser_dialog.py")
    return settings_handlers, batch_handlers


def _settings_diagram(
    settings_handlers: dict[str, str], batch_handlers: dict[str, str]
) -> str:
    """Assemble the settings + batch bridge Mermaid diagram."""
    lines = [
        "flowchart TD",
        "",
        '    subgraph SettingsCommands["Settings Commands<br/>(bridge:{json} envelope)"]',
    ]
    for cmd, handler in sorted(settings_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f'        s_{slug}["{cmd}"]')
    lines.append("    end")

    lines.append("")
    lines.append(
        '    subgraph BatchCommands["Batch Commands<br/>(bridge:{json} envelope)"]'
    )
    for cmd, handler in sorted(batch_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f'        b_{slug}["{cmd}"]')
    lines.append("    end")

    lines.append("")
    lines.append('    subgraph SettingsHandlers["Python: settings/commands.py"]')
    for cmd, handler in sorted(settings_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f'        sh_{slug}["{handler}"]')
    lines.append("    end")

    lines.append("")
    lines.append('    subgraph BatchHandlers["Python: browser_dialog.py"]')
    for cmd, handler in sorted(batch_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f'        bh_{slug}["{handler}"]')
    lines.append("    end")

    lines.append("")
    lines.append('    subgraph Services["Backend Services"]')
    lines.append('        ts_settings_bridge["lib/bridge.ts"]')
    lines.append('        ts_batch_bridge["batch/bridge.ts"]')
    lines.append("    end")

    for cmd in sorted(settings_handlers):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"    ts_settings_bridge --> s_{slug}")

    for cmd in sorted(batch_handlers):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"    ts_batch_bridge --> b_{slug}")

    return "\n".join(lines)


def _build_settings_batch() -> str:
    """Generate the settings + batch bridge messages Mermaid diagram."""
    settings_handlers, batch_handlers = _settings_py_commands()
    return _settings_diagram(settings_handlers, batch_handlers)


def _build_window_contract() -> str:
    """Generate the window contract Mermaid diagram."""
    entries = _parse_window_contract(
        SETTINGS_UI_SRC / "editor-inline" / "window-contract.ts"
    )

    lines = [
        "flowchart TD",
        '    subgraph Python["Python (evalWithCallback / web.eval)"]',
        "        py[\"editor_bridge.py<br/>editor_lifecycle_bridge.py<br/>editor_recording.py\"]",
        "    end",
        "",
        '    subgraph Window["window.__aqe* JavaScript Contract"]',
    ]
    for entry in entries:
        name = entry["window_name"]
        lines.append(f"        {name.lstrip('_').replace('__', '')}[\"{name}()\"]")
    lines.append("    end")

    lines.append("")
    lines.append('    py --> |"eval()"| Window')
    lines.append("")
    lines.append('    subgraph Legend["Legend"]')
    lines.append(
        '        note["22 entry points<br/>Install: installEditorWindowContract()<br/>File: window-contract.ts"]'
    )
    lines.append("    end")

    return "\n".join(lines)
