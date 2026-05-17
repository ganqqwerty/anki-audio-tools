"""Inline editor UI JavaScript for Audio Quick Editor."""

from __future__ import annotations

import json


def injection_script(audio_field_indices: list[int] | None = None) -> str:
    """Return JavaScript that mounts compact controls next to audio fields."""
    return (
        _SCRIPT_TEMPLATE.replace("__FIELD_INDICES_JSON__", json.dumps(audio_field_indices or []))
        .replace("__CSS_JSON__", json.dumps(_css()))
    )


_SCRIPT_TEMPLATE = r"""
(function() {
  const soundPattern = /\[sound:([^\]]+)\]/i;
  const supportedPattern = /\.(mp3|wav|ogg)$/i;
  const audioFieldIndices = new Set(__FIELD_INDICES_JSON__);
  const processingCommands = new Set([
    "aqe:trim-left",
    "aqe:trim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:remove-pauses",
    "aqe:remove-noise",
    "aqe:sidon",
    "aqe:mp-senet",
    "aqe:volume-down",
    "aqe:volume-up"
  ]);
  const commandSlugs = {
    "aqe:play": "play",
    "aqe:analyze": "graph",
    "aqe:show-file": "show-file",
    "aqe:trim-left": "trim-left",
    "aqe:trim-right": "trim-right",
    "aqe:remove-pauses": "remove-pauses",
    "aqe:remove-noise": "remove-noise",
    "aqe:sidon": "sidon",
    "aqe:mp-senet": "mp-senet",
    "aqe:slower": "slower",
    "aqe:faster": "faster",
    "aqe:volume-down": "volume-down",
    "aqe:volume-up": "volume-up",
    "aqe:undo": "undo"
  };
  const plot = { width: 620, height: 150, left: 44, right: 10, top: 10, bottom: 34 };
  const styleId = "aqe-inline-style";

  function ensureStyle() {
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = __CSS_JSON__;
    document.head.appendChild(style);
  }

  function fieldNodes() {
    const candidates = Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]'));
    const seen = new Set();
    return candidates.filter((node) => {
      if (seen.has(node)) return false;
      seen.add(node);
      return node.textContent || node.innerHTML;
    });
  }

  function explicitFieldTargets() {
    return Array.from(audioFieldIndices)
      .map((ord) => {
        const container = document.querySelector(`.field-container[data-index="${ord}"]`);
        if (!container) return null;
        return {
          ord,
          node: container.querySelector('[contenteditable="true"]') || container
        };
      })
      .filter(Boolean);
  }

  function fieldIndex(node, fallback) {
    const attrs = ["data-field-ord", "data-ord", "data-index"];
    for (const attr of attrs) {
      const raw = node.getAttribute && node.getAttribute(attr);
      if (raw !== null && raw !== undefined && /^\d+$/.test(raw)) return Number(raw);
    }
    const idMatch = String(node.id || "").match(/(\d+)/);
    return idMatch ? Number(idMatch[1]) : fallback;
  }

  function audioSourceForNode(node) {
    const html = node.innerHTML || node.textContent || "";
    const match = html.match(soundPattern);
    return match && supportedPattern.test(match[1]) ? match[1] : "";
  }

  function testId(ord, command) {
    return `aqe-button-${ord}-${commandSlugs[command] || command.replace(/[^a-z0-9]+/g, "-")}`;
  }

  function anyBusy() {
    return document.body.dataset.aqeBusy === "true";
  }

  function processingMessage(command) {
    if (command === "aqe:remove-noise") return "Removing noise...";
    if (command === "aqe:sidon") return "Restoring speech...";
    if (command === "aqe:mp-senet") return "Denoising with MP-SENet...";
    return "Processing...";
  }

  function send(command, node, ord) {
    if (anyBusy()) return;
    if (node && typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    if (command === "aqe:analyze") {
      requestGraph(ord, true);
      return;
    }
    if (command === "aqe:play" && handleHtmlPlaybackCommand(ord)) {
      return;
    }
    if (processingCommands.has(command)) {
      setControlsBusy(ord, true, processingMessage(command));
    }
    if (typeof pycmd === "function") {
      pycmd("focus:" + ord);
      pycmd(command);
    }
  }

  function makeButton(label, title, command, node, ord) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "aqe-button";
    button.dataset.aqeCommand = command;
    button.dataset.testid = testId(ord, command);
    button.textContent = label;
    button.title = title;
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => send(command, node, ord));
    return button;
  }

  function statusNode(ord) {
    const span = document.createElement("span");
    span.className = "aqe-status";
    span.dataset.testid = `aqe-status-${ord}`;
    span.textContent = "";
    return span;
  }

  function visualizerNode(ord) {
    const wrapper = document.createElement("div");
    wrapper.className = "aqe-visualizer";
    wrapper.dataset.aqeFieldOrd = String(ord);
    wrapper.dataset.anchorMs = "0";
    wrapper.dataset.cursorMs = "0";
    wrapper.dataset.progressMs = "0";
    wrapper.dataset.graphActive = "false";
    wrapper.dataset.graphBusy = "false";
    wrapper.dataset.hasTrack = "false";
    wrapper.dataset.playbackState = "stopped";
    wrapper.dataset.playbackEngine = "";
    wrapper.dataset.resumeRequiresRestart = "false";
    wrapper.dataset.testid = `aqe-graph-${ord}`;
    wrapper.hidden = true;
    wrapper.innerHTML = `
      <audio class="aqe-audio-clock" data-testid="aqe-audio-clock-${ord}" preload="metadata" hidden></audio>
      <svg class="aqe-visualizer-svg" data-testid="aqe-graph-svg-${ord}" viewBox="0 0 ${plot.width} ${plot.height}" role="img" aria-label="Audio pitch and intensity visualization">
        <path class="aqe-intensity" data-testid="aqe-intensity-${ord}" d=""></path>
        <g class="aqe-pitch" data-testid="aqe-pitch-${ord}"></g>
        <g class="aqe-labels"></g>
        <g class="aqe-x-axis" data-testid="aqe-x-axis-${ord}"></g>
        <line class="aqe-cursor" data-testid="aqe-cursor-${ord}" x1="${plot.left}" x2="${plot.left}" y1="${plot.top}" y2="${plot.height - plot.bottom}"></line>
      </svg>
      <div class="aqe-visualizer-meta">
        <span class="aqe-spinner" data-testid="aqe-graph-spinner-${ord}" hidden aria-hidden="true"></span>
        <span class="aqe-cursor-label" data-testid="aqe-progress-label-${ord}">0 ms</span>
        <span class="aqe-visualizer-status" data-testid="aqe-graph-status-${ord}"></span>
      </div>
    `;
    resetAudioClockState(wrapper);
    installAudioClockHandlers(wrapper);
    const svg = wrapper.querySelector(".aqe-visualizer-svg");
    svg.addEventListener("pointerdown", (event) => startCursorDrag(event, wrapper, ord, true));
    return wrapper;
  }

  function controlsFor(node, ord) {
    const wrapper = document.createElement("div");
    wrapper.className = "aqe-controls";
    wrapper.dataset.aqeFieldOrd = String(ord);
    wrapper.dataset.testid = `aqe-controls-${ord}`;
    wrapper.append(
      makeButton("Play", "Play or pause current audio", "aqe:play", node, ord),
      makeButton("Graph", "Analyze and show pitch/intensity graph", "aqe:analyze", node, ord),
      makeButton("Folder", "Show current audio file in folder", "aqe:show-file", node, ord),
      makeButton("-L", "Trim 100 ms from left", "aqe:trim-left", node, ord),
      makeButton("-R", "Trim 100 ms from right", "aqe:trim-right", node, ord),
      makeButton("Shorten Pauses", "Speed up long internal pauses", "aqe:remove-pauses", node, ord),
      makeButton("Sidon", "Restore speech with Sidon", "aqe:sidon", node, ord),
      makeButton("MP-SENet", "Denoise speech with MP-SENet", "aqe:mp-senet", node, ord),
      makeButton("Remove noise", "Reduce background noise with DeepFilterNet", "aqe:remove-noise", node, ord),
      makeButton("Slower", "Decrease speed", "aqe:slower", node, ord),
      makeButton("Faster", "Increase speed", "aqe:faster", node, ord),
      makeButton("Volume -", "Decrease volume", "aqe:volume-down", node, ord),
      makeButton("Volume +", "Increase volume", "aqe:volume-up", node, ord),
      makeButton("Undo", "Restore the previous generated audio reference", "aqe:undo", node, ord),
      statusNode(ord),
      visualizerNode(ord)
    );
    return wrapper;
  }

  function mountNear(node, ord) {
    const existingControls = Array.from(document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${ord}"]`));
    const sourceFilename = audioSourceForNode(node);
    const reusable = existingControls.find((controls) => controls.dataset.aqeSourceFilename === sourceFilename);
    if (reusable) {
      existingControls.forEach((controls) => {
        if (controls !== reusable) controls.remove();
      });
      return;
    }
    existingControls.forEach((controls) => controls.remove());
    const parent = node.closest && node.closest(".field-container")
      ? node.closest(".field-container")
      : node.closest && node.closest(".field")
        ? node.closest(".field")
        : node.parentElement;
    const controls = controlsFor(node, ord);
    controls.dataset.aqeSourceFilename = sourceFilename;
    if (parent && parent.parentElement) {
      parent.insertAdjacentElement("afterend", controls);
    } else {
      node.insertAdjacentElement("afterend", controls);
    }
  }

  function scan() {
    ensureStyle();
    const explicitTargets = explicitFieldTargets();
    if (explicitTargets.length) {
      explicitTargets.forEach((target) => mountNear(target.node, target.ord));
      return;
    }
    fieldNodes().forEach((node, fallback) => {
      const html = node.innerHTML || node.textContent || "";
      const match = html.match(soundPattern);
      if (!match || !supportedPattern.test(match[1])) return;
      mountNear(node, fieldIndex(node, fallback));
    });
  }

  function controlsForOrd(ord) {
    return document.querySelector(`.aqe-controls[data-aqe-field-ord="${ord}"]`);
  }

  function allButtons() {
    return Array.from(document.querySelectorAll(".aqe-button"));
  }

  function setControlsBusy(ord, busy, message, command) {
    document.body.dataset.aqeBusy = busy ? "true" : "false";
    document.querySelectorAll(".aqe-controls").forEach((controls) => {
      controls.dataset.busy = busy ? "true" : "false";
    });
    allButtons().forEach((button) => {
      button.disabled = !!busy;
    });
    const controls = controlsForOrd(ord);
    const status = controls && controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = busy ? "processing" : "info";
    status.title = command || "";
  }

  window.__aqeSetBusy = setControlsBusy;

  window.__aqeSetStatus = function(message, kind) {
    const ord = window.__aqeActiveField;
    const controls = controlsForOrd(ord);
    const status = controls && controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = kind || "info";
  };

  function clearStatus(ord) {
    const controls = controlsForOrd(ord);
    const status = controls && controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = "";
    status.dataset.kind = "info";
    status.title = "";
  }

  function prepareForNewNote() {
    document.body.dataset.aqeBusy = "false";
    window.__aqeActiveField = null;
    window.__aqeLastCursorIntent = null;
    document.querySelectorAll(".aqe-controls").forEach((controls) => {
      controls.dataset.busy = "false";
      controls.dataset.aqeSourceFilename = "";
      controls.querySelectorAll(".aqe-button").forEach((button) => {
        button.disabled = false;
        if (button.dataset.aqeCommand === "aqe:analyze") button.textContent = "Graph";
        if (button.dataset.aqeCommand === "aqe:play") button.textContent = "Play";
      });
      const status = controls.querySelector(".aqe-status");
      if (status) {
        status.textContent = "";
        status.dataset.kind = "info";
        status.title = "";
      }
      const visualizer = controls.querySelector(".aqe-visualizer");
      if (!visualizer) return;
      clearPlaybackFrame(visualizer);
      clearAudioClockSource(visualizer);
      visualizer.hidden = true;
      visualizer.dataset.anchorMs = "0";
      visualizer.dataset.cursorMs = "0";
      visualizer.dataset.progressMs = "0";
      visualizer.dataset.graphActive = "false";
      visualizer.dataset.graphBusy = "false";
      visualizer.dataset.hasTrack = "false";
      visualizer.dataset.playbackState = "stopped";
      visualizer.dataset.playbackEngine = "";
      visualizer.dataset.resumeRequiresRestart = "false";
      visualizer.dataset.durationMs = "0";
      visualizer.dataset.sourceFilename = "";
      visualizer.dataset.analyzerName = "";
      visualizer.dataset.playStartedAt = "0";
      visualizer.dataset.playStartMs = "0";
      visualizer.dataset.progressClockMode = "stopped";
      const intensity = visualizer.querySelector(".aqe-intensity");
      if (intensity) intensity.setAttribute("d", "");
      const pitch = visualizer.querySelector(".aqe-pitch");
      if (pitch) pitch.textContent = "";
      const labels = visualizer.querySelector(".aqe-labels");
      if (labels) labels.textContent = "";
      const xAxis = visualizer.querySelector(".aqe-x-axis");
      if (xAxis) xAxis.textContent = "";
      const cursor = visualizer.querySelector(".aqe-cursor");
      if (cursor) {
        cursor.setAttribute("x1", String(plot.left));
        cursor.setAttribute("x2", String(plot.left));
      }
      const label = visualizer.querySelector(".aqe-cursor-label");
      if (label) label.textContent = "0 ms";
      const graphStatus = visualizer.querySelector(".aqe-visualizer-status");
      if (graphStatus) {
        graphStatus.textContent = "";
        graphStatus.dataset.kind = "info";
      }
      const spinner = visualizer.querySelector(".aqe-spinner");
      if (spinner) spinner.hidden = true;
    });
  }

  function visualizerForOrd(ord) {
    return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
  }

  function buttonFor(ord, command) {
    const controls = controlsForOrd(ord);
    return controls && controls.querySelector(`[data-aqe-command="${command}"]`);
  }

  function graphButton(ord) {
    return buttonFor(ord, "aqe:analyze");
  }

  function playButton(ord) {
    return buttonFor(ord, "aqe:play");
  }

  function setVisualizerStatus(ord, message, kind) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return;
    const status = visualizer.querySelector(".aqe-visualizer-status");
    const spinner = visualizer.querySelector(".aqe-spinner");
    const processing = kind === "processing";
    visualizer.dataset.graphBusy = processing ? "true" : "false";
    if (spinner) spinner.hidden = !processing;
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = kind || "info";
  }

  function plotWidth() {
    return plot.width - plot.left - plot.right;
  }

  function plotHeight() {
    return plot.height - plot.top - plot.bottom;
  }

  function xForMs(ms, durationMs) {
    if (!durationMs) return plot.left;
    return plot.left + Math.max(0, Math.min(1, ms / durationMs)) * plotWidth();
  }

  function yForPitch(pitchHz, minHz, maxHz) {
    if (!pitchHz || !minHz || !maxHz || maxHz <= minHz) return plot.height - plot.bottom;
    const ratio = Math.max(0, Math.min(1, (pitchHz - minHz) / (maxHz - minHz)));
    return plot.top + (1 - ratio) * plotHeight();
  }

  function formatTime(ms, durationMs) {
    if (durationMs && durationMs < 2000) return `${Math.round(ms)} ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  }

  function mediaUrlForFilename(filename) {
    return encodeURIComponent(filename || "").replace(/%2F/gi, "/");
  }

  function audioClockFor(visualizer) {
    return visualizer && visualizer.querySelector(".aqe-audio-clock");
  }

  function resetAudioClockState(visualizer) {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = false;
    visualizer.__aqeAudioClockLastSeekedMs = 0;
    visualizer.dataset.progressClockMode = "stopped";
  }

  function clearPlaybackFrame(visualizer) {
    if (visualizer.__aqePlaybackTimer) {
      window.cancelAnimationFrame(visualizer.__aqePlaybackTimer);
      visualizer.__aqePlaybackTimer = null;
    }
  }

  function pauseAudioClock(visualizer) {
    const audio = audioClockFor(visualizer);
    if (!audio || typeof audio.pause !== "function") return;
    try {
      audio.pause();
    } catch (_error) {
      visualizer.__aqeAudioClockAvailable = false;
      visualizer.__aqeAudioClockFallback = true;
    }
  }

  function clearAudioClockSource(visualizer) {
    const audio = audioClockFor(visualizer);
    resetAudioClockState(visualizer);
    if (!audio) return;
    pauseAudioClock(visualizer);
    if (typeof audio.removeAttribute === "function") {
      audio.removeAttribute("src");
    }
    if ("src" in audio) {
      audio.src = "";
    }
    try {
      if (typeof audio.load === "function") audio.load();
    } catch (_error) {
      visualizer.__aqeAudioClockFallback = true;
    }
  }

  function configureAudioClock(visualizer, filename) {
    const audio = audioClockFor(visualizer);
    resetAudioClockState(visualizer);
    if (!audio) {
      visualizer.__aqeAudioClockFallback = true;
      return;
    }
    pauseAudioClock(visualizer);
    if (!filename) {
      clearAudioClockSource(visualizer);
      return;
    }
    const source = mediaUrlForFilename(filename);
    if (typeof audio.setAttribute === "function") {
      audio.setAttribute("src", source);
    } else {
      audio.src = source;
    }
    try {
      if (typeof audio.load === "function") audio.load();
    } catch (_error) {
      visualizer.__aqeAudioClockAvailable = false;
      visualizer.__aqeAudioClockFallback = true;
    }
  }

  function installAudioClockHandlers(visualizer) {
    const audio = audioClockFor(visualizer);
    if (!audio || audio.__aqeClockHandlersInstalled || typeof audio.addEventListener !== "function") return;
    audio.__aqeClockHandlersInstalled = true;
    audio.addEventListener("loadedmetadata", () => {
      if (typeof audio.getAttribute === "function" && !audio.getAttribute("src")) return;
      visualizer.__aqeAudioClockAvailable = true;
      visualizer.__aqeAudioClockFallback = false;
    });
    audio.addEventListener("error", () => {
      visualizer.__aqeAudioClockAvailable = false;
      visualizer.__aqeAudioClockFallback = true;
      if (visualizer.dataset.playbackState === "playing" && visualizer.dataset.progressClockMode === "audio") {
        startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"));
      }
    });
    audio.addEventListener("ended", () => {
      if (visualizer.dataset.playbackState === "playing") completePlayback(visualizer);
    });
    audio.addEventListener("seeked", () => {
      visualizer.__aqeAudioClockLastSeekedMs = Math.round((Number(audio.currentTime) || 0) * 1000);
    });
  }

  function audioClockReady(visualizer) {
    const audio = audioClockFor(visualizer);
    if (!audio || !visualizer.__aqeAudioClockAvailable) return false;
    if (typeof audio.getAttribute === "function" && !audio.getAttribute("src")) return false;
    return audio.readyState === undefined || audio.readyState >= 1;
  }

  function clampProgressMs(visualizer, ms) {
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
  }

  function seekAudioClock(visualizer, ms) {
    const audio = audioClockFor(visualizer);
    if (!audio) return false;
    const clamped = clampProgressMs(visualizer, ms);
    try {
      audio.currentTime = clamped / 1000;
      visualizer.__aqeAudioClockLastSeekedMs = Math.round(clamped);
      return true;
    } catch (_error) {
      visualizer.__aqeAudioClockAvailable = false;
      visualizer.__aqeAudioClockFallback = true;
      return false;
    }
  }

  function pathForIntensity(points, durationMs) {
    if (!points || !points.length || !durationMs) return "";
    const base = plot.height - plot.bottom;
    const head = `M ${xForMs(points[0][0], durationMs).toFixed(2)} ${base.toFixed(2)}`;
    const body = points.map((point) => {
      const x = xForMs(point[0], durationMs).toFixed(2);
      const y = (base - Math.max(0, Math.min(1, point[2] || 0)) * plotHeight()).toFixed(2);
      return `L ${x} ${y}`;
    }).join(" ");
    const tail = `L ${xForMs(points[points.length - 1][0], durationMs).toFixed(2)} ${base.toFixed(2)} Z`;
    return `${head} ${body} ${tail}`;
  }

  function pitchSegments(points, durationMs, minHz, maxHz) {
    const segments = [];
    let current = [];
    for (const point of points || []) {
      const pitchHz = point[1];
      const voiced = point[3] && pitchHz !== null && pitchHz !== undefined;
      if (!voiced) {
        if (current.length) segments.push(current);
        current = [];
        continue;
      }
      current.push([
        xForMs(point[0], durationMs),
        yForPitch(pitchHz, minHz, maxHz),
      ]);
    }
    if (current.length) segments.push(current);
    return segments;
  }

  function drawPitch(visualizer, track) {
    const group = visualizer.querySelector(".aqe-pitch");
    group.textContent = "";
    for (const segment of pitchSegments(track.points, track.durationMs, track.pitchMinHz, track.pitchMaxHz)) {
      if (segment.length < 2) continue;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", "aqe-pitch-path");
      path.setAttribute("d", segment.map((point, index) => `${index ? "L" : "M"} ${point[0].toFixed(2)} ${point[1].toFixed(2)}`).join(" "));
      group.appendChild(path);
    }
  }

  function drawLabels(visualizer, track) {
    const group = visualizer.querySelector(".aqe-labels");
    group.textContent = "";
    const maxHz = track.pitchMaxHz || 500;
    const minHz = track.pitchMinHz || 75;
    for (const item of [
      [maxHz, plot.top + 10],
      [minHz, plot.height - plot.bottom],
    ]) {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("class", "aqe-hz-label");
      text.setAttribute("x", "2");
      text.setAttribute("y", String(item[1]));
      text.textContent = `${Math.round(item[0])} Hz`;
      group.appendChild(text);
    }
  }

  function drawXAxis(visualizer, durationMs) {
    const group = visualizer.querySelector(".aqe-x-axis");
    group.textContent = "";
    const ticks = [0, durationMs / 2, durationMs].filter((value, index, values) => index === 0 || value !== values[index - 1]);
    for (const tick of ticks) {
      const x = xForMs(tick, durationMs);
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("class", "aqe-x-tick");
      line.setAttribute("x1", x.toFixed(2));
      line.setAttribute("x2", x.toFixed(2));
      line.setAttribute("y1", String(plot.height - plot.bottom));
      line.setAttribute("y2", String(plot.height - plot.bottom + 4));
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("class", "aqe-x-label");
      text.setAttribute("x", x.toFixed(2));
      text.setAttribute("y", String(plot.height - 8));
      text.textContent = formatTime(tick, durationMs);
      group.append(line, text);
    }
  }

  function setCursor(visualizer, ms, notifyPython, options) {
    const opts = options || {};
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
    visualizer.dataset.cursorMs = String(Math.round(clamped));
    visualizer.dataset.progressMs = String(Math.round(clamped));
    if (opts.updateAnchor !== false) {
      visualizer.dataset.anchorMs = String(Math.round(clamped));
    }
    const x = xForMs(clamped, durationMs);
    const cursor = visualizer.querySelector(".aqe-cursor");
    if (cursor) {
      cursor.setAttribute("x1", x.toFixed(2));
      cursor.setAttribute("x2", x.toFixed(2));
    }
    const label = visualizer.querySelector(".aqe-cursor-label");
    if (label) label.textContent = formatTime(clamped, durationMs);
    if (notifyPython && typeof pycmd === "function") {
      window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
      window.__aqeLastCursorIntent = {
        cursorMs: Math.round(clamped),
        previousPlaybackState: opts.previousPlaybackState || visualizer.dataset.playbackState || "stopped",
        restartPlayback: !!opts.restartPlayback
      };
      if (opts.engine) {
        window.__aqeLastCursorIntent.engine = opts.engine;
      }
      pycmd("focus:" + window.__aqeActiveField);
      pycmd("aqe:set-cursor");
    }
  }

  function graphPixelBounds(svg) {
    const rect = svg.getBoundingClientRect();
    const rectWidth = Number(rect.width) || plot.width;
    const rectHeight = Number(rect.height) || plot.height;
    const scaleX = Math.min(rectWidth / plot.width, rectHeight / plot.height) || 1;
    const renderedViewBoxLeft = rect.left + (rectWidth - plot.width * scaleX) / 2;
    return {
      left: renderedViewBoxLeft + plot.left * scaleX,
      width: plotWidth() * scaleX
    };
  }

  function cursorMsFromEvent(event, svg, durationMs) {
    const bounds = graphPixelBounds(svg);
    const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
    return ratio * durationMs;
  }

  function startCursorDrag(event, visualizer, ord, notifyPython) {
    event.preventDefault();
    const previousPlaybackState = visualizer.dataset.playbackState || "stopped";
    if (previousPlaybackState === "playing") {
      stopProgressClock(visualizer);
    }
    const svg = visualizer.querySelector(".aqe-visualizer-svg");
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    if (!svg || !durationMs) return;
    const move = (moveEvent) => {
      setCursor(visualizer, cursorMsFromEvent(moveEvent, svg, durationMs), false);
    };
    const up = (upEvent) => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      const restartPlayback = previousPlaybackState === "playing";
      if (previousPlaybackState === "paused") {
        visualizer.dataset.resumeRequiresRestart = "true";
      }
      const releasedMs = cursorMsFromEvent(upEvent, svg, durationMs);
      const restartEngine = restartPlayback && audioClockReady(visualizer) ? "html" : "";
      setCursor(visualizer, releasedMs, notifyPython, {
        previousPlaybackState,
        restartPlayback,
        engine: restartEngine
      });
      if (audioClockReady(visualizer)) {
        seekAudioClock(visualizer, releasedMs);
      }
      if (restartPlayback && restartEngine === "html") {
        startEditorHtmlPlayback(visualizer, {
          ord,
          action: "start",
          cursorMs: Math.round(clampProgressMs(visualizer, releasedMs)),
          engine: "html"
        });
      }
    };
    move(event);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  function requestGraph(ord, notifyPython) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return;
    stopProgressClock(visualizer, { clearAudio: true });
    visualizer.hidden = false;
    visualizer.dataset.graphActive = "true";
    visualizer.dataset.graphBusy = "true";
    visualizer.dataset.hasTrack = "false";
    visualizer.dataset.durationMs = "0";
    visualizer.dataset.sourceFilename = "";
    visualizer.dataset.anchorMs = "0";
    visualizer.dataset.cursorMs = "0";
    visualizer.dataset.progressMs = "0";
    visualizer.dataset.resumeRequiresRestart = "false";
    visualizer.dataset.playbackEngine = "";
    visualizer.querySelector(".aqe-intensity").setAttribute("d", "");
    visualizer.querySelector(".aqe-pitch").textContent = "";
    visualizer.querySelector(".aqe-labels").textContent = "";
    visualizer.querySelector(".aqe-x-axis").textContent = "";
    setCursor(visualizer, 0, false);
    const button = graphButton(ord);
    if (button) button.textContent = "Redraw";
    setVisualizerStatus(ord, "Analyzing...", "processing");
    window.__aqeActiveField = ord;
    if (notifyPython && typeof pycmd === "function") {
      setControlsBusy(ord, true, "Analyzing...", "");
      pycmd("focus:" + ord);
      pycmd("aqe:analyze");
    }
  }

  function resetGraphAfterEdit(ord) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return false;
    requestGraph(ord, true);
    return true;
  }

  function setPlaybackButtonLabel(visualizer, label) {
    const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
    const button = playButton(ord);
    if (button) button.textContent = label;
  }

  function manualProgressMs(visualizer) {
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    const elapsed = performance.now() - Number(visualizer.dataset.playStartedAt || "0");
    return Math.min(durationMs, Number(visualizer.dataset.playStartMs || "0") + elapsed);
  }

  function audioProgressMs(visualizer) {
    const audio = audioClockFor(visualizer);
    if (!audio) return null;
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    return Math.min(durationMs, (Number(audio.currentTime) || 0) * 1000);
  }

  function currentProgressMs(visualizer) {
    if (visualizer.dataset.progressClockMode === "audio") {
      return audioProgressMs(visualizer);
    }
    if (visualizer.dataset.progressClockMode === "manual") {
      return manualProgressMs(visualizer);
    }
    return Number(visualizer.dataset.progressMs || visualizer.dataset.cursorMs || "0");
  }

  function completePlayback(visualizer) {
    const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
    const anchorMs = Number(visualizer.dataset.anchorMs || "0");
    stopProgressClock(visualizer);
    setCursor(visualizer, anchorMs, false, { updateAnchor: false });
    if (audioClockReady(visualizer)) {
      seekAudioClock(visualizer, anchorMs);
    }
    clearStatus(ord);
    if (typeof pycmd === "function") {
      window.__aqeActiveField = ord;
      pycmd("focus:" + ord);
      pycmd("aqe:play-ended");
    }
  }

  function paintProgressFromClock(visualizer) {
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    const tick = () => {
      if (visualizer.dataset.playbackState !== "playing") return;
      const nextMs = audioProgressMs(visualizer);
      if (nextMs === null) {
        startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"));
        return;
      }
      setCursor(visualizer, nextMs, false, { updateAnchor: false });
      if (nextMs >= durationMs) {
        completePlayback(visualizer);
        return;
      }
      visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
    };
    visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
  }

  function startManualProgressClock(visualizer, startMs) {
    clearPlaybackFrame(visualizer);
    pauseAudioClock(visualizer);
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    if (!durationMs) return;
    const clampedStartMs = clampProgressMs(visualizer, startMs);
    visualizer.__aqeAudioClockFallback = true;
    visualizer.dataset.playbackState = "playing";
    visualizer.dataset.progressClockMode = "manual";
    visualizer.dataset.playStartedAt = String(performance.now());
    visualizer.dataset.playStartMs = String(clampedStartMs);
    setPlaybackButtonLabel(visualizer, "Pause");
    const tick = () => {
      if (visualizer.dataset.playbackState !== "playing") return;
      const nextMs = manualProgressMs(visualizer);
      setCursor(visualizer, nextMs, false, { updateAnchor: false });
      if (nextMs >= durationMs) {
        completePlayback(visualizer);
        return;
      }
      visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
    };
    visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
  }

  function startAudioProgressClock(visualizer, startMs, options) {
    const opts = options || {};
    const audio = audioClockFor(visualizer);
    if (!audio || !seekAudioClock(visualizer, startMs) || typeof audio.play !== "function") {
      if (opts.manualFallback === false) {
        if (opts.onAudioPlayFailed) opts.onAudioPlayFailed();
        return;
      }
      startManualProgressClock(visualizer, startMs);
      return;
    }
    visualizer.dataset.progressClockMode = "audio";
    visualizer.__aqeAudioClockFallback = false;
    let playResult;
    try {
      playResult = audio.play();
    } catch (_error) {
      if (opts.manualFallback === false) {
        if (opts.onAudioPlayFailed) opts.onAudioPlayFailed();
        return;
      }
      startManualProgressClock(visualizer, startMs);
      return;
    }
    const startPainting = () => {
      if (visualizer.dataset.playbackState !== "playing") return;
      clearPlaybackFrame(visualizer);
      visualizer.dataset.progressClockMode = "audio";
      paintProgressFromClock(visualizer);
      if (opts.onAudioStarted) opts.onAudioStarted();
    };
    if (playResult && typeof playResult.then === "function") {
      playResult.then(startPainting).catch(() => {
        if (visualizer.dataset.playbackState === "playing") {
          if (opts.manualFallback === false) {
            if (opts.onAudioPlayFailed) opts.onAudioPlayFailed();
            return;
          }
          startManualProgressClock(visualizer, currentProgressMs(visualizer));
        }
      });
      return;
    }
    startPainting();
  }

  function startProgressClock(visualizer, startMs, options) {
    const opts = options || {};
    const selectedEngine = opts.engine || visualizer.dataset.playbackEngine || "";
    stopProgressClock(visualizer, { clearEngine: false });
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    if (!durationMs) return;
    const clampedStartMs = clampProgressMs(visualizer, startMs);
    visualizer.dataset.playbackEngine = selectedEngine;
    visualizer.dataset.playbackState = "playing";
    visualizer.dataset.playStartedAt = String(performance.now());
    visualizer.dataset.playStartMs = String(clampedStartMs);
    setCursor(visualizer, clampedStartMs, false, { updateAnchor: false });
    setPlaybackButtonLabel(visualizer, "Pause");
    if (selectedEngine === "native") {
      startManualProgressClock(visualizer, clampedStartMs);
      return;
    }
    if (audioClockReady(visualizer)) {
      startAudioProgressClock(visualizer, clampedStartMs, opts);
      return;
    }
    if (opts.manualFallback === false) {
      if (opts.onAudioPlayFailed) opts.onAudioPlayFailed();
      return;
    }
    startManualProgressClock(visualizer, clampedStartMs);
  }

  function pauseProgressClock(visualizer) {
    const currentMs = currentProgressMs(visualizer);
    if (currentMs !== null) {
      setCursor(visualizer, currentMs, false, { updateAnchor: false });
    }
    clearPlaybackFrame(visualizer);
    pauseAudioClock(visualizer);
    visualizer.dataset.playbackState = "paused";
    visualizer.dataset.progressClockMode = "stopped";
    setPlaybackButtonLabel(visualizer, "Play");
  }

  function stopProgressClock(visualizer, options) {
    const opts = options || {};
    clearPlaybackFrame(visualizer);
    pauseAudioClock(visualizer);
    visualizer.dataset.playbackState = "stopped";
    visualizer.dataset.progressClockMode = "stopped";
    visualizer.dataset.resumeRequiresRestart = "false";
    if (opts.clearEngine !== false) {
      visualizer.dataset.playbackEngine = "";
    }
    if (opts.clearAudio) {
      clearAudioClockSource(visualizer);
    }
    setPlaybackButtonLabel(visualizer, "Play");
  }

  function playbackRequest(ord) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return { ord, action: "start", cursorMs: 0 };
    const state = visualizer.dataset.playbackState || "stopped";
    let action = "start";
    if (state === "playing") action = "pause";
    if (state === "paused") {
      action = visualizer.dataset.resumeRequiresRestart === "true" ? "start" : "resume";
    }
    let cursorMs = Number(visualizer.dataset.anchorMs || visualizer.dataset.cursorMs || "0");
    if (action === "pause" || action === "resume") {
      cursorMs = Number(currentProgressMs(visualizer) || visualizer.dataset.cursorMs || cursorMs);
    }
    return {
      ord,
      action,
      cursorMs: Math.round(cursorMs),
      engine: playbackEngineFor(visualizer)
    };
  }

  function playbackEngineFor(visualizer) {
    if (!visualizer || visualizer.dataset.hasTrack !== "true") return "native";
    const activeEngine = visualizer.dataset.playbackEngine || "";
    if (visualizer.dataset.playbackState !== "stopped" && activeEngine) {
      return activeEngine;
    }
    return audioClockReady(visualizer) ? "html" : "native";
  }

  function sendPlaybackRequest(request) {
    const visualizer = visualizerForOrd(request.ord);
    if (visualizer) {
      visualizer.dataset.playbackEngine = request.engine || "";
    }
    window.__aqePendingPlaybackRequest = request;
    window.__aqeLastPlaybackRequest = request;
    if (typeof pycmd === "function") {
      window.__aqeActiveField = request.ord;
      pycmd("focus:" + request.ord);
      pycmd("aqe:play");
    }
  }

  function startEditorHtmlPlayback(visualizer, request) {
    startProgressClock(visualizer, request.cursorMs, {
      engine: "html",
      manualFallback: false,
      onAudioStarted() {
        sendPlaybackRequest(request);
      },
      onAudioPlayFailed() {
        stopProgressClock(visualizer);
        sendPlaybackRequest({
          ...request,
          engine: "native"
        });
      }
    });
    return true;
  }

  function handleHtmlPlaybackCommand(ord) {
    const visualizer = visualizerForOrd(ord);
    if (playbackEngineFor(visualizer) !== "html") return false;
    const request = {
      ...playbackRequest(ord),
      engine: "html"
    };
    if (request.action === "pause") {
      pauseProgressClock(visualizer);
      request.cursorMs = Number(visualizer.dataset.cursorMs || request.cursorMs || "0");
      sendPlaybackRequest(request);
      return true;
    }
    if (request.action === "resume") {
      request.cursorMs = Number(visualizer.dataset.cursorMs || request.cursorMs || "0");
    }
    return startEditorHtmlPlayback(visualizer, request);
  }

  window.__aqeSetVisualizer = function(ord, track, cursorMs) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer || !track) return;
    visualizer.hidden = false;
    visualizer.dataset.graphActive = "true";
    visualizer.dataset.graphBusy = "false";
    visualizer.dataset.hasTrack = "true";
    visualizer.dataset.durationMs = String(track.durationMs || 0);
    visualizer.dataset.anchorMs = String(cursorMs || 0);
    visualizer.dataset.analyzerName = track.analyzerName || "";
    visualizer.dataset.sourceFilename = track.sourceFilename || "";
    configureAudioClock(visualizer, track.sourceFilename || "");
    const button = graphButton(ord);
    if (button) button.textContent = "Redraw";
    const intensity = visualizer.querySelector(".aqe-intensity");
    if (intensity) intensity.setAttribute("d", pathForIntensity(track.points, track.durationMs));
    drawPitch(visualizer, track);
    drawLabels(visualizer, track);
    drawXAxis(visualizer, track.durationMs || 0);
    setCursor(visualizer, cursorMs || 0, false);
    if (audioClockReady(visualizer)) {
      seekAudioClock(visualizer, cursorMs || 0);
    }
    setVisualizerStatus(ord, track.analyzerName || "", "info");
    setControlsBusy(ord, false, "", "");
  };

  window.__aqeSetVisualizerStatus = function(ord, message, kind) {
    const visualizer = visualizerForOrd(ord);
    if (visualizer) {
      visualizer.hidden = false;
      visualizer.dataset.graphActive = "true";
      if (kind === "processing") {
        visualizer.dataset.hasTrack = "false";
      }
      const button = graphButton(ord);
      if (button) button.textContent = "Redraw";
    }
    setVisualizerStatus(ord, message, kind);
  };

  window.__aqeResetGraphAfterEdit = resetGraphAfterEdit;

  window.__aqeSetPlaybackState = function(ord, state, cursorMs) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return;
    if (state === "playing" || state === "paused") {
      visualizer.dataset.resumeRequiresRestart = "false";
    }
    if (state === "playing") startProgressClock(visualizer, cursorMs, {
      engine: visualizer.dataset.playbackEngine || ""
    });
    else if (state === "paused") pauseProgressClock(visualizer);
    else stopProgressClock(visualizer);
  };

  window.__aqeGetPlaybackRequest = function() {
    if (window.__aqePendingPlaybackRequest) {
      const request = window.__aqePendingPlaybackRequest;
      window.__aqePendingPlaybackRequest = null;
      return request;
    }
    const ord = Number(window.__aqeActiveField || "0");
    const request = playbackRequest(ord);
    const visualizer = visualizerForOrd(ord);
    if (visualizer) {
      visualizer.dataset.playbackEngine = request.engine || "";
    }
    return request;
  };

  window.__aqeStopEditorPlayback = function(ord) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return false;
    stopProgressClock(visualizer);
    return true;
  };

  window.__aqeInstallAudioPlaybackTestDriverForTest = function(ord) {
    const visualizer = visualizerForOrd(ord);
    const audio = audioClockFor(visualizer);
    if (!visualizer || !audio) return false;
    audio.__aqeTestDriverInstalled = true;
    audio.pause = function() {
      audio.__aqeTestPlaying = false;
      if (audio.__aqeTestFrame) {
        window.cancelAnimationFrame(audio.__aqeTestFrame);
        audio.__aqeTestFrame = null;
      }
    };
    audio.play = function() {
      audio.__aqeTestPlaying = true;
      audio.__aqeTestLastNow = performance.now();
      const tick = () => {
        if (!audio.__aqeTestPlaying) return;
        const now = performance.now();
        const durationSeconds = Number(visualizer.dataset.durationMs || "0") / 1000;
        const elapsedSeconds = Math.max(0, (now - Number(audio.__aqeTestLastNow || now)) / 1000);
        audio.__aqeTestLastNow = now;
        audio.currentTime = Math.min(durationSeconds, (Number(audio.currentTime) || 0) + elapsedSeconds);
        if (durationSeconds && audio.currentTime >= durationSeconds) {
          audio.__aqeTestPlaying = false;
          if (typeof audio.dispatchEvent === "function") {
            audio.dispatchEvent(new Event("ended"));
          }
          return;
        }
        audio.__aqeTestFrame = window.requestAnimationFrame(tick);
      };
      audio.__aqeTestFrame = window.requestAnimationFrame(tick);
      return Promise.resolve();
    };
    return true;
  };

  window.__aqeGetCursorMs = function() {
    const ord = window.__aqeActiveField;
    const visualizer = visualizerForOrd(ord);
    return visualizer ? Number(visualizer.dataset.cursorMs || "0") : 0;
  };

  window.__aqeGetCursorIntent = function() {
    const ord = Number(window.__aqeActiveField || "0");
    const visualizer = visualizerForOrd(ord);
    const fallback = visualizer ? Number(visualizer.dataset.cursorMs || "0") : 0;
    return window.__aqeLastCursorIntent || {
      cursorMs: fallback,
      previousPlaybackState: visualizer ? visualizer.dataset.playbackState || "stopped" : "stopped",
      restartPlayback: false
    };
  };

  window.__aqeSetCursorForTest = function(ord, ms, notifyPython) {
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return false;
    visualizer.hidden = false;
    visualizer.dataset.graphActive = "true";
    setCursor(visualizer, ms, !!notifyPython);
    return true;
  };

  window.__aqeSetCursorByClientXForTest = function(ord, clientX, notifyPython) {
    const visualizer = visualizerForOrd(ord);
    const svg = visualizer && visualizer.querySelector(".aqe-visualizer-svg");
    if (!visualizer || !svg) return null;
    const durationMs = Number(visualizer.dataset.durationMs || "0");
    const ms = cursorMsFromEvent({ clientX }, svg, durationMs);
    setCursor(visualizer, ms, !!notifyPython);
    return {
      cursorMs: Number(visualizer.dataset.cursorMs || "0"),
      cursorX: Number(visualizer.querySelector(".aqe-cursor").getAttribute("x1")),
      bounds: graphPixelBounds(svg)
    };
  };

  window.__aqeGraphStateForTest = function(ord) {
    const visualizer = visualizerForOrd(ord);
    const graph = graphButton(ord);
    const play = playButton(ord);
    if (!visualizer) return null;
    const audio = audioClockFor(visualizer);
    return {
      active: visualizer.dataset.graphActive === "true",
      busy: visualizer.dataset.graphBusy === "true",
      hidden: !!visualizer.hidden,
      hasTrack: visualizer.dataset.hasTrack === "true",
      durationMs: Number(visualizer.dataset.durationMs || "0"),
      anchorMs: Number(visualizer.dataset.anchorMs || "0"),
      cursorMs: Number(visualizer.dataset.cursorMs || "0"),
      progressMs: Number(visualizer.dataset.progressMs || "0"),
      sourceFilename: visualizer.dataset.sourceFilename || "",
      graphButtonLabel: graph ? graph.textContent : "",
      playButtonLabel: play ? play.textContent : "",
      playbackState: visualizer.dataset.playbackState || "stopped",
      resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
      audioClockSrc: audio ? (audio.getAttribute("src") || "") : "",
      audioClockCurrentMs: audio ? Math.round((Number(audio.currentTime) || 0) * 1000) : 0,
      audioClockReady: !!(audio && visualizer.__aqeAudioClockAvailable),
      audioClockFallback: !!visualizer.__aqeAudioClockFallback,
      audioClockMuted: !!(audio && audio.muted),
      audioPlaybackTestDriver: !!(audio && audio.__aqeTestDriverInstalled),
      playbackEngine: playbackEngineFor(visualizer),
      progressClockMode: visualizer.dataset.progressClockMode || "stopped",
      xAxisLabels: Array.from(visualizer.querySelectorAll(".aqe-x-label")).map((node) => node.textContent),
      pitchPaths: visualizer.querySelectorAll(".aqe-pitch-path").length,
      intensity: visualizer.querySelector(".aqe-intensity")?.getAttribute("d") || "",
      cursorX: Number(visualizer.querySelector(".aqe-cursor")?.getAttribute("x1") || "0"),
      spinnerVisible: visualizer.querySelector(".aqe-spinner") ? !visualizer.querySelector(".aqe-spinner").hidden : false,
      allButtonsDisabled: allButtons().every((button) => button.disabled),
      anyButtonDisabled: allButtons().some((button) => button.disabled)
    };
  };

  window.__aqePrepareForNewNote = prepareForNewNote;
  prepareForNewNote();
  window.__aqeScan = scan;
  setTimeout(scan, 0);
  setTimeout(scan, 250);
  setTimeout(scan, 1000);
})();
"""


def _css() -> str:
    return """
.aqe-controls {
  align-items: center;
  border: 1px solid;
  border-radius: 10px;
  color: inherit;
  color-scheme: light dark;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  justify-content: flex-start;
  margin: 4px 0 10px;
  padding: 6px 8px;
}
.aqe-button {
  background: transparent;
  border: 1px solid;
  border-radius: 7px;
  color: inherit;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}
.aqe-button:hover {
  text-decoration: underline;
}
.aqe-controls[data-busy="true"] {
  border-style: dashed;
}
.aqe-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}
.aqe-button:disabled:hover {
  text-decoration: none;
}
.aqe-status {
  font-size: 12px;
  margin-left: 4px;
}
.aqe-status[data-kind="error"] {
  font-weight: 700;
}
.aqe-visualizer {
  align-self: stretch;
  flex: 1 0 100%;
  max-width: none;
  min-width: 0;
  width: 100%;
}
.aqe-visualizer[hidden] {
  display: none;
}
.aqe-visualizer[data-has-track="false"] .aqe-visualizer-svg,
.aqe-visualizer[data-has-track="false"] .aqe-cursor-label {
  display: none;
}
.aqe-visualizer-svg {
  border: 1px solid;
  border-radius: 8px;
  color: inherit;
  display: block;
  height: 150px;
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
.aqe-hz-label,
.aqe-x-label {
  fill: currentColor;
  font-size: 11px;
  opacity: 0.8;
}
.aqe-x-label {
  text-anchor: middle;
}
.aqe-x-tick {
  opacity: 0.5;
  stroke: currentColor;
  stroke-width: 1;
}
.aqe-visualizer-meta {
  align-items: center;
  display: flex;
  font-size: 12px;
  gap: 8px;
  justify-content: flex-start;
  margin-top: 2px;
}
.aqe-spinner {
  animation: aqe-spin 800ms linear infinite;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 999px;
  box-sizing: border-box;
  display: inline-block;
  height: 12px;
  opacity: 0.75;
  width: 12px;
}
.aqe-spinner[hidden] {
  display: none;
}
.aqe-visualizer-status[data-kind="error"] {
  font-weight: 700;
}
@keyframes aqe-spin {
  to {
    transform: rotate(360deg);
  }
}
"""
