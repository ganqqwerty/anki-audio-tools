"""E2E tests for the real inline editor audio workflow."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QWidget
from tests.prosody_language_fixtures import (
    LANGUAGE_CONTOUR_SPECS,
    ContourWindow,
    generate_praat_vowel_fixture,
    median,
    require_praat_and_ffmpeg,
    window_named,
)

from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)

ADDON_NUMERIC_ID = "1000000002"
PLAYBACK_INTERVAL_TOLERANCE_MS = 75


@dataclass
class PlaybackAttempt:
    filename: str
    path: Path
    duration_ms: int
    start_ms: int = 0
    end_ms: int = 0
    audible_start_ms: int = 0
    audible_end_ms: int = 0
    started_at: float = 0.0
    seek_calls: list[float] | None = None

    def __post_init__(self) -> None:
        self.end_ms = self.duration_ms
        self.audible_end_ms = self.duration_ms
        if self.seek_calls is None:
            self.seek_calls = []


class FakePlaybackRecorder:
    def __init__(
        self,
        media_dir: Path,
        durations_ms: dict[str, int],
        *,
        apply_immediate_seek: bool = True,
        ffmpeg_config: Any | None = None,
    ) -> None:
        self.media_dir = media_dir
        self.durations_ms = durations_ms
        self.apply_immediate_seek = apply_immediate_seek
        self.ffmpeg_config = ffmpeg_config
        self.attempts: list[PlaybackAttempt] = []
        self.unknown_filenames: list[str] = []
        self.stop_count = 0
        self.toggle_count = 0

    @property
    def current(self) -> PlaybackAttempt | None:
        return self.attempts[-1] if self.attempts else None

    def play_tags(self, tags) -> None:
        tag = tags[0]
        filename = str(tag.filename)
        path = Path(filename)
        if not path.is_absolute():
            path = self.media_dir / filename
        duration_ms = self._duration_ms(path)
        attempt = PlaybackAttempt(
            filename=path.name,
            path=path,
            duration_ms=duration_ms,
            started_at=time.monotonic(),
        )
        segment_start_ms = _playback_segment_start_ms(path.name)
        if segment_start_ms is not None:
            attempt.start_ms = segment_start_ms
            attempt.end_ms = segment_start_ms + duration_ms
            attempt.audible_start_ms = segment_start_ms
            attempt.audible_end_ms = attempt.end_ms
        self.attempts.append(attempt)

    def _duration_ms(self, path: Path) -> int:
        duration_ms = self.durations_ms.get(path.name)
        if duration_ms is not None:
            return duration_ms
        if self.ffmpeg_config is not None and path.is_file():
            from anki_audio_quick_editor.audio_processor import probe_duration_ms

            return probe_duration_ms(path, self.ffmpeg_config)
        self.unknown_filenames.append(path.name)
        return next(iter(self.durations_ms.values()))

    def seek_relative(self, seconds: float) -> None:
        current = self.current
        if current is None:
            return
        current.seek_calls = current.seek_calls or []
        current.seek_calls.append(seconds)
        current.start_ms = max(
            0,
            min(current.duration_ms, current.start_ms + round(seconds * 1000)),
        )
        if self.apply_immediate_seek:
            current.audible_start_ms = current.start_ms

    def stop_and_clear_queue(self) -> None:
        self.stop_count += 1
        current = self.current
        if current is None or current.started_at <= 0:
            return
        elapsed_ms = round((time.monotonic() - current.started_at) * 1000)
        current.audible_end_ms = max(
            current.audible_start_ms,
            min(current.duration_ms, current.audible_start_ms + elapsed_ms),
        )

    def toggle_pause(self) -> None:
        self.toggle_count += 1


@contextmanager
def _record_fake_playback(
    media_dir: Path,
    durations_ms: dict[str, int],
    *,
    apply_immediate_seek: bool = True,
    ffmpeg_config: Any | None = None,
):
    from aqt.sound import av_player

    recorder = FakePlaybackRecorder(
        media_dir,
        durations_ms,
        apply_immediate_seek=apply_immediate_seek,
        ffmpeg_config=ffmpeg_config,
    )
    with (
        patch.object(av_player, "stop_and_clear_queue", recorder.stop_and_clear_queue),
        patch.object(av_player, "play_tags", recorder.play_tags),
        patch.object(av_player, "seek_relative", recorder.seek_relative),
        patch.object(av_player, "toggle_pause", recorder.toggle_pause),
    ):
        yield recorder


def _assert_interval(
    attempt: PlaybackAttempt,
    expected_start_ms: int,
    *,
    expected_end_ms: int | None = None,
    tolerance_ms: int = PLAYBACK_INTERVAL_TOLERANCE_MS,
) -> None:
    assert abs(attempt.start_ms - expected_start_ms) <= tolerance_ms
    if expected_end_ms is not None:
        assert abs(attempt.end_ms - expected_end_ms) <= tolerance_ms
    else:
        assert attempt.end_ms >= attempt.start_ms


def _playback_segment_start_ms(filename: str) -> int | None:
    match = re.search(r"__from_(\d+)ms_", filename)
    return int(match.group(1)) if match else None


def _basic_audio_note(anki_mw, audio_filename: str):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = f"Prompt [sound:{audio_filename}]"
    note["Back"] = "Back"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _three_audio_field_note(anki_mw, audio_filenames: tuple[str, str, str]):
    models = anki_mw.col.models
    notetype = models.new("AQE E2E Three Audio Fields")
    for name in ("One", "Two", "Three"):
        models.add_field(notetype, models.new_field(name))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{One}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Two}} {{Three}}"
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    for index, filename in enumerate(audio_filenames):
        note.fields[index] = f"Field {index + 1} [sound:{filename}]"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _sound_filename(field_html: str) -> str:
    match = re.search(r"\[sound:([^\]]+)\]", field_html)
    assert match is not None
    return match.group(1)


def _configure_ffmpeg(anki_mw, ffmpeg_config, **overrides: Any) -> None:
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config.update({"ffmpeg_path": ffmpeg_config.ffmpeg_path, **overrides})
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)


def _fake_deep_filter_executable(tmp_path: Path, *, fail: bool = False) -> tuple[Path, Path]:
    log_path = tmp_path / "deep-filter-argv.json"
    script_path = tmp_path / "fake_deep_filter.py"
    script_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import json",
                "import shutil",
                "import sys",
                "from pathlib import Path",
                "",
                f"LOG_PATH = Path({str(log_path)!r})",
                f"FAIL = {fail!r}",
                "",
                "args = sys.argv[1:]",
                "LOG_PATH.write_text(json.dumps(args), encoding='utf-8')",
                "if FAIL:",
                "    sys.stderr.write('fake deep-filter failed')",
                "    raise SystemExit(12)",
                "if '--version' in args:",
                "    print('fake deep-filter 0.0')",
                "    raise SystemExit(0)",
                "try:",
                "    output_dir = Path(args[args.index('-o') + 1])",
                "except (ValueError, IndexError):",
                "    sys.stderr.write('missing output directory')",
                "    raise SystemExit(2)",
                "input_wav = Path(args[-1])",
                "output_dir.mkdir(parents=True, exist_ok=True)",
                "shutil.copyfile(input_wav, output_dir / 'clean.wav')",
            ]
        ),
        encoding="utf-8",
    )
    if os.name == "nt":
        executable = tmp_path / "deep-filter.cmd"
        executable.write_text(
            f'@echo off\n"{sys.executable}" "{script_path}" %*\n',
            encoding="utf-8",
        )
    else:
        executable = tmp_path / "deep-filter"
        executable.write_text(
            "#!/bin/sh\n"
            f"exec {shlex.quote(sys.executable)} {shlex.quote(str(script_path))} \"$@\"\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    return executable, log_path


def _render_direct_deep_filter_reference(
    ffmpeg_config,
    source: Path,
    output_path: Path,
    *,
    post_filter: bool,
) -> None:
    from anki_audio_quick_editor.audio_processor import find_deep_filter

    deep_filter = find_deep_filter("")
    work_dir = output_path.parent / "direct_deep_filter_work"
    input_wav = work_dir / "input_48k_mono.wav"
    output_dir = work_dir / "deep_filter_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-codec:a",
            "pcm_s16le",
            str(input_wav),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    deep_filter_command = [str(deep_filter), "-D"]
    if post_filter:
        deep_filter_command.append("--pf")
    deep_filter_command.extend(["-o", str(output_dir), str(input_wav)])
    subprocess.run(
        deep_filter_command,
        check=True,
        capture_output=True,
        text=True,
    )

    wav_outputs = sorted(output_dir.glob("*.wav"))
    assert len(wav_outputs) == 1
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(wav_outputs[0]),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _button_selector(command: str, ord_: int = 0) -> str:
    return f'.aqe-controls[data-aqe-field-ord="{ord_}"] [data-aqe-command="{command}"]'


def _open_editor(anki_mw, note):
    from aqt.editor import Editor, EditorMode

    parent = QWidget()
    container = QWidget(parent)
    parent.resize(1400, 900)
    parent.show()
    editor = Editor(anki_mw, container, parent, editor_mode=EditorMode.BROWSER)
    editor.set_note(note, hide=False, focusTo=0)
    return editor, parent


def _wait_for_generated_mp3(note, media_dir: Path, previous_name: str, field_index: int = 0) -> str:
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(note.fields[field_index])) != previous_name
            and "__aqe_" in filename
            and filename.endswith(".mp3")
            and (media_dir / filename).is_file()
        ),
        timeout=10.0,
        message="Editor did not replace the field with a newly generated MP3",
    )
    return _sound_filename(note.fields[field_index])


def _click_and_wait_for_new_file(
    editor,
    note,
    media_dir: Path,
    command: str,
    previous_name: str,
    field_index: int = 0,
) -> str:
    click_selector(editor.web, _button_selector(command, field_index), timeout=5.0)
    return _wait_for_generated_mp3(note, media_dir, previous_name, field_index)


def _processing_status_js() -> str:
    return """
    (() => {
      const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status');
      return status ? { text: status.textContent, title: status.title, kind: status.dataset.kind || "" } : null;
    })()
    """


def _visualizer_js(ord_: int = 0) -> str:
    return """
    (() => {
      const ord = __ORD__;
      const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
      if (!visualizer) return null;
      const labels = Array.from(visualizer.querySelectorAll('.aqe-hz-label')).map((node) => node.textContent);
      return {
        active: visualizer.dataset.graphActive === "true",
        busy: visualizer.dataset.graphBusy === "true",
        hidden: visualizer.hidden,
        durationMs: Number(visualizer.dataset.durationMs || "0"),
        sourceFilename: visualizer.dataset.sourceFilename || "",
        analyzerName: visualizer.dataset.analyzerName || "",
        anchorMs: Number(visualizer.dataset.anchorMs || "0"),
        cursorMs: Number(visualizer.dataset.cursorMs || "0"),
        progressMs: Number(visualizer.dataset.progressMs || "0"),
        resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
        intensity: visualizer.querySelector('.aqe-intensity')?.getAttribute('d') || "",
        pitchPaths: visualizer.querySelectorAll('.aqe-pitch-path').length,
        xAxisLabels: Array.from(visualizer.querySelectorAll('.aqe-x-label')).map((node) => node.textContent),
        labels,
        cursorX: visualizer.querySelector('.aqe-cursor')?.getAttribute('x1') || "",
        status: visualizer.querySelector('.aqe-visualizer-status')?.textContent || "",
        statusKind: visualizer.querySelector('.aqe-visualizer-status')?.dataset.kind || "",
        graphButtonLabel: document.querySelector(`[data-testid="aqe-button-${ord}-graph"]`)?.textContent || "",
        playButtonLabel: document.querySelector(`[data-testid="aqe-button-${ord}-play"]`)?.textContent || "",
        allButtonsDisabled: Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled),
      };
    })()
    """.replace("__ORD__", json.dumps(ord_))


def _wait_for_visualizer_track(editor, predicate=lambda track: True, timeout: float = 10.0, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _visualizer_js(ord_),
        lambda track: track is not None
        and track["durationMs"] > 0
        and track["allButtonsDisabled"] is False
        and predicate(track),
        timeout=timeout,
    )


def _graph_state_js(ord_: int = 0) -> str:
    return f"window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null"


def _click_graph_and_wait(editor, predicate=lambda track: True, ord_: int = 0, timeout: float = 10.0):
    selector = f'[data-testid="aqe-button-{ord_}-graph"]'
    wait_for_selector(editor.web, selector, timeout=5.0)
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const button = document.querySelector({json.dumps(selector)});
          if (!button) return null;
          button.click();
          return window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null;
        }})()
        """,
        lambda state: state is not None and state["active"] is True,
        timeout=5.0,
    )
    return _wait_for_visualizer_track(editor, predicate, timeout=timeout, ord_=ord_)


def _drag_cursor_to_ratio(editor, ratio: float, ord_: int = 0) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const ord = __ORD__;
          const ratio = __RATIO__;
          const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"] .aqe-visualizer-svg`);
          const rect = svg.getBoundingClientRect();
          const plot = { width: 620, left: 44, right: 10 };
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const x = plotLeft + plotWidth * ratio;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 20, bubbles: true }));
          window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 20, bubbles: true }));
        })()
        """.replace("__ORD__", json.dumps(ord_)).replace("__RATIO__", json.dumps(ratio)),
    )


def _generate_tone_silence_tone(ffmpeg_config, path: Path) -> None:
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=0.4",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono:d=0.45",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=330:duration=0.4",
            "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
            "-map",
            "[out]",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _generate_language_contour_for_e2e(path: Path, spec_name: str) -> None:
    require_praat_and_ffmpeg()
    generate_praat_vowel_fixture(path, LANGUAGE_CONTOUR_SPECS[spec_name])


def _rendered_pitch_points_js(ord_: int = 0) -> str:
    return """
    (() => {
      const ord = __ORD__;
      const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
      if (!visualizer) return null;
      const durationMs = Number(visualizer.dataset.durationMs || "0");
      const plot = { width: 620, left: 44, right: 10 };
      const plotWidth = plot.width - plot.left - plot.right;
      const points = [];
      for (const path of visualizer.querySelectorAll(".aqe-pitch-path")) {
        const values = (path.getAttribute("d") || "").match(/-?\\d+(?:\\.\\d+)?/g) || [];
        for (let index = 0; index + 1 < values.length; index += 2) {
          const x = Number(values[index]);
          const y = Number(values[index + 1]);
          const ms = ((x - plot.left) / plotWidth) * durationMs;
          points.push({ ms, y });
        }
      }
      return {
        durationMs,
        paths: visualizer.querySelectorAll(".aqe-pitch-path").length,
        points
      };
    })()
    """.replace("__ORD__", json.dumps(ord_))


def _median_rendered_y(rendered: dict, window: ContourWindow) -> float:
    values = [
        point["y"]
        for point in rendered["points"]
        if window.start_ms <= point["ms"] <= window.end_ms
    ]
    return median(values)


@contextmanager
def _language_contour_editor(anki_mw, ffmpeg_config, spec_name: str):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"editor_{spec_name}.wav"
    _generate_language_contour_for_e2e(source, spec_name)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note)
    try:
        yield editor, parent, source, LANGUAGE_CONTOUR_SPECS[spec_name]
    finally:
        editor.set_note(None)
        parent.close()


def _rendered_language_contour(editor, source_name: str) -> dict:
    _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source_name)
    return wait_for_js_condition(
        editor.web,
        _rendered_pitch_points_js(),
        lambda value: value is not None and value["paths"] > 0 and bool(value["points"]),
        timeout=5.0,
    )


def test_each_processing_button_updates_field_to_new_real_audio(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_each_button_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: all(
                command not in commands
                for command in (
                    "aqe:save",
                    "aqe:cancel",
                    "aqe:untrim-left",
                    "aqe:untrim-right",
                )
            ),
            timeout=5.0,
        )
        assert wait_for_js_condition(
            editor.web,
            """
            Array.from(document.querySelectorAll('.aqe-button'))
              .map((node) => node.textContent.trim())
            """,
            lambda labels: labels
            == [
                "Play",
                "Graph",
                "Folder",
                "-L",
                "-R",
                "Trim Silence",
                "Remove Pauses",
                "Sidon",
                "Remove noise",
                "Slower",
                "Faster",
                "Volume -",
                "Volume +",
                "Undo",
            ],
            timeout=5.0,
        )

        previous_name = source.name
        generated_names: list[str] = []
        for command in (
            "aqe:trim-left",
            "aqe:trim-right",
            "aqe:slower",
            "aqe:faster",
            "aqe:volume-down",
            "aqe:volume-up",
            "aqe:trim-silence",
            "aqe:remove-pauses",
        ):
            wait_for_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _click_and_wait_for_new_file(editor, note, media_dir, command, previous_name)
            generated_names.append(previous_name)

        assert len(generated_names) == len(set(generated_names))
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(media_dir / generated_names[0], ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        )
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


def test_remove_noise_button_runs_deep_filter_and_is_undoable(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_remove_noise_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    original_bytes = source.read_bytes()
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_path = media_dir / generated_name
        assert generated_path.is_file()
        assert generated_name.endswith(".mp3")
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(generated_path, ffmpeg_config) > 0
        assert abs(probe_duration_ms(generated_path, ffmpeg_config) - 1200) < 250

        deep_filter_args = json.loads(deep_filter_log.read_text(encoding="utf-8"))
        assert "-D" in deep_filter_args
        assert "--pf" in deep_filter_args
        assert "-o" in deep_filter_args
        output_dir = Path(deep_filter_args[deep_filter_args.index("-o") + 1])
        assert output_dir.name == "deep_filter_output"
        assert Path(deep_filter_args[-1]).name == "input_48k_mono.wav"

        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo did not restore the original audio reference after noise removal",
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_remove_noise_button_matches_direct_deep_filter_output(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    sample_path = Path(
        "/Users/iuriikatkov/Library/Application Support/Anki2/main2/collection.media/3d8ca69aee6.mp3"
    )
    if not sample_path.is_file():
        pytest.skip(f"Local DeepFilterNet sample is unavailable: {sample_path}")

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / sample_path.name
    shutil.copyfile(sample_path, source)
    direct_output = tmp_path / "3d8ca69aee6_direct_deep_filter.mp3"
    _render_direct_deep_filter_reference(
        ffmpeg_config,
        source,
        direct_output,
        post_filter=True,
    )

    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path="",
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        generated_path = media_dir / generated_name

        ui_bytes = generated_path.read_bytes()
        direct_bytes = direct_output.read_bytes()
        assert ui_bytes == direct_bytes, (
            "Remove noise button output differs from direct DeepFilterNet output: "
            f"ui={generated_path} ({len(ui_bytes)} bytes), "
            f"direct={direct_output} ({len(direct_bytes)} bytes)"
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_remove_noise_failure_leaves_note_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_remove_noise_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    original_field = f"Prompt [sound:{source.name}]"
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path, fail=True)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=10.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None
            and value["kind"] == "error"
            and "fake deep-filter failed" in value["text"],
            timeout=10.0,
        )

        assert status["title"] == ""
        assert note.fields[0] == original_field
        assert _sound_filename(note.fields[0]) == source.name
        assert json.loads(deep_filter_log.read_text(encoding="utf-8"))[-1].endswith(
            "input_48k_mono.wav"
        )
        assert not list(media_dir.glob("editor_remove_noise_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()


def test_sidon_failure_shows_support_hint_without_mutating_note(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_sidon_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    original_field = f"Prompt [sound:{source.name}]"
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_sidon_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("Sidon speech restoration failed.")
        ),
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:sidon"), timeout=10.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None
            and value["kind"] == "error"
            and "Sidon speech restoration failed." in value["text"]
            and "Open Settings > Diagnostics to copy logs for the developer." in value["text"],
            timeout=10.0,
        )

        assert status["title"] == ""
        assert note.fields[0] == original_field
        assert _sound_filename(note.fields[0]) == source.name
        assert not list(media_dir.glob("editor_sidon_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_renders_pitch_intensity_labels_and_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        initial = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )
        assert initial["active"] is False
        assert initial["hidden"] is True
        assert initial["graphButtonLabel"] == "Graph"

        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
        )

        assert track["intensity"].startswith("M ")
        assert len(track["labels"]) == 2
        assert all(label.endswith(" Hz") for label in track["labels"])
        assert track["cursorX"]
        assert track["graphButtonLabel"] == "Redraw"
        assert any(label.endswith("ms") for label in track["xAxisLabels"])
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_uses_second_axis_for_long_clip(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_long_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=14.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        assert track["durationMs"] >= 13_500
        assert any(label.endswith("s") for label in track["xAxisLabels"])
        assert not any(label.endswith("ms") for label in track["xAxisLabels"])
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_redraw_resets_after_audio_edit_when_active(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_redraw_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )
        track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        assert track["graphButtonLabel"] == "Redraw"
        assert track["progressMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_hides_when_browser_editor_switches_to_another_note(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    first_source = media_dir / "editor_switch_note_one.wav"
    second_source = media_dir / "editor_switch_note_two.wav"
    generate_tone(ffmpeg_config, first_source, duration_s=1.0)
    generate_tone(ffmpeg_config, second_source, duration_s=1.0)
    first_note = _basic_audio_note(anki_mw, first_source.name)
    second_note = _basic_audio_note(anki_mw, second_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, first_note)
    try:
        first_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == first_source.name,
        )
        assert first_track["hidden"] is False

        editor.set_note(second_note, hide=False, focusTo=0)
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        reset_state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["hidden"] is True
            and value["active"] is False
            and value["hasTrack"] is False
            and value["sourceFilename"] == ""
            and value["graphButtonLabel"] == "Graph",
            timeout=10.0,
        )

        assert reset_state["hidden"] is True
        assert reset_state["sourceFilename"] == ""

        second_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == second_source.name,
        )
        assert second_track["sourceFilename"] == second_source.name
    finally:
        editor.set_note(None)
        parent.close()


def test_redraw_button_resets_cursor_and_reanalyzes_current_clip(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_redraw_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(editor.web, "window.__aqeSetCursorForTest(0, 1500, false)")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["cursorMs"] == 1500,
            timeout=5.0,
        )
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        assert track["graphButtonLabel"] == "Redraw"
    finally:
        editor.set_note(None)
        parent.close()


def test_cursor_normalization_matches_pointer_position_at_multiple_widths(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_width_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        for width in (640, 1000, 1400):
            parent.resize(width, 900)
            resize_deadline = time.monotonic() + 0.1
            wait_for_condition(
                lambda deadline=resize_deadline: time.monotonic() >= deadline,
                timeout=1.0,
            )
            error = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const ord = 0;
                  const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
                  if (!svg || !window.__aqeSetCursorByClientXForTest) return 999;
                  const rect = svg.getBoundingClientRect();
                  const targetX = rect.left + rect.width * 0.73;
                  const result = window.__aqeSetCursorByClientXForTest(ord, targetX, false);
                  if (!result || !result.bounds) return 999;
                  const cursorX = Number(document.querySelector('[data-testid="aqe-cursor-0"]').getAttribute('x1'));
                  const pixelX = result.bounds.left + ((cursorX - 44) / 566) * result.bounds.width;
                  return Math.abs(pixelX - targetX);
                })()
                """,
                lambda value: isinstance(value, (int, float)) and value < 4,
                timeout=5.0,
            )
            assert error < 4
    finally:
        editor.set_note(None)
        parent.close()


def test_cursor_drag_updates_session_and_play_uses_playback_segment(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
              const rect = svg.getBoundingClientRect();
              const EventCtor = window.PointerEvent || window.MouseEvent;
              const x = rect.left + rect.width * 0.65;
              svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 20, bubbles: true }));
              window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 20, bubbles: true }));
            })()
            """,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.cursor_ms >= 1000
            ),
            timeout=5.0,
            message="Dragging the visualizer cursor did not update the editor session",
        )
        track = _wait_for_visualizer_track(editor, lambda value: value["cursorMs"] >= 1000)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: playback.current is not None,
                timeout=5.0,
                message="Playback did not start from the selected cursor segment",
            )
            progressed = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] > track["cursorMs"] + 120,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            paused_progress = paused["progressMs"]
            pause_deadline = time.monotonic() + 0.35
            wait_for_condition(
                lambda: time.monotonic() >= pause_deadline,
                timeout=1.0,
                message="short playback pause wait failed",
            )
            frozen = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None,
                timeout=2.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] > paused_progress + 120,
                timeout=5.0,
            )

        assert playback.current is not None
        _assert_interval(
            playback.current,
            round(track["cursorMs"]),
            expected_end_ms=round(track["durationMs"]),
        )
        assert playback.current.seek_calls == []
        assert progressed["playButtonLabel"] == "Pause"
        assert abs(frozen["progressMs"] - paused_progress) < 80
        assert playback.toggle_count >= 2
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_to_70_percent_play_records_70_to_100_interval(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_70_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _drag_cursor_to_ratio(editor, 0.70)
        dragged = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and 650 <= state["anchorMs"] <= 750,
            timeout=5.0,
        )
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: playback.current is not None,
                timeout=5.0,
                message="Playback did not record an effective interval from the dragged cursor",
            )

        assert playback.current is not None
        _assert_interval(
            playback.current,
            round(track["durationMs"] * 0.70),
            expected_end_ms=round(track["durationMs"]),
        )
        assert playback.current.seek_calls == []
        assert 220 <= playback.current.duration_ms <= 380
        assert "__from_" in playback.current.filename
        assert playback.current.start_ms > playback.current.duration_ms * 0.50
        assert playback.current.start_ms != 0
        assert dragged["cursorMs"] == dragged["anchorMs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_play_from_zero_uses_original_file_without_segment(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_play_zero_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with _record_fake_playback(media_dir, {source.name: round(track["durationMs"])}) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: playback.current is not None,
                timeout=5.0,
                message="Playback from zero did not start",
            )

        assert playback.current is not None
        _assert_interval(playback.current, 0, expected_end_ms=round(track["durationMs"]))
        assert playback.current.filename == source.name
        assert "__from_" not in playback.current.filename
        assert playback.current.seek_calls == []
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_to_70_percent_plays_audible_70_to_100_without_seek(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_70_delayed_seek_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _drag_cursor_to_ratio(editor, 0.70)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and 650 <= state["anchorMs"] <= 750,
            timeout=5.0,
        )
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            apply_immediate_seek=False,
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: playback.current is not None,
                timeout=5.0,
                message="Playback did not start the selected cursor segment",
            )
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "stopped",
                timeout=5.0,
            )

        assert playback.current is not None
        _assert_interval(
            playback.current,
            round(track["durationMs"] * 0.70),
            expected_end_ms=round(track["durationMs"]),
        )
        assert playback.current.audible_start_ms >= round(track["durationMs"] * 0.70)
        assert playback.current.seek_calls == []
        assert 220 <= playback.current.duration_ms <= 380
    finally:
        editor.set_note(None)
        parent.close()


def test_pause_drag_then_play_restarts_from_dragged_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_pause_drag_play_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] >= 500,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            _drag_cursor_to_ratio(editor, 0.40)
            dragged = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["resumeRequiresRestart"] is True
                and 700 <= state["cursorMs"] <= 900,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: len(playback.attempts) >= 2 and playback.current is not None,
                timeout=5.0,
                message="Playback did not restart from the cursor selected while paused",
            )

        assert playback.current is not None
        _assert_interval(
            playback.current,
            dragged["anchorMs"],
            expected_end_ms=round(track["durationMs"]),
        )
        assert playback.current.seek_calls == []
        assert dragged["anchorMs"] == dragged["cursorMs"]
        assert playback.toggle_count == 1
    finally:
        editor.set_note(None)
        parent.close()


def test_playback_completion_clears_status_and_returns_cursor_to_anchor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_playback_finish_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(editor.web, "window.__aqeSetCursorForTest(0, 300, false)")
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: playback.current is not None,
                timeout=5.0,
                message="Playback did not start from the selected anchor segment",
            )
            finished = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
                  const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status')?.textContent || "";
                  return state ? { ...state, status } : null;
                })()
                """,
                lambda state: state is not None
                and state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play"
                and state["status"] == ""
                and state["cursorMs"] == 300,
                timeout=5.0,
            )

        assert finished["anchorMs"] == 300
        assert len(playback.attempts) == 1
        _assert_interval(playback.attempts[0], 300, expected_end_ms=round(track["durationMs"]))
        assert playback.attempts[0].seek_calls == []
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_while_playing_restarts_playback_from_released_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_while_playing_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["playbackState"] == "playing"
                and state["progressMs"] >= 250,
                timeout=5.0,
            )
            _drag_cursor_to_ratio(editor, 0.75)
            restarted = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["playbackState"] == "playing"
                and 1400 <= state["anchorMs"] <= 1600,
                timeout=5.0,
            )
            wait_for_condition(
                lambda: len(playback.attempts) >= 2 and playback.current is not None,
                timeout=5.0,
                message="Dragging while playing did not restart playback from release point",
            )

        assert playback.current is not None
        _assert_interval(
            playback.current,
            restarted["anchorMs"],
            expected_end_ms=round(track["durationMs"]),
        )
        assert playback.current.seek_calls == []
        assert restarted["playButtonLabel"] == "Pause"
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_splits_internal_silence_into_separate_pitch_paths(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_tone_silence_tone.wav"
    _generate_tone_silence_tone(ffmpeg_config, source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] >= 2,
        )

        assert track["pitchPaths"] >= 2
        assert track["intensity"].startswith("M ")
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.praat
def test_visualizer_shows_japanese_nakadaka_internal_pitch_drop(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "ja_nakadaka_4mora_1_5s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        pre_drop_y = _median_rendered_y(rendered, window_named(spec, "pre_drop_high"))
        post_drop_y = _median_rendered_y(rendered, window_named(spec, "post_drop_low"))
        assert post_drop_y - pre_drop_y >= 16


@pytest.mark.praat
def test_visualizer_shows_japanese_odaka_drop_on_particle(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "ja_odaka_3mora_particle_1_6s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        word_y = _median_rendered_y(rendered, window_named(spec, "word_high"))
        particle_y = _median_rendered_y(rendered, window_named(spec, "particle_low"))
        assert particle_y - word_y >= 16


@pytest.mark.praat
@pytest.mark.parametrize(
    ("spec_name", "earlier_window", "later_window", "direction"),
    [
        ("zh_tone2_rising_0_9s", "early", "late", "rise"),
        ("zh_tone4_falling_0_8s", "early", "late", "fall"),
    ],
)
def test_visualizer_shows_mandarin_tone2_and_tone4_opposite_slopes(
    anki_mw,
    ffmpeg_config,
    spec_name: str,
    earlier_window: str,
    later_window: str,
    direction: str,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, spec_name) as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        earlier_y = _median_rendered_y(rendered, window_named(spec, earlier_window))
        later_y = _median_rendered_y(rendered, window_named(spec, later_window))
        if direction == "rise":
            assert earlier_y - later_y >= 16
        else:
            assert later_y - earlier_y >= 16


@pytest.mark.praat
def test_visualizer_shows_mandarin_tone3_dip(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "zh_tone3_dipping_1_1s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        early_y = _median_rendered_y(rendered, window_named(spec, "early"))
        trough_y = _median_rendered_y(rendered, window_named(spec, "trough"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert trough_y - early_y >= 16
        assert trough_y - late_y >= 16


@pytest.mark.praat
@pytest.mark.parametrize(
    ("spec_name", "earlier_window", "later_window", "direction"),
    [
        ("vi_sac_high_rising_0_9s", "early", "late", "rise"),
        ("vi_huyen_low_falling_0_9s", "early", "late", "fall"),
        ("vi_nang_low_checked_0_8s", "early", "late_low", "fall"),
    ],
)
def test_visualizer_shows_vietnamese_rising_and_falling_tones(
    anki_mw,
    ffmpeg_config,
    spec_name: str,
    earlier_window: str,
    later_window: str,
    direction: str,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, spec_name) as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        earlier_y = _median_rendered_y(rendered, window_named(spec, earlier_window))
        later_y = _median_rendered_y(rendered, window_named(spec, later_window))
        if direction == "rise":
            assert earlier_y - later_y >= 16
        else:
            assert later_y - earlier_y >= 16


@pytest.mark.praat
def test_visualizer_shows_vietnamese_hoi_dip(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "vi_hoi_dipping_1_0s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        early_y = _median_rendered_y(rendered, window_named(spec, "early"))
        trough_y = _median_rendered_y(rendered, window_named(spec, "trough"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert trough_y - early_y >= 16
        assert trough_y - late_y >= 16


@pytest.mark.praat
def test_visualizer_shows_vietnamese_nga_broken_rise(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "vi_nga_broken_rising_1_0s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        pre_break_y = _median_rendered_y(rendered, window_named(spec, "pre_break"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert rendered["paths"] >= 2
        assert pre_break_y - late_y >= 16


def test_silence_visualizer_renders_pitch_gaps_without_crashing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_silence_source.wav"

    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono:d=0.7",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        assert track["intensity"].startswith("M ")
        assert track["pitchPaths"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_failure_is_non_mutating_and_edit_buttons_still_work(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    monkeypatch.setattr(
        "anki_audio_quick_editor.prosody_cache.analyze_prosody",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("visualizer exploded")),
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        wait_for_js_condition(
            editor.web,
            _visualizer_js(),
            lambda value: value is not None
            and value["statusKind"] == "error"
            and "visualizer exploded" in value["status"],
            timeout=10.0,
        )
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        assert generated_name != source.name
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_ffmpeg_command_status_respects_settings_flag(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    hidden_source = media_dir / "editor_hidden_command_source.wav"
    shown_source = media_dir / "editor_shown_command_source.wav"
    generate_tone(ffmpeg_config, hidden_source, duration_s=2.0)
    generate_tone(ffmpeg_config, shown_source, duration_s=2.0)

    hidden_note = _basic_audio_note(anki_mw, hidden_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=False)
    hidden_editor, hidden_parent = _open_editor(anki_mw, hidden_note)
    try:
        wait_for_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        hidden_status = wait_for_js_condition(
            hidden_editor.web,
            _processing_status_js(),
            lambda status: status is not None and status["text"].startswith("Processing with ffmpeg"),
            timeout=5.0,
        )
        assert " -i " not in hidden_status["text"]
        assert hidden_status["title"] == ""
        _wait_for_generated_mp3(hidden_note, media_dir, hidden_source.name)
    finally:
        hidden_editor.set_note(None)
        hidden_parent.close()

    shown_note = _basic_audio_note(anki_mw, shown_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=True)
    shown_editor, shown_parent = _open_editor(anki_mw, shown_note)
    try:
        wait_for_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        shown_status = wait_for_js_condition(
            shown_editor.web,
            _processing_status_js(),
            lambda status: status is not None and " -i " in status["text"],
            timeout=5.0,
        )
        assert shown_status["title"].startswith(ffmpeg_config.ffmpeg_path)
        _wait_for_generated_mp3(shown_note, media_dir, shown_source.name)
    finally:
        shown_editor.set_note(None)
        shown_parent.close()


def test_undo_restores_previous_generated_reference(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda _seconds: None),
            patch.object(av_player, "toggle_pause", lambda: None),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        previous_name = source.name
        generated_names: list[str] = []
        for command in ("aqe:trim-left", "aqe:faster", "aqe:trim-right", "aqe:trim-silence"):
            previous_name = _click_and_wait_for_new_file(
                editor, note, media_dir, command, previous_name
            )
            generated_names.append(previous_name)
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=previous_name: value["sourceFilename"] == expected,
                timeout=10.0,
            )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_names[-2],
            timeout=5.0,
            message="Undo did not restore the previous generated audio reference",
        )
        restored_track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_names[-2],
            timeout=10.0,
        )

        assert len(generated_names) == len(set(generated_names))
        assert restored_track["sourceFilename"] == generated_names[-2]
        assert all((media_dir / name).is_file() for name in generated_names)
    finally:
        editor.set_note(None)
        parent.close()


def test_fast_clicks_are_ignored_while_processing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_fast_click_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        selector = _button_selector("aqe:trim-left")
        wait_for_selector(editor.web, selector, timeout=10.0)
        run_js(
            editor.web,
            f"""
            const button = document.querySelector({json.dumps(selector)});
            for (let i = 0; i < 5; i++) button.click();
            """,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_for_source = list(media_dir.glob("editor_fast_click_source__aqe_*.mp3"))
        assert generated_for_source == [media_dir / generated_name]
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_three_audio_fields_fast_cross_clicks_lock_globally_and_do_not_corrupt_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_three_fields_one.wav",
        media_dir / "editor_three_fields_two.wav",
        media_dir / "editor_three_fields_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left", 0), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:faster", 1), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:trim-right", 2), timeout=10.0)
        locked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-button-0-trim-left"]').click();
              const lockedAfterFirst = Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled);
              const firstButton = document.querySelector('[data-testid="aqe-button-0-trim-left"]');
              const controls = document.querySelector('[data-testid="aqe-controls-0"]');
              const buttonStyle = getComputedStyle(firstButton);
              const controlsStyle = getComputedStyle(controls);
              document.querySelector('[data-testid="aqe-button-1-faster"]').click();
              document.querySelector('[data-testid="aqe-button-2-trim-right"]').click();
              return {
                lockedAfterFirst,
                cursor: buttonStyle.cursor,
                opacity: Number(buttonStyle.opacity),
                borderStyle: controlsStyle.borderTopStyle
              };
            })()
            """,
            lambda value: value is not None and value["lockedAfterFirst"] is True,
            timeout=5.0,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, sources[0].name, field_index=0)
        unlocked = wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["allButtonsDisabled"] is False,
            timeout=5.0,
        )

        assert locked["lockedAfterFirst"] is True
        assert locked["cursor"] == "not-allowed"
        assert locked["opacity"] < 0.7
        assert locked["borderStyle"] == "dashed"
        assert unlocked["allButtonsDisabled"] is False
        assert _sound_filename(note.fields[0]) == generated_name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
        assert list(media_dir.glob("editor_three_fields_one__aqe_*.mp3")) == [media_dir / generated_name]
    finally:
        editor.set_note(None)
        parent.close()


def test_settings_trim_step_controls_editor_button_behavior(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=500)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.left_trim_ms == 500
            ),
            timeout=5.0,
            message="Editor did not use the configured trim step",
        )
        assert probe_duration_ms(media_dir / generated_name, ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        ) - 350
    finally:
        editor.set_note(None)
        parent.close()
