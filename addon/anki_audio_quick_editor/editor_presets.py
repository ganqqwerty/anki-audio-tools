"""Editor-side processing preset orchestration."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_processing_preset_runner import (
    ProcessingPresetRunnerAdapters,
    ProcessingPresetRunResult,
    run_processing_preset,
)
from .audio_processing_presets import (
    AudioProcessingPreset,
    preset_by_id,
    presets_from_raw,
)
from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_actions import EditorCommandPayload
from .editor_processing_shared import cancel_graph_analysis_for_processing
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    is_current_processing_guard,
)
from .error_codes import AQE_AUDIO_PROCESSING_FAILED, coded_error
from .i18n import t
from .permission_guidance import message_with_permission_guidance

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps

logger = logging.getLogger(__name__)


def run_processing_preset_async(
    editor: Any,
    command: EditorCommandPayload,
    deps: ProcessingDeps,
) -> None:
    """Run one saved processing preset against the active editor field."""
    existing = deps.sessions.get(editor)
    if existing and existing.processing.active:
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    if existing and existing.playback.preparing:
        deps.stop_session_playback(existing)
    raw_config = deps.config(editor)
    try:
        preset = preset_by_id(
            presets_from_raw(raw_config.get("audio_processing_presets")),
            command.preset_id or "",
        )
    except ValueError as exc:
        deps.eval_status(editor, coded_error(AQE_AUDIO_PROCESSING_FAILED, str(exc)), kind="error")
        return

    session, current_path = deps.current_media_path(editor)
    cancel_graph_analysis_for_processing(editor, session, deps)
    deps.stop_session_playback(session)
    session.post_edit_playback.generation += 1
    session.processing.next_status_summary = preset.name
    session.processing.active = True
    field_index = session.field_index if session.field_index is not None else getattr(editor, "currentField", 0)
    guard = begin_processing_guard(
        session,
        field_index=int(field_index),
        source_filename=current_path.name,
    )
    session.playback.active = False
    session.playback.paused = False
    deps.set_busy(editor, True, t("editor.status.running_preset", {"preset": preset.name}))
    deps.eval_playback_state(editor, guard.field_index, "stopped", session.cursor_ms)
    operation_id = new_operation_id("preset")
    record_breadcrumb(
        "editor.preset.started",
        source="editor",
        operation="editor.preset",
        operation_id=operation_id,
        context={"preset_id": preset.id, "preset_name": preset.name, "source_filename": current_path.name},
        flush=True,
    )

    def _run() -> None:
        _run_preset_worker(editor, session, current_path, preset, guard, operation_id, raw_config, deps)

    deps.threading.Thread(target=_run, daemon=True).start()


def _run_preset_worker(
    editor: Any,
    session: EditorSession,
    current_path: Path,
    preset: AudioProcessingPreset,
    guard: EditorProcessingGuard,
    operation_id: str,
    raw_config: dict[str, Any],
    deps: ProcessingDeps,
) -> None:
    result: ProcessingPresetRunResult | None = None
    try:
        config = AudioProcessingConfig.from_config(raw_config)
        result = run_processing_preset(
            preset,
            source_path=current_path,
            source_filename=current_path.name,
            config=config,
            adapters=_editor_preset_runner_adapters(deps),
            artifact_root=deps.artifact_root(editor),
            render_graph=False,
        )
        _schedule_preset_finish(editor, session, preset, result, guard, deps)
    except Exception as exc:
        _handle_preset_worker_failure(
            editor,
            session,
            current_path,
            preset,
            result,
            guard,
            operation_id,
            exc,
            deps,
        )


def _schedule_preset_finish(
    editor: Any,
    session: EditorSession,
    preset: AudioProcessingPreset,
    result: ProcessingPresetRunResult,
    guard: EditorProcessingGuard,
    deps: ProcessingDeps,
) -> None:
    if not is_current_processing_guard(session, guard):
        _cleanup_result(result)
        deps.main(editor, lambda: _discard_stale_preset(editor, guard, deps))
        return

    def _finish() -> None:
        try:
            if result.final_audio_path is not None and result.final_audio_name is not None:
                deps.replace_current_field_after_noise_removal(
                    editor,
                    result.final_audio_name,
                    guard=guard,
                    output_path=result.final_audio_path,
                )
                if preset.graph.enabled:
                    deps.request_graph_redraw(editor, None, _graph_settings_payload(preset))
                return
            if preset.graph.enabled:
                session.processing.active = False
                session.processing.next_status_summary = ""
                deps.set_busy(editor, False)
                deps.analyze_current_async(editor, graph_settings=_graph_settings_payload(preset))
                return
            session.processing.active = False
            session.processing.next_status_summary = ""
            deps.set_busy(editor, False)
            deps.eval_status(editor, t("editor.status.preset_no_changes"))
        finally:
            _cleanup_result(result)

    deps.main(editor, _finish)


def _handle_preset_worker_failure(
    editor: Any,
    session: EditorSession,
    current_path: Path,
    preset: AudioProcessingPreset,
    result: ProcessingPresetRunResult | None,
    guard: EditorProcessingGuard,
    operation_id: str,
    exc: Exception,
    deps: ProcessingDeps,
) -> None:
    _cleanup_result(result)
    message = message_with_permission_guidance(str(exc), exc)
    capture_exception(
        "editor.worker.preset",
        exc,
        operation="editor.preset",
        operation_id=operation_id,
        user_message=message,
        context={"source_path": str(current_path), "preset_id": preset.id, "preset_name": preset.name},
        log=logger,
    )
    if not is_current_processing_guard(session, guard):
        deps.main(editor, lambda: _discard_stale_preset(editor, guard, deps))
        return
    deps.main(editor, lambda: deps.render_failed(editor, message, guard=guard))


def _editor_preset_runner_adapters(deps: ProcessingDeps) -> ProcessingPresetRunnerAdapters:
    return ProcessingPresetRunnerAdapters(
        make_audio_output_filename=deps.make_output_filename,
        make_graph_output_filename=lambda filename: filename,
        temp_output_path=deps.temp_final_path,
        render_audio=_render_preset_audio(deps),
        render_converted_audio=_render_preset_converted_audio(deps),
        render_size_reduced_audio=_render_preset_size_reduced_audio(deps),
        render_denoise_audio=_render_preset_denoise_audio(deps),
        analyze_prosody=deps.analyze_prosody_cached,
        render_graph_svg=lambda _track: b"",
    )


def _render_preset_audio(
    deps: ProcessingDeps,
) -> Callable[[Path, Any, AudioProcessingConfig, Path, Path | None], None]:
    def _render(
        source_path: Path,
        state: Any,
        config: AudioProcessingConfig,
        output_path: Path,
        artifact_root: Path | None,
    ) -> None:
        deps.render_audio(
            source_path,
            state,
            config,
            output_path=output_path,
            artifact_root=artifact_root,
        )

    return _render


def _render_preset_converted_audio(
    deps: ProcessingDeps,
) -> Callable[[Path, AudioProcessingConfig, str, Path], None]:
    def _render(
        source_path: Path,
        config: AudioProcessingConfig,
        target_format: str,
        output_path: Path,
    ) -> None:
        deps.render_converted_audio(source_path, config, target_format, output_path=output_path)

    return _render


def _render_preset_size_reduced_audio(
    deps: ProcessingDeps,
) -> Callable[[Path, AudioProcessingConfig, Path], None]:
    def _render(source_path: Path, config: AudioProcessingConfig, output_path: Path) -> None:
        deps.render_size_reduced_audio(
            source_path,
            config,
            output_path=output_path,
            mode=config.size_reduction_mode,
        )

    return _render


def _render_preset_denoise_audio(
    deps: ProcessingDeps,
) -> Callable[[Path, AudioProcessingConfig, Path], None]:
    def _render(source_path: Path, config: AudioProcessingConfig, output_path: Path) -> None:
        renderers = {
            "standard": deps.render_noise_reduced_audio,
            "rnnoise": deps.render_rnnoise_audio,
            "dpdfnet": deps.render_dpdfnet_audio,
            "voice_only": deps.render_voice_only_audio,
        }
        renderers.get(config.denoise_algorithm, deps.render_noise_reduced_audio)(
            source_path,
            config,
            output_path=output_path,
        )

    return _render


def _graph_settings_payload(preset: AudioProcessingPreset) -> dict[str, object]:
    parameters = preset.graph.parameters
    return {
        "connectShortDropoutsMs": parameters.graph_connect_short_dropouts_ms,
        "recordingCondition": parameters.graph_recording_condition,
        "smoothness": parameters.graph_smoothness,
        "voiceLock": parameters.graph_voice_lock,
        "voiceRange": parameters.graph_voice_range,
    }


def _cleanup_result(result: ProcessingPresetRunResult | None) -> None:
    if result is not None and result.final_audio_path is not None:
        shutil.rmtree(result.final_audio_path.parent, ignore_errors=True)


def _discard_stale_preset(editor: Any, guard: EditorProcessingGuard, deps: ProcessingDeps) -> None:
    if clear_processing_for_stale_guard(deps.sessions.get(editor), guard):
        deps.set_busy(editor, False)
