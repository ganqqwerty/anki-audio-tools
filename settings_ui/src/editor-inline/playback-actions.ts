import { visualizerForOrd } from "./dom-selectors.js";
import {
  editorPracticePlaybackState,
  pauseEditorPracticeProgram,
  pauseEditorPracticeWait,
  resumeEditorPracticeProgram,
} from "./editor-practice-controller.js";
import {
  dispatchHtmlAudioSessionEvent,
  dispatchHtmlAudioSessionAttemptFact,
  readHtmlAudioTransportPosition,
  readHtmlAudioTransportSnapshot,
} from "./html-audio-session-controller.js";
import {
  logPlaybackReadinessDecision,
  playbackReadinessDecisionFor,
} from "./playback-telemetry.js";
import { playbackRequestForVisualizer } from "./playback-request-planning.js";
import { startSourcePlaybackAction } from "./source-playback-actions.js";
import type { CursorIntent, PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import { readFieldState } from "./field-state-store.js";
import { setPlaybackButtonLabelForVisualizer } from "./playback-button-label.js";
import { effectivePlaybackRegion } from "./selection-controller.js";

function fieldOrd(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function setPlaybackButtonLabel(visualizer: VisualizerElement, label: string): void {
  setPlaybackButtonLabelForVisualizer(visualizer, label);
}

export function currentProgressMs(visualizer: VisualizerElement): number | null {
  const ord = fieldOrd(visualizer);
  const snapshot = readHtmlAudioTransportSnapshot(ord);
  if (snapshot.active || snapshot.session.kind === "paused") {
    return snapshot.session.kind !== "empty"
      && snapshot.session.kind !== "failed"
      && snapshot.session.source.kind === "learner_recording"
      ? snapshot.session.source.startCursorMs + snapshot.activeMediaPositionMs
      : snapshot.activeMediaPositionMs;
  }
  return readFieldState(ord).cursor.progressMs;
}

export function handlePlaybackBoundary(visualizer: VisualizerElement, nextMs: number): boolean {
  const ord = fieldOrd(visualizer);
  const snapshot = readHtmlAudioTransportSnapshot(ord);
  const state = snapshot.session;
  if (state.kind !== "starting" && state.kind !== "playing") return false;
  if (nextMs < state.request.endMs) return false;
  if (!snapshot.attemptIdentity) return false;
  dispatchHtmlAudioSessionAttemptFact(ord, snapshot.attemptIdentity, {
    cursorMs: nextMs,
    resetCursorMs: state.request.resetCursorMs ?? state.request.cursorMs,
    type: "BoundaryReached",
  });
  return true;
}

export function completePlayback(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  const state = readHtmlAudioTransportSnapshot(ord).session;
  const attemptIdentity = readHtmlAudioTransportSnapshot(ord).attemptIdentity;
  if (state.kind !== "starting" && state.kind !== "playing") return;
  if (!attemptIdentity) return;
  dispatchHtmlAudioSessionAttemptFact(ord, attemptIdentity, {
    cursorMs: state.request.resetCursorMs ?? state.request.cursorMs,
    type: "BoundaryReached",
  });
}

export function pauseProgressClock(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: readHtmlAudioTransportPosition(ord),
    type: "PauseRequested",
  });
}

export function stopProgressClock(
  visualizer: VisualizerElement,
  options: { clearAudio?: boolean; clearEngine?: boolean } = {},
): void {
  const ord = fieldOrd(visualizer);
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: readHtmlAudioTransportPosition(ord),
    type: "StopRequested",
  });
  if (options.clearAudio) dispatchHtmlAudioSessionEvent(ord, { type: "SourceCleared" });
}

export function playbackRequest(ord: number): PlaybackRequest {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) {
    const decision = playbackReadinessDecisionFor(null);
    logPlaybackReadinessDecision("playback_request", null, decision, { action: "start", ord });
    return { ord, action: "start", cursorMs: 0 };
  }
  const decision = playbackReadinessDecisionFor(visualizer);
  const request = playbackRequestForVisualizer(visualizer, ord, decision);
  logPlaybackReadinessDecision("playback_request", visualizer, decision, {
    action: request.action,
    endMs: request.endMs ?? null,
    requestRegionMode: request.regionMode ?? "",
    source: request.source ?? "user",
  });
  return request;
}

export function playbackEngineFor(visualizer: VisualizerElement | null): "html" {
  return playbackReadinessDecisionFor(visualizer).engine;
}

export function startSourcePlayback(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  return startSourcePlaybackAction(visualizer, request);
}

export function handleHtmlPlaybackCommand(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const request: PlaybackRequest = { ...playbackRequest(ord), engine: "html" };
  if (request.action === "pause") {
    if (pauseEditorPracticeWait(ord)) {
      return true;
    }
    pauseEditorPracticeProgram(ord);
    pauseProgressClock(visualizer);
    return true;
  }
  if (request.action === "resume") {
    const transportWillResume = readHtmlAudioTransportSnapshot(ord).session.kind === "paused";
    const programHandled = resumeEditorPracticeProgram(ord, transportWillResume);
    if (transportWillResume || !programHandled) {
      dispatchHtmlAudioSessionEvent(ord, { type: "ResumeRequested" });
    }
    return true;
  }
  return startSourcePlayback(visualizer, request);
}

export function stopEditorPlayback(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const snapshot = readHtmlAudioTransportSnapshot(ord);
  if (!snapshot.active && snapshot.session.kind !== "paused") return false;
  stopProgressClock(visualizer);
  return true;
}

export function getCursorMs(): number {
  const ord = Number(window.__aqeActiveField || "0");
  return readFieldState(ord).cursor.ms;
}

export function getCursorIntent(): CursorIntent {
  const ord = Number(window.__aqeActiveField || "0");
  const visualizer = visualizerForOrd(ord);
  const fallback = readFieldState(ord).cursor.ms;
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
  const practiceState = editorPracticePlaybackState(fieldOrd(visualizer));
  if (practiceState !== "stopped") return practiceState;
  const state = readHtmlAudioTransportSnapshot(fieldOrd(visualizer)).session;
  if (state.kind === "paused") return "paused";
  if (state.kind === "starting" || state.kind === "playing") {
    return "playing";
  }
  return "stopped";
}
