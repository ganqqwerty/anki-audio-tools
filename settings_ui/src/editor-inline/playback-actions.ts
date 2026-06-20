import { focusAndSendCommand, popPendingPlaybackRequest, setPendingPlaybackRequest } from "./bridge.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import { htmlAudioReadinessFor } from "./audio-readiness.js";
import type { PlaybackEngineDecision } from "./playback-engine-decision.js";
import { logPlaybackEngineDecision, playbackEngineDecisionFor, postEditPlaybackStartContext } from "./playback-telemetry.js";
import { startSourceHtmlPlayback } from "./source-playback-controller.js";
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
import { planPlaybackRequest, type PlaybackSnapshot } from "./playback-model.js";
import {
  consumePostEditPlaybackIntent,
  postEditRenderedGraphCanDriveHtmlPlayback,
} from "./post-edit-playback.js";
import { dispatchHtmlAudioSessionEvent } from "./html-audio-session-controller.js";
import type { CursorIntent, PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import {
  effectivePlaybackRegion,
  playbackControllerDependencies,
  repeatEnabledFor,
  setRepeatEnabled,
  setRepeatPauseSeconds,
} from "./actions.js";
import { anyBusy, setCommandButtonLabel } from "./control-actions.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import { setPreserveStatusOnPlaybackEndRuntime } from "./visualizer-runtime-state.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function setPlaybackButtonLabel(visualizer: VisualizerElement, label: string): void {
  const s = fieldState(visualizer);
  setCommandButtonLabel(s.ord, "aqe:play", label);
  syncSelectionToolbar(visualizer);
}

export function manualProgressMs(visualizer: VisualizerElement): number { return manualProgressMsFromController(visualizer); }

export function audioProgressMs(visualizer: VisualizerElement): number | null { return audioProgressMsFromController(visualizer); }

export function currentProgressMs(visualizer: VisualizerElement): number | null { return currentProgressMsFromController(visualizer); }

export function handlePlaybackBoundary(visualizer: VisualizerElement, nextMs: number): boolean {
  return handlePlaybackBoundaryFromController(visualizer, nextMs, playbackControllerDependencies());
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
  if (!visualizer) {
    const decision = playbackEngineDecisionFor(null);
    logPlaybackEngineDecision("playback_request", null, decision, { action: "start", ord });
    return { ord, action: "start", cursorMs: 0 };
  }
  const decision = playbackEngineDecisionFor(visualizer);
  const request = planPlaybackRequest(playbackSnapshotFor(visualizer, ord, decision));
  logPlaybackEngineDecision("playback_request", visualizer, decision, {
    action: request.action,
    endMs: request.endMs ?? null,
    requestRegionMode: request.regionMode ?? "",
    source: request.source ?? "user",
  });
  return request;
}

function playbackSnapshotFor(
  visualizer: VisualizerElement,
  ord: number,
  decision: PlaybackEngineDecision = playbackEngineDecisionFor(visualizer),
): PlaybackSnapshot {
  const s = fieldState(visualizer);
  return {
    anchorMs: s.cursor.anchorMs,
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: s.cursor.ms,
    durationMs: readVisualizerTargetDurationMs(visualizer),
    engine: decision.engine,
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
  const readiness = htmlAudioReadinessFor(visualizer);
  if (readiness.transient && !postEditRenderedGraphCanDriveHtmlPlayback(
    ord,
    readFieldState(ord).sourceFilename,
    readiness,
  )) {
    logger.info("post-edit playback start rejected: browser audio loading", {
      ...postEditPlaybackStartContext(ord, visualizer),
      htmlAudioReadinessReason: readiness.reason,
      htmlAudioReadinessState: readiness.state,
    });
    return false;
  }
  const intent = consumePostEditPlaybackIntent(ord);
  if (intent) {
    setRepeatEnabled(visualizer, intent.repeat);
    setRepeatPauseSeconds(visualizer, intent.repeatPauseSeconds);
  }
  window.__aqeActiveField = ord;
  const region = effectivePlaybackRegion(visualizer);
  const decision = playbackEngineDecisionFor(visualizer);
  const request: PlaybackRequest = {
    action: "start",
    cursorMs: Math.round(region.startMs),
    endMs: Math.round(region.endMs),
    engine: decision.engine,
    loop: repeatEnabledFor(visualizer),
    ord,
    regionMode: region.mode,
    source: "post_edit",
  };
  logPlaybackEngineDecision("post_edit", visualizer, decision, {
    action: request.action,
    endMs: request.endMs ?? null,
    source: "post_edit",
  });
  logger.info("post-edit playback start requested", {
    ...postEditPlaybackStartContext(ord, visualizer),
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    loop: request.loop,
    regionMode: request.regionMode,
  });
  const started = startSourcePlayback(visualizer, request);
  logger.info("post-edit html playback start result", {
    ...postEditPlaybackStartContext(ord, visualizer),
    started,
  });
  return started;
}

export function playbackEngineFor(visualizer: VisualizerElement | null): "html" {
  return playbackEngineDecisionFor(visualizer).engine;
}

export function sendPlaybackRequest(request: PlaybackRequest): void {
  const visualizer = visualizerForOrd(request.ord);
  if (visualizer) {
    updateFieldState(request.ord, (state) => ({
      ...state,
      playback: { ...state.playback, engine: request.engine || "" },
    }));
    setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  }
  setPendingPlaybackRequest(request);
  window.__aqeActiveField = request.ord;
  logger.info("playback request queued", request);
  focusAndSendCommand(request.ord, "aqe:play");
}

export function startSourcePlayback(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  return startSourceHtmlPlayback(visualizer, { ...request, engine: "html" });
}

export function handleHtmlPlaybackCommand(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const request: PlaybackRequest = {
    ...playbackRequest(ord),
    engine: "html",
  };
  if (request.action === "pause") {
    pauseProgressClock(visualizer);
    const s = fieldState(visualizer);
    request.cursorMs = s.cursor.ms || request.cursorMs || 0;
    dispatchHtmlAudioSessionEvent(ord, { cursorMs: request.cursorMs, type: "PauseRequested" });
    sendPlaybackRequest(request);
    return true;
  }
  if (request.action === "resume") {
    const s = fieldState(visualizer);
    request.cursorMs = s.cursor.ms || request.cursorMs || 0;
    dispatchHtmlAudioSessionEvent(ord, { type: "ResumeRequested" });
    sendPlaybackRequest(request);
    return true;
  }
  return startSourcePlayback(visualizer, request);
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
      engine: s.playback.engine === "html" ? "html" : "",
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
    setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
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
