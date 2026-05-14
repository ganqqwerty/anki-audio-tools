"""Thin Anki editor integration for inline audio editing."""

from __future__ import annotations

import json
import logging
import shutil
import threading
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .audio_processor import (
    format_ffmpeg_command,
    make_output_filename,
    render_audio,
    temp_final_path,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .editor_actions import BRIDGE_COMMANDS, apply_processing_command
from .editor_ui import injection_script
from .errors import AudioProcessingError, AudioQuickEditorError, MissingMediaError
from .prosody_analyzer import analyze_prosody
from .prosody_types import ProsodyTrack, clamp_cursor_ms
from .sound_refs import (
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class HistoryEntry:
    """A field reference and edit state that can be restored by Undo."""

    state: AudioEditState
    filename: str


@dataclass
class EditorSession:
    """Mutable edit session for a single editor instance."""

    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    undo_stack: list[HistoryEntry] = field(default_factory=list)
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


_SESSIONS: "weakref.WeakKeyDictionary[Any, EditorSession]" = weakref.WeakKeyDictionary()


def register_editor_hooks(gui_hooks: Any) -> None:
    """Register all editor hooks used by the add-on."""
    gui_hooks.editor_did_init.append(_on_editor_did_init)
    gui_hooks.editor_will_load_note.append(_on_editor_will_load_note)


def _on_editor_did_init(editor: Any) -> None:
    for command in BRIDGE_COMMANDS:
        editor._links[command] = lambda current_editor, cmd=command: _handle_bridge_command(
            current_editor, cmd
        )


def _on_editor_will_load_note(js: str, note: Any, editor: Any) -> str:
    return f"{js}\n{injection_script(_audio_field_indices(note))}"


def _audio_field_indices(note: Any) -> list[int]:
    """Return field indices containing an MVP-supported sound reference."""
    indices: list[int] = []
    for index, field_html in enumerate(getattr(note, "fields", [])):
        try:
            selection = select_first_sound_reference(field_html)
        except AudioQuickEditorError:
            continue
        if selection.selected is not None:
            indices.append(index)
    return indices


def _handle_bridge_command(editor: Any, command: str) -> bool:
    try:
        if command == "aqe:scan":
            _eval_status(editor, "")
            editor.web.eval("window.__aqeScan && window.__aqeScan()")
            return True
        if command == "aqe:analyze":
            _analyze_current_async(editor)
            return True
        if command == "aqe:set-cursor":
            _set_cursor_from_web(editor)
            return True
        if command == "aqe:play":
            _play(editor)
            return True
        if command == "aqe:undo":
            _undo(editor)
            return True
        _update_state_and_render(editor, command)
        return True
    except AudioQuickEditorError as exc:
        _set_busy(editor, False)
        _eval_status(editor, str(exc), kind="error")
    except Exception as exc:  # pragma: no cover - defensive boundary for Anki bridge
        logger.exception("audio quick editor command failed: %s", command)
        _set_busy(editor, False)
        _eval_status(editor, f"Audio processing failed. The note was not changed. ({exc})", kind="error")
    return True


def _update_state_and_render(editor: Any, command: str) -> None:
    existing = _SESSIONS.get(editor)
    if existing and _is_busy(existing):
        _eval_status(editor, "Still processing. Please wait.", kind="processing")
        return
    session, source_path = _session_and_source(editor)
    config = AudioProcessingConfig.from_config(_config(editor))
    state = session.state or AudioEditState(source_file=source_path.name)
    updated_state = apply_processing_command(command, state, config)
    if updated_state is None:
        _set_busy(editor, False)
        return
    if updated_state == state:
        _set_busy(editor, False)
        _eval_status(editor, "No change to process.")
        return
    _render_and_replace_async(editor, session, source_path, updated_state, config)


def _render_and_replace_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
) -> None:
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
        raise AudioProcessingError("No [sound:...] reference found in the current field.")
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    session = _SESSIONS.get(editor)
    should_redraw_graph = False
    if session:
        if session.state is not None and session.current_filename is not None:
            session.undo_stack.append(HistoryEntry(session.state, session.current_filename))
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
        _request_graph_redraw(editor, field_index)
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


def _play(editor: Any) -> None:
    _eval_with_callback(
        editor,
        "window.__aqeGetPlaybackRequest ? window.__aqeGetPlaybackRequest() : "
        "({ action: 'start', cursorMs: 0 })",
        lambda request: _play_with_request(editor, request),
    )


def _play_with_request(editor: Any, request: Any) -> None:
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    session, source_path = _session_and_source(editor)
    if _is_busy(session):
        _eval_status(editor, "Still processing. Please wait.", kind="processing")
        return
    field_index = _current_field_index(editor)
    action = "start"
    cursor_ms = session.cursor_ms
    if isinstance(request, dict):
        action = str(request.get("action") or "start")
        cursor_ms = clamp_cursor_ms(request.get("cursorMs"), session.visualized_duration_ms)
    session.cursor_ms = cursor_ms
    if action in {"pause", "resume"} and session.playback_active:
        try:
            av_player.toggle_pause()
        except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
            logger.info("audio pause/resume failed: %s", exc)
            _eval_status(editor, "Pause/resume was not available.", kind="warning")
            return
        session.playback_paused = action == "pause"
        state = "paused" if session.playback_paused else "playing"
        _eval_playback_state(editor, field_index, state, cursor_ms)
        _eval_status(editor, "Paused" if session.playback_paused else "Playing")
        return

    filename = session.current_filename or source_path.name
    play_path = Path(editor.mw.col.media.dir()) / filename
    if not play_path.is_file():
        play_path = source_path
    av_player.stop_and_clear_queue()
    av_player.play_tags([SoundOrVideoTag(str(play_path))])
    offset_seconds = max(0.0, session.cursor_ms / 1000)
    session.playback_active = True
    session.playback_paused = False
    _eval_playback_state(editor, field_index, "playing", session.cursor_ms)
    if offset_seconds <= 0:
        _eval_status(editor, "Playing")
        return
    try:
        seek_relative = cast(Any, av_player.seek_relative)
        seek_relative(offset_seconds)
    except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
        logger.info("audio seek failed: %s", exc)
        _eval_status(editor, "Playing from start; seeking was not available.", kind="warning")
        return
    _eval_status(editor, f"Playing from {offset_seconds:.2f}s")


def _undo(editor: Any) -> None:
    session, _source_path = _session_and_source(editor)
    if _is_busy(session):
        _eval_status(editor, "Still processing. Please wait.", kind="processing")
        return
    if not session.undo_stack:
        _eval_status(editor, "Nothing to undo.")
        return
    previous = session.undo_stack.pop()
    field_index = _current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError("No [sound:...] reference found in the current field.")
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, previous.filename)
    session.state = previous.state
    session.current_filename = previous.filename
    session.field_index = field_index
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    editor.loadNote(focusTo=field_index)
    _eval_status(editor, f"Undid last edit; restored {previous.filename}")
    _eval_playback_state(editor, field_index, "stopped", 0)
    if field_index in session.graph_active_fields:
        _request_graph_redraw(editor, field_index)


def _session_and_source(editor: Any) -> tuple[EditorSession, Path]:
    field_index = _current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError("No [sound:...] reference found in the current field.")
    filename = safe_media_basename(selection.selected.filename)
    media_path = Path(editor.mw.col.media.dir()) / filename
    session = _SESSIONS.setdefault(editor, EditorSession())
    if (
        session.field_index == field_index
        and session.state is not None
        and session.current_filename == filename
    ):
        source_path = Path(editor.mw.col.media.dir()) / session.state.source_file
        if not source_path.is_file():
            raise MissingMediaError("The original audio file was not found in Anki's media folder.")
        return session, source_path

    if not media_path.is_file():
        raise MissingMediaError("The referenced audio file was not found in Anki's media folder.")

    mtime = media_path.stat().st_mtime_ns
    if (
        session.field_index != field_index
        or session.state is None
        or session.source_mtime_ns != mtime
        or session.state.source_file != filename
    ):
        session.state = AudioEditState(source_file=filename)
        session.current_filename = filename
        session.undo_stack.clear()
        session.processing = False
        session.analysis_busy = False
        session.field_index = field_index
        session.source_mtime_ns = mtime
        session.cursor_ms = 0
        session.visualized_filename = None
        session.visualized_duration_ms = None
        session.playback_active = False
        session.playback_paused = False
    return session, media_path


def _current_media_path(editor: Any) -> tuple[EditorSession, Path]:
    session, _source_path = _session_and_source(editor)
    filename = session.current_filename
    if not filename:
        raise AudioProcessingError("No [sound:...] reference found in the current field.")
    media_path = Path(editor.mw.col.media.dir()) / safe_media_basename(filename)
    if not media_path.is_file():
        raise MissingMediaError("The referenced audio file was not found in Anki's media folder.")
    return session, media_path


def _analyze_current_async(editor: Any) -> None:
    existing = _SESSIONS.get(editor)
    if existing and _is_busy(existing):
        _eval_visualizer_status(editor, "Still processing. Please wait.", kind="processing")
        return
    session, current_path = _current_media_path(editor)
    config = AudioProcessingConfig.from_config(_config(editor))
    field_index = _current_field_index(editor)
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
            track = analyze_prosody(current_path, config)
            _main(editor, lambda: _analysis_finished(editor, generation, track))
        except Exception as exc:
            message = str(exc)
            _main(editor, lambda: _analysis_failed(editor, generation, message))

    threading.Thread(target=_run, daemon=True).start()


def _analysis_finished(editor: Any, generation: int, track: ProsodyTrack) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.analysis_generation:
        return
    session.analysis_busy = False
    session.visualized_duration_ms = track.duration_ms
    session.cursor_ms = clamp_cursor_ms(session.cursor_ms, track.duration_ms)
    payload = json.dumps(track.to_payload())
    cursor_payload = json.dumps(session.cursor_ms)
    field_index = session.field_index if session.field_index is not None else _current_field_index(editor)
    editor.web.eval(
        "window.__aqeSetVisualizer && window.__aqeSetVisualizer("
        f"{json.dumps(int(field_index))}, {payload}, {cursor_payload})"
    )
    _set_busy(editor, False)


def _analysis_failed(editor: Any, generation: int, message: str) -> None:
    session = _SESSIONS.get(editor)
    if session is None or generation != session.analysis_generation:
        return
    session.analysis_busy = False
    session.playback_active = False
    session.playback_paused = False
    _set_busy(editor, False)
    _eval_visualizer_status(editor, message or "Audio visualization failed.", kind="error")


def _set_cursor_from_web(editor: Any) -> None:
    def _apply(value: Any) -> None:
        session = _SESSIONS.setdefault(editor, EditorSession())
        session.cursor_ms = clamp_cursor_ms(value, session.visualized_duration_ms)

    _eval_with_callback(
        editor,
        "window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0",
        _apply,
    )


def _is_busy(session: EditorSession) -> bool:
    return session.processing or session.analysis_busy


def _current_field_index(editor: Any) -> int:
    if editor.currentField is not None:
        return int(editor.currentField)
    if getattr(editor, "last_field_index", None) is not None:
        return int(editor.last_field_index)
    raise AudioProcessingError("No [sound:...] reference found in the current field.")


def _config(editor: Any) -> dict[str, Any]:
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return editor.mw.addonManager.getConfig(addon_id) or {}


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


def _request_graph_redraw(editor: Any, field_index: int) -> None:
    from aqt.qt import QTimer

    redraw_key = f"__aqeAutoRedrawStarted{int(field_index)}"
    script = (
        "(function() { "
        f"if (window.__aqeResetGraphAfterEdit && !window[{json.dumps(redraw_key)}]) {{ "
        f"window[{json.dumps(redraw_key)}] = true; "
        f"window.__aqeResetGraphAfterEdit({json.dumps(int(field_index))}); "
        "} "
        "})()"
    )

    def _attempt(remaining: int) -> None:
        try:
            editor.web.eval(script)
        except RuntimeError:
            return
        if remaining > 0:
            QTimer.singleShot(100, lambda: _attempt(remaining - 1))

    QTimer.singleShot(100, lambda: _attempt(30))


def _set_busy(editor: Any, busy: bool, message: str = "", command: str = "") -> None:
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
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
