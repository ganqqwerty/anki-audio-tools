#!/usr/bin/env python3
"""Generate Python dependency graphs using ast-based import analysis.

Outputs .dot files and renders them to SVG with graphviz.

Output:
  docs/graphs/python-overview.svg
  docs/graphs/python-audio-core.svg
  docs/graphs/python-editor.svg
  docs/graphs/python-bridge.svg
  docs/graphs/python-infra.svg
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = ROOT / "docs" / "graphs"
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
PKG = "anki_audio_quick_editor"

GRAPHS.mkdir(parents=True, exist_ok=True)


def _collect_imports(py_file: Path) -> set[str]:
    """Extract all import targets from a Python file."""
    if not py_file.is_file():
        return set()
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                level = node.level
                if level > 0:
                    module_path = py_file.relative_to(ADDON).parent
                    parts = list(module_path.parts)
                    for _ in range(level - 1):
                        if parts:
                            parts.pop()
                    if parts:
                        imports.add(f"{PKG}.{'.'.join(parts)}.{node.module}")
                    else:
                        imports.add(f"{PKG}.{node.module}")
                else:
                    imports.add(node.module)
    return imports


def _module_name(py_file: Path) -> str:
    """Convert a Python file path to its dotted module name."""
    rel = py_file.relative_to(ADDON.parent)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def _build_graph(
    include_modules: set[str], focus_prefixes: tuple[str, ...] = ()
) -> dict[str, set[str]]:
    """Build a dependency graph for the given modules.

    include_modules: set of module names to include as starting nodes
    focus_prefixes: only show nodes matching these prefixes (empty = all)
    """
    graph: dict[str, set[str]] = defaultdict(set)
    visited: set[str] = set()
    to_visit: set[str] = set(include_modules)

    while to_visit:
        mod_name = to_visit.pop()
        if mod_name in visited:
            continue
        visited.add(mod_name)

        mod = ADDON
        for part in mod_name.split("."):
            if part == PKG:
                continue
            child = mod / part
            if child.is_dir():
                if (child / "__init__.py").is_file():
                    mod = child
                else:
                    mod = None
                    break
            elif (mod / f"{part}.py").is_file():
                mod = mod / f"{part}.py"
                break
            else:
                mod = None
                break

        if mod is None or not mod.is_file():
            continue

        imports = _collect_imports(mod)
        for imp in imports:
            if imp.startswith(PKG) or any(
                imp.startswith(prefix) for prefix in focus_prefixes
            ):
                if not focus_prefixes or imp.startswith(PKG):
                    graph[mod_name].add(imp)
                    if imp not in visited:
                        to_visit.add(imp)

    return dict(graph)


def _to_dot(
    graph: dict[str, set[str]],
    output: Path,
    *,
    title: str = "",
    focus: tuple[str, ...] = (),
) -> Path:
    """Write a DOT file from a dependency graph."""
    dot_path = output.with_suffix(".dot")

    def _short(name: str) -> str:
        prefix = f"{PKG}."
        return name[len(prefix):] if name.startswith(prefix) else name

    def _cluster(name: str) -> str:
        parts = _short(name).split(".")
        if len(parts) >= 1:
            return parts[0]
        return "other"

    lines = [
        "digraph G {",
        '    rankdir=LR;',
        '    node [shape=box, style=filled, fillcolor="#85bbf0", fontname="Helvetica", fontsize=10];',
        '    edge [color="#666666", fontname="Helvetica", fontsize=8];',
        '    bgcolor="transparent";',
    ]

    if title:
        lines.append('    labelloc="t";')
        lines.append(f'    label="{title}";')
        lines.append('    fontsize=14;')

    nodes: set[str] = set()
    for src, deps in graph.items():
        if focus and not any(src.startswith(f) for f in focus):
            continue
        nodes.add(src)
        for dep in deps:
            if focus and not any(dep.startswith(f) for f in focus):
                continue
            nodes.add(dep)

    clusters: dict[str, list[str]] = defaultdict(list)
    for node in sorted(nodes):
        clusters[_cluster(node)].append(node)

    for cluster_name, cluster_nodes in sorted(clusters.items()):
        safe_name = cluster_name.replace("-", "_").replace(".", "_")
        lines.append(f'    subgraph cluster_{safe_name} {{')
        lines.append(f'        label="{cluster_name}";')
        lines.append('        style=filled;')
        lines.append('        fillcolor="#f0f4f8";')
        lines.append('        color="#d0d7de";')
        for node in sorted(cluster_nodes):
            node_id = node.replace(".", "_").replace("-", "_")
            lines.append(
                f'        {node_id} [label="{_short(node)}", '
                f'tooltip="{node}"];'
            )
        lines.append("    }")

    for src, deps in graph.items():
        if focus and not any(src.startswith(f) for f in focus):
            continue
        src_id = src.replace(".", "_").replace("-", "_")
        for dep in deps:
            if focus and not any(dep.startswith(f) for f in focus):
                continue
            dep_id = dep.replace(".", "_").replace("-", "_")
            lines.append(f"    {src_id} -> {dep_id};")

    lines.append("}")
    dot_path.write_text("\n".join(lines) + "\n")
    return dot_path


def _render_dot(dot_path: Path, svg_path: Path) -> int:
    """Render a DOT file to SVG using graphviz."""
    result = subprocess.run(
        ["dot", "-T", "svg", "-o", str(svg_path), str(dot_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[graphs-python] dot failed: {result.stderr}", file=sys.stderr)
        return result.returncode
    if svg_path.exists():
        print(f"  wrote {svg_path.relative_to(ROOT)}")
    return 0


def _render_graph(
    modules: list[str],
    svg_path: Path,
    *,
    title: str = "",
    focus: tuple[str, ...] = (),
) -> int:
    """Build and render one graph."""
    if not modules:
        return 0

    graph = _build_graph(set(modules), focus)
    if not graph:
        print(f"[graphs-python] no deps found for {svg_path.name}", file=sys.stderr)
        return 0

    dot_path = _to_dot(graph, svg_path, title=title, focus=focus)
    return _render_dot(dot_path, svg_path)


def _collect_pkg_modules(prefix: str) -> list[str]:
    """Collect all module names under a given prefix within the addon package."""
    modules: list[str] = []
    prefix_path = ADDON
    prefix_parts = prefix.split(".")
    pkg_parts = PKG.split(".")

    # Skip the package name parts
    part_idx = 0
    while part_idx < len(prefix_parts) and part_idx < len(pkg_parts):
        if prefix_parts[part_idx] == pkg_parts[part_idx]:
            part_idx += 1
        else:
            break

    remaining = prefix_parts[part_idx:]
    for part in remaining:
        prefix_path = prefix_path / part

    if prefix_path.is_dir():
        for py_file in sorted(prefix_path.rglob("*.py")):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            modules.append(_module_name(py_file))
        return modules

    # prefix is a filename prefix, not a subdirectory (e.g. "editor_*")
    parent = prefix_path.parent
    glob_pattern = f"{prefix_path.name}*.py"
    if parent.is_dir():
        for py_file in sorted(parent.glob(glob_pattern)):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            modules.append(_module_name(py_file))
    return modules


def generate_all() -> int:
    results: list[int] = []

    # Collect all modules in the addon for maximum coverage
    all_modules = set()
    for py_file in ADDON.rglob("*.py"):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        all_modules.add(_module_name(py_file))

    # Overview: set of entry-point modules, show the whole package
    entries = [
        f"{PKG}.__init__",
        f"{PKG}.editor_integration",
        f"{PKG}.editor_bridge",
        f"{PKG}.browser_integration",
        f"{PKG}.browser_dialog",
        f"{PKG}.reviewer_integration",
        f"{PKG}.webview_bridge",
        f"{PKG}.webview_shell",
        f"{PKG}.audio_processor",
        f"{PKG}.diagnostics_runtime",
        f"{PKG}.runtime_install",
    ]
    results.append(
        _render_graph(
            entries,
            GRAPHS / "python-overview.svg",
            title="Python Package Overview",
            focus=(f"{PKG}.",),
        )
    )

    # Audio core
    audio_modules = _collect_pkg_modules(f"{PKG}.audio")
    audio_modules.extend(_collect_pkg_modules(f"{PKG}.batch"))
    audio_modules.append(f"{PKG}.prosody_analyzer")
    audio_modules.append(f"{PKG}.prosody_cache")
    audio_modules.append(f"{PKG}.prosody_svg")
    results.append(
        _render_graph(
            audio_modules,
            GRAPHS / "python-audio-core.svg",
            title="Audio Core & Batch Operations",
            focus=(f"{PKG}.audio_", f"{PKG}.batch_", f"{PKG}.prosody_"),
        )
    )

    # Editor
    editor_modules = _collect_pkg_modules(f"{PKG}.editor")
    editor_modules.append(f"{PKG}.editor_frontend_callbacks")
    results.append(
        _render_graph(
            editor_modules,
            GRAPHS / "python-editor.svg",
            title="Editor Adapters",
            focus=(f"{PKG}.editor_", f"{PKG}.editor_frontend"),
        )
    )

    # Bridge
    bridge_modules = [
        f"{PKG}.webview_bridge",
        f"{PKG}.webview_shell",
        f"{PKG}.editor_frontend.bridge",
        f"{PKG}.editor_frontend_callbacks",
        f"{PKG}.editor_frontend.busy",
        f"{PKG}.editor_frontend.playback",
        f"{PKG}.editor_frontend.refresh",
        f"{PKG}.editor_frontend.status",
        f"{PKG}.editor_frontend.types",
    ]
    results.append(
        _render_graph(
            bridge_modules,
            GRAPHS / "python-bridge.svg",
            title="WebView Bridge Infrastructure",
            focus=(f"{PKG}.webview_", f"{PKG}.editor_frontend", f"{PKG}.settings."),
        )
    )

    # Infrastructure
    infra_modules = [
        f"{PKG}.runtime_install",
        f"{PKG}.runtime_manager",
        f"{PKG}.runtime_manifest",
        f"{PKG}.diagnostics_runtime",
        f"{PKG}.diagnostics",
        f"{PKG}.diagnostics_runtime_json",
        f"{PKG}.diagnostics_runtime_storage",
        f"{PKG}.config_migration",
        f"{PKG}.support",
        f"{PKG}.support_reporting",
        f"{PKG}.error_codes",
        f"{PKG}.errors",
        f"{PKG}.frontend_logs",
        f"{PKG}.i18n",
        f"{PKG}.external_links",
        f"{PKG}.editor_button_visibility",
        f"{PKG}.editor_actions",
    ]
    results.append(
        _render_graph(
            infra_modules,
            GRAPHS / "python-infra.svg",
            title="Infrastructure: Runtime, Config, Diagnostics",
            focus=(
                f"{PKG}.runtime_",
                f"{PKG}.diagnostics_",
                f"{PKG}.config_",
                f"{PKG}.support_",
                f"{PKG}.error_",
                f"{PKG}.frontend_logs",
                f"{PKG}.i18n",
                f"{PKG}.external_links",
                f"{PKG}.editor_button_visibility",
                f"{PKG}.editor_actions",
            ),
        )
    )

    return max(results) if results else 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
