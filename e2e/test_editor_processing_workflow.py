"""E2E tests for editor audio edit controls and processing state."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.media_oracles import (
    db_ratio,
    decode_mono_f32,
    difference_rms,
    probe_audio,
    rms,
    window_rms,
)

from e2e.editor_audio_generation_helpers import _generate_tone_silence_tone
from e2e.editor_graph_helpers import (
    _graph_state_js,
)
from e2e.editor_note_helpers import (
    _artifact_root,
    _basic_audio_note,
    _button_selector,
    _cleanup_artifact_dirs,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.editor_processing_workflow_helpers import expected_final_status
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_js,
    wait_for_js_condition,
    wait_for_selector,
)


def test_processing_toolbar_exposes_the_shipped_operation_contract(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_each_button_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    artifact_root = _artifact_root(anki_mw)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: all(
                hidden_command not in commands
                for hidden_command in (
                    "aqe:save",
                    "aqe:cancel",
                )
            ),
            timeout=5.0,
        )
        assert wait_for_js_condition(
            editor.web,
            """
            (() => {
              const buttons = Array.from(document.querySelectorAll('.aqe-button'))
                .filter((node) => getComputedStyle(node).display !== 'none' && node.getClientRects().length > 0);
              return {
                labels: buttons.map((node) => (
                  node.querySelector('.aqe-button-label')?.textContent || node.textContent || ''
                ).trim()),
                iconsPerButton: buttons.map((node) => node.querySelectorAll('.aqe-button-icon svg').length),
                iconStrokeValues: buttons.flatMap((button) =>
                  Array.from(button.querySelectorAll('.aqe-button-icon svg'))
                    .map((node) => node.getAttribute('stroke') || getComputedStyle(node).stroke || '')
                ),
              };
            })()
            """,
            lambda state: (
                state["labels"]
                == [
                    "Play",
                    "Options",
                    "Graph",
                    "Options",
                    "Folder",
                    "Share",
                    "Options",
                    "Denoise",
                    "Options",
                    "Shorten Pauses",
                    "Options",
                    "Slower",
                    "Faster",
                    "Options",
                    "Volume -",
                    "Volume +",
                    "Options",
                    "Back",
                    "Forward",
                    "Pitch Hum",
                    "Options",
                    "Convert",
                    "Options",
                    "Compress Audio",
                    "Options",
                    "Undo",
                    "Options",
                    "Redo",
                    "Options",
                    "Settings",
                ]
                and state["iconsPerButton"] == [
                    1 if label == "Options" else 0 for label in state["labels"]
                ]
                and state["iconStrokeValues"]
                and all(stroke == "currentColor" for stroke in state["iconStrokeValues"])
            ),
            timeout=5.0,
        )

        assert source.read_bytes() == original_bytes
        graph_state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )
        assert graph_state["active"] is False
        assert graph_state["hidden"] is True
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


@pytest.mark.parametrize(
    "command",
    [
        "aqe:slower",
        "aqe:faster",
        "aqe:volume-down",
        "aqe:volume-up",
        "aqe:remove-pauses",
        "aqe:pitch-hum",
    ],
)
def test_processing_button_changes_decoded_audio_semantics(
    anki_mw,
    ffmpeg_config,
    command: str,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"editor_semantic_{command.removeprefix('aqe:')}.wav"
    if command in {"aqe:remove-pauses", "aqe:pitch-hum"}:
        _generate_tone_silence_tone(ffmpeg_config, source)
    else:
        generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        pause_preprocess_denoise=False,
    )
    artifact_root = _artifact_root(anki_mw)
    ffmpeg = Path(ffmpeg_config.ffmpeg_path)
    ffprobe = ffmpeg.with_name("ffprobe")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector(command), timeout=10.0)
        click_selector(editor.web, _button_selector(command), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        output = media_dir / generated_name
        expected_status = expected_final_status(command)
        _wait_for_status_flow(
            editor,
            lambda value: value["text"] == expected_status,
            timeout=15.0,
        )

        source_probe = probe_audio(ffprobe, source)
        output_probe = probe_audio(ffprobe, output)
        source_pcm = decode_mono_f32(ffmpeg, source)
        output_pcm = decode_mono_f32(ffmpeg, output)
        if command == "aqe:slower":
            assert output_probe.duration_s / source_probe.duration_s == pytest.approx(1.5, abs=0.12)
        elif command == "aqe:faster":
            assert output_probe.duration_s / source_probe.duration_s == pytest.approx(2 / 3, abs=0.08)
        elif command == "aqe:volume-down":
            assert db_ratio(rms(source_pcm), rms(output_pcm)) == pytest.approx(-15.0, abs=0.8)
        elif command == "aqe:volume-up":
            assert db_ratio(rms(source_pcm), rms(output_pcm)) == pytest.approx(15.0, abs=0.8)
        elif command == "aqe:remove-pauses":
            assert output_probe.duration_s < source_probe.duration_s - 0.18
            assert rms(output_pcm) > 0.01
        else:
            source_gap = window_rms(source_pcm, start_s=0.5, end_s=0.75)
            output_gap = window_rms(output_pcm, start_s=0.5, end_s=0.75)
            assert source_gap < 0.001
            assert output_gap < 0.001
            assert difference_rms(
                source_pcm,
                output_pcm,
                start_s=0.08,
                end_s=0.32,
            ) > 0.01

        assert source.read_bytes() == original_bytes
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


def test_ffmpeg_command_status_respects_settings_flag(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    hidden_source = media_dir / "editor_hidden_command_source.wav"
    shown_source = media_dir / "editor_shown_command_source.wav"
    generate_tone(ffmpeg_config, hidden_source, duration_s=2.0)
    generate_tone(ffmpeg_config, shown_source, duration_s=2.0)

    hidden_note = _basic_audio_note(anki_mw, hidden_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=False)
    hidden_editor, hidden_parent = _open_editor(anki_mw, hidden_note)
    try:
        wait_for_selector(hidden_editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _start_status_transition_observer(hidden_editor)
        click_selector(hidden_editor.web, _button_selector("aqe:faster"), timeout=5.0)
        _wait_for_generated_mp3(hidden_note, media_dir, hidden_source.name)
        final_status = _wait_for_status_flow(
            hidden_editor,
            lambda status: status["text"] == "Increased speed to x1.5.",
            timeout=10.0,
        )
        assert final_status["title"] == ""
        hidden_status = _observed_processing_status(hidden_editor)
        assert " -i " not in hidden_status["text"]
        assert hidden_status["title"] == ""
    finally:
        hidden_editor.set_note(None)
        hidden_parent.close()

    shown_note = _basic_audio_note(anki_mw, shown_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=True)
    shown_editor, shown_parent = _open_editor(anki_mw, shown_note)
    try:
        wait_for_selector(shown_editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _start_status_transition_observer(shown_editor)
        click_selector(shown_editor.web, _button_selector("aqe:faster"), timeout=5.0)
        _wait_for_generated_mp3(shown_note, media_dir, shown_source.name)
        final_status = _wait_for_status_flow(
            shown_editor,
            lambda status: status["text"] == "Increased speed to x1.5.",
            timeout=10.0,
        )
        assert final_status["title"] == ""
        shown_status = _observed_processing_status(shown_editor)
        assert " -i " in shown_status["text"]
        assert ffmpeg_config.ffmpeg_path in shown_status["title"]
    finally:
        shown_editor.set_note(None)
        shown_parent.close()


def _start_status_transition_observer(editor) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const status = document.querySelector('[data-testid="aqe-status-0"]');
          if (!(status instanceof HTMLElement)) throw new Error('status element missing');
          window.__aqeObservedStatuses = [];
          const record = () => window.__aqeObservedStatuses.push({
            text: status.textContent || '',
            title: status.getAttribute('data-aqe-tooltip-content') || '',
          });
          record();
          new MutationObserver(record).observe(status, {
            attributes: true,
            childList: true,
            characterData: true,
            subtree: true,
          });
        })()
        """,
    )


def _observed_processing_status(editor) -> dict[str, str]:
    statuses = wait_for_js(editor.web, "window.__aqeObservedStatuses || []", timeout=1.0)
    matching = [
        status
        for status in statuses
        if status["text"].startswith("Processing with ffmpeg")
    ]
    assert matching, statuses
    assert all(status == matching[0] for status in matching), matching
    return matching[0]
