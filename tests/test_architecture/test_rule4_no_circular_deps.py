"""Rule 4: no circular dependencies in addon-relative imports."""

from typing import Union

import pytest

from .conftest import ALL_LAYERS, _get_module_relative_deps


def _build_dep_graph() -> dict[str, set[str]]:
    """Build adjacency list of module-level relative imports."""
    graph: dict[str, set[str]] = {}
    for name in ALL_LAYERS:
        graph[name] = _get_module_relative_deps(name)
    return graph


def _find_cycle(graph: dict[str, set[str]]) -> Union[list[str], None]:
    """DFS cycle detection. Returns cycle path or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    path: list[str] = []

    def dfs(node: str) -> Union[list[str], None]:
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
            if color[neighbor] == WHITE:
                result = dfs(neighbor)
                if result is not None:
                    return result
        path.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle is not None:
                return cycle
    return None


class TestNoCycles:
    """Build a dependency graph from relative imports and detect cycles via DFS."""

    def test_no_circular_dependencies(self) -> None:
        graph = _build_dep_graph()
        cycle = _find_cycle(graph)
        if cycle is not None:
            pytest.fail(f"Circular dependency: {' → '.join(cycle)}")
