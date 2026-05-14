"""Inline editor UI JavaScript for Audio Quick Editor."""

from __future__ import annotations

import json


def injection_script(audio_field_indices: list[int] | None = None) -> str:
    """Return JavaScript that mounts compact controls next to audio fields."""
    field_indices_json = json.dumps(audio_field_indices or [])
    return f"""
(function() {{
  const soundPattern = /\\[sound:([^\\]]+)\\]/i;
  const supportedPattern = /\\.(mp3|wav|ogg)$/i;
  const audioFieldIndices = new Set({field_indices_json});
  const processingCommands = new Set([
    "aqe:trim-left",
    "aqe:untrim-left",
    "aqe:trim-right",
    "aqe:untrim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:trim-silence",
    "aqe:remove-pauses"
  ]);
  const plot = {{ width: 620, height: 138, left: 44, right: 10, top: 10, bottom: 24 }};
  const styleId = "aqe-inline-style";

  function ensureStyle() {{
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = {json.dumps(_css())};
    document.head.appendChild(style);
  }}

  function fieldNodes() {{
    const candidates = Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]'));
    const seen = new Set();
    return candidates.filter((node) => {{
      if (seen.has(node)) return false;
      seen.add(node);
      return node.textContent || node.innerHTML;
    }});
  }}

  function explicitFieldTargets() {{
    return Array.from(audioFieldIndices)
      .map((ord) => {{
        const container = document.querySelector(`.field-container[data-index="${{ord}}"]`);
        if (!container) return null;
        return {{
          ord,
          node: container.querySelector('[contenteditable="true"]') || container
        }};
      }})
      .filter(Boolean);
  }}

  function fieldIndex(node, fallback) {{
    const attrs = ["data-field-ord", "data-ord", "data-index"];
    for (const attr of attrs) {{
      const raw = node.getAttribute && node.getAttribute(attr);
      if (raw !== null && raw !== undefined && /^\\d+$/.test(raw)) return Number(raw);
    }}
    const idMatch = String(node.id || "").match(/(\\d+)/);
    return idMatch ? Number(idMatch[1]) : fallback;
  }}

  function send(command, node, ord) {{
    const controls = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    if (controls && controls.dataset.busy === "true") return;
    if (node && typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    if (processingCommands.has(command)) setControlsBusy(ord, true, "Processing...");
    if (typeof pycmd === "function") {{
      pycmd("focus:" + ord);
      pycmd(command);
    }}
  }}

  function requestAnalysis(node, ord) {{
    if (node && typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    if (typeof pycmd === "function") {{
      pycmd("focus:" + ord);
      pycmd("aqe:analyze");
    }}
  }}

  function makeButton(label, title, command, node, ord) {{
    const button = document.createElement("button");
    button.type = "button";
    button.className = "aqe-button";
    button.dataset.aqeCommand = command;
    button.textContent = label;
    button.title = title;
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => send(command, node, ord));
    return button;
  }}

  function statusNode() {{
    const span = document.createElement("span");
    span.className = "aqe-status";
    span.textContent = "";
    return span;
  }}

  function visualizerNode(node, ord) {{
    const wrapper = document.createElement("div");
    wrapper.className = "aqe-visualizer";
    wrapper.dataset.aqeFieldOrd = String(ord);
    wrapper.dataset.cursorMs = "0";
    wrapper.innerHTML = `
      <svg class="aqe-visualizer-svg" viewBox="0 0 ${{plot.width}} ${{plot.height}}" role="img" aria-label="Audio pitch and intensity visualization">
        <path class="aqe-intensity" d=""></path>
        <g class="aqe-pitch"></g>
        <g class="aqe-labels"></g>
        <line class="aqe-cursor" x1="${{plot.left}}" x2="${{plot.left}}" y1="${{plot.top}}" y2="${{plot.height - plot.bottom}}"></line>
      </svg>
      <div class="aqe-visualizer-meta">
        <span class="aqe-cursor-label">0.00s</span>
        <span class="aqe-visualizer-status"></span>
      </div>
    `;
    const svg = wrapper.querySelector(".aqe-visualizer-svg");
    svg.addEventListener("pointerdown", (event) => startCursorDrag(event, wrapper, ord, true));
    return wrapper;
  }}

  function controlsFor(node, ord) {{
    const wrapper = document.createElement("div");
    wrapper.className = "aqe-controls";
    wrapper.dataset.aqeFieldOrd = String(ord);
    wrapper.append(
      makeButton("▶", "Play current audio", "aqe:play", node, ord),
      makeButton("-L", "Trim 100 ms from left", "aqe:trim-left", node, ord),
      makeButton("+L", "Undo 100 ms left trim", "aqe:untrim-left", node, ord),
      makeButton("-R", "Trim 100 ms from right", "aqe:trim-right", node, ord),
      makeButton("+R", "Undo 100 ms right trim", "aqe:untrim-right", node, ord),
      makeButton("Trim Silence", "Trim leading and trailing silence", "aqe:trim-silence", node, ord),
      makeButton("Remove Pauses", "Compress long internal pauses", "aqe:remove-pauses", node, ord),
      makeButton("Slower", "Decrease speed", "aqe:slower", node, ord),
      makeButton("Faster", "Increase speed", "aqe:faster", node, ord),
      makeButton("Undo", "Restore the previous generated audio reference", "aqe:undo", node, ord),
      statusNode(),
      visualizerNode(node, ord)
    );
    return wrapper;
  }}

  function mountNear(node, ord) {{
    const existing = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    if (existing) existing.remove();
    const parent = node.closest && node.closest(".field-container")
      ? node.closest(".field-container")
      : node.closest && node.closest(".field")
        ? node.closest(".field")
        : node.parentElement;
    const controls = controlsFor(node, ord);
    if (parent && parent.parentElement) {{
      parent.insertAdjacentElement("afterend", controls);
    }} else {{
      node.insertAdjacentElement("afterend", controls);
    }}
    setTimeout(() => requestAnalysis(node, ord), 300);
  }}

  function scan() {{
    ensureStyle();
    document.querySelectorAll(".aqe-controls").forEach((node) => node.remove());
    const explicitTargets = explicitFieldTargets();
    if (explicitTargets.length) {{
      explicitTargets.forEach((target) => mountNear(target.node, target.ord));
      return;
    }}
    fieldNodes().forEach((node, fallback) => {{
      const html = node.innerHTML || node.textContent || "";
      const match = html.match(soundPattern);
      if (!match || !supportedPattern.test(match[1])) return;
      mountNear(node, fieldIndex(node, fallback));
    }});
  }}

  function controlsForOrd(ord) {{
    const controls = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    return controls;
  }}

  function setControlsBusy(ord, busy, message, command) {{
    const controls = controlsForOrd(ord);
    if (!controls) return;
    controls.dataset.busy = busy ? "true" : "false";
    controls.querySelectorAll(".aqe-button").forEach((button) => {{
      button.disabled = !!busy;
    }});
    const status = controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = busy ? "processing" : "info";
    status.title = command || "";
  }}

  window.__aqeSetBusy = setControlsBusy;

  window.__aqeSetStatus = function(message, kind) {{
    const ord = window.__aqeActiveField;
    const controls = controlsForOrd(ord);
    const status = controls && controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = kind || "info";
  }};

  function visualizerForOrd(ord) {{
    return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"]`);
  }}

  function setVisualizerStatus(ord, message, kind) {{
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return;
    const status = visualizer.querySelector(".aqe-visualizer-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = kind || "info";
  }}

  function plotWidth() {{
    return plot.width - plot.left - plot.right;
  }}

  function plotHeight() {{
    return plot.height - plot.top - plot.bottom;
  }}

  function xForMs(ms, durationMs) {{
    if (!durationMs) return plot.left;
    return plot.left + Math.max(0, Math.min(1, ms / durationMs)) * plotWidth();
  }}

  function yForPitch(pitchHz, minHz, maxHz) {{
    if (!pitchHz || !minHz || !maxHz || maxHz <= minHz) return plot.height - plot.bottom;
    const ratio = Math.max(0, Math.min(1, (pitchHz - minHz) / (maxHz - minHz)));
    return plot.top + (1 - ratio) * plotHeight();
  }}

  function pathForIntensity(points, durationMs) {{
    if (!points || !points.length || !durationMs) return "";
    const base = plot.height - plot.bottom;
    const head = `M ${{xForMs(points[0][0], durationMs).toFixed(2)}} ${{base.toFixed(2)}}`;
    const body = points.map((point) => {{
      const x = xForMs(point[0], durationMs).toFixed(2);
      const y = (base - Math.max(0, Math.min(1, point[2] || 0)) * plotHeight()).toFixed(2);
      return `L ${{x}} ${{y}}`;
    }}).join(" ");
    const tail = `L ${{xForMs(points[points.length - 1][0], durationMs).toFixed(2)}} ${{base.toFixed(2)}} Z`;
    return `${{head}} ${{body}} ${{tail}}`;
  }}

  function pitchSegments(points, durationMs, minHz, maxHz) {{
    const segments = [];
    let current = [];
    for (const point of points || []) {{
      const pitchHz = point[1];
      const voiced = point[3] && pitchHz !== null && pitchHz !== undefined;
      if (!voiced) {{
        if (current.length) segments.push(current);
        current = [];
        continue;
      }}
      current.push([
        xForMs(point[0], durationMs),
        yForPitch(pitchHz, minHz, maxHz),
      ]);
    }}
    if (current.length) segments.push(current);
    return segments;
  }}

  function drawPitch(visualizer, track) {{
    const group = visualizer.querySelector(".aqe-pitch");
    group.textContent = "";
    for (const segment of pitchSegments(track.points, track.durationMs, track.pitchMinHz, track.pitchMaxHz)) {{
      if (segment.length < 2) continue;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", "aqe-pitch-path");
      path.setAttribute("d", segment.map((point, index) => `${{index ? "L" : "M"}} ${{point[0].toFixed(2)}} ${{point[1].toFixed(2)}}`).join(" "));
      group.appendChild(path);
    }}
  }}

  function drawLabels(visualizer, track) {{
    const group = visualizer.querySelector(".aqe-labels");
    group.textContent = "";
    const maxHz = track.pitchMaxHz || 500;
    const minHz = track.pitchMinHz || 75;
    for (const item of [
      [maxHz, plot.top + 10],
      [minHz, plot.height - plot.bottom],
    ]) {{
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("class", "aqe-hz-label");
      text.setAttribute("x", "2");
      text.setAttribute("y", String(item[1]));
      text.textContent = `${{Math.round(item[0])}} Hz`;
      group.appendChild(text);
    }}
  }}

  function setCursor(visualizer, ms, notifyPython) {{
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
    visualizer.dataset.cursorMs = String(Math.round(clamped));
    const x = xForMs(clamped, durationMs);
    const cursor = visualizer.querySelector(".aqe-cursor");
    if (cursor) {{
      cursor.setAttribute("x1", x.toFixed(2));
      cursor.setAttribute("x2", x.toFixed(2));
    }}
    const label = visualizer.querySelector(".aqe-cursor-label");
    if (label) label.textContent = `${{(clamped / 1000).toFixed(2)}}s`;
    if (notifyPython && typeof pycmd === "function") {{
      window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
      pycmd("focus:" + window.__aqeActiveField);
      pycmd("aqe:set-cursor");
    }}
  }}

  function cursorMsFromEvent(event, svg, durationMs) {{
    const rect = svg.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - (plot.left / plot.width) * rect.width) / ((plotWidth() / plot.width) * rect.width)));
    return ratio * durationMs;
  }}

  function startCursorDrag(event, visualizer, ord, notifyPython) {{
    event.preventDefault();
    const svg = visualizer.querySelector(".aqe-visualizer-svg");
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    if (!svg || !durationMs) return;
    const move = (moveEvent) => {{
      setCursor(visualizer, cursorMsFromEvent(moveEvent, svg, durationMs), false);
    }};
    const up = (upEvent) => {{
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      setCursor(visualizer, cursorMsFromEvent(upEvent, svg, durationMs), notifyPython);
    }};
    move(event);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }}

  window.__aqeSetVisualizer = function(ord, track, cursorMs) {{
    const visualizer = visualizerForOrd(ord);
    if (!visualizer || !track) return;
    visualizer.dataset.durationMs = String(track.durationMs || 0);
    visualizer.dataset.analyzerName = track.analyzerName || "";
    visualizer.dataset.sourceFilename = track.sourceFilename || "";
    const intensity = visualizer.querySelector(".aqe-intensity");
    if (intensity) intensity.setAttribute("d", pathForIntensity(track.points, track.durationMs));
    drawPitch(visualizer, track);
    drawLabels(visualizer, track);
    setCursor(visualizer, cursorMs || 0, false);
    setVisualizerStatus(ord, track.analyzerName || "", "info");
  }};

  window.__aqeSetVisualizerStatus = setVisualizerStatus;

  window.__aqeGetCursorMs = function() {{
    const ord = window.__aqeActiveField;
    const visualizer = visualizerForOrd(ord);
    return visualizer ? Number(visualizer.dataset.cursorMs || "0") : 0;
  }};

  window.__aqeSetCursorForTest = function(ord, ms, notifyPython) {{
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return false;
    setCursor(visualizer, ms, !!notifyPython);
    return true;
  }};

  window.__aqeScan = scan;
  setTimeout(scan, 0);
  setTimeout(scan, 250);
  setTimeout(scan, 1000);
}})();
"""


def _css() -> str:
    return """
.aqe-controls {
  align-items: center;
  border: 1px solid;
  border-radius: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 4px 0 10px;
  padding: 6px 8px;
}
.aqe-button {
  border: 1px solid;
  border-radius: 7px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}
.aqe-button:hover {
  text-decoration: underline;
}
.aqe-status {
  font-size: 12px;
  margin-left: 4px;
}
.aqe-status[data-kind="error"] {
  font-weight: 700;
}
.aqe-visualizer {
  flex-basis: 100%;
  min-width: 220px;
}
.aqe-visualizer-svg {
  border: 1px solid;
  border-radius: 8px;
  display: block;
  height: 138px;
  margin-top: 4px;
  width: 100%;
}
.aqe-intensity {
  fill: currentColor;
  opacity: 0.12;
  stroke: none;
}
.aqe-pitch-path {
  fill: none;
  opacity: 0.9;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
}
.aqe-cursor {
  opacity: 0.8;
  pointer-events: none;
  stroke: currentColor;
  stroke-width: 1.5;
}
.aqe-hz-label {
  fill: currentColor;
  font-size: 11px;
  opacity: 0.8;
}
.aqe-visualizer-meta {
  display: flex;
  font-size: 12px;
  gap: 8px;
  justify-content: space-between;
  margin-top: 2px;
}
.aqe-visualizer-status[data-kind="error"] {
  font-weight: 700;
}
"""
