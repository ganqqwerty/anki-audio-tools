"""Shared architecture inspection helpers for tests and reporting."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import MODULE_CONTRACTS, ModuleContract, SideEffect

ADDON_DIR = Path(__file__).parent.parent.parent / "addon" / "anki_audio_quick_editor"
ANKI_PREFIXES = ("aqt", "anki")
SIDE_EFFECT_PATTERNS: dict[SideEffect, tuple[str, ...]] = {
    SideEffect.MEDIA_WRITE: (r"\.media\.write_data\(",),
    SideEffect.NOTE_UPDATE: (r"\bcol\.update_note\(",),
    SideEffect.UNDO_MERGE: (r"\bcol\.add_custom_undo_entry\(", r"\bcol\.merge_undo_entries\("),
    SideEffect.SUBPROCESS_RUN: (r"\bsubprocess\.run\(",),
    SideEffect.SUBPROCESS_POPEN: (r"\bsubprocess\.Popen\(",),
    SideEffect.THREAD_SPAWN: (r"\bthreading\.Thread\(",),
    SideEffect.DB_ACCESS: (
        r"\bcol\.db\.",
        r"\bcol\.models\.",
        r"\bcol\.decks\.",
        r"\bmw\.col\.db\.",
        r"\bmw\.col\.models\.",
        r"\bmw\.col\.decks\.",
    ),
    SideEffect.GUI_HOOK_REGISTRATION: (r"\bgui_hooks\.[A-Za-z_]+\.append\(",),
    SideEffect.WEB_EVAL: (r"\.web\.eval\(", r"\bwebview\.eval\(", r"\b_webview\.eval\("),
    SideEffect.BACKGROUND_TASK_DISPATCH: (r"\.taskman\.run_in_background\(", r"\.taskman\.run_on_main\("),
    SideEffect.TEMP_FILESYSTEM_CLEANUP: (r"\bshutil\.rmtree\(", r"\btempfile\.mkdtemp\(", r"\btempfile\.mkstemp\("),
}


@dataclass(frozen=True)
class ModuleObservation:
    """Observed architecture surface for one production module."""

    module: str
    path: Path
    module_level_imports: tuple[str, ...]
    all_imports: tuple[str, ...]
    addon_deps: frozenset[str]
    module_level_anki_imports: frozenset[str]
    any_anki_imports: frozenset[str]
    side_effects: frozenset[SideEffect]


@dataclass(frozen=True)
class ModuleViolation:
    """One contract violation for a module."""

    module: str
    kind: str
    detail: str


def list_production_modules() -> list[str]:
    modules: list[str] = []
    for path in sorted(ADDON_DIR.glob("*.py")):
        if path.stem != "__pycache__":
            modules.append(path.stem)
    for package in sorted(ADDON_DIR.iterdir()):
        if not package.is_dir() or package.name in {"__pycache__", "templates", "vendor"}:
            continue
        if not (package / "__init__.py").exists():
            continue
        modules.append(package.name)
        for sub in sorted(package.glob("*.py")):
            if sub.stem != "__init__":
                modules.append(f"{package.name}.{sub.stem}")
    return modules


def module_to_path(module_name: str) -> Path:
    parts = module_name.split(".")
    base = ADDON_DIR / Path(*parts)
    py_file = base.with_suffix(".py")
    if py_file.exists():
        return py_file
    package_init = base / "__init__.py"
    if package_init.exists():
        return package_init
    raise FileNotFoundError(f"Module path not found for {module_name!r}")


def _is_type_checking_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
    )


def _extract_import_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    prefix = "." * node.level
    if node.module:
        return [f"{prefix}{node.module}"]
    if node.level > 0:
        return [f"{prefix}{alias.name}" for alias in node.names]
    return []


def _collect_imports(nodes: list[ast.stmt], *, recurse_into_defs: bool) -> list[str]:
    imports: list[str] = []
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_extract_import_names(node))
        elif isinstance(node, ast.If):
            if not _is_type_checking_guard(node):
                imports.extend(_collect_imports(node.body, recurse_into_defs=recurse_into_defs))
                imports.extend(_collect_imports(node.orelse, recurse_into_defs=recurse_into_defs))
        elif isinstance(node, ast.Try):
            imports.extend(_collect_imports(node.body, recurse_into_defs=recurse_into_defs))
            for handler in node.handlers:
                imports.extend(_collect_imports(handler.body, recurse_into_defs=recurse_into_defs))
            imports.extend(_collect_imports(node.orelse, recurse_into_defs=recurse_into_defs))
            imports.extend(_collect_imports(node.finalbody, recurse_into_defs=recurse_into_defs))
        elif recurse_into_defs and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            imports.extend(_collect_imports(node.body, recurse_into_defs=recurse_into_defs))
    return imports


def get_module_level_imports(path: Path) -> list[str]:
    return _collect_imports(ast.parse(path.read_text(encoding="utf-8")).body, recurse_into_defs=False)


def get_all_imports(path: Path) -> list[str]:
    return _collect_imports(ast.parse(path.read_text(encoding="utf-8")).body, recurse_into_defs=True)


def resolve_relative_import(import_name: str, source_path: Path) -> str:
    if not import_name.startswith("."):
        return import_name
    level = len(import_name) - len(import_name.lstrip("."))
    module_part = import_name.lstrip(".")
    package_parts = list(source_path.relative_to(ADDON_DIR).parts[:-1])
    remaining = max(0, len(package_parts) - (level - 1))
    prefix_parts = package_parts[:remaining]
    if module_part:
        return ".".join(prefix_parts + module_part.split("."))
    return ".".join(prefix_parts)


def _classify_module_name(resolved: str) -> str | None:
    best: str | None = None
    for module_name in MODULE_CONTRACTS:
        if resolved == module_name or resolved.startswith(module_name + "."):
            if best is None or len(module_name) > len(best):
                best = module_name
    return best


def _imports_anki(imports: list[str]) -> set[str]:
    return {m for m in imports if any(m == prefix or m.startswith(prefix + ".") for prefix in ANKI_PREFIXES)}


def _detect_side_effects(path: Path) -> set[SideEffect]:
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    joined = "\n".join(lines)
    hits: set[SideEffect] = set()
    for side_effect, patterns in SIDE_EFFECT_PATTERNS.items():
        if any(re.search(pattern, joined) for pattern in patterns):
            hits.add(side_effect)
    return hits


def observe_module(module_name: str) -> ModuleObservation:
    path = module_to_path(module_name)
    module_level_imports = tuple(get_module_level_imports(path))
    all_imports = tuple(get_all_imports(path))
    addon_deps: set[str] = set()
    for import_name in all_imports:
        if not import_name.startswith("."):
            continue
        resolved = resolve_relative_import(import_name, path)
        classified = _classify_module_name(resolved)
        if classified is not None and classified != module_name:
            addon_deps.add(classified)
    return ModuleObservation(
        module=module_name,
        path=path,
        module_level_imports=module_level_imports,
        all_imports=all_imports,
        addon_deps=frozenset(addon_deps),
        module_level_anki_imports=frozenset(_imports_anki(list(module_level_imports))),
        any_anki_imports=frozenset(_imports_anki(list(all_imports))),
        side_effects=frozenset(_detect_side_effects(path)),
    )


def observe_all_modules() -> dict[str, ModuleObservation]:
    return {module_name: observe_module(module_name) for module_name in sorted(MODULE_CONTRACTS)}


def validate_contracts(
    contracts: dict[str, ModuleContract] | None = None,
    observations: dict[str, ModuleObservation] | None = None,
) -> list[ModuleViolation]:
    contracts = contracts or MODULE_CONTRACTS
    observations = observations or observe_all_modules()
    violations: list[ModuleViolation] = []
    for module_name, contract in contracts.items():
        observation = observations[module_name]
        if not contract.allow_module_level_anki_imports and observation.module_level_anki_imports:
            violations.append(
                ModuleViolation(
                    module=module_name,
                    kind="module_level_anki_imports",
                    detail=", ".join(sorted(observation.module_level_anki_imports)),
                )
            )
        if not contract.allow_any_anki_imports and observation.any_anki_imports:
            violations.append(
                ModuleViolation(
                    module=module_name,
                    kind="anki_imports_anywhere",
                    detail=", ".join(sorted(observation.any_anki_imports)),
                )
            )
        extra_deps = sorted(observation.addon_deps - contract.allowed_addon_deps)
        if extra_deps:
            violations.append(
                ModuleViolation(
                    module=module_name,
                    kind="addon_deps",
                    detail=", ".join(extra_deps),
                )
            )
        for forbidden_prefix in contract.forbidden_import_prefixes:
            hits = [value for value in observation.all_imports if value == forbidden_prefix or value.startswith(forbidden_prefix + ".")]
            if hits:
                violations.append(
                    ModuleViolation(
                        module=module_name,
                        kind="forbidden_import_prefix",
                        detail=f"{forbidden_prefix}: {', '.join(sorted(set(hits)))}",
                    )
                )
        extra_effects = sorted(
            side_effect.value for side_effect in (observation.side_effects - contract.allowed_side_effects)
        )
        if extra_effects:
            violations.append(
                ModuleViolation(
                    module=module_name,
                    kind="side_effects",
                    detail=", ".join(extra_effects),
                )
            )
    return violations


def build_architecture_report() -> dict[str, object]:
    observations = observe_all_modules()
    violations = validate_contracts(observations=observations)
    rows = []
    for module_name, contract in sorted(MODULE_CONTRACTS.items()):
        observation = observations[module_name]
        module_violations = [item for item in violations if item.module == module_name]
        rows.append(
            {
                "module": module_name,
                "layer": contract.layer.value,
                "addon_deps": sorted(observation.addon_deps),
                "side_effects": sorted(side_effect.value for side_effect in observation.side_effects),
                "module_level_anki_imports": sorted(observation.module_level_anki_imports),
                "any_anki_imports": sorted(observation.any_anki_imports),
                "violations": [asdict(item) for item in module_violations],
            }
        )
    return {
        "modules": rows,
        "violations": [asdict(item) for item in violations],
    }


def format_architecture_report_json() -> str:
    return json.dumps(build_architecture_report(), indent=2, sort_keys=True)


def format_architecture_report_text() -> str:
    report = build_architecture_report()
    rows = report["modules"]
    assert isinstance(rows, list)
    lines = ["Architecture Report", ""]
    for row in rows:
        assert isinstance(row, dict)
        lines.append(f"{row['module']} [{row['layer']}]")
        lines.append(f"  addon deps: {', '.join(row['addon_deps']) or '-'}")
        lines.append(f"  side effects: {', '.join(row['side_effects']) or '-'}")
        module_level = ", ".join(row["module_level_anki_imports"]) or "-"
        any_level = ", ".join(row["any_anki_imports"]) or "-"
        lines.append(f"  anki imports: module-level={module_level}; anywhere={any_level}")
        row_violations = row["violations"]
        assert isinstance(row_violations, list)
        if row_violations:
            for item in row_violations:
                assert isinstance(item, dict)
                lines.append(f"  VIOLATION {item['kind']}: {item['detail']}")
        else:
            lines.append("  violations: none")
        lines.append("")
    violations = report["violations"]
    assert isinstance(violations, list)
    lines.append(f"Summary: {len(rows)} modules, {len(violations)} violations.")
    return "\n".join(lines)
