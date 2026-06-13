#!/usr/bin/env python3
"""Generate webview injection Mermaid diagram from docs/architecture/webviews.yaml.

Output:
  docs/graphs/webview-injection.mmd
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = ROOT / "docs" / "graphs"
WEBVIEWS_YAML = ROOT / "docs" / "architecture" / "webviews.yaml"

GRAPHS.mkdir(parents=True, exist_ok=True)

MERMAID_HEADER = "```mermaid\n"
MERMAID_FOOTER = "\n```\n"


def _parse_yaml(path: Path) -> list[dict]:
    """Minimal YAML parser for webviews.yaml structure."""
    if not path.is_file():
        return []
    text = path.read_text()
    screens: list[dict] = []
    current: dict | None = None
    in_hooks = False
    in_assets = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if stripped.endswith(":"):
            key = stripped[:-1]
            if indent == 0 and key == "screens":
                continue
            if indent == 2:
                current = {"name": key}
                screens.append(current)
            elif indent == 4 and current is not None:
                in_hooks = key == "hooks"
                in_assets = key == "assets"
            continue

        if current is None:
            continue

        if stripped.startswith("- ") and (in_hooks or in_assets):
            value = stripped[2:].strip()
            list_key = "hooks" if in_hooks else "assets"
            current.setdefault(list_key, []).append(value)
            continue

        if ":" in stripped and not stripped.startswith("-"):
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if current is not None:
                current[key] = value
                in_hooks = False
                in_assets = False

    return screens


def _render(screens: list[dict]) -> str:
    lines = [
        "flowchart TD",
        "",
        "    subgraph AnkiHooks[\"Anki Hooks\"]",
    ]
    hook_ids: dict[str, str] = {}
    hook_counter = 0
    for s in screens:
        for hook in s.get("hooks", []):
            hid = f"hook_{hook_counter}"
            hook_ids[hook] = hid
            lines.append(f"        {hid}[\"{hook}\"]")
            hook_counter += 1
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph PythonEntry[\"Python Entry Points\"]")

    pyt_id = 0
    for s in screens:
        name = s["name"]
        entry = s.get("python_entry", "")
        dispatcher = s.get("python_dispatcher", "")
        lines.append(f"        py_{name}[\"{name}: {Path(entry).name}\"]")
        lines.append(f"        disp_{name}[\"{Path(dispatcher).name}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph SvelteApps[\"Svelte Applications\"]")
    for s in screens:
        name = s["name"]
        ts_bridge = s.get("ts_bridge", "")
        frontend = s.get("frontend_root", "")
        lines.append(f"        svelte_{name}[\"{name}: {Path(frontend).name}\"]")
        lines.append(f"        bridge_{name}[\"{Path(ts_bridge).name}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph Bundles[\"Generated Bundles\"]")
    for s in screens:
        name = s["name"]
        for asset in s.get("assets", []):
            aid = f"asset_{name}_{Path(asset).stem}"
            lines.append(f"        {aid}[\"{Path(asset).name}\"]")
    lines.append("    end")

    lines.append("")
    for s in screens:
        name = s["name"]
        for hook in s.get("hooks", []):
            if hook in hook_ids:
                lines.append(f"    {hook_ids[hook]} --> py_{name}")
        protocol = s.get("protocol", "")
        lines.append(f"    svelte_{name} -->|{protocol[:30]}...| py_{name}")

    return "\n".join(lines)


def generate() -> int:
    screens = _parse_yaml(WEBVIEWS_YAML)
    if not screens:
        print(
            "[graphs-webview] no screens found in webviews.yaml",
        )
        return 1

    output = GRAPHS / "webview-injection.mmd"
    output.write_text(MERMAID_HEADER + _render(screens) + MERMAID_FOOTER)
    print(f"  wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(generate())
