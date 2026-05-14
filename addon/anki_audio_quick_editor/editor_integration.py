"""Thin Anki editor integration for inline audio editing."""

from __future__ import annotations

import json
import logging
import shutil
import threading
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .audio_processor import (
    format_ffmpeg_command,
    make_output_filename,
    render_audio,
    temp_final_path,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .editor_ui import injection_script
from .errors import AudioProcessingError, AudioQuickEditorError, MissingMediaError
from .sound_refs import (
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)

logger = logging.getLogger(__name__)

BRIDGE_COMMANDS = (
    "aqe:scan",
    "aqe:play",
    "aqe:trim-left",
    "aqe:untrim-left",
    "aqe:trim-right",
    "aqe:untrim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:trim-silence",
    "aqe:remove-pauses",
    "aqe:undo",
)


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
    source_mtime_ns: int | None = None


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
    session, source_path = _session_and_source(editor)
    if session.processing:
        _eval_status(editor, "Still processing. Please wait.", kind="processing")
        return
    config = AudioProcessingConfig.from_config(_config(editor))
    state = session.state or AudioEditState(source_file=source_path.name)
    updated_state = _apply_command_to_state(command, state, config)
    if updated_state is None:
        _set_busy(editor, False)
        return
    if updated_state == state:
        _set_busy(editor, False)
        _eval_status(editor, "No change to process.")
        return
    _render_and_replace_async(editor, session, source_path, updated_state, config)


def _apply_command_to_state(
    command: str,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a bridge command."""
    step = config.manual_trim_small_ms
    actions = {
        "aqe:trim-left": lambda: state.trim_left(step),
        "aqe:untrim-left": lambda: state.untrim_left(step),
        "aqe:trim-right": lambda: state.trim_right(step),
        "aqe:untrim-right": lambda: state.untrim_right(step),
        "aqe:slower": lambda: state.slower(config),
        "aqe:faster": lambda: state.faster(config),
        "aqe:trim-silence": state.toggle_edge_trim,
        "aqe:remove-pauses": state.toggle_internal_pauses,
    }
    action = actions.get(command)
    return action() if action else None


def _render_and_replace_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
) -> None:
    session.processing = True
    _set_busy(editor, True, "Processing...")

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
    if session:
        if session.state is not None and session.current_filename is not None:
            session.undo_stack.append(HistoryEntry(session.state, session.current_filename))
        session.state = updated_state
        session.current_filename = saved_name
        session.field_index = field_index
        session.processing = False
    editor.loadNote(focusTo=field_index)
    _set_busy(editor, False)
    _eval_status(editor, f"Updated field to {saved_name}")


def _render_failed(editor: Any, message: str) -> None:
    session = _SESSIONS.get(editor)
    if session:
        session.processing = False
    _set_busy(editor, False)
    _eval_status(editor, message, kind="error")


def _play(editor: Any) -> None:
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    session, source_path = _session_and_source(editor)
    filename = session.current_filename or source_path.name
    play_path = Path(editor.mw.col.media.dir()) / filename
    if not play_path.is_file():
        play_path = source_path
    av_player.stop_and_clear_queue()
    av_player.play_tags([SoundOrVideoTag(str(play_path))])
    _eval_status(editor, "Playing")


def _undo(editor: Any) -> None:
    session, _source_path = _session_and_source(editor)
    if session.processing:
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
    editor.loadNote(focusTo=field_index)
    _eval_status(editor, f"Undid last edit; restored {previous.filename}")


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
        session.field_index = field_index
        session.source_mtime_ns = mtime
    return session, media_path


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
