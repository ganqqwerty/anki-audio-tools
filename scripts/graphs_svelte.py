#!/usr/bin/env python3
"""Generate Svelte/TypeScript dependency graphs using regex-based import analysis.

Outputs .dot files and renders them to SVG with graphviz.

Output:
  docs/graphs/svelte-overview.svg
  docs/graphs/svelte-editor.svg
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = ROOT / "docs" / "graphs"
UI_SRC = ROOT / "settings_ui" / "src"

GRAPHS.mkdir(parents=True, exist_ok=True)

# Pattern for import/export lines in TypeScript and Svelte files
IMPORT_RE = re.compile(
    r"""(?:import|export)\s+
       (?:type\s+)?
       (?:\{[^}]*\}|\*\s+as\s+\w+|\w+)?
       \s*from\s*['\"]([^'\"]+)['\"]""",
    re.VERBOSE | re.MULTILINE,
)

# Pattern for dynamic/async imports
DYNAMIC_IMPORT_RE = re.compile(
    r"""import\s*\(\s*['\"]([^'\"]+)['\"]""",
    re.MULTILINE,
)


def _resolve_ts_import(from_module: Path, import_path: str) -> str | None:
    """Resolve a TypeScript import path to a relative file path.

    Handles:
    - Relative imports: './foo', '../bar'
    - Path aliases: '$lib/foo' -> 'src/lib/foo'
    - Bare specifiers: 'svelte' -> ignored (external)
    """
    if import_path.startswith("."):
        resolved = (from_module.parent / import_path).resolve()
        rel = resolved.relative_to(UI_SRC.parent)
        return str(rel)
    if import_path.startswith("$lib/"):
        lib_path = import_path[len("$lib/"):]
        return f"src/lib/{lib_path}"
    if import_path.startswith("$app/") or import_path.startswith("svelte"):
        return None
    # External dependency
    if "/" not in import_path:
        return None
    return None


def _collect_ts_imports(file_path: Path) -> set[str]:
    """Extract import targets from a TypeScript or Svelte file."""
    if not file_path.is_file():
        return set()
    try:
        source = file_path.read_text()
    except UnicodeDecodeError:
        return set()

    imports: set[str] = set()
    for match in IMPORT_RE.finditer(source):
        resolved = _resolve_ts_import(file_path, match.group(1))
        if resolved:
            imports.add(resolved)
    for match in DYNAMIC_IMPORT_RE.finditer(source):
        resolved = _resolve_ts_import(file_path, match.group(1))
        if resolved:
            imports.add(resolved)

    return imports


def _relative_path(file_path: Path) -> str:
    """Get path relative to settings_ui/."""
    return str(file_path.relative_to(UI_SRC.parent))


def _build_ts_graph(entry_points: list[str]) -> dict[str, set[str]]:
    """Build a dependency graph starting from entry points."""
    graph: dict[str, set[str]] = defaultdict(set)
    visited: set[str] = set()
    to_visit: set[str] = set()

    for ep in entry_points:
        full_path = UI_SRC.parent / ep
        if full_path.is_file():
            to_visit.add(ep)
        elif full_path.is_dir():
            for f in full_path.rglob("*"):
                if f.suffix in (".ts", ".svelte") and not f.name.startswith("_") and f.name != "globals.d.ts":
                    to_visit.add(_relative_path(f))

    while to_visit:
        rel = to_visit.pop()
        if rel in visited:
            continue
        visited.add(rel)

        full_path = UI_SRC.parent / rel
        if not full_path.is_file():
            continue

        imports = _collect_ts_imports(full_path)
        for imp in imports:
            # resolve to actual file
            imp_path = UI_SRC.parent / imp
            if not imp_path.is_file():
                # Try adding extensions
                for ext in (".ts", ".svelte", "/index.ts", "/index.svelte"):
                    candidate = UI_SRC.parent / (imp + ext)
                    if candidate.is_file():
                        imp_path = candidate
                        imp += ext
                        break
                else:
                    continue

            imp_rel = _relative_path(imp_path)
            graph[rel].add(imp_rel)
            if imp_rel not in visited:
                to_visit.add(imp_rel)

    return dict(graph)


def _to_dot(graph: dict[str, set[str]], output: Path, *, title: str = "") -> Path:
    """Write a DOT file from a dependency graph."""
    dot_path = output.with_suffix(".dot")

    def _short(name: str) -> str:
        return name.removeprefix("src/")

    def _cluster(name: str) -> str:
        parts = _short(name).split("/")
        if len(parts) >= 2:
            return parts[0]
        return "root"

    lines = [
        "digraph G {",
        '    rankdir=LR;',
        '    node [shape=box, style=filled, fillcolor="#febbff", fontname="Helvetica", fontsize=9];',
        '    edge [color="#999999", fontname="Helvetica", fontsize=7];',
        '    bgcolor="transparent";',
    ]

    if title:
        lines.append('    labelloc="t";')
        lines.append(f'    label="{title}";')
        lines.append('    fontsize=14;')

    nodes: set[str] = set()
    for src, deps in graph.items():
        nodes.add(src)
        nodes.update(deps)

    clusters: dict[str, list[str]] = defaultdict(list)
    for node in sorted(nodes):
        clusters[_cluster(node)].append(node)

    for cluster_name, cluster_nodes in sorted(clusters.items()):
        safe_cluster = cluster_name.replace("-", "_").replace(".", "_").replace("/", "_")
        lines.append(f'    subgraph cluster_{safe_cluster} {{')
        lines.append(f'        label="{cluster_name}";')
        lines.append('        style=filled;')
        lines.append('        fillcolor="#faf5ff";')
        lines.append('        color="#d8b4fe";')
        for node in sorted(cluster_nodes):
            node_id = node.replace("/", "_").replace(".", "_").replace("-", "_")
            label = _short(node).replace("/", "/\n")
            lines.append(
                f'        {node_id} [label="{label}", tooltip="{node}"];'
            )
        lines.append("    }")

    for src, deps in graph.items():
        src_id = src.replace("/", "_").replace(".", "_").replace("-", "_")
        for dep in deps:
            dep_id = dep.replace("/", "_").replace(".", "_").replace("-", "_")
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
        print(f"[graphs-svelte] dot failed: {result.stderr}", file=sys.stderr)
        return result.returncode
    if svg_path.exists():
        print(f"  wrote {svg_path.relative_to(ROOT)}")
    return 0


def _render_graph(
    entry_points: list[str],
    svg_path: Path,
    *,
    title: str = "",
) -> int:
    """Build and render one graph."""
    if not entry_points:
        return 0

    graph = _build_ts_graph(entry_points)
    if not graph:
        print(f"[graphs-svelte] no deps found for {svg_path.name}", file=sys.stderr)
        return 0

    dot_path = _to_dot(graph, svg_path, title=title)
    return _render_dot(dot_path, svg_path)


def generate_all() -> int:
    results: list[int] = []

    results.append(
        _render_graph(
            ["src/main.ts", "src/editor-inline/main.ts", "src/batch/main.ts"],
            GRAPHS / "svelte-overview.svg",
            title="Svelte/TypeScript Overview",
        )
    )

    results.append(
        _render_graph(
            ["src/editor-inline"],
            GRAPHS / "svelte-editor.svg",
            title="Editor Inline Components",
        )
    )

    return max(results) if results else 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
