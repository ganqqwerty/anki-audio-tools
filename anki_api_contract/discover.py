"""Discover the Anki API surface used by the add-on source."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
EXCLUDED_PARTS = {"__pycache__", "aqe_artifacts", "bin", "templates", "vendor"}


@dataclass(frozen=True, order=True)
class ImportedObject:
    """One imported Anki object that must exist."""

    module: str
    name: str

    @property
    def display_name(self) -> str:
        """Return a readable fully qualified API name."""
        return f"{self.module}.{self.name}"


@dataclass(frozen=True, order=True)
class CallableUse:
    """One callable Anki API use discovered from source."""

    module: str
    qualname: str
    positional_args: int
    keywords: tuple[str, ...] = ()
    implicit_self: bool = False
    exact: bool = False
    exact_parameter_names: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        """Return a readable callable name plus the discovered call shape."""
        args = self.positional_args + (1 if self.implicit_self else 0)
        keywords = ",".join(self.keywords)
        suffix = f"args={args}"
        if keywords:
            suffix = f"{suffix};kw={keywords}"
        return f"{self.module}.{self.qualname} ({suffix})"


@dataclass(frozen=True)
class AnkiApiSurface:
    """The Anki API surface discovered from the add-on source."""

    imported_modules: tuple[str, ...]
    imported_objects: tuple[ImportedObject, ...]
    callable_uses: tuple[CallableUse, ...]


@dataclass(frozen=True)
class _RuntimeOwner:
    segment: str
    module: str
    class_name: str


RUNTIME_OWNERS = (
    _RuntimeOwner("addonManager", "aqt.addons", "AddonManager"),
    _RuntimeOwner("taskman", "aqt.taskman", "TaskManager"),
    _RuntimeOwner("media", "anki.media", "MediaManager"),
    _RuntimeOwner("decks", "anki.decks", "DeckManager"),
    _RuntimeOwner("models", "anki.models", "ModelManager"),
    _RuntimeOwner("db", "anki.db", "DB"),
)


class _AnkiApiVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imported_modules: set[str] = set()
        self.imported_objects: set[ImportedObject] = set()
        self.callable_uses: set[CallableUse] = set()
        self.aliases: dict[str, ImportedObject] = {}
        self.function_parameters: dict[str, tuple[str, ...]] = {}

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            module_name = alias.name
            if not _is_anki_module(module_name):
                continue
            local_name = alias.asname or module_name.split(".", 1)[0]
            self.aliases[local_name] = ImportedObject(module_name, "")
            self.imported_modules.add(module_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.module is None or not _is_anki_module(node.module):
            self.generic_visit(node)
            return
        self.imported_modules.add(node.module)
        for alias in node.names:
            if alias.name == "*":
                continue
            local_name = alias.asname or alias.name
            imported = ImportedObject(node.module, alias.name)
            self.aliases[local_name] = imported
            self.imported_objects.add(imported)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.function_parameters[node.name] = _function_parameter_names(node.args)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.function_parameters[node.name] = _function_parameter_names(node.args)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        parts = _attribute_parts(node.func)
        if parts:
            self._record_call(parts, node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        self._record_subscript_assignments(node.targets)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        self._record_subscript_assignments((node.target,))
        self.generic_visit(node)

    def _record_call(self, parts: tuple[str, ...], node: ast.Call) -> None:
        self._record_direct_import_call(parts, node)
        self._record_hook_call(parts, node)
        self._record_mapped_object_call(parts, node)

    def _record_direct_import_call(self, parts: tuple[str, ...], node: ast.Call) -> None:
        root = parts[0]
        imported = self.aliases.get(root)
        if imported is None:
            return
        if imported.name in {"", "gui_hooks", "mw"}:
            return
        self.callable_uses.add(
            _callable_use(
                imported.module,
                ".".join((imported.name, *parts[1:])),
                node,
            )
        )

    def _record_hook_call(self, parts: tuple[str, ...], node: ast.Call) -> None:
        if parts[0] != "gui_hooks":
            return
        if len(parts) == 3 and parts[2] == "append":
            callback = node.args[0] if node.args else None
            parameters = self._callback_parameters(callback)
            self.callable_uses.add(
                CallableUse(
                    "aqt.gui_hooks",
                    parts[1],
                    positional_args=len(parameters),
                    exact=True,
                    exact_parameter_names=parameters,
                )
            )
            return
        if len(parts) == 2:
            self.callable_uses.add(
                _callable_use("aqt.gui_hooks", parts[1], node, exact=True)
            )

    def _callback_parameters(self, callback: ast.AST | None) -> tuple[str, ...]:
        if isinstance(callback, ast.Name):
            return self.function_parameters.get(callback.id, ())
        if isinstance(callback, ast.Call):
            for arg in callback.args:
                if isinstance(arg, ast.Name) and arg.id in self.function_parameters:
                    return self.function_parameters[arg.id]
        return ()

    def _record_mapped_object_call(self, parts: tuple[str, ...], node: ast.Call) -> None:
        if "()" in parts:
            return
        for owner in RUNTIME_OWNERS:
            tail = _tail_after(parts, owner.segment)
            if tail:
                self.callable_uses.add(
                    _callable_use(
                        owner.module,
                        ".".join((owner.class_name, *tail)),
                        node,
                        implicit_self=True,
                    )
                )
                return

        collection_tail = _collection_tail(parts)
        if collection_tail:
            self.callable_uses.add(
                _callable_use(
                    "anki.collection",
                    ".".join(("Collection", *collection_tail)),
                    node,
                    implicit_self=True,
                )
            )
            return

        if parts[-1] == "update_undo_actions":
            self.callable_uses.add(
                _callable_use(
                    "aqt.main",
                    "AnkiQt.update_undo_actions",
                    node,
                    implicit_self=True,
                )
            )
            return

        note_tail = _note_tail(parts)
        if note_tail:
            self.callable_uses.add(
                _callable_use(
                    "anki.notes",
                    ".".join(("Note", *note_tail)),
                    node,
                    implicit_self=True,
                )
            )
            return

        webview_tail = _webview_tail(parts)
        if webview_tail:
            self.callable_uses.add(
                _callable_use(
                    "aqt.webview",
                    ".".join(("AnkiWebView", *webview_tail)),
                    node,
                    implicit_self=True,
                )
            )

    def _record_subscript_assignments(self, targets: tuple[ast.expr, ...] | list[ast.expr]) -> None:
        for target in targets:
            if not isinstance(target, ast.Subscript):
                continue
            parts = _attribute_parts(target.value)
            if parts and _is_note_object_chain(parts):
                self.callable_uses.add(
                    CallableUse(
                        "anki.notes",
                        "Note.__setitem__",
                        positional_args=2,
                        implicit_self=True,
                    )
                )


def discover_anki_api_surface(addon_dir: Path = ADDON_DIR) -> AnkiApiSurface:
    """Discover Anki imports and callable API usage from production add-on code."""
    visitor = _AnkiApiVisitor()
    trees: list[ast.AST] = []
    for path in _source_paths(addon_dir):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        trees.append(tree)
        _collect_function_parameters(visitor, tree)
    for tree in trees:
        visitor.aliases = {}
        visitor.visit(tree)

    imported_modules = set(visitor.imported_modules)
    for imported in visitor.imported_objects:
        imported_modules.add(imported.module)
    for call in visitor.callable_uses:
        imported_modules.add(call.module)

    return AnkiApiSurface(
        imported_modules=tuple(sorted(imported_modules)),
        imported_objects=tuple(sorted(visitor.imported_objects)),
        callable_uses=tuple(sorted(visitor.callable_uses)),
    )


def _source_paths(addon_dir: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in addon_dir.rglob("*.py")
            if not EXCLUDED_PARTS.intersection(path.relative_to(addon_dir).parts)
        )
    )


def _collect_function_parameters(visitor: _AnkiApiVisitor, tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor.function_parameters[node.name] = _function_parameter_names(node.args)


def _is_anki_module(module_name: str) -> bool:
    return (
        module_name == "aqt"
        or module_name.startswith("aqt.")
        or module_name == "anki"
        or module_name.startswith("anki.")
    )


def _function_parameter_names(args: ast.arguments) -> tuple[str, ...]:
    return tuple(arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs))


def _attribute_parts(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return *_attribute_parts(node.value), node.attr
    if isinstance(node, ast.Call):
        return *_attribute_parts(node.func), "()"
    if isinstance(node, ast.Subscript):
        return *_attribute_parts(node.value), "[]"
    return ()


def _callable_use(
    module: str,
    qualname: str,
    node: ast.Call,
    *,
    implicit_self: bool = False,
    exact: bool = False,
) -> CallableUse:
    return CallableUse(
        module,
        qualname,
        positional_args=len(node.args),
        keywords=tuple(sorted(keyword.arg for keyword in node.keywords if keyword.arg is not None)),
        implicit_self=implicit_self,
        exact=exact,
    )


def _tail_after(parts: tuple[str, ...], segment: str) -> tuple[str, ...]:
    try:
        index = parts.index(segment)
    except ValueError:
        return ()
    return parts[index + 1 :]


def _collection_tail(parts: tuple[str, ...]) -> tuple[str, ...]:
    if "col" not in parts:
        return ()
    return _tail_after(parts, "col")


def _note_tail(parts: tuple[str, ...]) -> tuple[str, ...]:
    if parts[0] == "note":
        return parts[1:]
    tail = _tail_after(parts, "note")
    if tail and tail[0] != "fields":
        return tail
    return ()


def _is_note_object_chain(parts: tuple[str, ...]) -> bool:
    return parts == ("note",) or (parts[-1] == "note" and "fields" not in parts)


def _webview_tail(parts: tuple[str, ...]) -> tuple[str, ...]:
    webview_tail = _tail_after(parts, "_webview")
    if webview_tail:
        return webview_tail
    if "web" in parts:
        return _tail_after(parts, "web")
    return ()
