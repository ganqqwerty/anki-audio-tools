"""Tests for injected editor controls bundle wiring."""

from __future__ import annotations

import json
import re

from anki_audio_quick_editor.editor_ui import injection_script


def _embedded_config(script: str) -> dict:
    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    return json.loads(match.group("config"))


def test_injection_script_embeds_audio_field_indices_and_bundle() -> None:
    script = injection_script([1, 3])
    config = _embedded_config(script)

    assert config["audioFieldIndices"] == [1, 3]
    assert config["audioFieldSources"] == {}
    assert config["repeatPlaybackByDefault"] is False
    assert config["showGraphByDefault"] is False
    assert config["splitButtonDefaults"]["repeatPauseSeconds"] == 0.0
    assert config["splitButtonDefaults"]["pitchHumMode"] == "direct"
    assert config["splitButtonDefaults"]["dpdfnetAttnLimitDb"] == 12.0
    assert config["splitButtonDefaults"]["graphVoiceRange"] == "general"
    assert config["splitButtonDefaults"]["graphRecordingCondition"] == "auto"
    assert config["splitButtonDefaults"]["graphSmoothness"] == "very_smooth"
    assert config["splitButtonDefaults"]["graphConnectShortDropoutsMs"] == 240
    assert config["splitButtonDefaults"]["graphVoiceLock"] == "balanced"
    assert "window.__aqeEditorDispose" in script
    assert "aqe:frontend-log" in script
    assert "aqe:show-file" in script
    assert "aqe:volume-down" in script
    assert "aqe:volume-up" in script
    assert "aqe:denoise-standard" in script
    assert "aqe:rnnoise" in script
    assert "aqe:dpdfnet" in script
    assert "aqe:voice-only" in script
    assert "aqe:redo" in script
    assert "aqe:settings" in script
    assert "aqe:save-split-defaults" in script
    assert ("aqe:" + "remove" + "-noise") not in script
    assert "aqe:cancel" not in script


def test_injection_script_embeds_repeat_default() -> None:
    script = injection_script([0], repeat_playback_by_default=True)

    assert _embedded_config(script)["repeatPlaybackByDefault"] is True


def test_injection_script_embeds_show_graph_default() -> None:
    script = injection_script([0], show_graph_by_default=True)

    assert _embedded_config(script)["showGraphByDefault"] is True


def test_injection_script_embeds_audio_field_sources() -> None:
    script = injection_script([0, 2], audio_field_sources={0: "front.wav", 2: "back.mp3"})

    assert '"audioFieldSources": {"0": "front.wav", "2": "back.mp3"}' in script


def test_injection_script_embeds_split_button_defaults() -> None:
    script = injection_script(
        [0],
        split_button_defaults={
            "trimStepMs": 250,
            "volumeStepDb": 2.5,
            "speedStep": 0.1,
            "repeatPauseSeconds": 2.0,
            "pauseAggressiveness": "normal",
            "denoiseAlgorithm": "standard",
            "pitchHumMode": "pitch_tier",
            "dpdfnetAttnLimitDb": 18.0,
        },
    )

    assert _embedded_config(script)["splitButtonDefaults"] == {
        "trimStepMs": 250,
        "volumeStepDb": 2.5,
        "speedStep": 0.1,
        "repeatPauseSeconds": 2.0,
        "pauseAggressiveness": "normal",
        "denoiseAlgorithm": "standard",
        "pitchHumMode": "pitch_tier",
        "dpdfnetAttnLimitDb": 18.0,
    }


def test_injection_script_keeps_python_window_contract() -> None:
    script = injection_script([0])

    assert "__aqeSetBusy" in script
    assert "__aqeSetStatus" in script
    assert "__aqeSetVisualizer" in script
    assert "__aqeSetVisualizerStatus" in script
    assert "__aqeGetPlaybackRequest" in script
    assert "__aqeGetCursorIntent" in script
    assert "__aqePopFrontendLog" in script
    assert "__aqePopPendingGraphAnalysisRequest" in script
    assert "__aqeScan" in script
    assert "__aqeGraphStateForTest" in script


def test_injection_script_injects_editor_css() -> None:
    script = injection_script([0])

    assert "const styleId = \"aqe-inline-style\";" in script
    assert ".aqe-controls" in script
    assert ".aqe-button:disabled" in script
    assert "data-busy=true" in script
    assert "border-style:dashed" in script
    assert "filter:drop-shadow" in script
    assert ".aqe-selection-draft" in script
    assert "filter:none" in script
    assert "stroke-dasharray:none" in script
    assert "stroke-opacity:.65" in script
    assert "aqe-spin" in script
