"""Broad exception handler allowlist for Rule 21 enforcement."""

from __future__ import annotations

from dataclasses import dataclass


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
        "render_pause_removal_pipeline_audio",
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
        "batch_operation_processing",
        "process_graph_operation",
        1,
        "Per-note batch isolation converts graph generation failures into a failed row.",
    ),
    BroadExceptionAllowance(
        "batch_operation_processing",
        "process_transform_operation",
        1,
        "Per-note batch isolation converts audio transformation failures into a failed row.",
    ),
    BroadExceptionAllowance(
        "batch_processing_presets",
        "process_preset_operation",
        1,
        "Per-note batch preset isolation converts staged multi-output failures into a failed row.",
    ),
    BroadExceptionAllowance(
        "browser_batch_runner",
        "run_batch_in_background.done",
        1,
        "Anki background-task callback boundary reports unexpected task failures to the user.",
    ),
    BroadExceptionAllowance(
        "browser_audio_export_runner",
        "run_audio_export_in_background.done",
        1,
        "Anki background-task callback boundary reports unexpected export failures to the user.",
    ),
    BroadExceptionAllowance(
        "browser_integration",
        "_browser_hook_boundary._wrapped",
        1,
        "Browser hook boundary records diagnostics before re-raising hook failures.",
    ),
    BroadExceptionAllowance(
        "browser_batch_runner",
        "process_note",
        1,
        "Per-note browser batch boundary prevents one unexpected note failure from stopping the batch.",
    ),
    BroadExceptionAllowance(
        "browser_result_application",
        "_apply_written_result",
        1,
        "Anki collection write boundary preserves batch progress when one result cannot be applied.",
    ),
    BroadExceptionAllowance(
        "browser_batch_runner",
        "publish_collection_changes",
        1,
        "Best-effort browser refresh path must not fail an already-completed batch.",
    ),
    BroadExceptionAllowance(
        "trigger_integration",
        "_schedule",
        1,
        "Anki trigger hook boundary records diagnostics instead of letting hook failures escape.",
    ),
    BroadExceptionAllowance(
        "trigger_scheduler",
        "schedule_trigger_event",
        1,
        "Trigger config parsing boundary disables scheduling on malformed config while recording diagnostics.",
    ),
    BroadExceptionAllowance(
        "trigger_scheduler",
        "_dispatch_selected_jobs",
        1,
        "Trigger dispatch boundary marks synchronously rejected task dispatches as failed state.",
    ),
    BroadExceptionAllowance(
        "trigger_executor",
        "run_trigger_job",
        1,
        "Per-note trigger job boundary converts unexpected processing or write failures into failed trigger state.",
    ),
    BroadExceptionAllowance(
        "trigger_result_application",
        "publish_trigger_changes",
        1,
        "Best-effort Anki refresh path must not fail an already-completed trigger update.",
    ),
    BroadExceptionAllowance(
        "trigger_dispatch",
        "dispatch_trigger_job.done",
        1,
        "Anki background-task callback boundary records unexpected worker failures and marks trigger state failed.",
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
        "diagnostics",
        "build_silero_vad_health",
        1,
        "Diagnostic Silero VAD probe reports availability instead of raising.",
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
        "editor_processing",
        "replace_current_field_after_render",
        1,
        "Persistent undo journal writes are best-effort and must not block a completed render.",
    ),
    BroadExceptionAllowance(
        "editor_webview_injection",
        "_can_persistent_undo",
        1,
        "Initial editor injection must not fail note loading when the persistent history check fails.",
    ),
    BroadExceptionAllowance(
        "editor_webview_injection",
        "_latest_persistent_undo_item",
        1,
        "Initial editor injection must not fail note loading when persistent history item lookup fails.",
    ),
    BroadExceptionAllowance(
        "editor_webview_injection",
        "_persistent_undo_items",
        1,
        "Initial editor injection must not fail note loading when persistent history chain lookup fails.",
    ),
    BroadExceptionAllowance(
        "editor_special_transform_worker",
        "run_special_transform_worker",
        1,
        "Background special-transform worker boundary records support context and reports failure.",
    ),
    BroadExceptionAllowance(
        "editor_presets",
        "_run_preset_worker",
        1,
        "Background preset worker boundary reports staged multi-step preset failures without mutating the note.",
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
        2,
        "Main-thread field replacement boundary keeps failed region deletes non-mutating and persistent history best-effort.",
    ),
    BroadExceptionAllowance(
        "editor_sharing",
        "share_media_path._run",
        1,
        "Background upload worker boundary reports Catbox/Litterbox failures on the main thread.",
    ),
    BroadExceptionAllowance(
        "editor_source_metadata",
        "_start_probe._run",
        1,
        "Lazy editor source metadata worker sends non-blocking UI error callbacks instead of leaking thread exceptions.",
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
        "runtime_install_io",
        "download_extract_promote",
        1,
        "Runtime install promotion cleans rejected download/extract artifacts before re-raising.",
    ),
    BroadExceptionAllowance(
        "settings.async_commands",
        "handle_async_settings_command._run",
        1,
        "Settings async worker boundary sends webview error callbacks instead of leaking thread exceptions.",
    ),
)
