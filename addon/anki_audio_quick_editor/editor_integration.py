"""Thin Anki editor integration for inline audio editing."""

from __future__ import annotations

import json
import logging
import shutil
import threading
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .audio_processor import (
    AudioProcessingResult,
    format_ffmpeg_command,
    make_output_filename,
    render_audio,
    render_mp_senet_audio,
    render_noise_reduced_audio,
    render_playback_segment,
    temp_final_path,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .contracts_generated import FrontendLogPayload, ProsodyPayload
from .editor_actions import (
    BRIDGE_COMMANDS,
    CMD_DENOISE_STANDARD,
    CMD_MP_SENET,
    CMD_REDO,
    CMD_SETTINGS,
    apply_processing_command,
)
from .editor_ui import injection_script
from .errors import AudioProcessingError, AudioQuickEditorError, MissingMediaError
from .file_reveal import reveal_file
from .prosody_cache import (
    analyze_prosody_cached as _analyze_prosody_cached,
)
from .prosody_types import ProsodyTrack, clamp_cursor_ms
from .sound_refs import (
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)
from .support import (
    MP_SENET_SUPPORT_HINT,
    format_mp_senet_support_log_block,
    latest_mp_senet_support_incident,
    record_latest_mp_senet_support_incident,
)

logger = logging.getLogger(__name__)
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)

CURRENT_FIELD_AUDIO_MISSING = "No [sound:...] reference found in the current field."
REFERENCED_AUDIO_MISSING = "The referenced audio file was not found in Anki's media folder."
STILL_PROCESSING_MESSAGE = "Still processing. Please wait."
SettingsOpener = Callable[[Callable[[], None] | None], None]
_SETTINGS_OPENER: SettingsOpener | None = None

@dataclass(frozen=True)
class UndoEntry:
    """A field reference and edit state that can be restored by Undo."""

    state: AudioEditState
    filename: str


@dataclass
class UndoHistory:
    """Undo stack for generated audio references."""

    entries: list[UndoEntry] = field(default_factory=list)

    def push(self, state: AudioEditState | None, filename: str | None) -> None:
        """Remember the current generated/reference state before rendering."""
        if state is not None and filename:
            self.entries.append(UndoEntry(state, filename))

    def pop(self) -> UndoEntry | None:
        """Return the previous state to restore, if one exists."""
        return self.entries.pop() if self.entries else None

    def clear(self) -> None:
        """Drop history when switching fields or source media."""
        self.entries.clear()


@dataclass(frozen=True)
class EditSessionSnapshot:
    """Edit state to restore after read-only cross-field work."""

    state: AudioEditState | None
    field_index: int | None
    current_filename: str | None
    undo_entries: tuple[UndoEntry, ...]
    redo_entries: tuple[UndoEntry, ...]
    source_mtime_ns: int | None
    cursor_ms: int


@dataclass
class EditorSession:
    """Mutable edit session for a single editor instance."""

    note_id: int | None = None
    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    undo_history: UndoHistory = field(default_factory=UndoHistory)
    redo_history: UndoHistory = field(default_factory=UndoHistory)
    processing: bool = False
    analysis_busy: bool = False
    source_mtime_ns: int | None = None
    cursor_ms: int = 0
    analysis_generation: int = 0
    graph_active_fields: set[int] = field(default_factory=set)
    visualized_filename: str | None = None
    visualized_duration_ms: int | None = None
    playback_active: bool = False
    playback_paused: bool = False
    playback_preparing: bool = False
    playback_generation: int = 0
    temp_playback_path: Path | None = None


_SESSIONS: "weakref.WeakKeyDictionary[Any, EditorSession]" = weakref.WeakKeyDictionary()


def register_editor_hooks(
    gui_hooks: Any,
    *,
    settings_opener: SettingsOpener | None = None,
) -> None:
    """Register all editor hooks used by the add-on."""
    global _SETTINGS_OPENER
    _SETTINGS_OPENER = settings_opener
    gui_hooks.editor_did_init.append(_on_editor_did_init)
    gui_hooks.editor_will_load_note.append(_on_editor_will_load_note)


def _on_editor_did_init(editor: Any) -> None:
    for command in BRIDGE_COMMANDS:
        editor._links[command] = lambda current_editor, cmd=command: _handle_bridge_command(
            current_editor, cmd
        )


def _on_editor_will_load_note(js: str, note: Any, editor: Any) -> str:
    _reset_editor_session_for_note_load(editor, getattr(note, "id", None))
    _SESSIONS.setdefault(editor, EditorSession()).note_id = getattr(note, "id", None)
    config = _config(editor)
    audio_field_sources = _audio_field_sources(note)
    script = injection_script(
        list(audio_field_sources),
        audio_field_sources=audio_field_sources,
        repeat_playback_by_default=bool(config.get("repeat_playback_by_default", False)),
        show_graph_by_default=bool(config.get("show_graph_by_default", False)),
    )
    return f"{js}\n{script}"


def _audio_field_indices(note: Any) -> list[int]:
    """Return field indices containing an MVP-supported sound reference."""
    return list(_audio_field_sources(note))


def _audio_field_sources(note: Any) -> dict[int, str]:
    """Return field indices and first supported sound filename for the note."""
    sources: dict[int, str] = {}
    for index, field_html in enumerate(getattr(note, "fields", [])):
        try:
            selection = select_first_sound_reference(field_html)
        except AudioQuickEditorError:
            continue
        if selection.selected is not None:
            sources[index] = safe_media_basename(selection.selected.filename)
    return sources


def _reset_editor_session_for_note_load(editor: Any, note_id: int | None = None) -> None:
    session = _SESSIONS.get(editor)
    if session is None:
        return
    if session.note_id == note_id:
        return
    session.analysis_generation += 1
    _stop_session_playback(session)
    session.note_id = note_id
    session.state = None
    session.field_index = None
    session.current_filename = None
    session.undo_history.clear()
    session.redo_history.clear()
    session.processing = False
    session.analysis_busy = False
    session.source_mtime_ns = None
    session.cursor_ms = 0
    session.graph_active_fields.clear()
    session.visualized_filename = None
    session.visualized_duration_ms = None
    session.playback_active = False
    session.playback_paused = False
    session.playback_preparing = False


def _handle_bridge_command(editor: Any, command: str) -> None:
    try:
        if _handle_non_processing_command(editor, command):
            return
        _update_state_and_render(editor, command)
    except AudioQuickEditorError as exc:
        _set_busy(editor, False)
        _eval_status(editor, str(exc), kind="error")
    except Exception as exc:  # pragma: no cover - defensive boundary for Anki bridge
        logger.exception("audio quick editor command failed: %s", command)
        _set_busy(editor, False)
        _eval_status(editor, f"Audio processing failed. The note was not changed. ({exc})", kind="error")


def _handle_non_processing_command(editor: Any, command: str) -> bool:
    if command == "aqe:scan":
        _eval_status(editor, "")
        editor.web.eval("window.__aqeScan && window.__aqeScan()")
        return True
    handlers = {
        "aqe:analyze": _analyze_current_async,
        "aqe:set-cursor": _set_cursor_from_web,
        "aqe:play": _play,
        "aqe:frontend-log": _handle_editor_frontend_log,
        "aqe:show-file": _show_current_audio_file,
        "aqe:play-ended": _play_ended,
        "aqe:undo": _undo,
        CMD_REDO: _redo,
        CMD_SETTINGS: _open_settings_from_editor,
        CMD_DENOISE_STANDARD: _denoise_standard_async,
        CMD_MP_SENET: _mp_senet_async,
    }
    handler = handlers.get(command)
    if handler is None:
        return False
    handler(editor)
    return True


def _handle_editor_frontend_log(editor: Any) -> None:
    _eval_with_callback(
        editor,
        "window.__aqePopFrontendLog ? window.__aqePopFrontendLog() : null",
        _log_editor_frontend_payload,
    )


def _log_editor_frontend_payload(raw_payload: Any) -> None:
    if raw_payload is None:
        return
    try:
        payload = FrontendLogPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        logger.warning("editor frontend_log: invalid payload")
        return

    rendered = f"editor frontend: {payload.message}"
    if payload.context is not None:
        rendered = f"{rendered} | {payload.context!r}"
    level = payload.level.value
    if level == "debug":
        logger.debug(rendered)
    elif level == "warn":
        logger.warning(rendered)
    elif level == "error":
        logger.error(rendered)
    else:
        logger.info(rendered)


def _update_state_and_render(editor: Any, command: str) -> None:
    existing = _SESSIONS.get(editor)
    if existing and _is_busy(existing):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    session, source_path = _session_and_source(editor)
    config = AudioProcessingConfig.from_config(_config(editor))
    state = session.state or AudioEditState(source_file=source_path.name)
    updated_state = apply_processing_command(command, state, config)
    if updated_state is None:
        _set_busy(editor, False)
        return
    _render_and_replace_async(editor, session, source_path, updated_state, config)


def _render_and_replace_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
) -> None:
    _stop_session_playback(session)
    session.processing = True
    session.playback_active = False
    session.playback_paused = False
    _set_busy(editor, True, "Processing...")
    _eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        try:
            desired_name = make_output_filename(source_path.name)
            output_path = temp_final_path(desired_name)

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = format_ffmpeg_command(command)
                message = "Processing with ffmpeg"
                command_text = ""
                if config.show_ffmpeg_commands:
                    message = f"{message}: {rendered}"
                    command_text = rendered
                _main(
                    editor,
                    lambda: _set_busy(editor, True, message, command_text),
                )

            render_audio(
                source_path,
                updated_state,
                config,
                output_path=output_path,
                on_command=_show_command,
                artifact_root=_artifact_root(editor),
            )
            with output_path.open("rb") as file:
                saved_name = editor.mw.col.media.write_data(desired_name, file.read())
            _main(editor, lambda: _replace_current_field_after_render(editor, updated_state, saved_name))
            shutil.rmtree(output_path.parent, ignore_errors=True)
        except Exception as exc:
            message = str(exc)
            _main(editor, lambda: _render_failed(editor, message))

    threading.Thread(target=_run, daemon=True).start()


def _replace_current_field_after_render(
    editor: Any,
    updated_state: AudioEditState,
    saved_name: str,
) -> None:
    field_index = _current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    _dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    session = _SESSIONS.get(editor)
    should_redraw_graph = False
    if session:
        session.undo_history.push(session.state, session.current_filename)
        session.redo_history.clear()
        session.state = updated_state
        session.current_filename = saved_name
        session.field_index = field_index
        session.processing = False
        session.cursor_ms = 0
        session.playback_active = False
        session.playback_paused = False
        should_redraw_graph = (
            field_index in session.graph_active_fields
            or session.visualized_filename is not None
        )
        if should_redraw_graph:
            session.visualized_filename = None
            session.visualized_duration_ms = None
    editor.loadNote(focusTo=field_index)
    _eval_status(editor, f"Updated field to {saved_name}")
    _eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        _request_graph_redraw(editor)
    else:
        _set_busy(editor, False)


def _render_failed(editor: Any, message: str) -> None:
    session = _SESSIONS.get(editor)
    if session:
        session.processing = False
        session.playback_active = False
        session.playback_paused = False
    _set_busy(editor, False)
    _eval_status(editor, message, kind="error")


def _denoise_standard_async(editor: Any) -> None:
    _run_special_audio_transform_async(
        editor,
        label="Denoising with Standard",
        failure_log_label="standard denoise failed",
        renderer=render_noise_reduced_audio,
    )


def _mp_senet_async(editor: Any) -> None:
    _run_special_audio_transform_async(
        editor,
        label="Denoising with MP-SENet",
        failure_log_label="mp-senet denoise failed",
        renderer=render_mp_senet_audio,
        support_hint=MP_SENET_SUPPORT_HINT,
        failure_context_recorder=_record_mp_senet_failure_context,
    )


def _run_special_audio_transform_async(
    editor: Any,
    *,
    label: str,
    failure_log_label: str,
    renderer: Callable[..., AudioProcessingResult],
    support_hint: str = "",
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None = None,
) -> None:
    existing = _SESSIONS.get(editor)
    if existing and _is_busy(existing):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    session, current_path = _current_media_path(editor)
    config = AudioProcessingConfig.from_config(_config(editor))
    _stop_session_playback(session)
    session.processing = True
    session.playback_active = False
    session.playback_paused = False
    _set_busy(editor, True, f"{label}...")
    _eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        output_path: Path | None = None
        try:
            desired_name = make_output_filename(current_path.name)
            output_path = temp_final_path(desired_name)

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = format_ffmpeg_command(command)
                message = label
                command_text = ""
                if config.show_ffmpeg_commands:
                    message = f"{message}: {rendered}"
                    command_text = rendered
                _main(editor, lambda: _set_busy(editor, True, message, command_text))

            renderer(
                current_path,
                config,
                output_path=output_path,
                on_command=_show_command,
            )
            with output_path.open("rb") as file:
                saved_name = editor.mw.col.media.write_data(desired_name, file.read())
            _main(editor, lambda: _replace_current_field_after_noise_removal(editor, saved_name))
        except Exception as exc:
            message = str(exc)
            rendered_message = message
            if failure_context_recorder is not None:
                failure_context_recorder(current_path, config, exc)
            _log_special_transform_failure(failure_log_label, message)
            if support_hint:
                rendered_message = f"{message} {support_hint}"
            _main(editor, lambda: _render_failed(editor, rendered_message))
        finally:
            if output_path is not None:
                shutil.rmtree(output_path.parent, ignore_errors=True)

    threading.Thread(target=_run, daemon=True).start()


def _replace_current_field_after_noise_removal(editor: Any, saved_name: str) -> None:
    field_index = _current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    _dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    session = _SESSIONS.get(editor)
    should_redraw_graph = False
    if session:
        session.undo_history.push(session.state, session.current_filename)
        session.redo_history.clear()
        session.state = AudioEditState(source_file=saved_name)
        session.current_filename = saved_name
        session.field_index = field_index
        saved_path = Path(editor.mw.col.media.dir()) / safe_media_basename(saved_name)
        session.source_mtime_ns = saved_path.stat().st_mtime_ns if saved_path.is_file() else None
        session.processing = False
        session.cursor_ms = 0
        session.playback_active = False
        session.playback_paused = False
        should_redraw_graph = (
            field_index in session.graph_active_fields
            or session.visualized_filename is not None
        )
        if should_redraw_graph:
            session.visualized_filename = None
            session.visualized_duration_ms = None
    editor.loadNote(focusTo=field_index)
    _eval_status(editor, f"Updated field to {saved_name}")
    _eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        _request_graph_redraw(editor)
    else:
        _set_busy(editor, False)


def _stop_audio_playback() -> None:
    try:
        from aqt.sound import av_player

        av_player.stop_and_clear_queue()
    except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
        logger.info("audio stop failed: %s", exc)


def _stop_session_playback(session: EditorSession) -> None:
    session.playback_generation += 1
    session.playback_preparing = False
    session.playback_active = False
    session.playback_paused = False
    _stop_audio_playback()
    _cleanup_temp_playback(session)


def _cleanup_temp_playback(session: EditorSession) -> None:
    temp_path = session.temp_playback_path
    session.temp_playback_path = None
    if temp_path is None:
        return
    try:
        if temp_path.parent.name.startswith("aqe_playback_"):
            shutil.rmtree(temp_path.parent, ignore_errors=True)
        else:
            temp_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.info("temporary playback cleanup failed: %s", exc)


def _play(editor: Any) -> None:
    _eval_with_callback(
        editor,
        "window.__aqeGetPlaybackRequest ? window.__aqeGetPlaybackRequest() : "
        "({ action: 'start', cursorMs: 0 })",
        lambda request: _play_with_request(editor, request),
    )


def _play_ended(editor: Any) -> None:
    session = _SESSIONS.get(editor)
    if session:
        _stop_session_playback(session)
    else:
        _stop_audio_playback()
    _eval_status(editor, "")


def _play_with_request(editor: Any, request: Any) -> None:
    if getattr(editor, "note", None) is None:
        return
    session, source_path = _session_and_source(editor)
    if _is_busy(session):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    field_index = _current_field_index(editor)
    action, engine, cursor_ms = _playback_request_values(session, request)
    session.cursor_ms = cursor_ms
    if engine == "html":
        _apply_html_playback_request(editor, session, field_index, action, cursor_ms)
        return
    if _toggle_native_pause_resume(editor, session, field_index, action, cursor_ms):
        return

    _start_playback_from_cursor(editor, session, source_path, field_index, cursor_ms)


def _playback_request_values(
    session: EditorSession,
    request: Any,
) -> tuple[str, str, int]:
    if not isinstance(request, dict):
        return "start", "native", session.cursor_ms
    action = str(request.get("action") or "start")
    engine = str(request.get("engine") or "native")
    cursor_ms = clamp_cursor_ms(request.get("cursorMs"), session.visualized_duration_ms)
    return action, engine, cursor_ms


def _toggle_native_pause_resume(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
) -> bool:
    if action not in {"pause", "resume"} or not session.playback_active:
        return False
    from aqt.sound import av_player

    try:
        av_player.toggle_pause()
    except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
        logger.info("audio pause/resume failed: %s", exc)
        _eval_status(editor, "Pause/resume was not available.", kind="warning")
        return True
    session.playback_paused = action == "pause"
    state = "paused" if session.playback_paused else "playing"
    _eval_playback_state(editor, field_index, state, cursor_ms)
    _eval_status(editor, "Paused" if session.playback_paused else "Playing")
    return True


def _apply_html_playback_request(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
) -> None:
    if action == "pause":
        session.cursor_ms = cursor_ms
        session.playback_preparing = False
        session.playback_active = True
        session.playback_paused = True
        _set_busy(editor, False)
        _eval_status(editor, "Paused")
        return

    if action == "start":
        _stop_session_playback(session)

    session.cursor_ms = cursor_ms
    session.field_index = field_index
    session.playback_preparing = False
    session.playback_active = True
    session.playback_paused = False
    _set_busy(editor, False)
    if cursor_ms > 0 and action == "start":
        _eval_status(editor, f"Playing from {max(0.0, cursor_ms / 1000):.2f}s")
    else:
        _eval_status(editor, "Playing")


def _start_playback_from_cursor(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    field_index: int,
    cursor_ms: int,
) -> None:
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    filename = session.current_filename or source_path.name
    play_path = Path(editor.mw.col.media.dir()) / filename
    if not play_path.is_file():
        play_path = source_path
    _stop_session_playback(session)
    session.cursor_ms = clamp_cursor_ms(cursor_ms, session.visualized_duration_ms)
    offset_seconds = max(0.0, session.cursor_ms / 1000)
    if offset_seconds <= 0:
        av_player.play_tags([SoundOrVideoTag(str(play_path))])
        session.playback_active = True
        session.playback_paused = False
        _eval_playback_state(editor, field_index, "playing", session.cursor_ms)
        _eval_status(editor, "Playing")
        return

    config = AudioProcessingConfig.from_config(_config(editor))
    session.playback_generation += 1
    generation = session.playback_generation
    session.playback_preparing = True
    session.playback_active = True
    session.playback_paused = False
    playback_cursor_ms = session.cursor_ms
    _set_busy(editor, True, "Preparing playback...")
    _eval_playback_state(editor, field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        try:
            def _show_command(command: tuple[str, ...]) -> None:
                rendered = format_ffmpeg_command(command)
                message = "Preparing playback with ffmpeg"
                command_text = ""
                if config.show_ffmpeg_commands:
                    message = f"{message}: {rendered}"
                    command_text = rendered
                _main(editor, lambda: _set_busy(editor, True, message, command_text))

            result = render_playback_segment(
                play_path,
                playback_cursor_ms,
                config,
                on_command=_show_command,
            )
            _main(
                editor,
                lambda: _playback_segment_ready(
                    editor,
                    generation,
                    field_index,
                    playback_cursor_ms,
                    result.output_path,
                ),
            )
        except Exception as exc:
            message = str(exc)
            _main(editor, lambda: _playback_segment_failed(editor, generation, message))

    threading.Thread(target=_run, daemon=True).start()


def _playback_segment_ready(
    editor: Any,
    generation: int,
    field_index: int,
    cursor_ms: int,
    playback_path: Path,
) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.playback_generation:
        shutil.rmtree(playback_path.parent, ignore_errors=True)
        return
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    session.playback_preparing = False
    session.temp_playback_path = playback_path
    session.playback_active = True
    session.playback_paused = False
    av_player.stop_and_clear_queue()
    av_player.play_tags([SoundOrVideoTag(str(playback_path))])
    _set_busy(editor, False)
    _eval_playback_state(editor, field_index, "playing", cursor_ms)
    _eval_status(editor, f"Playing from {max(0.0, cursor_ms / 1000):.2f}s")


def _playback_segment_failed(editor: Any, generation: int, message: str) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.playback_generation:
        return
    session.playback_preparing = False
    session.playback_active = False
    session.playback_paused = False
    _set_busy(editor, False)
    _eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)
    _eval_status(editor, message or "Could not prepare playback.", kind="error")


def _undo(editor: Any) -> None:
    session, _source_path = _session_and_source(editor)
    if _is_busy(session):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    previous = session.undo_history.pop()
    if previous is None:
        _eval_status(editor, "Nothing to undo.")
        return
    _restore_history_entry(
        editor,
        session,
        previous,
        redo_current=True,
        status=f"Undid last edit; restored {previous.filename}",
    )


def _redo(editor: Any) -> None:
    session, _source_path = _session_and_source(editor)
    if _is_busy(session):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    next_entry = session.redo_history.pop()
    if next_entry is None:
        _eval_status(editor, "Nothing to redo.")
        return
    _restore_history_entry(
        editor,
        session,
        next_entry,
        redo_current=False,
        status=f"Redid edit; restored {next_entry.filename}",
    )


def _restore_history_entry(
    editor: Any,
    session: EditorSession,
    entry: UndoEntry,
    *,
    redo_current: bool,
    status: str,
) -> None:
    _stop_session_playback(session)
    field_index = _current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    current_state = session.state
    current_filename = session.current_filename
    _dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, entry.filename)
    if redo_current:
        session.redo_history.push(current_state, current_filename)
    else:
        session.undo_history.push(current_state, current_filename)
    session.state = entry.state
    session.current_filename = entry.filename
    session.field_index = field_index
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    restored_path = Path(editor.mw.col.media.dir()) / safe_media_basename(entry.filename)
    session.source_mtime_ns = restored_path.stat().st_mtime_ns if restored_path.is_file() else None
    editor.loadNote(focusTo=field_index)
    _eval_status(editor, status)
    _eval_playback_state(editor, field_index, "stopped", 0)
    if field_index in session.graph_active_fields:
        _request_graph_redraw(editor)


def _open_settings_from_editor(editor: Any) -> None:
    if _SETTINGS_OPENER is None:
        _eval_status(editor, "Settings are not available.", kind="error")
        return

    def _after_saved() -> None:
        _refresh_editor_after_settings_save(editor)

    _SETTINGS_OPENER(_after_saved)
    _eval_status(editor, "Opened settings.")


def _refresh_editor_after_settings_save(editor: Any) -> None:
    field_index = _current_field_index(editor)
    session = _SESSIONS.get(editor)
    if session is not None:
        session.analysis_generation += 1
        _stop_session_playback(session)
        session.processing = False
        session.analysis_busy = False
        session.playback_active = False
        session.playback_paused = False
        session.playback_preparing = False
    _dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)


def _show_current_audio_file(editor: Any) -> None:
    session, media_path = _current_media_path(editor)
    if _is_busy(session):
        _eval_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    reveal_file(media_path)
    _eval_status(editor, f"Showing {media_path.name} in folder")

def _record_mp_senet_failure_context(
    source_path: Path,
    config: AudioProcessingConfig,
    exc: Exception,
) -> None:
    record_latest_mp_senet_support_incident(
        operation="mp_senet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def _log_special_transform_failure(failure_log_label: str, message: str) -> None:
    if failure_log_label == "mp-senet denoise failed":
        incident = latest_mp_senet_support_incident()
        if incident:
            logger.exception(
                "%s: %s\n%s",
                failure_log_label,
                message,
                format_mp_senet_support_log_block(incident),
            )
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    logger.exception("%s: %s", failure_log_label, message)


def _session_and_source(editor: Any) -> tuple[EditorSession, Path]:
    field_index = _current_field_index(editor)
    filename, media_path = _current_sound_reference(editor, field_index)
    session = _SESSIONS.setdefault(editor, EditorSession())
    source_path = _session_original_source_path(editor, session, field_index, filename)
    if source_path is not None:
        return session, source_path

    if not media_path.is_file():
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)

    mtime = media_path.stat().st_mtime_ns
    if _session_needs_media_reset(session, field_index, filename, mtime):
        _reset_session_for_media(session, field_index, filename, mtime)
    return session, media_path


def _current_sound_reference(editor: Any, field_index: int) -> tuple[str, Path]:
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    filename = safe_media_basename(selection.selected.filename)
    return filename, Path(editor.mw.col.media.dir()) / filename


def _session_original_source_path(
    editor: Any,
    session: EditorSession,
    field_index: int,
    filename: str,
) -> Path | None:
    if session.field_index != field_index or session.state is None or session.current_filename != filename:
        return None
    source_path = Path(editor.mw.col.media.dir()) / session.state.source_file
    if not source_path.is_file():
        raise MissingMediaError("The original audio file was not found in Anki's media folder.")
    return source_path


def _session_needs_media_reset(
    session: EditorSession,
    field_index: int,
    filename: str,
    mtime: int,
) -> bool:
    return (
        session.field_index != field_index
        or session.state is None
        or session.source_mtime_ns != mtime
        or session.state.source_file != filename
    )


def _reset_session_for_media(
    session: EditorSession,
    field_index: int,
    filename: str,
    mtime: int,
) -> None:
    _stop_session_playback(session)
    session.state = AudioEditState(source_file=filename)
    session.current_filename = filename
    session.undo_history.clear()
    session.redo_history.clear()
    session.processing = False
    session.analysis_busy = False
    session.field_index = field_index
    session.source_mtime_ns = mtime
    session.cursor_ms = 0
    session.visualized_filename = None
    session.visualized_duration_ms = None
    session.playback_active = False
    session.playback_paused = False
    session.playback_preparing = False


def _current_media_path(editor: Any) -> tuple[EditorSession, Path]:
    session, _source_path = _session_and_source(editor)
    filename = session.current_filename
    if not filename:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    media_path = Path(editor.mw.col.media.dir()) / safe_media_basename(filename)
    if not media_path.is_file():
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)
    return session, media_path


def _analyze_current_async(editor: Any) -> None:
    existing = _SESSIONS.get(editor)
    if existing and _is_busy(existing):
        _eval_visualizer_status(editor, STILL_PROCESSING_MESSAGE, kind="processing")
        return
    field_index = _current_field_index(editor)
    snapshot = _snapshot_edit_state_for_cross_field_analysis(existing, field_index)
    try:
        session, current_path = _current_media_path(editor)
    except AudioQuickEditorError:
        if existing is not None:
            _restore_edit_state_snapshot(existing, snapshot)
        raise
    _restore_edit_state_snapshot(session, snapshot)
    config = AudioProcessingConfig.from_config(_config(editor))
    _stop_session_playback(session)
    session.analysis_generation += 1
    generation = session.analysis_generation
    session.analysis_busy = True
    session.playback_active = False
    session.playback_paused = False
    session.cursor_ms = 0
    session.graph_active_fields.add(field_index)
    session.visualized_filename = current_path.name
    session.visualized_duration_ms = None
    _set_busy(editor, True, "Analyzing...")
    _eval_playback_state(editor, field_index, "stopped", 0)
    _eval_visualizer_status(editor, "Analyzing...")

    def _run() -> None:
        try:
            track = _analyze_prosody_cached(current_path, config)
            _main(editor, lambda: _analysis_finished(editor, generation, field_index, track))
        except Exception as exc:
            message = str(exc)
            _main(editor, lambda: _analysis_failed(editor, generation, field_index, message))

    threading.Thread(target=_run, daemon=True).start()


def _snapshot_edit_state_for_cross_field_analysis(
    session: EditorSession | None,
    field_index: int,
) -> EditSessionSnapshot | None:
    if session is None or session.field_index is None or session.field_index == field_index:
        return None
    return EditSessionSnapshot(
        state=session.state,
        field_index=session.field_index,
        current_filename=session.current_filename,
        undo_entries=tuple(session.undo_history.entries),
        redo_entries=tuple(session.redo_history.entries),
        source_mtime_ns=session.source_mtime_ns,
        cursor_ms=session.cursor_ms,
    )


def _restore_edit_state_snapshot(
    session: EditorSession,
    snapshot: EditSessionSnapshot | None,
) -> None:
    if snapshot is None:
        return
    session.state = snapshot.state
    session.field_index = snapshot.field_index
    session.current_filename = snapshot.current_filename
    session.undo_history.entries = list(snapshot.undo_entries)
    session.redo_history.entries = list(snapshot.redo_entries)
    session.source_mtime_ns = snapshot.source_mtime_ns
    session.cursor_ms = snapshot.cursor_ms


def _analysis_finished(
    editor: Any,
    generation: int,
    field_index: int,
    track: ProsodyTrack,
) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.analysis_generation:
        return
    session.analysis_busy = False
    session.visualized_duration_ms = track.duration_ms
    session.cursor_ms = clamp_cursor_ms(session.cursor_ms, track.duration_ms)
    payload = json.dumps(ProsodyPayload.from_dict(track.to_payload()).to_dict())
    cursor_payload = json.dumps(session.cursor_ms)
    editor.web.eval(
        "window.__aqeSetVisualizer && window.__aqeSetVisualizer("
        f"{json.dumps(int(field_index))}, {payload}, {cursor_payload})"
    )
    _set_busy(editor, False)


def _analysis_failed(editor: Any, generation: int, field_index: int, message: str) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.analysis_generation:
        return
    session.analysis_busy = False
    session.playback_active = False
    session.playback_paused = False
    _set_busy(editor, False)
    editor.web.eval(
        "window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus("
        f"{json.dumps(int(field_index))}, "
        f"{json.dumps(message or 'Audio visualization failed.')}, "
        f"{json.dumps('error')})"
    )


def _set_cursor_from_web(editor: Any) -> None:
    def _apply(value: Any) -> None:
        if getattr(editor, "note", None) is None:
            return
        session, source_path = _session_and_source(editor)
        cursor_value = value.get("cursorMs") if isinstance(value, dict) else value
        session.cursor_ms = clamp_cursor_ms(cursor_value, session.visualized_duration_ms)
        if isinstance(value, dict) and value.get("restartPlayback"):
            if value.get("engine") == "html":
                session.playback_active = True
                session.playback_paused = False
                return
            field_index = _current_field_index(editor)
            _start_playback_from_cursor(editor, session, source_path, field_index, session.cursor_ms)

    _eval_with_callback(
        editor,
        "window.__aqeGetCursorIntent ? window.__aqeGetCursorIntent() : "
        "(window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0)",
        _apply,
    )


def _is_busy(session: EditorSession) -> bool:
    return session.processing or session.analysis_busy or session.playback_preparing


def _current_field_index(editor: Any) -> int:
    if editor.currentField is not None:
        return int(editor.currentField)
    if getattr(editor, "last_field_index", None) is not None:
        return int(editor.last_field_index)
    raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)


def _config(editor: Any) -> dict[str, Any]:
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return editor.mw.addonManager.getConfig(addon_id) or {}


def _artifact_root(editor: Any) -> Path:
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return Path(editor.mw.addonManager.addonsFolder(addon_id)) / "aqe_artifacts"


def _dispose_editor_frontend_controls(editor: Any) -> None:
    editor.web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def _eval_status(editor: Any, message: str, kind: str = "info") -> None:
    payload = json.dumps(message)
    kind_payload = json.dumps(kind)
    editor.web.eval(f"window.__aqeSetStatus && window.__aqeSetStatus({payload}, {kind_payload})")


def _eval_visualizer_status(editor: Any, message: str, kind: str = "info") -> None:
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus("
        f"{json.dumps(int(field_index))}, {json.dumps(message)}, {json.dumps(kind)})"
    )


def _eval_playback_state(
    editor: Any,
    field_index: int | None,
    state: str,
    cursor_ms: int,
) -> None:
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetPlaybackState && window.__aqeSetPlaybackState("
        f"{json.dumps(int(field_index))}, {json.dumps(state)}, {json.dumps(int(cursor_ms))})"
    )


def _request_graph_redraw(editor: Any) -> None:
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = _SESSIONS.get(editor)
        field_index = session.field_index if session else 0
    _schedule_graph_redraw_attempt(editor, int(field_index or 0), remaining=12, delay_ms=150)


def _schedule_graph_redraw_attempt(
    editor: Any,
    field_index: int,
    *,
    remaining: int,
    delay_ms: int,
) -> None:
    from aqt.qt import QTimer

    def _attempt() -> None:
        if getattr(editor, "note", None) is None:
            return
        try:
            _eval_with_callback(
                editor,
                _graph_redraw_expression(field_index),
                lambda started: _retry_graph_redraw(editor, field_index, bool(started), remaining - 1),
            )
        except RuntimeError:
            return

    QTimer.singleShot(delay_ms, _attempt)


def _graph_redraw_expression(field_index: int) -> str:
    return (
        "(() => {"
        "if (!window.__aqeScan || !window.__aqeResetGraphAfterEdit) return false;"
        "window.__aqeScan();"
        f"return window.__aqeResetGraphAfterEdit({json.dumps(int(field_index))});"
        "})()"
    )


def _retry_graph_redraw(editor: Any, field_index: int, started: bool, remaining: int) -> None:
    if started or remaining <= 0:
        return
    _schedule_graph_redraw_attempt(editor, field_index, remaining=remaining, delay_ms=100)


def _set_busy(editor: Any, busy: bool, message: str = "", command: str = "") -> None:
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = _SESSIONS.get(editor)
        field_index = session.field_index if session else None
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetBusy && window.__aqeSetBusy("
        f"{json.dumps(int(field_index))}, {json.dumps(busy)}, "
        f"{json.dumps(message)}, {json.dumps(command)})"
    )


def _main(editor: Any, callback: Any) -> None:
    editor.mw.taskman.run_on_main(callback)


def _eval_with_callback(editor: Any, expression: str, callback: Any) -> None:
    if hasattr(editor.web, "evalWithCallback"):
        editor.web.evalWithCallback(expression, callback)
        return
    page = editor.web.page() if hasattr(editor.web, "page") else None
    if page is not None and hasattr(page, "runJavaScript"):
        page.runJavaScript(expression, callback)
