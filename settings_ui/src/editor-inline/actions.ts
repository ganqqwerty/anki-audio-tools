import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { COMMAND_SLUGS, PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import {
  focusAndSendCommand,
  popPendingPlaybackRequest,
  setCursorIntent,
  setPendingPlaybackRequest,
} from "./bridge.js";
import { logger } from "./logger.js";
import {
  PLOT,
  cursorMsFromEvent,
  drawLabels,
  drawPitch,
  drawXAxis,
  formatTime,
  graphPixelBounds,
  pathForIntensity,
  xForMs,
} from "./plot.js";
import type {
  AudioClockElement,
  CursorIntent,
  CursorPositionForTest,
  EditorCommand,
  GraphStateForTest,
  NormalizedProsodyTrack,
  PlaybackRequest,
  PlaybackState,
  ProgressClockMode,
  VisualizerElement,
} from "./types.js";
import { isPlaybackState, normalizeTrack } from "./types.js";

export { popEditorFrontendLog } from "./bridge.js";

export function controlsForOrd(ord: number): HTMLElement | null {
  return document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`);
}

export function visualizerForOrd(ord: number): VisualizerElement | null {
  return document.querySelector<VisualizerElement>(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
}

export function buttonFor(ord: number, command: EditorCommand): HTMLButtonElement | null {
  const controls = controlsForOrd(ord);
  return controls?.querySelector<HTMLButtonElement>(`[data-aqe-command="${command}"]`) ?? null;
}

export function graphButton(ord: number): HTMLButtonElement | null {
  return buttonFor(ord, "aqe:analyze");
}

export function playButton(ord: number): HTMLButtonElement | null {
  return buttonFor(ord, "aqe:play");
}

function allButtons(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>(".aqe-button"));
}

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

export function setControlsBusy(ord: number, busy: boolean, message = "", command = ""): void {
  document.body.dataset.aqeBusy = busy ? "true" : "false";
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = busy ? "true" : "false";
  });
  allButtons().forEach((button) => {
    button.disabled = !!busy;
  });
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = busy ? "processing" : "info";
  status.title = command || "";
}

export function setStatus(message: string, kind = "info"): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = kind || "info";
}

export function clearStatus(ord: number): void {
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = "";
  status.dataset.kind = "info";
  status.title = "";
}

export function send(command: EditorCommand, node: HTMLElement, ord: number): void {
  if (anyBusy()) return;
  if (typeof node.focus === "function") node.focus();
  window.__aqeActiveField = ord;
  logger.info("command dispatched", { command, ord });
  if (command === "aqe:analyze") {
    requestGraph(ord, true);
    return;
  }
  if (command === "aqe:play" && handleHtmlPlaybackCommand(ord)) {
    return;
  }
  if (PROCESSING_COMMANDS.has(command)) {
    setControlsBusy(ord, true, processingMessage(command));
  }
  focusAndSendCommand(ord, command);
}

export function mediaUrlForFilename(filename: string): string {
  return encodeURIComponent(filename || "").replaceAll("%2F", "/");
}

export function audioClockFor(visualizer: VisualizerElement | null): AudioClockElement | null {
  return visualizer?.querySelector<AudioClockElement>(".aqe-audio-clock") ?? null;
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  visualizer.__aqeAudioClockAvailable = false;
  visualizer.__aqeAudioClockFallback = false;
  visualizer.__aqeAudioClockLastSeekedMs = 0;
  visualizer.dataset.progressClockMode = "stopped";
}

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  if (visualizer.__aqePlaybackTimer) {
    window.cancelAnimationFrame(visualizer.__aqePlaybackTimer);
    visualizer.__aqePlaybackTimer = null;
  }
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.pause !== "function") return;
  try {
    audio.pause();
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  const audio = audioClockFor(visualizer);
  resetAudioClockState(visualizer);
  if (!audio) return;
  pauseAudioClock(visualizer);
  audio.removeAttribute("src");
  audio.src = "";
  try {
    audio.load();
  } catch {
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string): void {
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
  audio.setAttribute("src", mediaUrlForFilename(filename));
  try {
    audio.load();
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function installAudioClockHandlers(visualizer: VisualizerElement): void {
  const audio = audioClockFor(visualizer);
  if (!audio || audio.__aqeClockHandlersInstalled) return;
  audio.__aqeClockHandlersInstalled = true;
  audio.addEventListener("loadedmetadata", () => {
    if (!audio.getAttribute("src")) return;
    visualizer.__aqeAudioClockAvailable = true;
    visualizer.__aqeAudioClockFallback = false;
  });
  audio.addEventListener("error", () => {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
    if (visualizer.dataset.playbackState === "playing" && visualizer.dataset.progressClockMode === "audio") {
      logger.warn("audio clock failed during playback", { ord: visualizer.dataset.aqeFieldOrd });
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

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio || !visualizer?.__aqeAudioClockAvailable) return false;
  if (!audio.getAttribute("src")) return false;
  return audio.readyState === undefined || audio.readyState >= 1;
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function seekAudioClock(visualizer: VisualizerElement, ms: number): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio) return false;
  const clamped = clampProgressMs(visualizer, ms);
  try {
    audio.currentTime = clamped / 1000;
    visualizer.__aqeAudioClockLastSeekedMs = Math.round(clamped);
    return true;
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
    return false;
  }
}

export function setCursor(
  visualizer: VisualizerElement,
  ms: number,
  notifyPython: boolean,
  options: {
    engine?: "html" | "native" | "";
    previousPlaybackState?: PlaybackState;
    restartPlayback?: boolean;
    updateAnchor?: boolean;
  } = {},
): void {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
  visualizer.dataset.cursorMs = String(Math.round(clamped));
  visualizer.dataset.progressMs = String(Math.round(clamped));
  if (options.updateAnchor !== false) {
    visualizer.dataset.anchorMs = String(Math.round(clamped));
  }
  const x = xForMs(clamped, durationMs);
  const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
  if (cursor) {
    cursor.setAttribute("x1", x.toFixed(2));
    cursor.setAttribute("x2", x.toFixed(2));
  }
  const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
  if (label) label.textContent = formatTime(clamped, durationMs);
  if (notifyPython) {
    window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
    const intent: CursorIntent = {
      cursorMs: Math.round(clamped),
      previousPlaybackState: options.previousPlaybackState || playbackStateFor(visualizer),
      restartPlayback: !!options.restartPlayback,
    };
    if (options.engine) intent.engine = options.engine;
    setCursorIntent(intent);
    logger.info("cursor committed", intent);
    focusAndSendCommand(window.__aqeActiveField, "aqe:set-cursor");
  }
}

export function startCursorDrag(event: PointerEvent, visualizer: VisualizerElement, ord: number, notifyPython: boolean): void {
  event.preventDefault();
  const previousPlaybackState = playbackStateFor(visualizer);
  if (previousPlaybackState === "playing") {
    stopProgressClock(visualizer);
  }
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!svg || !durationMs) return;
  const move = (moveEvent: PointerEvent): void => {
    setCursor(visualizer, cursorMsFromEvent(moveEvent, svg, durationMs), false);
  };
  const up = (upEvent: PointerEvent): void => {
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
      engine: restartEngine,
    });
    if (audioClockReady(visualizer)) {
      seekAudioClock(visualizer, releasedMs);
    }
    if (restartPlayback && restartEngine === "html") {
      startEditorHtmlPlayback(visualizer, {
        action: "start",
        cursorMs: Math.round(clampProgressMs(visualizer, releasedMs)),
        engine: "html",
        ord,
      });
    }
  };
  move(event);
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
}

export function handleVisualizerPointerDown(event: PointerEvent, ord: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  startCursorDrag(event, visualizer, ord, true);
}

export function requestGraph(ord: number, notifyPython: boolean): void {
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
  visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.setAttribute("d", "");
  clearText(visualizer, ".aqe-pitch");
  clearText(visualizer, ".aqe-labels");
  clearText(visualizer, ".aqe-x-axis");
  setCursor(visualizer, 0, false);
  const button = graphButton(ord);
  if (button) button.textContent = "Redraw";
  setVisualizerStatus(ord, "Analyzing...", "processing");
  window.__aqeActiveField = ord;
  logger.info("graph requested", { notifyPython, ord });
  if (notifyPython) {
    setControlsBusy(ord, true, "Analyzing...", "");
    focusAndSendCommand(ord, "aqe:analyze");
  }
}

export function resetGraphAfterEdit(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  requestGraph(ord, true);
  return true;
}

export function setVisualizerStatus(ord: number, message: string, kind = "info"): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  const status = visualizer.querySelector<HTMLElement>(".aqe-visualizer-status");
  const spinner = visualizer.querySelector<HTMLElement>(".aqe-spinner");
  const processing = kind === "processing";
  visualizer.dataset.graphBusy = processing ? "true" : "false";
  if (spinner) spinner.hidden = !processing;
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = kind || "info";
}

export function setVisualizer(ord: number, rawTrack: ProsodyPayload, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return;
  const track = normalizeTrack(rawTrack);
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
  const intensity = visualizer.querySelector<SVGPathElement>(".aqe-intensity");
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
  logger.info("graph rendered", graphLogContext(ord, track));
}

export function setVisualizerStatusFromPython(ord: number, message: string, kind = "info"): void {
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
}

export function prepareForNewNote(): void {
  document.body.dataset.aqeBusy = "false";
  window.__aqeActiveField = null;
  window.__aqeLastCursorIntent = null;
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = "false";
    controls.dataset.aqeSourceFilename = "";
    controls.querySelectorAll<HTMLButtonElement>(".aqe-button").forEach((button) => {
      button.disabled = false;
      if (button.dataset.aqeCommand === "aqe:analyze") button.textContent = "Graph";
      if (button.dataset.aqeCommand === "aqe:play") button.textContent = "Play";
    });
    const status = controls.querySelector<HTMLElement>(".aqe-status");
    if (status) {
      status.textContent = "";
      status.dataset.kind = "info";
      status.title = "";
    }
    const visualizer = controls.querySelector<VisualizerElement>(".aqe-visualizer");
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
    visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.setAttribute("d", "");
    clearText(visualizer, ".aqe-pitch");
    clearText(visualizer, ".aqe-labels");
    clearText(visualizer, ".aqe-x-axis");
    const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
    if (cursor) {
      cursor.setAttribute("x1", String(PLOT.left));
      cursor.setAttribute("x2", String(PLOT.left));
    }
    const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
    if (label) label.textContent = "0 ms";
    const graphStatus = visualizer.querySelector<HTMLElement>(".aqe-visualizer-status");
    if (graphStatus) {
      graphStatus.textContent = "";
      graphStatus.dataset.kind = "info";
    }
    const spinner = visualizer.querySelector<HTMLElement>(".aqe-spinner");
    if (spinner) spinner.hidden = true;
  });
}

export function setPlaybackButtonLabel(visualizer: VisualizerElement, label: string): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const button = playButton(ord);
  if (button) button.textContent = label;
}

export function manualProgressMs(visualizer: VisualizerElement): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const elapsed = performance.now() - Number(visualizer.dataset.playStartedAt || "0");
  return Math.min(durationMs, Number(visualizer.dataset.playStartMs || "0") + elapsed);
}

export function audioProgressMs(visualizer: VisualizerElement): number | null {
  const audio = audioClockFor(visualizer);
  if (!audio) return null;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.min(durationMs, (Number(audio.currentTime) || 0) * 1000);
}

export function currentProgressMs(visualizer: VisualizerElement): number | null {
  if (visualizer.dataset.progressClockMode === "audio") {
    return audioProgressMs(visualizer);
  }
  if (visualizer.dataset.progressClockMode === "manual") {
    return manualProgressMs(visualizer);
  }
  return Number(visualizer.dataset.progressMs || visualizer.dataset.cursorMs || "0");
}

export function completePlayback(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const anchorMs = Number(visualizer.dataset.anchorMs || "0");
  stopProgressClock(visualizer);
  setCursor(visualizer, anchorMs, false, { updateAnchor: false });
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, anchorMs);
  }
  clearStatus(ord);
  window.__aqeActiveField = ord;
  focusAndSendCommand(ord, "aqe:play-ended");
}

export function paintProgressFromClock(visualizer: VisualizerElement): void {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const tick = (): void => {
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

export function startManualProgressClock(visualizer: VisualizerElement, startMs: number): void {
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
  const tick = (): void => {
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

export function startAudioProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  options: {
    manualFallback?: boolean;
    onAudioPlayFailed?: () => void;
    onAudioStarted?: () => void;
  } = {},
): void {
  const audio = audioClockFor(visualizer);
  if (!audio || !seekAudioClock(visualizer, startMs) || typeof audio.play !== "function") {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualProgressClock(visualizer, startMs);
    return;
  }
  visualizer.dataset.progressClockMode = "audio";
  visualizer.__aqeAudioClockFallback = false;
  const handlePlaybackFailure = (): void => {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualProgressClock(visualizer, startMs);
  };
  const startPainting = (): void => {
    if (visualizer.dataset.playbackState !== "playing") return;
    clearPlaybackFrame(visualizer);
    visualizer.dataset.progressClockMode = "audio";
    logger.info("html audio playback started", { ord: visualizer.dataset.aqeFieldOrd });
    paintProgressFromClock(visualizer);
    options.onAudioStarted?.();
  };
  void Promise.resolve(audio.play())
    .then(startPainting)
    .catch(() => {
      if (visualizer.dataset.playbackState !== "playing") return;
      logger.warn("html audio play rejected; using manual clock", { ord: visualizer.dataset.aqeFieldOrd });
      handlePlaybackFailure();
    });
}

export function startProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  options: {
    engine?: "html" | "native" | "";
    manualFallback?: boolean;
    onAudioPlayFailed?: () => void;
    onAudioStarted?: () => void;
  } = {},
): void {
  const selectedEngine = options.engine || visualizer.dataset.playbackEngine || "";
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
  logger.info("playback clock selected", { engine: selectedEngine || "auto", startMs: clampedStartMs });
  if (selectedEngine === "native") {
    startManualProgressClock(visualizer, clampedStartMs);
    return;
  }
  if (audioClockReady(visualizer)) {
    startAudioProgressClock(visualizer, clampedStartMs, options);
    return;
  }
  if (options.manualFallback === false) {
    options.onAudioPlayFailed?.();
    return;
  }
  startManualProgressClock(visualizer, clampedStartMs);
}

export function pauseProgressClock(visualizer: VisualizerElement): void {
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

export function stopProgressClock(
  visualizer: VisualizerElement,
  options: { clearAudio?: boolean; clearEngine?: boolean } = {},
): void {
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  visualizer.dataset.playbackState = "stopped";
  visualizer.dataset.progressClockMode = "stopped";
  visualizer.dataset.resumeRequiresRestart = "false";
  if (options.clearEngine !== false) {
    visualizer.dataset.playbackEngine = "";
  }
  if (options.clearAudio) {
    clearAudioClockSource(visualizer);
  }
  setPlaybackButtonLabel(visualizer, "Play");
}

export function playbackRequest(ord: number): PlaybackRequest {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return { ord, action: "start", cursorMs: 0 };
  const state = playbackStateFor(visualizer);
  let action: PlaybackRequest["action"] = "start";
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
    engine: playbackEngineFor(visualizer),
  };
}

export function playbackEngineFor(visualizer: VisualizerElement | null): "html" | "native" {
  if (!visualizer || visualizer.dataset.hasTrack !== "true") return "native";
  const activeEngine = visualizer.dataset.playbackEngine || "";
  if (visualizer.dataset.playbackState !== "stopped" && (activeEngine === "html" || activeEngine === "native")) {
    return activeEngine;
  }
  return audioClockReady(visualizer) ? "html" : "native";
}

export function sendPlaybackRequest(request: PlaybackRequest): void {
  const visualizer = visualizerForOrd(request.ord);
  if (visualizer) {
    visualizer.dataset.playbackEngine = request.engine || "";
  }
  setPendingPlaybackRequest(request);
  window.__aqeActiveField = request.ord;
  logger.info("playback request queued", request);
  focusAndSendCommand(request.ord, "aqe:play");
}

export function startEditorHtmlPlayback(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  startProgressClock(visualizer, request.cursorMs, {
    engine: "html",
    manualFallback: false,
    onAudioStarted() {
      sendPlaybackRequest(request);
    },
    onAudioPlayFailed() {
      logger.warn("html playback failed; falling back to native", { ord: request.ord });
      stopProgressClock(visualizer);
      sendPlaybackRequest({
        ...request,
        engine: "native",
      });
    },
  });
  return true;
}

export function handleHtmlPlaybackCommand(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || playbackEngineFor(visualizer) !== "html") return false;
  const request: PlaybackRequest = {
    ...playbackRequest(ord),
    engine: "html",
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

export function setPlaybackState(ord: number, state: PlaybackState, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  if (state === "playing" || state === "paused") {
    visualizer.dataset.resumeRequiresRestart = "false";
  }
  if (state === "playing") {
    startProgressClock(visualizer, cursorMs, {
      engine: visualizer.dataset.playbackEngine === "html" || visualizer.dataset.playbackEngine === "native"
        ? visualizer.dataset.playbackEngine
        : "",
    });
  } else if (state === "paused") {
    pauseProgressClock(visualizer);
  } else {
    stopProgressClock(visualizer);
  }
}

export function getPlaybackRequest(): PlaybackRequest {
  const pending = popPendingPlaybackRequest();
  if (pending) return pending;
  const ord = Number(window.__aqeActiveField || "0");
  const request = playbackRequest(ord);
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.dataset.playbackEngine = request.engine || "";
  }
  return request;
}

export function stopEditorPlayback(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  stopProgressClock(visualizer);
  return true;
}

export function installAudioPlaybackTestDriver(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  const audio = audioClockFor(visualizer);
  if (!visualizer || !audio) return false;
  audio.__aqeTestDriverInstalled = true;
  audio.pause = function pause(): void {
    audio.__aqeTestPlaying = false;
    if (audio.__aqeTestFrame) {
      window.cancelAnimationFrame(audio.__aqeTestFrame);
      audio.__aqeTestFrame = null;
    }
  };
  audio.play = function play(): Promise<void> {
    audio.__aqeTestPlaying = true;
    audio.__aqeTestLastNow = performance.now();
    const tick = (): void => {
      if (!audio.__aqeTestPlaying) return;
      const now = performance.now();
      const durationSeconds = Number(visualizer.dataset.durationMs || "0") / 1000;
      const elapsedSeconds = Math.max(0, (now - Number(audio.__aqeTestLastNow || now)) / 1000);
      audio.__aqeTestLastNow = now;
      audio.currentTime = Math.min(durationSeconds, (Number(audio.currentTime) || 0) + elapsedSeconds);
      if (durationSeconds && audio.currentTime >= durationSeconds) {
        audio.__aqeTestPlaying = false;
        audio.dispatchEvent(new Event("ended"));
        return;
      }
      audio.__aqeTestFrame = window.requestAnimationFrame(tick);
    };
    audio.__aqeTestFrame = window.requestAnimationFrame(tick);
    return Promise.resolve();
  };
  return true;
}

export function getCursorMs(): number {
  const ord = Number(window.__aqeActiveField || "0");
  const visualizer = visualizerForOrd(ord);
  return visualizer ? Number(visualizer.dataset.cursorMs || "0") : 0;
}

export function getCursorIntent(): CursorIntent {
  const ord = Number(window.__aqeActiveField || "0");
  const visualizer = visualizerForOrd(ord);
  const fallback = visualizer ? Number(visualizer.dataset.cursorMs || "0") : 0;
  return window.__aqeLastCursorIntent || {
    cursorMs: fallback,
    previousPlaybackState: visualizer ? playbackStateFor(visualizer) : "stopped",
    restartPlayback: false,
  };
}

export function setCursorForTest(ord: number, ms: number, notifyPython: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  visualizer.hidden = false;
  visualizer.dataset.graphActive = "true";
  setCursor(visualizer, ms, !!notifyPython);
  return true;
}

export function setCursorByClientXForTest(ord: number, clientX: number, notifyPython: boolean): CursorPositionForTest | null {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  if (!visualizer || !svg) return null;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const ms = cursorMsFromEvent({ clientX }, svg, durationMs);
  setCursor(visualizer, ms, !!notifyPython);
  return {
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    cursorX: Number(visualizer.querySelector<SVGLineElement>(".aqe-cursor")?.getAttribute("x1") || "0"),
    bounds: graphPixelBounds(svg),
  };
}

export function graphStateForTest(ord: number): GraphStateForTest | null {
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
    graphButtonLabel: graph ? graph.textContent || "" : "",
    playButtonLabel: play ? play.textContent || "" : "",
    playbackState: playbackStateFor(visualizer),
    resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
    audioClockSrc: audio ? (audio.getAttribute("src") || "") : "",
    audioClockCurrentMs: audio ? Math.round((Number(audio.currentTime) || 0) * 1000) : 0,
    audioClockReady: !!(audio && visualizer.__aqeAudioClockAvailable),
    audioClockFallback: !!visualizer.__aqeAudioClockFallback,
    audioClockMuted: !!(audio && audio.muted),
    audioPlaybackTestDriver: !!(audio && audio.__aqeTestDriverInstalled),
    playbackEngine: playbackEngineFor(visualizer),
    progressClockMode: progressClockModeFor(visualizer),
    xAxisLabels: Array.from(visualizer.querySelectorAll<SVGTextElement>(".aqe-x-label")).map((node) => node.textContent || ""),
    pitchPaths: visualizer.querySelectorAll(".aqe-pitch-path").length,
    intensity: visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.getAttribute("d") || "",
    cursorX: Number(visualizer.querySelector<SVGLineElement>(".aqe-cursor")?.getAttribute("x1") || "0"),
    spinnerVisible: visualizer.querySelector<HTMLElement>(".aqe-spinner") ? !visualizer.querySelector<HTMLElement>(".aqe-spinner")?.hidden : false,
    allButtonsDisabled: allButtons().every((button) => button.disabled),
    anyButtonDisabled: allButtons().some((button) => button.disabled),
  };
}

function clearText(root: VisualizerElement, selector: string): void {
  const node = root.querySelector<HTMLElement | SVGElement>(selector);
  if (node) node.textContent = "";
}

function playbackStateFor(visualizer: VisualizerElement): PlaybackState {
  const state = visualizer.dataset.playbackState;
  return isPlaybackState(state) ? state : "stopped";
}

function progressClockModeFor(visualizer: VisualizerElement): ProgressClockMode {
  const mode = visualizer.dataset.progressClockMode;
  if (mode === "audio" || mode === "manual" || mode === "stopped") return mode;
  return "stopped";
}

function graphLogContext(ord: number, track: NormalizedProsodyTrack): { analyzerName: string; durationMs: number; ord: number; points: number; sourceFilename: string } {
  return {
    analyzerName: track.analyzerName,
    durationMs: track.durationMs,
    ord,
    points: track.points.length,
    sourceFilename: track.sourceFilename,
  };
}

export function commandSlugsForTest(): Readonly<Record<EditorCommand, string>> {
  return COMMAND_SLUGS;
}
