"""Python module catalog: layer assignments, import classification, and module metadata."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
PKG = "anki_audio_quick_editor"

ANKI_PREFIXES = ("aqt", "anki")

STDLIB: set[str] = {
    "__future__", "ast", "collections", "copy", "dataclasses", "enum",
    "functools", "hashlib", "io", "itertools", "json", "logging",
    "math", "os", "pathlib", "re", "shutil", "subprocess",
    "sys", "tempfile", "threading", "time", "typing", "uuid",
    "warnings", "weakref", "contextlib", "urllib", "zipfile", "struct",
}

LAYERS: dict[str, str] = {
    f"{PKG}": "entry_point",
}

IMPORT_SAFE = [
    "_version", "audio_artifacts", "audio_commands", "audio_commands_runtime",
    "audio_deps", "audio_external", "audio_formats", "audio_operation_params",
    "audio_operations", "audio_output_policy", "audio_pause_pipeline",
    "audio_pause_pipeline_detection", "audio_pause_pipeline_stage",
    "audio_pause_pipeline_steps", "audio_pitch_hum", "audio_pitch_hum_frames",
    "audio_pitch_hum_synthesis", "audio_processor", "audio_rendering",
    "audio_size_reduction", "audio_state", "audio_tools", "audio_types",
    "audio_noise_reduction", "audio_noise_reduction_bundled",
    "batch_operation_processing", "batch_operation_types",
    "batch_operations", "batch_operations_helpers",
    "config_migration", "config", "config.schema",
    "contracts_generated", "diagnostics", "diagnostics_runtime",
    "diagnostics_runtime_json", "diagnostics_runtime_storage",
    "editor_actions", "editor_button_visibility", "editor_media",
    "editor_session", "editor_ui", "editor_settings_actions",
    "error_codes", "errors", "external_links", "file_reveal",
    "file_sharing", "frontend_logs", "i18n", "media_paths",
    "persistent_history", "prosody_analyzer", "prosody_cache",
    "prosody_fallback", "prosody_praat", "prosody_settings",
    "prosody_svg", "prosody_types", "runtime_install", "runtime_manager",
    "runtime_manifest", "runtime_status", "settings_state",
    "sound_refs", "support", "support_reporting",
    "webview_bridge", "webview_shell",
]

UI_ADAPTERS = [
    "audio_recording", "browser_batch_runner", "browser_dialog",
    "browser_dialog_state", "browser_integration", "browser_report",
    "editor_analysis", "editor_bridge", "editor_callbacks",
    "editor_conversion", "editor_dependencies", "editor_frontend",
    "editor_frontend_callbacks", "editor_history", "editor_integration",
    "editor_persistent_undo", "editor_playback", "editor_playback_bounds",
    "editor_playback_request", "editor_processing", "editor_recording",
    "editor_recording_analysis", "editor_recording_frontend",
    "editor_recording_requests", "editor_region_delete",
    "editor_region_delete_request", "editor_region_delete_worker",
    "editor_reload_status", "editor_runtime", "editor_sharing",
    "editor_source_metadata", "editor_special_transforms",
    "editor_split_defaults", "editor_status", "editor_webview_injection",
    "reviewer_audio_targets", "reviewer_integration",
    "reviewer_template_filter", "reviewer_template_filter_integration",
    "runtime_installer_dialog",
]

SETTINGS_SHELL = ["settings"]
SETTINGS_BACKEND = [
    "settings.async_commands", "settings.async_operations",
    "settings.commands", "settings.initial_state",
]

for m in IMPORT_SAFE:
    LAYERS.setdefault(f"{PKG}.{m}", "import_safe_core")
for m in UI_ADAPTERS:
    LAYERS.setdefault(f"{PKG}.{m}", "ui_adapter")
for m in SETTINGS_SHELL:
    LAYERS.setdefault(f"{PKG}.{m}", "settings_shell")
for m in SETTINGS_BACKEND:
    LAYERS.setdefault(f"{PKG}.{m}", "settings_backend")


def _collect_imports(py_file: Path) -> dict[str, list[str]]:
    """Extract imports from a Python file grouped by category."""
    if not py_file.is_file():
        return {}
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return {}

    anki_imports: list[str] = []
    addon_imports: list[str] = []
    stdlib_imports: list[str] = []
    third_party: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in STDLIB:
                    stdlib_imports.append(alias.name)
                elif name.startswith(ANKI_PREFIXES):
                    anki_imports.append(alias.name)
                elif name == PKG.split(".", maxsplit=1)[0] or name == PKG:
                    addon_imports.append(alias.name)
                else:
                    third_party.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                name = node.module.split(".")[0]
                full = node.module + (f".{node.names[0].name}" if node.names and node.names[0].name != "*" else "")
                if name in STDLIB:
                    stdlib_imports.append(node.module)
                elif name.startswith(ANKI_PREFIXES) or (node.level > 0):
                    anki_imports.append(full)
                elif name == PKG.split(".", maxsplit=1)[0] or name == PKG:
                    addon_imports.append(full)
                elif node.level > 0:
                    stdlib_imports.append(node.module)  # relative internal
                else:
                    third_party.append(node.module)

    return {
        "anki": sorted(set(anki_imports)),
        "addon": sorted(set(addon_imports)),
        "stdlib": sorted(set(stdlib_imports)),
        "third_party": sorted(set(third_party)),
    }


def _module_name(py_file: Path) -> str:
    """Convert a Python file path to its dotted module name."""
    rel = py_file.relative_to(ADDON.parent)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def _module_summary(py_file: Path) -> str:
    """Extract first docstring sentence or derive purpose from filename."""
    if not py_file.is_file():
        return ""
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""

    if (isinstance(tree, ast.Module) and tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        doc = tree.body[0].value.value.strip()
        first_line = doc.split("\n")[0].rstrip(".")
        return first_line

    return f"Module: {py_file.stem}"


def _build_python_catalog() -> list[dict]:
    modules = []
    for py_file in sorted(ADDON.rglob("*.py")):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        name = _module_name(py_file)
        if "user_files" in name or "vendor" in name or "bin" in name:
            continue
        if "templates" in name:
            continue

        imports = _collect_imports(py_file)
        modules.append({
            "module": name,
            "file": str(py_file.relative_to(ROOT)),
            "layer": LAYERS.get(name, "unclassified"),
            "summary": _module_summary(py_file),
            "imports": imports,
        })
    return modules
