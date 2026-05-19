import { focusAndSendCommand, popPendingPlaybackRequest, setPendingPlaybackRequest } from "./bridge.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import {
  audioProgressMs as audioProgressMsFromController,
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
  type ProgressClockOptions,
} from "./playback-controller.js";
import { buildPlaybackRequestForPython } from "./playback-state.js";
import type { CursorIntent, PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import { isPlaybackState } from "./types.js";
import {
  audioClockReady,
  effectivePlaybackRegion,
  playbackControllerDependencies,
  repeatEnabledFor,
} from "./actions.js";
import { setCommandButtonLabel, setStatus } from "./control-actions.js";

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

export function handlePlaybackBoundary(visualizer: VisualizerElement, nextMs: number, options: { forceAudioPlay?: boolean } = {}): boolean {
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
  if (!visualizer) return "native";
  const activeEngine = visualizer.dataset.playbackEngine || "";
  if (visualizer.dataset.playbackState !== "stopped" && (activeEngine === "html" || activeEngine === "native")) {
    return activeEngine;
  }
  if (visualizer.dataset.hasTrack !== "true") {
    const hasDuration = Number(visualizer.dataset.durationMs || "0") > 0;
    return repeatEnabledFor(visualizer) && hasDuration && audioClockReady(visualizer) ? "html" : "native";
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
        setStatus("Repeat playback needs browser audio.", "warning");
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

export function playbackStateFor(visualizer: VisualizerElement): PlaybackState {
  const state = visualizer.dataset.playbackState;
  return isPlaybackState(state) ? state : "stopped";
}
