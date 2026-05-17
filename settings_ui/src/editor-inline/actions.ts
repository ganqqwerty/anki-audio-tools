import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import {
  allButtons,
  allVisualizers,
  controlsForOrd,
  graphButton,
  playButton,
  repeatButtonForOrd,
  visualizerForOrd,
} from "./dom-selectors.js";
import {
  focusAndSendCommand,
  popPendingPlaybackRequest,
  sendGraphAnalysisRequest,
  setCursorIntent,
  setPendingPlaybackRequest,
} from "./bridge.js";
import {
  audioClockFor as audioClockForElement,
  audioClockReady as isAudioClockReady,
  clearAudioClockSource as clearAudioClockElementSource,
  configureAudioClock as configureAudioClockElement,
  installAudioClockHandlers as installAudioClockElementHandlers,
  mediaUrlForFilename as mediaUrlForAudioFilename,
  pauseAudioClock as pauseAudioClockElement,
  resetAudioClockState as resetAudioClockElementState,
  seekAudioClock as seekAudioClockElement,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import {
  continueDefaultGraphQueue,
  finishDefaultGraphRequest,
} from "./default-graph-queue.js";
import {
  buildPlaybackRequestForPython,
  type PlaybackRegion,
} from "./playback-state.js";
import type { AudioClockElement, CursorIntent, DefaultGraphTarget, EditorCommand, PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import { isPlaybackState, normalizeTrack } from "./types.js";
import {
  shouldTreatSelectionGestureAsClick as isClickLikeSelectionGesture,
} from "./selection-state.js";
import {
  clearSelection as clearSelectionFromController,
  clearSelectionDraft as clearSelectionDraftFromController,
  commitSelectionDraft as commitSelectionDraftFromController,
  draftSelectionForVisualizer as draftSelectionForVisualizerFromController,
  effectivePlaybackRegion as effectivePlaybackRegionFromController,
  selectionForVisualizer as selectionForVisualizerFromController,
  setSelection as setSelectionFromController,
  setSelectionDraft as setSelectionDraftFromController,
  type SelectionControllerDependencies,
} from "./selection-controller.js";
import {
  handleVisualizerPointerDown as handleVisualizerPointerDownGesture,
  startCursorDrag as startCursorDragGesture,
  startSelectionGesture as startSelectionGestureFlow,
  type SelectionGestureDependencies,
} from "./selection-gestures.js";
import {
  graphLogContext,
  renderCursor,
  renderGraphRequested,
  renderVisualizerStatus,
  renderVisualizerTrack,
  resetCursorProjection,
  resetVisualizerPlot,
} from "./visualizer-renderer.js";
import {
  audioProgressMs as audioProgressMsFromController,
  clearPlaybackFrame as clearPlaybackFrameFromController,
  completePlayback as completePlaybackFromController,
  currentProgressMs as currentProgressMsFromController,
  handlePlaybackBoundary as handlePlaybackBoundaryFromController,
  manualProgressMs as manualProgressMsFromController,
  paintProgressFromClock as paintProgressFromClockFromController,
  pauseProgressClock as pauseProgressClockFromController,
  startAudioProgressClock as startAudioProgressClockFromController,
  startManualProgressClock as startManualProgressClockFromController,
  startProgressClock as startProgressClockFromController,
  stopProgressClock as stopProgressClockFromController,
  type PlaybackControllerDependencies,
  type ProgressClockOptions,
} from "./playback-controller.js";

export { popEditorFrontendLog, popPendingGraphAnalysisRequest } from "./bridge.js";
export {
  buttonFor,
  controlsForOrd,
  graphButton,
  playButton,
  visualizerForOrd,
} from "./dom-selectors.js";

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function repeatDefaultFromConfig(): boolean {
  return window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
}

function stopOtherPlayback(activeVisualizer: VisualizerElement): void {
  for (const visualizer of allVisualizers()) {
    if (visualizer !== activeVisualizer && playbackStateFor(visualizer) !== "stopped") {
      stopProgressClock(visualizer);
    }
  }
}

function stopAllEditorPlayback(): void {
  for (const visualizer of allVisualizers()) {
    if (playbackStateFor(visualizer) !== "stopped") {
      stopProgressClock(visualizer);
    }
  }
}

export function setControlsBusy(ord: number, busy: boolean, message = "", command = ""): void {
  document.body.dataset.aqeBusy = busy ? "true" : "false";
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = busy ? "true" : "false";
  });
  allButtons().forEach((button) => {
    button.disabled = !!busy;
  });
  if (!busy) {
    queueMicrotask(() => continueDefaultGraphQueue(defaultGraphQueueDependencies()));
  }
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

function setCommandButtonLabel(ord: number, command: EditorCommand, label: string): void {
  const button = command === "aqe:play"
    ? playButton(ord)
    : command === "aqe:analyze"
      ? graphButton(ord)
      : controlsForOrd(ord)?.querySelector<HTMLButtonElement>(`[data-aqe-command="${command}"]`) ?? null;
  if (!button) return;
  const labelNode = button.querySelector<HTMLElement>(".aqe-button-label");
  if (labelNode) {
    labelNode.textContent = label;
  } else {
    button.textContent = label;
  }
  if (command === "aqe:play") {
    button.dataset.aqeButtonState = label === "Pause" ? "pause" : "play";
  }
  if (command === "aqe:analyze") {
    button.dataset.aqeButtonState = label === "Redraw" ? "redraw" : "graph";
  }
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
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command));
  }
  focusAndSendCommand(ord, command);
}

export function mediaUrlForFilename(filename: string): string {
  return mediaUrlForAudioFilename(filename);
}

export function audioClockFor(visualizer: VisualizerElement | null): AudioClockElement | null {
  return audioClockForElement(visualizer);
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  resetAudioClockElementState(visualizer);
}

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  clearPlaybackFrameFromController(visualizer);
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  pauseAudioClockElement(visualizer);
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  clearAudioClockElementSource(visualizer);
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string): void {
  configureAudioClockElement(visualizer, filename);
}

export function installAudioClockHandlers(visualizer: VisualizerElement): void {
  installAudioClockElementHandlers(visualizer, {
    onErrorDuringPlayback() {
      logger.warn("audio clock failed during playback", { ord: visualizer.dataset.aqeFieldOrd });
      startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"));
    },
    onEndedDuringPlayback() {
      handlePlaybackBoundary(visualizer, Number(visualizer.dataset.durationMs || "0"), { forceAudioPlay: true });
    },
  });
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  return isAudioClockReady(visualizer);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function selectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return selectionForVisualizerFromController(visualizer);
}

export function draftSelectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return draftSelectionForVisualizerFromController(visualizer);
}

export function effectivePlaybackRegion(visualizer: VisualizerElement): PlaybackRegion {
  return effectivePlaybackRegionFromController(visualizer);
}

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const button = repeatButtonForOrd(ord);
  if (button) {
    button.ariaPressed = enabled ? "true" : "false";
    button.dataset.aqeButtonState = enabled ? "active" : "default";
  }
}

export function setRepeatEnabledForOrd(ord: number, enabled: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatEnabled(visualizer, enabled);
  return true;
}

export function clearSelectionDraft(
  visualizer: VisualizerElement,
  options: { redraw?: boolean } = {},
): void {
  clearSelectionDraftFromController(visualizer, options);
}

export function setSelectionDraft(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { redraw?: boolean } = {},
): boolean {
  return setSelectionDraftFromController(visualizer, startMs, endMs, options);
}

export function commitSelectionDraft(
  visualizer: VisualizerElement,
  options: { updateCursor?: boolean } = {},
): boolean {
  return commitSelectionDraftFromController(visualizer, selectionControllerDependencies(), options);
}

export function clearSelection(
  visualizer: VisualizerElement,
  options: { resetPlaybackRegion?: boolean } = {},
): void {
  clearSelectionFromController(visualizer, options);
}

export function setSelection(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { updateCursor?: boolean } = {},
): boolean {
  return setSelectionFromController(visualizer, startMs, endMs, selectionControllerDependencies(), options);
}

export function initializePlaybackRegionState(visualizer: VisualizerElement): void {
  visualizer.dataset.playbackStartMs = "0";
  visualizer.dataset.playbackEndMs = String(Number(visualizer.dataset.durationMs || "0") || 0);
  visualizer.dataset.playbackRegionMode = "full";
  setRepeatEnabled(visualizer, repeatDefaultFromConfig());
  clearSelection(visualizer, { resetPlaybackRegion: false });
}

export function shouldTreatSelectionGestureAsClick(
  startEvent: Pick<PointerEvent, "clientX">,
  endEvent: Pick<PointerEvent, "clientX">,
  startMs: number,
  endMs: number,
): boolean {
  return isClickLikeSelectionGesture(startEvent, endEvent, startMs, endMs);
}

function selectionGestureDependencies(): SelectionGestureDependencies {
  return {
    audioClockReady,
    clearSelection,
    clearSelectionDraft,
    commitSelectionDraft,
    currentProgressMs,
    draftSelectionForVisualizer,
    playbackRequestForStart,
    playbackStateFor,
    seekAudioClock,
    selectionForVisualizer,
    setCursor,
    setSelectionDraft,
    startEditorHtmlPlayback,
    stopProgressClock,
    visualizerForOrd,
  };
}

function selectionControllerDependencies(): SelectionControllerDependencies {
  return {
    setCursor,
  };
}

function repeatEnabledFor(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

function playbackControllerDependencies(): PlaybackControllerDependencies {
  return {
    clearStatus,
    effectivePlaybackRegion,
    focusAndSendCommand,
    playbackEngineFor,
    repeatEnabledFor,
    setCursor,
    setPlaybackButtonLabel,
    stopOtherPlayback,
  };
}

function playbackRequestForStart(
  visualizer: VisualizerElement,
  ord: number,
  startMs: number,
  engine: "html" | "native" | "" = playbackEngineFor(visualizer),
): PlaybackRequest {
  const region = effectivePlaybackRegion(visualizer);
  return {
    ord,
    action: "start",
    cursorMs: Math.round(clampProgressMs(visualizer, startMs)),
    endMs: Math.round(region.endMs),
    engine,
    loop: repeatEnabledFor(visualizer),
    regionMode: region.mode,
  };
}

export function seekAudioClock(visualizer: VisualizerElement, ms: number): boolean {
  return seekAudioClockElement(visualizer, ms, Number(visualizer.dataset.durationMs || "0"));
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
  renderCursor(visualizer, clamped, durationMs);
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
  startCursorDragGesture(event, visualizer, ord, notifyPython, selectionGestureDependencies());
}

export function startSelectionGesture(event: PointerEvent, visualizer: VisualizerElement, ord: number): void {
  startSelectionGestureFlow(event, visualizer, ord, selectionGestureDependencies());
}

export function handleVisualizerPointerDown(event: PointerEvent, ord: number): void {
  handleVisualizerPointerDownGesture(event, ord, selectionGestureDependencies());
}

export function requestGraph(ord: number, notifyPython: boolean): void {
  if (!prepareGraphRequest(ord)) return;
  window.__aqeActiveField = ord;
  logger.info("graph requested", { notifyPython, ord });
  if (notifyPython) {
    setControlsBusy(ord, true, "Analyzing...", "");
    focusAndSendCommand(ord, "aqe:analyze");
  }
}

export function requestDefaultGraph(target: DefaultGraphTarget): void {
  if (!prepareGraphRequest(target.ord)) return;
  logger.info("default graph requested", target);
  setControlsBusy(target.ord, true, "Analyzing...", "");
  sendGraphAnalysisRequest(target);
}

function prepareGraphRequest(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  stopProgressClock(visualizer, { clearAudio: true });
  renderGraphRequested(visualizer);
  clearSelection(visualizer);
  setCursor(visualizer, 0, false);
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setVisualizerStatus(ord, "Analyzing...", "processing");
  return true;
}

export function resetGraphAfterEdit(ord: number): boolean {
  window.__aqePendingGraphRedrawField = ord;
  return requestPendingGraphRedraw();
}

export function requestPendingGraphRedraw(): boolean {
  const ord = window.__aqePendingGraphRedrawField;
  if (typeof ord !== "number") return false;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  if (visualizer.dataset.graphBusy === "true" || visualizer.dataset.hasTrack === "true") return true;
  requestGraph(ord, true);
  return true;
}

export function setVisualizerStatus(ord: number, message: string, kind = "info"): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  renderVisualizerStatus(visualizer, message, kind);
}

export function setVisualizer(ord: number, rawTrack: ProsodyPayload, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return;
  const track = normalizeTrack(rawTrack);
  renderVisualizerTrack(visualizer, track);
  visualizer.dataset.anchorMs = String(cursorMs || 0);
  if (window.__aqePendingGraphRedrawField === ord) {
    window.__aqePendingGraphRedrawField = null;
  }
  clearSelection(visualizer);
  visualizer.dataset.playbackStartMs = "0";
  visualizer.dataset.playbackEndMs = String(track.durationMs || 0);
  visualizer.dataset.playbackRegionMode = "full";
  configureAudioClock(visualizer, track.sourceFilename || "");
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setCursor(visualizer, cursorMs || 0, false);
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, cursorMs || 0);
  }
  setVisualizerStatus(ord, track.analyzerName || "", "info");
  setControlsBusy(ord, false, "", "");
  finishDefaultGraphRequest(ord, defaultGraphQueueDependencies());
  logger.info("graph rendered", graphLogContext(ord, track));
}

export function setVisualizerStatusFromPython(ord: number, message: string, kind = "info"): void {
  if (kind !== "processing" && window.__aqePendingGraphRedrawField === ord) {
    window.__aqePendingGraphRedrawField = null;
  }
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.hidden = false;
    visualizer.dataset.graphActive = "true";
    if (kind === "processing") {
      visualizer.dataset.hasTrack = "false";
    }
    setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  }
  setVisualizerStatus(ord, message, kind);
  if (kind !== "processing") {
    finishDefaultGraphRequest(ord, defaultGraphQueueDependencies());
  }
}

function defaultGraphQueueDependencies() {
  return {
    anyBusy,
    requestDefaultGraph,
  };
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
      if (button.dataset.aqeCommand === "aqe:analyze") {
        setCommandButtonLabel(Number(controls.dataset.aqeFieldOrd || "0"), "aqe:analyze", "Graph");
      }
      if (button.dataset.aqeCommand === "aqe:play") {
        setCommandButtonLabel(Number(controls.dataset.aqeFieldOrd || "0"), "aqe:play", "Play");
      }
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
    visualizer.dataset.playbackStartMs = "0";
    visualizer.dataset.playbackEndMs = "0";
    visualizer.dataset.playbackRegionMode = "full";
    visualizer.dataset.progressClockMode = "stopped";
    setRepeatEnabled(visualizer, repeatDefaultFromConfig());
    clearSelection(visualizer);
    resetVisualizerPlot(visualizer);
    resetCursorProjection(visualizer);
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
  setCommandButtonLabel(ord, "aqe:play", label);
}

export function manualProgressMs(visualizer: VisualizerElement): number {
  return manualProgressMsFromController(visualizer);
}

export function audioProgressMs(visualizer: VisualizerElement): number | null {
  return audioProgressMsFromController(visualizer);
}

export function currentProgressMs(visualizer: VisualizerElement): number | null {
  return currentProgressMsFromController(visualizer);
}

function handlePlaybackBoundary(visualizer: VisualizerElement, nextMs: number, options: { forceAudioPlay?: boolean } = {}): boolean {
  return handlePlaybackBoundaryFromController(visualizer, nextMs, playbackControllerDependencies(), options);
}

export function completePlayback(visualizer: VisualizerElement): void {
  completePlaybackFromController(visualizer, playbackControllerDependencies());
}

export function paintProgressFromClock(visualizer: VisualizerElement): void {
  paintProgressFromClockFromController(visualizer, playbackControllerDependencies());
}

export function startManualProgressClock(visualizer: VisualizerElement, startMs: number): void {
  startManualProgressClockFromController(visualizer, startMs, playbackControllerDependencies());
}

export function startAudioProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  options: ProgressClockOptions = {},
): void {
  startAudioProgressClockFromController(visualizer, startMs, playbackControllerDependencies(), options);
}

export function startProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  options: ProgressClockOptions = {},
): void {
  startProgressClockFromController(visualizer, startMs, playbackControllerDependencies(), options);
}

export function pauseProgressClock(visualizer: VisualizerElement): void {
  pauseProgressClockFromController(visualizer, playbackControllerDependencies());
}

export function stopProgressClock(
  visualizer: VisualizerElement,
  options: { clearAudio?: boolean; clearEngine?: boolean } = {},
): void {
  stopProgressClockFromController(visualizer, playbackControllerDependencies(), options);
}

export function playbackRequest(ord: number): PlaybackRequest {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return { ord, action: "start", cursorMs: 0 };
  return buildPlaybackRequestForPython({
    anchorMs: Number(visualizer.dataset.anchorMs || visualizer.dataset.cursorMs || "0"),
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    engine: playbackEngineFor(visualizer),
    ord,
    playbackState: playbackStateFor(visualizer),
    region: effectivePlaybackRegion(visualizer),
    repeat: repeatEnabledFor(visualizer),
    resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
  });
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
      if (request.regionMode === "selection" || request.loop) {
        window.__aqeActiveField = request.ord;
        setStatus("Selected repeat playback needs browser audio.", "warning");
        return;
      }
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

function playbackStateFor(visualizer: VisualizerElement): PlaybackState {
  const state = visualizer.dataset.playbackState;
  return isPlaybackState(state) ? state : "stopped";
}
