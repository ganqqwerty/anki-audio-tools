"""E2E stress coverage for repeat playback across generated editor transforms."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pytest

from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _set_full_time_viewport,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_region_loop_helpers import _set_repeat, _shift_drag_region
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_editor_real_media_repeat_workflow import (
    MEDIA_FIXTURE_DIR,
    _install_real_audio_probe,
    _real_audio_probe_js,
    _stop_real_audio_playback,
    _trusted_click_selector,
    _wait_for_real_audio_ready,
    _wait_for_real_html_playback,
)

pytestmark = pytest.mark.trusted_input

SourceKind = Literal["forvo-ogg", "hidden-tone", "graph-tone"]


@dataclass(frozen=True)
class TransformStressScenario:
    name: str
    source_kind: SourceKind
    source_filename: str
    commands: tuple[str, ...]
    duration_s: float = 2.4
    select_middle_region: bool = False


SCENARIOS = (
    TransformStressScenario(
        name="hidden-speed-volume",
        source_kind="forvo-ogg",
        source_filename="editor_stress_hidden_forvo.ogg",
        commands=(
            "aqe:slower",
            "aqe:faster",
            "aqe:volume-up",
            "aqe:volume-down",
            "aqe:slower",
            "aqe:faster",
        ),
    ),
    TransformStressScenario(
        name="graph-speed-volume",
        source_kind="graph-tone",
        source_filename="editor_stress_graph_source.mp3",
        commands=(
            "aqe:faster",
            "aqe:volume-up",
            "aqe:slower",
            "aqe:volume-down",
            "aqe:faster",
        ),
    ),
    TransformStressScenario(
        name="selection-delete-rest",
        source_kind="graph-tone",
        source_filename="editor_stress_delete_rest_source.mp3",
        commands=(
            "aqe:delete-rest",
            "aqe:faster",
            "aqe:volume-up",
            "aqe:slower",
            "aqe:volume-down",
        ),
        select_middle_region=True,
    ),
    TransformStressScenario(
        name="selection-delete-selection",
        source_kind="graph-tone",
        source_filename="editor_stress_delete_selection_source.mp3",
        commands=(
            "aqe:delete-selection",
            "aqe:slower",
            "aqe:volume-down",
            "aqe:faster",
            "aqe:volume-up",
        ),
        select_middle_region=True,
    ),
    TransformStressScenario(
        name="heavy-processing",
        source_kind="hidden-tone",
        source_filename="editor_stress_processing_source.wav",
        commands=(
            "aqe:convert",
            "aqe:remove-pauses",
            "aqe:reduce-size",
            "aqe:volume-up",
            "aqe:faster",
        ),
        duration_s=2.0,
    ),
    TransformStressScenario(
        name="seeded-shuffle",
        source_kind="hidden-tone",
        source_filename="editor_stress_seeded_shuffle_source.wav",
        commands=(
            "aqe:convert",
            "aqe:slower",
            "aqe:volume-up",
            "aqe:remove-pauses",
            "aqe:faster",
            "aqe:reduce-size",
            "aqe:volume-down",
            "aqe:slower",
            "aqe:volume-up",
        ),
        duration_s=2.2,
    ),
)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[scenario.name for scenario in SCENARIOS])
def test_real_repeat_survives_mixed_generated_transform_stress(
    anki_mw,
    ffmpeg_config,
    scenario: TransformStressScenario,
) -> None:
    media_dir, source, note, editor, parent = _open_stress_editor(
        anki_mw,
        ffmpeg_config,
        scenario,
    )
    try:
        if scenario.select_middle_region:
            _select_middle_region(editor)
        observation = _run_command_sequence(
            editor,
            note,
            media_dir,
            source.name,
            scenario.commands,
            scenario.name,
        )
        _assert_generated_repeat_invariants(observation)
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def _open_stress_editor(anki_mw, ffmpeg_config, scenario: TransformStressScenario):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / scenario.source_filename
    if scenario.source_kind == "forvo-ogg":
        shutil.copy2(MEDIA_FIXTURE_DIR / "forvo_Vertrag.ogg", source)
    elif scenario.source_kind == "hidden-tone":
        generate_tone(ffmpeg_config, source, duration_s=scenario.duration_s)
    else:
        _generate_high_bitrate_mp3(ffmpeg_config, source, duration_s=scenario.duration_s)

    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        output_format="mp3",
        pause_aggressiveness="normal",
        repeat_playback_by_default=False,
        size_reduction_mode="normal",
    )
    editor, parent = _open_editor(anki_mw, note)
    try:
        if scenario.source_kind == "graph-tone":
            _click_graph_and_wait(
                editor,
                lambda state: state["sourceFilename"] == source.name,
                timeout=30.0,
            )
            _set_full_time_viewport(editor)
        else:
            wait_for_selector(editor.web, _button_selector("aqe:play"), timeout=10.0)
        _start_repeat_playback(editor)
    except Exception:
        editor.set_note(None)
        parent.close()
        raise
    return media_dir, source, note, editor, parent


def _start_repeat_playback(editor) -> None:
    _wait_for_real_audio_ready(editor)
    _install_real_audio_probe(editor)
    _set_repeat(editor, True)
    _trusted_click_selector(editor, _button_selector("aqe:play"))
    _wait_for_real_html_playback(editor)


def _select_middle_region(editor) -> None:
    _shift_drag_region(editor, 0.25, 0.625)
    wait_for_js_condition(
        editor.web,
        _graph_state_js(),
        lambda state: state is not None
        and state["selectionActive"] is True
        and state["regionDeleteButtonDisabled"] is False
        and state["regionDeleteRestButtonDisabled"] is False,
        timeout=5.0,
    )


def _run_command_sequence(
    editor,
    note,
    media_dir: Path,
    source_name: str,
    commands: tuple[str, ...],
    scenario_name: str,
) -> dict[str, Any]:
    initial = _probe(editor)
    observation: dict[str, Any] = {
        "commands": [],
        "initialPlayCalls": initial["playCalls"],
        "scenario": scenario_name,
        "source": source_name,
    }
    previous_name = _sound_filename(note.fields[0])
    for command in commands:
        before = _probe(editor)
        click_selector(editor.web, _button_selector(command), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        observation["commands"].append(
            {
                "command": command,
                "generated": generated_name,
                "playCallsBeforeCommand": before["playCalls"],
                "sourceBeforeCommand": before["state"]["sourceFilename"],
            }
        )
        previous_name = generated_name

    observation["final"] = _observe_repeats_after_generated_start(editor, previous_name)
    return observation


def _observe_repeats_after_generated_start(editor, generated_name: str) -> dict[str, Any]:
    started = _wait_for_generated_repeat_state(
        editor,
        generated_name,
        lambda value: value["currentTimeMs"] >= 80,
        timeout=12.0,
    )
    target_play_calls = started["playCalls"] + 3
    timeout = max(10.0, (started["durationMs"] / 1000.0) * 4.0 + 8.0)
    observed = _wait_for_generated_repeat_state(
        editor,
        generated_name,
        lambda value: value["playCalls"] >= target_play_calls,
        timeout=timeout,
    )
    return _summarize_final_repeat_observation(
        generated_name,
        started["playCalls"],
        observed,
    )


def _wait_for_generated_repeat_state(
    editor,
    generated_name: str,
    extra_predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout: float,
) -> dict[str, Any]:
    return wait_for_js_condition(
        editor.web,
        _real_audio_probe_js(),
        lambda value: value is not None
        and value["state"]["sourceFilename"] == generated_name
        and generated_name in value["src"]
        and value["state"]["repeatEnabled"] is True
        and value["state"]["playbackState"] == "playing"
        and value["state"]["playbackEngine"] == "html"
        and value["state"]["progressClockMode"] == "audio"
        and value["paused"] is False
        and extra_predicate(value),
        timeout=timeout,
    )


def _summarize_final_repeat_observation(
    generated_name: str,
    baseline_play_calls: int,
    observed: dict[str, Any],
) -> dict[str, Any]:
    return {
        "audioErrorCode": observed["errorCode"],
        "backendPlaybackRequests": observed["backendPlaybackRequests"],
        "currentTimeMs": observed["currentTimeMs"],
        "durationMs": observed["durationMs"],
        "generated": generated_name,
        "nativePlaybackRequests": observed["nativePlaybackRequests"],
        "paused": observed["paused"],
        "playCallsAtFirstGeneratedStart": baseline_play_calls,
        "playCallsObserved": observed["playCalls"],
        "repeatRestartsAfterGeneratedStart": observed["playCalls"] - baseline_play_calls,
        "state": observed["state"],
    }


def _assert_generated_repeat_invariants(observation: dict[str, Any]) -> None:
    final = observation["final"]
    expected = {
        "audioErrorCode": None,
        "backendPlaybackRequests": [],
        "nativePlaybackRequests": [],
        "paused": False,
        "repeatRestartsAfterGeneratedStart": 3,
    }
    actual = {key: final[key] for key in expected}
    actual.update(
        {
            "playbackEngine": final["state"]["playbackEngine"],
            "playbackState": final["state"]["playbackState"],
            "progressClockMode": final["state"]["progressClockMode"],
            "repeatEnabled": final["state"]["repeatEnabled"],
            "sourceFilename": final["state"]["sourceFilename"],
        }
    )
    expected.update(
        {
            "playbackEngine": "html",
            "playbackState": "playing",
            "progressClockMode": "audio",
            "repeatEnabled": True,
            "sourceFilename": final["generated"],
        }
    )
    assert actual == expected, json.dumps(observation, indent=2, sort_keys=True)


def _probe(editor) -> dict[str, Any]:
    return wait_for_js_condition(
        editor.web,
        _real_audio_probe_js(),
        lambda value: value is not None,
        timeout=5.0,
    )
