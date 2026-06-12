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
import { planPlaybackRequest, selectionCoversFullDuration, type PlaybackSnapshot } from "./playback-model.js";
import { consumePostEditPlaybackIntent } from "./post-edit-playback.js";
import type { CursorIntent, PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import {
  audioClockReady,
  effectivePlaybackRegion,
  playbackControllerDependencies,
  repeatEnabledFor,
  setRepeatEnabled,
  setRepeatPauseSeconds,
} from "./actions.js";
import { anyBusy, setCommandButtonLabel, setStatus } from "./control-actions.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import { t } from "../lib/i18n.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function setPlaybackButtonLabel(visualizer: VisualizerElement, label: string): void {
  const s = fieldState(visualizer);
  setCommandButtonLabel(s.ord, "aqe:play", label);
  syncSelectionToolbar(visualizer);
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
  return planPlaybackRequest(playbackSnapshotFor(visualizer, ord));
}

function playbackSnapshotFor(visualizer: VisualizerElement, ord: number): PlaybackSnapshot {
  const s = fieldState(visualizer);
  return {
    anchorMs: s.cursor.anchorMs,
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: s.cursor.ms,
    durationMs: readVisualizerTargetDurationMs(visualizer),
    engine: playbackEngineFor(visualizer),
    ord,
    playbackState: playbackStateFor(visualizer),
    region: effectivePlaybackRegion(visualizer),
    repeat: repeatEnabledFor(visualizer),
    resumeRequiresRestart: s.playback.resumeRequiresRestart,
  };
}

export function playAfterEdit(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) {
    logger.warn("post-edit playback start rejected: visualizer missing", { ord });
    return false;
  }
  if (anyBusy()) {
    logger.info("post-edit playback start rejected: editor busy", postEditPlaybackStartContext(ord, visualizer));
    return false;
  }
  const intent = consumePostEditPlaybackIntent(ord);
  if (intent) {
    setRepeatEnabled(visualizer, intent.repeat);
    setRepeatPauseSeconds(visualizer, intent.repeatPauseSeconds);
  }
  window.__aqeActiveField = ord;
  const region = effectivePlaybackRegion(visualizer);
  const request: PlaybackRequest = {
    action: "start",
    cursorMs: Math.round(region.startMs),
    endMs: Math.round(region.endMs),
    engine: playbackEngineFor(visualizer),
    loop: repeatEnabledFor(visualizer),
    ord,
    regionMode: region.mode,
    source: "post_edit",
  };
  logger.info("post-edit playback start requested", {
    ...postEditPlaybackStartContext(ord, visualizer),
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    loop: request.loop,
    regionMode: request.regionMode,
  });
  if (request.engine === "html") {
    const started = startEditorHtmlPlayback(visualizer, request);
    logger.info("post-edit html playback start result", {
      ...postEditPlaybackStartContext(ord, visualizer),
      started,
    });
    return started;
  }
  sendPlaybackRequest(request);
  logger.info("post-edit native playback request sent", postEditPlaybackStartContext(ord, visualizer));
  return true;
}

function postEditPlaybackStartContext(ord: number, visualizer: VisualizerElement): Record<string, unknown> {
  const s = fieldState(visualizer);
  return {
    audioClockReady: audioClockReady(visualizer),
    engine: playbackEngineFor(visualizer),
    graphBusy: s.graph.busy ? "true" : "",
    hasTrack: s.graph.hasTrack ? "true" : "",
    ord,
    playbackState: s.playback.state,
    repeatEnabled: repeatEnabledFor(visualizer),
    sourceFilename: s.sourceFilename,
  };
}

export function playbackEngineFor(visualizer: VisualizerElement | null): "html" | "native" {
  if (!visualizer) return "native";
  const s = fieldState(visualizer);
  const activeEngine = s.playback.engine;
  if (s.playback.state !== "stopped" && (activeEngine === "html" || activeEngine === "native")) {
    return activeEngine;
  }
  const region = effectivePlaybackRegion(visualizer);
  if (region.mode === "selection" && repeatEnabledFor(visualizer)) {
    return "html";
  }
  if (!s.graph.hasTrack) {
    return repeatEnabledFor(visualizer) && s.graph.durationMs > 0 && audioClockReady(visualizer) ? "html" : "native";
  }
  return audioClockReady(visualizer) ? "html" : "native";
}

export function sendPlaybackRequest(request: PlaybackRequest): void {
  const visualizer = visualizerForOrd(request.ord);
  if (visualizer) {
    updateFieldState(request.ord, (state) => ({
      ...state,
      playback: { ...state.playback, engine: request.engine || "" },
    }));
    visualizer.dataset.preserveStatusOnPlaybackEnd = request.source === "post_edit" ? "true" : "false";
  }
  setPendingPlaybackRequest(request);
  window.__aqeActiveField = request.ord;
  logger.info("playback request queued", request);
  focusAndSendCommand(request.ord, "aqe:play");
}

export function startEditorHtmlPlayback(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  visualizer.dataset.preserveStatusOnPlaybackEnd = request.source === "post_edit" ? "true" : "false";
  startProgressClock(visualizer, request.cursorMs, {
    engine: "html",
    manualFallback: false,
    onAudioStarted() {
      sendPlaybackRequest(request);
    },
    onAudioPlayFailed() {
      logger.warn("html playback failed; falling back to native", { ord: request.ord });
      stopProgressClock(visualizer);
      if (repeatFallbackRequiresBrowserAudio(visualizer, request)) {
        window.__aqeActiveField = request.ord;
        setStatus(t("editor.status.selected_repeat_browser_audio"), "warning", "playback");
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

function repeatFallbackRequiresBrowserAudio(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  if (!request.loop) return false;
  if (request.source === "post_edit") return true;
  if (request.regionMode !== "selection") return false;
  const s = fieldState(visualizer);
  const startMs = s.selection.active
    ? (s.selection.startMs ?? 0)
    : Number(request.cursorMs || "0");
  const endMs = s.selection.active
    ? (s.selection.endMs ?? request.endMs ?? s.graph.durationMs)
    : Number(request.endMs || s.graph.durationMs);
  return !selectionCoversFullDuration({ endMs, mode: "selection", startMs }, s.graph.durationMs);
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
    const s = fieldState(visualizer);
    request.cursorMs = s.cursor.ms || request.cursorMs || 0;
    sendPlaybackRequest(request);
    return true;
  }
  if (request.action === "resume") {
    const s = fieldState(visualizer);
    request.cursorMs = s.cursor.ms || request.cursorMs || 0;
  }
  return startEditorHtmlPlayback(visualizer, request);
}

export function setPlaybackState(ord: number, state: PlaybackState, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  if (state === "playing" || state === "paused") {
    updateFieldState(ord, (fieldState) => ({
      ...fieldState,
      playback: { ...fieldState.playback, resumeRequiresRestart: false },
    }));
  }
  if (state === "playing") {
    const s = fieldState(visualizer);
    startProgressClock(visualizer, cursorMs, {
      engine: s.playback.engine === "html" || s.playback.engine === "native"
        ? s.playback.engine
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
    updateFieldState(ord, (state) => ({
      ...state,
      playback: { ...state.playback, engine: request.engine || "" },
    }));
    visualizer.dataset.preserveStatusOnPlaybackEnd = request.source === "post_edit" ? "true" : "false";
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
  if (!visualizer) return 0;
  return fieldState(visualizer).cursor.ms;
}

export function getCursorIntent(): CursorIntent {
  const ord = Number(window.__aqeActiveField || "0");
  const visualizer = visualizerForOrd(ord);
  const fallback = visualizer ? fieldState(visualizer).cursor.ms : 0;
  const region = visualizer ? effectivePlaybackRegion(visualizer) : null;
  const fallbackIntent: CursorIntent = {
    cursorMs: fallback,
    previousPlaybackState: visualizer ? playbackStateFor(visualizer) : "stopped",
    restartPlayback: false,
  };
  if (region) {
    fallbackIntent.endMs = Math.round(region.endMs);
    fallbackIntent.regionMode = region.mode;
  }
  return window.__aqeLastCursorIntent || fallbackIntent;
}

export function playbackStateFor(visualizer: VisualizerElement): PlaybackState {
  return fieldState(visualizer).playback.state;
}
