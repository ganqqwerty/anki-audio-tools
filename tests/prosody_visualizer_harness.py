"""Node-backed helpers for exercising injected visualizer JavaScript."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from anki_audio_quick_editor.editor_ui import injection_script


def render_pitch_points(track_payload: dict) -> dict:
    return run_visualizer_helper_js(
        """
        const track = __TRACK__;
        const pitchGroup = new FakeNode("g");
        const visualizer = {
          querySelector(selector) {
            if (selector === ".aqe-pitch") return pitchGroup;
            throw new Error(`Unexpected selector: ${selector}`);
          }
        };
        drawPitch(visualizer, track);
        const rendered = (track.points || [])
          .filter((point) => point[3] && point[1] !== null && point[1] !== undefined)
          .map((point) => ({
            timeMs: point[0],
            pitchHz: point[1],
            x: xForMs(point[0], track.durationMs),
            y: yForPitch(point[1], track.pitchMinHz, track.pitchMaxHz)
          }));
        return {
          paths: pitchGroup.children.map((node) => node.attributes.d),
          rendered
        };
        """.replace("__TRACK__", json.dumps(track_payload))
    )


def run_visualizer_helper_js(scenario: str):
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
