"""Tests for injected editor controls."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from anki_audio_quick_editor.editor_ui import injection_script


def test_injection_script_embeds_audio_field_indices() -> None:
    script = injection_script([1, 3])

    assert "const audioFieldIndices = new Set([1, 3]);" in script
    assert '.field-container[data-index="' in script
    assert "button.dataset.aqeCommand = command;" in script
    assert '"aqe:undo"' in script
    assert '"aqe:show-file"' in script
    assert 'pycmd("aqe:analyze");' in script
    assert 'pycmd("aqe:set-cursor");' in script
    assert '"aqe:save"' not in script
    assert '"aqe:cancel"' not in script
    assert '"aqe:untrim-left"' not in script
    assert '"aqe:untrim-right"' not in script
    assert 'makeButton("+L"' not in script
    assert 'makeButton("+R"' not in script
    assert "window.__aqeSetBusy = setControlsBusy;" in script
    assert "window.__aqeSetVisualizer =" in script
    assert "class=\"aqe-visualizer-svg\"" in script
    assert 'class="aqe-spinner"' in script
    assert "Hz`" in script
    assert "button.disabled = !!busy;" in script
    assert "status.title = command || \"\";" in script
    assert 'pycmd("focus:" + ord);' in script
    assert 'makeButton("Folder", "Show current audio file in folder", "aqe:show-file"' in script


def test_graph_is_user_requested_and_redraws_after_active_edits() -> None:
    script = injection_script([0])

    assert 'makeButton("Graph", "Analyze and show pitch/intensity graph", "aqe:analyze"' in script
    assert "requestGraph(ord, true);" in script
    assert "rememberGraphRedrawIfActive" not in script
    assert "redrawAfterEditKey" not in script
    assert "sessionStorage" not in script
    assert "function audioSourceForNode(node)" in script
    assert "const existingControls = Array.from" in script
    assert "controls.dataset.aqeSourceFilename === sourceFilename" in script
    assert "existingControls.forEach((controls) => controls.remove());" in script
    assert "controls.dataset.aqeSourceFilename = sourceFilename;" in script
    assert 'document.querySelectorAll(".aqe-controls").forEach((node) => node.remove());' not in script
    assert "requestAnalysis" not in script


def test_visualizer_has_progress_axis_and_lock_test_hooks() -> None:
    script = injection_script([0])

    assert "durationMs < 2000" in script
    assert "return `${Math.round(ms)} ms`;" in script
    assert "setControlsBusy(ord, true, \"Analyzing...\", \"\");" in script
    assert 'visualizer.dataset.hasTrack = "false";' in script
    assert 'visualizer.dataset.hasTrack = "true";' in script
    assert "spinner.hidden = !processing;" in script
    assert "spinnerVisible" in script
    assert "document.body.dataset.aqeBusy" in script
    assert "window.__aqeGraphStateForTest" in script
    assert "window.__aqeSetCursorByClientXForTest" in script
    assert "window.__aqeSetPlaybackState" in script
    assert "window.requestAnimationFrame(tick)" in script
    assert 'setControlsBusy(ord, false, "", "");' in script


def test_disabled_button_styling_is_visible_without_color() -> None:
    script = injection_script([0])

    assert ".aqe-controls[data-busy=" in script
    assert "border-style: dashed;" in script
    assert ".aqe-button:disabled" in script
    assert "cursor: not-allowed;" in script
    assert "opacity: 0.45;" in script


def test_visualizer_layout_spinner_and_dark_theme_safe_styles_are_injected() -> None:
    script = injection_script([0])

    assert "color-scheme: light dark;" in script
    assert "background: transparent;" in script
    assert "color: inherit;" in script
    assert "flex: 0 0 100%;" in script
    assert "width: min(760px, 100%);" in script
    assert '.aqe-visualizer[data-has-track=\\"false\\"] .aqe-visualizer-svg' in script
    assert '.aqe-visualizer[data-has-track=\\"false\\"] .aqe-cursor-label' in script
    assert ".aqe-spinner" in script
    assert "animation: aqe-spin 800ms linear infinite;" in script
    assert "@keyframes aqe-spin" in script


def test_playback_finish_and_cursor_drag_intents_are_injected() -> None:
    script = injection_script([0])

    assert 'pycmd("aqe:play-ended");' in script
    assert 'clearStatus(ord);' in script
    assert 'setCursor(visualizer, anchorMs, false, { updateAnchor: false });' in script
    assert 'visualizer.dataset.resumeRequiresRestart = "true";' in script
    assert 'const restartPlayback = previousPlaybackState === "playing";' in script
    assert "window.__aqeGetCursorIntent" in script
    assert "anchorMs" in script


def test_visualizer_pitch_paths_split_at_unvoiced_points() -> None:
    paths = _run_visualizer_helper_js(
        """
        const pitchGroup = new FakeNode("g");
        const visualizer = {
          querySelector(selector) {
            if (selector === ".aqe-pitch") return pitchGroup;
            throw new Error(`Unexpected selector: ${selector}`);
          }
        };
        drawPitch(visualizer, {
          durationMs: 1000,
          pitchMinHz: 100,
          pitchMaxHz: 300,
          points: [
            [0, 120, 0.5, true],
            [100, 140, 0.5, true],
            [200, null, 0.0, false],
            [300, 240, 0.5, true],
            [400, 260, 0.5, true]
          ]
        });
        return pitchGroup.children.map((node) => node.attributes.d);
        """
    )

    assert len(paths) == 2
    assert all(path.startswith("M ") for path in paths)
    assert all("NaN" not in path and "Infinity" not in path for path in paths)


def test_visualizer_pitch_y_axis_rises_with_higher_frequency() -> None:
    result = _run_visualizer_helper_js(
        """
        return {
          rising: pitchSegments([
            [0, 100, 0.5, true],
            [500, 200, 0.5, true],
            [1000, 300, 0.5, true]
          ], 1000, 100, 300)[0],
          falling: pitchSegments([
            [0, 300, 0.5, true],
            [500, 200, 0.5, true],
            [1000, 100, 0.5, true]
          ], 1000, 100, 300)[0]
        };
        """
    )

    assert result["rising"][0][1] > result["rising"][1][1] > result["rising"][2][1]
    assert result["falling"][0][1] < result["falling"][1][1] < result["falling"][2][1]


def test_visualizer_flat_pitch_range_renders_finite_path_and_labels() -> None:
    result = _run_visualizer_helper_js(
        """
        const pitchGroup = new FakeNode("g");
        const labelGroup = new FakeNode("g");
        const visualizer = {
          querySelector(selector) {
            if (selector === ".aqe-pitch") return pitchGroup;
            if (selector === ".aqe-labels") return labelGroup;
            throw new Error(`Unexpected selector: ${selector}`);
          }
        };
        const track = {
          durationMs: 1000,
          pitchMinHz: 220,
          pitchMaxHz: 220,
          points: [
            [0, 220, 0.5, true],
            [500, 220, 0.5, true],
            [1000, 220, 0.5, true]
          ]
        };
        drawPitch(visualizer, track);
        drawLabels(visualizer, track);
        return {
          paths: pitchGroup.children.map((node) => node.attributes.d),
          labels: labelGroup.children.map((node) => node.textContent)
        };
        """
    )

    assert result["labels"] == ["220 Hz", "220 Hz"]
    assert len(result["paths"]) == 1
    coordinates = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", result["paths"][0])]
    assert coordinates
    assert all(value == value and abs(value) < 10_000 for value in coordinates)


def _run_visualizer_helper_js(scenario: str):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to evaluate visualizer helper JavaScript")
    script = injection_script([0])
    helpers = "\n".join(
        _extract_js_function(script, name)
        for name in (
            "plotWidth",
            "plotHeight",
            "xForMs",
            "yForPitch",
            "pitchSegments",
            "drawPitch",
            "drawLabels",
        )
    )
    node_code = f"""
    const plot = {{ width: 620, height: 150, left: 44, right: 10, top: 10, bottom: 34 }};
    {helpers}

    class FakeNode {{
      constructor(tagName) {{
        this.tagName = tagName;
        this.children = [];
        this.attributes = {{}};
        this.textContent = "";
      }}

      setAttribute(name, value) {{
        this.attributes[name] = String(value);
      }}

      appendChild(node) {{
        this.children.push(node);
        return node;
      }}

      append(...nodes) {{
        this.children.push(...nodes);
      }}
    }}

    const document = {{
      createElementNS(_namespace, tagName) {{
        return new FakeNode(tagName);
      }}
    }};

    function runScenario() {{
      {scenario}
    }}

    process.stdout.write(JSON.stringify(runScenario()));
    """
    result = subprocess.run([node, "-e", node_code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _extract_js_function(script: str, name: str) -> str:
    start = script.index(f"function {name}(")
    body_start = script.index("{", start)
    depth = 0
    for index in range(body_start, len(script)):
        if script[index] == "{":
            depth += 1
        elif script[index] == "}":
            depth -= 1
            if depth == 0:
                return script[start : index + 1]
    raise AssertionError(f"Could not extract JavaScript function: {name}")
