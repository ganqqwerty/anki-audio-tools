"""Rule 21: broad exception handlers require a documented allowlist entry."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .inspection import ADDON_DIR


@dataclass(frozen=True)
class BroadExceptionAllowance:
    """One approved broad exception boundary."""

    module: str
    qualname: str
    count: int
    reason: str


BROAD_EXCEPTION_ALLOWLIST: tuple[BroadExceptionAllowance, ...] = (
    BroadExceptionAllowance(
        "__init__",
        "_with_hook_boundary._wrapped",
        1,
        "Startup hook boundary records diagnostics before re-raising for Anki startup visibility.",
    ),
    BroadExceptionAllowance(
        "audio_pause_pipeline",
        "_render_deep_filter_pause_speedup_audio",
        1,
        "External DeepFilterNet rendering boundary records support context before surfacing an add-on error.",
    ),
    BroadExceptionAllowance(
        "audio_noise_reduction_bundled",
        "render_rnnoise_audio",
        1,
        "External RNNoise runtime boundary records support context before surfacing an add-on error.",
    ),
    BroadExceptionAllowance(
        "audio_noise_reduction_bundled",
        "render_dpdfnet_audio",
        1,
        "External DPDFNet runtime boundary records support context before surfacing an add-on error.",
    ),
    BroadExceptionAllowance(
        "audio_noise_reduction_bundled",
        "render_voice_only_audio",
        1,
        "External Sherpa Spleeter boundary records model and command context before surfacing an add-on error.",
    ),
    BroadExceptionAllowance(
        "batch_operations",
        "_process_graph_operation",
        1,
        "Per-note batch isolation converts graph generation failures into a failed row.",
    ),
    BroadExceptionAllowance(
        "batch_operations",
        "_process_transform_operation",
        1,
        "Per-note batch isolation converts audio transformation failures into a failed row.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_run_batch_in_background.done",
        1,
        "Anki background-task callback boundary reports unexpected task failures to the user.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_browser_hook_boundary._wrapped",
        1,
        "Browser hook boundary records diagnostics before re-raising hook failures.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_process_note",
        1,
        "Per-note browser batch boundary prevents one unexpected note failure from stopping the batch.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_apply_result",
        1,
        "Anki collection write boundary preserves batch progress when one result cannot be applied.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_publish_collection_changes",
        1,
        "Best-effort browser refresh path must not fail an already-completed batch.",
    ),
    BroadExceptionAllowance(
        "diagnostics",
        "build_deep_filter_health",
        1,
        "Diagnostic external-tool probe reports availability instead of raising.",
    ),
    BroadExceptionAllowance(
        "diagnostics",
        "build_rnnoise_health",
        1,
        "Diagnostic external-tool probe reports availability instead of raising.",
    ),
    BroadExceptionAllowance(
        "diagnostics",
        "build_dpdfnet_health",
        1,
        "Diagnostic external-tool probe reports availability instead of raising.",
    ),
    BroadExceptionAllowance(
        "diagnostics",
        "build_spleeter_health",
        1,
        "Diagnostic source-separation probe reports Sherpa Spleeter availability instead of raising.",
    ),
    BroadExceptionAllowance(
        "diagnostics_runtime",
        "flush_logging",
        1,
        "Diagnostics must never fail while flushing a broken logging handler after an error.",
    ),
    BroadExceptionAllowance(
        "editor_bridge",
        "handle_bridge_command",
        1,
        "Anki editor bridge callback boundary keeps unexpected command failures user-visible.",
    ),
    BroadExceptionAllowance(
        "editor_processing",
        "_run_standard_render_worker",
        1,
        "Background render worker boundary reports failed audio generation on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_special_transform_worker",
        "run_special_transform_worker",
        1,
        "Background special-transform worker boundary records support context and reports failure.",
    ),
    BroadExceptionAllowance(
        "editor_region_delete_worker",
        "run_region_delete_worker",
        1,
        "Background region-delete worker boundary logs request context and reports failure on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_region_delete",
        "replace_current_field_after_region_delete",
        1,
        "Main-thread field replacement boundary keeps failed region deletes non-mutating and user-visible.",
    ),
    BroadExceptionAllowance(
        "editor_sharing",
        "share_current_audio_file._run",
        1,
        "Background upload worker boundary reports Catbox/Litterbox failures on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_playback",
        "stop_audio_playback",
        1,
        "Best-effort playback backend integration cannot assume a stable Anki audio API surface.",
    ),
    BroadExceptionAllowance(
        "editor_playback",
        "toggle_native_pause_resume",
        1,
        "Best-effort playback backend integration reports pause/resume unavailability as a warning.",
    ),
    BroadExceptionAllowance(
        "editor_playback",
        "start_playback_from_cursor._run",
        1,
        "Background playback-segment worker boundary reports failures on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_analysis",
        "start_field_analysis_async._run",
        1,
        "Background prosody analysis worker boundary reports analyzer failures on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_recording",
        "analyze_learner_recording_async._run",
        1,
        "Background learner-recording analysis worker reports analyzer failures on the main thread.",
    ),
    BroadExceptionAllowance(
        "file_reveal",
        "_open_parent_folder",
        1,
        "Best-effort OS file reveal bridge converts platform failures into an add-on error.",
    ),
    BroadExceptionAllowance(
        "file_reveal",
        "open_external_url",
        1,
        "Best-effort Qt browser bridge converts platform failures into an add-on error.",
    ),
    BroadExceptionAllowance(
        "prosody_analyzer",
        "analyze_prosody",
        1,
        "Optional Parselmouth backend boundary falls back to the bundled analyzer when unavailable.",
    ),
    BroadExceptionAllowance(
        "runtime_manager",
        "_download_extract_promote",
        1,
        "Runtime install promotion cleans rejected download/extract artifacts before re-raising.",
    ),
    BroadExceptionAllowance(
        "runtime_manager",
        "ensure_runtime",
        1,
        "Runtime install boundary converts download, disk, and archive failures into a diagnostics status.",
    ),
    BroadExceptionAllowance(
        "settings.commands",
        "_handle_async_cmd._run",
        1,
        "Settings async worker boundary sends webview error callbacks instead of leaking thread exceptions.",
    ),
)


class BroadExceptionVisitor(ast.NodeVisitor):
    """Collect broad exception handlers by module-qualified function name."""

    def __init__(self, module: str) -> None:
        self.module = module
        self._stack: list[str] = []
        self.handlers: Counter[tuple[str, str]] = Counter()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if _is_broad_exception_type(node.type):
            qualname = ".".join(self._stack) or "<module>"
            self.handlers[(self.module, qualname)] += 1
        self.generic_visit(node)


def test_broad_exception_handlers_are_allowlisted_with_reasons() -> None:
    observed = _collect_broad_exception_handlers()
    allowed = {(item.module, item.qualname): item for item in BROAD_EXCEPTION_ALLOWLIST}
    violations: list[str] = []

    for key, count in sorted(observed.items()):
        allowance = allowed.get(key)
        if allowance is None:
            violations.append(f"{key[0]}.{key[1]} has {count} unallowlisted broad exception handler(s)")
            continue
        if count != allowance.count:
            violations.append(
                f"{key[0]}.{key[1]} has {count} broad exception handler(s), expected {allowance.count}"
            )
        if not allowance.reason.strip():
            violations.append(f"{key[0]}.{key[1]} allowlist entry must include a reason")

    for key, allowance in sorted(allowed.items()):
        if key not in observed:
            violations.append(f"{allowance.module}.{allowance.qualname} is allowlisted but no handler was found")

    assert violations == [], "\n".join(violations)


def _collect_broad_exception_handlers() -> Counter[tuple[str, str]]:
    observed: Counter[tuple[str, str]] = Counter()
    for path in sorted(ADDON_DIR.rglob("*.py")):
        if "vendor" in path.parts:
            continue
        module = _module_name(path)
        visitor = BroadExceptionVisitor(module)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        observed.update(visitor.handlers)
    return observed


def _is_broad_exception_type(node: ast.expr | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Attribute):
        return node.attr in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(_is_broad_exception_type(item) for item in node.elts)
    return False


def _module_name(path: Path) -> str:
    relative = path.relative_to(ADDON_DIR).with_suffix("")
    parts = relative.parts
    if parts == ("__init__",):
        return "__init__"
    if parts[-1] == "__init__":
        return ".".join(parts[:-1])
    return ".".join(parts)
